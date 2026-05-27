# Diagnostic-State Distillation Claim Readiness

This gate tests train-only predicted PULSE/EIS diagnostic-state features. It does not use true diagnostic values as downstream features.

| Claim area | Status | Evidence |
|---|---|---|
| Diagnostic-state distillation | `not_supported` | D3 must improve a primary capacity or threshold-warning metric by at least 10%, avoid C-rate collapse, and use only out-of-fold predicted diagnostic-state features. |
| Auxiliary surrogate prediction | `supported_for_diagnostics` | `12` of `12` auxiliary leaderboard rows beat train-mean baselines. |
| Capacity-horizon gain | `not_supported` | Best relative D3 gain: `-0.00790693`. |
| Threshold-warning gain | `not_supported` | Best relative D3 gain: `-0.0620807`. |
| C-rate non-collapse | `not_supported` | D3 must not be worse than D0 on C-rate downstream rows. |
| Leakage audit | `passed` | Downstream features are check-up-k state/time/nominal fields plus out-of-fold predicted diagnostic state. |
| CBAT architecture | `blocked` | Not tested. |
| Neural or sequence models | `blocked` | Not tested. |
| Policy ranking | `blocked` | Not tested. |
| Calibrated risk or uncertainty | `blocked` | Not tested. |

Allowed wording must stay limited to non-neural diagnostic-state distillation under grouped validation.
Forbidden wording: true multimodal architecture, CBAT validation, calibrated risk, policy recommendation, causal effects, or same-cell counterfactual claims.
