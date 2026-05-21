"""Writers for audit outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from mbp.audit.models import DatasetManifest, FileInventoryRecord, SCHEMA_VERSION

FILE_INVENTORY_FIELDS = [
    "schema_version",
    "relative_path",
    "file_name",
    "file_suffix",
    "file_family",
    "size_bytes",
    "modified_time_utc",
    "sha256",
    "row_count",
    "is_archive",
    "provenance_data_root",
    "provenance_tool",
    "provenance_generated_at_utc",
]


def write_manifest_json(manifest: DatasetManifest, out_path: Path) -> None:
    ensure_parent(out_path)
    with out_path.open("w", encoding="utf-8") as file_obj:
        json.dump(manifest.to_dict(), file_obj, indent=2, sort_keys=True)
        file_obj.write("\n")


def write_file_inventory(records: list[FileInventoryRecord], out_path: Path) -> None:
    suffix = out_path.suffix.lower()
    if suffix == ".parquet":
        write_file_inventory_parquet(records, out_path)
        return
    if suffix != ".csv":
        raise ValueError("file_inventory output must end with .csv or .parquet")
    write_file_inventory_csv(records, out_path)


def write_file_inventory_csv(records: list[FileInventoryRecord], out_path: Path) -> None:
    ensure_parent(out_path)
    with out_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=FILE_INVENTORY_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())


def write_sha256_manifest(records: list[FileInventoryRecord], out_path: Path) -> None:
    """Write MANIFEST.sha256 lines with digest and relative path."""

    ensure_parent(out_path)
    with out_path.open("w", encoding="utf-8") as file_obj:
        for record in sorted(records, key=lambda item: item.relative_path):
            file_obj.write(f"{record.sha256}  {record.relative_path}\n")


def write_file_inventory_parquet(records: list[FileInventoryRecord], out_path: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "Parquet output requires the optional dependency: uv sync --extra parquet"
        ) from exc

    ensure_parent(out_path)
    rows: list[dict[str, Any]] = [record.to_dict() for record in records]
    if not rows:
        rows = [{field: None for field in FILE_INVENTORY_FIELDS}]
        rows[0]["schema_version"] = SCHEMA_VERSION
    table = pa.Table.from_pylist(rows, schema=parquet_schema(pa))
    pq.write_table(table, out_path)


def parquet_schema(pa: Any) -> Any:
    return pa.schema(
        [
            pa.field("schema_version", pa.string()),
            pa.field("relative_path", pa.string()),
            pa.field("file_name", pa.string()),
            pa.field("file_suffix", pa.string()),
            pa.field("file_family", pa.string()),
            pa.field("size_bytes", pa.int64()),
            pa.field("modified_time_utc", pa.string()),
            pa.field("sha256", pa.string()),
            pa.field("row_count", pa.int64()),
            pa.field("is_archive", pa.bool_()),
            pa.field("provenance_data_root", pa.string()),
            pa.field("provenance_tool", pa.string()),
            pa.field("provenance_generated_at_utc", pa.string()),
        ]
    )


def ensure_parent(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
