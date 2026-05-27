# C-Rate Generalization Root-Cause Diagnostics

## Scope

This is a report-only diagnostic over existing capacity prediction artifacts. It does not train models, add feature engineering, recommend policies, or make causal claims.

## Inputs

- Report schema: `gate5.capacity_baseline.v1`
- Primary split: `c_rate_holdout_fold`
- Primary model for stress-error associations: `L2_hist_gradient_boosting`
- Primary feature group for stress-error associations: `F8_timestamp_weighted_stress`

## Summary

- C-rate metric summary rows: `28`
- Condition hotspot rows: `336`
- Support-overlap rows: `76`
- Low-support condition rows: `52`
- Stress-error association rows: `30`

## Top Condition Hotspots

| Target | Model | Feature group | Parameter set | MAE | Support score | Temperature | C-rate | Voltage/profile |
|---|---|---|---:|---:|---:|---:|---|---|
| delta_capacity_Ah | L2_hist_gradient_boosting | F7_c_rate_focused | 36 | 0.316118 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F7_c_rate_focused | 36 | 0.314184 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| delta_capacity_Ah | L2_hist_gradient_boosting | F10_c_rate_v1_1 | 36 | 0.297399 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F10_c_rate_v1_1 | 36 | 0.288311 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F9_event_segmented_stress | 32 | 0.282835 | 0.598802 | 10.0 | 1.67/1.0 | approx_0_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F7_c_rate_focused | 32 | 0.279398 | 0.598802 | 10.0 | 1.67/1.0 | approx_0_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F4_state_log_age_scalar | 36 | 0.276435 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| capacity_Ah_k1 | L2_hist_gradient_boosting | F9_event_segmented_stress | 36 | 0.27362 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| delta_capacity_Ah | L2_hist_gradient_boosting | F9_event_segmented_stress | 36 | 0.269968 | 0.598802 | 10.0 | 1.67/1.0 | approx_10_100/0 |
| delta_capacity_Ah | L2_hist_gradient_boosting | F7_c_rate_focused | 32 | 0.269921 | 0.598802 | 10.0 | 1.67/1.0 | approx_0_100/0 |

## Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| C-rate root-cause diagnostics | `supported_for_diagnostics` | 336 condition-hotspot rows and 28 C-rate metric summary rows. |
| train-only C-rate support overlap | `supported_for_diagnostics` | 52 of 76 C-rate condition rows have support_score < 0.5. |
| stress-feature error association | `supported_for_diagnostics` | 30 stress-feature high-error association rows. |
| new C-rate repair model readiness | `blocked` | This gate is report-only and trains no repair model. |
| architecture or policy readiness | `blocked` | The report contains no neural, sequence, CBAT, policy-ranking, or causal evidence. |

## Interpretation

The output identifies where C-rate transfer fails and whether failures align with train-only support gaps or stress-exposure regimes. It is not a repair model and does not relax any existing guardrail.
