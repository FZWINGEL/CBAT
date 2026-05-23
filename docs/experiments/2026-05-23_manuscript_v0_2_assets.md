# Manuscript v0.2 Assets

Date: 2026-05-23

Milestone 1.2 generated a continuous manuscript draft plus source-linked SVG and Markdown assets from existing tracked reports only.
The SVG generator is dependency-free because plotting packages are not core
project dependencies in the current environment; no dependency changes were
introduced for manuscript assembly.

## Generated Figures

- `manuscript/figures/generated/fig01_data_product_architecture.svg`
- `manuscript/figures/generated/fig02_grouped_validation_design.svg`
- `manuscript/figures/generated/fig03_capacity_baseline_ladder.svg`
- `manuscript/figures/generated/fig04_c_rate_failure_analysis.svg`
- `manuscript/figures/generated/fig05_stress_feature_decision.svg`
- `manuscript/figures/generated/fig06_pulse_qa_coverage.svg`
- `manuscript/figures/generated/fig07_pulse_resistance_baseline.svg`
- `manuscript/figures/generated/fig08_pulse_capacity_coupling.svg`
- `manuscript/figures/generated/fig09_prior_pulse_vs_nonpulse.svg`
- `manuscript/figures/generated/fig10_claim_ladder.svg`

## Generated Tables

- `manuscript/tables/generated/table01_dataset_audit.md`
- `manuscript/tables/generated/table02_model_ladder.md`
- `manuscript/tables/generated/table03_split_difficulty.md`
- `manuscript/tables/generated/table04_claim_matrix.md`
- `manuscript/tables/generated/table05_negative_results.md`

## Manuscript Draft

- `manuscript/manuscript_v0_2.md`

## Validation Summary

- `mbp report check-manuscript`: `passed`
- `ruff check . --no-cache`: `passed`
- `pytest -p no:cacheprovider`: `110 passed`
- `git diff --check`: `passed`
- Generated assets consume tracked Markdown/CSV/JSON synthesis artifacts only.
- No model training, feature engineering, EIS modeling, or architecture work was performed.

## Remaining Drafting Tasks

- Replace first-pass SVGs with publication-polished plots if needed.
- Convert table Markdown into venue-specific formatting.
- Tighten prose after venue selection.
