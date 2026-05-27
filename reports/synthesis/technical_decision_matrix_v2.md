# Technical Decision Matrix v2

| Option | Evidence for | Evidence against | Risk | Recommendation |
|---|---|---|---|---|
| Stop modeling and return to manuscript/benchmark integration | Major charter gates are closed; claim posture is coherent; threshold-warning diagnostic is now hardened. | Some claims remain diagnostic rather than predictive. | Low; strongest path to publishable benchmark. | Recommended default. |
| Benchmark task freeze and leaderboard reproducibility | Milestone 7.0 defines the frozen task registry, validates it against the v2 claim matrix, and renders task/model cards from tracked reports only. Milestone 8.0 extends the registry to 17 tasks. | Does not create new model performance. | Low; protects benchmark reproducibility and external handoff. | Complete and maintain as the benchmark interface. |
| Threshold-warning diagnostic extension | 80% threshold warning survives proximity and verified-only sensitivity. | Lead-time remains exploratory and calibration is poor. | Moderate scope creep. | Allow only if tied to reporting, not new architectures. |
| Threshold-warning calibration branch | Diagnostic scores are strong and post-hoc calibration improves mean ECE; Milestone 5.2 adds equal-frequency ECE sensitivity and Milestone 5.3 hardens readiness logic. | Policy-specific C-rate ECE remains above guardrail under fixed-width and equal-frequency binning. | Moderate; further tuning could chase calibration noise. | Do not extend unless a narrow diagnostic calibration question is explicitly needed. |
| Quantile/calibration hygiene | Milestone 5.2 enforced noncrossing capacity quantile endpoints and added equal-frequency ECE. | The hygiene pass did not unblock calibrated risk or calibrated uncertainty. | Low if kept as maintenance; moderate if misread as a new claim. | Complete; keep as diagnostics only. |
| Stressor-robustness diagnostics | Milestone 5.1 finds a real C-rate `delta_capacity_Ah` gain; Milestone 5.4 maps the gain/degradation tradeoff; Milestone 5.5 shows conservative train-only adaptive R2/F8 selection passes the outer diagnostic gate; Milestone 5.6 replicates that conservative diagnostic across five logical deterministic seeds with C-rate gains `0.0200436` vs F4 and `0.0214266` vs stress R0 plus max outside-C-rate degradation `0.0279117`; Milestone 5.7 decomposes the result and finds incremental F8 C-rate gain `0.00940756` under adaptive selection; Milestone 5.8 shows targeted D2-for-C-rate/D0-elsewhere routing preserves C-rate gain `0.0106361` with max outside-C-rate degradation `0`; Milestones 8.6 and 8.7 confirm the delta-only repair boundary explicitly; Milestone 8.8 explains the failed reconstruction branch. | The max-gain selector still fails the guardrail, the result is target-specific, raw F8 does not help C-rate delta, the incremental F8 attribution comparison fails outside-C-rate non-degradation at `0.717391`, the Milestone 5.8 router is not a global model, Milestone 8.6 shows no direct transfer to `capacity_Ah_k1` (`-0.00527031` adaptive gain vs F4, zero router gain), Milestone 8.7 shows capacity-from-delta reconstruction fails the outside-split transfer guardrail (`0.293828` router degradation), and Milestone 8.8 finds two failing direct-reference outside-split comparisons plus 58 degrading hotspots. | Moderate; further tuning would risk claim chasing. | Complete as narrow `delta_capacity_Ah` replicated/adaptive/routing diagnostics with attribution and target-boundary/reconstruction failure diagnostics only; close the current capacity-level branch and return to synthesis/release maintenance. |
| Hierarchical replicate baseline branch | Milestone 5.9 implements the charter-requested L5 comparator with train-only residual partial pooling and replicate-variance intervals. | H4/F4 C-rate delta gain is tiny (`0.000100645`) and paired p05 is negative (`-1.88643e-05`); H5 interval coverage is low (`0.312102` C-rate delta; minimum primary `0.151596`). | Moderate if used for tuning; low if treated as completed negative comparator. | Complete as diagnostic/negative L5 evidence; do not extend without a fresh predeclared question. |
| Multi-horizon capacity forecasting | Milestone 6.0 implements a Q1 multi-step forecasting gate. Prospective HGB K2 beats persistence and prior slope for C-rate horizons 2/3 on both `capacity_Ah_kh` and `delta_capacity_Ah_h`, and for all-split `delta_capacity_Ah_h` horizons 2/3. Milestone 6.1 forensics confirm the C-rate rows. | Overall capacity-level support is partial because all-split horizon-3 `capacity_Ah_kh` HGB K2 MAE `0.0935304` narrowly misses prior slope `0.0932329`; K3 future exposure is oracle-only. Milestone 6.2 prior-trajectory K5 does not repair the horizon-3 capacity row (`0.0981241`) and does not preserve all C-rate horizon-2/3 rows. | Moderate if used for post-hoc tuning or architecture justification. | Complete as scoped diagnostic evidence; prior-trajectory shape is partial/diagnostic only. |
| Run-event engineering acceleration | Run-event product is large and had OOM/performance history. | Temporal-order result is negative for modeling value. | Engineering work may not improve claims. | Only if needed for reproducibility/release. |
| EIS feature-quality extension | EIS QA/features are useful diagnostics. | Prior-EIS signal is narrow; broad EIS improvement is blocked. | Modality expansion without claim value. | Defer. |
| Sequence model branch | Charter mentions sequence value as a possible path. | Order-aware features failed vs aggregate/shuffled controls, and Milestone 7.1 CUDA Torch MLP fixed-length event sequences still fail aggregate-event HGB, timestamp-stress HGB, and C-rate delta controls. | High; violates gate discipline. | Do not open. |
| Observed policy-contrast feasibility | Milestone 7.2 finds 234 triplet-supported observed contrasts across charge C-rate, temperature, voltage-window, and profile families, with 2,943/3,213 observed capacity-loss rows sign-stable. | No ranking model, no calibrated risk, no intervention design, and no causal/same-cell counterfactual evidence. | High if overclaimed as policy guidance; moderate if used only as a next-gate support audit. | Treat as support diagnostics only; a ranking-feasibility baseline would need a separate predeclared gate. |
| Supported contrast-ordering feasibility | Milestone 7.3 uses existing out-of-fold multi-horizon predictions and finds partial signal: HGB K2 `delta_capacity_Ah_h` C-rate horizon-2/3 sign accuracy is `0.826923`/`0.888889`. | The strict bootstrap reference gate fails versus prior slope (`0/10` primary checks pass), and there is still no calibrated risk, intervention design, or causal/same-cell counterfactual evidence. | High if overclaimed as recommendation; moderate if kept as diagnostic. | Complete as partial diagnostic evidence; do not open recommendation or causal branches. |
| Contrast-ordering failure forensics | Milestone 7.4 decomposes the 7.3 failure by effect-size threshold, HGB-vs-prior failure bin, rank correlation, and top-k/regret diagnostics. | The strict prior-slope gate still fails (`0/10`), C-rate medium/large pass rows are only `1/4`, and the result remains diagnostic-only. | High if used to rationalize policy recommendation after a failed gate. | Complete as failure forensics; do not open policy ranking unless a future predeclared large-effect gate is explicitly requested. |
| Support-aware selective reliability | Milestone 8.0 computes train-only support distances and selective retention curves over existing capacity-horizon, threshold-warning, and supported contrast-ordering artifacts. | Primary capacity and threshold-warning metrics worsen at 50% retention, and C-rate support reliability is not supported. | High if misread as deployment reliability or policy safety. | Complete as abstention/support audit only; do not use as policy, calibrated-risk, or deployment evidence. |
| Diagnostic-state distillation | Milestone 8.1 shows PULSE/EIS scalar diagnostic-state surrogates are learnable from check-up-k state and nominal fields: 12/12 auxiliary rows beat train-mean references. | Predicted PULSE+EIS state does not improve downstream capacity-horizon or threshold-warning baselines under the predeclared D3 gate; best all-split capacity primary relative gain is `-0.00790693`, threshold-warning all-split relative Brier gain is `-0.0620807`, and C-rate non-collapse fails. | High if misread as broad multimodal state learning or architecture readiness. | Complete as a negative Q2/H3 gate; keep PULSE/EIS as auxiliary diagnostics only. |
| Diagnostic endpoint horizon forecasting | Milestone 8.2 shows future PULSE/EIS scalar endpoint targets can be constructed leakage-safely and DH3 HGB has useful gains in many grouped rows. Milestone 8.2.1 shows `eis_z_abs_1kHz`, `nyquist_semicircle_width_proxy`, and `pulse_10ms_resistance` pass endpoint-specific diagnostic checks. | The broad strict gate does not fully pass: only `21/24` primary horizon-2/3 rows clear the 10% gain rule and only `22/24` C-rate rows avoid negative gain; `eis_phase_1kHz`, `nyquist_im_peak_abs`, and `pulse_1s_resistance` remain partial. | High if misread as broad multimodal endpoint forecasting or architecture readiness. | Complete as selected scalar endpoint diagnostic evidence plus partial broad endpoint evidence; do not open architecture or broad multimodal branches. |
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
Milestone 8.0 adds support-aware selective reliability diagnostics, but support
filtering does not improve the primary capacity or threshold-warning metrics
and C-rate support reliability is not supported, so it remains an audit layer.
Milestone 8.1 tests diagnostic-state distillation and closes it as a negative
gate: auxiliary PULSE/EIS state can be predicted, but predicted diagnostic
state does not improve downstream capacity-horizon or threshold-warning
baselines enough to support architecture or broad multimodal claims.
Milestone 8.2 tests future PULSE/EIS endpoint forecasting directly. Milestone
8.2.1 narrows this to selected scalar endpoint diagnostics, but the broad gate
is still partial, not an architecture-opening or calibrated-risk result.
Additional robustness tuning would need a fresh predeclared question to avoid
claim chasing.
Milestone 5.2 calibration/quantile hygiene and
Milestone 5.3 correctness hardening remain complete and do not justify a new
modeling branch.
Do not open policy, causal, CBAT, neural, or sequence claims.
