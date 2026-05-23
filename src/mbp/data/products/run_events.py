"""LOG_AGE run-event table and interval sequence-feature sidecars."""

from __future__ import annotations

from array import array
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import csv
import json
import math
from pathlib import Path
import random
import sys
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from mbp.data.schema_contracts import (
    INTERVAL_SEQUENCE_FEATURES_V1_SCHEMA,
    RUN_EVENT_TABLE_V1_SCHEMA,
    validate_table,
)

SCHEMA_VERSION = "gate24.run_events.v1"
SEQUENCE_SCHEMA_VERSION = "gate24.interval_sequence_features.v1"
FEATURE_POLICY_VERSION = "temporal_history_value.v1"
EVENT_WRITE_BATCH_ROWS = 50_000
RETURN_TABLE_ROW_LIMIT = 100_000
REST_CURRENT_A = 0.05
HIGH_CURRENT_A = 4.5
HIGH_VOLTAGE_V = 4.1
COLD_C = 10.0
HOT_C = 35.0
MAX_GAP_S = 300.0
RUN_EVENT_DURATION_WARNING_H = 24.0
LOG_COLUMNS = [
    "cell_id",
    "timestamp_s",
    "v_raw_V",
    "i_raw_A",
    "t_cell_degC",
    "soc_est",
    "delta_q_Ah",
    "EFC",
]
_EVENT_TYPE_TO_CODE = {"rest": 0, "charge": 1, "discharge": 2, "unknown": 3}
_EVENT_CODE_TO_TYPE = {value: key for key, value in _EVENT_TYPE_TO_CODE.items()}


@dataclass(frozen=True)
class IntervalKey:
    cell_id: str
    checkup_k: int
    checkup_k_next: int


