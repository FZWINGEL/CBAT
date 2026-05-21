"""Dataset manifest assembly."""

from __future__ import annotations

import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from mbp import __version__
from mbp.audit.inventory import build_archive_inventory, build_inventory, utc_now_iso
from mbp.audit.models import DatasetManifest, FileInventoryRecord, Provenance, SCHEMA_VERSION

EXPECTED_AUDIT_REQUIREMENTS = [
    "archive name, DOI, source, and download date",
    "SHA-256 hash for every observed file and archive",
    "extracted file count for each archive",
    "row count by file family where tabular rows can be counted safely",
    "cell count by modality",
    "condition count and 76 parameter sets x 3 replicate verification",
    "EIS coverage by cell/SOC/temperature/check-up",
    "PULSE coverage by cell/SOC/temperature/check-up",
    "LOG and LOG_AGE availability",
    "known anomalies and data gaps",
    "preprocessing script commit hash",
    "generated table schema version",
]

MODALITY_FAMILIES = ("cfg", "eoc", "eis", "pulse", "log", "log_age")


def build_manifest(data_root: Path) -> DatasetManifest:
    generated_at_utc = utc_now_iso()
    file_inventory = build_inventory(data_root, generated_at_utc=generated_at_utc)
    archive_inventory = build_archive_inventory(file_inventory)
    provenance = Provenance(
        schema_version=SCHEMA_VERSION,
        generated_at_utc=generated_at_utc,
        tool_name="mbp audit manifest",
        tool_version=__version__,
        data_root_input=str(data_root),
        data_root_exists=data_root.exists(),
        preprocessing_commit=current_commit(Path.cwd()),
    )

    return DatasetManifest(
        provenance=provenance,
        archive_inventory=archive_inventory,
        file_inventory=file_inventory,
        file_count=len(file_inventory),
        archive_count=len(archive_inventory),
        total_size_bytes=sum(record.size_bytes for record in file_inventory),
        row_count_by_file_family=row_counts_by_family(file_inventory),
        file_count_by_family=dict(Counter(record.file_family for record in file_inventory)),
        modality_file_count=modality_file_counts(file_inventory),
        expected_audit_requirements=EXPECTED_AUDIT_REQUIREMENTS,
        known_anomalies=[],
        audit_warnings=audit_warnings(data_root, file_inventory),
    )


def row_counts_by_family(records: list[FileInventoryRecord]) -> dict[str, int]:
    counts: defaultdict[str, int] = defaultdict(int)
    for record in records:
        if record.row_count is not None:
            counts[record.file_family] += record.row_count
    return dict(counts)


def modality_file_counts(records: list[FileInventoryRecord]) -> dict[str, int]:
    family_counts = Counter(record.file_family for record in records)
    return {family: family_counts.get(family, 0) for family in MODALITY_FAMILIES}


def audit_warnings(data_root: Path, records: list[FileInventoryRecord]) -> list[str]:
    warnings: list[str] = []
    if not data_root.exists():
        warnings.append("data_root does not exist; manifest contains no dataset file evidence")
        return warnings
    if not records:
        warnings.append("data_root exists but no files were found")
    missing_modalities = [
        family for family, count in modality_file_counts(records).items() if count == 0
    ]
    if missing_modalities:
        warnings.append("no files detected for modalities: " + ", ".join(missing_modalities))
    return warnings


def current_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None
