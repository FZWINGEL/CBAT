# Milestone 2.2: Semi-Empirical And Hierarchical Baseline Gate

Date: 2026-05-23

## Scope

Milestone 2.2 adds charter-required domain and replicate-aware comparators before
any architecture work. It evaluates ridge-style semi-empirical stress baselines
for capacity targets and quantifies condition-triplet replicate uncertainty.

This milestone does not authorize neural models, sequence models, CBAT, DRT,
EIS embeddings, policy ranking, capacity+PULSE+EIS architecture work, or
causal/mechanistic claims.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-semi-empirical \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/semi_empirical_capacity_report.json \
  --predictions-out data/processed/semi_empirical_capacity_predictions.parquet \
  --report-dir reports/baselines/semi_empirical_capacity

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline compare-semi-empirical \
  --semi-empirical-report reports/baselines/semi_empirical_capacity_report.json \
  --hgb-f4-report reports/baselines/capacity_hgb50_focused_report.json \
  --stress-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --out-dir reports/baselines/semi_empirical_capacity/comparisons

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp analysis replicate-uncertainty \
  --interval-table data/interim/interval_table.parquet \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --out-dir reports/analysis/replicate_uncertainty
```

The prediction Parquet is an ignored generated artifact and is not tracked.

## Outputs

- `reports/baselines/semi_empirical_capacity_report.json`
- `reports/baselines/semi_empirical_capacity/leaderboard.csv`
- `reports/baselines/semi_empirical_capacity/baseline_summary.md`
- `reports/baselines/semi_empirical_capacity/semi_empirical_claim_readiness.md`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_hgb_f4.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_best_stress.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison_summary.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison.md`
- `reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv`
- `reports/analysis/replicate_uncertainty/model_error_vs_replicate_spread.csv`
- `reports/analysis/replicate_uncertainty/condition_tolerance_intervals.csv`
- `reports/analysis/replicate_uncertainty/c_rate_replicate_uncertainty.md`
- `reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md`
- `reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md`

## Semi-Empirical Baseline Result

The semi-empirical runner produced 240 metric rows across two capacity targets,
five grouped split views, five feature families, and linear/ridge-style
interpretable estimators. The best semi-empirical rows are useful domain
comparators, but they do not beat the current grouped HGB baselines in the
hardest C-rate views.

Positive gain means the semi-empirical comparator has lower condition MAE than
the reference.

| Reference | Target | Split | Best semi group | Reference group | Mean gain | Win rate |
|---|---|---|---|---|---:|---:|
| HGB F4 | `capacity_Ah_k1` | C-rate | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | -0.0979716 | 0.166667 |
| HGB F4 | `delta_capacity_Ah` | C-rate | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | -0.121962 | 0.0833333 |
| strongest stress HGB | `capacity_Ah_k1` | C-rate | `SE3_c_rate_interactions` | `F5_log_age_histograms` | -0.102553 | 0.166667 |
| strongest stress HGB | `delta_capacity_Ah` | C-rate | `SE3_c_rate_interactions` | `F8_timestamp_weighted_stress` | -0.120579 | 0.166667 |
| HGB F4 | `capacity_Ah_k1` | profile | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 0.00417803 | 0.666667 |
| HGB F4 | `delta_capacity_Ah` | profile | `SE3_c_rate_interactions` | `F4_state_log_age_scalar` | 0.0290456 | 0.75 |

The limited profile-holdout gains against F4 do not override the C-rate result
or the strongest-stress comparison. The supported interpretation is that
semi-empirical stress baselines are valuable domain checks, not stronger current
headline baselines.

## Replicate Uncertainty Result

The replicate diagnostic quantifies condition-triplet spread, empirical
tolerance intervals, and model error versus replicate spread. For the focused
HGB F4 C-rate rows:

| Target | Mean model MAE | Mean replicate spread | Error above spread fraction |
|---|---:|---:|---:|
| `capacity_Ah_k1` | 0.125186 | 0.130519 | 0.5 |
| `delta_capacity_Ah` | 0.101133 | 0.115525 | 0.416667 |

C-rate model error is near the observed triplet spread on average, with a
substantial fraction of conditions still above spread. This contextualizes the
C-rate failure but does not prove that the failure is only intrinsic replicate
variability.

## Claim Status

| Claim area | Status | Interpretation |
|---|---|---|
| Semi-empirical beats time/EFC-only comparator | diagnostic_only | SE feature families provide an interpretable ladder, but headline value depends on comparison target and split. |
| Semi-empirical beats HGB F4 | not_supported | C-rate capacity/fade gains versus F4 are negative. |
| Semi-empirical beats strongest stress HGB | not_supported | C-rate capacity/fade gains versus strongest stress HGB are negative. |
| C-rate remains hardest | supported | C-rate remains the unresolved capacity/fade transfer setting. |
| Replicate spread quantified | supported_for_diagnostics | Triplet spread and empirical intervals are now reported by condition/check-up. |
| Calibrated uncertainty readiness | not_supported | Replicate-aware intervals are diagnostic; HGB quantile calibration remains unsupported. |
| Architecture readiness | blocked | Semi-empirical and replicate diagnostics do not justify CBAT or multimodal architecture work. |

## Validation

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
126 passed.

git diff --check
passed.
```

## Decision

Milestone 2.2 strengthens the benchmark by adding domain and replicate-aware
comparators, but it does not change the conservative claim posture. Current
grouped HGB/stress baselines remain stronger than the semi-empirical ridge
comparators in C-rate capacity/fade views. Replicate diagnostics are useful for
interpreting model error but do not validate calibrated uncertainty.

Do not proceed to neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, or capacity+PULSE+EIS architecture work from this evidence.
