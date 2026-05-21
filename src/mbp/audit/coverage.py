"""Modality coverage summaries derived from file inventory and archive evidence."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from mbp.audit.models import FileInventoryRecord, SCHEMA_VERSION

REQUIRED_MODALITIES = ("cfg", "eoc", "eis", "pulse", "log", "log_age")
EXPECTED_CELL_IDS = [f"P{p:03d}_{r}" for p in range(1, 77) for r in range(1, 4)]
CELL_ID_PATTERN = re.compile(r"P\d{3}_\d")


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
    # New coverage metrics with defaults to preserve backwards compatibility
    expected_cells: int = 0
    observed_cells: int = 0
    missing_cells_count: int = 0
    coverage_ratio: float = 0.0
    parameter_sets_with_any_replicate: int = 0
    parameter_sets_with_all_replicates: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def extract_cell_id(name: str) -> str | None:
    match = CELL_ID_PATTERN.search(name)
    return match.group(0) if match else None


def build_modality_coverage(
    records: list[FileInventoryRecord],
    generated_at_utc: str,
) -> list[ModalityCoverageRecord]:
    # 1. Fetch zip members list if possible
    zip_members = []
    if records:
        try:
            data_root = Path(records[0].provenance_data_root)
            if data_root.exists():
                from mbp.audit.archives import inventory_zip_archives

                zip_members = inventory_zip_archives(data_root)
        except Exception:
            pass

    # Group loose records by family
    loose_by_family: dict[str, list[FileInventoryRecord]] = defaultdict(list)
    for record in records:
        loose_by_family[record.file_family].append(record)

    # Group zip members by family
    zip_by_family = defaultdict(list)
    for member in zip_members:
        zip_by_family[member.inferred_modality].append(member)

    coverage: list[ModalityCoverageRecord] = []

    for modality in REQUIRED_MODALITIES:
        family_loose = loose_by_family.get(modality, [])
        family_zip = zip_by_family.get(modality, [])

        # Count total files/members
        file_count = len(family_loose)
        if family_zip:
            # If we have zip members, count the zip members
            file_count += len(family_zip)

        total_size_bytes = sum(record.size_bytes for record in family_loose) + sum(
            m.uncompressed_size_bytes for m in family_zip
        )

        row_counts = [record.row_count for record in family_loose if record.row_count is not None]
        row_count = sum(row_counts) if row_counts else None

        # Find observed cell IDs from both loose files and zip members
        observed_cell_ids: set[str] = set()
        for r in family_loose:
            cid = extract_cell_id(r.file_name)
            if cid:
                observed_cell_ids.add(cid)
        for m in family_zip:
            if m.cell_id:
                observed_cell_ids.add(m.cell_id)

        # Compute coverage metrics
        is_diagnostics = modality in ("cfg", "eoc", "eis", "pulse")
        expected_cells_count = len(EXPECTED_CELL_IDS) if is_diagnostics else 0

        expected_set = set(EXPECTED_CELL_IDS)
        observed_expected = observed_cell_ids & expected_set

        observed_cells_count = len(observed_expected) if is_diagnostics else len(observed_cell_ids)
        missing_cells_count = expected_cells_count - observed_cells_count if is_diagnostics else 0
        coverage_ratio = (
            observed_cells_count / expected_cells_count if expected_cells_count > 0 else 0.0
        )

        # Calculate replicates & parameter sets coverage
        any_rep_count = 0
        all_rep_count = 0

        if is_diagnostics:
            for p in range(1, 77):
                p_str = f"P{p:03d}"
                replicates = [f"{p_str}_1", f"{p_str}_2", f"{p_str}_3"]
                observed_reps = [r for r in replicates if r in observed_expected]
                if len(observed_reps) > 0:
                    any_rep_count += 1
                if len(observed_reps) == 3:
                    all_rep_count += 1

        # Determine status
        if is_diagnostics:
            if observed_cells_count == expected_cells_count and expected_cells_count > 0:
                status = "complete"
            elif observed_cells_count > 0:
                status = "incomplete"
            else:
                status = "observed" if file_count > 0 else "missing"
        else:
            status = "observed" if file_count > 0 else "missing"

        # Construct evidence paths preview
        paths = [r.relative_path for r in family_loose] + [
            f"{m.archive_name}::{m.member_name}" for m in family_zip
        ]
        evidence_paths = ";".join(paths[:25])

        coverage.append(
            ModalityCoverageRecord(
                schema_version=SCHEMA_VERSION,
                modality=modality,
                file_count=file_count,
                row_count=row_count,
                total_size_bytes=total_size_bytes,
                status=status,
                evidence_paths=evidence_paths,
                provenance_tool="mbp audit coverage",
                provenance_generated_at_utc=generated_at_utc,
                expected_cells=expected_cells_count,
                observed_cells=observed_cells_count,
                missing_cells_count=missing_cells_count,
                coverage_ratio=coverage_ratio,
                parameter_sets_with_any_replicate=any_rep_count,
                parameter_sets_with_all_replicates=all_rep_count,
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
        "expected_cells",
        "observed_cells",
        "missing_cells_count",
        "coverage_ratio",
        "parameter_sets_with_any_replicate",
        "parameter_sets_with_all_replicates",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
