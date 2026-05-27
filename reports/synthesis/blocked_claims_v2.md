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
| Stressor-robust training solves C-rate fade globally | Milestone 5.6 supports a narrow replicated conservative train-only adaptive R2/F8 diagnostic for `delta_capacity_Ah`, but this is not a global solved-fade claim. The earlier fixed-weight predeclared R2/F8/weight=1.0 setting still fails the 5% guardrail at `0.0528343`; the max-gain adaptive policy still fails at `0.0645764`; the conservative result is target-specific, non-neural, and diagnostic only. Milestone 5.8 adds targeted C-rate routing over existing arms, but that is not a global robust-capacity model. | `docs/experiments/2026-05-24_adaptive_stressor_robust_replication.md`; `docs/experiments/2026-05-27_stressor_robust_arm_selector_gate.md` |
| Adaptive stressor-robust gain is independently attributable to F8 stress features | Milestone 5.7 shows incremental F8 value under adaptive selection for C-rate `delta_capacity_Ah`, but that comparison fails the unchanged outside-C-rate non-degradation guardrail at `0.717391`; reweighting-only also contributes a positive C-rate gain. | `docs/experiments/2026-05-27_stressor_robust_attribution_gate.md` |
| Hierarchical partial pooling solves C-rate fade | Milestone 5.9 implements train-only hierarchical replicate-aware partial pooling, but H4/F4 gives only a tiny C-rate `delta_capacity_Ah` gain (`0.000100645`) and paired bootstrap p05 is negative (`-1.88643e-05`); H5 interval coverage also fails. | `docs/experiments/2026-05-27_hierarchical_replicate_baseline_gate.md` |
| Multi-horizon capacity forecasting is solved globally | Milestone 6.0 supports C-rate and delta-capacity multi-horizon diagnostics, but all-split horizon-3 `capacity_Ah_kh` HGB K2 narrowly misses prior slope. | `docs/experiments/2026-05-27_multi_horizon_capacity_forecasting_gate.md` |
| Future k-to-k+h exposure is a prospective multi-horizon input | K3 oracle exposure features aggregate the actual future horizon exposure and are diagnostic only. | `docs/experiments/2026-05-27_multi_horizon_capacity_forecasting_gate.md` |
| Same-cell counterfactual claims | No same-cell intervention or counterfactual design exists. | `docs/PROJECT_CHARTER.md` |
| DRT or learned EIS embeddings | EIS is gated; current evidence does not justify high-choice feature paths. | `docs/EIS_FEATURE_POLICY.md` |

## Rule

None of these claims may be marked supported in manuscripts, summaries, release
notes, or future branch plans without a new gated milestone and source-linked
evidence.
