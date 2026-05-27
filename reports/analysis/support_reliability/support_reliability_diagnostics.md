# Support-Aware Selective Reliability Diagnostics

This report audits whether train-only condition-support scores identify reliable subsets of existing predictions. It does not train a model, create features, recommend policies, estimate causal effects, or validate calibrated risk.

## Claim Readiness

| Claim area | Status | Evidence | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| support-aware reliability diagnostics | supported_for_diagnostics | Train-only support-distance diagnostics were generated for capacity, threshold-warning, and policy-contrast artifacts. | Support distance can be used to audit where existing predictions are inside or outside observed experimental support. | Support scoring validates deployment, intervention, or counterfactual policy decisions. |
| selective prediction reliability | diagnostic_only | 50% retention gains: capacity MAE -0.0115957, threshold-warning Brier -0.0040389, policy sign accuracy 0.0173861. | Selective reliability curves may be discussed as diagnostic abstention/support-audit evidence. | A selective model is calibrated, deployable, or globally reliable. |
| C-rate support reliability | not_supported | C-rate primary capacity 50% retention MAE gain is -0.0525537. | C-rate support reliability can be discussed only as split-specific diagnostics. | C-rate transfer is solved or safe for policy decisions. |
| policy recommendation | blocked | Support filtering is an abstention diagnostic over existing predictions, not an optimizer or intervention study. | No operating-policy recommendation is made. | Select, prescribe, optimize, or deploy an operating policy. |
| causal or same-cell counterfactual claims | blocked | Support scores compare observed condition metadata and do not create same-cell interventions. | Report support-bounded diagnostics only. | Changing a policy would cause the estimated effect in the same cell. |
| calibrated risk or CBAT readiness | blocked | Selective diagnostics do not calibrate probabilities or justify architecture. | Scores are diagnostic reliability outputs. | Calibrated risk, CBAT, or architecture readiness is supported. |

## Primary Capacity Rows

| Split | Target | Horizon | Retention | Rows | MAE | Support |
|---|---|---:|---:|---:|---:|---:|
| c_rate_holdout_fold | capacity_Ah_kh | 1 | 1 | 157 | 0.112731 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 1 | 0.5 | 79 | 0.134081 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 1 | 121 | 0.183684 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.5 | 61 | 0.202952 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 1 | 87 | 0.221461 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 0.5 | 44 | 0.244208 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 5 | 1 | 50 | 0.292647 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 5 | 0.5 | 25 | 0.432609 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 1 | 1 | 157 | 0.110626 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 1 | 0.5 | 79 | 0.131463 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 1 | 121 | 0.18302 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 0.5 | 61 | 0.199017 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 1 | 87 | 0.232468 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 0.5 | 44 | 0.255922 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 5 | 1 | 50 | 0.302592 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 5 | 0.5 | 25 | 0.452519 | 0.598802 |
| condition_fold | capacity_Ah_kh | 1 | 1 | 3827 | 0.0282871 | 0.743692 |
| condition_fold | capacity_Ah_kh | 1 | 0.5 | 1914 | 0.023085 | 0.783053 |
| condition_fold | capacity_Ah_kh | 2 | 1 | 3599 | 0.0509975 | 0.743279 |
| condition_fold | capacity_Ah_kh | 2 | 0.5 | 1800 | 0.0356836 | 0.782465 |
| condition_fold | capacity_Ah_kh | 3 | 1 | 3373 | 0.0603207 | 0.742843 |
| condition_fold | capacity_Ah_kh | 3 | 0.5 | 1687 | 0.0416387 | 0.781851 |
| condition_fold | capacity_Ah_kh | 5 | 1 | 2971 | 0.0781763 | 0.742555 |
| condition_fold | capacity_Ah_kh | 5 | 0.5 | 1486 | 0.0542661 | 0.7815 |
| condition_fold | delta_capacity_Ah_h | 1 | 1 | 3827 | 0.0270319 | 0.743692 |
| condition_fold | delta_capacity_Ah_h | 1 | 0.5 | 1914 | 0.020327 | 0.783053 |
| condition_fold | delta_capacity_Ah_h | 2 | 1 | 3599 | 0.0511646 | 0.743279 |
| condition_fold | delta_capacity_Ah_h | 2 | 0.5 | 1800 | 0.0361271 | 0.782465 |
| condition_fold | delta_capacity_Ah_h | 3 | 1 | 3373 | 0.054406 | 0.742843 |
| condition_fold | delta_capacity_Ah_h | 3 | 0.5 | 1687 | 0.0376945 | 0.781851 |

## Primary Threshold-Warning Rows

| Split | Target | Retention | Rows | Brier | ECE | Support |
|---|---|---:|---:|---:|---:|---:|
| c_rate_holdout_fold | event_within_1_checkup | 1 | 157 | 0.0946311 | 0.106224 | 0.598802 |
| c_rate_holdout_fold | event_within_1_checkup | 0.5 | 79 | 0.143328 | 0.159807 | 0.598802 |
| c_rate_holdout_fold | event_within_2_checkups | 1 | 157 | 0.179176 | 0.198155 | 0.598802 |
| c_rate_holdout_fold | event_within_2_checkups | 0.5 | 79 | 0.249247 | 0.290744 | 0.598802 |
| c_rate_holdout_fold | event_within_3_checkups | 1 | 157 | 0.15993 | 0.174673 | 0.598802 |
| c_rate_holdout_fold | event_within_3_checkups | 0.5 | 79 | 0.176317 | 0.20796 | 0.598802 |
| condition_fold | event_within_1_checkup | 1 | 3827 | 0.0180229 | 0.0115975 | 0.743692 |
| condition_fold | event_within_1_checkup | 0.5 | 1914 | 0.0135667 | 0.00964939 | 0.783053 |
| condition_fold | event_within_2_checkups | 1 | 3827 | 0.0329656 | 0.0213274 | 0.743692 |
| condition_fold | event_within_2_checkups | 0.5 | 1914 | 0.0251347 | 0.018377 | 0.783053 |
| condition_fold | event_within_3_checkups | 1 | 3827 | 0.0424326 | 0.0256558 | 0.743692 |
| condition_fold | event_within_3_checkups | 0.5 | 1914 | 0.0265007 | 0.0149269 | 0.783053 |
| profile_holdout_fold | event_within_1_checkup | 1 | 752 | 0.0385021 | 0.0369786 | 0.405583 |
| profile_holdout_fold | event_within_1_checkup | 0.5 | 376 | 0.0517961 | 0.0561323 | 0.405583 |
| profile_holdout_fold | event_within_2_checkups | 1 | 752 | 0.0503378 | 0.0359409 | 0.405583 |
| profile_holdout_fold | event_within_2_checkups | 0.5 | 376 | 0.061464 | 0.0523207 | 0.405583 |
| profile_holdout_fold | event_within_3_checkups | 1 | 752 | 0.0827742 | 0.0578649 | 0.405583 |
| profile_holdout_fold | event_within_3_checkups | 0.5 | 376 | 0.0943595 | 0.0858527 | 0.405583 |
| temperature_holdout_fold | event_within_1_checkup | 1 | 1802 | 0.0247654 | 0.0202784 | 0.676471 |
| temperature_holdout_fold | event_within_1_checkup | 0.5 | 901 | 0.0181322 | 0.0186101 | 0.727941 |
| temperature_holdout_fold | event_within_2_checkups | 1 | 1802 | 0.0444031 | 0.0383971 | 0.676471 |
| temperature_holdout_fold | event_within_2_checkups | 0.5 | 901 | 0.0320153 | 0.0284965 | 0.727941 |
| temperature_holdout_fold | event_within_3_checkups | 1 | 1802 | 0.0568194 | 0.0453184 | 0.676471 |
| temperature_holdout_fold | event_within_3_checkups | 0.5 | 901 | 0.0310409 | 0.0285971 | 0.727941 |
| voltage_window_holdout_fold | event_within_1_checkup | 1 | 3827 | 0.0273181 | 0.0238258 | 0.44096 |
| voltage_window_holdout_fold | event_within_1_checkup | 0.5 | 1914 | 0.0374704 | 0.0298358 | 0.491861 |
| voltage_window_holdout_fold | event_within_2_checkups | 1 | 3827 | 0.044963 | 0.0308963 | 0.44096 |
| voltage_window_holdout_fold | event_within_2_checkups | 0.5 | 1914 | 0.0659051 | 0.055811 | 0.491861 |
| voltage_window_holdout_fold | event_within_3_checkups | 1 | 3827 | 0.0694696 | 0.0586963 | 0.44096 |
| voltage_window_holdout_fold | event_within_3_checkups | 0.5 | 1914 | 0.103403 | 0.0917054 | 0.491861 |

## Primary Policy-Contrast Rows

| Split | Target | Horizon | Retention | Rows | Sign accuracy | Support |
|---|---|---:|---:|---:|---:|---:|
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 1 | 52 | 0.903846 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.5 | 26 | 0.961538 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 1 | 33 | 0.848485 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.5 | 17 | 0.941176 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 1 | 19 | 1 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.5 | 10 | 1 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 1 | 27 | 0.888889 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 0.5 | 14 | 0.928571 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 1 | 18 | 0.833333 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 0.5 | 9 | 1 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 1 | 9 | 1 | 0.598802 |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | 0.5 | 5 | 1 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 1 | 52 | 0.826923 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 0.5 | 26 | 0.884615 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 1 | 33 | 0.787879 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 0.5 | 17 | 0.941176 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 1 | 19 | 0.894737 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 2 | 0.5 | 10 | 0.9 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 1 | 27 | 0.888889 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 0.5 | 14 | 0.928571 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 1 | 18 | 0.833333 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 0.5 | 9 | 1 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 1 | 9 | 1 | 0.598802 |
| c_rate_holdout_fold | delta_capacity_Ah_h | 3 | 0.5 | 5 | 1 | 0.598802 |
| condition_fold | capacity_Ah_kh | 2 | 1 | 2874 | 0.91858 | 0.72161 |
| condition_fold | capacity_Ah_kh | 2 | 0.5 | 1437 | 0.914405 | 0.761283 |
| condition_fold | capacity_Ah_kh | 2 | 1 | 172 | 0.97093 | 0.727843 |
| condition_fold | capacity_Ah_kh | 2 | 0.5 | 86 | 0.94186 | 0.752643 |
| condition_fold | capacity_Ah_kh | 2 | 1 | 164 | 0.908537 | 0.662771 |
| condition_fold | capacity_Ah_kh | 2 | 0.5 | 82 | 0.926829 | 0.735255 |

## Interpretation

- Support filtering is an abstention/reliability diagnostic over existing artifacts.
- It must not be described as calibrated risk, policy optimization, causal evidence, same-cell counterfactual evidence, CBAT readiness, or deployment support.