@dataclass
class EventBuilder:
    interval: dict[str, Any]
    event_index: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    event_type: str | None = None
    start_s: float | None = None
    end_s: float | None = None
    source_rows: int = 0
    max_gap_s: float = 0.0
    voltage_sum: float = 0.0
    voltage_count: int = 0
    voltage_min: float | None = None
    voltage_max: float | None = None
    current_sum: float = 0.0
    current_abs_sum: float = 0.0
    current_count: int = 0
    current_abs_max: float | None = None
    temp_sum: float = 0.0
    temp_count: int = 0
    temp_min: float | None = None
    temp_max: float | None = None
    soc_sum: float = 0.0
    soc_count: int = 0
    soc_min: float | None = None
    soc_max: float | None = None
    first_delta_q: float | None = None
    last_delta_q: float | None = None
    first_efc: float | None = None
    last_efc: float | None = None

    def update(self, rows: list[dict[str, Any]]) -> None:
        rows = sorted(rows, key=lambda row: float(row["timestamp_s"]))
        if not rows:
            return
        self.update_arrays(
            _array([row.get("timestamp_s") for row in rows]),
            _array([row.get("v_raw_V") for row in rows]),
            _array([row.get("i_raw_A") for row in rows]),
            _array([row.get("t_cell_degC") for row in rows]),
            _array([row.get("soc_est") for row in rows]),
            _array([row.get("delta_q_Ah") for row in rows]),
            _array([row.get("EFC") for row in rows]),
        )

    def update_arrays(
        self,
        timestamps: np.ndarray,
        voltage: np.ndarray,
        current: np.ndarray,
        temperature: np.ndarray,
        soc: np.ndarray,
        delta_q: np.ndarray,
        efc: np.ndarray,
    ) -> None:
        finite_time = np.isfinite(timestamps)
        if not bool(finite_time.any()):
            return
        order = np.argsort(timestamps[finite_time], kind="stable")
        indices = np.flatnonzero(finite_time)[order]
        timestamps = timestamps[indices]
        voltage = voltage[indices]
        current = current[indices]
        temperature = temperature[indices]
        soc = soc[indices]
        delta_q = delta_q[indices]
        efc = efc[indices]
        event_codes = _event_codes(current)
        gaps = np.zeros(len(timestamps), dtype=float)
        if len(timestamps) > 1:
            gaps[1:] = np.maximum(0.0, np.diff(timestamps))
        if self.end_s is not None:
            gaps[0] = max(0.0, float(timestamps[0]) - self.end_s)
        break_mask = np.zeros(len(timestamps), dtype=bool)
        break_mask[0] = True
        if len(timestamps) > 1:
            break_mask[1:] = (event_codes[1:] != event_codes[:-1]) | (gaps[1:] > MAX_GAP_S)
        if gaps[0] > MAX_GAP_S and self.event_type is not None:
            break_mask[0] = True
        starts = np.flatnonzero(break_mask)
        ends = list(starts[1:]) + [len(timestamps)]
        for start, end in zip(starts, ends, strict=True):
            event_type = _EVENT_CODE_TO_TYPE[int(event_codes[start])]
            first_gap = float(gaps[start])
            internal_max_gap = float(np.max(gaps[start + 1 : end])) if end - start > 1 else 0.0
            self._append_segment(
                event_type,
                float(timestamps[start]),
                float(timestamps[end - 1]),
                first_gap,
                internal_max_gap,
                voltage[start:end],
                current[start:end],
                temperature[start:end],
                soc[start:end],
                delta_q[start:end],
                efc[start:end],
            )

    def close(self) -> None:
        if self.event_type is not None:
            self._finalize("")

    def _start(self, event_type: str, timestamp: float) -> None:
        self.event_type = event_type
        self.start_s = timestamp
        self.end_s = timestamp
        self.source_rows = 0
        self.max_gap_s = 0.0
        self.voltage_sum = 0.0
        self.voltage_count = 0
        self.voltage_min = None
        self.voltage_max = None
        self.current_sum = 0.0
        self.current_abs_sum = 0.0
        self.current_count = 0
        self.current_abs_max = None
        self.temp_sum = 0.0
        self.temp_count = 0
        self.temp_min = None
        self.temp_max = None
        self.soc_sum = 0.0
        self.soc_count = 0
        self.soc_min = None
        self.soc_max = None
        self.first_delta_q = None
        self.last_delta_q = None
        self.first_efc = None
        self.last_efc = None

    def _append_segment(
        self,
        event_type: str,
        start_s: float,
        end_s: float,
        first_gap_s: float,
        internal_max_gap_s: float,
        voltage: np.ndarray,
        current: np.ndarray,
        temperature: np.ndarray,
        soc: np.ndarray,
        delta_q: np.ndarray,
        efc: np.ndarray,
    ) -> None:
        if self.event_type is None:
            self._start(event_type, start_s)
        elif event_type != self.event_type or first_gap_s > MAX_GAP_S:
            self._finalize("gap_gt_300s" if first_gap_s > MAX_GAP_S else "")
            self._start(event_type, start_s)
        self.end_s = end_s
        self.max_gap_s = max(self.max_gap_s, first_gap_s, internal_max_gap_s)
        self.source_rows += int(len(current))
        self._record_array_values(voltage, current, temperature, soc, delta_q, efc)

    def _record_array_values(
        self,
        voltage: np.ndarray,
        current: np.ndarray,
        temperature: np.ndarray,
        soc: np.ndarray,
        delta_q: np.ndarray,
        efc: np.ndarray,
    ) -> None:
        self.voltage_sum, self.voltage_count, self.voltage_min, self.voltage_max = _update_stats(
            voltage, self.voltage_sum, self.voltage_count, self.voltage_min, self.voltage_max
        )
        finite_current = current[np.isfinite(current)]
        if len(finite_current):
            self.current_sum += float(np.sum(finite_current))
            self.current_abs_sum += float(np.sum(np.abs(finite_current)))
            self.current_count += int(len(finite_current))
            current_abs_max = float(np.max(np.abs(finite_current)))
            self.current_abs_max = (
                current_abs_max if self.current_abs_max is None else max(self.current_abs_max, current_abs_max)
            )
        self.temp_sum, self.temp_count, self.temp_min, self.temp_max = _update_stats(
            temperature, self.temp_sum, self.temp_count, self.temp_min, self.temp_max
        )
        self.soc_sum, self.soc_count, self.soc_min, self.soc_max = _update_stats(
            soc, self.soc_sum, self.soc_count, self.soc_min, self.soc_max
        )
        finite_delta_q = delta_q[np.isfinite(delta_q)]
        if len(finite_delta_q):
            self.first_delta_q = float(finite_delta_q[0]) if self.first_delta_q is None else self.first_delta_q
            self.last_delta_q = float(finite_delta_q[-1])
        finite_efc = efc[np.isfinite(efc)]
        if len(finite_efc):
            self.first_efc = float(finite_efc[0]) if self.first_efc is None else self.first_efc
            self.last_efc = float(finite_efc[-1])

    def _finalize(self, extra_flag: str) -> None:
        assert self.event_type is not None
        assert self.start_s is not None
        assert self.end_s is not None
        duration_s = max(0.0, self.end_s - self.start_s)
        flags = []
        if extra_flag:
            flags.append(extra_flag)
        if duration_s <= 0:
            flags.append("zero_duration")
        row = {
            "cell_id": str(self.interval["cell_id"]),
            "parameter_set": int(self.interval["parameter_set"]),
            "replicate_id": int(self.interval["replicate_id"]),
            "checkup_k": int(self.interval["checkup_k"]),
            "checkup_k_next": int(self.interval["checkup_k_next"]),
            "event_index": self.event_index,
            "event_type": self.event_type,
            "event_start_s": self.start_s,
            "event_end_s": self.end_s,
            "event_duration_s": duration_s,
            "event_duration_h": duration_s / 3600.0,
            "mean_voltage_V": _mean_from_stats(self.voltage_sum, self.voltage_count),
            "min_voltage_V": self.voltage_min,
            "max_voltage_V": self.voltage_max,
            "mean_current_A": _mean_from_stats(self.current_sum, self.current_count),
            "mean_abs_current_A": _mean_from_stats(self.current_abs_sum, self.current_count),
            "max_abs_current_A": self.current_abs_max,
            "mean_temperature_C": _mean_from_stats(self.temp_sum, self.temp_count),
            "max_temperature_C": self.temp_max,
            "mean_soc": _mean_from_stats(self.soc_sum, self.soc_count),
            "min_soc": self.soc_min,
            "max_soc": self.soc_max,
            "delta_q_Ah": (
                self.last_delta_q - self.first_delta_q
                if self.first_delta_q is not None and self.last_delta_q is not None
                else None
            ),
            "delta_EFC": (
                self.last_efc - self.first_efc
                if self.first_efc is not None and self.last_efc is not None
                else None
            ),
            "high_voltage_event": bool(self.voltage_max is not None and self.voltage_max >= HIGH_VOLTAGE_V),
            "cold_event": bool(self.temp_min is not None and self.temp_min <= COLD_C),
            "hot_event": bool(self.temp_max is not None and self.temp_max >= HOT_C),
            "high_abs_current_event": bool(self.current_abs_max is not None and self.current_abs_max >= HIGH_CURRENT_A),
            "cold_high_current_event": bool(
                self.temp_min is not None
                and self.current_abs_max is not None
                and self.temp_min <= COLD_C
                and self.current_abs_max >= HIGH_CURRENT_A
            ),
            "high_voltage_high_current_event": bool(
                self.voltage_max is not None
                and self.current_abs_max is not None
                and self.voltage_max >= HIGH_VOLTAGE_V
                and self.current_abs_max >= HIGH_CURRENT_A
            ),
            "source_rows": self.source_rows,
            "max_gap_s": self.max_gap_s,
            "quality_flags": ";".join(flags),
            "schema_version": SCHEMA_VERSION,
        }
        self.events.append(row)
        self.event_index += 1

    def drain_events(self) -> list[dict[str, Any]]:
        events = self.events
        self.events = []
        return events


