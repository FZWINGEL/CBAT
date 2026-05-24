# Stressor-Robust Capacity Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Robust C-rate fade improvement | `not_supported` | Gain vs F4 `0.0305899`; gain vs stress reference `0.0319729`; paired p05 vs F4 `0.0216868`; paired p05 vs stress `0.0165793`. |
| Other split non-degradation | `not_supported` | Max relative degradation outside C-rate is `0.0528343`. |
| Architecture readiness | `blocked` | This is a non-neural baseline gate only. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

R4 selects from R0/R1/R2 on internal training-only condition splits. Exact validation-metric ties prefer R2, then R1, then R0. R3 bagging is evaluated directly but excluded from nested selection to avoid redundant bagged refits.

Support requires C-rate delta gains over F4 and strongest stress R0, paired bootstrap p05 above zero against both references, and <=5% degradation outside C-rate.
