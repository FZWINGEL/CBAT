"""Build the Gate 2 interval table from EOC, condition, split, and LOG_AGE products."""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from mbp.data.schema_contracts import INTERVAL_TABLE_SCHEMA, validate_table

SCHEMA_VERSION = "gate2.interval.v1"

LOG_AGE_COLUMNS = [
    "cell_id",
    "timestamp_s",
    "v_raw_V",
    "i_raw_A",
    "t_cell_degC",
    "soc_est",
    "delta_q_Ah",
    "EFC",
    "cap_aged_est_Ah",
    "R0_mOhm",
    "R1_mOhm",
]


@dataclass(frozen=True)
class IntervalKey:
    cell_id: str
    checkup_k: int


@dataclass
class LogAgeAccumulator:
    row_count: int = 0
    min_timestamp_s: float | None = None
    max_timestamp_s: float | None = None
    min_efc: float | None = None
    max_efc: float | None = None
    min_delta_q: float | None = None
    max_delta_q: float | None = None
    voltage_sum: float = 0.0
    voltage_count: int = 0
    min_voltage: float | None = None
    max_voltage: float | None = None
    temperature_sum: float = 0.0
    temperature_count: int = 0
    min_temperature: float | None = None
    max_temperature: float | None = None
    current_sum: float = 0.0
    current_count: int = 0
    abs_current_sum: float = 0.0
    abs_current_count: int = 0
    max_abs_current: float | None = None
    soc_sum: float = 0.0
    soc_count: int = 0
    min_soc: float | None = None
    max_soc: float | None = None
    capacity_diag_rows_masked: int = 0
    r0_diag_rows_masked: int = 0
    r1_diag_rows_masked: int = 0

    def update(self, table: pa.Table) -> None:
        self.row_count += table.num_rows
        self.min_timestamp_s = _min_value(self.min_timestamp_s, table, "timestamp_s")
        self.max_timestamp_s = _max_value(self.max_timestamp_s, table, "timestamp_s")
        self.min_efc = _min_value(self.min_efc, table, "EFC")
        self.max_efc = _max_value(self.max_efc, table, "EFC")
        self.min_delta_q = _min_value(self.min_delta_q, table, "delta_q_Ah")
        self.max_delta_q = _max_value(self.max_delta_q, table, "delta_q_Ah")
        self.voltage_sum, self.voltage_count = _sum_count(
            self.voltage_sum, self.voltage_count, table, "v_raw_V"
        )
        self.min_voltage = _min_value(self.min_voltage, table, "v_raw_V")
        self.max_voltage = _max_value(self.max_voltage, table, "v_raw_V")
        self.temperature_sum, self.temperature_count = _sum_count(
            self.temperature_sum, self.temperature_count, table, "t_cell_degC"
        )
        self.min_temperature = _min_value(self.min_temperature, table, "t_cell_degC")
        self.max_temperature = _max_value(self.max_temperature, table, "t_cell_degC")
        self.current_sum, self.current_count = _sum_count(
            self.current_sum, self.current_count, table, "i_raw_A"
        )
        abs_current = pc.abs(table.column("i_raw_A"))
        self.abs_current_sum += float(pc.sum(abs_current).as_py() or 0.0)
        self.abs_current_count += int(pc.count(abs_current, mode="only_valid").as_py() or 0)
        abs_max = pc.max(abs_current).as_py()
        if abs_max is not None:
            self.max_abs_current = (
                float(abs_max)
                if self.max_abs_current is None
                else max(self.max_abs_current, float(abs_max))
            )
        self.soc_sum, self.soc_count = _sum_count(self.soc_sum, self.soc_count, table, "soc_est")
        self.min_soc = _min_value(self.min_soc, table, "soc_est")
        self.max_soc = _max_value(self.max_soc, table, "soc_est")
        self.capacity_diag_rows_masked += _nonnull_count(table, "cap_aged_est_Ah")
        self.r0_diag_rows_masked += _nonnull_count(table, "R0_mOhm")
        self.r1_diag_rows_masked += _nonnull_count(table, "R1_mOhm")


