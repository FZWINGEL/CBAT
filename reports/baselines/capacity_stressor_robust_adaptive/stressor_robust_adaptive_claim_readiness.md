# Stressor-Robust Adaptive Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Adaptive robust-selection diagnostic | `not_supported` | Train-only adaptive setting passes 5% gate: `False`. |
| C-rate gain | `diagnostic` | Gain vs F4 `0.0312177`; gain vs stress reference `0.0326007`. |
| Paired support | `diagnostic` | p05 vs F4 `0.0194557`; p05 vs stress `0.0122782`. |
| Other split non-degradation | `not_supported` | Max outside-C-rate degradation `0.0645764`. |
| Architecture readiness | `blocked` | This is a non-neural train-only selector. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires the train-only adaptive selector on F8 to retain positive C-rate delta gains versus F4 and stress references, paired p05 above zero for both references, and <=5% outside-C-rate degradation. Outer held-out rows must not be used for weight selection.

Selected weight counts from inner validation: w=0.25: 13, w=0.5: 3, w=0.75: 4, w=1.0: 4.

## Frontier Rows

| Setting | Model | Feature | Gain vs F4 | Gain vs stress | Max outside-C-rate degradation |
|---|---|---|---:|---:|---:|
| `R5_train_only_stressor_selected_hgb` | `R5_train_only_stressor_selected_hgb` | `F4_state_log_age_scalar` | `0.0106361` | `0.0120191` | `0.0564437` |
| `R5_train_only_stressor_selected_hgb` | `R5_train_only_stressor_selected_hgb` | `F8_timestamp_weighted_stress` | `0.0312177` | `0.0326007` | `0.0645764` |

Metric rows evaluated: `48`.
Decision: this supports only an adaptive robust-selection diagnostic if the strict outer guardrail passes.
