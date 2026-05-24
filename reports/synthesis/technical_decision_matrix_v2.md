# Technical Decision Matrix v2

| Option | Evidence for | Evidence against | Risk | Recommendation |
|---|---|---|---|---|
| Stop modeling and return to manuscript/benchmark integration | Major charter gates are closed; claim posture is coherent; threshold-warning diagnostic is now hardened. | Some claims remain diagnostic rather than predictive. | Low; strongest path to publishable benchmark. | Recommended default. |
| Threshold-warning diagnostic extension | 80% threshold warning survives proximity and verified-only sensitivity. | Lead-time remains exploratory and calibration is poor. | Moderate scope creep. | Allow only if tied to reporting, not new architectures. |
| Threshold-warning calibration branch | Diagnostic scores are strong and post-hoc calibration improves mean ECE; Milestone 5.2 adds equal-frequency ECE sensitivity and Milestone 5.3 hardens readiness logic. | Policy-specific C-rate ECE remains above guardrail under fixed-width and equal-frequency binning. | Moderate; further tuning could chase calibration noise. | Do not extend unless a narrow diagnostic calibration question is explicitly needed. |
| Quantile/calibration hygiene | Milestone 5.2 enforced noncrossing capacity quantile endpoints and added equal-frequency ECE. | The hygiene pass did not unblock calibrated risk or calibrated uncertainty. | Low if kept as maintenance; moderate if misread as a new claim. | Complete; keep as diagnostics only. |
| Stressor-robustness forensics | Milestone 5.1 finds a real C-rate `delta_capacity_Ah` gain and Milestone 5.4 shows lighter Pareto settings can reduce outside-C-rate degradation diagnostically. | The predeclared R2/F8/weight=1.0 setting still fails the 5% guardrail at `0.0528343`; passing lighter settings are non-predeclared. | Moderate; further tuning would risk claim chasing. | Complete; keep as diagnostics only. |
| Run-event engineering acceleration | Run-event product is large and had OOM/performance history. | Temporal-order result is negative for modeling value. | Engineering work may not improve claims. | Only if needed for reproducibility/release. |
| EIS feature-quality extension | EIS QA/features are useful diagnostics. | Prior-EIS signal is narrow; broad EIS improvement is blocked. | Modality expansion without claim value. | Defer. |
| Sequence model branch | Charter mentions sequence value as a possible path. | Order-aware features failed vs aggregate/shuffled controls. | High; violates gate discipline. | Do not open. |
| CBAT branch | Long-term charter includes architecture. | Calibration, sequence value, multimodal superiority, and policy gates do not support it. | Very high overclaim risk. | Do not open. |
| Policy ranking branch | Threshold warning is promising. | No calibrated risk, no causal evidence, no intervention validation. | Very high; scientifically unsafe. | Do not open. |

## Recommended Path

Return to benchmark release maintenance or manuscript integration. Milestone
5.4 closes the stressor-robustness forensics pass as diagnostic-only evidence;
additional robustness tuning would need a fresh predeclared question to avoid
claim chasing. Milestone 5.2 calibration/quantile hygiene and Milestone 5.3
correctness hardening are complete and do not justify a new modeling branch.
Do not open policy, causal, CBAT, neural, or sequence claims.
