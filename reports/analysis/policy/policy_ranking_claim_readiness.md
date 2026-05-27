# Supported Contrast Ordering Claim Readiness

This report evaluates existing out-of-fold multi-horizon predictions on matched observed condition contrasts. It does not train a model, optimize policies, estimate causal effects, or create same-cell counterfactuals.

## Claim Readiness

| Claim area | Status | Evidence | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| supported observed contrast ordering feasibility | partially_supported | Primary HGB K2 mean sign accuracy 0.780; 0/10 primary bootstrap reference checks pass; 2 families pass reference comparison | Existing prospective forecasts can be evaluated for supported observed contrast ordering diagnostics. | Policy recommendation, causal ranking, or deployment utility is supported. |
| C-rate contrast ordering | diagnostic_only | 2 C-rate primary horizon rows have sign accuracy at or above 0.5. | C-rate contrast ordering may be discussed only as a held-out diagnostic if the primary gate passes. | C-rate policy optimization is authorized. |
| K3 oracle exposure ordering diagnostic | diagnostic_only | 54700 oracle K3 pairwise rows are labeled oracle_diagnostic_only. | K3 can be used only to bound the value of future exposure information. | K3 is a prospective policy input. |
| policy recommendation | blocked | The gate evaluates observed support and out-of-fold ordering only; it does not optimize interventions. | No policy recommendation is made. | Choose, prescribe, or deploy an operating policy from these diagnostics. |
| causal or same-cell counterfactual policy claims | blocked | Contrasts are between observed condition triplets, not randomized same-cell interventions. | Effects are observed contrast diagnostics inside support. | Changing a policy would cause the estimated effect in the same cell. |
| calibrated policy risk or utility | blocked | Capacity and threshold-warning calibration gates still block calibrated risk/uncertainty wording. | Scores are diagnostic ordering outputs only. | The probabilities or utilities are calibrated for policy decisions. |

## Primary HGB K2 Rows

| Split | Horizon | Rows | Sign accuracy | Mean effect abs error |
|---|---:|---:|---:|---:|
| c_rate_holdout_fold | 2 | 52 | 0.826923 | 0.215642 |
| c_rate_holdout_fold | 3 | 27 | 0.888889 | 0.235118 |
| condition_fold | 2 | 2874 | 0.797627 | 0.0627611 |
| condition_fold | 3 | 2647 | 0.790212 | 0.0622394 |
| profile_holdout_fold | 2 | 462 | 0.742424 | 0.0735502 |
| profile_holdout_fold | 3 | 432 | 0.67907 | 0.108319 |
| temperature_holdout_fold | 2 | 867 | 0.86088 | 0.064663 |
| temperature_holdout_fold | 3 | 793 | 0.851206 | 0.0755417 |
| voltage_window_holdout_fold | 2 | 2874 | 0.655914 | 0.0808923 |
| voltage_window_holdout_fold | 3 | 2647 | 0.707893 | 0.0766438 |

## Primary Bootstrap Reference Checks

| Split | Horizon | Reference | Gain | Gain p05 | Matched contrasts |
|---|---:|---|---:|---:|---:|
| c_rate_holdout_fold | 2 | MH1_prior_slope_linear / prior_slope | -0.0740741 | -0.190476 | 11 |
| c_rate_holdout_fold | 3 | MH1_prior_slope_linear / prior_slope | 0 | 0 | 6 |
| condition_fold | 2 | MH1_prior_slope_linear / prior_slope | -0.0561031 | -0.0712721 | 189 |
| condition_fold | 3 | MH1_prior_slope_linear / prior_slope | -0.0408664 | -0.0577135 | 180 |
| profile_holdout_fold | 2 | MH1_prior_slope_linear / prior_slope | -0.0763889 | -0.125327 | 30 |
| profile_holdout_fold | 3 | MH1_prior_slope_linear / prior_slope | -0.134328 | -0.207858 | 30 |
| temperature_holdout_fold | 2 | MH1_prior_slope_linear / prior_slope | -0.0338542 | -0.0531547 | 63 |
| temperature_holdout_fold | 3 | MH1_prior_slope_linear / prior_slope | -0.0379009 | -0.0708611 | 60 |
| voltage_window_holdout_fold | 2 | MH1_prior_slope_linear / prior_slope | -0.201788 | -0.235646 | 189 |
| voltage_window_holdout_fold | 3 | MH1_prior_slope_linear / prior_slope | -0.135348 | -0.169862 | 180 |

## Interpretation

- Supported wording is limited to observed-support contrast-ordering diagnostics.
- K3 oracle rows are diagnostic only because they include future exposure over the forecast horizon.
- Policy recommendations, causal claims, same-cell counterfactual claims, calibrated risk, CBAT, and broad architecture claims remain blocked.
