# Technical Decision Matrix v2

| Option | Evidence for | Evidence against | Risk | Recommendation |
|---|---|---|---|---|
| Stop modeling and return to manuscript/benchmark integration | Major charter gates are closed; claim posture is coherent; threshold-warning diagnostic is now hardened. | Some claims remain diagnostic rather than predictive. | Low; strongest path to publishable benchmark. | Recommended default. |
| Benchmark task freeze and leaderboard reproducibility | Milestone 7.0 defines the frozen task registry, validates it against the v2 claim matrix, and renders task/model cards from tracked reports only. Milestone 7.4 extends the registry to 16 tasks. | Does not create new model performance. | Low; protects benchmark reproducibility and external handoff. | Complete and maintain as the benchmark interface. |
| Threshold-warning diagnostic extension | 80% threshold warning survives proximity and verified-only sensitivity. | Lead-time remains exploratory and calibration is poor. | Moderate scope creep. | Allow only if tied to reporting, not new architectures. |
| Threshold-warning calibration branch | Diagnostic scores are strong and post-hoc calibration improves mean ECE; Milestone 5.2 adds equal-frequency ECE sensitivity and Milestone 5.3 hardens readiness logic. | Policy-specific C-rate ECE remains above guardrail under fixed-width and equal-frequency binning. | Moderate; further tuning could chase calibration noise. | Do not extend unless a narrow diagnostic calibration question is explicitly needed. |
| Quantile/calibration hygiene | Milestone 5.2 enforced noncrossing capacity quantile endpoints and added equal-frequency ECE. | The hygiene pass did not unblock calibrated risk or calibrated uncertainty. | Low if kept as maintenance; moderate if misread as a new claim. | Complete; keep as diagnostics only. |
| Stressor-robustness diagnostics | Milestone 5.1 finds a real C-rate `delta_capacity_Ah` gain; Milestone 5.4 maps the gain/degradation tradeoff; Milestone 5.5 shows conservative train-only adaptive R2/F8 selection passes the outer diagnostic gate; Milestone 5.6 replicates that conservative diagnostic across five logical deterministic seeds with C-rate gains `0.0200436` vs F4 and `0.0214266` vs stress R0 plus max outside-C-rate degradation `0.0279117`; Milestone 5.7 decomposes the result and finds incremental F8 C-rate gain `0.00940756` under adaptive selection; Milestone 5.8 shows targeted D2-for-C-rate/D0-elsewhere routing preserves C-rate gain `0.0106361` with max outside-C-rate degradation `0`. | The max-gain selector still fails the guardrail, the result is target-specific, raw F8 does not help C-rate delta, the incremental F8 attribution comparison fails outside-C-rate non-degradation at `0.717391`, and the Milestone 5.8 router is not a global model. | Moderate; further tuning would risk claim chasing. | Complete as narrow replicated/adaptive/routing diagnostics with attribution diagnostics only; return to synthesis/release maintenance. |
| Hierarchical replicate baseline branch | Milestone 5.9 implements the charter-requested L5 comparator with train-only residual partial pooling and replicate-variance intervals. | H4/F4 C-rate delta gain is tiny (`0.000100645`) and paired p05 is negative (`-1.88643e-05`); H5 interval coverage is low (`0.312102` C-rate delta; minimum primary `0.151596`). | Moderate if used for tuning; low if treated as completed negative comparator. | Complete as diagnostic/negative L5 evidence; do not extend without a fresh predeclared question. |
| Multi-horizon capacity forecasting | Milestone 6.0 implements a Q1 multi-step forecasting gate. Prospective HGB K2 beats persistence and prior slope for C-rate horizons 2/3 on both `capacity_Ah_kh` and `delta_capacity_Ah_h`, and for all-split `delta_capacity_Ah_h` horizons 2/3. Milestone 6.1 forensics confirm the C-rate rows. | Overall capacity-level support is partial because all-split horizon-3 `capacity_Ah_kh` HGB K2 MAE `0.0935304` narrowly misses prior slope `0.0932329`; K3 future exposure is oracle-only. Milestone 6.2 prior-trajectory K5 does not repair the horizon-3 capacity row (`0.0981241`) and does not preserve all C-rate horizon-2/3 rows. | Moderate if used for post-hoc tuning or architecture justification. | Complete as scoped diagnostic evidence; prior-trajectory shape is partial/diagnostic only. |
| Run-event engineering acceleration | Run-event product is large and had OOM/performance history. | Temporal-order result is negative for modeling value. | Engineering work may not improve claims. | Only if needed for reproducibility/release. |
| EIS feature-quality extension | EIS QA/features are useful diagnostics. | Prior-EIS signal is narrow; broad EIS improvement is blocked. | Modality expansion without claim value. | Defer. |
| Sequence model branch | Charter mentions sequence value as a possible path. | Order-aware features failed vs aggregate/shuffled controls, and Milestone 7.1 CUDA Torch MLP fixed-length event sequences still fail aggregate-event HGB, timestamp-stress HGB, and C-rate delta controls. | High; violates gate discipline. | Do not open. |
| Observed policy-contrast feasibility | Milestone 7.2 finds 234 triplet-supported observed contrasts across charge C-rate, temperature, voltage-window, and profile families, with 2,943/3,213 observed capacity-loss rows sign-stable. | No ranking model, no calibrated risk, no intervention design, and no causal/same-cell counterfactual evidence. | High if overclaimed as policy guidance; moderate if used only as a next-gate support audit. | Treat as support diagnostics only; a ranking-feasibility baseline would need a separate predeclared gate. |
| Supported contrast-ordering feasibility | Milestone 7.3 uses existing out-of-fold multi-horizon predictions and finds partial signal: HGB K2 `delta_capacity_Ah_h` C-rate horizon-2/3 sign accuracy is `0.826923`/`0.888889`. | The strict bootstrap reference gate fails versus prior slope (`0/10` primary checks pass), and there is still no calibrated risk, intervention design, or causal/same-cell counterfactual evidence. | High if overclaimed as recommendation; moderate if kept as diagnostic. | Complete as partial diagnostic evidence; do not open recommendation or causal branches. |
| Contrast-ordering failure forensics | Milestone 7.4 decomposes the 7.3 failure by effect-size threshold, HGB-vs-prior failure bin, rank correlation, and top-k/regret diagnostics. | The strict prior-slope gate still fails (`0/10`), C-rate medium/large pass rows are only `1/4`, and the result remains diagnostic-only. | High if used to rationalize policy recommendation after a failed gate. | Complete as failure forensics; do not open policy ranking unless a future predeclared large-effect gate is explicitly requested. |
| CBAT branch | Long-term charter includes architecture. | Calibration, sequence value, multimodal superiority, and policy gates do not support it. | Very high overclaim risk. | Do not open. |
| Policy ranking branch | Observed matched support exists and Milestone 7.3 shows partial ordering signal. | HGB K2 fails the strict prior-slope bootstrap reference gate, and there is still no calibrated risk, causal evidence, or intervention validation. | Very high; scientifically unsafe if treated as recommendation. | Do not open as a claim branch. |

