# Milestone 5.3 - Calibration and Robustness Gate Correctness Hardening

Date: 2026-05-24

## Scope

This milestone fixes correctness issues in existing readiness gates and runners.
It does not add model families, feature engineering, calibrated-risk claims,
robust-capacity claims, policy ranking, causal claims, sequence/neural models,
DRT, EIS embeddings, or CBAT work.

## Fixes

- Threshold-warning calibration readiness now requires both `all_rows` and
  `verified_only` policies before any strict method can pass.
- C-rate calibration readiness is evaluated per required label policy instead
  of averaging all policies together.
- Fallback-raw calibration rows cannot satisfy strict calibrated-risk readiness.
- Platt scaling uses the same unpenalized logistic convention as the existing
  unpenalized warning baseline.
- Baseline warning probabilities and calibration C0 probabilities are clipped
  consistently before scoring/writing.
- Calibration leaderboards now expose calibrated-only mean metrics alongside
  all-status means so fallback-raw rows cannot be mistaken for calibrated
  performance.
- Calibrated prediction Parquet output now carries Arrow schema metadata.
- Threshold-warning and stressor-robust runners fail when no metrics are
  generated instead of writing a passed empty report.
- Stressor-robust non-degradation readiness treats missing outside-C-rate
  evidence as missing evidence, not as zero degradation.
- Condition-bagged stressor-robust predictions use a stable full-training
  encoder and balanced per-condition row draws.
- R4 train-only selection now documents and applies an explicit tie-break:
  R2, then R1, then R0.

## Refreshed Commands

```bash
.venv/bin/mbp baseline calibrate-threshold-warning \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --out reports/baselines/threshold_warning_calibration_report.json \
  --predictions-out data/processed/threshold_warning_calibrated_predictions.parquet \
  --out-dir reports/baselines/threshold_warning_calibration \
  --targets event_within_1_checkup,event_within_2_checkups,event_within_3_checkups \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --label-policies all_rows,verified_only \
  --hgb-max-iter 50
```

```bash
.venv/bin/mbp baseline run-stressor-robust-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_hgb50_report.json \
  --predictions-out data/processed/capacity_stressor_robust_hgb50_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_hgb50 \
  --model-levels R0_reference_hgb50,R1_condition_balanced_hgb,R2_stressor_balanced_hgb,R3_condition_bagged_hgb,R4_worst_fold_selected_hgb \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50 \
  --bag-count 5
```

## Corrected Calibration Result

The probability-calibration claim remains blocked. The corrected Platt
calibration result improves mean reliability, but C-rate remains above the
fixed-width and equal-frequency ECE guardrails.

| Method | Policy | Primary fixed ECE | Primary equal-freq ECE | C-rate fixed ECE | C-rate equal-freq ECE | C-rate Brier |
|---|---|---:|---:|---:|---:|---:|
| Platt | verified only | `0.0748136` | `0.0729286` | `0.167653` | `0.176185` | `0.148704` |
| Isotonic | verified only | `0.0725802` | `0.0706746` | `0.159021` | `0.159021` | `0.147795` |

Strict calibrated-risk readiness remains `not_supported` because no method
passes the C-rate ECE guardrail under the required policies.

## Corrected Stressor-Robust Result

The stressor-robust capacity result remains diagnostic only. The refreshed
readiness report still finds a supported C-rate `delta_capacity_Ah` diagnostic
gain, but the global robust-capacity claim remains blocked by outside-C-rate
degradation.

| Check | Result |
|---|---:|
| Gain vs F4 R0 | `0.0305899` |
| Gain vs stress R0 | `0.0319729` |
| Paired p05 vs F4 | `0.0216868` |
| Paired p05 vs stress R0 | `0.0165793` |
| Max outside-C-rate degradation | `0.0528343` |

Because the outside-C-rate degradation exceeds the 5% guardrail, robust-capacity
wording remains `not_supported`.

## Claim Decision

Authorized:

- calibration and robustness diagnostics with corrected readiness logic;
- threshold-warning probabilities as diagnostic scores only;
- stressor-balanced HGB as diagnostic C-rate robustness evidence only.

Still blocked:

- calibrated risk;
- calibrated capacity uncertainty;
- robust-capacity or fade-solved claims;
- policy ranking;
- causal or same-cell counterfactual claims;
- sequence/neural models;
- DRT or learned EIS embeddings;
- CBAT architecture;
- broad multimodal claims.

## Validation

Validation run during implementation:

```bash
.venv/bin/pytest tests/test_threshold_warning.py tests/test_stressor_robust_capacity.py -q
.venv/bin/pytest tests/test_threshold_warning.py -q
.venv/bin/ruff check src/mbp/baselines/threshold_warning.py src/mbp/baselines/stressor_robust_capacity.py src/mbp/cli.py tests/test_threshold_warning.py tests/test_stressor_robust_capacity.py --no-cache
.venv/bin/ruff check . --no-cache
.venv/bin/pytest -p no:cacheprovider
.venv/bin/mbp report check-release-candidate
git diff --check
```

Results:

- focused tests: 22 passed;
- full tests: 167 passed;
- Ruff: passed;
- release-candidate checker: passed;
- `git diff --check`: passed.