@dataclass
class MonotonicityAccumulator:
    violation_count: int = 0
    timestamp_decrease_count: int = 0
    efc_decrease_count: int = 0
    max_timestamp_drop_s: float = 0.0
    max_efc_drop: float = 0.0

    def update(self, violation_type: str, timestamp_drop: float, efc_drop: float) -> None:
        self.violation_count += 1
        if violation_type in ("timestamp_decrease", "both"):
            self.timestamp_decrease_count += 1
        if violation_type in ("efc_decrease", "both"):
            self.efc_decrease_count += 1
        self.max_timestamp_drop_s = max(self.max_timestamp_drop_s, timestamp_drop)
        self.max_efc_drop = max(self.max_efc_drop, efc_drop)


def build_interval_table(
    interim_dir: Path,
    out_path: Path,
    monotonicity_violations_path: Path | None = None,
) -> pa.Table:
    """Build and write one row per adjacent EOC check-up interval."""
    condition_path = interim_dir / "cell_condition_table.parquet"
    checkup_path = interim_dir / "checkup_event_table.parquet"
    split_path = interim_dir.parent / "splits" / "split_registry_v1.parquet"
    log_age_path = interim_dir / "modality_table_log_age.parquet"

    for path in (condition_path, checkup_path, split_path, log_age_path):
        if not path.exists():
            raise FileNotFoundError(f"Required interval input not found: {path}")

    condition_by_cell = _table_by_cell(pq.read_table(condition_path))
    split_by_cell = _table_by_cell(pq.read_table(split_path))
    checkup_table = pq.read_table(checkup_path)
    interval_rows = _build_interval_spine(checkup_table, condition_by_cell, split_by_cell)
    accumulators = {IntervalKey(row["cell_id"], row["checkup_k"]): LogAgeAccumulator() for row in interval_rows}
    monotonicity = {
        IntervalKey(row["cell_id"], row["checkup_k"]): MonotonicityAccumulator()
        for row in interval_rows
    }

    intervals_by_cell: dict[str, list[dict]] = {}
    for row in interval_rows:
        intervals_by_cell.setdefault(row["cell_id"], []).append(row)

    _scan_log_age(log_age_path, intervals_by_cell, accumulators)
    if monotonicity_violations_path and monotonicity_violations_path.exists():
        _map_monotonicity_violations(
            monotonicity_violations_path, intervals_by_cell, monotonicity
        )

    output = {field.name: [] for field in INTERVAL_TABLE_SCHEMA}
    for row in interval_rows:
        acc = accumulators[IntervalKey(row["cell_id"], row["checkup_k"])]
        mono = monotonicity[IntervalKey(row["cell_id"], row["checkup_k"])]
        quality_flags = []
        if acc.row_count == 0:
            quality_flags.append("LOG_AGE_missing_interval")
        if (
            acc.capacity_diag_rows_masked
            or acc.r0_diag_rows_masked
            or acc.r1_diag_rows_masked
        ):
            quality_flags.append("LOG_AGE_inserted_diagnostics_masked")
        if mono.violation_count:
            quality_flags.append("LOG_AGE_monotonicity_violation")

        values = {
            **row,
            "log_age_row_count": acc.row_count,
            "log_age_elapsed_s": _delta(acc.min_timestamp_s, acc.max_timestamp_s),
            "log_age_efc_delta": _delta(acc.min_efc, acc.max_efc),
            "log_age_delta_q_Ah": _delta(acc.min_delta_q, acc.max_delta_q),
            "log_age_mean_voltage_V": _mean(acc.voltage_sum, acc.voltage_count),
            "log_age_min_voltage_V": acc.min_voltage,
            "log_age_max_voltage_V": acc.max_voltage,
            "log_age_mean_temperature_C": _mean(acc.temperature_sum, acc.temperature_count),
            "log_age_min_temperature_C": acc.min_temperature,
            "log_age_max_temperature_C": acc.max_temperature,
            "log_age_mean_current_A": _mean(acc.current_sum, acc.current_count),
            "log_age_mean_abs_current_A": _mean(acc.abs_current_sum, acc.abs_current_count),
            "log_age_max_abs_current_A": acc.max_abs_current,
            "log_age_mean_soc": _mean(acc.soc_sum, acc.soc_count),
            "log_age_min_soc": acc.min_soc,
            "log_age_max_soc": acc.max_soc,
            "log_age_capacity_diag_rows_masked": acc.capacity_diag_rows_masked,
            "log_age_r0_diag_rows_masked": acc.r0_diag_rows_masked,
            "log_age_r1_diag_rows_masked": acc.r1_diag_rows_masked,
            "LOG_AGE_available": acc.row_count > 0,
            "log_age_monotonicity_violation_count": mono.violation_count,
            "log_age_timestamp_decrease_count": mono.timestamp_decrease_count,
            "log_age_efc_decrease_count": mono.efc_decrease_count,
            "log_age_max_timestamp_drop_s": mono.max_timestamp_drop_s,
            "log_age_max_efc_drop": mono.max_efc_drop,
            "LOG_AGE_monotonicity_clean": mono.violation_count == 0,
            "quality_flags": ";".join(quality_flags),
            "schema_version": SCHEMA_VERSION,
        }
        for field in INTERVAL_TABLE_SCHEMA:
            output[field.name].append(values[field.name])

    table = pa.Table.from_pydict(output, schema=INTERVAL_TABLE_SCHEMA)
    if not validate_table(table, INTERVAL_TABLE_SCHEMA):
        raise TypeError("Generated interval table does not match INTERVAL_TABLE_SCHEMA.")

    metadata = {
        b"schema_version": SCHEMA_VERSION.encode(),
        b"split_registry_sha256": _sha256(split_path).encode(),
        b"split_registry_path": str(split_path).encode(),
        b"log_age_path": str(log_age_path).encode(),
    }
    if monotonicity_violations_path and monotonicity_violations_path.exists():
        metadata[b"log_age_monotonicity_violations_path"] = str(
            monotonicity_violations_path
        ).encode()
    table = table.replace_schema_metadata(metadata)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table


