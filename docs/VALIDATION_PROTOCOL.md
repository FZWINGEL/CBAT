# Validation Protocol

Milestone 0.5/0.5b/0.5c/0.6/0.6.1/0.6.2/0.6.3 authorizes only scalar capacity baseline work on
interval features. Milestone 0.5b is review and robustness hardening. Milestone
0.5c is synthesis and stress-feature decision work. Milestone 0.6 adds
capacity-only LOG_AGE-derived scalar stress features. Milestone 0.6.1 hardens
those features with current-sign audit evidence, timestamp-weighted dwell, and
event-segmented scalar summaries. Milestone 0.6.2 audits target consistency and
C-rate failure modes without adding new modalities or model classes. Milestone
0.6.3 permits normalized delta-rate target diagnostics, train-fold residual
bias-correction diagnostics, and narrow cold/current stress feature groups.
These milestones are not modality or architecture expansions.

Milestone 0.7 opens PULSE as a separate QA-first resistance endpoint. It
authorizes PULSE QA, canonical PULSE target extraction, PULSE interval target
tables, and scalar grouped PULSE resistance baselines. It does not authorize
EIS modeling, capacity+PULSE multimodal claims, sequence models, neural models,
policy ranking, or CBAT.

Required split discipline:

- Primary evidence uses condition-level grouped splits.
- Replicates from the same parameter-set condition remain together for headline
  claims.
- Random row/cell splits are leakage smoke tests only and are not part of the
  Milestone 0.5 baseline report.
- LOG_AGE inserted diagnostics must remain masked for interval prediction.
- Baseline code must consume `interval_subset_registry_v1.parquet`.
- The primary capacity run uses `baseline_clean_tolerant`.
- Every baseline report must include a sensitivity run excluding
  `sensitivity_flagged_monotonicity == true`.

Allowed Milestone 0.5 targets:

- `capacity_Ah_k1`
- `delta_capacity_Ah`

Allowed Milestone 0.5 feature groups:

- `F0_time_only`
- `F1_state_time`
- `F2_state_exposure`
- `F3_state_nominal`
- `F4_state_log_age_scalar`

Allowed Milestone 0.6 stress-feature groups:

- `F5_log_age_histograms`
- `F6_coupled_stress`
- `F7_c_rate_focused`

Allowed Milestone 0.6.1 stress-feature groups:

- `F8_timestamp_weighted_stress`
- `F9_event_segmented_stress`
- `F10_c_rate_v1_1`

Allowed Milestone 0.6.3 narrow C-rate feature groups:

- `F11_minimal_cold_current`
- `F12_voltage_cold_current_interactions`
- `F13_sparse_c_rate_context`

`F0_time_only` is intentionally weak. Non-persistence learned baselines must
include prior check-up state through `capacity_Ah_k` in at least one state-aware
feature group.

Allowed Milestone 0.5 split views:

- `condition_fold`
- `temperature_holdout_fold`
- `c_rate_holdout_fold`
- `profile_holdout_fold`
- `voltage_window_holdout_fold`

Required Milestone 0.5 report artifacts:

- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`

Required Milestone 0.5b diagnostic artifacts:

- `baseline_diagnostics.md`
- `c_rate_holdout_error_analysis.md`
- `claim_readiness.md`
- `plots/feature_gain_by_split.csv`
- `plots/best_by_target_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/c_rate_grouped_summaries.csv`

Milestone 0.5b linear baselines use train-fold numeric standardization for
`L1_ridge`. The standardization statistics must be fit on train rows only.

Milestone 0.5b quantile diagnostics for `L3_quantile_hist_gradient_boosting`
include:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Milestone 0.5c diagnostics for focused reports should compare against an L0
reference report when the focused report does not include persistence rows.
Missing references must be rendered explicitly as `reference_missing`; silent
`NA` values are not acceptable for L0 comparison fields.

Milestone 0.5c claim-readiness summaries are allowed to recommend the next
feature-engineering direction, but they do not authorize new modalities or
advanced models.

Milestone 0.6 stress-feature data products must remain modular sidecars keyed by
`cell_id`, `checkup_k`, and `checkup_k_next`. The baseline runner may join them
through `--stress-features`; the core interval table should remain stable.

Target-derived stress diagnostics such as `delta_capacity_per_day`,
`delta_capacity_per_efc`, and `delta_capacity_per_Ah_throughput` must not enter
predictive feature groups because they encode the capacity target.

Required Milestone 0.6 stress-feature artifacts:

- `data/interim/interval_stress_features_v1.parquet` (ignored generated data)
- `reports/audit/stress_feature_qa_report.json`
- `reports/baselines/capacity_stress_features_hgb50_report.json`
- `reports/baselines/capacity_stress_features_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_gain_by_split.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/c_rate_stress_feature_errors.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_claim_readiness.csv`

Milestone 0.6 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.125186`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`.

Required Milestone 0.6.1 hardening artifacts:

- `reports/audit/current_sign_audit_report.json`
- `data/interim/interval_stress_features_v1_1.parquet` (ignored generated data)
- `reports/audit/stress_feature_v1_1_qa_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Milestone 0.6.1 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.124656`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`;
- do not promote sign-dependent charge features unless current-sign evidence is
  high confidence.

Required Milestone 0.6.2 diagnostic artifacts:

- `target_consistency_diagnostics.md`
- `c_rate_residual_analysis.md`
- `stress_feature_ablation_summary.md`
- `plots/derived_delta_from_capacity_metrics.csv`
- `plots/derived_capacity_from_delta_metrics.csv`
- `plots/direct_vs_derived_target_metrics.csv`
- `plots/c_rate_residuals_by_parameter_set.csv`
- `plots/c_rate_residuals_by_temperature.csv`
- `plots/c_rate_residuals_by_voltage_window.csv`
- `plots/c_rate_residuals_by_capacity_bin.csv`
- `plots/c_rate_residuals_by_interval_count.csv`
- `plots/c_rate_signed_error_summary.csv`
- `plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`
- `plots/c_rate_gain_by_feature_group.csv`

Milestone 0.6.2 must not retrain by default. It should use existing row-level
prediction Parquet files and JSON reports to decide whether direct delta,
derived delta from capacity, or both target paths should be reported.

Required Milestone 0.6.3 diagnostic artifacts:

- `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
- `reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_c_rate_bias_corrected_report.json`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/c_rate_bias_before_after.csv`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`

Milestone 0.6.3 may train on normalized target modes
`delta_capacity_per_day_target` and `delta_capacity_per_efc_target`, but the
report metrics must evaluate predictions back in `delta_capacity_Ah` units. The
true target-derived rates must never enter predictive input feature groups.
Residual correction must be fit inside each train fold only; test-fold
residuals must not be used for correction.

Required Milestone 0.7 PULSE artifacts:

- `docs/PULSE_TARGET_POLICY.md`
- `reports/audit/pulse_qa_report.json`
- `reports/audit/pulse_alignment_report.json`
- `reports/audit/pulse_target_coverage.csv`
- `data/interim/pulse_target_table.parquet` (ignored generated data)
- `reports/baselines/pulse_resistance_l0_l3_report.json`
- `reports/baselines/pulse_resistance_l0_l3/leaderboard.csv`
- `reports/baselines/pulse_resistance_l0_l3/baseline_summary.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md`

Allowed Milestone 0.7 PULSE targets:

- `delta_pulse_1s_resistance`
- `pulse_1s_resistance_k1`
- `delta_pulse_10ms_resistance`
- `pulse_10ms_resistance_k1`

Allowed Milestone 0.7 PULSE feature groups:

- `P0_persistence`
- `P1_state_time`
- `P2_state_capacity`
- `P3_state_nominal`
- `P4_state_log_age_scalar`
- `P5_stress_v1_1`

Milestone 0.7 reports must use grouped split views and report target coverage.
PULSE results are resistance-baseline diagnostics only; they are not evidence
for a capacity+PULSE multimodal claim.

Blocked until later milestones:

- EIS and PULSE scientific claims.
- Sequence models, neural models, policy ranking, and CBAT architecture.
