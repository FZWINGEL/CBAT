# Multi-Horizon Error Forensics

Milestone 6.1 diagnoses the Milestone 6.0 multi-horizon result using existing reports and prediction artifacts only. It does not train a new model and does not add a new scientific claim.

Baseline rows: 960 metric rows.
Recommended next branch: `prior_trajectory_shape_audit`.

## Primary Horizon 2/3 Reference Gains

| Split | Target | Horizon | HGB K2 MAE | Prior-slope MAE | Gain vs prior | Beats both |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| all | capacity_Ah_kh | 2 | 0.0773609 | 0.0793428 | 0.00198181 | True |
| all | capacity_Ah_kh | 3 | 0.0935304 | 0.0932329 | -0.000297496 | False |
| all | delta_capacity_Ah_h | 2 | 0.0722043 | 0.0793428 | 0.00713843 | True |
| all | delta_capacity_Ah_h | 3 | 0.0807277 | 0.0932329 | 0.0125052 | True |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.183684 | 0.29926 | 0.115576 | True |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 0.221461 | 0.302605 | 0.0811434 | True |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 0.18302 | 0.29926 | 0.11624 | True |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 0.232468 | 0.302605 | 0.0701366 | True |

## C-Rate Condition Hotspots

| Target | Horizon | Parameter set | MAE | Mean SOH | Charge C-rate | Profile |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| delta_capacity_Ah_h | 5 | 40 | 1.02722 | 1 | 1.67 | 0 |
| capacity_Ah_kh | 5 | 56 | 1.02454 | 1 | 1.67 | 0 |
| delta_capacity_Ah_h | 5 | 56 | 1.00566 | 1 | 1.67 | 0 |
| capacity_Ah_kh | 5 | 40 | 0.957776 | 1 | 1.67 | 0 |
| delta_capacity_Ah_h | 2 | 36 | 0.641805 | 1 | 1.67 | 0 |
| capacity_Ah_kh | 2 | 36 | 0.637625 | 1 | 1.67 | 0 |
| delta_capacity_Ah_h | 5 | 60 | 0.53388 | 0.982306 | 1.67 | 0 |
| capacity_Ah_kh | 5 | 60 | 0.527522 | 0.982306 | 1.67 | 0 |
| capacity_Ah_kh | 3 | 28 | 0.499237 | 1 | 1.67 | 0 |
| delta_capacity_Ah_h | 3 | 28 | 0.47364 | 1 | 1.67 | 0 |

## Prior-Slope Failure Modes

| Split | Target | Horizon | Check-up bin | SOH bin | Prior-delta bin | Rows | HGB - prior MAE |
| --- | --- | ---: | --- | --- | --- | ---: | ---: |
| voltage_window_holdout_fold | capacity_Ah_kh | 5 | checkup_13_plus | soh_lt_0_70 | prior_abs_ge_0_05 | 4 | 0.366998 |
| profile_holdout_fold | delta_capacity_Ah_h | 2 | checkup_0_3 | soh_0_70_0_80 | prior_abs_ge_0_05 | 2 | 0.335743 |
| temperature_holdout_fold | capacity_Ah_kh | 5 | checkup_13_plus | soh_lt_0_70 | prior_abs_0_02_0_05 | 1 | 0.309263 |
| condition_fold | delta_capacity_Ah_h | 3 | checkup_8_12 | soh_lt_0_70 | prior_abs_ge_0_05 | 3 | 0.308636 |
| condition_fold | capacity_Ah_kh | 3 | checkup_8_12 | soh_lt_0_70 | prior_abs_ge_0_05 | 3 | 0.304296 |
| temperature_holdout_fold | capacity_Ah_kh | 5 | checkup_13_plus | soh_0_70_0_80 | prior_abs_0_02_0_05 | 55 | 0.298942 |
| profile_holdout_fold | capacity_Ah_kh | 2 | checkup_0_3 | soh_0_70_0_80 | prior_abs_ge_0_05 | 2 | 0.293096 |
| temperature_holdout_fold | delta_capacity_Ah_h | 5 | checkup_13_plus | soh_lt_0_70 | prior_abs_0_02_0_05 | 1 | 0.280269 |
| voltage_window_holdout_fold | delta_capacity_Ah_h | 3 | checkup_8_12 | soh_lt_0_70 | prior_abs_ge_0_05 | 3 | 0.279133 |
| voltage_window_holdout_fold | capacity_Ah_kh | 5 | checkup_0_3 | soh_ge_0_90 | prior_abs_0_005_0_02 | 62 | 0.245802 |

## Oracle Exposure Diagnostic

Rows where K3 oracle exposure improves over K2: 43.
K3 aggregates actual k-to-k+h exposure and remains oracle-diagnostic only.

## Claim Posture

- Multi-horizon forecasting remains scoped by the existing Milestone 6.0 claim readiness.
- C-rate and delta-capacity diagnostics remain the supported diagnostic subset when their rows pass.
- Sequence/neural models, CBAT, policy ranking, causal claims, and calibrated risk/uncertainty remain blocked.