def _build_interval_spine(
    checkup_table: pa.Table, condition_by_cell: dict[str, dict], split_by_cell: dict[str, dict]
) -> list[dict]:
    by_cell: dict[str, list[dict]] = {}
    for row in checkup_table.to_pylist():
        by_cell.setdefault(row["cell_id"], []).append(row)

    rows: list[dict] = []
    for cell_id in sorted(by_cell):
        events = sorted(by_cell[cell_id], key=lambda row: (row["checkup_k"], row["timestamp"]))
        if not events:
            continue
        log_age_zero_s = float(events[0]["timestamp"])
        for left, right in zip(events, events[1:]):
            if right["checkup_k"] <= left["checkup_k"]:
                continue
            condition = condition_by_cell[cell_id]
            split = split_by_cell[cell_id]
            duration_s = float(right["timestamp"]) - float(left["timestamp"])
            rows.append(
                {
                    "cell_id": cell_id,
                    "parameter_set": int(left["parameter_set"]),
                    "replicate_id": int(left["replicate_id"]),
                    "aging_mode": condition["aging_mode"],
                    "nominal_temperature_C": float(condition["nominal_temperature_C"]),
                    "voltage_window": condition["voltage_window"],
                    "voltage_window_family": condition.get(
                        "voltage_window_family", condition["voltage_window"]
                    ),
                    "soc_window_approx": condition["soc_window_approx"],
                    "nominal_charge_C_rate": float(condition["nominal_charge_C_rate"]),
                    "nominal_discharge_C_rate": float(condition["nominal_discharge_C_rate"]),
                    "profile_label": condition["profile_label"],
                    "checkup_k": int(left["checkup_k"]),
                    "checkup_k_next": int(right["checkup_k"]),
                    "t_result_k_s": float(left["timestamp"]),
                    "t_result_k1_s": float(right["timestamp"]),
                    "_log_age_window_start_s": float(left["timestamp"]) - log_age_zero_s,
                    "_log_age_window_end_s": float(right["timestamp"]) - log_age_zero_s,
                    "duration_s": duration_s,
                    "duration_h": duration_s / 3600.0,
                    "calendar_days": duration_s / 86400.0,
                    "capacity_Ah_k": float(left["capacity_Ah"]),
                    "capacity_Ah_k1": float(right["capacity_Ah"]),
                    "delta_capacity_Ah": float(right["capacity_Ah"]) - float(left["capacity_Ah"]),
                    "delta_capacity_soh": float(right["capacity_soh"]) - float(left["capacity_soh"]),
                    "condition_fold": int(split["condition_fold"]),
                    "temperature_holdout_fold": int(split["temperature_holdout_fold"]),
                    "voltage_window_holdout_fold": int(
                        split.get(
                            "voltage_window_holdout_fold",
                            split["soc_window_holdout_fold"],
                        )
                    ),
                    "soc_window_holdout_fold": int(split["soc_window_holdout_fold"]),
                    "c_rate_holdout_fold": int(split["c_rate_holdout_fold"]),
                    "profile_holdout_fold": int(split["profile_holdout_fold"]),
                    "replicate_calibration_fold": int(split["replicate_calibration_fold"]),
                    "time_horizon_fold": int(split["time_horizon_fold"]),
                }
            )
    return rows


