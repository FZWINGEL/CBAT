# Stressor-Robust Arm Selector Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Stressor-family arm-router diagnostic | `supported_for_diagnostics` | C-rate gain vs D0 `0.0106361`; paired p05 `0.00594397`. |
| Outside-C-rate non-degradation | `supported_for_diagnostics` | Max outside-C-rate degradation `0`. |
| Leakage audit | `passed` | C-rate routing uses the D2 train-only adaptive guardrail; non-C-rate views route to D0. |
| Selected arm counts | `diagnostic` | `D0_R0_F4_reference:11; D2_adaptive_R2_F4_conservative:1`. |
| Architecture readiness | `blocked` | This remains a non-neural selector over existing arms. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires the stressor-family arm router to beat D0 R0/F4 on C-rate delta capacity with paired p05 above zero, <=5% outside-C-rate degradation, and a passed leakage audit. This is a targeted diagnostic router over existing arms, not a broad robustness, architecture, policy, or causal claim.

## Primary C-rate Selector Comparison

| Comparison | Gain | Paired p05 | Relative degradation |
|---|---:|---:|---:|
| `selector_vs_d0_f4` | `0.0106361` | `0.00594397` | `-0.105169` |

## Outside-Split Degradation

| Target | Max outside-C-rate degradation | Passes 5% |
|---|---:|---:|
| `delta_capacity_Ah` | `0` | `True` |

Selection rows evaluated: `24`.
Comparison rows evaluated: `5`.
Decision: keep claims narrow. Do not infer C-rate fade is solved or architecture is justified.
