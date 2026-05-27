"""Fixed-length event-sequence data product for the sequence reopening gate."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import (
    INTERVAL_EVENT_SEQUENCE_TABLE_V1_SCHEMA,
    validate_table,
)

SCHEMA_VERSION = "gate71.interval_event_sequence_table.v1"
FEATURE_POLICY_VERSION = "minimal_sequence_reopening.v1"
DEFAULT_MAX_EVENTS = 64
DEFAULT_BATCH_SIZE = 200_000
EVENT_FEATURE_COLUMNS = (
    "event_type_rest",
    "event_type_charge",
    "event_type_discharge",
    "event_type_unknown",
    "event_duration_h",
    "mean_voltage_V",
    "mean_abs_current_A",
    "max_abs_current_A",
    "mean_temperature_C",
    "mean_soc",
    "delta_q_Ah",
    "delta_EFC",
    "high_voltage_event",
    "high_abs_current_event",
    "cold_high_current_event",
    "high_voltage_high_current_event",
)
EVENT_COLUMNS = [
    "cell_id",
    "parameter_set",
    "replicate_id",
    "checkup_k",
    "checkup_k_next",
    "event_index",
    "event_type",
    "event_duration_h",
    "mean_voltage_V",
    "mean_abs_current_A",
    "max_abs_current_A",
    "mean_temperature_C",
    "mean_soc",
    "delta_q_Ah",
    "delta_EFC",
    "high_voltage_event",
    "high_abs_current_event",
    "cold_high_current_event",
    "high_voltage_high_current_event",
]
LEAKAGE_FIELD_TOKENS = (
    "capacity_Ah_k1",
    "delta_capacity",
    "target",
    "pulse_k1",
    "eis_k1",
)


def build_interval_event_sequence_table(
    run_events_path: Path,
    interval_table_path: Path,
    out_path: Path,
    *,
    max_events: int = DEFAULT_MAX_EVENTS,
    seed: int = 42,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> pa.Table:
    """Build a fixed-length event-sequence table from streamed run events."""
    if max_events <= 0:
        raise ValueError("max_events must be positive.")
    if not run_events_path.exists():
        raise FileNotFoundError(f"Run-event table not found: {run_events_path}")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")

    intervals = pq.read_table(interval_table_path).to_pylist()
    interval_by_key = {_interval_key(row): row for row in intervals}
    if len(interval_by_key) != len(intervals):
        raise ValueError("Interval table contains duplicate interval keys.")

    event_counts = _count_events_by_interval(run_events_path, batch_size=batch_size)
    selected_indices = {
        key: set(_selected_event_indices(count, max_events))
        for key, count in event_counts.items()
    }
    selected_events = _load_selected_events(
        run_events_path,
        selected_indices,
        batch_size=batch_size,
    )

    rows = []
    for interval in intervals:
        key = _interval_key(interval)
        events = sorted(selected_events.get(key, []), key=lambda item: item[0])
        event_count = int(event_counts.get(key, 0))
        true_vectors = [vector for _, vector in events]
        shuffled_vectors = list(true_vectors)
        random.Random(_shuffle_seed(seed, interval)).shuffle(shuffled_vectors)
        selected_count = len(true_vectors)
        quality_flags = []
        if event_count == 0:
            quality_flags.append("missing_events")
        if event_count > max_events:
            quality_flags.append("truncated_events")
        rows.append(
            {
                "cell_id": str(interval["cell_id"]),
                "parameter_set": int(interval["parameter_set"]),
                "replicate_id": int(interval["replicate_id"]),
                "checkup_k": int(interval["checkup_k"]),
                "checkup_k_next": int(interval["checkup_k_next"]),
                "schema_version": SCHEMA_VERSION,
                "feature_policy_version": FEATURE_POLICY_VERSION,
                "max_events": int(max_events),
                "event_feature_count": len(EVENT_FEATURE_COLUMNS),
                "event_feature_columns": ",".join(EVENT_FEATURE_COLUMNS),
                "event_count": event_count,
                "selected_event_count": selected_count,
                "truncated_event_count": max(0, event_count - selected_count),
                "true_sequence_vector": _padded_vector(true_vectors, max_events),
                "shuffled_sequence_vector": _padded_vector(shuffled_vectors, max_events),
                "event_mask": [1 if idx < selected_count else 0 for idx in range(max_events)],
                "sequence_shuffle_seed": int(seed),
                "sequence_quality_flags": ";".join(quality_flags),
            }
        )

    table = pa.Table.from_pylist(rows, schema=INTERVAL_EVENT_SEQUENCE_TABLE_V1_SCHEMA)
    if not validate_table(table, INTERVAL_EVENT_SEQUENCE_TABLE_V1_SCHEMA):
        raise TypeError("Generated event-sequence table does not match schema.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"feature_policy_version": FEATURE_POLICY_VERSION.encode(),
            b"run_events_path": str(run_events_path).encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"max_events": str(max_events).encode(),
            b"shuffle_seed": str(seed).encode(),
        }
    )
    _write_parquet_atomic(table, out_path)
    return table


def write_interval_event_sequence_qa(
    event_sequences_path: Path,
    interval_table_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Write QA for the fixed-length event-sequence table."""
    if not event_sequences_path.exists():
        raise FileNotFoundError(f"Event-sequence table not found: {event_sequences_path}")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    rows = pq.read_table(event_sequences_path).to_pylist()
    intervals = pq.read_table(interval_table_path).to_pylist()
    interval_keys = {_interval_key(row) for row in intervals}
    row_keys = {_interval_key(row) for row in rows}
    vector_length_errors = 0
    mask_length_errors = 0
    leakage_columns = []
    for row in rows:
        expected = int(row["max_events"]) * int(row["event_feature_count"])
        if len(row["true_sequence_vector"]) != expected or len(row["shuffled_sequence_vector"]) != expected:
            vector_length_errors += 1
        if len(row["event_mask"]) != int(row["max_events"]):
            mask_length_errors += 1
        columns = str(row["event_feature_columns"]).split(",")
        leakage_columns.extend(
            column
            for column in columns
            if any(token in column for token in LEAKAGE_FIELD_TOKENS)
        )
    missing_intervals = sorted(interval_keys - row_keys)
    extra_intervals = sorted(row_keys - interval_keys)
    truncated = sum(int(row["truncated_event_count"]) > 0 for row in rows)
    missing_events = sum(int(row["event_count"]) == 0 for row in rows)
    warnings = []
    if missing_intervals:
        warnings.append("missing_intervals")
    if extra_intervals:
        warnings.append("extra_intervals")
    if vector_length_errors:
        warnings.append("vector_length_errors")
    if mask_length_errors:
        warnings.append("mask_length_errors")
    if leakage_columns:
        warnings.append("leakage_columns")
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "row_count": len(rows),
        "intervals": len(intervals),
        "missing_intervals": len(missing_intervals),
        "extra_intervals": len(extra_intervals),
        "truncated_intervals": truncated,
        "missing_event_intervals": missing_events,
        "event_count_summary": _summary([int(row["event_count"]) for row in rows]),
        "selected_event_count_summary": _summary(
            [int(row["selected_event_count"]) for row in rows]
        ),
        "vector_length_errors": vector_length_errors,
        "mask_length_errors": mask_length_errors,
        "leakage_check": {
            "status": "failed" if leakage_columns else "passed",
            "leakage_columns": sorted(set(leakage_columns)),
        },
        "warnings": warnings,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _count_events_by_interval(
    run_events_path: Path,
    *,
    batch_size: int,
) -> Counter[tuple[str, int, int]]:
    counts: Counter[tuple[str, int, int]] = Counter()
    for batch in pq.ParquetFile(run_events_path).iter_batches(
        columns=["cell_id", "checkup_k", "checkup_k_next"],
        batch_size=batch_size,
    ):
        data = batch.to_pydict()
        for idx, cell_id in enumerate(data["cell_id"]):
            counts[(str(cell_id), int(data["checkup_k"][idx]), int(data["checkup_k_next"][idx]))] += 1
    return counts


