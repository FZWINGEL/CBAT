# Supplement v0.7

This venue-neutral supplement supports `manuscript/manuscript_v0_7.md`. It is
source-linked and claim bounded. It adds no new experiments, models, features,
or claims.

## S1. Dataset and Artifact Policy

The benchmark release is anchored by `benchmark-v0.1-rc2`. Full reruns require
local raw data and generated products described in:

- `docs/BENCHMARK_REPRODUCIBILITY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/COMMAND_DAG.md`
- `reports/synthesis/artifact_manifest_v2.csv`

Large local Parquets remain ignored artifacts. Tracked reports and manifests
carry the reviewable evidence.

## S2. Validation Protocol

Primary evidence uses grouped splits over parameter-set conditions and
stressor-axis holdouts. Random row or cell splits are leakage smoke tests only.
The protocol is documented in `docs/VALIDATION_PROTOCOL.md`.

Key validation themes:

- 76 parameter-set conditions, not 228 independent regimes
- condition-level and stressor-axis holdouts
- split-specific reporting
- leakage guards for future diagnostics and target-derived rates
- parameter-set aggregation for paired comparisons

## S3. Capacity and LOG_AGE Evidence

The capacity baseline ladder, stress-feature diagnostics, target-consistency
checks, and C-rate negative results are summarized by:

- `reports/synthesis/model_ladder_summary.csv`
- `reports/synthesis/split_difficulty_summary.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`
- `reports/synthesis/negative_results.md`

Reviewer caveat: the benchmark treats C-rate as a hard observed stressor view
and does not claim C-rate fade has been resolved.

## S4. PULSE and EIS Gates

PULSE is treated as a scalar diagnostic endpoint. EIS is treated as a gated QA
and scalar diagnostic modality. Reviewers should be pointed to:

- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`
- `reports/coupling/pulse_capacity_robustness/`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/`
- `docs/experiments/2026-05-23_eis_claim_hardening.md`
- `reports/audit/eis_claim_readiness.md`

Reviewer caveat: broad multimodal and broad EIS outcome claims remain blocked.

## S5. Domain and Reliability Gates

Semi-empirical comparators, replicate diagnostics, and interval diagnostics are
documented by:

- `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`
- `reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md`
- `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`
- `reports/analysis/calibration_capacity/calibration_claim_readiness.md`

Reviewer caveat: these gates contextualize C-rate error and interval behavior,
but they do not support global interval-reliability wording.

## S6. Temporal Order, Knee Labels, and Threshold Events

Temporal-order, detector-knee, and threshold-label readiness are documented by:

- `docs/experiments/2026-05-23_temporal_history_value_gate.md`
- `docs/experiments/2026-05-23_knee_label_stability_gate.md`
- `docs/experiments/2026-05-23_knee_threshold_label_forensics.md`

Reviewer caveat: sequence readiness and detector-knee prediction remain
blocked. The 80% threshold label is the stronger candidate threshold-event
target.

Post-rc2 sequence evidence is tracked separately by:

- `docs/experiments/2026-05-28_neural_sequence_architecture_gate.md`
- `reports/baselines/neural_sequence_gate/neural_sequence_claim_readiness.md`

Reviewer caveat: the Milestone 9 CUDA CNN/TCN/CNN-LSTM gate is negative. It
does not justify neural sequence readiness or CBAT prototype readiness.

## S7. Threshold-Event Warning

Threshold-warning diagnostics are documented by:

- `docs/experiments/2026-05-23_threshold_event_warning_baseline.md`
- `docs/experiments/2026-05-23_threshold_warning_hardening.md`
- `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`

Reviewer caveat: the supported statement is diagnostic threshold-event
forecasting. Risk-score calibration, policy use, detector-knee prediction, and
causal warning wording remain unsupported.

## S8. Release and Reproducibility

Release artifacts include:

- `docs/BENCHMARK_V0_1_RC2_SUMMARY.md`
- `docs/RELEASE_NOTES_v0.1-rc2.md`
- `docs/POST_RC2_MAIN_STATUS.md`
- `docs/POST_M9_REVIEW_CHECKLIST.md`
- `reports/synthesis/release_candidate_check.md`
- `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md`
- `reports/synthesis/benchmark_task_registry_check_v2.md`

Reviewer caveat: the rc2 source archive is the reviewer-facing handoff package.
Latest `main` adds post-rc2 maintenance and negative Milestone 9 evidence. It
does not include raw data or generated Parquets.

## S9. Reviewer-Risk Crosswalk

The reviewer-risk register and response prep are part of the submission
preflight package:

- `reports/synthesis/reviewer_risk_register_v2.md`
- `manuscript/reviewer_response_prep_v2.md`

They should be refreshed again only after new evidence or venue-specific
constraints are introduced.
