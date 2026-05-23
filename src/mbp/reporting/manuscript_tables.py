"""Build generated manuscript tables, captions, and a continuous v0.2 draft."""

from __future__ import annotations

from pathlib import Path

from mbp.reporting.manuscript_checks import check_manuscript, write_check_reports
from mbp.reporting.manuscript_figures import build_manuscript_figures, read_csv_rows


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
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines) + "\n"


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
        ("Current milestone", "Milestone 1.2" if "Milestone 1.2" in text else "See docs/REPO_STATUS.md", "docs/REPO_STATUS.md"),
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

## Figure 6. PULSE QA coverage

Claim IDs: C04. Source artifact: `reports/audit/pulse_qa_report.json`. Allowed interpretation: canonical RT/50 PULSE coverage is sufficient for scalar diagnostics. Limitation: missing canonical endpoints still require reporting.

## Figure 7. PULSE resistance baseline

Claim IDs: C04. Source artifact: `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`. Allowed interpretation: RT/50 PULSE is usable as a scalar resistance endpoint. Limitation: this is not a broad multimodal claim.

## Figure 8. Capacity-PULSE coupling

Claim IDs: C05. Source artifact: `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv`. Allowed interpretation: PULSE growth is associated with capacity residual magnitude. Limitation: the association is diagnostic, not causal.

## Figure 9. Prior PULSE versus strongest non-PULSE

Claim IDs: C06, C07, C08. Source artifact: `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv`. Allowed interpretation: prior PULSE does not beat the strongest supplied non-PULSE baseline. Limitation: the result is limited to prior PULSE state at check-up k.

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


def assemble_manuscript(out_dir: Path) -> Path:
    chunks = [
        "# Manuscript v0.2\n\n",
        "Working title: Grouped-validation battery degradation benchmarks with operating-history and PULSE diagnostics.\n\n",
        "This draft is assembled from the Milestone 1.1 section files. Figure and table callouts point to generated assets under `manuscript/figures/generated/` and `manuscript/tables/generated/`.\n\n",
    ]
    for heading, filename, callouts in SECTION_ORDER:
        section_path = out_dir / filename
        body = section_path.read_text(encoding="utf-8") if section_path.exists() else ""
        chunks.append(f"\n## {heading}\n\n")
        chunks.append(body.strip() + "\n\n")
        if callouts:
            chunks.append("Referenced assets: " + ", ".join(callouts) + ".\n")
    return _write(out_dir / "manuscript_v0_2.md", "\n".join(chunks))


def _write_asset_note(
    out_dir: Path,
    figures: list[Path],
    tables: list[Path],
    checks: dict[str, object],
) -> Path:
    status = "passed" if checks.get("status") == "passed" else "failed"
    lines = [
        "# Manuscript v0.2 Assets",
        "",
        "Date: 2026-05-23",
        "",
        "Milestone 1.2 generated a continuous manuscript draft plus source-linked SVG and Markdown assets from existing tracked reports only.",
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
            "- `manuscript/manuscript_v0_2.md`",
            "",
            "## Validation Summary",
            "",
            f"- `mbp report check-manuscript`: `{status}`",
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
    return _write(out_dir.parent / "docs" / "experiments" / "2026-05-23_manuscript_v0_2_assets.md", "\n".join(lines) + "\n")


def build_manuscript_assets(out_dir: Path, reports_dir: Path, docs_dir: Path) -> dict[str, object]:
    """Build all Milestone 1.2 manuscript assets."""

    figures = build_manuscript_figures(out_dir, reports_dir, docs_dir)
    tables = build_manuscript_tables(out_dir, reports_dir, docs_dir)
    captions = write_captions(out_dir)
    manuscript = assemble_manuscript(out_dir)
    check_result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=docs_dir / "PAPER_CLAIM_LEDGER.md",
        traceability=out_dir / "source_traceability.md",
    )
    check_paths = write_check_reports(
        out_dir=out_dir,
        check_result=check_result,
        figures=figures,
        tables=tables,
        captions=captions,
    )
    note = _write_asset_note(out_dir, figures, tables, check_result)
    return {
        "status": check_result["status"],
        "figures": [str(path) for path in figures],
        "tables": [str(path) for path in tables],
        "captions": [str(path) for path in captions],
        "manuscript": str(manuscript),
        "checks": [str(path) for path in check_paths],
        "experiment_note": str(note),
    }
