"""LOG_AGE-derived scalar stress-feature sidecar for capacity baselines."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from mbp.data.schema_contracts import INTERVAL_STRESS_FEATURES_SCHEMA, validate_table

SCHEMA_VERSION = "gate6.interval_stress_features.v1"
FEATURE_POLICY_VERSION = "log_age_stress_features.v1"
CURRENT_SIGN_POLICY = "positive_current_charge_provisional_abs_current_primary"
CURRENT_SIGN_CONVENTION_CONFIRMED = False
SIGN_DEPENDENT_FEATURES_PROVISIONAL = True
NOMINAL_CAPACITY_AH = 3.0
REST_CURRENT_A = 0.05

LOG_AGE_STRESS_COLUMNS = [
    "cell_id",
    "timestamp_s",
    "v_raw_V",
    "i_raw_A",
    "t_cell_degC",
    "soc_est",
]

STRESS_FEATURE_COLUMNS = [
    field.name
    for field in INTERVAL_STRESS_FEATURES_SCHEMA
    if field.name
    not in {
        "cell_id",
        "parameter_set",
        "replicate_id",
        "checkup_k",
        "checkup_k_next",
        "schema_version",
        "feature_policy_version",
        "current_sign_policy",
        "current_sign_convention_confirmed",
        "sign_dependent_features_provisional",
        "stress_log_age_row_count",
        "stress_duration_h",
    }
]

DWELL_FEATURE_COLUMNS = [
    column
    for column in STRESS_FEATURE_COLUMNS
    if column.startswith("time_") or column.endswith("_time_h")
]

NONNEGATIVE_QA_FEATURE_COLUMNS = tuple(
    sorted(
        set(DWELL_FEATURE_COLUMNS)
        | {
            "mean_charge_current_A",
            "mean_discharge_current_A",
            "log_age_efc_per_day",
        }
    )
)


@dataclass(frozen=True)
class StressIntervalKey:
    cell_id: str
    checkup_k: int
    checkup_k_next: int


@dataclass
class StressAccumulator:
    duration_h: float
    delta_capacity_Ah: float
    calendar_days: float
    log_age_efc_delta: float | None
    log_age_delta_q_Ah: float | None
    row_count: int = 0
    voltage_lt_3p3_count: int = 0
    voltage_3p3_3p6_count: int = 0
    voltage_3p6_3p9_count: int = 0
    voltage_3p9_4p1_count: int = 0
    voltage_ge_4p1_count: int = 0
    temp_lt_5_count: int = 0
    temp_5_15_count: int = 0
    temp_15_30_count: int = 0
    temp_30_40_count: int = 0
    temp_ge_40_count: int = 0
    charge_count: int = 0
    discharge_count: int = 0
    rest_count: int = 0
    abs_current_ge_1c_count: int = 0
    abs_current_ge_1p5c_count: int = 0
    abs_current_ge_5over3c_count: int = 0
    charge_current_ge_1c_count: int = 0
    charge_current_ge_1p5c_count: int = 0
    charge_current_ge_5over3c_count: int = 0
    charge_current_sum: float = 0.0
    discharge_current_abs_sum: float = 0.0
    soc_lt_20_count: int = 0
    soc_20_50_count: int = 0
    soc_50_80_count: int = 0
    soc_ge_80_count: int = 0
    cold_high_charge_count: int = 0
    cold_high_abs_current_count: int = 0
    high_voltage_hot_count: int = 0
    high_soc_hot_count: int = 0
    high_voltage_high_abs_current_count: int = 0
    high_soc_high_abs_current_count: int = 0

    def update(self, table: pa.Table) -> None:
        self.row_count += table.num_rows
        voltage = table.column("v_raw_V")
        temperature = table.column("t_cell_degC")
        current = table.column("i_raw_A")
        soc = table.column("soc_est")
        abs_current = pc.abs(current)

        voltage_lt_3p3 = pc.less(voltage, 3.3)
        voltage_3p3_3p6 = _between(voltage, 3.3, 3.6)
        voltage_3p6_3p9 = _between(voltage, 3.6, 3.9)
        voltage_3p9_4p1 = _between(voltage, 3.9, 4.1)
        voltage_ge_4p1 = pc.greater_equal(voltage, 4.1)
        self.voltage_lt_3p3_count += _mask_count(voltage_lt_3p3)
        self.voltage_3p3_3p6_count += _mask_count(voltage_3p3_3p6)
        self.voltage_3p6_3p9_count += _mask_count(voltage_3p6_3p9)
        self.voltage_3p9_4p1_count += _mask_count(voltage_3p9_4p1)
        self.voltage_ge_4p1_count += _mask_count(voltage_ge_4p1)

        temp_lt_5 = pc.less(temperature, 5.0)
        temp_5_15 = _between(temperature, 5.0, 15.0)
        temp_15_30 = _between(temperature, 15.0, 30.0)
        temp_30_40 = _between(temperature, 30.0, 40.0)
        temp_ge_40 = pc.greater_equal(temperature, 40.0)
        cold = pc.less(temperature, 15.0)
        hot = temp_ge_40
        self.temp_lt_5_count += _mask_count(temp_lt_5)
        self.temp_5_15_count += _mask_count(temp_5_15)
        self.temp_15_30_count += _mask_count(temp_15_30)
        self.temp_30_40_count += _mask_count(temp_30_40)
        self.temp_ge_40_count += _mask_count(temp_ge_40)

        charge = pc.greater(current, REST_CURRENT_A)
        discharge = pc.less(current, -REST_CURRENT_A)
        rest = pc.less_equal(abs_current, REST_CURRENT_A)
        abs_ge_1c = pc.greater_equal(abs_current, NOMINAL_CAPACITY_AH)
        abs_ge_1p5c = pc.greater_equal(abs_current, 1.5 * NOMINAL_CAPACITY_AH)
        abs_ge_5over3c = pc.greater_equal(abs_current, (5.0 / 3.0) * NOMINAL_CAPACITY_AH)
        charge_ge_1c = pc.greater_equal(current, NOMINAL_CAPACITY_AH)
        charge_ge_1p5c = pc.greater_equal(current, 1.5 * NOMINAL_CAPACITY_AH)
        charge_ge_5over3c = pc.greater_equal(current, (5.0 / 3.0) * NOMINAL_CAPACITY_AH)
        self.charge_count += _mask_count(charge)
        self.discharge_count += _mask_count(discharge)
        self.rest_count += _mask_count(rest)
        self.abs_current_ge_1c_count += _mask_count(abs_ge_1c)
        self.abs_current_ge_1p5c_count += _mask_count(abs_ge_1p5c)
        self.abs_current_ge_5over3c_count += _mask_count(abs_ge_5over3c)
        self.charge_current_ge_1c_count += _mask_count(charge_ge_1c)
        self.charge_current_ge_1p5c_count += _mask_count(charge_ge_1p5c)
        self.charge_current_ge_5over3c_count += _mask_count(charge_ge_5over3c)
        self.charge_current_sum += _sum_where(current, charge)
        self.discharge_current_abs_sum += _sum_where(abs_current, discharge)

        soc_lt_20 = pc.less(soc, 20.0)
        soc_20_50 = _between(soc, 20.0, 50.0)
        soc_50_80 = _between(soc, 50.0, 80.0)
        soc_ge_80 = pc.greater_equal(soc, 80.0)
        self.soc_lt_20_count += _mask_count(soc_lt_20)
        self.soc_20_50_count += _mask_count(soc_20_50)
        self.soc_50_80_count += _mask_count(soc_50_80)
        self.soc_ge_80_count += _mask_count(soc_ge_80)

        self.cold_high_charge_count += _mask_count(pc.and_(cold, charge_ge_1p5c))
        self.cold_high_abs_current_count += _mask_count(pc.and_(cold, abs_ge_1p5c))
        self.high_voltage_hot_count += _mask_count(pc.and_(voltage_ge_4p1, hot))
        self.high_soc_hot_count += _mask_count(pc.and_(soc_ge_80, hot))
        self.high_voltage_high_abs_current_count += _mask_count(
            pc.and_(voltage_ge_4p1, abs_ge_1p5c)
        )
        self.high_soc_high_abs_current_count += _mask_count(pc.and_(soc_ge_80, abs_ge_1p5c))

    def to_features(self) -> dict[str, Any]:
        values = {
            "stress_log_age_row_count": self.row_count,
            "stress_duration_h": self.duration_h,
            "time_voltage_lt_3p3_h": self._hours(self.voltage_lt_3p3_count),
            "time_voltage_3p3_3p6_h": self._hours(self.voltage_3p3_3p6_count),
            "time_voltage_3p6_3p9_h": self._hours(self.voltage_3p6_3p9_count),
            "time_voltage_3p9_4p1_h": self._hours(self.voltage_3p9_4p1_count),
            "time_voltage_ge_4p1_h": self._hours(self.voltage_ge_4p1_count),
            "time_temp_lt_5C_h": self._hours(self.temp_lt_5_count),
            "time_temp_5_15C_h": self._hours(self.temp_5_15_count),
            "time_temp_15_30C_h": self._hours(self.temp_15_30_count),
            "time_temp_30_40C_h": self._hours(self.temp_30_40_count),
            "time_temp_ge_40C_h": self._hours(self.temp_ge_40_count),
            "mean_charge_current_A": _safe_ratio(self.charge_current_sum, self.charge_count),
            "mean_discharge_current_A": _safe_ratio(
                self.discharge_current_abs_sum, self.discharge_count
            ),
            "charge_time_h": self._hours(self.charge_count),
            "discharge_time_h": self._hours(self.discharge_count),
            "rest_time_h": self._hours(self.rest_count),
            "abs_current_ge_1C_time_h": self._hours(self.abs_current_ge_1c_count),
            "abs_current_ge_1p5C_time_h": self._hours(self.abs_current_ge_1p5c_count),
            "abs_current_ge_5over3C_time_h": self._hours(
                self.abs_current_ge_5over3c_count
            ),
            "charge_current_ge_1C_time_h": self._hours(self.charge_current_ge_1c_count),
            "charge_current_ge_1p5C_time_h": self._hours(
                self.charge_current_ge_1p5c_count
            ),
            "charge_current_ge_5over3C_time_h": self._hours(
                self.charge_current_ge_5over3c_count
            ),
            "time_soc_lt_20_h": self._hours(self.soc_lt_20_count),
            "time_soc_20_50_h": self._hours(self.soc_20_50_count),
            "time_soc_50_80_h": self._hours(self.soc_50_80_count),
            "time_soc_ge_80_h": self._hours(self.soc_ge_80_count),
            "cold_high_charge_time_h": self._hours(self.cold_high_charge_count),
            "cold_high_abs_current_time_h": self._hours(self.cold_high_abs_current_count),
            "high_voltage_hot_time_h": self._hours(self.high_voltage_hot_count),
            "high_soc_hot_time_h": self._hours(self.high_soc_hot_count),
            "high_voltage_high_abs_current_time_h": self._hours(
                self.high_voltage_high_abs_current_count
            ),
            "high_soc_high_abs_current_time_h": self._hours(
                self.high_soc_high_abs_current_count
            ),
            "delta_capacity_per_day": _safe_ratio(self.delta_capacity_Ah, self.calendar_days),
            "delta_capacity_per_efc": _safe_ratio(
                self.delta_capacity_Ah, self.log_age_efc_delta
            ),
            "delta_capacity_per_Ah_throughput": _safe_ratio(
                self.delta_capacity_Ah, self.log_age_delta_q_Ah
            ),
            "log_age_efc_per_day": _safe_ratio(self.log_age_efc_delta, self.calendar_days),
        }
        values["high_voltage_time_h"] = values["time_voltage_ge_4p1_h"]
        values["voltage_dwell_weighted_h"] = (
            0.25 * values["time_voltage_3p3_3p6_h"]
            + 0.5 * values["time_voltage_3p6_3p9_h"]
            + values["time_voltage_3p9_4p1_h"]
            + 1.5 * values["time_voltage_ge_4p1_h"]
        )
        values["cold_time_h"] = values["time_temp_lt_5C_h"] + values["time_temp_5_15C_h"]
        values["hot_time_h"] = values["time_temp_ge_40C_h"]
        values["high_soc_time_h"] = values["time_soc_ge_80_h"]
        return values

    def _hours(self, count: int) -> float:
        if self.row_count <= 0:
            return 0.0
        return self.duration_h * count / self.row_count


def build_interval_stress_features(
    interim_dir: Path,
    interval_table_path: Path,
    out_path: Path,
) -> pa.Table:
    """Build the interval stress-feature sidecar from LOG_AGE row groups."""
    log_age_path = interim_dir / "modality_table_log_age.parquet"
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    if not log_age_path.exists():
        raise FileNotFoundError(f"LOG_AGE table not found: {log_age_path}")

    interval_rows = pq.read_table(interval_table_path).to_pylist()
    intervals_by_cell, accumulators = _prepare_intervals(interval_rows)
    _scan_log_age_for_stress(log_age_path, intervals_by_cell, accumulators)

    output = {field.name: [] for field in INTERVAL_STRESS_FEATURES_SCHEMA}
    for row in interval_rows:
        key = StressIntervalKey(
            str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])
        )
        acc = accumulators[key]
        values = {
            "cell_id": str(row["cell_id"]),
            "parameter_set": int(row["parameter_set"]),
            "replicate_id": int(row["replicate_id"]),
            "checkup_k": int(row["checkup_k"]),
            "checkup_k_next": int(row["checkup_k_next"]),
            "schema_version": SCHEMA_VERSION,
            "feature_policy_version": FEATURE_POLICY_VERSION,
            "current_sign_policy": CURRENT_SIGN_POLICY,
            "current_sign_convention_confirmed": CURRENT_SIGN_CONVENTION_CONFIRMED,
            "sign_dependent_features_provisional": SIGN_DEPENDENT_FEATURES_PROVISIONAL,
            **acc.to_features(),
        }
        for field in INTERVAL_STRESS_FEATURES_SCHEMA:
            output[field.name].append(values[field.name])

    table = pa.Table.from_pydict(output, schema=INTERVAL_STRESS_FEATURES_SCHEMA)
    if not validate_table(table, INTERVAL_STRESS_FEATURES_SCHEMA):
        raise TypeError(
            "Generated stress-feature table does not match "
            "INTERVAL_STRESS_FEATURES_SCHEMA."
        )

    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"feature_policy_version": FEATURE_POLICY_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"log_age_path": str(log_age_path).encode(),
            b"current_sign_policy": CURRENT_SIGN_POLICY.encode(),
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    pq.write_table(table, tmp_path)
    tmp_path.replace(out_path)
    return table


def run_stress_feature_qa(
    stress_features_path: Path,
    out_path: Path,
    interval_table_path: Path | None = None,
    duration_tolerance_h: float = 1.0 / 3600.0,
) -> dict[str, Any]:
    """Write a JSON QA report for the interval stress-feature sidecar."""
    if not stress_features_path.exists():
        raise FileNotFoundError(f"Stress-feature table not found: {stress_features_path}")
    if interval_table_path is None:
        candidate = stress_features_path.parent / "interval_table.parquet"
        interval_table_path = candidate if candidate.exists() else None

    table = pq.read_table(stress_features_path)
    rows = table.to_pylist()
    failures: list[str] = []
    if not validate_table(table, INTERVAL_STRESS_FEATURES_SCHEMA):
        failures.append("Stress-feature table schema mismatch.")

    missing_interval_keys = 0
    if interval_table_path is not None and interval_table_path.exists():
        interval_rows = pq.read_table(
            interval_table_path,
            columns=["cell_id", "checkup_k", "checkup_k_next"],
        ).to_pylist()
        stress_keys = {_interval_key(row) for row in rows}
        interval_keys = {_interval_key(row) for row in interval_rows}
        missing_interval_keys = len(interval_keys - stress_keys)
        if missing_interval_keys:
            failures.append(
                f"{missing_interval_keys} interval rows are missing stress features."
            )

    negative_feature_counts: dict[str, int] = {}
    exceeding_duration_counts: dict[str, int] = {}
    voltage_sum_failures = 0
    temperature_sum_failures = 0
    soc_sum_failures = 0
    current_sum_failures = 0
    for row in rows:
        duration_h = _as_float(row.get("stress_duration_h"))
        for column in NONNEGATIVE_QA_FEATURE_COLUMNS:
            value = _as_float(row.get(column))
            if math.isfinite(value) and value < -duration_tolerance_h:
                negative_feature_counts[column] = negative_feature_counts.get(column, 0) + 1
        for column in DWELL_FEATURE_COLUMNS:
            value = _as_float(row.get(column))
            if (
                math.isfinite(value)
                and math.isfinite(duration_h)
                and value > duration_h + duration_tolerance_h
            ):
                exceeding_duration_counts[column] = (
                    exceeding_duration_counts.get(column, 0) + 1
                )
        voltage_sum = sum(
            _as_float(row[column])
            for column in (
                "time_voltage_lt_3p3_h",
                "time_voltage_3p3_3p6_h",
                "time_voltage_3p6_3p9_h",
                "time_voltage_3p9_4p1_h",
                "time_voltage_ge_4p1_h",
            )
        )
        temperature_sum = sum(
            _as_float(row[column])
            for column in (
                "time_temp_lt_5C_h",
                "time_temp_5_15C_h",
                "time_temp_15_30C_h",
                "time_temp_30_40C_h",
                "time_temp_ge_40C_h",
            )
        )
        soc_sum = sum(
            _as_float(row[column])
            for column in (
                "time_soc_lt_20_h",
                "time_soc_20_50_h",
                "time_soc_50_80_h",
                "time_soc_ge_80_h",
            )
        )
        current_sum = sum(
            _as_float(row[column])
            for column in ("charge_time_h", "discharge_time_h", "rest_time_h")
        )
        if abs(voltage_sum - duration_h) > duration_tolerance_h:
            voltage_sum_failures += 1
        if abs(temperature_sum - duration_h) > duration_tolerance_h:
            temperature_sum_failures += 1
        if abs(soc_sum - duration_h) > duration_tolerance_h:
            soc_sum_failures += 1
        if abs(current_sum - duration_h) > duration_tolerance_h:
            current_sum_failures += 1

    if negative_feature_counts:
        failures.append("Negative stress feature values detected.")
    if exceeding_duration_counts:
        failures.append("Stress dwell features exceed interval duration.")
    if voltage_sum_failures:
        failures.append("Voltage dwell bins do not sum to duration.")
    if temperature_sum_failures:
        failures.append("Temperature dwell bins do not sum to duration.")
    if soc_sum_failures:
        failures.append("SOC dwell bins do not sum to duration.")
    if current_sum_failures:
        failures.append("Current dwell bins do not sum to duration.")

    report = {
        "status": "failed" if failures else "passed",
        "stress_features": str(stress_features_path),
        "interval_table": str(interval_table_path) if interval_table_path else None,
        "schema_version": SCHEMA_VERSION,
        "feature_policy_version": FEATURE_POLICY_VERSION,
        "row_count": len(rows),
        "unique_cells": len({str(row["cell_id"]) for row in rows}),
        "unique_parameter_sets": len({int(row["parameter_set"]) for row in rows}),
        "intervals_missing_stress_features": missing_interval_keys,
        "duration_consistency": {
            "voltage_sum_failures": voltage_sum_failures,
            "temperature_sum_failures": temperature_sum_failures,
            "soc_sum_failures": soc_sum_failures,
            "current_sum_failures": current_sum_failures,
            "tolerance_h": duration_tolerance_h,
        },
        "negative_feature_counts": dict(sorted(negative_feature_counts.items())),
        "features_exceeding_duration_counts": dict(
            sorted(exceeding_duration_counts.items())
        ),
        "current_sign_policy": CURRENT_SIGN_POLICY,
        "current_sign_convention_confirmed": CURRENT_SIGN_CONVENTION_CONFIRMED,
        "sign_dependent_features_provisional": SIGN_DEPENDENT_FEATURES_PROVISIONAL,
        "feature_policy_counts": dict(
            sorted(Counter(str(row["feature_policy_version"]) for row in rows).items())
        ),
        "failures": failures,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _prepare_intervals(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[StressIntervalKey, StressAccumulator]]:
    first_result_time_by_cell: dict[str, float] = {}
    for row in rows:
        cell_id = str(row["cell_id"])
        start = float(row["t_result_k_s"])
        first_result_time_by_cell[cell_id] = min(
            start, first_result_time_by_cell.get(cell_id, start)
        )

    intervals_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    accumulators: dict[StressIntervalKey, StressAccumulator] = {}
    for row in rows:
        cell_id = str(row["cell_id"])
        zero_s = first_result_time_by_cell[cell_id]
        interval = dict(row)
        interval["_log_age_window_start_s"] = float(row["t_result_k_s"]) - zero_s
        interval["_log_age_window_end_s"] = float(row["t_result_k1_s"]) - zero_s
        intervals_by_cell[cell_id].append(interval)
        key = StressIntervalKey(cell_id, int(row["checkup_k"]), int(row["checkup_k_next"]))
        accumulators[key] = StressAccumulator(
            duration_h=float(row["duration_h"]),
            delta_capacity_Ah=float(row["delta_capacity_Ah"]),
            calendar_days=float(row["calendar_days"]),
            log_age_efc_delta=_nullable_float(row.get("log_age_efc_delta")),
            log_age_delta_q_Ah=_nullable_float(row.get("log_age_delta_q_Ah")),
        )
    return dict(intervals_by_cell), accumulators


def _scan_log_age_for_stress(
    log_age_path: Path,
    intervals_by_cell: dict[str, list[dict[str, Any]]],
    accumulators: dict[StressIntervalKey, StressAccumulator],
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

        table = parquet_file.read_row_group(rg_idx, columns=LOG_AGE_STRESS_COLUMNS)
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
                    key = StressIntervalKey(
                        cell_id,
                        int(interval["checkup_k"]),
                        int(interval["checkup_k_next"]),
                    )
                    accumulators[key].update(filtered)


def _between(array: Any, lower: float, upper: float) -> Any:
    return pc.and_(pc.greater_equal(array, lower), pc.less(array, upper))


def _mask_count(mask: Any) -> int:
    mask = pc.fill_null(mask, False)
    return int(pc.sum(pc.cast(mask, pa.int64())).as_py() or 0)


def _sum_where(values: Any, mask: Any) -> float:
    mask = pc.fill_null(mask, False)
    filtered = pc.filter(values, mask)
    return float(pc.sum(filtered).as_py() or 0.0)


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return None
    if abs(denominator) <= 1e-12:
        return None
    return numerator / denominator


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _nullable_float(value: Any) -> float | None:
    numeric = _as_float(value)
    return numeric if math.isfinite(numeric) else None
