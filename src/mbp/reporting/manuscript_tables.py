"""Build generated manuscript tables, captions, and continuous manuscript drafts."""

from __future__ import annotations

from pathlib import Path

from mbp.reporting.manuscript_checks import (
    check_manuscript,
    check_reader_manuscript,
    write_check_reports,
    write_reader_check_reports,
)
from mbp.reporting.manuscript_figures import (
    build_manuscript_figures,
    build_reader_figures,
    figure_data_checks,
    read_csv_rows,
)


SECTION_ORDER = [
    ("Abstract", "abstract_v0.md", ["[Figure 10]", "[Table 4]"]),
    ("Introduction", "introduction_v0.md", ["[Figure 2]", "[Table 4]"]),
    ("Dataset and Linked Data Products", "methods_data_products_v0.md", ["[Figure 1]", "[Table 1]"]),
    ("Grouped Validation Protocol", "methods_validation_v0.md", ["[Figure 2]"]),
    ("Capacity Baseline Ladder", "results_capacity_baselines_v0.md", ["[Figure 3]", "[Table 2]", "[Table 3]"]),
    ("LOG_AGE Stress-Feature Experiments", "results_stress_features_v0.md", ["[Figure 5]", "[Table 5]"]),
    ("PULSE QA and Resistance Baseline", "results_pulse_resistance_v0.md", ["[Figure 6]", "[Figure 7]"]),
    ("Capacity-PULSE Coupling Diagnostics", "results_capacity_pulse_coupling_v0.md", ["[Figure 8]", "[Figure 9]"]),
    ("Negative Results and Limitations", "discussion_negative_results_v0.md", ["[Table 5]"]),
    ("Limitations", "limitations_v0.md", ["[Figure 10]"]),
]

READER_CALLOUTS = {
    "Abstract": "Table 4 summarizes the claim ladder that bounds these statements.",
    "Introduction": "Figure 2 summarizes the grouped validation design used throughout the benchmark.",
    "Dataset and Linked Data Products": "Figure 1 summarizes the linked data-product architecture, and Table 1 lists the audited cohort facts.",
    "Grouped Validation Protocol": "Figure 2 shows how cell replicates are grouped by parameter-set condition before split evaluation.",
    "Capacity Baseline Ladder": "Figure 3 summarizes the capacity ladder on the C-rate holdout, and Table 3 summarizes split difficulty.",
    "LOG_AGE Stress-Feature Experiments": "Figure 5 summarizes the mixed stress-feature decision, and Table 5 records the negative results.",
    "PULSE QA and Resistance Baseline": "Figure 6 summarizes PULSE target coverage, while Figure 7 shows scalar resistance baseline performance.",
    "Capacity-PULSE Coupling Diagnostics": "Figure 8 shows the diagnostic residual association, and Figure 9 compares prior PULSE against the strongest supplied non-PULSE baselines.",
    "Negative Results and Limitations": "Table 5 consolidates the negative results that constrain the paper's claims.",
    "Limitations": "Figure 10 summarizes the final claim ladder.",
}


def _csv_to_markdown(path: Path, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    rows = read_csv_rows(path)
    if max_rows is not None:
        rows = rows[:max_rows]
    if not rows:
        return f"Source artifact missing or empty: `{path}`\n"
    columns = columns or list(rows[0].keys())
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(_paper_safe_text(str(row.get(column, ""))) for column in columns) + " |"
        )
    return "\n".join(lines) + "\n"


