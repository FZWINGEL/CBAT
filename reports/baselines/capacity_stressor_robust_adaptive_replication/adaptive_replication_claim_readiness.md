# Adaptive Stressor-Robust Replication Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Replicated adaptive robust-selection diagnostic | `supported_for_diagnostics` | All required seeds pass: `True`. |
| Required seed coverage | `diagnostic` | Observed `5` of `5` required seeds; missing `none`. |
| C-rate gain floor | `diagnostic` | Min gain vs F4 `0.0200436`; min gain vs stress `0.0214266`. |
| Paired support floor | `diagnostic` | Min p05 vs F4 `0.00749857`; min p05 vs stress `0.00465696`. |
| Other split non-degradation | `supported_for_diagnostics` | Max outside-C-rate degradation across required seeds `0.0279117`. |
| Leakage audit | `passed` | Outer held-out rows must not enter inner selection. |
| Architecture readiness | `blocked` | This remains a non-neural diagnostic. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires every required conservative_guarded seed to pass C-rate gains versus F4 and stress references, paired p05 above zero, <=5% outside-C-rate degradation, and a passed leakage audit. Any seed failure blocks replicated support.

Seed reuse mode: `deterministic_hgb_no_bagging_reuse`; effective fit seeds: `42`.

## Policy Sensitivity

| Policy | Seeds | Passing seeds | Min gain vs F4 | Min gain vs stress | Max outside-C-rate degradation |
|---|---:|---:|---:|---:|---:|
| `conservative_guarded` | `5` | `5` | `0.0200436` | `0.0214266` | `0.0279117` |
| `max_gain_guarded` | `5` | `0` | `0.0312177` | `0.0326007` | `0.0645764` |

Replication rows evaluated: `10`.
Decision: replicated support is narrow and diagnostic only. Do not claim C-rate fade is solved globally.