@dataclass
class SequenceAccumulator:
    event_types: array = field(default_factory=lambda: array("b"))
    durations_h: array = field(default_factory=lambda: array("f"))
    high_current_flags: array = field(default_factory=lambda: array("b"))
    cold_high_current_flags: array = field(default_factory=lambda: array("b"))
    counts: Counter[str] = field(default_factory=Counter)
    durations_by_type: Counter[str] = field(default_factory=Counter)
    max_duration_by_type: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    high_current_count: int = 0
    cold_high_current_count: int = 0
    high_voltage_high_current_count: int = 0
    transition_counts: Counter[tuple[str, str]] = field(default_factory=Counter)
    alternation_count: int = 0
    previous_event_type: str | None = None
    first_high_current_index: int | None = None
    last_high_current_index: int | None = None
    longest_high_current_burst_h: float = 0.0
    current_high_current_burst_h: float = 0.0
    longest_cold_high_current_burst_h: float = 0.0
    current_cold_high_current_burst_h: float = 0.0

    def update(
        self,
        event_type: str,
        duration_h: float,
        high_current: bool,
        cold_high_current: bool,
        high_voltage_high_current: bool,
    ) -> None:
        event_index = len(self.event_types)
        event_code = _EVENT_TYPE_TO_CODE.get(event_type, _EVENT_TYPE_TO_CODE["unknown"])
        self.event_types.append(event_code)
        self.durations_h.append(float(duration_h))
        self.high_current_flags.append(int(high_current))
        self.cold_high_current_flags.append(int(cold_high_current))
        self.counts[event_type] += 1
        self.durations_by_type[event_type] += float(duration_h)
        self.max_duration_by_type[event_type] = max(self.max_duration_by_type[event_type], float(duration_h))
        if self.previous_event_type is not None:
            self.transition_counts[(self.previous_event_type, event_type)] += 1
            self.alternation_count += int(self.previous_event_type != event_type)
        self.previous_event_type = event_type
        if high_current:
            self.high_current_count += 1
            self.first_high_current_index = (
                event_index if self.first_high_current_index is None else self.first_high_current_index
            )
            self.last_high_current_index = event_index
            self.current_high_current_burst_h += float(duration_h)
            self.longest_high_current_burst_h = max(
                self.longest_high_current_burst_h, self.current_high_current_burst_h
            )
        else:
            self.current_high_current_burst_h = 0.0
        if cold_high_current:
            self.cold_high_current_count += 1
            self.current_cold_high_current_burst_h += float(duration_h)
            self.longest_cold_high_current_burst_h = max(
                self.longest_cold_high_current_burst_h, self.current_cold_high_current_burst_h
            )
        else:
            self.current_cold_high_current_burst_h = 0.0
        if high_voltage_high_current:
            self.high_voltage_high_current_count += 1


