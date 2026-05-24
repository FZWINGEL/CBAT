# Milestone 5.1 - Stressor-Axis Robust Capacity Baseline Gate

## Scope

Milestone 5.1 tests whether non-neural robust HGB training variants improve the
hard C-rate capacity/fade split without degrading other grouped views. It uses
existing interval and stress-feature products only. It does not add new feature
engineering, neural/sequence models, CBAT, policy ranking, calibrated-risk
claims, causal claims, or broad multimodal claims.

## Command

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

## Artifacts

- `reports/baselines/capacity_stressor_robust_hgb50_report.json`
- `reports/baselines/capacity_stressor_robust_hgb50/robustness_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/paired_condition_gains.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/c_rate_robustness_summary.md`
- `reports/baselines/capacity_stressor_robust_hgb50/stressor_robustness_claim_readiness.md`
- `data/processed/capacity_stressor_robust_hgb50_predictions.parquet` ignored generated prediction artifact

The run produced 480 metric rows and 356,120 prediction rows over 3,827 primary
interval rows and 2,773 monotonicity-excluding sensitivity rows.

## Model Variants

- `R0_reference_hgb50`: unweighted HGB-50 reference.
- `R1_condition_balanced_hgb`: sample weights equalize parameter-set condition contribution.
- `R2_stressor_balanced_hgb`: train-only sample weights balance the held-out stressor axis.
- `R3_condition_bagged_hgb`: condition-bootstrap ensemble.
- `R4_worst_fold_selected_hgb`: train-only internal condition validation selects among R0/R1/R2.

R4 excludes R3 from nested selection to avoid redundant bagged refits. R3 is
still evaluated directly.

## Result

The strongest C-rate fade row is:

| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---:|---:|
| `delta_capacity_Ah` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0705429` | `0.133845` |

References:

| Reference | Condition mean MAE |
|---|---:|
| F4 R0 | `0.101133` |
| F8 stress R0 | `0.102516` |

The C-rate `delta_capacity_Ah` gain is positive versus both references:

- gain versus F4 R0: `0.0305899`;
- gain versus F8 stress R0: `0.0319729`;
- paired condition bootstrap p05 versus F4: `0.0216868`;
- paired condition bootstrap p05 versus F8 stress R0: `0.0165793`.

This is a real diagnostic improvement in the hard C-rate fade view.

## Claim Gate

The global robust-capacity claim remains **not supported**.

The pre-set rule required C-rate delta gains over F4 and the strongest stress
R0 reference, paired bootstrap p05 above zero against both references, and no
more than 5% relative degradation outside C-rate. The selected candidate fails
the last condition:

| Split | Candidate | Same-feature R0 | Relative degradation |
|---|---:|---:|---:|
| voltage-window holdout, `delta_capacity_Ah` | `0.133259` | `0.126572` | `0.0528343` |

Because `0.0528343` exceeds the 5% guardrail, the result is diagnostic only.

## Decision

Allowed wording:

> Stressor-balanced HGB improves the hard C-rate `delta_capacity_Ah` diagnostic
> row under grouped validation, but a global robust-capacity claim is not
> supported because another grouped split narrowly fails the non-degradation
> guardrail.

Forbidden wording:

- C-rate fade is solved.
- Stressor-robust training globally improves capacity prediction.
- Robust capacity baselines justify CBAT, neural/sequence models, policy ranking, or causal claims.

## Next Action

Default: return to synthesis/release maintenance.

Optional technical follow-up: a narrow forensics pass on the voltage-window
degradation and selection stability. Do not open architecture or new modality
branches from this result.
