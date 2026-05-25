# Milestone 5.6 - Adaptive Stressor-Robust Replication

## Purpose

Milestone 5.6 hardens the Milestone 5.5 adaptive stressor-robust result. It
asks whether the conservative train-only R2 stressor-balanced selector remains
claim-ready under seed/policy sensitivity without relaxing the predeclared 5%
outside-C-rate non-degradation guardrail.

This is not a new model-family milestone. It uses the existing non-neural HGB
stress-feature path, existing F4/F8 feature groups, and existing grouped split
discipline. It does not authorize neural models, sequence models, CBAT, policy
ranking, calibrated-risk wording, calibrated-uncertainty wording, causal
claims, or C-rate fade-solved wording.

## Command

```bash
mbp baseline replicate-stressor-robust-adaptive \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_adaptive_replication \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress \
  --targets delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --weight-strengths 0.25,0.5,0.75,1.0 \
  --selection-split-views condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold \
  --selection-policies conservative_guarded,max_gain_guarded \
  --hgb-max-iter 50
```

The runner records `deterministic_hgb_no_bagging_reuse` because the evaluated
HGB path has no bagging and is deterministic for the represented sample sizes.
The effective fit seed is `42`; logical seeds are `42,101,202,303,404`.

## Outputs

- `reports/baselines/capacity_stressor_robust_adaptive_replication/replication_summary.json`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/adaptive_replication_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/seed_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/policy_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/outside_split_degradation.csv`

## Result

The conservative guarded policy passes all five logical seeds:

- C-rate gain floor versus F4: `0.0200436`;
- C-rate gain floor versus stress R0: `0.0214266`;
- paired p05 floor versus F4: `0.00749857`;
- paired p05 floor versus stress R0: `0.00465696`;
- max outside-C-rate degradation: `0.0279117`;
- leakage audit: `passed`.

The max-gain guarded policy does not pass. It has larger C-rate gains
(`0.0312177` versus F4 and `0.0326007` versus stress R0), but it fails the
outside-C-rate non-degradation guardrail with max degradation `0.0645764`.

## Decision

Supported wording:

> Conservative train-only adaptive stressor-balanced HGB supports a narrow
> replicated diagnostic C-rate `delta_capacity_Ah` robustness result under the
> unchanged grouped validation and outside-C-rate non-degradation guardrail.

Forbidden wording:

- C-rate fade is solved globally.
- Stressor-robust training justifies architecture work.
- The result authorizes policy ranking.
- The result authorizes calibrated risk or calibrated uncertainty.
- The result is causal or same-cell counterfactual evidence.

## Next Step

Return to synthesis, release maintenance, or manuscript integration. Further
robustness tuning would need a fresh predeclared question to avoid claim
chasing.
