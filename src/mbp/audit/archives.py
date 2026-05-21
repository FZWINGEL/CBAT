"""Introspect zip archives and inventory their contents without extraction."""

from __future__ import annotations

import csv
import re
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from mbp.audit.inventory import utc_now_iso

SCHEMA_VERSION = "gate1.audit.archives.v1"

CELL_ID_PATTERN = re.compile(r"P\d{3}_\d")

MODALITY_KEYWORDS = {
    "cfg": ("cfg", "config"),
    "eoc": ("eoc",),
    "eis": ("eis", "impedance"),
    "pulse": ("pulse", "pls"),
    "log_age": ("log_age", "log-age", "logage"),
    "log": ("log",),
}

ARCHIVE_FIELDS = [
    "schema_version",
    "archive_name",
    "archive_relative_path",
    "member_name",
    "compressed_size_bytes",
    "uncompressed_size_bytes",
    "suffix",
    "inferred_modality",
    "cell_id",
    "provenance_data_root",
    "provenance_tool",
    "provenance_generated_at_utc",
]


@dataclass(frozen=True)
class ZipMemberRecord:
    schema_version: str
    archive_name: str
    archive_relative_path: str
    member_name: str
    compressed_size_bytes: int
    uncompressed_size_bytes: int
    suffix: str
    inferred_modality: str
    cell_id: str | None
    provenance_data_root: str
    provenance_tool: str
    provenance_generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def infer_modality_from_name(name: str) -> str:
    normalized = name.lower()
    for modality, keywords in MODALITY_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return modality
    return "unknown"


def extract_cell_id(name: str) -> str | None:
    match = CELL_ID_PATTERN.search(name)
    return match.group(0) if match else None


def inventory_zip_archives(data_root: Path) -> list[ZipMemberRecord]:
    """Inspect all zip files inside ``data_root`` and inventory their members.

    Does not extract files from the archives.
    """
    generated_at_utc = utc_now_iso()
    records: list[ZipMemberRecord] = []

    if not data_root.exists():
        return []

    # Find all zip files under data_root recursively
    zip_paths = sorted(
        p for p in data_root.rglob("*") if p.is_file() and p.suffix.lower() == ".zip"
    )

    for zip_path in zip_paths:
        archive_relative_path = zip_path.relative_to(data_root).as_posix()
        archive_name = zip_path.name

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    # Skip directory members
                    if info.is_dir():
                        continue

                    member_name = info.filename
                    suffix = Path(member_name).suffix.lower()

                    # Infer modality from either archive name or member name
                    modality = infer_modality_from_name(archive_name)
                    if modality == "unknown":
                        modality = infer_modality_from_name(member_name)

                    cell_id = extract_cell_id(member_name)

                    records.append(
                        ZipMemberRecord(
                            schema_version=SCHEMA_VERSION,
                            archive_name=archive_name,
                            archive_relative_path=archive_relative_path,
                            member_name=member_name,
                            compressed_size_bytes=info.compress_size,
                            uncompressed_size_bytes=info.file_size,
                            suffix=suffix,
                            inferred_modality=modality,
                            cell_id=cell_id,
                            provenance_data_root=str(data_root),
                            provenance_tool="mbp audit archives",
                            provenance_generated_at_utc=generated_at_utc,
                        )
                    )
        except zipfile.BadZipFile:
            # Handle corrupted zip files or skip with warning
            pass

    return records


def write_archive_inventory(records: list[ZipMemberRecord], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = out_path.suffix.lower()
    if suffix == ".parquet":
        write_archive_inventory_parquet(records, out_path)
    elif suffix == ".csv":
        write_archive_inventory_csv(records, out_path)
    else:
        raise ValueError("Archive inventory output must end with .csv or .parquet")


def write_archive_inventory_csv(records: list[ZipMemberRecord], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())


def write_archive_inventory_parquet(records: list[ZipMemberRecord], out_path: Path) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Parquet output requires pyarrow: uv sync --extra parquet") from exc

    rows = [r.to_dict() for r in records]
    if not rows:
        rows = [{field: None for field in ARCHIVE_FIELDS}]
        rows[0]["schema_version"] = SCHEMA_VERSION

    schema = pa.schema(
        [
            pa.field("schema_version", pa.string()),
            pa.field("archive_name", pa.string()),
            pa.field("archive_relative_path", pa.string()),
            pa.field("member_name", pa.string()),
            pa.field("compressed_size_bytes", pa.int64()),
            pa.field("uncompressed_size_bytes", pa.int64()),
            pa.field("suffix", pa.string()),
            pa.field("inferred_modality", pa.string()),
            pa.field("cell_id", pa.string()),
            pa.field("provenance_data_root", pa.string()),
            pa.field("provenance_tool", pa.string()),
            pa.field("provenance_generated_at_utc", pa.string()),
        ]
    )

    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, out_path)


def print_archive_summary(records: list[ZipMemberRecord]) -> None:
    """Print counts of zip members by modality and cell_id."""
    modality_counts = Counter(r.inferred_modality for r in records)
    cell_counts = Counter(r.cell_id for r in records if r.cell_id is not None)

    print("=== Archive Inventory Summary ===")
    print(f"Total zip members inventoried: {len(records)}")
    print("\nMembers by modality:")
    for mod, count in sorted(modality_counts.items()):
        print(f"  {mod}: {count}")

    print("\nDistinct Cell IDs observed:")
    print(f"  Total cell IDs: {len(cell_counts)}")
    if cell_counts:
        top_cells = cell_counts.most_common(5)
        print("  Top 5 cells by member count:")
        for cell_id, count in top_cells:
            print(f"    {cell_id}: {count} members")
