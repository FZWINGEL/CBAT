"""Streaming LOG_AGE monotonicity violation reports."""

from __future__ import annotations

import csv
from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
import heapq
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

DETAIL_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("source_file", pa.string(), False),
        ("row_group_idx", pa.int64(), False),
        ("local_row_idx", pa.int64(), False),
        ("previous_timestamp_s", pa.float64(), False),
        ("current_timestamp_s", pa.float64(), False),
        ("delta_timestamp_s", pa.float64(), False),
        ("previous_EFC", pa.float64(), False),
        ("current_EFC", pa.float64(), False),
        ("delta_EFC", pa.float64(), False),
        ("violation_type", pa.string(), False),
        ("magnitude_bucket", pa.string(), False),
    ]
)

SCAN_COLUMNS = ["cell_id", "source_file", "timestamp_s", "EFC"]
SUMMARY_FIELDS = [
    "summary_scope",
    "summary_key",
    "violation_count",
    "timestamp_decrease_count",
    "efc_decrease_count",
    "both_count",
    "max_timestamp_drop_s",
    "max_efc_drop",
]

DEFAULT_BATCH_SIZE_ROWS = 1_048_576


@dataclass
class Summary:
    violation_count: int = 0
    timestamp_decrease_count: int = 0
    efc_decrease_count: int = 0
    both_count: int = 0
    max_timestamp_drop_s: float = 0.0
    max_efc_drop: float = 0.0

    def update(self, violation_type: str, timestamp_drop: float, efc_drop: float) -> None:
        self.violation_count += 1
        if violation_type in ("timestamp_decrease", "both"):
            self.timestamp_decrease_count += 1
        if violation_type in ("efc_decrease", "both"):
            self.efc_decrease_count += 1
        if violation_type == "both":
            self.both_count += 1
        self.max_timestamp_drop_s = max(self.max_timestamp_drop_s, timestamp_drop)
        self.max_efc_drop = max(self.max_efc_drop, efc_drop)


@dataclass(frozen=True)
class RowRecord:
    cell_id: str
    source_file: str
    timestamp: float
    efc: float
    global_row_idx: int