def _load_selected_events(
    run_events_path: Path,
    selected_indices: dict[tuple[str, int, int], set[int]],
    *,
    batch_size: int,
) -> dict[tuple[str, int, int], list[tuple[int, list[float]]]]:
    selected: dict[tuple[str, int, int], list[tuple[int, list[float]]]] = defaultdict(list)
    for batch in pq.ParquetFile(run_events_path).iter_batches(
        columns=EVENT_COLUMNS,
        batch_size=batch_size,
    ):
        data = batch.to_pydict()
        for idx, cell_id in enumerate(data["cell_id"]):
            key = (str(cell_id), int(data["checkup_k"][idx]), int(data["checkup_k_next"][idx]))
            event_index = int(data["event_index"][idx])
            if event_index not in selected_indices.get(key, set()):
                continue
            selected[key].append((event_index, _event_vector(data, idx)))
    return selected


def _event_vector(data: dict[str, list[Any]], idx: int) -> list[float]:
    event_type = str(data["event_type"][idx])
    return [
        1.0 if event_type == "rest" else 0.0,
        1.0 if event_type == "charge" else 0.0,
        1.0 if event_type == "discharge" else 0.0,
        1.0 if event_type == "unknown" else 0.0,
        _finite(data["event_duration_h"][idx]),
        _finite(data["mean_voltage_V"][idx]),
        _finite(data["mean_abs_current_A"][idx]),
        _finite(data["max_abs_current_A"][idx]),
        _finite(data["mean_temperature_C"][idx]),
        _finite(data["mean_soc"][idx]),
        _finite(data["delta_q_Ah"][idx]),
        _finite(data["delta_EFC"][idx]),
        1.0 if bool(data["high_voltage_event"][idx]) else 0.0,
        1.0 if bool(data["high_abs_current_event"][idx]) else 0.0,
        1.0 if bool(data["cold_high_current_event"][idx]) else 0.0,
        1.0 if bool(data["high_voltage_high_current_event"][idx]) else 0.0,
    ]