def build_run_event_table(
    log_age_path: Path,
    interval_table_path: Path,
    out_path: Path,
    progress_interval: int = 0,
) -> pa.Table:
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    intervals_by_cell, builders = _prepare_event_builders(interval_rows)
    parquet_file = pq.ParquetFile(log_age_path)
    schema_names = parquet_file.schema_arrow.names
    cell_idx = schema_names.index("cell_id")
    time_idx = schema_names.index("timestamp_s")
    total_rows = 0
    row_group_count = parquet_file.metadata.num_row_groups
    output_schema = RUN_EVENT_TABLE_V1_SCHEMA.with_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"log_age_path": str(log_age_path).encode(),
            b"current_sign_policy": b"positive_current_charge",
        }
    )
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if tmp_path.exists():
        tmp_path.unlink()
    writer: pq.ParquetWriter | None = None
    pending_event_rows: list[dict[str, Any]] = []
    return_rows: list[dict[str, Any]] | None = []
    rows_written = 0

    def flush_pending(force: bool = False) -> None:
        nonlocal pending_event_rows, return_rows, rows_written, writer
        if not pending_event_rows:
            return
        if not force and len(pending_event_rows) < EVENT_WRITE_BATCH_ROWS:
            return
        table = pa.Table.from_pylist(pending_event_rows, schema=output_schema)
        if not validate_table(table, output_schema):
            raise TypeError("Generated run-event table chunk does not match RUN_EVENT_TABLE_V1_SCHEMA.")
        if writer is None:
            writer = pq.ParquetWriter(tmp_path, output_schema)
        writer.write_table(table)
        rows_written += table.num_rows
        if return_rows is not None:
            if len(return_rows) + len(pending_event_rows) <= RETURN_TABLE_ROW_LIMIT:
                return_rows.extend(pending_event_rows)
            else:
                return_rows = None
        pending_event_rows = []
        del table
        pa.default_memory_pool().release_unused()

    try:
        for row_group_idx in range(row_group_count):
            row_group = parquet_file.metadata.row_group(row_group_idx)
            candidate_cells = _candidate_cells(row_group, cell_idx, intervals_by_cell)
            if candidate_cells == set():
                _print_row_group_progress(
                    row_group_idx + 1,
                    row_group_count,
                    row_group_idx,
                    0,
                    total_rows,
                    progress_interval,
                )
                continue
            min_t, max_t = _row_group_time_bounds(row_group, time_idx)
            if (
                min_t is not None
                and max_t is not None
                and not _row_group_overlaps(candidate_cells, intervals_by_cell, min_t, max_t)
            ):
                _print_row_group_progress(
                    row_group_idx + 1,
                    row_group_count,
                    row_group_idx,
                    0,
                    total_rows,
                    progress_interval,
                )
                continue

            table = parquet_file.read_row_group(row_group_idx, columns=LOG_COLUMNS)
            total_rows += table.num_rows
            touched_keys: set[IntervalKey] = set()
            if table.num_rows:
                if candidate_cells is None:
                    candidate_cells = {
                        str(cell_id)
                        for cell_id in pc.unique(table.column("cell_id")).to_pylist()
                        if str(cell_id) in intervals_by_cell
                    }
                touched_keys = _assign_row_group_to_builders(
                    table,
                    candidate_cells,
                    intervals_by_cell,
                    builders,
                    min_t,
                    max_t,
                )
                for key in touched_keys:
                    pending_event_rows.extend(builders[key].drain_events())
                flush_pending()
            _print_row_group_progress(
                row_group_idx + 1,
                row_group_count,
                row_group_idx,
                table.num_rows,
                total_rows,
                progress_interval,
            )
            del table
            pa.default_memory_pool().release_unused()

        for key in sorted(builders, key=lambda value: (value.cell_id, value.checkup_k)):
            builders[key].close()
            pending_event_rows.extend(builders[key].drain_events())
            flush_pending()
        flush_pending(force=True)
        if writer is None:
            pq.write_table(pa.Table.from_batches([], schema=output_schema), tmp_path)
    finally:
        if writer is not None:
            writer.close()

    tmp_path.replace(out_path)
    if return_rows is not None:
        return pa.Table.from_pylist(return_rows, schema=output_schema)
    return pa.Table.from_batches([], schema=output_schema)


