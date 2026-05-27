# Milestone 5.8 - Stressor-Family Arm-Routing Diagnostic Gate

## Question

Can the C-rate `delta_capacity_Ah` gain from train-only reweighting be retained
without carrying the non-C-rate degradation from the broader adaptive/F8 arms?

This is not a new architecture or feature-engineering milestone. It routes
between existing Milestone 5.7 attribution arms:

- C-rate transfer: D2 adaptive R2/F4 when its train-only adaptive guardrail
  passes.
- Non-C-rate transfer: D0 R0/F4 reference.

## Command

```bash
mbp baseline run-stressor-robust-arm-selector \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --attribution-report reports/baselines/capacity_stressor_robust_attribution_report.json \
  --attribution-predictions data/processed/capacity_stressor_robust_attribution_predictions.parquet \
  --out reports/baselines/capacity_stressor_robust_arm_selector_report.json \
  --predictions-out data/processed/capacity_stressor_robust_arm_selector_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_arm_selector \
  --targets delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --selection-split-views condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold \
  --hgb-max-iter 50
```

The report-based mode recombines existing Milestone 5.7 outer-fold predictions
instead of refitting models. The generated prediction Parquet remains ignored.

## Result

The targeted router passes the narrow diagnostic rule:

| Metric | Value |
|---|---:|
| C-rate selector gain vs D0 | `0.0106361` |
| C-rate paired p05 | `0.00594397` |
| Max outside-C-rate degradation | `0` |
| Comparison rows | `5` |
| Selection rows | `24` |
| Prediction rows | `20730` |

The selected-arm summary is deliberately simple: D2 is used for the C-rate
view and D0 is used for the non-C-rate views. This is why the outside-C-rate
degradation is zero; the result should be described as stressor-family routing,
not as a global robust model.

## Claim Decision

Allowed wording:

> A targeted stressor-family router over existing arms preserves the
> reweighting-only C-rate `delta_capacity_Ah` gain while avoiding non-C-rate
> degradation by routing non-C-rate views to the D0 reference.

Forbidden wording:

- C-rate fade is solved.
- Stressor-robust training is globally supported.
- F8 stress features independently explain the gain.
- Architecture, CBAT, policy ranking, calibrated risk, calibrated uncertainty,
  or causal claims are authorized.

## Next Action

Lock this as C24 in the v2 claim ledger. Further stressor-robust work should
not proceed without a fresh, predeclared validation question and preferably an
independent validation design.