def write_log_age_monotonicity_report(
    log_age_path: Path,
    out_path: Path,
    summary_path: Path,
    timestamp_epsilon_s: float = 0.0,
    efc_epsilon: float = 1e-9,
    workers: int | None = None,
    batch_size_rows: int = DEFAULT_BATCH_SIZE_ROWS,
) -> dict[str, object]:
    """Scan LOG_AGE Parquet row groups and write detailed monotonicity violations."""
    if timestamp_epsilon_s < 0:
        raise ValueError("timestamp_epsilon_s must be non-negative")
    if efc_epsilon < 0:
        raise ValueError("efc_epsilon must be non-negative")
    if batch_size_rows <= 0:
        raise ValueError("batch_size_rows must be positive")
    if not log_age_path.exists():
        raise FileNotFoundError(f"LOG_AGE Parquet not found: {log_age_path}")

    parquet_file = pq.ParquetFile(log_age_path)
    worker_count = workers or min(10, pa.cpu_count())
    worker_count = max(1, worker_count)
    previous_cpu_count = pa.cpu_count()
    previous_io_thread_count = pa.io_thread_count()
    pa.set_cpu_count(worker_count)
    pa.set_io_thread_count(worker_count)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    temp_out_path = out_path.with_name(f"{out_path.name}.tmp")
    temp_summary_path = summary_path.with_name(f"{summary_path.name}.tmp")
    if temp_out_path.exists():
        temp_out_path.unlink()
    if temp_summary_path.exists():
        temp_summary_path.unlink()

    by_cell: dict[str, Summary] = defaultdict(Summary)
    by_source_file: dict[str, Summary] = defaultdict(Summary)
    by_type: Counter[str] = Counter()
    top_violations_heap: list[tuple[tuple[float, float, float], int, dict[str, object]]] = []
    top_violations_seen = 0
    previous_by_cell: dict[str, tuple[str, float, float]] = {}
    writer: pq.ParquetWriter | None = None
    total = 0

    try:
        row_group_starts = _row_group_starts(parquet_file)
        results = _iter_batch_results(
            parquet_file,
            row_group_starts,
            timestamp_epsilon_s,
            efc_epsilon,
            use_threads=worker_count > 1,
            batch_size_rows=batch_size_rows,
        )

        for detail_rows, first_record, last_record in results:
            if first_record is not None:
                cell_id = first_record.cell_id
                source_file = first_record.source_file
                timestamp = first_record.timestamp
                efc = first_record.efc
                previous = previous_by_cell.get(cell_id)
                if previous is not None:
                    row_group_idx, local_row_idx = _row_location(
                        first_record.global_row_idx, row_group_starts
                    )
                    _, previous_timestamp, previous_efc = previous
                    detail = _detail_if_violation(
                        cell_id=cell_id,
                        source_file=source_file,
                        row_group_idx=row_group_idx,
                        local_row_idx=local_row_idx,
                        previous_timestamp=previous_timestamp,
                        current_timestamp=timestamp,
                        previous_efc=previous_efc,
                        current_efc=efc,
                        timestamp_epsilon_s=timestamp_epsilon_s,
                        efc_epsilon=efc_epsilon,
                    )
                    if detail:
                        detail_rows.insert(0, detail)

            for detail in detail_rows:
                cell_id = str(detail["cell_id"])
                source_file = str(detail["source_file"])
                violation_type = str(detail["violation_type"])
                timestamp_drop = max(0.0, -float(detail["delta_timestamp_s"]))
                efc_drop = max(0.0, -float(detail["delta_EFC"]))
                by_cell[cell_id].update(violation_type, timestamp_drop, efc_drop)
                by_source_file[source_file].update(violation_type, timestamp_drop, efc_drop)
                by_type[violation_type] += 1
                top_violations_seen += 1
                _retain_top_violation(top_violations_heap, top_violations_seen, detail)
                total += 1

            if detail_rows:
                detail_table = pa.Table.from_pylist(detail_rows, schema=DETAIL_SCHEMA)
                if writer is None:
                    writer = pq.ParquetWriter(temp_out_path, DETAIL_SCHEMA)
                writer.write_table(detail_table)
                del detail_table
            if last_record is not None:
                previous_by_cell[last_record.cell_id] = (
                    last_record.source_file,
                    last_record.timestamp,
                    last_record.efc,
                )
            detail_rows.clear()
            pa.default_memory_pool().release_unused()
    finally:
        pa.set_cpu_count(previous_cpu_count)
        pa.set_io_thread_count(previous_io_thread_count)
        if writer is not None:
            writer.close()

    if writer is None:
        pq.write_table(pa.Table.from_batches([], schema=DETAIL_SCHEMA), temp_out_path)

    top_violations = [
        item[2] for item in sorted(top_violations_heap, key=lambda item: item[0], reverse=True)
    ]
    _write_summary_csv(temp_summary_path, by_cell, by_source_file, top_violations)
    temp_out_path.replace(out_path)
    temp_summary_path.replace(summary_path)

    return {
        "violation_count": total,
        "timestamp_decrease_count": by_type["timestamp_decrease"] + by_type["both"],
        "efc_decrease_count": by_type["efc_decrease"] + by_type["both"],
        "both_count": by_type["both"],
        "cells_with_violations": len(by_cell),
        "source_files_with_violations": len(by_source_file),
        "top_20_worst": top_violations,
    }


