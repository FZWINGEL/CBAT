# 2026-05-22 Capacity Baseline Review And Robustness

## Scope

Milestone 0.5b reviews and hardens the scalar capacity baseline evidence. It
does not add EIS/PULSE features, knee labels, sequence models, neural models,
policy ranking, or CBAT architecture.

## Experiment 1: Baseline Diagnostics From Existing Full Report

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-capacity \
  --report reports/baselines/capacity_l0_l3_report.json \
  --out-dir reports/baselines/capacity_l0_l3
```

Generated artifacts:

- `reports/baselines/capacity_l0_l3/baseline_diagnostics.md`
- `reports/baselines/capacity_l0_l3/c_rate_holdout_error_analysis.md`
- `reports/baselines/capacity_l0_l3/plots/feature_gain_by_split.csv`
- `reports/baselines/capacity_l0_l3/plots/best_by_target_split.csv`
- `reports/baselines/capacity_l0_l3/plots/c_rate_holdout_errors.csv`
- `reports/baselines/capacity_l0_l3/plots/c_rate_holdout_by_condition.csv`

Finding:

- C-rate holdout remains the hardest split in the bounded `hgb_max_iter=5`
  full report.
- Adjacent feature gains in the original full report were mixed:
  - `F1_state_time -> F2_state_exposure`: mean primary gain `-0.001142`
  - `F2_state_exposure -> F3_state_nominal`: mean primary gain `0.009012`
  - `F3_state_nominal -> F4_state_log_age_scalar`: mean primary gain `-0.033302`
- Strict-vs-tolerant sensitivity remained small on average:
  mean primary-minus-sensitivity condition-mean MAE `-0.000087`.

Decision:

- Do not claim LOG_AGE scalar features help from the first full report alone.
- Keep C-rate holdout as the first focused error-analysis target.

## Experiment 2: Ridge Train-Fold Numeric Standardization

Implementation:

- `FeatureEncoder.fit()` now stores train-fold numeric means and standard
  deviations.
- `FeatureEncoder.transform(..., standardize_numeric=True)` standardizes only
  numeric columns.
- `L1_ridge` uses train-fold numeric standardization.
- Categorical one-hot columns are not standardized.
- Reports record:
  - `numeric_standardization = train_fold_mean_std`
  - `numeric_standardization_applies_to = ["L1_ridge"]`

Command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
UV_CACHE_DIR=/tmp/uv-cache timeout 7200s .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --out reports/baselines/capacity_l1_scaled_report.json \
  --predictions-out data/processed/capacity_l1_scaled_predictions.parquet \
  --model-levels L0_persistence,L1_ridge
```

Result:

- Status: passed.
- Metric rows: `288`.
- Prediction Parquet: `data/processed/capacity_l1_scaled_predictions.parquet`
  (`ignored`).

Selected comparisons against the previous unscaled full report:

| Split | Target | Feature group | Old MAE | Scaled MAE | Gain |
|---|---|---|---:|---:|---:|
| `condition_fold` | `capacity_Ah_k1` | `F4_state_log_age_scalar` | 0.081819 | 0.078224 | 0.003595 |
| `condition_fold` | `delta_capacity_Ah` | `F4_state_log_age_scalar` | 0.081203 | 0.078215 | 0.002988 |
| `profile_holdout_fold` | `capacity_Ah_k1` | `F2_state_exposure` | 0.078735 | 0.077580 | 0.001156 |
| `c_rate_holdout_fold` | `capacity_Ah_k1` | `F3_state_nominal` | 0.175561 | 0.176993 | -0.001432 |

Finding:

- Scaling modestly improves Ridge in several condition/profile comparisons.
- Scaling does not resolve the C-rate holdout difficulty.
- For scaled Ridge, `F3_state_nominal -> F4_state_log_age_scalar` remains
  negative on average, so LOG_AGE scalar features are still not a stable Ridge
  win.

## Experiment 3: Focused HGB-50 Robustness

Command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
UV_CACHE_DIR=/tmp/uv-cache timeout 7200s .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --out reports/baselines/capacity_hgb50_focused_report.json \
  --predictions-out data/processed/capacity_hgb50_focused_predictions.parquet \
  --model-levels L2_hist_gradient_boosting,L3_quantile_hist_gradient_boosting \
  --feature-groups F1_state_time,F2_state_exposure,F3_state_nominal,F4_state_log_age_scalar \
  --hgb-max-iter 50
```

Result:

- Status: passed.
- Metric rows: `384`.
- `hgb_max_iter`: `50`.
- Prediction Parquet: `data/processed/capacity_hgb50_focused_predictions.parquet`
  (`ignored`).

Primary-run highlights:

- Best `capacity_Ah_k1`: `L2_hist_gradient_boosting` +
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.053927`.
- Best `delta_capacity_Ah`: `L2_hist_gradient_boosting` +
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.044645`.
- Best C-rate `delta_capacity_Ah`: `L2_hist_gradient_boosting` +
  `F4_state_log_age_scalar`, condition-mean MAE `0.101133`.
- Best C-rate `capacity_Ah_k1`: `L2_hist_gradient_boosting` +
  `F4_state_log_age_scalar`, condition-mean MAE `0.125186`.
- Quantile rows: `40`; mean q10-q90 coverage `0.664674`, mean interval width
  `0.162964`.

Feature-gain summary:

| Feature transition | Mean primary gain | Median primary gain | Positive rows |
|---|---:|---:|---:|
| `F1_state_time -> F2_state_exposure` | -0.002655 | -0.000247 | 10 / 20 |
| `F2_state_exposure -> F3_state_nominal` | 0.008439 | 0.006469 | 19 / 20 |
| `F3_state_nominal -> F4_state_log_age_scalar` | 0.000085 | 0.001124 | 10 / 20 |

Finding:

- The `hgb_max_iter=5` run was too constrained for HGB interpretation.
- With `hgb_max_iter=50`, HGB improves materially and `F4_state_log_age_scalar`
  becomes the best focused HGB feature group for several split/target views.
- Nominal protocol features remain more consistently useful than raw exposure
  deltas alone.
- LOG_AGE scalar features look model-dependent: weak/unstable for Ridge,
  potentially useful for HGB.

## Experiment 4: Quantile Metrics

Added metrics:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Decision:

- Quantile metrics are computed only when q10/q50/q90 predictions are present.
- The first HGB-50 quantile coverage is diagnostic only; it is not yet a
  calibrated uncertainty claim.

## Current Decisions

- Milestone 0.5b remains capacity-only.
- C-rate holdout is still the leading generalization failure mode.
- Ridge conclusions should use train-fold numeric standardization.
- HGB conclusions should not be based on the `hgb_max_iter=5` bounded smoke
  alone.
- Do not expand to EIS/PULSE, knee prediction, sequence models, neural models,
  policy ranking, or CBAT until the capacity diagnostics are reviewed.

## Validation

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
```

Result:

- Ruff: passed.
- Pytest: `74 passed, 1 warning`.
- Warning: existing `datetime.utcnow()` deprecation warning in
  `src/mbp/data/luh_blank/qa_result_data.py`.
