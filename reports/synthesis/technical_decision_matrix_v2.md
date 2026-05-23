# Technical Decision Matrix v2

| Option | Evidence for | Evidence against | Risk | Recommendation |
|---|---|---|---|---|
| Stop modeling and return to manuscript/benchmark integration | Major charter gates are closed; claim posture is coherent; threshold-warning diagnostic is now hardened. | Some claims remain diagnostic rather than predictive. | Low; strongest path to publishable benchmark. | Recommended default. |
| Threshold-warning diagnostic extension | 80% threshold warning survives proximity and verified-only sensitivity. | Lead-time remains exploratory and calibration is poor. | Moderate scope creep. | Allow only if tied to reporting, not new architectures. |
| Threshold-warning calibration branch | Diagnostic scores are strong but uncalibrated. | C-rate ECE remains high; calibrated-risk claim could fail. | Moderate; must avoid policy claims. | Optional narrow 3.1 branch. |
| Run-event engineering acceleration | Run-event product is large and had OOM/performance history. | Temporal-order result is negative for modeling value. | Engineering work may not improve claims. | Only if needed for reproducibility/release. |
| EIS feature-quality extension | EIS QA/features are useful diagnostics. | Prior-EIS signal is narrow; broad EIS improvement is blocked. | Modality expansion without claim value. | Defer. |
| Sequence model branch | Charter mentions sequence value as a possible path. | Order-aware features failed vs aggregate/shuffled controls. | High; violates gate discipline. | Do not open. |
| CBAT branch | Long-term charter includes architecture. | Calibration, sequence value, multimodal superiority, and policy gates do not support it. | Very high overclaim risk. | Do not open. |
| Policy ranking branch | Threshold warning is promising. | No calibrated risk, no causal evidence, no intervention validation. | Very high; scientifically unsafe. | Do not open. |

## Recommended Path

Return to manuscript integration and benchmark release preparation. If the
project needs one more technical branch, choose threshold-warning calibration
only, with no policy, causal, CBAT, neural, or sequence claims.