def _scan_log_age(
    log_age_path: Path,
    intervals_by_cell: dict[str, list[dict]],
    accumulators: dict[IntervalKey, LogAgeAccumulator],
) -> None:
    parquet_file = pq.ParquetFile(log_age_path)
    cell_idx = parquet_file.schema_arrow.get_field_index("cell_id")
    time_idx = parquet_file.schema_arrow.get_field_index("timestamp_s")

    for rg_idx in range(parquet_file.metadata.num_row_groups):
        row_group = parquet_file.metadata.row_group(rg_idx)
        cell_stats = row_group.column(cell_idx).statistics
        time_stats = row_group.column(time_idx).statistics
        candidate_cells = None
        if cell_stats and cell_stats.min is not None and cell_stats.max is not None:
            if cell_stats.min == cell_stats.max:
                candidate_cells = {str(cell_stats.min)}
                if not (candidate_cells & intervals_by_cell.keys()):
                    continue

        min_t = None
        max_t = None
        if time_stats and time_stats.min is not None and time_stats.max is not None:
            min_t = float(time_stats.min)
            max_t = float(time_stats.max)
            if not any(
                interval["_log_age_window_start_s"] < max_t
                and interval["_log_age_window_end_s"] >= min_t
                for cell in (candidate_cells or intervals_by_cell.keys())
                for interval in intervals_by_cell.get(cell, [])
            ):
                continue

        table = parquet_file.read_row_group(rg_idx, columns=LOG_AGE_COLUMNS)
        if candidate_cells is None:
            candidate_cells = set(pc.unique(table.column("cell_id")).to_pylist())

        timestamps = table.column("timestamp_s")
        for cell_id in candidate_cells:
            intervals = intervals_by_cell.get(cell_id, [])
            if min_t is not None and max_t is not None:
                intervals = [
                    interval
                    for interval in intervals
                    if interval["_log_age_window_start_s"] < max_t
                    and interval["_log_age_window_end_s"] >= min_t
                ]
            if not intervals:
                continue
            cell_mask = pc.equal(table.column("cell_id"), cell_id)
            for interval in intervals:
                after_start = pc.greater(timestamps, interval["_log_age_window_start_s"])
                before_end = pc.less_equal(timestamps, interval["_log_age_window_end_s"])
                mask = pc.and_(cell_mask, pc.and_(after_start, before_end))
                filtered = table.filter(mask)
                if filtered.num_rows:
                    accumulators[IntervalKey(cell_id, interval["checkup_k"])].update(filtered)


def _map_monotonicity_violations(
    violations_path: Path,
    intervals_by_cell: dict[str, list[dict]],
    accumulators: dict[IntervalKey, MonotonicityAccumulator],
) -> None:
    table = pq.read_table(violations_path)
    for violation in table.to_pylist():
        cell_id = violation["cell_id"]
        timestamp = float(violation["current_timestamp_s"])
        for interval in intervals_by_cell.get(cell_id, []):
            if interval["_log_age_window_start_s"] < timestamp <= interval["_log_age_window_end_s"]:
                accumulators[IntervalKey(cell_id, interval["checkup_k"])].update(
                    str(violation["violation_type"]),
                    max(0.0, -float(violation["delta_timestamp_s"])),
                    max(0.0, -float(violation["delta_EFC"])),
                )
                break


def _table_by_cell(table: pa.Table) -> dict[str, dict]:
    return {row["cell_id"]: row for row in table.to_pylist()}


def _min_value(current: float | None, table: pa.Table, column: str) -> float | None:
    value = pc.min(table.column(column)).as_py()
    if value is None:
        return current
    value = float(value)
    return value if current is None else min(current, value)


def _max_value(current: float | None, table: pa.Table, column: str) -> float | None:
    value = pc.max(table.column(column)).as_py()
    if value is None:
        return current
    value = float(value)
    return value if current is None else max(current, value)


def _sum_count(current_sum: float, current_count: int, table: pa.Table, column: str) -> tuple[float, int]:
    array = table.column(column)
    return (
        current_sum + float(pc.sum(array).as_py() or 0.0),
        current_count + int(pc.count(array, mode="only_valid").as_py() or 0),
    )


