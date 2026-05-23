# Table 2. Model Ladder Summary

| ladder_stage | target | split | best_metric | metric_name | interpretation |
| --- | --- | --- | --- | --- | --- |
| L0_persistence | capacity_Ah_k1 | c_rate_holdout_fold | 0.334853996 | condition_mean_mae | Persistence is a necessary reference and is much worse than HGB on C-rate capacity level. |
| L0_persistence | delta_capacity_Ah | c_rate_holdout_fold | 0.334853996 | condition_mean_mae | Persistence is a weak reference for C-rate delta after conversion to delta target. |
| L1_ridge | capacity_Ah_k1 | condition_fold | 0.078224473 | condition_mean_mae | Scaled Ridge with F4 is useful as a linear baseline but does not drive the final claims. |
| L1_ridge | delta_capacity_Ah | condition_fold | 0.078215497 | condition_mean_mae | Ridge remains a sanity baseline for delta and is sensitive to feature scale/feature group choice. |
| HGB_F4 | capacity_Ah_k1 | c_rate_holdout_fold | 0.125186368 | condition_mean_mae | HGB F4 is the main non-stress capacity baseline and establishes C-rate difficulty. |
| HGB_F4 | delta_capacity_Ah | c_rate_holdout_fold | 0.101132771 | condition_mean_mae | HGB F4 remains the threshold that LOG_AGE stress features and prior PULSE failed to beat for C-rate delta. |
| HGB_stress_features | capacity_Ah_k1 | c_rate_holdout_fold | 0.120605293 | condition_mean_mae | Stress features improve C-rate capacity level slightly but do not materially clear the claim threshold. |
| HGB_stress_features | delta_capacity_Ah | c_rate_holdout_fold | 0.101132771 | condition_mean_mae | The best v1.1 stress report still selects F4 for C-rate delta; stress features do not solve fade-rate transfer. |
| prior_PULSE_capacity | capacity_Ah_k1 | c_rate_holdout_fold | 0.120212687 | condition_mean_mae | Prior PULSE improves over F4 but not over the strongest supplied non-PULSE baseline with bootstrap support. |
| prior_PULSE_capacity | delta_capacity_Ah | c_rate_holdout_fold | 0.097734743 | condition_mean_mae | This report-level best row does not overturn paired strongest-non-PULSE comparisons; fade-rate claim remains blocked. |
| PULSE_resistance_baseline | delta_pulse_1s_resistance | condition_fold | 0.000960407 | condition_mean_mae | Canonical RT/50 PULSE resistance is usable for scalar resistance-baseline diagnostics. |
| PULSE_resistance_baseline | delta_pulse_1s_resistance | c_rate_holdout_fold | 0.001858424 | condition_mean_mae | C-rate is also harder for PULSE resistance and should be reported with row-count limitations. |
