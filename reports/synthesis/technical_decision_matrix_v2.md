# Technical Decision Matrix v2

| Option | Evidence for | Evidence against | Risk | Recommendation |
|---|---|---|---|---|
| Stop modeling and return to manuscript/benchmark integration | Major charter gates are closed; claim posture is coherent; threshold-warning diagnostic is now hardened. | Some claims remain diagnostic rather than predictive. | Low; strongest path to publishable benchmark. | Recommended default. |
| Threshold-warning diagnostic extension | 80% threshold warning survives proximity and verified-only sensitivity. | Lead-time remains exploratory and calibration is poor. | Moderate scope creep. | Allow only if tied to reporting, not new architectures. |
| Threshold-warning calibration branch | Diagnostic scores are strong and post-hoc calibration improves mean ECE; Milestone 5.2 adds equal-frequency ECE sensitivity and Milestone 5.3 hardens readiness logic. | Policy-specific C-rate ECE remains above guardrail under fixed-width and equal-frequency binning. | Moderate; further tuning could chase calibration noise. | Do not extend unless a narrow diagnostic calibration question is explicitly needed. |
| Quantile/calibration hygiene | Milestone 5.2 enforced noncrossing capacity quantile endpoints and added equal-frequency ECE. | The hygiene pass did not unblock calibrated risk or calibrated uncertainty. | Low if kept as maintenance; moderate if misread as a new claim. | Complete; keep as diagnostics only. |
| Stressor-robustness forensics | Milestone 5.1 finds a real C-rate `delta_capacity_Ah` gain for stressor-balanced HGB. | The selected candidate narrowly fails the outside-C-rate non-degradation guardrail, especially voltage-window delta. | Moderate; could become tuning unless framed as diagnostics. | Allow only as a narrow forensics pass, not architecture. |
| Run-event engineering acceleration | Run-event product is large and had OOM/performance history. | Temporal-order result is negative for modeling value. | Engineering work may not improve claims. | Only if needed for reproducibility/release. |
| EIS feature-quality extension | EIS QA/features are useful diagnostics. | Prior-EIS signal is narrow; broad EIS improvement is blocked. | Modality expansion without claim value. | Defer. |
| Sequence model branch | Charter mentions sequence value as a possible path. | Order-aware features failed vs aggregate/shuffled controls. | High; violates gate discipline. | Do not open. |
| CBAT branch | Long-term charter includes architecture. | Calibration, sequence value, multimodal superiority, and policy gates do not support it. | Very high overclaim risk. | Do not open. |
| Policy ranking branch | Threshold warning is promising. | No calibrated risk, no causal evidence, no intervention validation. | Very high; scientifically unsafe. | Do not open. |

## Recommended Path

Return to benchmark release maintenance or manuscript integration. If the user
wants one more technical pass, the only defensible ML branch is narrow
stressor-robustness forensics around the Milestone 5.1 voltage-window
degradation. Milestone 5.2 calibration/quantile hygiene is complete and should
not be extended into claim-chasing. Milestone 5.3 correctness hardening is
also complete and does not justify a new modeling branch. Do not open policy,
causal, CBAT, neural, or sequence claims.
