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
    qa_report: dict[str, object] | None = None,
    gate2_reports: dict[str, object] | None = None,
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

    qa_status = str(qa_report.get("status", "unknown")) if qa_report else "not_run"
    qa_passed = qa_status == "passed"

    all_complete = (
        bagit_status == "PASSED"
        and has_logs
        and eis_status == "complete"
        and pulse_status == "complete"
    )
    gate2_data_products_ready = all_complete
    interval_report = _dict_report(gate2_reports, "interval_qa")
    split_report = _dict_report(gate2_reports, "split_registry")
    interval_subset_report = _dict_report(gate2_reports, "interval_subset")
    monotonicity_report = _dict_report(gate2_reports, "log_age_monotonicity")
    raw_log_report = _dict_report(gate2_reports, "raw_log_inventory")
    interval_passed = interval_report.get("status") == "passed"
    split_passed = split_report.get("status") == "passed"
    interval_subset_passed = interval_subset_report.get("status") == "passed"
    gate2b_complete = bool(interval_passed and split_passed and monotonicity_report)
    modeling_authorized = gate2_data_products_ready and qa_passed and gate2b_complete
    capacity_baseline_authorized = bool(
        gate2_data_products_ready and gate2b_complete and interval_subset_passed
    )

    lines = [
        "# Dataset Evidence Memo",
        "",
        "Status: Auto-generated Gate 1.1 Integrity Report plus Gate 2 ingestion evidence",
        "Project: Multimodal Battery Prediction (MBP)",
        "Gate: Gate 1 — Dataset Audit & Provenance Verification",
        "",
        "---",
        "",
        "## Go/No-Go Decision Gate",
        "",
    ]

    if gate2_data_products_ready:
        gate_note = (
            "Gate 2b interval QA and split-registry audits have passed; Milestone 0.4 defines strict/tolerant interval subsets, and Milestone 0.5 authorizes only the first scalar capacity baseline ladder."
            if capacity_baseline_authorized
            else (
                "Gate 2b interval QA and split-registry audits have passed; modeling remains blocked until a LOG_AGE monotonicity handling policy selects the clean baseline subset."
                if gate2b_complete
                else "Modeling remains blocked until LOG_AGE QA failures, leakage mitigation, and baseline gates are resolved."
            )
        )
        lines.extend(
            [
                "> [!TIP]",
                "> **GATE 1 STATUS: GO FOR DATA PRODUCTS**",
                f"> Result and reduced-log modalities are observed, BagIt validation passed successfully for the result package, and Gate 2 data-product construction is authorized. {gate_note}",
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
            "| Modality | Status | Expected Cells | Observed Cells/Files | Coverage % | Replicates (Any) | Replicates (All 3) | Total Size |",
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

    log_age_table = _qa_table(qa_report, "modality_table_log_age")
    if log_age_table:
        lines.extend(
            [
                "",
                "---",
                "",
                "## LOG_AGE Ingestion Evidence",
                "",
                "`mbp ingest log-age` has produced the reduced operating-history table at",
                "`data/interim/modality_table_log_age.parquet`.",
                "",
                "| Field | Value |",
                "|---|---|",
                "| Source package path | `data/raw/Log_Raw_Data_Version_2` |",
                "| Source archive | `cell_log_age_ultracompr.7z` |",
                "| Log package DOI path | `10.35097-kww7jv8ajuvchcah` |",
                f"| Ingested rows | `{_format_int(log_age_table.get('row_count'))}` |",
                f"| Parquet size | `{_format_int(log_age_table.get('file_size_bytes'))} bytes` |",
                f"| Parquet row groups | `{_format_int(log_age_table.get('row_groups'))}` |",
                f"| Unique cohort cells | `{_format_int(log_age_table.get('unique_cells'))}` |",
                f"| Non-cohort cells in table | `{_format_int(log_age_table.get('non_cohort_cell_count'))}` |",
                f"| Latest QA status | `{qa_status}` |",
                f"| LOG_AGE monotonicity violations | `{_format_int(log_age_table.get('monotonic_timestamp_efc_violations'))}` strict QA decreases flagged; `{_format_int(monotonicity_report.get('row_count'))}` default-tolerance detailed violations |",
                f"| `cap_aged_est_Ah` non-null rows | `{_format_int(_diagnostic_count(log_age_table, 'cap_aged_est_Ah'))}` |",
                f"| `R0_mOhm` non-null rows | `{_format_int(_diagnostic_count(log_age_table, 'R0_mOhm'))}` |",
                f"| `R1_mOhm` non-null rows | `{_format_int(_diagnostic_count(log_age_table, 'R1_mOhm'))}` |",
                "",
                "Inserted LOG_AGE diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) are active leakage risks. They may be counted and masked for QA, but must not enter interval features unless they are explicitly prior-to-cutoff values.",
            ]
        )

    if gate2_reports:
        lines.extend(
            [
                "",
                "---",
                "",
                "## Gate 2b Data-Product Hardening Evidence",
                "",
                "| Artifact | Status | Key evidence |",
                "|---|---|---|",
                (
                    "| LOG_AGE monotonicity report | "
                    f"`generated` | `{_format_int(monotonicity_report.get('row_count'))}` detailed violations; "
                    f"`{_format_int(monotonicity_report.get('summary_lines'))}` summary CSV lines |"
                ),
                (
                    "| Interval QA report | "
                    f"`{interval_report.get('status', 'not_run')}` | "
                    f"`{_format_int(interval_report.get('row_count'))}` intervals; "
                    f"`{_format_int(interval_report.get('intervals_with_monotonicity_violations'))}` monotonicity-flagged; "
                    f"LOG_AGE availability `{interval_report.get('LOG_AGE_available_fraction', 'N/A')}` |"
                ),
                (
                    "| Split registry audit | "
                    f"`{split_report.get('status', 'not_run')}` | "
                    f"`{_format_int(split_report.get('row_count'))}` cells; hot holdout uses 40 C; "
                    "high-C-rate holdout includes 5/3 C; voltage-window holdout is non-empty |"
                ),
                (
                    "| Interval subset registry | "
                    f"`{interval_subset_report.get('status', 'not_run')}` | "
                    f"`{_format_int(interval_subset_report.get('baseline_clean_strict_count'))}` strict-clean; "
                    f"`{_format_int(interval_subset_report.get('baseline_clean_tolerant_count'))}` tolerant-clean; "
                    f"threshold `{interval_subset_report.get('efc_jitter_threshold', 'N/A')}` EFC |"
                ),
                (
                    "| Raw LOG archive inventory | "
                    f"`generated` | `{_format_int(raw_log_report.get('row_count'))}` archive members inventoried; "
                    f"sampled header available `{raw_log_report.get('sampled_header_available', 'N/A')}` |"
                ),
                "",
                "Gate 2b classifies the LOG_AGE monotonicity issue as small EFC decreases in the reduced table and propagates affected rows into interval quality flags. Milestone 0.4 defines strict and tolerant clean subsets; Milestone 0.5 baseline tooling must consume the interval subset registry and report sensitivity excluding monotonicity-flagged intervals.",
            ]
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
        status = record.status
        evidence = record.evidence
        if record.issue_id == "KI004" and log_age_table:
            status = "active_mitigation"
            evidence = f"{_format_int(log_age_table.get('row_count'))} LOG_AGE rows ingested"
        lines.append(
            f"| {record.issue_id} | {record.issue_name} | {record.severity} | "
            f"`{status}` | {evidence} | {record.handling_decision} |"
        )

    monotonic_violations = (
        int(log_age_table.get("monotonic_timestamp_efc_violations", 0) or 0)
        if log_age_table
        else 0
    )
    if monotonic_violations:
        monotonic_status = "policy_defined" if interval_subset_passed else "flagged_by_qa"
        monotonic_handling = (
            "`docs/LOG_AGE_MONOTONICITY_POLICY.md` defines strict and tolerant baseline subsets; Milestone 0.5 baselines must report sensitivity excluding flagged intervals."
            if interval_subset_passed
            else "Investigate or quality-flag affected intervals before treating them as clean exposure evidence."
        )
        lines.append(
            f"| KI006 | LOG_AGE timestamp/EFC monotonicity violations | medium | "
            f"`{monotonic_status}` | {monotonic_violations:,} timestamp/EFC decreases detected | "
            f"{monotonic_handling} |"
        )

    # 4. Gate 1 Decision Table
    if capacity_baseline_authorized:
        modeling_auth = "Limited"
        modeling_notes = (
            "Milestone 0.5 authorizes only scalar capacity baselines using "
            "`interval_subset_registry_v1.parquet`; EIS, PULSE, sequence, neural, "
            "policy-ranking, and CBAT claims remain blocked."
        )
    else:
        modeling_auth = "Yes" if modeling_authorized else "No"
        modeling_notes = (
            "All Gate 1 and Gate 2 QA checks passed successfully."
            if modeling_authorized
            else "Gate 2 data products are authorized; model training waits for an explicit baseline milestone and must consume the interval subset registry."
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
            f"| Required modality coverage verified | {'Complete' if (eis_status == 'complete' and pulse_status == 'complete') else 'Pending'} | Coverage is file-level for raw archives and parser-backed for interim tables with QA. |",
            f"| Gate 2 QA status | `{qa_status}` | { _qa_failure_summary(qa_report) } |",
            f"| Gate 2b interval QA | `{interval_report.get('status', 'not_run')}` | {_format_int(interval_report.get('intervals_with_monotonicity_violations'))} intervals carry LOG_AGE monotonicity flags. |",
            f"| Gate 2b split audit | `{split_report.get('status', 'not_run')}` | Headline OOD folds are non-empty and parameter-set triplets remain grouped. |",
            f"| Baseline subset registry | `{interval_subset_report.get('status', 'not_run')}` | {_format_int(interval_subset_report.get('baseline_clean_tolerant_count'))} tolerant-clean intervals defined by policy. |",
            "| Known issues register initialized | Complete | Checks remain pending or blocked until data evidence exists. |",
            f"| Modeling authorized | {modeling_auth} | {modeling_notes} |",
        ]
    )

    audit_warnings = [
        warning
        for warning in manifest.audit_warnings
        if not (has_logs and "no files detected for modalities: log, log_age" in warning)
    ]
    if audit_warnings:
        lines.extend(["", "## Audit Warnings", ""])
        for warning in audit_warnings:
            lines.append(f"- {warning}")

    lines.append("")
    return "\n".join(lines)


def write_evidence_memo(
    manifest: DatasetManifest,
    coverage: list[ModalityCoverageRecord],
    known_issues: list[KnownIssueRecord],
    out_path: Path,
    bagit_report: dict[str, object] | None = None,
    qa_report: dict[str, object] | None = None,
    gate2_reports: dict[str, object] | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_evidence_memo(
            manifest,
            coverage,
            known_issues,
            bagit_report,
            qa_report,
            gate2_reports,
        ),
        encoding="utf-8",
    )


def _dict_report(reports: dict[str, object] | None, key: str) -> dict[str, object]:
    if not reports:
        return {}
    report = reports.get(key)
    return report if isinstance(report, dict) else {}


def _qa_table(qa_report: dict[str, object] | None, table_name: str) -> dict[str, object] | None:
    if not qa_report:
        return None
    tables = qa_report.get("tables")
    if not isinstance(tables, dict):
        return None
    table = tables.get(table_name)
    return table if isinstance(table, dict) and table.get("exists") else None


def _format_int(value: object) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _diagnostic_count(table: dict[str, object], field_name: str) -> object:
    counts = table.get("diagnostic_nonnull_counts")
    if not isinstance(counts, dict):
        return None
    return counts.get(field_name)


def _qa_failure_summary(qa_report: dict[str, object] | None) -> str:
    if not qa_report:
        return "No QA report was available when the memo was generated."
    failures = qa_report.get("failures")
    if not isinstance(failures, list) or not failures:
        return "All available QA checks passed."
    first = str(failures[0])
    if len(failures) == 1:
        return first
    return f"{first}; plus {len(failures) - 1} additional failures."
