# Stressor-Robust Attribution Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Incremental F8 value under adaptive selection | `diagnostic_only` | Gain vs adaptive F4 `0.00940756`; paired p05 `6.06012e-05`. |
| Outside-C-rate non-degradation | `not_supported` | Max outside-C-rate degradation for D3 vs D2 `0.717391`. |
| Reweighting-only diagnostic | `diagnostic` | D2 vs D0 C-rate gain `0.0106361`; paired p05 `0.00594397`. |
| Raw F8 diagnostic | `diagnostic` | D1 vs D0 C-rate gain `-0.00138302`; paired p05 `-0.0166381`. |
| Combined adaptive F8 diagnostic | `diagnostic` | D3 vs D0 C-rate gain `0.0200436`; paired p05 `0.00749857`. |
| Leakage audit | `passed` | Adaptive attribution arms use outer-training rows only for selection. |
| Architecture readiness | `blocked` | This remains a non-neural decomposition gate. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires D3 adaptive R2/F8 to beat D2 adaptive R2/F4 on C-rate delta capacity with paired p05 above zero, <=5% outside-C-rate degradation, and a passed leakage audit. If D2 explains the gain, attribute the result to train-only reweighting rather than F8 stress features.

## Primary C-rate Comparisons

| Comparison | Candidate | Reference | Gain | Paired p05 | Relative degradation |
|---|---|---|---:|---:|---:|
| `reweighting_only` | `D2_adaptive_R2_F4_conservative` | `D0_R0_F4_reference` | `0.0106361` | `0.00594397` | `-0.105169` |
| `raw_f8_stress_feature_value` | `D1_R0_F8_stress_reference` | `D0_R0_F4_reference` | `-0.00138302` | `-0.0166381` | `0.0136753` |
| `incremental_f8_under_adaptive` | `D3_adaptive_R2_F8_conservative` | `D2_adaptive_R2_F4_conservative` | `0.00940756` | `6.06012e-05` | `-0.103955` |
| `combined_adaptive_f8_vs_f4` | `D3_adaptive_R2_F8_conservative` | `D0_R0_F4_reference` | `0.0200436` | `0.00749857` | `-0.198191` |
| `adaptive_f8_vs_raw_f8` | `D3_adaptive_R2_F8_conservative` | `D1_R0_F8_stress_reference` | `0.0214266` | `0.00465696` | `-0.209008` |

## Outside-Split Degradation

| Comparison | Max outside-C-rate degradation | Passes 5% |
|---|---:|---:|
| `adaptive_f8_vs_raw_f8` | `0.0279117` | `True` |
| `combined_adaptive_f8_vs_f4` | `0.836479` | `False` |
| `incremental_f8_under_adaptive` | `0.717391` | `False` |
| `raw_f8_stress_feature_value` | `0.786611` | `False` |
| `reweighting_only` | `0.0693425` | `False` |

Comparison rows evaluated: `50`.
Decision: attribution support is diagnostic only and does not authorize a broad C-rate fade-solved claim.
