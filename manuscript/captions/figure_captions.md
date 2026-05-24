# Figure Captions

## Figure 1. Data product architecture

Claim IDs: C12. Source artifact: `docs/PAPER_FIGURE_PLAN.md`. Allowed interpretation: the benchmark is built from linked audited data products. Limitation: the figure is schematic and not a coverage metric.

## Figure 2. Grouped validation design

Claim IDs: C12. Source artifact: `docs/VALIDATION_PROTOCOL.md`. Allowed interpretation: paper-facing claims use grouped validation. Limitation: grouped splits reduce the number of independent held-out conditions.

## Figure 3. Capacity baseline ladder

Claim IDs: C01, C03. Source artifact: `reports/synthesis/model_ladder_summary.csv`. Allowed interpretation: C-rate remains difficult for capacity targets. Limitation: descriptive best rows do not override paired claim-readiness tests.

## Figure 4. C-rate failure analysis

Claim IDs: C03. Source artifact: `reports/synthesis/split_difficulty_summary.csv`. Allowed interpretation: C-rate is the dominant unresolved capacity generalization stressor. Limitation: split-level summaries aggregate condition-specific failures.

## Figure 5. Stress-feature decision

Claim IDs: C02. Source artifact: `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv`. Allowed interpretation: stress features are mixed and do not solve C-rate fade transfer. Limitation: only scalar LOG_AGE stress groups are represented.
What not to infer: this figure does not show that stress features solve C-rate fade prediction.

## Figure 6. PULSE QA coverage

Claim IDs: C04. Source artifact: `reports/audit/pulse_qa_report.json`. Allowed interpretation: canonical RT/50 PULSE coverage is sufficient for scalar diagnostics. Limitation: missing canonical endpoints still require reporting.

## Figure 7. PULSE resistance baseline

Claim IDs: C04. Source artifact: `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`. Allowed interpretation: RT/50 PULSE is usable as a scalar resistance endpoint. Limitation: this is not a broad multimodal claim.

## Figure 8. Capacity-PULSE coupling

Claim IDs: C05. Source artifact: `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv`. Allowed interpretation: PULSE growth is associated with capacity residual magnitude. Limitation: the association is diagnostic, not causal.
What not to infer: this figure does not establish causality or independence from all confounding.

## Figure 9. Prior PULSE versus strongest non-PULSE

Claim IDs: C06, C07, C08. Source artifact: `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv`. Allowed interpretation: prior PULSE does not beat the strongest supplied non-PULSE baseline. Limitation: the result is limited to prior PULSE state at check-up k.
What not to infer: this figure does not support a claim that prior PULSE beats the strongest supplied non-PULSE baseline.

## Figure 10. Claim ladder

Claim IDs: C01-C12. Source artifact: `reports/synthesis/claim_matrix.csv`. Allowed interpretation: the paper separates supported, partial, negative, gated, and blocked claims. Limitation: the ladder summarizes evidence rather than replacing detailed reports.

## Figure 11. EIS scalar diagnostic gate

Claim IDs: C10. Source artifact: `docs/experiments/2026-05-23_eis_claim_hardening.md`. Allowed interpretation: EIS is QA-ready and useful as a scalar diagnostic endpoint with narrow profile-split prior-feature signal. Limitation: this does not authorize broad EIS predictive claims.

## Figure 12. Replicate and interval-calibration gate

Claim IDs: C09, C14, C15. Source artifact: `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`. Allowed interpretation: replicate spread and grouped conformal diagnostics contextualize uncertainty, while C-rate coverage remains insufficient for a global interval claim. Limitation: this figure does not authorize calibrated interval wording.

## Figure 13. Temporal-order and knee-label gates

Claim IDs: C16, C17, C18. Source artifact: `docs/experiments/2026-05-23_temporal_history_value_gate.md`; `docs/experiments/2026-05-23_knee_threshold_label_forensics.md`. Allowed interpretation: event-order summaries and detector-knee labels do not justify sequence or knee-prediction branches, while 80% threshold labels are the more stable candidate label family. Limitation: threshold labels alone do not authorize warning claims.

## Figure 14. Threshold-warning and release gate

Claim IDs: C19. Source artifact: `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`; `reports/synthesis/release_candidate_check.md`. Allowed interpretation: non-neural baselines forecast the 80% threshold event diagnostically beyond proximity and under verified-only sensitivity, and the benchmark release checker passes. Limitation: this does not authorize risk calibration, policy ranking, or causal warning.
