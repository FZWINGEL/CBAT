# Blocked Claims v2

| Blocked claim | Reason | Source |
|---|---|---|
| Calibrated risk | Threshold-warning probabilities remain diagnostic; post-hoc calibration improves mean ECE but policy-specific C-rate ECE remains high under fixed-width and equal-frequency binning after Milestone 5.3 readiness hardening. | `reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md` |
| Calibrated capacity uncertainty | C-rate conformal coverage remains below target, and noncrossing quantile hygiene does not fix raw q10-q90 undercoverage. | `reports/analysis/calibration_capacity/calibration_claim_readiness.md` |
| Detector-knee prediction | Primary detector knees fail replicate consistency. | `docs/experiments/2026-05-23_knee_label_stability_gate.md` |
| Sequence models | Order-aware event features do not beat aggregate or shuffled controls. | `docs/experiments/2026-05-23_temporal_history_value_gate.md` |
| CBAT | Simpler baselines, calibration, sequence, and multimodal gates do not justify architecture. | `docs/PROJECT_CHARTER.md` |
| Policy ranking | No calibrated risk, no intervention test, and no causal evidence. | `reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md` |
| Broad multimodal improvement | Prior PULSE/EIS do not beat strongest baselines broadly. | `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`; `docs/experiments/2026-05-23_eis_claim_hardening.md` |
| Broad EIS improvement | EIS support is diagnostic/narrow profile-split only. | `docs/experiments/2026-05-23_eis_claim_hardening.md` |
| Prior PULSE strongest-baseline dominance | Prior PULSE does not beat strongest non-PULSE HGB baselines. | `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md` |
| Fade-rate solved | LOG_AGE stress, prior PULSE, and prior EIS do not solve C-rate `delta_capacity_Ah`. | `reports/synthesis/negative_results.md` |
| Stressor-robust training solves C-rate fade globally | Milestone 5.4 confirms C-rate `delta_capacity_Ah` gains are diagnostic only: the predeclared R2/F8/weight=1.0 setting fails the 5% outside-C-rate non-degradation guardrail at `0.0528343`, and lighter passing Pareto settings are non-predeclared. | `docs/experiments/2026-05-24_stressor_robust_pareto_forensics.md` |
| Same-cell counterfactual claims | No same-cell intervention or counterfactual design exists. | `docs/PROJECT_CHARTER.md` |
| DRT or learned EIS embeddings | EIS is gated; current evidence does not justify high-choice feature paths. | `docs/EIS_FEATURE_POLICY.md` |

## Rule

None of these claims may be marked supported in manuscripts, summaries, release
notes, or future branch plans without a new gated milestone and source-linked
evidence.
