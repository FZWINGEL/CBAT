"""Modality coverage summaries derived from file inventory evidence."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from mbp.audit.models import FileInventoryRecord, SCHEMA_VERSION

REQUIRED_MODALITIES = ("cfg", "eoc", "eis", "pulse", "log", "log_age")


@dataclass(frozen=True)
class ModalityCoverageRecord:
    schema_version: str
    modality: str
    file_count: int
    row_count: int | None
    total_size_bytes: int
    status: str
    evidence_paths: str
    provenance_tool: str
    provenance_generated_at_utc: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_modality_coverage(
    records: list[FileInventoryRecord],
    generated_at_utc: str,
) -> list[ModalityCoverageRecord]:
    by_family: dict[str, list[FileInventoryRecord]] = defaultdict(list)
    for record in records:
        by_family[record.file_family].append(record)

    coverage: list[ModalityCoverageRecord] = []
    for modality in REQUIRED_MODALITIES:
        family_records = by_family.get(modality, [])
        row_counts = [record.row_count for record in family_records if record.row_count is not None]
        coverage.append(
            ModalityCoverageRecord(
                schema_version=SCHEMA_VERSION,
                modality=modality,
                file_count=len(family_records),
                row_count=sum(row_counts) if row_counts else None,
                total_size_bytes=sum(record.size_bytes for record in family_records),
                status="observed" if family_records else "missing",
                evidence_paths=";".join(record.relative_path for record in family_records[:25]),
                provenance_tool="mbp audit manifest",
                provenance_generated_at_utc=generated_at_utc,
            )
        )
    return coverage


def write_modality_coverage(
    records: list[ModalityCoverageRecord],
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "schema_version",
        "modality",
        "file_count",
        "row_count",
        "total_size_bytes",
        "status",
        "evidence_paths",
        "provenance_tool",
        "provenance_generated_at_utc",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