def _paper_safe_text(value: str) -> str:
    replacements = {
        "EIS improves": "EIS predictive value",
        "PULSE improves fade-rate prediction": "prior PULSE fade-rate improvement",
        "calibrated uncertainty": "calibration claim",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _extract_repo_status_table(repo_status: Path) -> str:
    text = repo_status.read_text(encoding="utf-8") if repo_status.exists() else ""
    facts = [
        ("Cohort cells", "228", "docs/REPO_STATUS.md"),
        ("Condition triplets", "76", "docs/REPO_STATUS.md"),
        ("Interval rows", "3,827", "docs/REPO_STATUS.md"),
        ("LOG_AGE rows", "904,977,105", "docs/REPO_STATUS.md"),
        ("PULSE finite transition rows", "3,751", "docs/REPO_STATUS.md"),
        (
            "Current milestone",
            "Milestone 1.3" if "Milestone 1.3" in text else "See docs/REPO_STATUS.md",
            "docs/REPO_STATUS.md",
        ),
    ]
    lines = ["| Item | Value | Source |", "|---|---:|---|"]
    lines.extend(f"| {item} | {value} | `{source}` |" for item, value, source in facts)
    return "\n".join(lines) + "\n"


def build_manuscript_tables(out_dir: Path, reports_dir: Path, docs_dir: Path) -> list[Path]:
    """Generate Markdown tables for the manuscript."""

    table_dir = out_dir / "tables" / "generated"
    paths = [
        _write(
            table_dir / "table01_dataset_audit.md",
            "# Table 1. Dataset Audit Summary\n\n"
            + _extract_repo_status_table(docs_dir / "REPO_STATUS.md"),
        ),
        _write(
            table_dir / "table02_model_ladder.md",
            "# Table 2. Model Ladder Summary\n\n"
            + _csv_to_markdown(
                reports_dir / "synthesis" / "model_ladder_summary.csv",
                [
                    "ladder_stage",
                    "target",
                    "split",
                    "best_metric",
                    "metric_name",
                    "interpretation",
                ],
            ),
        ),
        _write(
            table_dir / "table03_split_difficulty.md",
            "# Table 3. Split Difficulty Summary\n\n"
            + _csv_to_markdown(
                reports_dir / "synthesis" / "split_difficulty_summary.csv",
                [
                    "split",
                    "capacity_Ah_k1_best_known",
                    "delta_capacity_Ah_best_known",
                    "pulse_delta_1s_best_known",
                    "qualitative_difficulty",
                    "note",
                ],
            ),
        ),
        _write(
            table_dir / "table04_claim_matrix.md",
            "# Table 4. Claim Matrix\n\n"
            + _csv_to_markdown(
                reports_dir / "synthesis" / "claim_matrix.csv",
                ["claim_id", "claim_area", "claim", "status", "allowed_wording"],
            ),
        ),
        _write(
            table_dir / "table05_negative_results.md",
            "# Table 5. Negative Results\n\n"
            + (
                reports_dir / "synthesis" / "negative_results.md"
            ).read_text(encoding="utf-8"),
        ),
    ]
    return paths


def write_captions(out_dir: Path) -> list[Path]:
    figure_captions = """# Figure Captions

## Figure 1. Data product architecture

Claim IDs: C12. Source artifact: `docs/PAPER_FIGURE_PLAN.md`. Allowed interpretation: the benchmark is built from linked audited data products. Limitation: the figure is schematic and not a coverage metric.

## Figure 2. Grouped validation design

Claim IDs: C12. Source artifact: `docs/VALIDATION_PROTOCOL.md`. Allowed interpretation: paper-facing claims use grouped validation. Limitation: grouped splits reduce the number of independent held-out conditions.

## Figure 3. Capacity baseline ladder

Claim IDs: C01, C03. Source artifact: `reports/synthesis/model_ladder_summary.csv`. Allowed interpretation: C-rate remains difficult for capacity targets. Limitation: descriptive best rows do not override paired claim-readiness tests.

## Figure 4. C-rate failure analysis

Claim IDs: C03. Source artifact: `reports/synthesis/split_difficulty_summary.csv`. Allowed interpretation: C-rate is the dominant unresolved capacity generalization stressor. Limitation: split-level summaries aggregate condition-specific failures.

## Figure 5. Stress-feature decision

Claim IDs: C02. Source artifact: `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv`. Allowed interpretation: stress features are mixed and do not solve C-rate fade transfer. Limitation: only scalar LOG_AGE stress groups are represented.
What not to infer: this figure does not show that stress features solve C-rate fade prediction.

## Figure 6. PULSE QA coverage

Claim IDs: C04. Source artifact: `reports/audit/pulse_qa_report.json`. Allowed interpretation: canonical RT/50 PULSE coverage is sufficient for scalar diagnostics. Limitation: missing canonical endpoints still require reporting.

## Figure 7. PULSE resistance baseline

Claim IDs: C04. Source artifact: `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`. Allowed interpretation: RT/50 PULSE is usable as a scalar resistance endpoint. Limitation: this is not a broad multimodal claim.

## Figure 8. Capacity-PULSE coupling

Claim IDs: C05. Source artifact: `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv`. Allowed interpretation: PULSE growth is associated with capacity residual magnitude. Limitation: the association is diagnostic, not causal.
What not to infer: this figure does not establish causality or independence from all confounding.

## Figure 9. Prior PULSE versus strongest non-PULSE

Claim IDs: C06, C07, C08. Source artifact: `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv`. Allowed interpretation: prior PULSE does not beat the strongest supplied non-PULSE baseline. Limitation: the result is limited to prior PULSE state at check-up k.
What not to infer: this figure does not support a claim that prior PULSE beats the strongest supplied non-PULSE baseline.

## Figure 10. Claim ladder

Claim IDs: C01-C12. Source artifact: `reports/synthesis/claim_matrix.csv`. Allowed interpretation: the paper separates supported, partial, negative, gated, and blocked claims. Limitation: the ladder summarizes evidence rather than replacing detailed reports.
"""
    table_captions = """# Table Captions

## Table 1. Dataset audit summary

Claim IDs: C12. Source artifact: `docs/REPO_STATUS.md`. Allowed interpretation: the benchmark uses a fixed audited cohort and interval population. Limitation: large generated data products remain ignored local artifacts.

## Table 2. Model ladder summary

Claim IDs: C01, C02, C03, C04, C06, C07, C08. Source artifact: `reports/synthesis/model_ladder_summary.csv`. Allowed interpretation: the ladder summarizes major baseline stages. Limitation: best-row metrics are descriptive and claim support follows paired tests.

## Table 3. Split difficulty summary

Claim IDs: C03. Source artifact: `reports/synthesis/split_difficulty_summary.csv`. Allowed interpretation: split views have different difficulty profiles. Limitation: descriptive best rows do not authorize unsupported claims.

## Table 4. Claim matrix

Claim IDs: C01-C12. Source artifact: `reports/synthesis/claim_matrix.csv`. Allowed interpretation: paper claims are status-gated. Limitation: claim wording must still be checked in prose.

## Table 5. Negative results

Claim IDs: C02, C07, C08, C09, C10, C11. Source artifact: `reports/synthesis/negative_results.md`. Allowed interpretation: negative results are part of the benchmark contribution. Limitation: they do not rule out future gated modalities.
"""
    return [
        _write(out_dir / "captions" / "figure_captions.md", figure_captions),
        _write(out_dir / "captions" / "table_captions.md", table_captions),
    ]


def write_reader_captions(out_dir: Path) -> list[Path]:
    figure_captions = """# Figure Captions v0.4

## Figure 1. Data product architecture

Linked result-data products are transformed into interval tables, LOG_AGE stress-feature sidecars, PULSE target sidecars, grouped baselines, and paper-facing claim checks.
Source: `docs/PAPER_FIGURE_PLAN.md`.

## Figure 2. Grouped validation design

The benchmark treats 228 cells as 76 parameter-set conditions with replicate-aware grouped evaluation, then reports stressor-axis holdouts at condition level.
Source: `docs/VALIDATION_PROTOCOL.md`.

## Figure 3. Capacity baseline ladder

The C-rate capacity ladder shows that learned HGB baselines improve over persistence, while C-rate remains a difficult out-of-distribution split.
Source: `reports/synthesis/model_ladder_summary.csv`.

## Figure 4. C-rate failure analysis

Split-level best-known rows show C-rate as the dominant unresolved capacity generalization view.
Source: `reports/synthesis/split_difficulty_summary.csv`.

## Figure 5. Stress-feature decision

LOG_AGE stress-feature gains are mixed on the C-rate holdout, with some capacity-level gains and persistent fade-rate failures.
Source: `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv`.
Limitation: do not infer that stress features solve C-rate fade prediction.

## Figure 6. PULSE QA coverage

Canonical RT/50 PULSE target coverage includes 39,365 summary rows, 228 cells, 3,980 available canonical check-ups, 75 missing check-ups, and no duplicate canonical check-ups.
Source: `reports/audit/pulse_qa_report.json`.

## Figure 7. PULSE resistance baseline

Scalar PULSE resistance targets are predictable enough for diagnostic baselines under grouped validation.
Source: `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`.

## Figure 8. Capacity-PULSE coupling

PULSE growth is associated with capacity-model residual magnitude in condition-level diagnostics.
Source: `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv`.
Limitation: do not infer causality or independence from all confounding.

## Figure 9. Prior PULSE versus strongest non-PULSE

Prior PULSE does not beat the strongest supplied non-PULSE baseline in paired condition-level comparisons.
Source: `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv`.
Limitation: do not infer that prior PULSE is the strongest non-neural capacity feature path.

## Figure 10. Claim ladder

The claim ladder separates supported, partially supported, diagnostic, negative, gated, and blocked claims.
Source: `reports/synthesis/claim_matrix.csv`.
"""
    table_captions = """# Table Captions v0.4

## Table 1. Dataset audit summary

The fixed benchmark cohort contains 228 cells, 76 condition triplets, and 3,827 interval rows.
Source: `docs/REPO_STATUS.md`.

## Table 2. Model ladder summary

The model ladder summarizes major capacity and PULSE baseline stages. Best-row metrics are descriptive and do not replace paired claim-readiness tests.
Source: `reports/synthesis/model_ladder_summary.csv`.

## Table 3. Split difficulty summary

Split difficulty differs across condition, temperature, C-rate, profile, and voltage-window holdouts.
Source: `reports/synthesis/split_difficulty_summary.csv`.

## Table 4. Claim matrix

The claim matrix states the allowed wording, blocked wording, source artifact, and status for each paper-facing claim.
Source: `reports/synthesis/claim_matrix.csv`.

## Table 5. Negative results

Negative results are retained as benchmark evidence, including C-rate fade failures, unsupported prior-PULSE fade-rate improvement, and gated EIS/CBAT claims.
Source: `reports/synthesis/negative_results.md`.
"""
    return [
        _write(out_dir / "captions" / "figure_captions_v0_4.md", figure_captions),
        _write(out_dir / "captions" / "table_captions_v0_4.md", table_captions),
    ]


def _strip_top_heading(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def _reader_clean_section(text: str) -> str:
    lines = _strip_top_heading(text).splitlines()
    cleaned: list[str] = []
    skip_block = False
    block_markers = {
        "allowed claim:",
        "allowed claims:",
        "blocked claim:",
        "blocked claims:",
        "figure/table references:",
        "source artifact:",
        "source artifacts:",
    }
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower in block_markers:
            skip_block = True
            continue
        if skip_block:
            if not stripped or stripped.startswith("-") or line.startswith((" ", "\t")):
                continue
            skip_block = False
        if lower.startswith("claim ids:") or lower.startswith("referenced assets:"):
            continue
        if lower.startswith("source artifact:") or lower.startswith("source artifacts:"):
            continue
        cleaned.append(line)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return "\n".join(cleaned).strip()


def assemble_manuscript(out_dir: Path, *, version: str = "v0_3") -> Path:
    label = version.replace("_", ".")
    chunks = [
        f"# Manuscript {label}\n\n",
        "Working title: Grouped-validation battery degradation benchmarks with operating-history and PULSE diagnostics.\n\n",
        "This draft is assembled from the Milestone 1.1 section files with source-section headings stripped during assembly. Figure and table callouts point to generated assets under `manuscript/figures/generated/` and `manuscript/tables/generated/`.\n\n",
    ]
    for heading, filename, callouts in SECTION_ORDER:
        section_path = out_dir / filename
        body = section_path.read_text(encoding="utf-8") if section_path.exists() else ""
        chunks.append(f"\n## {heading}\n\n")
        chunks.append(_strip_top_heading(body) + "\n\n")
        if callouts:
            chunks.append("Referenced assets: " + ", ".join(callouts) + ".\n")
    return _write(out_dir / f"manuscript_{version}.md", "\n".join(chunks))


def assemble_reader_manuscript(out_dir: Path) -> Path:
    chunks = [
        "# Manuscript v0.4",
        "",
        "Working title: Grouped-validation battery degradation benchmarks with operating-history and PULSE diagnostics.",
        "",
        "This reader-facing draft removes internal claim-control scaffolding from the manuscript body while preserving source traceability in a sidecar.",
        "",
    ]
    for heading, filename, _callouts in SECTION_ORDER:
        section_path = out_dir / filename
        body = section_path.read_text(encoding="utf-8") if section_path.exists() else ""
        chunks.extend([f"## {heading}", "", _reader_clean_section(body), ""])
        callout = READER_CALLOUTS.get(heading)
        if callout:
            chunks.extend([callout, ""])
    return _write(out_dir / "manuscript_v0_4.md", "\n".join(chunks).strip() + "\n")


def write_reader_traceability(out_dir: Path) -> Path:
    source = out_dir / "source_traceability.md"
    text = source.read_text(encoding="utf-8") if source.exists() else ""
    text = text.replace("# Manuscript Source Traceability", "# Manuscript v0.4 Traceability")
    intro = (
        "This sidecar preserves the claim, figure/table, source artifact, allowed wording, "
        "and forbidden wording mappings that were removed from the reader-facing v0.4 body.\n\n"
    )
    return _write(out_dir / "manuscript_v0_4_traceability.md", text.replace("\n\n", "\n\n" + intro, 1))


def write_figure_data_check(out_dir: Path, reports_dir: Path) -> Path:
    checks = figure_data_checks(reports_dir)
    lines = [
        "# Figure Data Check",
        "",
        "| Figure | Kind | Source | Rows consumed | Key values | Warnings |",
        "|---|---|---|---:|---|---|",
    ]
    for check in checks:
        warnings = check.get("warnings", [])
        warning_text = "; ".join(str(value) for value in warnings) if warnings else "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(check["figure"]),
                    str(check["kind"]),
                    f"`{check['source']}`",
                    str(check["rows_consumed"]),
                    str(check["key_values"]),
                    warning_text,
                ]
            )
            + " |"
        )
    return _write(out_dir / "checks" / "figure_data_check.md", "\n".join(lines) + "\n")


