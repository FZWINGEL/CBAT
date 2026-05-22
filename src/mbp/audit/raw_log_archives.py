"""Raw LOG archive inventory without full parsing or extraction."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import py7zr

from mbp.audit.archives import extract_cell_id

RAW_LOG_ARCHIVE_SCHEMA = pa.schema(
    [
        ("archive_name", pa.string(), False),
        ("member_name", pa.string(), False),
        ("cell_id", pa.string(), True),
        ("uncompressed_size_bytes", pa.int64(), True),
        ("inferred_log_type", pa.string(), False),
        ("pool_logs_exist", pa.bool_(), False),
        ("slave_logs_exist", pa.bool_(), False),
        ("sampled_header", pa.string(), True),
        ("scheduler_state_columns_available", pa.bool_(), True),
    ]
)


def inventory_raw_log_archives(data_root: Path, out_path: Path) -> pa.Table:
    """Inventory raw LOG 7z members and sample at most one member header."""
    if not data_root.exists():
        raise FileNotFoundError(f"Raw LOG data root not found: {data_root}")

    archive_paths = sorted(data_root.rglob("*.7z"))
    pool_logs_exist = any("pool" in path.name.lower() for path in archive_paths)
    slave_logs_exist = any("slave" in path.name.lower() for path in archive_paths)
    sampled = False
    rows: list[dict[str, object]] = []

    for archive_path in archive_paths:
        inferred_type = _infer_log_type(archive_path.name)
        with py7zr.SevenZipFile(archive_path, "r") as archive:
            members = archive.list()
            for member in members:
                member_name = member.filename
                if member.is_directory:
                    continue
                sampled_header = None
                scheduler_columns = None
                if not sampled and extract_cell_id(member_name):
                    sampled_header = _sample_member_header(archive_path, member_name)
                    scheduler_columns = (
                        _has_scheduler_columns(sampled_header)
                        if sampled_header is not None
                        else None
                    )
                    sampled = True
                rows.append(
                    {
                        "archive_name": archive_path.name,
                        "member_name": member_name,
                        "cell_id": extract_cell_id(member_name),
                        "uncompressed_size_bytes": getattr(member, "uncompressed", None),
                        "inferred_log_type": inferred_type,
                        "pool_logs_exist": pool_logs_exist,
                        "slave_logs_exist": slave_logs_exist,
                        "sampled_header": sampled_header,
                        "scheduler_state_columns_available": scheduler_columns,
                    }
                )

    table = pa.Table.from_pylist(rows, schema=RAW_LOG_ARCHIVE_SCHEMA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table


def _infer_log_type(name: str) -> str:
    lower = name.lower()
    if "log_age" in lower:
        return "log_age"
    if "logext" in lower or "cell_log" in lower:
        return "cell_log"
    if "pool" in lower:
        return "pool_log"
    if "slave" in lower:
        return "slave_log"
    return "unknown"


def _sample_member_header(archive_path: Path, member_name: str) -> str | None:
    temp_dir = Path(tempfile.mkdtemp(prefix="mbp_raw_log_sample_"))
    try:
        with py7zr.SevenZipFile(archive_path, "r") as archive:
            archive.extract(path=temp_dir, targets=[member_name])
        extracted = temp_dir / member_name
        if not extracted.exists():
            matches = [path for path in temp_dir.rglob("*") if path.is_file()]
            extracted = matches[0] if matches else extracted
        with extracted.open("r", encoding="utf-8", errors="replace") as f:
            return f.readline().strip()
    except Exception:
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _has_scheduler_columns(header: str | None) -> bool:
    if not header:
        return False
    lower = header.lower()
    return "scheduler" in lower or "state" in lower or "status" in lower
