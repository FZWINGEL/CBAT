"""Multi-horizon PULSE/EIS diagnostic endpoint target construction and QA."""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA, validate_table

SCHEMA_VERSION = "gate82.diagnostic_horizon_table.v1"
DEFAULT_HORIZONS = (1, 2, 3, 5)
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
PULSE_TARGETS = {
    "pulse_1s_resistance": ("pulse_1s_resistance_k", "pulse_1s_resistance_k1"),
    "pulse_10ms_resistance": ("pulse_10ms_resistance_k", "pulse_10ms_resistance_k1"),
}
EIS_TARGETS = {
    "eis_z_abs_1kHz": ("eis_z_abs_1kHz_k", "eis_z_abs_1kHz_k1"),
    "eis_phase_1kHz": ("eis_phase_1kHz_k", "eis_phase_1kHz_k1"),
    "nyquist_im_peak_abs": ("nyquist_im_peak_abs_k", "nyquist_im_peak_abs_k1"),
    "nyquist_semicircle_width_proxy": (
        "nyquist_semicircle_width_proxy_k",
        "nyquist_semicircle_width_proxy_k1",
    ),
}
TARGET_FAMILIES = {
    "pulse": PULSE_TARGETS,
    "eis": EIS_TARGETS,
}
LEAKAGE_MARKERS = (
    "k1",
    "kh",
    "delta_capacity_Ah_h",
    "horizon_log_age",
    "event_within",
    "time_to_event",
)
FEATURE_SAFE_COLUMNS = {
    "cell_id",
    "parameter_set",
    "replicate_id",
    "checkup_k",
    "target_checkup_k",
    "horizon_checkups",
    "diagnostic_family",
    "target_name",
    "diagnostic_value_k",
    "capacity_Ah_k",
    "soh_k",
    "calendar_day_k",
    "cumulative_efc_k",
    "cumulative_q_Ah_k",
    "prior_delta_capacity_Ah",
    "prior_capacity_slope_per_day",
    "nominal_temperature_C",
    "voltage_window_family",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
    "profile_label",
    "aging_mode",
    *SPLIT_COLUMNS,
    "event_observed",
    "diagnostic_quality_flags",
    "schema_version",
}