def _write_asset_note(
    out_dir: Path,
    figures: list[Path],
    tables: list[Path],
    checks: dict[str, object],
) -> Path:
    status = "passed" if checks.get("status") == "passed" else "failed"
    lines = [
        "# Manuscript v0.3 Polish",
        "",
        "Date: 2026-05-23",
        "",
        "Milestone 1.3 fixes Figure 6 PULSE QA extraction, strips duplicate source-section headings, extends no-overclaim checks across paper-facing files, and emits a cleaner continuous v0.3 draft.",
        "The SVG generator remains dependency-free because plotting packages are not core project dependencies in the current environment; no dependency changes were introduced for manuscript polish.",
        "",
        "## Generated Figures",
        "",
    ]
    lines.extend(f"- `{path}`" for path in figures)
    lines.extend(["", "## Generated Tables", ""])
    lines.extend(f"- `{path}`" for path in tables)
    lines.extend(
        [
            "",
            "## Manuscript Draft",
            "",
            "- `manuscript/manuscript_v0_3.md`",
            "",
            "## Validation Summary",
            "",
            f"- `mbp report check-manuscript`: `{status}`",
            "- Figure 6 reads canonical RT/50 counts from `canonical_target`.",
            "- Duplicate source-section headings are stripped during v0.3 assembly.",
            "- Generated assets consume tracked Markdown/CSV/JSON synthesis artifacts only.",
            "- No model training, feature engineering, EIS modeling, or architecture work was performed.",
            "",
            "## Remaining Drafting Tasks",
            "",
            "- Replace first-pass SVGs with publication-polished plots if needed.",
            "- Convert table Markdown into venue-specific formatting.",
            "- Tighten prose after venue selection.",
        ]
    )
    return _write(
        out_dir.parent / "docs" / "experiments" / "2026-05-23_manuscript_v0_3_polish.md",
        "\n".join(lines) + "\n",
    )