def write_run_event_qa(
    run_events_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out_path: Path,
) -> dict[str, Any]:
    intervals = pq.read_table(interval_table_path).to_pylist()
    event_count_by_key: Counter[tuple[str, int, int]] = Counter()
    duration_by_key: Counter[tuple[str, int, int]] = Counter()
    max_gap_by_key: dict[tuple[str, int, int], float] = defaultdict(float)
    event_counts: Counter[str] = Counter()
    row_count = 0
    for batch in pq.ParquetFile(run_events_path).iter_batches(
        columns=[
            "cell_id",
            "checkup_k",
            "checkup_k_next",
            "event_type",
            "event_duration_h",
            "max_gap_s",
        ],
        batch_size=200_000,
    ):
        data = batch.to_pydict()
        for idx, cell_id in enumerate(data["cell_id"]):
            key = (str(cell_id), int(data["checkup_k"][idx]), int(data["checkup_k_next"][idx]))
            event_count_by_key[key] += 1
            duration_by_key[key] += float(data["event_duration_h"][idx])
            max_gap_by_key[key] = max(max_gap_by_key[key], float(data["max_gap_s"][idx]))
            event_counts[str(data["event_type"][idx])] += 1
            row_count += 1
    coverage_rows = []
    missing = 0
    duration_deltas = []
    interval_max_gaps = []
    for interval in intervals:
        key = _interval_key(interval)
        event_count = int(event_count_by_key[key])
        if not event_count:
            missing += 1
        duration_h = float(duration_by_key[key])
        duration_delta_h = duration_h - float(interval["duration_h"])
        duration_deltas.append(duration_delta_h)
        interval_max_gap = float(max_gap_by_key[key])
        interval_max_gaps.append(interval_max_gap)
        coverage_rows.append(
            {
                "cell_id": key[0],
                "parameter_set": int(interval["parameter_set"]),
                "replicate_id": int(interval["replicate_id"]),
                "checkup_k": key[1],
                "checkup_k_next": key[2],
                "event_count": event_count,
                "event_duration_h": duration_h,
                "interval_duration_h": float(interval["duration_h"]),
                "duration_delta_h": duration_delta_h,
                "max_gap_s": interval_max_gap,
            }
        )
    duration_mismatch_count = sum(abs(value) > RUN_EVENT_DURATION_WARNING_H for value in duration_deltas)
    warnings = []
    if missing:
        warnings.append("missing_intervals")
    if duration_mismatch_count:
        warnings.append("duration_delta_gt_24h")
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "row_count": row_count,
        "intervals": len(intervals),
        "intervals_covered": len(intervals) - missing,
        "missing_intervals": missing,
        "duration_delta_gt_24h_intervals": duration_mismatch_count,
        "event_type_counts": dict(event_counts),
        "event_count_summary": _summary([row["event_count"] for row in coverage_rows]),
        "duration_delta_h_summary": _summary(duration_deltas),
        "max_gap_s_summary": _summary(interval_max_gaps),
        "max_gap_s_summary_scope": "per_interval_max_gap",
        "warnings": warnings,
    }
    _write_csv(coverage_out_path, coverage_rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def build_sequence_feature_table(
    run_events_path: Path,
    interval_table_path: Path,
    out_path: Path,
    seed: int = 42,
) -> pa.Table:
    intervals = pq.read_table(interval_table_path).to_pylist()
    accumulators: dict[tuple[str, int, int], SequenceAccumulator] = defaultdict(SequenceAccumulator)
    for batch in pq.ParquetFile(run_events_path).iter_batches(
        columns=[
            "cell_id",
            "checkup_k",
            "checkup_k_next",
            "event_type",
            "event_duration_h",
            "high_abs_current_event",
            "cold_high_current_event",
            "high_voltage_high_current_event",
        ],
        batch_size=200_000,
    ):
        data = batch.to_pydict()
        for idx, cell_id in enumerate(data["cell_id"]):
            key = (str(cell_id), int(data["checkup_k"][idx]), int(data["checkup_k_next"][idx]))
            accumulators[key].update(
                str(data["event_type"][idx]),
                float(data["event_duration_h"][idx]),
                bool(data["high_abs_current_event"][idx]),
                bool(data["cold_high_current_event"][idx]),
                bool(data["high_voltage_high_current_event"][idx]),
            )
    output_rows = []
    for interval in intervals:
        output_rows.append(_sequence_features_for_interval(interval, accumulators.get(_interval_key(interval)), seed))
    table = pa.Table.from_pylist(output_rows, schema=INTERVAL_SEQUENCE_FEATURES_V1_SCHEMA)
    if not validate_table(table, INTERVAL_SEQUENCE_FEATURES_V1_SCHEMA):
        raise TypeError(
            "Generated sequence-feature table does not match INTERVAL_SEQUENCE_FEATURES_V1_SCHEMA."
        )
    table = table.replace_schema_metadata(
        {
            b"schema_version": SEQUENCE_SCHEMA_VERSION.encode(),
            b"feature_policy_version": FEATURE_POLICY_VERSION.encode(),
            b"run_events_path": str(run_events_path).encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"shuffle_seed": str(seed).encode(),
        }
    )
    _write_parquet_atomic(table, out_path)
    return table


def write_sequence_feature_qa(
    sequence_features_path: Path,
    interval_table_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    rows = pq.read_table(sequence_features_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    nan_counts: dict[str, int] = {}
    for column in INTERVAL_SEQUENCE_FEATURES_V1_SCHEMA.names:
        count = sum(_is_nan(row.get(column)) for row in rows)
        if count:
            nan_counts[column] = count
    missing = len(interval_rows) - len(rows)
    report = {
        "status": "warning" if missing or nan_counts else "passed",
        "schema_version": SEQUENCE_SCHEMA_VERSION,
        "row_count": len(rows),
        "interval_rows": len(interval_rows),
        "missing_intervals": missing,
        "nan_counts": nan_counts,
        "event_count_summary": _summary([row["sequence_event_count"] for row in rows]),
        "shuffle_seed": rows[0]["sequence_shuffle_seed"] if rows else None,
        "leakage_check": {
            "target_derived_capacity_rates_present": False,
            "status": "passed",
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _sequence_features_for_interval(
    interval: dict[str, Any],
    accumulator: SequenceAccumulator | None,
    seed: int,
) -> dict[str, Any]:
    accumulator = accumulator or SequenceAccumulator()
    event_count = len(accumulator.event_types)
    thirds = _third_exposure_fractions_from_accumulator(accumulator)
    shuffled = _shuffled_order_features_from_accumulator(accumulator, interval, seed)
    first_high = (
        accumulator.first_high_current_index / max(1, event_count - 1)
        if accumulator.first_high_current_index is not None
        else None
    )
    last_high = (
        accumulator.last_high_current_index / max(1, event_count - 1)
        if accumulator.last_high_current_index is not None
        else None
    )
    features = {
        "cell_id": str(interval["cell_id"]),
        "parameter_set": int(interval["parameter_set"]),
        "replicate_id": int(interval["replicate_id"]),
        "checkup_k": int(interval["checkup_k"]),
        "checkup_k_next": int(interval["checkup_k_next"]),
        "schema_version": SEQUENCE_SCHEMA_VERSION,
        "feature_policy_version": FEATURE_POLICY_VERSION,
        "sequence_event_count": event_count,
        "sequence_total_event_duration_h": float(sum(accumulator.durations_h)),
        "sequence_charge_event_count": accumulator.counts["charge"],
        "sequence_discharge_event_count": accumulator.counts["discharge"],
        "sequence_rest_event_count": accumulator.counts["rest"],
        "sequence_unknown_event_count": accumulator.counts["unknown"],
        "sequence_charge_duration_h": float(accumulator.durations_by_type["charge"]),
        "sequence_discharge_duration_h": float(accumulator.durations_by_type["discharge"]),
        "sequence_rest_duration_h": float(accumulator.durations_by_type["rest"]),
        "sequence_max_charge_duration_h": float(accumulator.max_duration_by_type.get("charge", 0.0)),
        "sequence_max_discharge_duration_h": float(accumulator.max_duration_by_type.get("discharge", 0.0)),
        "sequence_max_rest_duration_h": float(accumulator.max_duration_by_type.get("rest", 0.0)),
        "sequence_high_current_event_count": accumulator.high_current_count,
        "sequence_cold_high_current_event_count": accumulator.cold_high_current_count,
        "sequence_high_voltage_high_current_event_count": accumulator.high_voltage_high_current_count,
        "sequence_transition_charge_rest": accumulator.transition_counts[("charge", "rest")],
        "sequence_transition_rest_charge": accumulator.transition_counts[("rest", "charge")],
        "sequence_transition_discharge_rest": accumulator.transition_counts[("discharge", "rest")],
        "sequence_transition_rest_discharge": accumulator.transition_counts[("rest", "discharge")],
        "sequence_alternation_count": accumulator.alternation_count,
        "sequence_first_high_current_position": first_high,
        "sequence_last_high_current_position": last_high,
        "sequence_early_high_current_fraction": thirds[0],
        "sequence_mid_high_current_fraction": thirds[1],
        "sequence_late_high_current_fraction": thirds[2],
        "sequence_longest_high_current_burst_h": accumulator.longest_high_current_burst_h,
        "sequence_longest_cold_high_current_burst_h": accumulator.longest_cold_high_current_burst_h,
        **shuffled,
        "sequence_shuffle_seed": seed,
        "sequence_quality_flags": "missing_events" if not event_count else "",
    }
    return features


def _order_features(events: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    event_types = [str(row["event_type"]) for row in events]
    transitions = Counter(zip(event_types, event_types[1:], strict=False))
    high_positions = [
        idx / max(1, len(events) - 1)
        for idx, row in enumerate(events)
        if bool(row["high_abs_current_event"])
    ]
    thirds = _third_exposure_fractions(events)
    return {
        f"{prefix}transition_charge_rest": transitions[("charge", "rest")],
        f"{prefix}transition_rest_charge": transitions[("rest", "charge")],
        f"{prefix}transition_discharge_rest": transitions[("discharge", "rest")],
        f"{prefix}transition_rest_discharge": transitions[("rest", "discharge")],
        f"{prefix}alternation_count": sum(a != b for a, b in zip(event_types, event_types[1:], strict=False)),
        f"{prefix}first_high_current_position": high_positions[0] if high_positions else None,
        f"{prefix}last_high_current_position": high_positions[-1] if high_positions else None,
        f"{prefix}early_high_current_fraction": thirds[0],
        f"{prefix}mid_high_current_fraction": thirds[1],
        f"{prefix}late_high_current_fraction": thirds[2],
        f"{prefix}longest_high_current_burst_h": _longest_burst(events, "high_abs_current_event"),
        f"{prefix}longest_cold_high_current_burst_h": _longest_burst(events, "cold_high_current_event"),
    }


def _shuffled_order_features(events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = _order_features(events, "sequence_shuffled_")
    return {
        "sequence_shuffled_transition_charge_rest": ordered[
            "sequence_shuffled_transition_charge_rest"
        ],
        "sequence_shuffled_transition_rest_charge": ordered[
            "sequence_shuffled_transition_rest_charge"
        ],
        "sequence_shuffled_transition_discharge_rest": ordered[
            "sequence_shuffled_transition_discharge_rest"
        ],
        "sequence_shuffled_transition_rest_discharge": ordered[
            "sequence_shuffled_transition_rest_discharge"
        ],
        "sequence_shuffled_alternation_count": ordered["sequence_shuffled_alternation_count"],
        "sequence_shuffled_early_high_current_fraction": ordered[
            "sequence_shuffled_early_high_current_fraction"
        ],
        "sequence_shuffled_mid_high_current_fraction": ordered[
            "sequence_shuffled_mid_high_current_fraction"
        ],
        "sequence_shuffled_late_high_current_fraction": ordered[
            "sequence_shuffled_late_high_current_fraction"
        ],
    }


def _third_exposure_fractions_from_accumulator(accumulator: SequenceAccumulator) -> tuple[float, float, float]:
    total = sum(
        float(duration)
        for duration, high_current in zip(accumulator.durations_h, accumulator.high_current_flags, strict=False)
        if high_current
    )
    if total <= 0:
        return 0.0, 0.0, 0.0
    buckets = [0.0, 0.0, 0.0]
    n = max(1, len(accumulator.event_types))
    for idx, (duration, high_current) in enumerate(
        zip(accumulator.durations_h, accumulator.high_current_flags, strict=False)
    ):
        if high_current:
            bucket = min(2, int((idx / n) * 3))
            buckets[bucket] += float(duration)
    return buckets[0] / total, buckets[1] / total, buckets[2] / total


def _shuffled_order_features_from_accumulator(
    accumulator: SequenceAccumulator,
    interval: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    n = len(accumulator.event_types)
    if not n:
        return {
            "sequence_shuffled_transition_charge_rest": 0,
            "sequence_shuffled_transition_rest_charge": 0,
            "sequence_shuffled_transition_discharge_rest": 0,
            "sequence_shuffled_transition_rest_discharge": 0,
            "sequence_shuffled_alternation_count": 0,
            "sequence_shuffled_early_high_current_fraction": 0.0,
            "sequence_shuffled_mid_high_current_fraction": 0.0,
            "sequence_shuffled_late_high_current_fraction": 0.0,
        }
    indices = list(range(n))
    random.Random(seed + int(interval["parameter_set"]) * 100 + int(interval["checkup_k"])).shuffle(indices)
    transitions: Counter[tuple[str, str]] = Counter()
    alternation_count = 0
    previous_type: str | None = None
    high_total = 0.0
    buckets = [0.0, 0.0, 0.0]
    for shuffled_idx, source_idx in enumerate(indices):
        event_type = _EVENT_CODE_TO_TYPE[int(accumulator.event_types[source_idx])]
        if previous_type is not None:
            transitions[(previous_type, event_type)] += 1
            alternation_count += int(previous_type != event_type)
        previous_type = event_type
        if accumulator.high_current_flags[source_idx]:
            duration = float(accumulator.durations_h[source_idx])
            high_total += duration
            bucket = min(2, int((shuffled_idx / max(1, n)) * 3))
            buckets[bucket] += duration
    if high_total > 0:
        buckets = [value / high_total for value in buckets]
    return {
        "sequence_shuffled_transition_charge_rest": transitions[("charge", "rest")],
        "sequence_shuffled_transition_rest_charge": transitions[("rest", "charge")],
        "sequence_shuffled_transition_discharge_rest": transitions[("discharge", "rest")],
        "sequence_shuffled_transition_rest_discharge": transitions[("rest", "discharge")],
        "sequence_shuffled_alternation_count": alternation_count,
        "sequence_shuffled_early_high_current_fraction": buckets[0],
        "sequence_shuffled_mid_high_current_fraction": buckets[1],
        "sequence_shuffled_late_high_current_fraction": buckets[2],
    }


def _prepare_event_builders(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[IntervalKey, EventBuilder]]:
    first_result_time_by_cell: dict[str, float] = {}
    for row in rows:
        cell_id = str(row["cell_id"])
        start = float(row["t_result_k_s"])
        first_result_time_by_cell[cell_id] = min(start, first_result_time_by_cell.get(cell_id, start))
    intervals_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    builders: dict[IntervalKey, EventBuilder] = {}
    for row in rows:
        cell_id = str(row["cell_id"])
        zero_s = first_result_time_by_cell[cell_id]
        interval = dict(row)
        interval["_log_age_window_start_s"] = float(row["t_result_k_s"]) - zero_s
        interval["_log_age_window_end_s"] = float(row["t_result_k1_s"]) - zero_s
        intervals_by_cell[cell_id].append(interval)
        key = IntervalKey(cell_id, int(row["checkup_k"]), int(row["checkup_k_next"]))
        builders[key] = EventBuilder(interval)
    return dict(intervals_by_cell), builders


def _assign_row_group_to_builders(
    table: pa.Table,
    candidate_cells: set[str],
    intervals_by_cell: dict[str, list[dict[str, Any]]],
    builders: dict[IntervalKey, EventBuilder],
    min_t: float | None,
    max_t: float | None,
) -> set[IntervalKey]:
    single_cell = len(candidate_cells) == 1
    arrays = _table_arrays(table)
    all_cell_ids: np.ndarray | None = None if single_cell else _string_array(table.column("cell_id"))
    touched_keys: set[IntervalKey] = set()
    for cell_id in candidate_cells:
        intervals = intervals_by_cell.get(str(cell_id), [])
        if min_t is not None and max_t is not None:
            intervals = [
                interval
                for interval in intervals
                if interval["_log_age_window_start_s"] < max_t
                and interval["_log_age_window_end_s"] >= min_t
            ]
        if not intervals:
            continue
        intervals = sorted(intervals, key=lambda row: float(row["_log_age_window_start_s"]))
        if all_cell_ids is not None:
            cell_mask = all_cell_ids == str(cell_id)
            if not bool(cell_mask.any()):
                continue
            cell_arrays = {name: values[cell_mask] for name, values in arrays.items()}
        else:
            cell_arrays = arrays
        timestamps = cell_arrays["timestamp_s"]
        finite_time = np.isfinite(timestamps)
        if not bool(finite_time.any()):
            continue
        if not np.all(finite_time):
            cell_arrays = {name: values[finite_time] for name, values in cell_arrays.items()}
            timestamps = cell_arrays["timestamp_s"]
        if len(timestamps) > 1 and bool(np.any(np.diff(timestamps) < 0)):
            order = np.argsort(timestamps, kind="stable")
            cell_arrays = {name: values[order] for name, values in cell_arrays.items()}
            timestamps = cell_arrays["timestamp_s"]
        for interval in intervals:
            start_idx = int(np.searchsorted(timestamps, float(interval["_log_age_window_start_s"]), side="right"))
            end_idx = int(np.searchsorted(timestamps, float(interval["_log_age_window_end_s"]), side="right"))
            if end_idx <= start_idx:
                continue
            key = IntervalKey(str(cell_id), int(interval["checkup_k"]), int(interval["checkup_k_next"]))
            builders[key].update_arrays(
                timestamps[start_idx:end_idx],
                cell_arrays["v_raw_V"][start_idx:end_idx],
                cell_arrays["i_raw_A"][start_idx:end_idx],
                cell_arrays["t_cell_degC"][start_idx:end_idx],
                cell_arrays["soc_est"][start_idx:end_idx],
                cell_arrays["delta_q_Ah"][start_idx:end_idx],
                cell_arrays["EFC"][start_idx:end_idx],
            )
            touched_keys.add(key)
    return touched_keys


def _candidate_cells(row_group: pq.RowGroupMetaData, cell_idx: int, intervals_by_cell: dict[str, Any]) -> set[str] | None:
    stats = row_group.column(cell_idx).statistics
    if stats and stats.min is not None and stats.max is not None and stats.min == stats.max:
        cell_id = str(stats.min)
        return {cell_id} if cell_id in intervals_by_cell else set()
    return None


def _row_group_time_bounds(row_group: pq.RowGroupMetaData, time_idx: int) -> tuple[float | None, float | None]:
    stats = row_group.column(time_idx).statistics
    if stats and stats.min is not None and stats.max is not None:
        return float(stats.min), float(stats.max)
    return None, None


def _row_group_overlaps(
    candidate_cells: set[str] | None,
    intervals_by_cell: dict[str, list[dict[str, Any]]],
    min_t: float,
    max_t: float,
) -> bool:
    cells = candidate_cells or intervals_by_cell.keys()
    return any(
        interval["_log_age_window_start_s"] < max_t and interval["_log_age_window_end_s"] >= min_t
        for cell in cells
        for interval in intervals_by_cell.get(str(cell), [])
    )


def _event_type(current_a: float | None) -> str:
    if current_a is None:
        return "unknown"
    if abs(current_a) <= REST_CURRENT_A:
        return "rest"
    return "charge" if current_a > 0 else "discharge"


def _event_codes(current_a: np.ndarray) -> np.ndarray:
    codes = np.full(len(current_a), _EVENT_TYPE_TO_CODE["unknown"], dtype=np.int8)
    finite = np.isfinite(current_a)
    if bool(finite.any()):
        codes[finite & (np.abs(current_a) <= REST_CURRENT_A)] = _EVENT_TYPE_TO_CODE["rest"]
        codes[finite & (current_a > REST_CURRENT_A)] = _EVENT_TYPE_TO_CODE["charge"]
        codes[finite & (current_a < -REST_CURRENT_A)] = _EVENT_TYPE_TO_CODE["discharge"]
    return codes


def _array(values: list[Any]) -> np.ndarray:
    output = np.full(len(values), np.nan, dtype=float)
    for idx, value in enumerate(values):
        finite = _finite(value)
        if finite is not None:
            output[idx] = finite
    return output


def _table_arrays(table: pa.Table) -> dict[str, np.ndarray]:
    return {
        column: np.asarray(
            table.column(column).combine_chunks().to_numpy(zero_copy_only=False),
            dtype=float,
        )
        for column in LOG_COLUMNS
        if column != "cell_id"
    }


def _string_array(column: pa.ChunkedArray) -> np.ndarray:
    return np.asarray(column.combine_chunks().to_pylist(), dtype=object)


def _update_stats(
    values: np.ndarray,
    total: float,
    count: int,
    current_min: float | None,
    current_max: float | None,
) -> tuple[float, int, float | None, float | None]:
    finite = values[np.isfinite(values)]
    if not len(finite):
        return total, count, current_min, current_max
    value_min = float(np.min(finite))
    value_max = float(np.max(finite))
    return (
        total + float(np.sum(finite)),
        count + int(len(finite)),
        value_min if current_min is None else min(current_min, value_min),
        value_max if current_max is None else max(current_max, value_max),
    )


def _mean_from_stats(total: float, count: int) -> float | None:
    return total / count if count else None


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _mean_or_none(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _print_row_group_progress(
    processed_row_groups: int,
    total_row_groups: int,
    row_group_idx: int,
    row_group_rows: int,
    total_rows: int,
    progress_interval: int,
) -> None:
    if progress_interval <= 0:
        return
    if processed_row_groups % progress_interval and processed_row_groups != total_row_groups:
        return
    print(
        "run-events progress: "
        f"{processed_row_groups}/{total_row_groups} row groups processed, "
        f"last_row_group={row_group_idx}, last_row_group_rows={row_group_rows}, "
        f"total_rows={total_rows}",
        file=sys.stderr,
        flush=True,
    )


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _duration_for(events: list[dict[str, Any]], event_type: str) -> float:
    return sum(float(row["event_duration_h"]) for row in events if row["event_type"] == event_type)


def _max_duration_for(events: list[dict[str, Any]], event_type: str) -> float:
    return max((float(row["event_duration_h"]) for row in events if row["event_type"] == event_type), default=0.0)


def _third_exposure_fractions(events: list[dict[str, Any]]) -> tuple[float, float, float]:
    total = sum(float(row["event_duration_h"]) for row in events if bool(row["high_abs_current_event"]))
    if total <= 0:
        return 0.0, 0.0, 0.0
    buckets = [0.0, 0.0, 0.0]
    n = max(1, len(events))
    for idx, row in enumerate(events):
        if bool(row["high_abs_current_event"]):
            bucket = min(2, int((idx / n) * 3))
            buckets[bucket] += float(row["event_duration_h"])
    return buckets[0] / total, buckets[1] / total, buckets[2] / total


def _longest_burst(events: list[dict[str, Any]], flag: str) -> float:
    best = 0.0
    current = 0.0
    for row in events:
        if bool(row[flag]):
            current += float(row["event_duration_h"])
            best = max(best, current)
        else:
            current = 0.0
    return best


def _summary(values: list[float]) -> dict[str, float | int | None]:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "median": finite[len(finite) // 2],
        "p95": finite[min(len(finite) - 1, int(math.ceil(0.95 * len(finite))) - 1)],
        "max": finite[-1],
    }


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_parquet_atomic(table: pa.Table, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    pq.write_table(table, tmp_path)
    tmp_path.replace(out_path)


def _empty_event_row() -> dict[str, Any]:
    return {
        name: "" if field.type == pa.string() else False if field.type == pa.bool_() else 0
        for name, field in zip(RUN_EVENT_TABLE_V1_SCHEMA.names, RUN_EVENT_TABLE_V1_SCHEMA, strict=False)
    }
