# Stressor-Robust Adaptive Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Adaptive robust-selection diagnostic | `supported_for_diagnostics` | Train-only adaptive setting passes 5% gate: `True`. |
| C-rate gain | `diagnostic` | Gain vs F4 `0.0200436`; gain vs stress reference `0.0214266`. |
| Paired support | `diagnostic` | p05 vs F4 `0.00749857`; p05 vs stress `0.00465696`. |
| Other split non-degradation | `supported_for_diagnostics` | Max outside-C-rate degradation `0.0279117`. |
| Architecture readiness | `blocked` | This is a non-neural train-only selector. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires the train-only adaptive selector on F8 to retain positive C-rate delta gains versus F4 and stress references, paired p05 above zero for both references, and <=5% outside-C-rate degradation. Outer held-out rows must not be used for weight selection.

Selected weight counts from inner validation: w=0.25: 23, w=0.75: 1.

## Frontier Rows

| Setting | Model | Feature | Gain vs F4 | Gain vs stress | Max outside-C-rate degradation |
|---|---|---|---:|---:|---:|
| `R5_train_only_stressor_selected_hgb` | `R5_train_only_stressor_selected_hgb` | `F8_timestamp_weighted_stress` | `0.0200436` | `0.0214266` | `0.0279117` |
| `R5_train_only_stressor_selected_hgb` | `R5_train_only_stressor_selected_hgb` | `F4_state_log_age_scalar` | `0.0106361` | `0.0120191` | `0.0693425` |

Metric rows evaluated: `48`.
Decision: this supports only an adaptive robust-selection diagnostic if the strict outer guardrail passes.