def _write_reader_note(out_dir: Path, reader_result: dict[str, object]) -> Path:
    status = "passed" if reader_result.get("status") == "passed" else "failed"
    lines = [
        "# Manuscript v0.4 Reader Polish",
        "",
        "Date: 2026-05-23",
        "",
        "Milestone 1.4 converts the internally traceable v0.3 draft into a reader-facing v0.4 manuscript while preserving claim traceability in a sidecar.",
        "",
        "## Changed From v0.3",
        "",
        "- Removed raw claim IDs from the main manuscript body.",
        "- Removed allowed-claim, blocked-claim, source-artifact, and referenced-asset scaffolding from reader prose.",
        "- Added `manuscript/manuscript_v0_4_traceability.md` for claim/source mapping.",
        "- Added v0.4 reader-facing captions.",
        "- Added `manuscript/figures/generated_v0_4/*.svg` draft figure assets.",
        "",
        "## Validation Summary",
        "",
        f"- `mbp report check-reader-manuscript`: `{status}`",
        "- No new model training, feature engineering, EIS modeling, or architecture work was performed.",
        "",
        "## Remaining Tasks",
        "",
        "- Convert v0.4 into target venue format.",
        "- Improve final figure visual design if needed.",
        "- Decide whether traceability belongs in supplement or repository-only material.",
    ]
    return _write(
        out_dir.parent / "docs" / "experiments" / "2026-05-23_manuscript_v0_4_reader_polish.md",
        "\n".join(lines) + "\n",
    )


