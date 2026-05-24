# Milestone 5.5 - Train-Only Stressor-Robust Adaptive Selection

## Scope

Milestone 5.5 follows the Milestone 5.4 Pareto near miss. It tests whether
inner grouped validation on outer-training rows can choose a stressor-balanced
HGB weight that keeps the C-rate `delta_capacity_Ah` gain while satisfying the
unchanged 5% outside-C-rate non-degradation guardrail.

This is still a non-neural baseline gate. It does not add feature engineering,
CBAT, sequence models, policy ranking, calibrated-risk claims,
calibrated-uncertainty claims, causal claims, or same-cell counterfactual
claims.

## Commands

Max-gain selector:

```bash
.venv/bin/mbp baseline run-stressor-robust-adaptive \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_adaptive_report.json \
  --predictions-out data/processed/capacity_stressor_robust_adaptive_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_adaptive \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress \
  --targets delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --selection-split-views condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold \
  --hgb-max-iter 50
```

Conservative selector:

```bash
.venv/bin/mbp baseline run-stressor-robust-adaptive \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_adaptive_conservative_report.json \
  --predictions-out data/processed/capacity_stressor_robust_adaptive_conservative_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_adaptive_conservative \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress \
  --targets delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --selection-split-views condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold \
  --selection-policy conservative_guarded \
  --hgb-max-iter 50
```

## Outputs

- `reports/baselines/capacity_stressor_robust_adaptive_report.json`
- `reports/baselines/capacity_stressor_robust_adaptive/stressor_robust_adaptive_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive/adaptive_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_adaptive/plots/adaptive_frontier.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative_report.json`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/stressor_robust_adaptive_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/adaptive_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/plots/adaptive_frontier.csv`

Generated prediction Parquets:

- `data/processed/capacity_stressor_robust_adaptive_predictions.parquet`
- `data/processed/capacity_stressor_robust_adaptive_conservative_predictions.parquet`

The prediction Parquets are local generated artifacts and remain ignored.

## Result

Both adaptive runs evaluated 3,827 selected interval rows for
`delta_capacity_Ah`, producing 48 metric rows, 96 inner-selection rows, and
41,460 prediction rows per selection policy.

The max-gain policy chooses the highest inner-validation gain among candidates
that pass the inner guardrail. It improves C-rate more strongly, but it fails
the outer non-degradation gate:

| Quantity | Value |
|---|---:|
| C-rate gain vs F4 | `0.0312177` |
| C-rate gain vs stress R0 | `0.0326007` |
| Paired p05 vs F4 | `0.0194557` |
| Paired p05 vs stress R0 | `0.0122782` |
| Max outside-C-rate relative degradation | `0.0645764` |
| Claim status | `not_supported` |

The conservative policy chooses the lowest guarded positive-gain weight when
available. It gives up some C-rate gain but passes the outer diagnostic rule:

| Quantity | Value |
|---|---:|
| C-rate gain vs F4 | `0.0200436` |
| C-rate gain vs stress R0 | `0.0214266` |
| Paired p05 vs F4 | `0.00749857` |
| Paired p05 vs stress R0 | `0.00465696` |
| Max outside-C-rate relative degradation | `0.0279117` |
| Claim status | `supported_for_diagnostics` |

The conservative selector selected weight `0.25` in 23 outer
target/split/feature contexts and weight `0.75` once. The supported frontier
row is:

```text
model: R5_train_only_stressor_selected_hgb
feature group: F8_timestamp_weighted_stress
target: delta_capacity_Ah
```

## Decision

Milestone 5.5 supports a narrow diagnostic claim:

> Conservative train-only adaptive stressor-balanced HGB selection improves
> C-rate `delta_capacity_Ah` while satisfying the unchanged 5%
> outside-C-rate non-degradation guardrail under grouped validation.

Do not claim:

- C-rate fade is solved globally;
- robust-capacity support for all targets;
- calibrated risk or calibrated uncertainty;
- policy ranking readiness;
- causal/mechanistic improvement;
- architecture or CBAT readiness.

The broad C-rate solved-fade claim remains blocked. The adaptive result is a
non-neural diagnostic robustness result and should be replicated before being
elevated in manuscript wording.

## Validation

Focused validation during implementation:

```text
.venv/bin/ruff check src/mbp/baselines/stressor_robust_capacity.py src/mbp/cli.py tests/test_stressor_robust_capacity.py --no-cache
.venv/bin/pytest tests/test_stressor_robust_capacity.py -q
```

Result:

```text
All checks passed.
19 passed.
```
