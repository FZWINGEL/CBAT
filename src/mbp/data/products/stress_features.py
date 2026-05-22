"""LOG_AGE-derived scalar stress-feature sidecar for capacity baselines."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from mbp.data.schema_contracts import INTERVAL_STRESS_FEATURES_SCHEMA, validate_table

SCHEMA_VERSION = "gate6.interval_stress_features.v1_1"
FEATURE_POLICY_VERSION = "log_age_stress_features.v1_1_timestamp_event"
CURRENT_SIGN_POLICY = "positive_current_charge_provisional_abs_current_primary"
CURRENT_SIGN_CONVENTION_CONFIRMED = False
SIGN_DEPENDENT_FEATURES_PROVISIONAL = True
NOMINAL_CAPACITY_AH = 3.0
REST_CURRENT_A = 0.05
MAX_DWELL_GAP_S = 300.0
MAX_DT_SAMPLES_PER_INTERVAL = 4096

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
            "stress_observed_duration_h",
            "stress_coverage_fraction",
            "max_log_age_gap_s",
            "n_charge_events",
            "n_discharge_events",
            "n_rest_events",
            "max_charge_event_h",
            "max_discharge_event_h",
            "max_rest_event_h",
            "max_abs_current_ge_1C_event_h",
            "max_abs_current_ge_1p5C_event_h",
            "max_abs_current_ge_5over3C_event_h",
            "max_cold_high_abs_current_event_h",
            "max_high_voltage_high_abs_current_event_h",
            "max_high_soc_high_abs_current_event_h",
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
    window_start_s: float
    window_end_s: float
    delta_capacity_Ah: float
    calendar_days: float
    log_age_efc_delta: float | None
    log_age_delta_q_Ah: float | None
    row_count: int = 0
    voltage_lt_3p3_h: float = 0.0
    voltage_3p3_3p6_h: float = 0.0
    voltage_3p6_3p9_h: float = 0.0
    voltage_3p9_4p1_h: float = 0.0
    voltage_ge_4p1_h: float = 0.0
    temp_lt_5_h: float = 0.0
    temp_5_15_h: float = 0.0
    temp_15_30_h: float = 0.0
    temp_30_40_h: float = 0.0
    temp_ge_40_h: float = 0.0
    charge_h: float = 0.0
    discharge_h: float = 0.0
    rest_h: float = 0.0
    abs_current_ge_1c_h: float = 0.0
    abs_current_ge_1p5c_h: float = 0.0
    abs_current_ge_5over3c_h: float = 0.0
    charge_current_ge_1c_h: float = 0.0
    charge_current_ge_1p5c_h: float = 0.0
    charge_current_ge_5over3c_h: float = 0.0
    charge_current_sum: float = 0.0
    charge_current_weight_h: float = 0.0
    discharge_current_abs_sum: float = 0.0
    discharge_current_weight_h: float = 0.0
    soc_lt_20_h: float = 0.0
    soc_20_50_h: float = 0.0
    soc_50_80_h: float = 0.0
    soc_ge_80_h: float = 0.0
    cold_high_charge_h: float = 0.0
    cold_high_abs_current_h: float = 0.0
    high_voltage_hot_h: float = 0.0
    high_soc_hot_h: float = 0.0
    high_voltage_high_abs_current_h: float = 0.0
    high_soc_high_abs_current_h: float = 0.0
    observed_duration_h: float = 0.0
    max_log_age_gap_s: float = 0.0
    log_age_gap_count_gt_60s: int = 0
    log_age_gap_count_gt_300s: int = 0
    dt_samples_s: list[float] | None = None
    previous_timestamp_s: float | None = None
    n_charge_events: int = 0
    n_discharge_events: int = 0
    n_rest_events: int = 0
    max_charge_event_h: float = 0.0
    max_discharge_event_h: float = 0.0
    max_rest_event_h: float = 0.0
    max_abs_current_ge_1c_event_h: float = 0.0
    max_abs_current_ge_1p5c_event_h: float = 0.0
    max_abs_current_ge_5over3c_event_h: float = 0.0
    max_cold_high_abs_current_event_h: float = 0.0
    max_high_voltage_high_abs_current_event_h: float = 0.0
    max_high_soc_high_abs_current_event_h: float = 0.0
    _active_events: dict[str, bool] | None = None
    _active_event_h: dict[str, float] | None = None

    def update(self, table: pa.Table) -> None:
        if table.num_rows == 0:
            return
        timestamps = _column_numpy(table, "timestamp_s")
        order = np.argsort(timestamps, kind="stable")
        timestamps = timestamps[order]
        voltage = _column_numpy(table, "v_raw_V")[order]
        temperature = _column_numpy(table, "t_cell_degC")[order]
        current = _column_numpy(table, "i_raw_A")[order]
        soc = _column_numpy(table, "soc_est")[order]

        previous_s = self.previous_timestamp_s
        if previous_s is None:
            previous_s = self.window_start_s
        previous = np.empty_like(timestamps)
        previous[0] = previous_s
        if len(timestamps) > 1:
            previous[1:] = timestamps[:-1]
        raw_dt_s = timestamps - previous
        valid = (timestamps > self.window_start_s) & (timestamps <= self.window_end_s) & (raw_dt_s > 0.0)
        if not bool(np.any(valid)):
            self.previous_timestamp_s = float(timestamps[-1])
            return

        timestamps = timestamps[valid]
        voltage = voltage[valid]
        temperature = temperature[valid]
        current = current[valid]
        soc = soc[valid]
        raw_dt_s = raw_dt_s[valid]
        dt_s = np.minimum(raw_dt_s, MAX_DWELL_GAP_S)
        dt_h = dt_s / 3600.0

        self.row_count += int(len(dt_h))
        self.previous_timestamp_s = float(timestamps[-1])
        self.max_log_age_gap_s = max(self.max_log_age_gap_s, float(np.max(raw_dt_s)))
        self.log_age_gap_count_gt_60s += int(np.sum(raw_dt_s > 60.0))
        self.log_age_gap_count_gt_300s += int(np.sum(raw_dt_s > 300.0))
        if self.dt_samples_s is None:
            self.dt_samples_s = []
        remaining_samples = MAX_DT_SAMPLES_PER_INTERVAL - len(self.dt_samples_s)
        if remaining_samples > 0:
            self.dt_samples_s.extend(float(value) for value in dt_s[:remaining_samples])
        self.observed_duration_h += float(np.sum(dt_h))

        abs_current = np.abs(current)
        voltage_lt_3p3 = voltage < 3.3
        voltage_3p3_3p6 = (voltage >= 3.3) & (voltage < 3.6)
        voltage_3p6_3p9 = (voltage >= 3.6) & (voltage < 3.9)
        voltage_3p9_4p1 = (voltage >= 3.9) & (voltage < 4.1)
        voltage_ge_4p1 = voltage >= 4.1
        self.voltage_lt_3p3_h += _sum_dt(dt_h, voltage_lt_3p3)
        self.voltage_3p3_3p6_h += _sum_dt(dt_h, voltage_3p3_3p6)
        self.voltage_3p6_3p9_h += _sum_dt(dt_h, voltage_3p6_3p9)
        self.voltage_3p9_4p1_h += _sum_dt(dt_h, voltage_3p9_4p1)
        self.voltage_ge_4p1_h += _sum_dt(dt_h, voltage_ge_4p1)

        temp_lt_5 = temperature < 5.0
        temp_5_15 = (temperature >= 5.0) & (temperature < 15.0)
        temp_15_30 = (temperature >= 15.0) & (temperature < 30.0)
        temp_30_40 = (temperature >= 30.0) & (temperature < 40.0)
        temp_ge_40 = temperature >= 40.0
        cold = temperature < 15.0
        hot = temp_ge_40
        self.temp_lt_5_h += _sum_dt(dt_h, temp_lt_5)
        self.temp_5_15_h += _sum_dt(dt_h, temp_5_15)
        self.temp_15_30_h += _sum_dt(dt_h, temp_15_30)
        self.temp_30_40_h += _sum_dt(dt_h, temp_30_40)
        self.temp_ge_40_h += _sum_dt(dt_h, temp_ge_40)

        charge = current > REST_CURRENT_A
        discharge = current < -REST_CURRENT_A
        rest = abs_current <= REST_CURRENT_A
        abs_ge_1c = abs_current >= NOMINAL_CAPACITY_AH
        abs_ge_1p5c = abs_current >= 1.5 * NOMINAL_CAPACITY_AH
        abs_ge_5over3c = abs_current >= (5.0 / 3.0) * NOMINAL_CAPACITY_AH
        charge_ge_1c = current >= NOMINAL_CAPACITY_AH
        charge_ge_1p5c = current >= 1.5 * NOMINAL_CAPACITY_AH
        charge_ge_5over3c = current >= (5.0 / 3.0) * NOMINAL_CAPACITY_AH
        self.charge_h += _sum_dt(dt_h, charge)
        self.discharge_h += _sum_dt(dt_h, discharge)
        self.rest_h += _sum_dt(dt_h, rest)
        self.abs_current_ge_1c_h += _sum_dt(dt_h, abs_ge_1c)
        self.abs_current_ge_1p5c_h += _sum_dt(dt_h, abs_ge_1p5c)
        self.abs_current_ge_5over3c_h += _sum_dt(dt_h, abs_ge_5over3c)
        self.charge_current_ge_1c_h += _sum_dt(dt_h, charge_ge_1c)
        self.charge_current_ge_1p5c_h += _sum_dt(dt_h, charge_ge_1p5c)
        self.charge_current_ge_5over3c_h += _sum_dt(dt_h, charge_ge_5over3c)
        self.charge_current_sum += _sum_dt(current * dt_h, charge)
        self.charge_current_weight_h += _sum_dt(dt_h, charge)
        self.discharge_current_abs_sum += _sum_dt(abs_current * dt_h, discharge)
        self.discharge_current_weight_h += _sum_dt(dt_h, discharge)

        soc_lt_20 = soc < 20.0
        soc_20_50 = (soc >= 20.0) & (soc < 50.0)
        soc_50_80 = (soc >= 50.0) & (soc < 80.0)
        soc_ge_80 = soc >= 80.0
        self.soc_lt_20_h += _sum_dt(dt_h, soc_lt_20)
        self.soc_20_50_h += _sum_dt(dt_h, soc_20_50)
        self.soc_50_80_h += _sum_dt(dt_h, soc_50_80)
        self.soc_ge_80_h += _sum_dt(dt_h, soc_ge_80)

        cold_high_charge = cold & charge_ge_1p5c
        cold_high_abs_current = cold & abs_ge_1p5c
        high_voltage_hot = voltage_ge_4p1 & hot
        high_soc_hot = soc_ge_80 & hot
        high_voltage_high_abs_current = voltage_ge_4p1 & abs_ge_1p5c
        high_soc_high_abs_current = soc_ge_80 & abs_ge_1p5c
        self.cold_high_charge_h += _sum_dt(dt_h, cold_high_charge)
        self.cold_high_abs_current_h += _sum_dt(dt_h, cold_high_abs_current)
        self.high_voltage_hot_h += _sum_dt(dt_h, high_voltage_hot)
        self.high_soc_hot_h += _sum_dt(dt_h, high_soc_hot)
        self.high_voltage_high_abs_current_h += _sum_dt(
            dt_h, high_voltage_high_abs_current
        )
        self.high_soc_high_abs_current_h += _sum_dt(dt_h, high_soc_high_abs_current)

        self._update_event_array("charge", charge, dt_h)
        self._update_event_array("discharge", discharge, dt_h)
        self._update_event_array("rest", rest, dt_h)
        self._update_event_array("abs_current_ge_1c", abs_ge_1c, dt_h)
        self._update_event_array("abs_current_ge_1p5c", abs_ge_1p5c, dt_h)
        self._update_event_array("abs_current_ge_5over3c", abs_ge_5over3c, dt_h)
        self._update_event_array("cold_high_abs_current", cold_high_abs_current, dt_h)
        self._update_event_array(
            "high_voltage_high_abs_current", high_voltage_high_abs_current, dt_h
        )
        self._update_event_array("high_soc_high_abs_current", high_soc_high_abs_current, dt_h)

    def to_features(self) -> dict[str, Any]:
        values = {
            "stress_log_age_row_count": self.row_count,
            "stress_duration_h": self.duration_h,
            "time_voltage_lt_3p3_h": self.voltage_lt_3p3_h,
            "time_voltage_3p3_3p6_h": self.voltage_3p3_3p6_h,
            "time_voltage_3p6_3p9_h": self.voltage_3p6_3p9_h,
            "time_voltage_3p9_4p1_h": self.voltage_3p9_4p1_h,
            "time_voltage_ge_4p1_h": self.voltage_ge_4p1_h,
            "time_temp_lt_5C_h": self.temp_lt_5_h,
            "time_temp_5_15C_h": self.temp_5_15_h,
            "time_temp_15_30C_h": self.temp_15_30_h,
            "time_temp_30_40C_h": self.temp_30_40_h,
            "time_temp_ge_40C_h": self.temp_ge_40_h,
            "mean_charge_current_A": _safe_ratio(
                self.charge_current_sum, self.charge_current_weight_h
            ),
            "mean_discharge_current_A": _safe_ratio(
                self.discharge_current_abs_sum, self.discharge_current_weight_h
            ),
            "charge_time_h": self.charge_h,
            "discharge_time_h": self.discharge_h,
            "rest_time_h": self.rest_h,
            "abs_current_ge_1C_time_h": self.abs_current_ge_1c_h,
            "abs_current_ge_1p5C_time_h": self.abs_current_ge_1p5c_h,
            "abs_current_ge_5over3C_time_h": self.abs_current_ge_5over3c_h,
            "charge_current_ge_1C_time_h": self.charge_current_ge_1c_h,
            "charge_current_ge_1p5C_time_h": self.charge_current_ge_1p5c_h,
            "charge_current_ge_5over3C_time_h": self.charge_current_ge_5over3c_h,
            "time_soc_lt_20_h": self.soc_lt_20_h,
            "time_soc_20_50_h": self.soc_20_50_h,
            "time_soc_50_80_h": self.soc_50_80_h,
            "time_soc_ge_80_h": self.soc_ge_80_h,
            "cold_high_charge_time_h": self.cold_high_charge_h,
            "cold_high_abs_current_time_h": self.cold_high_abs_current_h,
            "high_voltage_hot_time_h": self.high_voltage_hot_h,
            "high_soc_hot_time_h": self.high_soc_hot_h,
            "high_voltage_high_abs_current_time_h": self.high_voltage_high_abs_current_h,
            "high_soc_high_abs_current_time_h": self.high_soc_high_abs_current_h,
            "delta_capacity_per_day": _safe_ratio(self.delta_capacity_Ah, self.calendar_days),
            "delta_capacity_per_efc": _safe_ratio(
                self.delta_capacity_Ah, self.log_age_efc_delta
            ),
            "delta_capacity_per_Ah_throughput": _safe_ratio(
                self.delta_capacity_Ah, self.log_age_delta_q_Ah
            ),
            "log_age_efc_per_day": _safe_ratio(self.log_age_efc_delta, self.calendar_days),
            "stress_observed_duration_h": self.observed_duration_h,
            "stress_coverage_fraction": min(
                1.0, _safe_ratio(self.observed_duration_h, self.duration_h) or 0.0
            ),
            "median_log_age_dt_s": _median(self.dt_samples_s or []),
            "max_log_age_gap_s": self.max_log_age_gap_s,
            "log_age_gap_count_gt_60s": self.log_age_gap_count_gt_60s,
            "log_age_gap_count_gt_300s": self.log_age_gap_count_gt_300s,
            "n_charge_events": self.n_charge_events,
            "n_discharge_events": self.n_discharge_events,
            "n_rest_events": self.n_rest_events,
            "max_charge_event_h": self.max_charge_event_h,
            "max_discharge_event_h": self.max_discharge_event_h,
            "max_rest_event_h": self.max_rest_event_h,
            "max_abs_current_ge_1C_event_h": self.max_abs_current_ge_1c_event_h,
            "max_abs_current_ge_1p5C_event_h": self.max_abs_current_ge_1p5c_event_h,
            "max_abs_current_ge_5over3C_event_h": self.max_abs_current_ge_5over3c_event_h,
            "max_cold_high_abs_current_event_h": self.max_cold_high_abs_current_event_h,
            "max_high_voltage_high_abs_current_event_h": (
                self.max_high_voltage_high_abs_current_event_h
            ),
            "max_high_soc_high_abs_current_event_h": (
                self.max_high_soc_high_abs_current_event_h
            ),
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

    def _update_events(self, active: dict[str, bool], dt_h: float) -> None:
        if self._active_events is None:
            self._active_events = {}
        if self._active_event_h is None:
            self._active_event_h = {}
        for event_name, is_active in active.items():
            was_active = self._active_events.get(event_name, False)
            if is_active and not was_active:
                if event_name == "charge":
                    self.n_charge_events += 1
                elif event_name == "discharge":
                    self.n_discharge_events += 1
                elif event_name == "rest":
                    self.n_rest_events += 1
                self._active_event_h[event_name] = 0.0
            if is_active:
                total = self._active_event_h.get(event_name, 0.0) + dt_h
                self._active_event_h[event_name] = total
                self._record_event_max(event_name, total)
            else:
                self._active_event_h[event_name] = 0.0
            self._active_events[event_name] = is_active

    def _update_event_array(
        self,
        event_name: str,
        active: np.ndarray,
        dt_h: np.ndarray,
    ) -> None:
        if self._active_events is None:
            self._active_events = {}
        if self._active_event_h is None:
            self._active_event_h = {}
        active = active.astype(bool, copy=False)
        if active.size == 0:
            return
        previous_active = self._active_events.get(event_name, False)
        current_duration = self._active_event_h.get(event_name, 0.0)
        starts = np.flatnonzero(active & np.concatenate(([not previous_active], ~active[:-1])))
        for start_idx in starts:
            if event_name == "charge":
                self.n_charge_events += 1
            elif event_name == "discharge":
                self.n_discharge_events += 1
            elif event_name == "rest":
                self.n_rest_events += 1
            if start_idx > 0 or not previous_active:
                current_duration = 0.0
        boundaries = np.flatnonzero(active[1:] != active[:-1]) + 1
        segment_starts = np.concatenate(([0], boundaries))
        segment_ends = np.concatenate((boundaries, [active.size]))
        for start_idx, end_idx in zip(segment_starts, segment_ends, strict=True):
            if not active[start_idx]:
                if end_idx == active.size:
                    current_duration = 0.0
                continue
            if start_idx > 0 or not previous_active:
                current_duration = 0.0
            current_duration += float(np.sum(dt_h[start_idx:end_idx]))
            self._record_event_max(event_name, current_duration)
        self._active_events[event_name] = bool(active[-1])
        self._active_event_h[event_name] = current_duration if active[-1] else 0.0

    def _record_event_max(self, event_name: str, value_h: float) -> None:
        if event_name == "charge":
            self.max_charge_event_h = max(self.max_charge_event_h, value_h)
        elif event_name == "discharge":
            self.max_discharge_event_h = max(self.max_discharge_event_h, value_h)
        elif event_name == "rest":
            self.max_rest_event_h = max(self.max_rest_event_h, value_h)
        elif event_name == "abs_current_ge_1c":
            self.max_abs_current_ge_1c_event_h = max(
                self.max_abs_current_ge_1c_event_h, value_h
            )
        elif event_name == "abs_current_ge_1p5c":
            self.max_abs_current_ge_1p5c_event_h = max(
                self.max_abs_current_ge_1p5c_event_h, value_h
            )
        elif event_name == "abs_current_ge_5over3c":
            self.max_abs_current_ge_5over3c_event_h = max(
                self.max_abs_current_ge_5over3c_event_h, value_h
            )
        elif event_name == "cold_high_abs_current":
            self.max_cold_high_abs_current_event_h = max(
                self.max_cold_high_abs_current_event_h, value_h
            )
        elif event_name == "high_voltage_high_abs_current":
            self.max_high_voltage_high_abs_current_event_h = max(
                self.max_high_voltage_high_abs_current_event_h, value_h
            )
        elif event_name == "high_soc_high_abs_current":
            self.max_high_soc_high_abs_current_event_h = max(
                self.max_high_soc_high_abs_current_event_h, value_h
            )


def build_interval_stress_features(
    interim_dir: Path,
    interval_table_path: Path,
    out_path: Path,
    current_sign_report_path: Path | None = None,
) -> pa.Table:
    """Build the interval stress-feature sidecar from LOG_AGE row groups."""
    log_age_path = interim_dir / "modality_table_log_age.parquet"
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    if not log_age_path.exists():
        raise FileNotFoundError(f"LOG_AGE table not found: {log_age_path}")

    interval_rows = pq.read_table(interval_table_path).to_pylist()
    sign_policy = _resolve_current_sign_policy(current_sign_report_path)
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
            "current_sign_policy": sign_policy["current_sign_policy"],
            "current_sign_convention_confirmed": sign_policy[
                "current_sign_convention_confirmed"
            ],
            "sign_dependent_features_provisional": sign_policy[
                "sign_dependent_features_provisional"
            ],
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
            b"current_sign_policy": str(sign_policy["current_sign_policy"]).encode(),
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
        observed_duration_h = _as_float(row.get("stress_observed_duration_h"))
        dwell_reference_h = observed_duration_h if math.isfinite(observed_duration_h) else duration_h
        for column in NONNEGATIVE_QA_FEATURE_COLUMNS:
            value = _as_float(row.get(column))
            if math.isfinite(value) and value < -duration_tolerance_h:
                negative_feature_counts[column] = negative_feature_counts.get(column, 0) + 1
        for column in DWELL_FEATURE_COLUMNS:
            value = _as_float(row.get(column))
            if (
                math.isfinite(value)
                and math.isfinite(duration_h)
                and value > dwell_reference_h + duration_tolerance_h
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
        if abs(voltage_sum - dwell_reference_h) > duration_tolerance_h:
            voltage_sum_failures += 1
        if abs(temperature_sum - dwell_reference_h) > duration_tolerance_h:
            temperature_sum_failures += 1
        if abs(soc_sum - dwell_reference_h) > duration_tolerance_h:
            soc_sum_failures += 1
        if abs(current_sum - dwell_reference_h) > duration_tolerance_h:
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
            "reference": "stress_observed_duration_h",
        },
        "negative_feature_counts": dict(sorted(negative_feature_counts.items())),
        "features_exceeding_duration_counts": dict(
            sorted(exceeding_duration_counts.items())
        ),
        "current_sign_policy_counts": dict(
            sorted(Counter(str(row["current_sign_policy"]) for row in rows).items())
        ),
        "current_sign_convention_confirmed_counts": dict(
            sorted(
                Counter(
                    str(bool(row["current_sign_convention_confirmed"])) for row in rows
                ).items()
            )
        ),
        "sign_dependent_features_provisional_counts": dict(
            sorted(
                Counter(
                    str(bool(row["sign_dependent_features_provisional"])) for row in rows
                ).items()
            )
        ),
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
            window_start_s=float(interval["_log_age_window_start_s"]),
            window_end_s=float(interval["_log_age_window_end_s"]),
            delta_capacity_Ah=float(row["delta_capacity_Ah"]),
            calendar_days=float(row["calendar_days"]),
            log_age_efc_delta=_nullable_float(row.get("log_age_efc_delta")),
            log_age_delta_q_Ah=_nullable_float(row.get("log_age_delta_q_Ah")),
        )
    return dict(intervals_by_cell), accumulators


def _resolve_current_sign_policy(
    current_sign_report_path: Path | None,
) -> dict[str, str | bool]:
    default = {
        "current_sign_policy": CURRENT_SIGN_POLICY,
        "current_sign_convention_confirmed": CURRENT_SIGN_CONVENTION_CONFIRMED,
        "sign_dependent_features_provisional": SIGN_DEPENDENT_FEATURES_PROVISIONAL,
    }
    if current_sign_report_path is None or not current_sign_report_path.exists():
        return default
    try:
        report = json.loads(current_sign_report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    convention = str(report.get("current_sign_convention", "unknown"))
    confidence = str(report.get("confidence", "low"))
    if convention == "positive_current_charge" and confidence == "high":
        return {
            "current_sign_policy": "positive_current_charge_confirmed",
            "current_sign_convention_confirmed": True,
            "sign_dependent_features_provisional": False,
        }
    return default


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


def _column_numpy(table: pa.Table, column: str) -> np.ndarray:
    return np.asarray(table.column(column).combine_chunks().to_numpy(zero_copy_only=False))


def _sum_dt(values: np.ndarray, mask: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.sum(values[mask]))


def _median(values: list[float]) -> float | None:
    finite_values = sorted(value for value in values if math.isfinite(value))
    if not finite_values:
        return None
    middle = len(finite_values) // 2
    if len(finite_values) % 2:
        return finite_values[middle]
    return (finite_values[middle - 1] + finite_values[middle]) / 2.0
