"""Multi-horizon capacity target construction and QA."""

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

from mbp.data.schema_contracts import CAPACITY_HORIZON_TABLE_V1_SCHEMA, validate_table

SCHEMA_VERSION = "gate60.capacity_horizon_table.v1"
DEFAULT_HORIZONS = (1, 2, 3, 5)
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)


def build_capacity_horizon_table(
    interval_table_path: Path,
    out_path: Path,
    *,
    horizons: list[int] | None = None,
) -> pa.Table:
    """Build observed multi-check-up capacity targets from adjacent interval rows.

    The output keeps prospective check-up-k state separate from the aggregated
    k-to-k+h exposure fields, which are oracle diagnostics and not safe
    prospective inputs.
    """
    selected_horizons = _normalize_horizons(horizons)
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    if not interval_rows:
        raise ValueError("Interval table is empty.")

    rows: list[dict[str, Any]] = []
    for cell_rows in _group_by_cell(interval_rows).values():
        rows.extend(_cell_horizon_rows(cell_rows, selected_horizons))
    if not rows:
        raise ValueError("No observed multi-horizon rows were generated.")

    table = pa.Table.from_pylist(rows, schema=CAPACITY_HORIZON_TABLE_V1_SCHEMA)
    if not validate_table(table, CAPACITY_HORIZON_TABLE_V1_SCHEMA):
        raise TypeError("Generated capacity horizon table does not match CAPACITY_HORIZON_TABLE_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"horizons": ",".join(str(value) for value in selected_horizons).encode(),
            b"feature_policy": b"prior_state_features_plus_oracle_exposure_diagnostic_fields",
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table


def write_capacity_horizon_qa(
    horizon_table_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out: Path,
) -> dict[str, Any]:
    """Write coverage and censoring diagnostics for a capacity horizon table."""
    horizon_rows = pq.read_table(horizon_table_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_out.parent.mkdir(parents=True, exist_ok=True)

    coverage_rows = capacity_horizon_coverage_rows(horizon_rows, interval_rows)
    _write_csv(coverage_out, coverage_rows)
    warnings = []
    for row in coverage_rows:
        if int(row["row_count"]) == 0:
            warnings.append(f"zero_rows_horizon_{row['horizon_checkups']}")
        if int(row["c_rate_holdout_rows"]) == 0:
            warnings.append(f"zero_c_rate_rows_horizon_{row['horizon_checkups']}")
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "rows": len(horizon_rows),
            "cells": len({str(row["cell_id"]) for row in horizon_rows}),
            "parameter_sets": len({int(row["parameter_set"]) for row in horizon_rows}),
            "horizons": sorted({int(row["horizon_checkups"]) for row in horizon_rows}),
        },
        "warnings": sorted(set(warnings)),
        "outputs": {"report": str(out_path), "coverage": str(coverage_out)},
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def capacity_horizon_coverage_rows(
    horizon_rows: list[dict[str, Any]],
    interval_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    horizons = sorted({int(row["horizon_checkups"]) for row in horizon_rows})
    if not horizons:
        horizons = list(DEFAULT_HORIZONS)
    starts_by_cell = {
        cell_id: sorted({int(row["checkup_k"]) for row in rows})
        for cell_id, rows in _group_by_cell(interval_rows).items()
    }
    points_by_cell = {
        cell_id: sorted({int(row["checkup_k"]) for row in rows} | {int(row["checkup_k_next"]) for row in rows})
        for cell_id, rows in _group_by_cell(interval_rows).items()
    }
    observed_by_horizon: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in horizon_rows:
        observed_by_horizon[int(row["horizon_checkups"])].append(row)

    output = []
    for horizon in horizons:
        possible = 0
        for cell_id, starts in starts_by_cell.items():
            available = set(points_by_cell[cell_id])
            for start in starts:
                possible += int(start + horizon in available)
        rows = observed_by_horizon[horizon]
        c_rate_rows = [row for row in rows if int(row["c_rate_holdout_fold"]) != 0]
        profile_rows = [row for row in rows if int(row["profile_holdout_fold"]) != 0]
        output.append(
            {
                "horizon_checkups": horizon,
                "row_count": len(rows),
                "possible_start_rows": possible,
                "missing_or_censored_rows": max(possible - len(rows), 0),
                "cells": len({str(row["cell_id"]) for row in rows}),
                "parameter_sets": len({int(row["parameter_set"]) for row in rows}),
                "c_rate_holdout_rows": len(c_rate_rows),
                "c_rate_holdout_parameter_sets": len({int(row["parameter_set"]) for row in c_rate_rows}),
                "profile_holdout_rows": len(profile_rows),
                "profile_holdout_parameter_sets": len({int(row["parameter_set"]) for row in profile_rows}),
            }
        )
    return output


def _cell_horizon_rows(cell_rows: list[dict[str, Any]], horizons: tuple[int, ...]) -> list[dict[str, Any]]:
    ordered = sorted(cell_rows, key=lambda row: int(row["checkup_k"]))
    if not ordered:
        return []
    first_t = _as_float(ordered[0].get("t_result_k_s"), default=0.0)
    first_capacity = _as_float(ordered[0].get("capacity_Ah_k"))
    intervals_by_start = {int(row["checkup_k"]): row for row in ordered}
    points: dict[int, dict[str, float]] = {}
    cumulative_efc = 0.0
    cumulative_q = 0.0
    prior_delta_by_k: dict[int, float | None] = {int(ordered[0]["checkup_k"]): None}
    prior_days_by_k: dict[int, float | None] = {int(ordered[0]["checkup_k"]): None}

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
    for start, row in sorted(intervals_by_start.items()):
        start_point = points.get(start)
        if start_point is None:
            continue
        for horizon in horizons:
            target = start + horizon
            target_point = points.get(target)
            span = [intervals_by_start.get(k) for k in range(start, target)]
            if target_point is None or any(item is None for item in span):
                continue
            span_rows = [item for item in span if item is not None]
            capacity_k = _as_float(start_point.get("capacity"))
            capacity_kh = _as_float(target_point.get("capacity"))
            prior_delta = prior_delta_by_k.get(start)
            prior_days = prior_days_by_k.get(start)
            quality_flags = sorted(
                {
                    flag
                    for span_row in span_rows
                    for flag in str(span_row.get("quality_flags", "")).split(";")
                    if flag
                }
            )
            if prior_delta is None or not math.isfinite(prior_delta):
                quality_flags.append("no_prior_delta")
            output.append(
                {
                    "cell_id": str(row["cell_id"]),
                    "parameter_set": int(row["parameter_set"]),
                    "replicate_id": int(row["replicate_id"]),
                    "checkup_k": start,
                    "target_checkup_k": target,
                    "horizon_checkups": horizon,
                    "capacity_Ah_k": capacity_k,
                    "capacity_Ah_kh": capacity_kh,
                    "delta_capacity_Ah_h": capacity_kh - capacity_k,
                    "soh_k": _safe_ratio(capacity_k, first_capacity),
                    "soh_kh": _safe_ratio(capacity_kh, first_capacity),
                    "calendar_day_k": (_as_float(start_point.get("t_s")) - first_t) / 86400.0,
                    "horizon_days": (_as_float(target_point.get("t_s")) - _as_float(start_point.get("t_s"))) / 86400.0,
                    "cumulative_efc_k": _as_float(start_point.get("cumulative_efc")),
                    "cumulative_q_Ah_k": _as_float(start_point.get("cumulative_q")),
                    "prior_delta_capacity_Ah": prior_delta,
                    "prior_capacity_slope_per_checkup": prior_delta,
                    "prior_capacity_slope_per_day": _safe_ratio(prior_delta, prior_days),
                    "nominal_temperature_C": _as_float(row.get("nominal_temperature_C")),
                    "voltage_window_family": str(row.get("voltage_window_family", "")),
                    "nominal_charge_C_rate": _as_float(row.get("nominal_charge_C_rate")),
                    "nominal_discharge_C_rate": _as_float(row.get("nominal_discharge_C_rate")),
                    "profile_label": str(row.get("profile_label", "")),
                    "aging_mode": str(row.get("aging_mode", "")),
                    "condition_fold": int(row["condition_fold"]),
                    "temperature_holdout_fold": int(row["temperature_holdout_fold"]),
                    "c_rate_holdout_fold": int(row["c_rate_holdout_fold"]),
                    "profile_holdout_fold": int(row["profile_holdout_fold"]),
                    "voltage_window_holdout_fold": int(row["voltage_window_holdout_fold"]),
                    "horizon_interval_count": len(span_rows),
                    "horizon_duration_h": _sum_numeric(span_rows, "duration_h"),
                    "horizon_calendar_days": _sum_numeric(span_rows, "calendar_days"),
                    "horizon_log_age_efc_delta": _sum_numeric(span_rows, "log_age_efc_delta"),
                    "horizon_log_age_delta_q_Ah": _sum_numeric(span_rows, "log_age_delta_q_Ah"),
                    "horizon_log_age_row_count": int(sum(int(item.get("log_age_row_count", 0) or 0) for item in span_rows)),
                    "event_observed": True,
                    "quality_flags": ";".join(sorted(set(quality_flags))) if quality_flags else "none",
                    "schema_version": SCHEMA_VERSION,
                }
            )
    return output


def _group_by_cell(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["cell_id"])].append(row)
    return grouped


def _sum_numeric(rows: list[dict[str, Any]], column: str) -> float | None:
    values = [_as_float(row.get(column)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) if finite else None


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
    num = _as_float(numerator)
    den = _as_float(denominator)
    if not math.isfinite(num) or not math.isfinite(den) or abs(den) <= 1e-12:
        return None
    return num / den


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
