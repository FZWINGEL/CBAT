"""Tests verifying schema contracts and metadata fields for Gate 1 data products."""

from __future__ import annotations

from mbp.audit.coverage import ModalityCoverageRecord
from mbp.audit.known_issues import KnownIssueRecord
from mbp.audit.models import (
    SCHEMA_VERSION,
    ArchiveInventoryRecord,
    DatasetManifest,
    FileInventoryRecord,
    Provenance,
)


def test_provenance_schema_fields() -> None:
    """Assert Provenance has all expected fields and serialization works."""
    prov = Provenance(
        schema_version=SCHEMA_VERSION,
        generated_at_utc="2026-05-21T00:00:00Z",
        tool_name="mbp audit manifest",
        tool_version="0.1.0",
        data_root_input="data/raw",
        data_root_exists=True,
        preprocessing_commit="abcdef",
    )
    d = prov.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["generated_at_utc"] == "2026-05-21T00:00:00Z"
    assert d["tool_name"] == "mbp audit manifest"
    assert d["tool_version"] == "0.1.0"
    assert d["data_root_input"] == "data/raw"
    assert d["data_root_exists"] is True
    assert d["preprocessing_commit"] == "abcdef"


def test_file_inventory_record_schema_fields() -> None:
    """Assert FileInventoryRecord contains all mandatory schema fields."""
    record = FileInventoryRecord(
        schema_version=SCHEMA_VERSION,
        relative_path="raw/EOC.csv",
        file_name="EOC.csv",
        file_suffix=".csv",
        file_family="eoc",
        size_bytes=1024,
        modified_time_utc="2026-05-21T00:00:00Z",
        sha256="a" * 64,
        row_count=100,
        is_archive=False,
        provenance_data_root="data/raw",
        provenance_tool="mbp audit inventory",
        provenance_generated_at_utc="2026-05-21T00:00:00Z",
    )
    d = record.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["relative_path"] == "raw/EOC.csv"
    assert d["file_name"] == "EOC.csv"
    assert d["file_suffix"] == ".csv"
    assert d["file_family"] == "eoc"
    assert d["size_bytes"] == 1024
    assert d["modified_time_utc"] == "2026-05-21T00:00:00Z"
    assert d["sha256"] == "a" * 64
    assert d["row_count"] == 100
    assert d["is_archive"] is False
    assert d["provenance_data_root"] == "data/raw"
    assert d["provenance_tool"] == "mbp audit inventory"
    assert d["provenance_generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_archive_inventory_record_schema_fields() -> None:
    """Assert ArchiveInventoryRecord contains all mandatory schema fields."""
    record = ArchiveInventoryRecord(
        schema_version=SCHEMA_VERSION,
        archive_name="data.zip",
        relative_path="data.zip",
        size_bytes=2048,
        sha256="b" * 64,
        extracted_file_count=10,
        doi="10.1000/xyz123",
        source="http://example.com/data.zip",
        date_downloaded="2026-05-21",
        provenance_data_root="data/raw",
        provenance_tool="mbp audit manifest",
        provenance_generated_at_utc="2026-05-21T00:00:00Z",
    )
    d = record.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["archive_name"] == "data.zip"
    assert d["relative_path"] == "data.zip"
    assert d["size_bytes"] == 2048
    assert d["sha256"] == "b" * 64
    assert d["extracted_file_count"] == 10
    assert d["doi"] == "10.1000/xyz123"
    assert d["source"] == "http://example.com/data.zip"
    assert d["date_downloaded"] == "2026-05-21"
    assert d["provenance_data_root"] == "data/raw"
    assert d["provenance_tool"] == "mbp audit manifest"
    assert d["provenance_generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_modality_coverage_record_schema_fields() -> None:
    """Assert ModalityCoverageRecord contains expected schema fields."""
    record = ModalityCoverageRecord(
        schema_version=SCHEMA_VERSION,
        modality="eis",
        file_count=5,
        row_count=5000,
        total_size_bytes=204800,
        status="observed",
        evidence_paths="file1.csv;file2.csv",
        provenance_tool="mbp audit manifest",
        provenance_generated_at_utc="2026-05-21T00:00:00Z",
    )
    d = record.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["modality"] == "eis"
    assert d["file_count"] == 5
    assert d["row_count"] == 5000
    assert d["total_size_bytes"] == 204800
    assert d["status"] == "observed"
    assert d["evidence_paths"] == "file1.csv;file2.csv"
    assert d["provenance_tool"] == "mbp audit manifest"
    assert d["provenance_generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_known_issue_record_schema_fields() -> None:
    """Assert KnownIssueRecord contains expected schema fields."""
    record = KnownIssueRecord(
        schema_version=SCHEMA_VERSION,
        issue_id="KI001",
        issue_name="EIS validation",
        severity="high",
        status="pending_audit",
        evidence="EIS files observed",
        handling_decision="Do not use EIS yet.",
        provenance_tool="mbp audit manifest",
        provenance_generated_at_utc="2026-05-21T00:00:00Z",
    )
    d = record.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["issue_id"] == "KI001"
    assert d["issue_name"] == "EIS validation"
    assert d["severity"] == "high"
    assert d["status"] == "pending_audit"
    assert d["evidence"] == "EIS files observed"
    assert d["handling_decision"] == "Do not use EIS yet."
    assert d["provenance_tool"] == "mbp audit manifest"
    assert d["provenance_generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_dataset_manifest_schema_fields() -> None:
    """Assert DatasetManifest fields serialize and contain necessary records."""
    prov = Provenance(
        schema_version=SCHEMA_VERSION,
        generated_at_utc="2026-05-21T00:00:00Z",
        tool_name="mbp audit manifest",
        tool_version="0.1.0",
        data_root_input="data/raw",
        data_root_exists=True,
        preprocessing_commit="abcdef",
    )
    manifest = DatasetManifest(
        provenance=prov,
        file_count=0,
        archive_count=0,
        total_size_bytes=0,
        row_count_by_file_family={},
        file_count_by_family={},
        modality_file_count={},
        expected_audit_requirements=[],
        known_anomalies=[],
        audit_warnings=[],
    )
    d = manifest.to_dict()
    assert d["provenance"]["schema_version"] == SCHEMA_VERSION
    assert d["file_count"] == 0
    assert d["archive_count"] == 0
    assert d["total_size_bytes"] == 0
    assert isinstance(d["archive_inventory"], list)
    assert isinstance(d["file_inventory"], list)