def _nonnull_count(table: pa.Table, column: str) -> int:
    return int(pc.count(table.column(column), mode="only_valid").as_py() or 0)


def _mean(total: float, count: int) -> float | None:
    return total / count if count else None


def _delta(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    return end - start


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_interval_qa(
    interval_table_path: Path,
    out_path: Path,
    checkup_table_path: Path | None = None,
    duration_tolerance_s: float = 1.0,
) -> dict[str, object]:
    """Write a JSON QA report for the interval table."""
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    if checkup_table_path is None:
        checkup_table_path = interval_table_path.parent / "checkup_event_table.parquet"
    if not checkup_table_path.exists():
        raise FileNotFoundError(f"Check-up event table not found: {checkup_table_path}")

    interval_table = pq.read_table(interval_table_path)
    checkup_table = pq.read_table(checkup_table_path)
    rows = interval_table.to_pylist()
    checkups = checkup_table.to_pylist()
    cells_with_checkups = {row["cell_id"] for row in checkups}
    expected_intervals = len(checkups) - len(cells_with_checkups)

    failures: list[str] = []
    quality_counts: Counter[str] = Counter()
    log_age_available = 0
    zero_log_age_rows = 0
    affected_monotonicity = 0
    non_cohort_cells = []

    for row in rows:
        cell_id = str(row["cell_id"])
        if not _is_cohort_cell_id(cell_id):
            non_cohort_cells.append(cell_id)
        if row["duration_s"] <= 0:
            failures.append(f"{cell_id} checkup {row['checkup_k']}: duration_s <= 0")
        if not (0 < row["calendar_days"] < 5000):
            failures.append(f"{cell_id} checkup {row['checkup_k']}: calendar_days unreasonable")
        if row["LOG_AGE_available"]:
            log_age_available += 1
        if row["log_age_row_count"] == 0:
            zero_log_age_rows += 1
        elapsed = row.get("log_age_elapsed_s")
        if elapsed is not None and elapsed > row["duration_s"] + duration_tolerance_s:
            failures.append(f"{cell_id} checkup {row['checkup_k']}: LOG_AGE elapsed exceeds interval")
        if row.get("log_age_efc_delta") is not None and row["log_age_efc_delta"] < 0:
            failures.append(f"{cell_id} checkup {row['checkup_k']}: negative LOG_AGE EFC delta")
        if row.get("log_age_monotonicity_violation_count", 0) > 0:
            affected_monotonicity += 1
        flags = str(row.get("quality_flags") or "")
        for flag in [f for f in flags.split(";") if f]:
            quality_counts[flag] += 1

    if len(rows) != expected_intervals:
        failures.append(
            f"Expected {expected_intervals} intervals from {len(checkups)} check-ups and "
            f"{len(cells_with_checkups)} cells, found {len(rows)}"
        )
    if non_cohort_cells:
        failures.append(f"Non-cohort cells present: {sorted(set(non_cohort_cells))[:10]}")

    report = {
        "status": "failed" if failures else "passed",
        "interval_table": str(interval_table_path),
        "checkup_event_table": str(checkup_table_path),
        "row_count": len(rows),
        "expected_interval_count": expected_intervals,
        "checkup_event_rows": len(checkups),
        "cells_with_checkups": len(cells_with_checkups),
        "non_cohort_cell_count": len(set(non_cohort_cells)),
        "duration_positive": not any(row["duration_s"] <= 0 for row in rows),
        "LOG_AGE_available_fraction": log_age_available / len(rows) if rows else 0.0,
        "intervals_with_log_age_row_count_zero": zero_log_age_rows,
        "intervals_with_monotonicity_violations": affected_monotonicity,
        "masked_diagnostic_rows": {
            "cap_aged_est_Ah": sum(row["log_age_capacity_diag_rows_masked"] for row in rows),
            "R0_mOhm": sum(row["log_age_r0_diag_rows_masked"] for row in rows),
            "R1_mOhm": sum(row["log_age_r1_diag_rows_masked"] for row in rows),
        },
        "quality_flags_distribution": dict(sorted(quality_counts.items())),
        "failures": failures[:100],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _is_cohort_cell_id(cell_id: str) -> bool:
    import re

    match = re.match(r"^P(\d{3})_([1-3])$", cell_id)
    return bool(match and 1 <= int(match.group(1)) <= 76)
