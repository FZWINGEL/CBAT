# Milestone 5.7 - Stressor-Robust Attribution and Reweighting Decomposition Gate

Date: 2026-05-27

## Scope

This milestone decomposes the Milestone 5.6 conservative adaptive
stressor-robust result. The question is whether the C-rate
`delta_capacity_Ah` gain is attributable to timestamp-weighted F8 stress
features, train-only reweighting, or their combination.

No new feature engineering, neural models, sequence models, CBAT, DRT, EIS
embeddings, policy ranking, calibrated-risk claims, calibrated-uncertainty
claims, causal claims, or same-cell counterfactual claims were opened.

## Command

```bash
mbp baseline run-stressor-robust-attribution \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_attribution_report.json \
  --predictions-out data/processed/capacity_stressor_robust_attribution_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_attribution \
  --targets delta_capacity_Ah,capacity_Ah_k1 \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --selection-split-views condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold \
  --hgb-max-iter 50
```

Generated prediction Parquet remains ignored under `data/processed/`.

## Attribution Arms

| Arm | Meaning |
|---|---|
| `D0_R0_F4_reference` | Unweighted HGB with F4 state/LOG_AGE scalar features. |
| `D1_R0_F8_stress_reference` | Unweighted HGB with F8 timestamp-weighted stress features. |
| `D2_adaptive_R2_F4_conservative` | Conservative train-only adaptive stressor-balanced HGB with F4. |
| `D3_adaptive_R2_F8_conservative` | Conservative train-only adaptive stressor-balanced HGB with F8. |

## Results

Primary C-rate `delta_capacity_Ah` comparisons:

| Comparison | Gain | Paired p05 | Interpretation |
|---|---:|---:|---|
| Reweighting only, D2 vs D0 | `0.0106361` | `0.00594397` | Train-only reweighting contributes a real C-rate delta gain. |
| Raw F8, D1 vs D0 | `-0.00138302` | `-0.0166381` | F8 alone does not improve the C-rate delta row. |
| Incremental F8 under adaptive selection, D3 vs D2 | `0.00940756` | `6.06012e-05` | F8 adds C-rate delta signal after reweighting. |
| Combined adaptive F8, D3 vs D0 | `0.0200436` | `0.00749857` | This reproduces the Milestone 5.6 conservative adaptive C-rate delta gain. |
| Adaptive F8 vs raw F8, D3 vs D1 | `0.0214266` | `0.00465696` | Adaptive reweighting remains important relative to raw F8. |

The attribution claim does not pass because the incremental F8 comparison fails
outside-C-rate non-degradation:

| Comparison | Max outside-C-rate degradation | Passes 5% |
|---|---:|---|
| Incremental F8 under adaptive selection | `0.717391` | `False` |
| Reweighting only | `0.0693425` | `False` |
| Adaptive F8 vs raw F8 | `0.0279117` | `True` |

The largest incremental F8 failure is the voltage-window `delta_capacity_Ah`
view. That failure blocks independent stress-feature attribution even though
F8 helps the hard C-rate delta row under adaptive selection.

## Leakage Audit

The adaptive attribution arms use outer-training rows only for selection. The
report records train/test and inner train/validation overlap counts, and the
claim-readiness leakage audit is `passed`.

## Decision

Milestone 5.7 supports a conservative interpretation:

- The Milestone 5.6 adaptive result is not just raw F8 stress-feature value.
- Train-only reweighting contributes C-rate `delta_capacity_Ah` gain.
- F8 adds incremental C-rate delta signal under adaptive selection.
- Independent F8 stress-feature attribution is diagnostic-only because the
  incremental F8 comparison fails outside-C-rate non-degradation.

Allowed wording:

> Conservative train-only adaptive stressor-balanced HGB remains a narrow
> diagnostic C-rate `delta_capacity_Ah` robustness result. F8 stress features
> add C-rate delta signal under adaptive selection, but independent
> stress-feature attribution remains diagnostic-only because outside-C-rate
> non-degradation fails.

Forbidden wording:

- F8 stress features explain the adaptive result independently.
- C-rate fade is solved.
- Architecture, CBAT, sequence/neural models, policy ranking, calibrated risk,
  calibrated uncertainty, causal claims, or broad multimodal claims are
  justified.

## Artifacts

- `reports/baselines/capacity_stressor_robust_attribution_report.json`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_comparisons.csv`
- `reports/baselines/capacity_stressor_robust_attribution/adaptive_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/c_rate_attribution.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/f4_vs_f8_adaptive_gain.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/outside_split_degradation.csv`
