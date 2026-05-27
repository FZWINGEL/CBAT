# Milestone 5.9 — Hierarchical Replicate-Aware Capacity Baseline Gate

## Question

Can a non-neural, train-only hierarchical/partial-pooling comparator improve
capacity prediction under grouped stressor holdouts, especially C-rate
`delta_capacity_Ah`, without using held-out condition residuals?

This is the charter-required L5 comparator gate. It is not architecture work,
not sequence modeling, not policy ranking, and not a calibrated-uncertainty
claim.

## Command

```bash
mbp baseline run-hierarchical-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_hierarchical_replicate_report.json \
  --predictions-out data/processed/capacity_hierarchical_replicate_predictions.parquet \
  --out-dir reports/baselines/capacity_hierarchical_replicate \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50
```

## Methods

The runner evaluates:

- `H0_global_train_mean`
- `H1_state_time_ridge`
- `H2_partial_pooling_ridge`
- `H3_hgb_reference`
- `H4_hgb_residual_partial_pooling`
- `H5_replicate_variance_interval`

Residual offsets, shrinkage factors, and interval radii are computed from
outer-training rows only. Parameter-set random effects are not fit. Held-out
parameter sets fall back to stressor-family offsets or the global train
residual offset.

## Outputs

- `reports/baselines/capacity_hierarchical_replicate_report.json`
- `reports/baselines/capacity_hierarchical_replicate/leaderboard.csv`
- `reports/baselines/capacity_hierarchical_replicate/hierarchical_claim_readiness.md`
- `reports/baselines/capacity_hierarchical_replicate/plots/c_rate_hierarchical_gain.csv`
- `reports/baselines/capacity_hierarchical_replicate/plots/c_rate_paired_condition_gains.csv`
- `reports/baselines/capacity_hierarchical_replicate/plots/outside_split_degradation.csv`
- `data/processed/capacity_hierarchical_replicate_predictions.parquet` ignored

The run produced 288 metric rows and 213,672 ignored prediction rows.

## Result

H4/F4 partial pooling gives a tiny C-rate `delta_capacity_Ah` gain versus the
H3/F4 HGB reference:

| Metric | Value |
|---|---:|
| C-rate `delta_capacity_Ah` gain vs H3/F4 | `0.000100645` |
| Paired condition bootstrap p05 | `-1.88643e-05` |
| C-rate paired conditions | `12` |
| Max outside-C-rate relative degradation | `0.00275483` |

The paired-support guardrail fails because p05 is below zero. This keeps the
hierarchical partial-pooling result diagnostic-only.

The H5 replicate-variance interval diagnostic also fails coverage:

| Coverage metric | Value |
|---|---:|
| C-rate `delta_capacity_Ah` interval coverage | `0.312102` |
| Minimum primary interval coverage | `0.151596` |

## Decision

Hierarchical replicate-aware partial pooling is implemented and useful as an
L5 comparator, but it does not authorize a new robustness claim. It also does
not validate calibrated uncertainty.

Allowed wording:

- Train-only hierarchical partial pooling is an L5 diagnostic comparator.
- H4/F4 does not pass paired support for a C-rate `delta_capacity_Ah`
  robustness claim.
- H5 replicate-variance intervals are diagnostic-only and undercovered.

Forbidden wording:

- hierarchical partial pooling solves C-rate fade;
- replicate-aware intervals validate calibrated uncertainty;
- architecture, policy ranking, or CBAT is now justified;
- the result is causal or counterfactual.

## Remaining Blockers

- global robust-capacity claims remain not supported;
- calibrated uncertainty remains blocked;
- calibrated risk remains blocked;
- policy ranking remains blocked;
- CBAT, neural, and sequence models remain blocked.
