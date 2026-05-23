"""PULSE QA and canonical interval target products."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import PULSE_TARGET_TABLE_SCHEMA, validate_table

SCHEMA_VERSION = "gate7.pulse_targets.v1"
POLICY_VERSION = "pulse_target_policy.v1"


def write_pulse_qa_report(
    pulse_summary_path: Path,
    checkup_table_path: Path,
    out_path: Path,
    coverage_out_path: Path,
    alignment_out_path: Path,
    *,
    canonical_soc_percent: float = 50.0,
    canonical_temperature_context: str = "RT",
    large_alignment_delta_s: float = 86_400.0,
) -> dict[str, Any]:
    """Write PULSE target coverage and alignment QA reports."""
    pulse_rows = _read_parquet_rows(pulse_summary_path)
    checkup_rows = _read_parquet_rows(checkup_table_path)
    checkup_keys = {(str(row["cell_id"]), int(row["checkup_k"])) for row in checkup_rows}
    canonical_temp = canonical_temperature_context.upper()

    coverage_rows = _coverage_rows(pulse_rows)
    _write_csv(coverage_out_path, coverage_rows)

    alignment_report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "alignment_method_counts": dict(Counter(str(row.get("alignment_method", "")) for row in pulse_rows)),
        "alignment_delta_s": _numeric_summary([_as_float(row.get("alignment_delta_s")) for row in pulse_rows]),
        "large_alignment_delta_s": large_alignment_delta_s,
        "large_alignment_delta_rows": sum(
            _as_float(row.get("alignment_delta_s")) > large_alignment_delta_s
            for row in pulse_rows
        ),
    }
    alignment_out_path.parent.mkdir(parents=True, exist_ok=True)
    alignment_out_path.write_text(json.dumps(alignment_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    canonical_rows = [
        row
        for row in pulse_rows
        if _same_soc(row.get("soc_percent"), canonical_soc_percent)
        and str(row.get("temperature_context", "")).upper() == canonical_temp
    ]
    canonical_keys = {
        (str(row["cell_id"]), int(row["checkup_k"]))
        for row in canonical_rows
    }
    duplicate_keys = _duplicate_target_keys(canonical_rows)
    missing_canonical = sorted(checkup_keys - canonical_keys)
    warnings: list[str] = []
    if missing_canonical:
        warnings.append(f"missing_canonical_target_keys={len(missing_canonical)}")
    if duplicate_keys:
        warnings.append(f"duplicate_canonical_target_keys={len(duplicate_keys)}")
    if alignment_report["large_alignment_delta_rows"]:
        warnings.append(
            f"large_alignment_delta_rows={alignment_report['large_alignment_delta_rows']}"
        )

    report = {
        "status": "passed" if not missing_canonical else "warning",
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "pulse_summary": str(pulse_summary_path),
            "checkup_table": str(checkup_table_path),
        },
        "row_count": len(pulse_rows),
        "unique_cells": len({str(row["cell_id"]) for row in pulse_rows}),
        "checkup_event_rows": len(checkup_rows),
        "canonical_target": {
            "soc_percent": canonical_soc_percent,
            "temperature_context": canonical_temp,
            "available_cell_checkups": len(canonical_keys),
            "missing_cell_checkups": len(missing_canonical),
            "duplicate_cell_checkups": len(duplicate_keys),
        },
        "soc_context_counts": dict(Counter(_soc_label(row.get("soc_percent")) for row in pulse_rows)),
        "temperature_context_counts": dict(Counter(str(row.get("temperature_context", "")) for row in pulse_rows)),
        "direction_counts": dict(Counter(str(row.get("pulse_direction", "")) for row in pulse_rows)),
        "alignment": alignment_report,
        "warnings": warnings,
        "outputs": {
            "coverage": str(coverage_out_path),
            "alignment": str(alignment_out_path),
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_pulse_target_table(
    pulse_summary_path: Path,
    interval_table_path: Path,
    out_path: Path,
    *,
    soc_percent: float = 50.0,
    temperature_context: str = "RT",
    direction: str = "mean",
) -> pa.Table:
    """Build one canonical PULSE target row per interval."""
    pulse_rows = _read_parquet_rows(pulse_summary_path)
    interval_rows = _read_parquet_rows(interval_table_path)
    canonical = _canonical_by_cell_checkup(
        pulse_rows,
        soc_percent=soc_percent,
        temperature_context=temperature_context,
        direction=direction,
    )
    output_rows: list[dict[str, Any]] = []
    for interval in interval_rows:
        key_k = (str(interval["cell_id"]), int(interval["checkup_k"]))
        key_k1 = (str(interval["cell_id"]), int(interval["checkup_k_next"]))
        pulse_k = canonical.get(key_k)
        pulse_k1 = canonical.get(key_k1)
        flags: list[str] = []
        if pulse_k is None:
            flags.append("missing_pulse_k")
        if pulse_k1 is None:
            flags.append("missing_pulse_k1")
        output_rows.append(
            {
                "cell_id": str(interval["cell_id"]),
                "parameter_set": int(interval["parameter_set"]),
                "replicate_id": int(interval["replicate_id"]),
                "checkup_k": int(interval["checkup_k"]),
                "checkup_k_next": int(interval["checkup_k_next"]),
                "soc_percent": float(soc_percent),
                "temperature_context": temperature_context.upper(),
                "pulse_1s_resistance_k": _maybe(pulse_k, "pulse_1s_resistance"),
                "pulse_1s_resistance_k1": _maybe(pulse_k1, "pulse_1s_resistance"),
                "delta_pulse_1s_resistance": _delta(
                    _maybe(pulse_k, "pulse_1s_resistance"),
                    _maybe(pulse_k1, "pulse_1s_resistance"),
                ),
                "pulse_10ms_resistance_k": _maybe(pulse_k, "pulse_10ms_resistance"),
                "pulse_10ms_resistance_k1": _maybe(pulse_k1, "pulse_10ms_resistance"),
                "delta_pulse_10ms_resistance": _delta(
                    _maybe(pulse_k, "pulse_10ms_resistance"),
                    _maybe(pulse_k1, "pulse_10ms_resistance"),
                ),
                "alignment_delta_s_k": _maybe(pulse_k, "alignment_delta_s"),
                "alignment_delta_s_k1": _maybe(pulse_k1, "alignment_delta_s"),
                "quality_flags": ";".join(flags) if flags else "OK",
                "schema_version": SCHEMA_VERSION,
            }
        )
    table = pa.Table.from_pylist(output_rows, schema=PULSE_TARGET_TABLE_SCHEMA)
    if not validate_table(table, PULSE_TARGET_TABLE_SCHEMA):
        raise ValueError("PULSE target table schema validation failed.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"policy_version": POLICY_VERSION.encode(),
                b"direction": direction.encode(),
                b"pulse_summary_path": str(pulse_summary_path).encode(),
                b"interval_table_path": str(interval_table_path).encode(),
            }
        ),
        out_path,
    )
    return table


def _canonical_by_cell_checkup(
    rows: list[dict[str, Any]],
    *,
    soc_percent: float,
    temperature_context: str,
    direction: str = "mean",
) -> dict[tuple[str, int], dict[str, float]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    temp = temperature_context.upper()
    direction = direction.lower()
    if direction not in {"mean", "charge", "discharge"}:
        raise ValueError("direction must be one of: mean, charge, discharge")
    for row in rows:
        if (
            _same_soc(row.get("soc_percent"), soc_percent)
            and str(row.get("temperature_context", "")).upper() == temp
            and (direction == "mean" or str(row.get("pulse_direction", "")).lower() == direction)
        ):
            grouped[(str(row["cell_id"]), int(row["checkup_k"]))].append(row)
    canonical: dict[tuple[str, int], dict[str, float]] = {}
    for key, values in grouped.items():
        canonical[key] = {
            "pulse_1s_resistance": _mean([_as_float(row.get("pulse_1s_resistance")) for row in values]),
            "pulse_10ms_resistance": _mean([_as_float(row.get("pulse_10ms_resistance")) for row in values]),
            "alignment_delta_s": _mean([_as_float(row.get("alignment_delta_s")) for row in values]),
        }
    return canonical


def write_pulse_alignment_sensitivity_report(
    pulse_summary_path: Path,
    pulse_targets_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out_path: Path,
    *,
    canonical_soc_percent: float = 50.0,
    canonical_temperature_context: str = "RT",
    thresholds_s: tuple[float, ...] = (21_600.0, 43_200.0, 86_400.0, 129_600.0),
) -> dict[str, Any]:
    """Write alignment-threshold coverage diagnostics for canonical PULSE targets."""
    pulse_rows = _read_parquet_rows(pulse_summary_path)
    target_rows = _read_parquet_rows(pulse_targets_path)
    interval_rows = _read_parquet_rows(interval_table_path)
    interval_by_key = {_interval_key(row): row for row in interval_rows}
    canonical_rows = [
        row
        for row in pulse_rows
        if _same_soc(row.get("soc_percent"), canonical_soc_percent)
        and str(row.get("temperature_context", "")).upper() == canonical_temperature_context.upper()
    ]
    grouped_rows: list[dict[str, Any]] = []
    for grouping, column in (
        ("soc", "soc_percent"),
        ("temperature_context", "temperature_context"),
        ("pulse_direction", "pulse_direction"),
        ("cell_id", "cell_id"),
        ("checkup_k", "checkup_k"),
    ):
        buckets: dict[str, list[float]] = defaultdict(list)
        for row in pulse_rows:
            buckets[_group_value(row.get(column))].append(_as_float(row.get("alignment_delta_s")))
        for value, deltas in sorted(buckets.items()):
            grouped_rows.append({"grouping": grouping, "group_value": value, **_numeric_summary(deltas)})
    threshold_rows: list[dict[str, Any]] = []
    all_thresholds = (*thresholds_s, math.inf)
    for threshold in all_thresholds:
        retained = [
            row
            for row in target_rows
            if _target_available_under_threshold(row, threshold)
        ]
        split_counts: Counter[str] = Counter()
        for row in retained:
            interval = interval_by_key.get(_interval_key(row))
            if interval is None:
                continue
            split_counts[f"c_rate={interval.get('c_rate_holdout_fold')}"] += 1
            split_counts[f"profile={interval.get('profile_holdout_fold')}"] += 1
        threshold_rows.append(
            {
                "threshold_s": "all" if math.isinf(threshold) else threshold,
                "retained_intervals": len(retained),
                "missing_intervals": len(target_rows) - len(retained),
                "retained_cells": len({str(row["cell_id"]) for row in retained}),
                "retained_parameter_sets": len(
                    {
                        int(interval_by_key[_interval_key(row)]["parameter_set"])
                        for row in retained
                        if _interval_key(row) in interval_by_key
                    }
                ),
                "c_rate_holdout_rows": split_counts.get("c_rate=1", 0),
                "profile_holdout_rows": split_counts.get("profile=1", 0),
            }
        )
    _write_csv(coverage_out_path, [*grouped_rows, *threshold_rows])
    warnings = [
        f"threshold_{row['threshold_s']}_low_c_rate_coverage"
        for row in threshold_rows
        if row["threshold_s"] != "all" and int(row["c_rate_holdout_rows"]) == 0
    ]
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "pulse_summary": str(pulse_summary_path),
            "pulse_targets": str(pulse_targets_path),
            "interval_table": str(interval_table_path),
        },
        "canonical_alignment_delta_s": _numeric_summary(
            [_as_float(row.get("alignment_delta_s")) for row in canonical_rows]
        ),
        "thresholds": threshold_rows,
        "warnings": warnings,
        "outputs": {"coverage": str(coverage_out_path)},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def write_pulse_missingness_reports(
    pulse_targets_path: Path,
    interval_table_path: Path,
    missing_out_path: Path,
    by_condition_out_path: Path,
    by_split_out_path: Path,
) -> dict[str, Any]:
    """Write condition and split diagnostics for missing canonical PULSE endpoints."""
    targets = _read_parquet_rows(pulse_targets_path)
    intervals = _read_parquet_rows(interval_table_path)
    interval_by_key = {_interval_key(row): row for row in intervals}
    missing_rows: list[dict[str, Any]] = []
    for row in targets:
        if str(row.get("quality_flags")) == "OK":
            continue
        interval = interval_by_key.get(_interval_key(row), {})
        reason = str(row.get("quality_flags", "unknown"))
        missing_rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": interval.get("parameter_set"),
                "replicate_id": interval.get("replicate_id"),
                "checkup_k": row["checkup_k"],
                "aging_mode": interval.get("aging_mode"),
                "nominal_temperature_C": interval.get("nominal_temperature_C"),
                "voltage_window_family": interval.get("voltage_window_family"),
                "nominal_charge_C_rate": interval.get("nominal_charge_C_rate"),
                "profile_holdout_fold": interval.get("profile_holdout_fold"),
                "c_rate_holdout_fold": interval.get("c_rate_holdout_fold"),
                "missing_reason": reason,
            }
        )
    _write_csv(missing_out_path, missing_rows)
    _write_csv(by_condition_out_path, _missing_group_rows(missing_rows, "parameter_set"))
    _write_csv(by_split_out_path, _missing_group_rows(missing_rows, "c_rate_holdout_fold") + _missing_group_rows(missing_rows, "profile_holdout_fold"))
    return {"missing_rows": len(missing_rows)}


def _coverage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, str, str, str], int] = Counter()
    for row in rows:
        grouped[
            (
                str(row["cell_id"]),
                int(row["checkup_k"]),
                _soc_label(row.get("soc_percent")),
                str(row.get("temperature_context", "")),
                str(row.get("pulse_direction", "")),
            )
        ] += 1
    return [
        {
            "cell_id": key[0],
            "checkup_k": key[1],
            "soc_percent": key[2],
            "temperature_context": key[3],
            "pulse_direction": key[4],
            "row_count": count,
        }
        for key, count in sorted(grouped.items())
    ]


def _target_available_under_threshold(row: dict[str, Any], threshold_s: float) -> bool:
    required = (
        row.get("delta_pulse_1s_resistance"),
        row.get("alignment_delta_s_k"),
        row.get("alignment_delta_s_k1"),
    )
    if not all(math.isfinite(_as_float(value)) for value in required):
        return False
    if math.isinf(threshold_s):
        return True
    return _as_float(row.get("alignment_delta_s_k")) <= threshold_s and _as_float(row.get("alignment_delta_s_k1")) <= threshold_s


def _missing_group_rows(rows: list[dict[str, Any]], column: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_group_value(row.get(column))].append(row)
    return [
        {
            "grouping": column,
            "group_value": value,
            "missing_rows": len(group),
            "missing_cells": len({str(row["cell_id"]) for row in group}),
            "missing_parameter_sets": len({_group_value(row.get("parameter_set")) for row in group}),
        }
        for value, group in sorted(grouped.items())
    ]


def _alignment_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("alignment_method", ""))].append(_as_float(row.get("alignment_delta_s")))
    return [
        {"alignment_method": method, **_numeric_summary(values)}
        for method, values in sorted(grouped.items())
    ]


def _duplicate_target_keys(rows: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts = Counter((str(row["cell_id"]), int(row["checkup_k"])) for row in rows)
    return [key for key, count in counts.items() if count > 1]


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "median": _percentile(finite, 0.5),
        "p95": _percentile(finite, 0.95),
        "max": finite[-1],
    }


def _percentile(sorted_values: list[float], q: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * q
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return sorted_values[lower]
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (idx - lower)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def _same_soc(value: Any, expected: float) -> bool:
    observed = _as_float(value)
    return math.isfinite(observed) and abs(observed - expected) <= 0.25


def _soc_label(value: Any) -> str:
    observed = _as_float(value)
    return "unknown" if not math.isfinite(observed) else f"{observed:g}"


def _group_value(value: Any) -> str:
    if value is None:
        return "unknown"
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:g}"
    text = str(value).strip()
    return text if text else "unknown"


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _maybe(row: dict[str, Any] | None, column: str) -> float | None:
    if row is None:
        return None
    value = _as_float(row.get(column))
    return value if math.isfinite(value) else None


def _delta(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    return end - start


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan
