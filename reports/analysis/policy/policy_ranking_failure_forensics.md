# Policy Ranking Failure Forensics

This report diagnoses the Milestone 7.3 supported contrast-ordering near miss using existing CSV artifacts only. It does not train a model, add features, recommend policies, estimate causal effects, or create same-cell counterfactuals.

## Claim Readiness

| Claim area | Status | Evidence | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| contrast-ordering failure forensics | supported_for_diagnostics | Report-only diagnostics generated over existing 7.3 artifacts; 0/10 strict HGB-vs-prior all-family checks pass. | The 7.3 failure can be decomposed by effect size, rank metric, split, horizon, and family. | The diagnostics train a new policy model or prove policy utility. |
| large-effect contrast ordering next gate | diagnostic_only | Some large-effect or thresholded diagnostics improve, but not enough for a new gate. Large-effect passing families: charge_c_rate, temperature; C-rate medium/large pass rows: 1/4; HGB ge_0.02Ah mean sign accuracy: 0.856314. | At most, a future predeclared large-effect supported-contrast gate may be considered if diagnostics justify it. | Policy ranking, recommendation, or broad policy-response modeling is authorized. |
| rank-metric robustness | diagnostic_only | HGB K2 Spearman exceeds prior slope in 3 contrast families: charge_c_rate, temperature, voltage_window. | Rank correlations can contextualize sign-accuracy failures. | Rank metrics validate policy recommendation quality. |
| K3 oracle exclusion | supported_for_diagnostics | Oracle K3 rows are excluded from prospective forensics readiness. | K3 remains an oracle/future-exposure diagnostic only. | K3 is a prospective policy input. |
| policy recommendation | blocked | The gate uses observed supported contrasts and existing prediction artifacts only. | No operating-policy recommendation is made. | Select, prescribe, optimize, or deploy a battery operating policy. |
| causal or same-cell counterfactual policy claims | blocked | Observed condition-triplet contrasts are not same-cell interventions. | Report support-bounded observed contrast diagnostics only. | Changing a policy would cause the estimated degradation effect in the same cell. |
| calibrated policy risk or CBAT readiness | blocked | Calibrated policy utility/risk, CBAT, and architecture claims require later gates that remain blocked. | Scores are diagnostic ordering outputs. | Calibrated policy risk, utility, CBAT, or architecture readiness is supported. |

## Strict Prior-Slope Bootstrap Rows

| Split | Horizon | Gain | Gain p05 | Candidate accuracy | Prior accuracy |
|---|---:|---:|---:|---:|---:|
| c_rate_holdout_fold | 2 | -0.0740741 | -0.190476 | 0.814815 | 0.888889 |
| c_rate_holdout_fold | 3 | 0 | 0 | 0.8125 | 0.8125 |
| condition_fold | 2 | -0.0561031 | -0.0712721 | 0.808188 | 0.864291 |
| condition_fold | 3 | -0.0408664 | -0.0577135 | 0.802207 | 0.843073 |
| profile_holdout_fold | 2 | -0.0763889 | -0.125327 | 0.766204 | 0.842593 |
| profile_holdout_fold | 3 | -0.134328 | -0.207858 | 0.686567 | 0.820896 |
| temperature_holdout_fold | 2 | -0.0338542 | -0.0531547 | 0.867188 | 0.901042 |
| temperature_holdout_fold | 3 | -0.0379009 | -0.0708611 | 0.855685 | 0.893586 |
| voltage_window_holdout_fold | 2 | -0.201788 | -0.235646 | 0.66563 | 0.867418 |
| voltage_window_holdout_fold | 3 | -0.135348 | -0.169862 | 0.719667 | 0.855015 |

## HGB Versus Prior By Effect Bin

| Split | Horizon | Bin | Rows | HGB sign acc. | Prior sign acc. | Gain | HGB MAE | Prior MAE |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| c_rate_holdout_fold | 2 | large_ge_0.05Ah | 46 | 0.891304 | 0.958333 | -0.067029 | 0.234081 | 0.337483 |
| c_rate_holdout_fold | 2 | medium_0.02_to_0.05Ah | 3 | 0.333333 | 0.333333 | 0 | 0.0716656 | 0.0449298 |
| c_rate_holdout_fold | 2 | small_0.01_to_0.02Ah | 1 | 0 | nan | nan | 0.0421976 | 0.0119717 |
| c_rate_holdout_fold | 2 | tiny_lt_0.01Ah | 2 | 0.5 | nan | nan | 0.0942409 | 0.000974 |
| c_rate_holdout_fold | 3 | large_ge_0.05Ah | 25 | 0.88 | 0.8 | 0.08 | 0.248614 | 0.356149 |
| c_rate_holdout_fold | 3 | medium_0.02_to_0.05Ah | 1 | 1 | nan | nan | 0.0143709 | 0.022032 |
| c_rate_holdout_fold | 3 | tiny_lt_0.01Ah | 1 | 1 | 1 | 0 | 0.118476 | 0.004232 |
| condition_fold | 2 | large_ge_0.05Ah | 742 | 0.889488 | 0.954186 | -0.0646985 | 0.180615 | 0.170073 |
| condition_fold | 2 | medium_0.02_to_0.05Ah | 506 | 0.875494 | 0.944568 | -0.0690736 | 0.0457714 | 0.0202677 |
| condition_fold | 2 | small_0.01_to_0.02Ah | 370 | 0.832432 | 0.899425 | -0.0669929 | 0.0291728 | 0.0133251 |
| condition_fold | 2 | tiny_lt_0.01Ah | 1256 | 0.701122 | 0.776771 | -0.0756492 | 0.00987647 | 0.00447989 |
| condition_fold | 3 | large_ge_0.05Ah | 818 | 0.880196 | 0.917355 | -0.0371598 | 0.156571 | 0.165757 |
| condition_fold | 3 | medium_0.02_to_0.05Ah | 481 | 0.846154 | 0.925754 | -0.0796002 | 0.0422944 | 0.0282286 |
| condition_fold | 3 | small_0.01_to_0.02Ah | 363 | 0.839779 | 0.893064 | -0.0532846 | 0.0188494 | 0.0144031 |
| condition_fold | 3 | tiny_lt_0.01Ah | 985 | 0.668718 | 0.72956 | -0.0608418 | 0.00963093 | 0.006054 |
| profile_holdout_fold | 2 | large_ge_0.05Ah | 167 | 0.868263 | 0.955975 | -0.0877114 | 0.156752 | 0.147195 |
| profile_holdout_fold | 2 | medium_0.02_to_0.05Ah | 83 | 0.710843 | 0.802817 | -0.0919735 | 0.0492438 | 0.0339932 |
| profile_holdout_fold | 2 | small_0.01_to_0.02Ah | 70 | 0.6 | 0.796875 | -0.196875 | 0.0229531 | 0.0160491 |
| profile_holdout_fold | 2 | tiny_lt_0.01Ah | 142 | 0.683099 | 0.753623 | -0.0705246 | 0.0148495 | 0.009232 |
| profile_holdout_fold | 3 | large_ge_0.05Ah | 182 | 0.846154 | 0.863905 | -0.0177515 | 0.192875 | 0.19571 |

## HGB Effect-Threshold Sign Accuracy

| Split | Horizon | Threshold | Rows | Sign accuracy | Median abs effect |
|---|---:|---|---:|---:|---:|
| c_rate_holdout_fold | 2 | ge_0.005Ah | 50 | 0.84 | 0.295802 |
| c_rate_holdout_fold | 2 | ge_0.01Ah | 50 | 0.84 | 0.295802 |
| c_rate_holdout_fold | 2 | ge_0.02Ah | 49 | 0.857143 | 0.301872 |
| c_rate_holdout_fold | 2 | ge_0.05Ah | 46 | 0.891304 | 0.312978 |
| c_rate_holdout_fold | 2 | ge_0Ah | 52 | 0.826923 | 0.286359 |
| c_rate_holdout_fold | 3 | ge_0.005Ah | 27 | 0.888889 | 0.315296 |
| c_rate_holdout_fold | 3 | ge_0.01Ah | 26 | 0.884615 | 0.322257 |
| c_rate_holdout_fold | 3 | ge_0.02Ah | 26 | 0.884615 | 0.322257 |
| c_rate_holdout_fold | 3 | ge_0.05Ah | 25 | 0.88 | 0.329218 |
| c_rate_holdout_fold | 3 | ge_0Ah | 27 | 0.888889 | 0.315296 |
| condition_fold | 2 | ge_0.005Ah | 2015 | 0.869479 | 0.0300417 |
| condition_fold | 2 | ge_0.01Ah | 1618 | 0.872064 | 0.0433775 |
| condition_fold | 2 | ge_0.02Ah | 1248 | 0.883814 | 0.0650025 |
| condition_fold | 2 | ge_0.05Ah | 742 | 0.889488 | 0.131777 |
| condition_fold | 2 | ge_0Ah | 2874 | 0.797627 | 0.0139038 |
| condition_fold | 3 | ge_0.005Ah | 1951 | 0.857876 | 0.0368737 |
| condition_fold | 3 | ge_0.01Ah | 1662 | 0.861529 | 0.0480332 |
| condition_fold | 3 | ge_0.02Ah | 1299 | 0.86759 | 0.0718083 |
| condition_fold | 3 | ge_0.05Ah | 818 | 0.880196 | 0.128728 |
| condition_fold | 3 | ge_0Ah | 2647 | 0.790212 | 0.0190323 |

## HGB Rank Diagnostics

| Split | Horizon | Contrasts | Spearman | Kendall tau-b | Status |
|---|---:|---:|---:|---:|---|
| c_rate_holdout_fold | 2 | 25 | 0.31 | 0.173333 | evaluated |
| c_rate_holdout_fold | 3 | 11 | 0.836364 | 0.672727 | evaluated |
| condition_fold | 2 | 227 | 0.753662 | 0.634556 | evaluated |
| condition_fold | 3 | 189 | 0.706195 | 0.607002 | evaluated |
| profile_holdout_fold | 2 | 30 | 0.894994 | 0.71954 | evaluated |
| profile_holdout_fold | 3 | 30 | 0.870078 | 0.687356 | evaluated |
| temperature_holdout_fold | 2 | 74 | 0.831203 | 0.681599 | evaluated |
| temperature_holdout_fold | 3 | 63 | 0.822341 | 0.673323 | evaluated |
| voltage_window_holdout_fold | 2 | 227 | 0.562347 | 0.461296 | evaluated |
| voltage_window_holdout_fold | 3 | 189 | 0.722108 | 0.553867 | evaluated |

## HGB Top-K Harmful Contrast Diagnostics

| Split | Horizon | Top-k | Overlap | Regret | Status |
|---|---:|---:|---:|---:|---|
| c_rate_holdout_fold | 2 | 3 | 0.333333 | 0.303396 | evaluated |
| c_rate_holdout_fold | 2 | 5 | 0.4 | 0.129221 | evaluated |
| c_rate_holdout_fold | 3 | 3 | 0.666667 | 0.0369818 | evaluated |
| c_rate_holdout_fold | 3 | 5 | 1 | 0 | evaluated |
| condition_fold | 2 | 3 | 0 | 0.277047 | evaluated |
| condition_fold | 2 | 5 | 0.2 | 0.337896 | evaluated |
| condition_fold | 3 | 3 | 0.333333 | 0.37479 | evaluated |
| condition_fold | 3 | 5 | 0.2 | 0.399306 | evaluated |
| profile_holdout_fold | 2 | 3 | 0.666667 | 0.121207 | evaluated |
| profile_holdout_fold | 2 | 5 | 0.8 | 0.0223433 | evaluated |
| profile_holdout_fold | 3 | 3 | 0 | 0.460021 | evaluated |
| profile_holdout_fold | 3 | 5 | 0.6 | 0.161124 | evaluated |
| temperature_holdout_fold | 2 | 3 | 0.333333 | 0.12765 | evaluated |
| temperature_holdout_fold | 2 | 5 | 0.2 | 0.151049 | evaluated |
| temperature_holdout_fold | 3 | 3 | 0.333333 | 0.298272 | evaluated |
| temperature_holdout_fold | 3 | 5 | 0.6 | 0.262849 | evaluated |
| voltage_window_holdout_fold | 2 | 3 | 0.333333 | 0.877922 | evaluated |
| voltage_window_holdout_fold | 2 | 5 | 0.2 | 1.0225 | evaluated |
| voltage_window_holdout_fold | 3 | 3 | 0 | 0.522019 | evaluated |
| voltage_window_holdout_fold | 3 | 5 | 0.2 | 0.372881 | evaluated |

## Interpretation

- Near-zero observed contrasts can make sign accuracy brittle; thresholded rows show whether that explains the 7.3 strict-gate failure.
- Rank and top-k diagnostics are support-bounded forensics, not policy optimization.
- Policy recommendation, causal effects, same-cell counterfactuals, calibrated policy risk/utility, sequence/neural models, and CBAT remain blocked.
