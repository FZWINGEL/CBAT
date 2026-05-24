# Supplement v0.6

This venue-neutral supplement scaffold supports `manuscript/manuscript_v0_6.md`.
It is intentionally source-linked and claim bounded. It does not add new
experiments, models, features, or claims.

## S1. Dataset and Artifacts

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
stressor-axis holdouts. Random row or cell splits are not paper-facing support.
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

The main-paper interpretation is that C-rate remains the hardest capacity
generalization view and scalar LOG_AGE/stress features are mixed.

## S4. PULSE and EIS Gates

PULSE is treated as a scalar diagnostic endpoint. EIS is treated as a gated QA
and scalar diagnostic modality. The supplement should point reviewers to:

- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`
- `reports/coupling/pulse_capacity_robustness/`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/`
- `docs/experiments/2026-05-23_eis_claim_hardening.md`
- `reports/audit/eis_claim_readiness.md`

The supported interpretation is diagnostic. Broad multimodal claims remain
blocked.

## S5. Domain and Reliability Gates

Semi-empirical comparators, replicate diagnostics, and interval diagnostics
are documented by:

- `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`
- `reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md`
- `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`
- `reports/analysis/calibration_capacity/calibration_claim_readiness.md`

These gates contextualize C-rate error and interval behavior, but they do not
support global interval-reliability wording.

## S6. Temporal Order, Knee Labels, and Threshold Events

Temporal-order, detector-knee, and threshold-label readiness are documented by:

- `docs/experiments/2026-05-23_temporal_history_value_gate.md`
- `docs/experiments/2026-05-23_knee_label_stability_gate.md`
- `docs/experiments/2026-05-23_knee_threshold_label_forensics.md`

The main result is negative for sequence readiness and detector-knee
prediction. The 80% threshold label is the strongest candidate threshold-event
target.

## S7. Threshold-Event Warning

Threshold-warning diagnostics are documented by:

- `docs/experiments/2026-05-23_threshold_event_warning_baseline.md`
- `docs/experiments/2026-05-23_threshold_warning_hardening.md`
- `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`

The supported statement is diagnostic threshold-event forecasting. Risk-score
calibration and policy use remain unsupported.

## S8. Release and Reproducibility

Release artifacts include:

- `docs/BENCHMARK_V0_1_RC2_SUMMARY.md`
- `docs/RELEASE_NOTES_v0.1-rc2.md`
- `reports/synthesis/release_candidate_check.md`
- `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md`

The rc2 source archive is the reviewer-facing handoff package. It does not
include raw data or generated Parquets.
