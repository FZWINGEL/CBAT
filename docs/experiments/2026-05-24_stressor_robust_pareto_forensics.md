# Milestone 5.4 - Stressor-Robust Pareto Forensics

## Scope

Milestone 5.4 follows up the Milestone 5.1 stressor-robust capacity near miss.
It is a bounded diagnostic gate, not a new architecture milestone. The 5%
outside-C-rate non-degradation guardrail is unchanged.

Allowed:

- split-level and condition-level stressor-robust failure forensics;
- a bounded Pareto grid over existing non-neural robust HGB variants;
- reweighting-strength and bag-count sensitivity;
- non-degradation threshold sensitivity reporting.

Blocked:

- new feature engineering;
- neural or sequence models;
- CBAT;
- policy ranking;
- calibrated-risk or calibrated-uncertainty claims;
- causal or same-cell counterfactual claims;
- broad multimodal claims.

## Commands

Existing-report forensics:

```bash
.venv/bin/mbp baseline diagnose-stressor-robust-forensics \
  --report reports/baselines/capacity_stressor_robust_hgb50_report.json \
  --predictions data/processed/capacity_stressor_robust_hgb50_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_hgb50
```

Bounded Pareto grid:

```bash
.venv/bin/mbp baseline run-stressor-robust-pareto \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_pareto_report.json \
  --predictions-out data/processed/capacity_stressor_robust_pareto_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_pareto \
  --model-levels R0_reference_hgb50,R1_condition_balanced_hgb,R2_stressor_balanced_hgb,R3_condition_bagged_hgb,R4_worst_fold_selected_hgb \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --bag-counts 3,5,9 \
  --hgb-max-iter 50
```

## Outputs

- `reports/baselines/capacity_stressor_robust_hgb50/stressor_failure_forensics.md`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/degradation_by_split_target_feature.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/degradation_by_condition.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/worst_regression_conditions.csv`
- `reports/baselines/capacity_stressor_robust_pareto_report.json`
- `reports/baselines/capacity_stressor_robust_pareto/robustness_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_pareto/paired_condition_gains.csv`
- `reports/baselines/capacity_stressor_robust_pareto/plots/pareto_frontier.csv`
- `reports/baselines/capacity_stressor_robust_pareto/plots/non_degradation_threshold_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_pareto/stressor_robust_pareto_claim_readiness.md`

Generated prediction Parquet:

- `data/processed/capacity_stressor_robust_pareto_predictions.parquet`

The prediction Parquet is a local generated artifact and remains ignored.

## Result

The Pareto grid evaluated 16 model settings over 3,827 selected interval rows,
producing 768 metric rows and 663,360 prediction rows.

The predeclared primary setting is:

```text
R2_stressor_balanced_hgb__w1
model: R2_stressor_balanced_hgb
feature group: F8_timestamp_weighted_stress
weight strength: 1.0
```

For `delta_capacity_Ah` under `c_rate_holdout_fold`, the predeclared setting
retains the diagnostic C-rate gain:

| Quantity | Value |
|---|---:|
| C-rate gain vs F4 | `0.0305899` |
| C-rate gain vs stress R0 | `0.0319729` |
| Paired p05 vs F4 | `0.0216868` |
| Paired p05 vs stress R0 | `0.0165793` |
| Max outside-C-rate relative degradation | `0.0528343` |

The predeclared setting therefore fails the unchanged 5% non-degradation
guardrail by `0.0028343` absolute relative-degradation units.

The Pareto frontier also includes lighter R2/F8 settings:

| Setting | Gain vs F4 | Gain vs stress R0 | Max outside-C-rate degradation | Status |
|---|---:|---:|---:|---|
| `R2_stressor_balanced_hgb__w0p25` | `0.0200436` | `0.0214266` | `0.0279117` | diagnostic only |
| `R2_stressor_balanced_hgb__w0p5` | `0.0214501` | `0.0228331` | `0.0476830` | diagnostic only |
| `R2_stressor_balanced_hgb__w1` | `0.0305899` | `0.0319729` | `0.0528343` | predeclared; fails 5% gate |

Because the lighter settings were not the predeclared support rule, they are
useful Pareto diagnostics but do not authorize a supported robust-capacity
claim.

## Forensics

The existing-run forensics rendered 80 split-level degradation rows. The
largest regressions for `delta_capacity_Ah` are concentrated in non-C-rate
views for some robust variants, especially profile and voltage-window rows.
For the predeclared R2/F8 setting specifically, the max outside-C-rate failure
comes from `voltage_window_holdout_fold` on `delta_capacity_Ah`:

```text
reference R0/F8 condition mean MAE: 0.126572
candidate R2/F8 condition mean MAE: 0.133259
relative degradation: 0.0528343
```

## Decision

Milestone 5.4 closes the stressor-robustness follow-up as a diagnostic-only
result:

> Stressor-balanced HGB provides a real diagnostic C-rate `delta_capacity_Ah`
> gain, but the predeclared robust-capacity setting does not pass the unchanged
> 5% outside-C-rate non-degradation guardrail.

Do not claim:

- robust-capacity support;
- C-rate fade is solved;
- architecture readiness;
- policy ranking readiness;
- causal/mechanistic improvement;
- calibrated risk or calibrated uncertainty.

The safe wording is:

> Bounded Pareto diagnostics show a tradeoff between C-rate `delta_capacity_Ah`
> improvement and outside-C-rate degradation. Lighter stressor-balanced weights
> reduce the degradation penalty but remain diagnostic-only because the
> predeclared support setting fails the 5% guardrail.

## Validation

Focused validation during implementation:

```text
.venv/bin/ruff check src/mbp/baselines/stressor_robust_capacity.py src/mbp/cli.py tests/test_stressor_robust_capacity.py --no-cache
.venv/bin/pytest tests/test_stressor_robust_capacity.py -q
```

Result:

```text
All checks passed.
15 passed.
```