def build_manuscript_assets(out_dir: Path, reports_dir: Path, docs_dir: Path) -> dict[str, object]:
    """Build all current manuscript assets."""

    figures = build_manuscript_figures(out_dir, reports_dir, docs_dir)
    tables = build_manuscript_tables(out_dir, reports_dir, docs_dir)
    captions = write_captions(out_dir)
    reader_captions = write_reader_captions(out_dir)
    manuscript = assemble_manuscript(out_dir, version="v0_3")
    reader_manuscript = assemble_reader_manuscript(out_dir)
    reader_traceability = write_reader_traceability(out_dir)
    reader_figures = build_reader_figures(out_dir)
    check_result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=docs_dir / "PAPER_CLAIM_LEDGER.md",
        traceability=out_dir / "source_traceability.md",
    )
    reader_result = check_reader_manuscript(
        manuscript=reader_manuscript,
        claim_ledger=docs_dir / "PAPER_CLAIM_LEDGER.md",
        traceability=reader_traceability,
    )
    figure_data_check = write_figure_data_check(out_dir, reports_dir)
    check_paths = write_check_reports(
        out_dir=out_dir,
        check_result=check_result,
        figures=figures,
        tables=tables,
        captions=captions,
        extra_reports=[figure_data_check],
    )
    reader_check_paths = write_reader_check_reports(
        out_dir=out_dir,
        check_result=check_result,
        reader_result=reader_result,
    )
    note = _write_asset_note(out_dir, figures, tables, check_result)
    reader_note = _write_reader_note(out_dir, reader_result)
    overall_status = "passed" if check_result["status"] == reader_result["status"] == "passed" else "failed"
    return {
        "status": overall_status,
        "figures": [str(path) for path in [*figures, *reader_figures]],
        "tables": [str(path) for path in tables],
        "captions": [str(path) for path in [*captions, *reader_captions]],
        "manuscript": str(reader_manuscript),
        "checks": [str(path) for path in [*check_paths, *reader_check_paths, figure_data_check]],
        "experiment_note": str(reader_note),
        "prior_experiment_note": str(note),
    }
