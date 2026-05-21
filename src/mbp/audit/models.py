"""Typed audit records for local dataset evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "gate1.audit.v1"


@dataclass(frozen=True)
class Provenance:
    """Common provenance attached to generated audit artifacts."""

    schema_version: str
    generated_at_utc: str
    tool_name: str
    tool_version: str
    data_root_input: str
    data_root_exists: bool
    preprocessing_commit: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FileInventoryRecord:
    """One observed file under a data root."""

    schema_version: str
    relative_path: str
    file_name: str
    file_suffix: str
    file_family: str
    size_bytes: int
    modified_time_utc: str
    sha256: str
    row_count: int | None
    is_archive: bool
    provenance_data_root: str
    provenance_tool: str
    provenance_generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArchiveInventoryRecord:
    """One observed archive and its extracted-file evidence, if known."""

    schema_version: str
    archive_name: str
    relative_path: str
    size_bytes: int
    sha256: str
    extracted_file_count: int | None
    doi: str | None
    source: str | None
    date_downloaded: str | None
    provenance_data_root: str
    provenance_tool: str
    provenance_generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetManifest:
    """Gate 1 manifest assembled from observed local evidence."""

    provenance: Provenance
    archive_inventory: list[ArchiveInventoryRecord] = field(default_factory=list)
    file_inventory: list[FileInventoryRecord] = field(default_factory=list)
    file_count: int = 0
    archive_count: int = 0
    total_size_bytes: int = 0
    row_count_by_file_family: dict[str, int] = field(default_factory=dict)
    file_count_by_family: dict[str, int] = field(default_factory=dict)
    modality_file_count: dict[str, int] = field(default_factory=dict)
    expected_audit_requirements: list[str] = field(default_factory=list)
    known_anomalies: list[str] = field(default_factory=list)
    audit_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance": self.provenance.to_dict(),
            "archive_inventory": [record.to_dict() for record in self.archive_inventory],
            "file_inventory": [record.to_dict() for record in self.file_inventory],
            "file_count": self.file_count,
            "archive_count": self.archive_count,
            "total_size_bytes": self.total_size_bytes,
            "row_count_by_file_family": self.row_count_by_file_family,
            "file_count_by_family": self.file_count_by_family,
            "modality_file_count": self.modality_file_count,
            "expected_audit_requirements": self.expected_audit_requirements,
            "known_anomalies": self.known_anomalies,
            "audit_warnings": self.audit_warnings,
        }