def _write_summary_csv(
    summary_path: Path,
    by_cell: dict[str, Summary],
    by_source_file: dict[str, Summary],
    top_violations: list[dict[str, object]],
) -> None:
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for scope, summaries in (("cell", by_cell), ("source_file", by_source_file)):
            for key, summary in sorted(summaries.items()):
                writer.writerow(_summary_row(scope, key, summary))
        for idx, violation in enumerate(top_violations, start=1):
            summary = Summary()
            summary.update(
                str(violation["violation_type"]),
                max(0.0, -float(violation["delta_timestamp_s"])),
                max(0.0, -float(violation["delta_EFC"])),
            )
            writer.writerow(_summary_row("top20", str(idx), summary))


def _row_group_starts(parquet_file: pq.ParquetFile) -> list[int]:
    starts = [0]
    for idx in range(parquet_file.metadata.num_row_groups):
        starts.append(starts[-1] + parquet_file.metadata.row_group(idx).num_rows)
    return starts


def _row_location(global_row_idx: int, row_group_starts: list[int]) -> tuple[int, int]:
    row_group_idx = bisect_right(row_group_starts, global_row_idx) - 1
    return row_group_idx, global_row_idx - row_group_starts[row_group_idx]


def _iter_batch_results(
    parquet_file: pq.ParquetFile,
    row_group_starts: list[int],
    timestamp_epsilon_s: float,
    efc_epsilon: float,
    *,
    use_threads: bool,
    batch_size_rows: int,
):
    global_row_start = 0
    for batch in parquet_file.iter_batches(
        batch_size=batch_size_rows,
        columns=SCAN_COLUMNS,
        use_threads=use_threads,
    ):
        table = pa.Table.from_batches([batch])
        detail_rows, first_record, last_record = _detect_batch_violations(
            table,
            row_group_starts,
            global_row_start,
            timestamp_epsilon_s,
            efc_epsilon,
        )
        global_row_start += batch.num_rows
        del table
        del batch
        pa.default_memory_pool().release_unused()
        yield detail_rows, first_record, last_record


def _detect_batch_violations(
    table: pa.Table,
    row_group_starts: list[int],
    global_row_start: int,
    timestamp_epsilon_s: float,
    efc_epsilon: float,
) -> tuple[list[dict[str, object]], RowRecord | None, RowRecord | None]:
    rows = table.num_rows
    if rows == 0:
        return [], None, None

    cell = table.column("cell_id").combine_chunks()
    source = table.column("source_file").combine_chunks()
    timestamps = table.column("timestamp_s").combine_chunks()
    efc = table.column("EFC").combine_chunks()
    detail_rows: list[dict[str, object]] = []

    if rows > 1:
        import pyarrow.compute as pc

        timestamp_diff = pc.pairwise_diff(timestamps).slice(1)
        efc_diff = pc.pairwise_diff(efc).slice(1)
        same_cell = pc.equal(cell.slice(1), cell.slice(0, rows - 1))
        timestamp_bad = pc.less(timestamp_diff, -timestamp_epsilon_s)
        efc_bad = pc.less(efc_diff, -efc_epsilon)
        violation_mask = pc.and_(same_cell, pc.or_(timestamp_bad, efc_bad))
        for diff_idx in pc.indices_nonzero(violation_mask).to_pylist():
            local_row_idx = int(diff_idx) + 1
            previous_idx = local_row_idx - 1
            global_row_idx = global_row_start + local_row_idx
            row_group_idx, row_group_local_idx = _row_location(
                global_row_idx, row_group_starts
            )
            detail = _detail_if_violation(
                cell_id=str(cell[local_row_idx].as_py()),
                source_file=str(source[local_row_idx].as_py()),
                row_group_idx=row_group_idx,
                local_row_idx=row_group_local_idx,
                previous_timestamp=float(timestamps[previous_idx].as_py()),
                current_timestamp=float(timestamps[local_row_idx].as_py()),
                previous_efc=float(efc[previous_idx].as_py()),
                current_efc=float(efc[local_row_idx].as_py()),
                timestamp_epsilon_s=timestamp_epsilon_s,
                efc_epsilon=efc_epsilon,
            )
            if detail:
                detail_rows.append(detail)

    first_record = RowRecord(
        cell_id=str(cell[0].as_py()),
        source_file=str(source[0].as_py()),
        timestamp=float(timestamps[0].as_py()),
        efc=float(efc[0].as_py()),
        global_row_idx=global_row_start,
    )
    last_record = RowRecord(
        cell_id=str(cell[rows - 1].as_py()),
        source_file=str(source[rows - 1].as_py()),
        timestamp=float(timestamps[rows - 1].as_py()),
        efc=float(efc[rows - 1].as_py()),
        global_row_idx=global_row_start + rows - 1,
    )
    return detail_rows, first_record, last_record