## Recommended Path

Return to benchmark release maintenance or manuscript integration. Milestone
5.6 locks a narrow positive adaptive stressor-robust diagnostic,
Milestone 5.7 keeps F8 stress-feature attribution diagnostic-only because the
incremental F8 comparison fails outside-split guardrails, and Milestone 5.8
adds targeted stressor-family routing rather than a global robust model.
Milestone 5.9 adds the hierarchical replicate-aware comparator but does not
pass paired C-rate support or interval coverage. Milestone 6.0 adds a scoped
multi-horizon diagnostic, strongest in C-rate and delta-capacity rows, and
Milestone 6.2 shows prior-trajectory shape does not repair the remaining
capacity-level gap. This does not create architecture or policy readiness.
Milestone 7.0 freezes the task registry and leaderboard so future work can
build from a reproducible benchmark interface rather than reopening completed
gates. Milestone 7.1 then tests the obvious sequence/neural objection with
CUDA Torch MLP rows and keeps H7 blocked.
Milestone 7.2 establishes observed matched contrast support but still blocks
policy recommendation, causal, counterfactual, and deployment ranking claims.
Milestone 7.3 then evaluates supported contrast ordering from existing
multi-horizon predictions; the signal is partial and fails the strict
prior-slope bootstrap reference gate, so the policy branch remains blocked.
Milestone 7.4 decomposes that failure, but large-effect and rank diagnostics
remain diagnostic-only.
Additional robustness tuning would need a fresh predeclared question to avoid
claim chasing.
Milestone 5.2 calibration/quantile hygiene and
Milestone 5.3 correctness hardening remain complete and do not justify a new
modeling branch.
Do not open policy, causal, CBAT, neural, or sequence claims.
