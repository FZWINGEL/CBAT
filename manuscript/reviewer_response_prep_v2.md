# Reviewer Response Prep v2

This file converts `reports/synthesis/reviewer_risk_register_v2.md` into
source-linked response strategies for the v0.7 manuscript package.

## Grouped Splits Versus Random Splits

Likely criticism: Random split scores are missing or de-emphasized.

Response strategy: The experimental unit for generalization is the
parameter-set condition. The cohort has 228 cells but only 76 condition
triplets. Random row or cell splits can share operating-condition structure
across train and test, so they are not headline evidence.

Artifact to cite: `docs/VALIDATION_PROTOCOL.md`.

## C-Rate Generalization

Likely criticism: C-rate evidence uses limited held-out condition counts.

Response strategy: Agree and keep the claim narrow. The manuscript treats
C-rate as the hardest observed stressor-axis view and an unresolved fade-rate
setting, not as a solved regime.

Artifact to cite: `reports/synthesis/main_project_gate_status.md`.

## LOG_AGE Leakage Risk

Likely criticism: LOG_AGE contains inserted diagnostics or future information.

Response strategy: Explain the feature policy: inserted diagnostics are masked,
target-derived rates are not predictive inputs, and prospective warning
features use check-up-k state/time/nominal metadata only.

Artifact to cite: `docs/VALIDATION_PROTOCOL.md`.

## PULSE Claims

Likely criticism: PULSE alignment, direction handling, or strongest-baseline
comparisons undermine PULSE conclusions.

Response strategy: Keep PULSE as a scalar diagnostic endpoint. Prior PULSE can
beat F4 in selected capacity-level views, but it does not beat the strongest
non-PULSE baselines and does not support a fade-rate claim.

Artifacts to cite:
`docs/experiments/2026-05-23_pulse_target_robustness_decision.md`;
`reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`.

## EIS Scope

Likely criticism: EIS appears in the benchmark title but does not support broad
outcome improvement.

Response strategy: State that EIS passed QA and scalar endpoint gates, but
hardening found only narrow profile-split prior-feature signal. EIS is
diagnostic in the current claim ledger.

Artifact to cite: `docs/experiments/2026-05-23_eis_claim_hardening.md`.

## Semi-Empirical Comparators

Likely criticism: Semi-empirical baselines may be too simple.

Response strategy: Frame them as interpretable stress comparators required by
the charter, not as electrochemical mechanism identification. Their role is to
challenge flexible ML baselines before architecture work.

Artifact to cite: `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`.

## Replicate and Interval Diagnostics

Likely criticism: Uncertainty claims are weak.

Response strategy: Agree. The manuscript uses replicate spread and grouped
interval diagnostics to contextualize error, while global interval reliability
remains unsupported because C-rate coverage fails.

Artifacts to cite:
`reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md`;
`docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`.

## Temporal Order and Sequence Models

Likely criticism: Why not use sequence models after building run events?

Response strategy: The charter requires temporal-order value before sequence
models. Ordered event features did not beat aggregate or shuffled controls, so
sequence models remain blocked.

Artifact to cite: `docs/experiments/2026-05-23_temporal_history_value_gate.md`.

## Knee Labels and Threshold Events

Likely criticism: Knee prediction is attractive and should be modeled.

Response strategy: Detector-knee labels fail replicate consistency. The
threshold-event alternative is more stable, and only the 80% threshold warning
diagnostic baseline is supported.

Artifacts to cite:
`docs/experiments/2026-05-23_knee_label_stability_gate.md`;
`docs/experiments/2026-05-23_knee_threshold_label_forensics.md`.

## Threshold-Warning Wording

Likely criticism: The threshold-warning result sounds like risk prediction or
policy guidance.

Response strategy: The claim is diagnostic threshold-event forecasting. It
survives proximity and verified-only censoring sensitivity, but risk-score
calibration, policy ranking, and causal warning wording remain blocked.

Artifact to cite: `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`.

## Release Reproducibility

Likely criticism: Raw data and generated Parquets are absent from the release.

Response strategy: The release is a source/report/checker package. Raw data and
generated products remain local ignored artifacts because of size and
provenance. The runbook, command DAG, artifact manifest, and release checker
define reproducibility.

Artifacts to cite:
`docs/BENCHMARK_RUNBOOK.md`;
`reports/synthesis/artifact_manifest_v2.csv`;
`reports/synthesis/release_candidate_check.md`.