def build_diagnostic_horizon_table(
    interval_table_path: Path,
    pulse_target_table_path: Path,
    eis_target_table_path: Path,
    out_path: Path,
    *,
    horizons: list[int] | None = None,
    target_families: list[str] | None = None,
) -> pa.Table:
    """Build long-format multi-horizon PULSE/EIS diagnostic endpoint targets."""
    selected_horizons = _normalize_horizons(horizons)
    selected_families = _normalize_families(target_families)
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    if not interval_rows:
        raise ValueError("Interval table is empty.")

    pulse_values = _diagnostic_values_by_checkup(
        pq.read_table(pulse_target_table_path).to_pylist(),
        PULSE_TARGETS,
    )
    eis_values = _diagnostic_values_by_checkup(
        pq.read_table(eis_target_table_path).to_pylist(),
        EIS_TARGETS,
    )
    values_by_family = {"pulse": pulse_values, "eis": eis_values}
    rows: list[dict[str, Any]] = []
    for cell_rows in _group_by_cell(interval_rows).values():
        rows.extend(
            _cell_diagnostic_horizon_rows(
                cell_rows,
                selected_horizons,
                selected_families,
                values_by_family,
            )
        )
    if not rows:
        raise ValueError("No diagnostic horizon rows were generated.")

    table = pa.Table.from_pylist(rows, schema=DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA)
    if not validate_table(table, DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA):
        raise TypeError("Generated diagnostic horizon table does not match DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"pulse_target_table_path": str(pulse_target_table_path).encode(),
            b"eis_target_table_path": str(eis_target_table_path).encode(),
            b"horizons": ",".join(str(value) for value in selected_horizons).encode(),
            b"target_families": ",".join(selected_families).encode(),
            b"feature_policy": b"checkup_k_state_plus_current_same_diagnostic_endpoint_only",
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table


def write_diagnostic_horizon_qa(
    diagnostic_horizon_table_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out: Path,
) -> dict[str, Any]:
    """Write coverage and leakage QA for a diagnostic horizon table."""
    rows = pq.read_table(diagnostic_horizon_table_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_out.parent.mkdir(parents=True, exist_ok=True)
    coverage_rows = diagnostic_horizon_coverage_rows(rows, interval_rows)
    _write_csv(coverage_out, coverage_rows)

    target_counts: dict[str, int] = defaultdict(int)
    current_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        target = str(row["target_name"])
        target_counts[target] += 1
        current_counts[target] += int(math.isfinite(_as_float(row.get("diagnostic_value_k"))))

    leakage_columns = [
        field.name
        for field in DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA
        if field.name in FEATURE_SAFE_COLUMNS and any(marker in field.name for marker in LEAKAGE_MARKERS)
    ]
    warnings = []
    if not rows:
        warnings.append("empty_diagnostic_horizon_table")
    if leakage_columns:
        warnings.append("feature_safe_leakage_columns_detected")
    for row in coverage_rows:
        if int(row["row_count"]) == 0:
            warnings.append(f"zero_rows_{row['diagnostic_family']}_{row['target_name']}_h{row['horizon_checkups']}")
        if int(row["c_rate_holdout_rows"]) == 0:
            warnings.append(f"zero_c_rate_rows_{row['diagnostic_family']}_{row['target_name']}_h{row['horizon_checkups']}")

    report = {
        "status": "failed" if leakage_columns or not rows else ("warning" if warnings else "passed"),
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "rows": len(rows),
            "cells": len({str(row["cell_id"]) for row in rows}),
            "parameter_sets": len({int(row["parameter_set"]) for row in rows}),
            "horizons": sorted({int(row["horizon_checkups"]) for row in rows}),
            "targets": len(target_counts),
        },
        "target_row_counts": dict(sorted(target_counts.items())),
        "finite_current_diagnostic_counts": dict(sorted(current_counts.items())),
        "leakage_columns": leakage_columns,
        "warnings": sorted(set(warnings)),
        "outputs": {"report": str(out_path), "coverage": str(coverage_out)},
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def diagnostic_horizon_coverage_rows(
    diagnostic_rows: list[dict[str, Any]],
    interval_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    horizons = sorted({int(row["horizon_checkups"]) for row in diagnostic_rows})
    possible_by_horizon = _possible_starts_by_horizon(interval_rows, horizons or DEFAULT_HORIZONS)
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in diagnostic_rows:
        grouped[
            (
                str(row["diagnostic_family"]),
                str(row["target_name"]),
                int(row["horizon_checkups"]),
            )
        ].append(row)
    keys = sorted(grouped)
    output = []
    for family, target, horizon in keys:
        rows = grouped[(family, target, horizon)]
        c_rate_rows = [row for row in rows if int(row["c_rate_holdout_fold"]) != 0]
        profile_rows = [row for row in rows if int(row["profile_holdout_fold"]) != 0]
        finite_current = [row for row in rows if math.isfinite(_as_float(row.get("diagnostic_value_k")))]
        output.append(
            {
                "diagnostic_family": family,
                "target_name": target,
                "horizon_checkups": horizon,
                "row_count": len(rows),
                "possible_capacity_start_rows": possible_by_horizon.get(horizon, 0),
                "missing_or_unobserved_target_rows": max(possible_by_horizon.get(horizon, 0) - len(rows), 0),
                "finite_current_diagnostic_rows": len(finite_current),
                "cells": len({str(row["cell_id"]) for row in rows}),
                "parameter_sets": len({int(row["parameter_set"]) for row in rows}),
                "c_rate_holdout_rows": len(c_rate_rows),
                "c_rate_holdout_parameter_sets": len({int(row["parameter_set"]) for row in c_rate_rows}),
                "profile_holdout_rows": len(profile_rows),
                "profile_holdout_parameter_sets": len({int(row["parameter_set"]) for row in profile_rows}),
            }
        )
    return output


def _cell_diagnostic_horizon_rows(
    cell_rows: list[dict[str, Any]],
    horizons: tuple[int, ...],
    target_families: tuple[str, ...],
    values_by_family: dict[str, dict[tuple[str, int], dict[str, float | str]]],
) -> list[dict[str, Any]]:
    ordered = sorted(cell_rows, key=lambda row: int(row["checkup_k"]))
    first_t = _as_float(ordered[0].get("t_result_k_s"), default=0.0)
    first_capacity = _as_float(ordered[0].get("capacity_Ah_k"))
    points: dict[int, dict[str, float]] = {}
    cumulative_efc = 0.0
    cumulative_q = 0.0
    prior_delta_by_k: dict[int, float | None] = {int(ordered[0]["checkup_k"]): None}
    prior_days_by_k: dict[int, float | None] = {int(ordered[0]["checkup_k"]): None}
    intervals_by_start = {int(row["checkup_k"]): row for row in ordered}

    for row in ordered:
        start = int(row["checkup_k"])
        stop = int(row["checkup_k_next"])
        points.setdefault(
            start,
            {
                "capacity": _as_float(row.get("capacity_Ah_k")),
                "t_s": _as_float(row.get("t_result_k_s")),
                "cumulative_efc": cumulative_efc,
                "cumulative_q": cumulative_q,
            },
        )
        cumulative_efc += max(0.0, _as_float(row.get("log_age_efc_delta"), default=0.0))
        cumulative_q += max(0.0, _as_float(row.get("log_age_delta_q_Ah"), default=0.0))
        points[stop] = {
            "capacity": _as_float(row.get("capacity_Ah_k1")),
            "t_s": _as_float(row.get("t_result_k1_s")),
            "cumulative_efc": cumulative_efc,
            "cumulative_q": cumulative_q,
        }
        prior_delta_by_k[stop] = _as_float(row.get("delta_capacity_Ah"))
        prior_days_by_k[stop] = _as_float(row.get("calendar_days"))

    output: list[dict[str, Any]] = []
    for start, interval in sorted(intervals_by_start.items()):
        start_point = points.get(start)
        if start_point is None:
            continue
        capacity_k = _as_float(start_point.get("capacity"))
        prior_delta = prior_delta_by_k.get(start)
        prior_days = prior_days_by_k.get(start)
        for horizon in horizons:
            target_checkup = start + horizon
            if target_checkup not in points:
                continue
            for family in target_families:
                values = values_by_family[family]
                current = values.get((str(interval["cell_id"]), start), {})
                future = values.get((str(interval["cell_id"]), target_checkup), {})
                for target_name in TARGET_FAMILIES[family]:
                    target_value = _as_float(future.get(target_name))
                    if not math.isfinite(target_value):
                        continue
                    current_value = _as_float(current.get(target_name))
                    flags = _merge_flags(
                        str(interval.get("quality_flags", "")),
                        str(current.get("quality_flags", "")),
                        str(future.get("quality_flags", "")),
                    )
                    if not math.isfinite(current_value):
                        flags.append("missing_current_diagnostic")
                    output.append(
                        {
                            "cell_id": str(interval["cell_id"]),
                            "parameter_set": int(interval["parameter_set"]),
                            "replicate_id": int(interval["replicate_id"]),
                            "checkup_k": start,
                            "target_checkup_k": target_checkup,
                            "horizon_checkups": horizon,
                            "diagnostic_family": family,
                            "target_name": target_name,
                            "diagnostic_value_k": current_value,
                            "diagnostic_value_kh": target_value,
                            "delta_diagnostic_value_h": target_value - current_value
                            if math.isfinite(current_value)
                            else None,
                            "capacity_Ah_k": capacity_k,
                            "soh_k": _safe_ratio(capacity_k, first_capacity),
                            "calendar_day_k": (_as_float(start_point.get("t_s")) - first_t) / 86400.0,
                            "cumulative_efc_k": _as_float(start_point.get("cumulative_efc")),
                            "cumulative_q_Ah_k": _as_float(start_point.get("cumulative_q")),
                            "prior_delta_capacity_Ah": prior_delta,
                            "prior_capacity_slope_per_day": _safe_ratio(prior_delta, prior_days),
                            "nominal_temperature_C": _as_float(interval.get("nominal_temperature_C")),
                            "voltage_window_family": str(interval.get("voltage_window_family", "")),
                            "nominal_charge_C_rate": _as_float(interval.get("nominal_charge_C_rate")),
                            "nominal_discharge_C_rate": _as_float(interval.get("nominal_discharge_C_rate")),
                            "profile_label": str(interval.get("profile_label", "")),
                            "aging_mode": str(interval.get("aging_mode", "")),
                            "condition_fold": int(interval["condition_fold"]),
                            "temperature_holdout_fold": int(interval["temperature_holdout_fold"]),
                            "c_rate_holdout_fold": int(interval["c_rate_holdout_fold"]),
                            "profile_holdout_fold": int(interval["profile_holdout_fold"]),
                            "voltage_window_holdout_fold": int(interval["voltage_window_holdout_fold"]),
                            "event_observed": True,
                            "diagnostic_quality_flags": ";".join(sorted(set(flags))) if flags else "none",
                            "schema_version": SCHEMA_VERSION,
                        }
                    )
    return output


def _diagnostic_values_by_checkup(
    rows: list[dict[str, Any]],
    target_columns: dict[str, tuple[str, str]],
) -> dict[tuple[str, int], dict[str, float | str]]:
    values: dict[tuple[str, int], dict[str, float | str]] = {}
    for row in rows:
        start_key = (str(row["cell_id"]), int(row["checkup_k"]))
        stop_key = (str(row["cell_id"]), int(row["checkup_k_next"]))
        for target_name, (start_column, stop_column) in target_columns.items():
            values.setdefault(start_key, {})[target_name] = _as_float(row.get(start_column))
            values.setdefault(stop_key, {})[target_name] = _as_float(row.get(stop_column))
        values.setdefault(start_key, {})["quality_flags"] = str(row.get("quality_flags", ""))
        values.setdefault(stop_key, {})["quality_flags"] = str(row.get("quality_flags", ""))
    return values


def _possible_starts_by_horizon(interval_rows: list[dict[str, Any]], horizons: list[int] | tuple[int, ...]) -> dict[int, int]:
    possible: dict[int, int] = defaultdict(int)
    for cell_rows in _group_by_cell(interval_rows).values():
        starts = sorted({int(row["checkup_k"]) for row in cell_rows})
        points = {int(row["checkup_k"]) for row in cell_rows} | {int(row["checkup_k_next"]) for row in cell_rows}
        for start in starts:
            for horizon in horizons:
                possible[horizon] += int(start + horizon in points)
    return possible


def _group_by_cell(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["cell_id"])].append(row)
    return grouped


def _normalize_horizons(horizons: list[int] | None) -> tuple[int, ...]:
    selected = list(DEFAULT_HORIZONS if horizons is None else horizons)
    unique = []
    seen = set()
    for value in selected:
        horizon = int(value)
        if horizon <= 0:
            raise ValueError("Horizons must be positive check-up counts.")
        if horizon not in seen:
            seen.add(horizon)
            unique.append(horizon)
    if not unique:
        raise ValueError("At least one horizon must be selected.")
    return tuple(unique)


def _normalize_families(target_families: list[str] | None) -> tuple[str, ...]:
    selected = list(TARGET_FAMILIES if target_families is None else target_families)
    unique = []
    seen = set()
    for value in selected:
        family = str(value).strip().lower()
        if family not in TARGET_FAMILIES:
            raise ValueError(f"Unknown diagnostic target family: {family}")
        if family not in seen:
            seen.add(family)
            unique.append(family)
    if not unique:
        raise ValueError("At least one diagnostic target family must be selected.")
    return tuple(unique)


def _merge_flags(*values: str) -> list[str]:
    flags = []
    for value in values:
        for flag in str(value).split(";"):
            cleaned = flag.strip()
            if cleaned and cleaned.upper() != "OK" and cleaned.lower() != "none":
                flags.append(cleaned)
    return flags


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
    num = _as_float(numerator)
    den = _as_float(denominator)
    if not math.isfinite(num) or not math.isfinite(den) or abs(den) <= 1e-12:
        return None
    return num / den


def _as_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
