"""Build local file and archive inventories without assuming dataset presence."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from mbp.audit.hashing import sha256_file
from mbp.audit.models import ArchiveInventoryRecord, FileInventoryRecord, SCHEMA_VERSION

ARCHIVE_SUFFIXES = {
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}

FAMILY_KEYWORDS = {
    "cfg": ("cfg", "config", "structure"),
    "eoc": ("eoc",),
    "eis": ("eis", "impedance"),
    "pulse": ("pulse",),
    "log_age": ("log_age", "log-age", "logage"),
    "log": ("log",),
    "pool_log": ("pool",),
    "slave_log": ("slave",),
    "plausibility": ("plausibility", "quality"),
}


def build_inventory(
    data_root: Path, generated_at_utc: str | None = None
) -> list[FileInventoryRecord]:
    """Return file inventory records for all files under ``data_root``."""

    generated_at_utc = generated_at_utc or utc_now_iso()
    if not data_root.exists():
        return []

    records: list[FileInventoryRecord] = []
    for path in sorted(item for item in data_root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(data_root).as_posix()
        suffix = full_suffix(path)
        records.append(
            FileInventoryRecord(
                schema_version=SCHEMA_VERSION,
                relative_path=relative_path,
                file_name=path.name,
                file_suffix=suffix,
                file_family=infer_file_family(relative_path),
                size_bytes=path.stat().st_size,
                modified_time_utc=datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                sha256=sha256_file(path),
                row_count=count_rows_if_tabular(path),
                is_archive=is_archive_path(path),
                provenance_data_root=str(data_root),
                provenance_tool="mbp audit inventory",
                provenance_generated_at_utc=generated_at_utc,
            )
        )
    return records


def build_archive_inventory(
    file_records: list[FileInventoryRecord],
) -> list[ArchiveInventoryRecord]:
    """Return archive inventory records derived from file inventory records."""

    archives: list[ArchiveInventoryRecord] = []
    for record in file_records:
        if not record.is_archive:
            continue
        archives.append(
            ArchiveInventoryRecord(
                schema_version=record.schema_version,
                archive_name=record.file_name,
                relative_path=record.relative_path,
                size_bytes=record.size_bytes,
                sha256=record.sha256,
                extracted_file_count=None,
                doi=None,
                source=None,
                date_downloaded=None,
                provenance_data_root=record.provenance_data_root,
                provenance_tool=record.provenance_tool,
                provenance_generated_at_utc=record.provenance_generated_at_utc,
            )
        )
    return archives


def infer_file_family(relative_path: str) -> str:
    """Infer a coarse dataset family from the path name."""

    normalized = relative_path.lower()
    for family, keywords in FAMILY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return family
    return "unknown"


def is_archive_path(path: Path) -> bool:
    suffixes = {suffix.lower() for suffix in path.suffixes}
    return bool(suffixes & ARCHIVE_SUFFIXES)


def full_suffix(path: Path) -> str:
    return "".join(path.suffixes).lower()


def count_rows_if_tabular(path: Path) -> int | None:
    """Count data rows for simple delimited text files.

    The count excludes one header row when at least one row exists. Binary and unknown files
    return ``None`` because Gate 1 should not infer schemas from opaque archives.
    """

    if path.suffix.lower() not in {".csv", ".tsv"}:
        return None

    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as file_obj:
            row_count = sum(1 for _ in csv.reader(file_obj, delimiter=delimiter))
    except UnicodeDecodeError:
        return None
    return max(row_count - 1, 0)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