def _selected_event_indices(event_count: int, max_events: int) -> list[int]:
    if event_count <= 0:
        return []
    if event_count <= max_events:
        return list(range(event_count))
    indices: list[int] = []
    seen: set[int] = set()
    for idx in range(max_events):
        selected = round(idx * (event_count - 1) / max(1, max_events - 1))
        if selected not in seen:
            indices.append(selected)
            seen.add(selected)
    candidate = 0
    while len(indices) < max_events and candidate < event_count:
        if candidate not in seen:
            indices.append(candidate)
            seen.add(candidate)
        candidate += 1
    return sorted(indices)


def _padded_vector(vectors: list[list[float]], max_events: int) -> list[float]:
    width = len(EVENT_FEATURE_COLUMNS)
    output: list[float] = []
    for idx in range(max_events):
        if idx < len(vectors):
            output.extend(vectors[idx])
        else:
            output.extend([0.0] * width)
    return output


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return (str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"]))


def _shuffle_seed(seed: int, row: dict[str, Any]) -> int:
    return (
        int(seed)
        + int(row["parameter_set"]) * 100_000
        + int(row["replicate_id"]) * 1_000
        + int(row["checkup_k"])
    )


def _finite(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric if math.isfinite(numeric) else 0.0


def _summary(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "median": None, "mean": None, "max": None}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = (
        float(ordered[middle])
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    return {
        "min": int(ordered[0]),
        "median": median,
        "mean": sum(values) / len(values),
        "max": int(ordered[-1]),
    }


def _write_parquet_atomic(table: pa.Table, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    pq.write_table(table, tmp_path)
    tmp_path.replace(out_path)
