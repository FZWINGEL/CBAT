"""Markdown report generation for Gate 1 evidence."""

from __future__ import annotations

from pathlib import Path

from mbp.audit.coverage import ModalityCoverageRecord
from mbp.audit.known_issues import KnownIssueRecord
from mbp.audit.models import DatasetManifest


def render_evidence_memo(
    manifest: DatasetManifest,
    coverage: list[ModalityCoverageRecord],
    known_issues: list[KnownIssueRecord],
) -> str:
    lines = [
        "# Dataset Evidence Memo",
        "",
        "Status: Auto-generated preliminary Gate 1 memo",
        "Project: Multimodal Battery Prediction",
        "Gate: Gate 1 - dataset audit and provenance verification",
        "",
        "## Provenance",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Schema version | {manifest.provenance.schema_version} |",
        f"| Generated at UTC | {manifest.provenance.generated_at_utc} |",
        f"| Data root | `{manifest.provenance.data_root_input}` |",
        f"| Data root exists | {manifest.provenance.data_root_exists} |",
        f"| Tool | {manifest.provenance.tool_name} {manifest.provenance.tool_version} |",
        f"| Preprocessing commit | {manifest.provenance.preprocessing_commit or 'unavailable'} |",
        "",
        "## Inventory Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Files | {manifest.file_count} |",
        f"| Archives | {manifest.archive_count} |",
        f"| Total size bytes | {manifest.total_size_bytes} |",
        "",
        "## Modality Coverage",
        "",
        "| Modality | Status | Files | Rows | Evidence paths |",
        "|---|---|---:|---:|---|",
    ]
    for record in coverage:
        rows = "" if record.row_count is None else str(record.row_count)
        lines.append(
            f"| {record.modality} | {record.status} | {record.file_count} | {rows} | "
            f"{record.evidence_paths or 'TODO'} |"
        )

    lines.extend(
        [
            "",
            "## Known-Issue Checks",
            "",
            "| ID | Issue | Severity | Status | Evidence | Handling decision |",
            "|---|---|---|---|---|---|",
        ]
    )
    for record in known_issues:
        lines.append(
            f"| {record.issue_id} | {record.issue_name} | {record.severity} | "
            f"{record.status} | {record.evidence} | {record.handling_decision} |"
        )

    lines.extend(
        [
            "",
            "## Gate 1 Decision",
            "",
            "| Decision item | Status | Notes |",
            "|---|---|---|",
            "| Archive hashes recorded | Pending | Requires downloaded archives. |",
            "| File inventory generated | Complete | Generated from observed local files. |",
            "| Dataset manifest generated | Complete | Preliminary manifest only until source metadata is filled. |",
            "| Required modality coverage verified | Pending | Coverage is file-level only until parsers exist. |",
            "| Known issues register initialized | Complete | Checks remain pending or blocked until data evidence exists. |",
            "| Modeling authorized | No | Modeling remains blocked until Gate 1 audit passes. |",
            "",
        ]
    )
    if manifest.audit_warnings:
        lines.extend(["## Audit Warnings", ""])
        for warning in manifest.audit_warnings:
            lines.append(f"- {warning}")
        lines.append("")
    return "\n".join(lines)


def write_evidence_memo(
    manifest: DatasetManifest,
    coverage: list[ModalityCoverageRecord],
    known_issues: list[KnownIssueRecord],
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_evidence_memo(manifest, coverage, known_issues), encoding="utf-8")
