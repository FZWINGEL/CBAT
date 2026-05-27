# Milestone 8.4 - C-Rate Generalization Root-Cause Diagnostics

## Purpose

This gate diagnoses the persistent C-rate capacity/fade generalization blocker
after the foundational extraction layer passed reproducibility validation. It
uses existing capacity reports, prediction Parquets, interval metadata, and
stress-feature sidecars only.

This is not a repair-model milestone. It adds no feature engineering, no new
model training, no architecture work, no policy ranking, no calibrated-risk
claim, and no causal claim.

## Command

```bash
.venv/bin/mbp analysis diagnose-c-rate-generalization \
  --capacity-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --predictions data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet \
  --interval-table data/interim/interval_table.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out-dir reports/analysis/c_rate_generalization
```

## Outputs

- `reports/analysis/c_rate_generalization/c_rate_failure_report.json`
- `reports/analysis/c_rate_generalization/c_rate_failure_summary.md`
- `reports/analysis/c_rate_generalization/c_rate_condition_hotspots.csv`
- `reports/analysis/c_rate_generalization/c_rate_support_overlap.csv`
- `reports/analysis/c_rate_generalization/c_rate_claim_readiness.md`
- `reports/analysis/c_rate_generalization/plots/c_rate_metric_summary.csv`
- `reports/analysis/c_rate_generalization/plots/c_rate_stress_error_bins.csv`
- `reports/analysis/c_rate_generalization/plots/c_rate_claim_readiness.csv`

## Result

Status: `passed`.

The diagnostic generated:

| Artifact row family | Rows |
|---|---:|
| C-rate metric summaries | 28 |
| C-rate condition hotspots | 336 |
| C-rate support-overlap rows | 76 |
| Low-support C-rate condition rows | 52 |
| Stress-feature high-error association rows | 30 |

The top C-rate hotspots are concentrated in cyclic 1.67C/1.0C held-out
conditions, especially parameter sets 32 and 36 at 10 C and related
high-error C-rate rows. The support-overlap diagnostics show that 52 of 76
C-rate condition rows have support score below 0.5 under the train-only
support metric.

Stress-error associations are diagnostic and non-causal. The strongest
high-error association rows for the primary HGB/F8 setting include larger
`cold_time_h`, higher high-voltage exposure, and different current-exposure
profiles, but these rows do not establish a mechanism or authorize new claims.

## Claim Readiness

| Claim area | Status |
|---|---|
| C-rate root-cause diagnostics | `supported_for_diagnostics` |
| Train-only C-rate support overlap | `supported_for_diagnostics` |
| Stress-feature error association | `supported_for_diagnostics` |
| New C-rate repair model readiness | `blocked` |
| Architecture or policy readiness | `blocked` |

## Decision

The next technical branch, if opened, should be a separate predeclared
non-neural C-rate repair run using this diagnostic report as input. This memo
does not authorize repair-model support, robust-capacity support, calibrated
risk, calibrated uncertainty, policy ranking, neural/sequence models, CBAT,
or causal claims.

## Validation

Commands run:

```bash
.venv/bin/ruff check src/mbp/analysis/c_rate_generalization.py tests/test_c_rate_generalization.py src/mbp/cli.py --no-cache
.venv/bin/pytest tests/test_c_rate_generalization.py -q
.venv/bin/pytest -p no:cacheprovider
.venv/bin/mbp analysis diagnose-c-rate-generalization --capacity-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json --predictions data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet --interval-table data/interim/interval_table.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out-dir reports/analysis/c_rate_generalization
```

Results:

- ruff: passed;
- targeted tests: 4 passed;
- full test suite: 261 passed;
- real report-only diagnostic: passed.