def _retain_top_violation(
    heap: list[tuple[tuple[float, float, float], int, dict[str, object]]],
    sequence: int,
    detail: dict[str, object],
) -> None:
    item = (_violation_rank_key(detail), sequence, detail)
    if len(heap) < 20:
        heapq.heappush(heap, item)
    elif item[0] > heap[0][0]:
        heapq.heapreplace(heap, item)


def _violation_rank_key(row: dict[str, object]) -> tuple[float, float, float]:
    timestamp_delta = abs(float(row["delta_timestamp_s"]))
    efc_delta = abs(float(row["delta_EFC"]))
    return (max(timestamp_delta, efc_delta), timestamp_delta, efc_delta)


def _detail_if_violation(
    *,
    cell_id: str,
    source_file: str,
    row_group_idx: int,
    local_row_idx: int,
    previous_timestamp: float,
    current_timestamp: float,
    previous_efc: float,
    current_efc: float,
    timestamp_epsilon_s: float,
    efc_epsilon: float,
) -> dict[str, object] | None:
    delta_timestamp = current_timestamp - previous_timestamp
    delta_efc = current_efc - previous_efc
    timestamp_bad = delta_timestamp < -timestamp_epsilon_s
    efc_bad = delta_efc < -efc_epsilon
    if not (timestamp_bad or efc_bad):
        return None
    violation_type = _violation_type(timestamp_bad, efc_bad)
    timestamp_drop = max(0.0, -delta_timestamp)
    efc_drop = max(0.0, -delta_efc)
    return {
        "cell_id": cell_id,
        "source_file": source_file,
        "row_group_idx": row_group_idx,
        "local_row_idx": local_row_idx,
        "previous_timestamp_s": previous_timestamp,
        "current_timestamp_s": current_timestamp,
        "delta_timestamp_s": delta_timestamp,
        "previous_EFC": previous_efc,
        "current_EFC": current_efc,
        "delta_EFC": delta_efc,
        "violation_type": violation_type,
        "magnitude_bucket": _magnitude_bucket(timestamp_drop, efc_drop),
    }


def _summary_row(scope: str, key: str, summary: Summary) -> dict[str, object]:
    return {
        "summary_scope": scope,
        "summary_key": key,
        "violation_count": summary.violation_count,
        "timestamp_decrease_count": summary.timestamp_decrease_count,
        "efc_decrease_count": summary.efc_decrease_count,
        "both_count": summary.both_count,
        "max_timestamp_drop_s": summary.max_timestamp_drop_s,
        "max_efc_drop": summary.max_efc_drop,
    }


def _violation_type(timestamp_bad: bool, efc_bad: bool) -> str:
    if timestamp_bad and efc_bad:
        return "both"
    if timestamp_bad:
        return "timestamp_decrease"
    return "efc_decrease"


def _magnitude_bucket(timestamp_drop: float, efc_drop: float) -> str:
    magnitude = max(timestamp_drop, efc_drop)
    if magnitude <= 1e-9:
        return "tiny"
    if magnitude <= 1.0:
        return "small"
    if magnitude <= 60.0:
        return "medium"
    if magnitude <= 3600.0:
        return "large"
    return "severe"
