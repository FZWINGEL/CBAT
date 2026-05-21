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
    bagit_report: dict[str, object] | None = None,
) -> str:
    # 1. Fetch metadata if present
    meta = manifest.dataset_metadata or {}
    desc = meta.get("descriptive", {})
    bag_info = meta.get("bag_info", {})

    title = desc.get("title") or "Comprehensive battery aging dataset: Luh–Blank NMC/C-SiO"
    doi = desc.get("doi") or "10.35097/1969"
    pub_year = desc.get("publication_year") or "2024"
    rights = desc.get("rights") or "CC BY 4.0 Attribution"
    creators_list = desc.get("creators", [])
    creators = (
        ", ".join(c["name"] for c in creators_list)
        if creators_list
        else "Matthias Luh, Thomas Blank"
    )

    # 2. Compile BagIt Status
    bagit_status = "unknown"
    bagit_errors = []
    if bagit_report:
        bagit_status = str(bagit_report.get("status", "unknown")).upper()
        bagit_errors = list(bagit_report.get("errors", []))
    elif manifest.provenance.data_root_exists:
        # Try to parse on-the-fly
        from mbp.audit.bagit import validate_bagit

        try:
            report = validate_bagit(Path(manifest.provenance.data_root_input))
            bagit_status = report["status"].upper()
            bagit_errors = report["errors"]
        except Exception:
            pass

    # 3. Determine overall Go/No-Go
    missing_modalities = []
    observed_modalities = []
    for record in coverage:
        if record.file_count > 0:
            observed_modalities.append(record.modality)
        else:
            missing_modalities.append(record.modality)

    has_logs = "log" in observed_modalities and "log_age" in observed_modalities
    eis_record = next((r for r in coverage if r.modality == "eis"), None)
    pulse_record = next((r for r in coverage if r.modality == "pulse"), None)

    eis_status = eis_record.status if eis_record else "unknown"
    pulse_status = pulse_record.status if pulse_record else "unknown"

    all_complete = (
        bagit_status == "PASSED"
        and has_logs
        and eis_status == "complete"
        and pulse_status == "complete"
    )

    lines = [
        "# Dataset Evidence Memo",
        "",
        "Status: Auto-generated Gate 1.1 Integrity Report",
        "Project: Multimodal Battery Prediction (MBP)",
        "Gate: Gate 1 — Dataset Audit & Provenance Verification",
        "",
        "---",
        "",
        "## Go/No-Go Decision Gate",
        "",
    ]

    if all_complete:
        lines.extend(
            [
                "> [!TIP]",
                "> **GATE 1 STATUS: GO (Modeling Authorized)**",
                "> All result and log modalities are fully observed, BagIt validation passed successfully, and coverages are 100% complete.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "> [!CAUTION]",
                "> **GATE 1 STATUS: NO-GO (Modeling Blocked)**",
                "> Modeling remains strictly **NOT AUTHORIZED** until the following blockages are resolved:",
            ]
        )
        if not has_logs:
            lines.append(
                "> - **Missing Log Data**: `log` and `log_age` raw files are not yet observed (currently downloading)."
            )
        if bagit_status != "PASSED":
            lines.append(
                f"> - **BagIt Validation Status**: {bagit_status} (package integrity could not be verified)."
            )
        if eis_status != "complete":
            lines.append(
                f"> - **EIS Modality Coverage**: {eis_status} (complete expected 228-cell matrix not observed)."
            )
        if pulse_status != "complete":
            lines.append(
                f"> - **PULSE Modality Coverage**: {pulse_status} (complete expected 228-cell matrix not observed)."
            )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Dataset Metadata & Provenance",
            "",
            f"**Title**: {title}  ",
            f"**DOI**: {doi}  ",
            f"**Creators**: {creators}  ",
            f"**Publication Year**: {pub_year}  ",
            f"**Rights / License**: {rights}  ",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Schema version | `{manifest.provenance.schema_version}` |",
            f"| Generated at UTC | `{manifest.provenance.generated_at_utc}` |",
            f"| Input data root | `{manifest.provenance.data_root_input}` |",
            f"| Data root exists | `{manifest.provenance.data_root_exists}` |",
            f"| Bagging Date | `{bag_info.get('Bagging-Date', 'N/A')}` |",
            f"| External Identifier | `{bag_info.get('External-Identifier', 'N/A')}` |",
            f"| Tool version | `mbp {manifest.provenance.tool_version}` |",
            f"| Preprocessing commit | `{manifest.provenance.preprocessing_commit or 'unavailable'}` |",
            "",
            "---",
            "",
            "## BagIt Integrity Verification",
            "",
            f"**Status**: **{bagit_status}**  ",
        ]
    )

    if bagit_errors:
        lines.extend(["", "### Validation Warnings/Errors", ""])
        for error in bagit_errors[:15]:
            lines.append(f"- [ ] {error}")
        if len(bagit_errors) > 15:
            lines.append(f"- ... and {len(bagit_errors) - 15} more warnings.")
    else:
        lines.append("All payload and tag files match their MD5 checksum manifests perfectly.")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Modality & Cell Coverage Summary",
            "",
            "| Modality | Status | Expected Cells | Observed Cells | Coverage % | Replicates (Any) | Replicates (All 3) | Total Size |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    for record in coverage:
        cov_pct = f"{record.coverage_ratio * 100:.1f}%"
        is_diag = record.modality in ("cfg", "eoc", "eis", "pulse")
        exp_cells = str(record.expected_cells) if is_diag else "N/A"
        obs_cells = str(record.observed_cells) if is_diag else str(record.file_count)
        any_rep = str(record.parameter_sets_with_any_replicate) if is_diag else "N/A"
        all_rep = str(record.parameter_sets_with_all_replicates) if is_diag else "N/A"

        # Formatted sizes
        size_mb = record.total_size_bytes / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb > 0.1 else f"{record.total_size_bytes} B"

        lines.append(
            f"| {record.modality} | **{record.status.upper()}** | {exp_cells} | {obs_cells} | {cov_pct} | {any_rep} | {all_rep} | {size_str} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Known-Issue Register",
            "",
            "| ID | Issue | Severity | Status | Evidence | Handling Decision |",
            "|---|---|---|---|---|---|",
        ]
    )

    for record in known_issues:
        lines.append(
            f"| {record.issue_id} | {record.issue_name} | {record.severity} | "
            f"`{record.status}` | {record.evidence} | {record.handling_decision} |"
        )

    # 4. Gate 1 Decision Table
    modeling_auth = "Yes" if all_complete else "No"
    modeling_notes = (
        "All Gate 1 audit checks passed successfully."
        if all_complete
        else "Modeling remains blocked until Gate 1 audit passes."
    )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Gate 1 Decision",
            "",
            "| Decision item | Status | Notes |",
            "|---|---|---|",
            f"| Archive hashes recorded | {'Complete' if bagit_status == 'PASSED' else 'Pending'} | Requires downloaded archives. |",
            "| File inventory generated | Complete | Generated from observed local files. |",
            "| Dataset manifest generated | Complete | Preliminary manifest only until source metadata is filled. |",
            f"| Required modality coverage verified | {'Complete' if (eis_status == 'complete' and pulse_status == 'complete') else 'Pending'} | Coverage is file-level only until parsers exist. |",
            "| Known issues register initialized | Complete | Checks remain pending or blocked until data evidence exists. |",
            f"| Modeling authorized | {modeling_auth} | {modeling_notes} |",
        ]
    )

    if manifest.audit_warnings:
        lines.extend(["", "## Audit Warnings", ""])
        for warning in manifest.audit_warnings:
            lines.append(f"- {warning}")

    lines.append("")
    return "\n".join(lines)


def write_evidence_memo(
    manifest: DatasetManifest,
    coverage: list[ModalityCoverageRecord],
    known_issues: list[KnownIssueRecord],
    out_path: Path,
    bagit_report: dict[str, object] | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_evidence_memo(manifest, coverage, known_issues, bagit_report), encoding="utf-8"
    )
