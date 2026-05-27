# Benchmark Task Cards v1

Benchmark version: `benchmark-task-freeze-v1`

These cards freeze the benchmark task definitions and current claim posture. They do not add new model results.

## T01_capacity_next_checkup - next-check-up capacity generalization

- Area: capacity
- Primary claim: C03
- Status: `supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: grouped MAE under held-out condition and stressor splits
- Primary result: C-rate is the hardest capacity view with MAE 0.125186 for capacity_Ah_k1 and 0.101133 for delta_capacity_Ah
- Best reference: grouped HGB F4/F8 capacity baseline family
- Allowed wording: C-rate is the dominant unresolved capacity generalization stressor under grouped validation
- Forbidden wording: Random row splits are publishable evidence or stress features solve C-rate fade
- Decision: keep as core capacity benchmark task with C-rate difficulty highlighted
- Source artifacts: docs/experiments/2026-05-22_capacity_baseline_synthesis.md

## T02_pulse_scalar_endpoint - PULSE RT/50 scalar diagnostic endpoint

- Area: PULSE
- Primary claim: C04
- Status: `supported_for_diagnostics`
- Targets: pulse_1s_resistance_RT50, delta_pulse_1s_resistance
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: grouped resistance MAE and capacity residual coupling diagnostics
- Primary result: RT/50 PULSE is a usable scalar endpoint; prior PULSE value is narrow and selected-split only
- Best reference: scalar PULSE and prior-PULSE non-neural baselines
- Allowed wording: RT/50 PULSE supports scalar diagnostic endpoint and explanatory residual diagnostics
- Forbidden wording: PULSE validates broad multimodal modeling or improves all capacity targets
- Decision: keep PULSE as diagnostic and narrow prior-state evidence only
- Source artifacts: docs/experiments/2026-05-23_pulse_target_robustness_decision.md, docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md

## T03_eis_scalar_endpoint - gated EIS scalar diagnostic endpoint

- Area: EIS
- Primary claim: C10
- Status: `partially_supported`
- Targets: eis_RT50_scalar_targets
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: grouped scalar EIS target metrics and non-EIS improvement checks
- Primary result: EIS is a scalar diagnostic endpoint with narrow profile-split signal; broad non-EIS improvement is unsupported
- Best reference: EIS scalar L0-L3 diagnostics
- Allowed wording: EIS is a gated scalar diagnostic endpoint with narrow signals
- Forbidden wording: EIS broadly improves degradation prediction or authorizes learned embeddings
- Decision: keep EIS gated and auxiliary
- Source artifacts: docs/experiments/2026-05-23_eis_claim_hardening.md, reports/baselines/eis_scalar_l0_l3_report.json

## T04_threshold_warning - 80pct threshold-event forecasting diagnostic

- Area: threshold_warning
- Primary claim: C19
- Status: `supported_for_diagnostics`
- Targets: event_within_1_checkup, event_within_2_checkups, event_within_3_checkups
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: verified-only Brier, AUROC, AUPRC against event-rate and proximity references
- Primary result: verified-only 3-checkup Brier improves from prior 0.178655 and proximity 0.168492 to HGB W2 0.090116
- Best reference: HGB W2 threshold-warning classifier
- Allowed wording: non-neural baselines forecast 80pct threshold events diagnostically beyond proximity under verified-only sensitivity
- Forbidden wording: calibrated risk, causal early warning, detector-knee prediction, or policy ranking
- Decision: lock as diagnostic threshold-event forecasting task
- Source artifacts: docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md, reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md

## T05_threshold_warning_calibration - threshold-warning probability calibration

- Area: calibration
- Primary claim: C20
- Status: `not_supported`
- Targets: event_within_3_checkups
- Split views: condition_fold, c_rate_holdout_fold
- Primary metric: fixed-width and equal-frequency ECE under all-row and verified-only policies
- Primary result: primary verified-only Platt ECE passes mean threshold but C-rate verified-only ECE remains 0.167653 fixed and 0.176185 equal-frequency
- Best reference: Platt and isotonic post-hoc calibration diagnostics
- Allowed wording: post-hoc calibration improves mean reliability but C-rate ECE keeps calibrated-risk blocked
- Forbidden wording: threshold-warning probabilities are calibrated risk estimates
- Decision: keep as calibration negative result
- Source artifacts: docs/experiments/2026-05-24_calibration_robustness_correctness_hardening.md, reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md

## T06_capacity_uncertainty_calibration - grouped capacity uncertainty calibration

- Area: uncertainty
- Primary claim: C15
- Status: `not_supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, c_rate_holdout_fold, stressor_family_holdout
- Primary metric: empirical interval coverage versus nominal target
- Primary result: grouped conformal improves mean coverage but C-rate coverage remains below nominal target
- Best reference: raw HGB quantile and grouped conformal diagnostics
- Allowed wording: calibrated capacity uncertainty remains blocked by C-rate coverage failure
- Forbidden wording: conformal validates global uncertainty or HGB quantiles are calibrated
- Decision: keep uncertainty as blocked benchmark diagnostic
- Source artifacts: docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md, reports/analysis/calibration_capacity/calibration_claim_readiness.md

## T07_temporal_order_falsification - temporal order value falsification

- Area: temporal_order
- Primary claim: C16
- Status: `not_supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: order-aware versus aggregate and shuffled-order MAE gains
- Primary result: order-aware mean gain is negative versus aggregate and shuffled controls
- Best reference: aggregate event and shuffled-order controls
- Allowed wording: ordered event structure does not justify sequence models
- Forbidden wording: sequence models are justified by current temporal-order evidence
- Decision: keep as falsification gate and block sequence models
- Source artifacts: docs/experiments/2026-05-23_temporal_history_value_gate.md, reports/baselines/capacity_sequence_value_hgb50/sequence_value_claim_readiness.md

## T08_stressor_robust_delta_capacity - adaptive stressor-robust C-rate delta diagnostic

- Area: stressor_robustness
- Primary claim: C22
- Status: `supported_for_diagnostics`
- Targets: delta_capacity_Ah
- Split views: c_rate_holdout_fold
- Primary metric: C-rate delta MAE gain with outside-C-rate non-degradation guardrail
- Primary result: conservative adaptive R2 selection replicates with min C-rate gain 0.0200436 versus F4 and max outside-C-rate degradation 0.0279117
- Best reference: conservative train-only adaptive stressor-balanced HGB
- Allowed wording: conservative train-only adaptive R2 selection supports a narrow diagnostic C-rate delta robustness result
- Forbidden wording: C-rate fade is solved globally or architecture work is justified
- Decision: lock narrow diagnostic only
- Source artifacts: docs/experiments/2026-05-24_adaptive_stressor_robust_replication.md, reports/baselines/capacity_stressor_robust_adaptive_replication/adaptive_replication_claim_readiness.md

## T09_hierarchical_replicate_comparator - hierarchical replicate-aware capacity comparator

- Area: hierarchical_replicate
- Primary claim: C25
- Status: `diagnostic_only`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, c_rate_holdout_fold
- Primary metric: C-rate MAE gain and replicate-variance interval coverage
- Primary result: H4/F4 C-rate delta gain is 0.000100645 with negative paired p05 and H5 intervals are undercovered
- Best reference: H4 residual partial-pooling comparator and H5 replicate interval diagnostic
- Allowed wording: hierarchical partial pooling is an L5 diagnostic comparator only
- Forbidden wording: hierarchical partial pooling solves C-rate fade or validates calibrated uncertainty
- Decision: retain as charter-required comparator and negative uncertainty evidence
- Source artifacts: docs/experiments/2026-05-27_hierarchical_replicate_baseline_gate.md, reports/baselines/capacity_hierarchical_replicate/hierarchical_claim_readiness.md

## T10_multi_horizon_capacity - multi-horizon capacity forecasting diagnostic

- Area: multi_horizon_capacity
- Primary claim: C26
- Status: `partially_supported`
- Targets: capacity_Ah_kh, delta_capacity_Ah_h
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: grouped horizon MAE versus persistence and prior-slope references
- Primary result: C-rate horizons 2 and 3 pass for capacity and delta; all-split horizon-3 capacity narrowly misses prior slope
- Best reference: prospective HGB K2 nominal-condition model
- Allowed wording: prospective HGB K2 supports scoped C-rate and delta-capacity multi-horizon diagnostics
- Forbidden wording: multi-horizon capacity forecasting is solved globally or K3 future exposure is prospective
- Decision: keep broad task partially supported only
- Source artifacts: docs/experiments/2026-05-27_multi_horizon_capacity_forecasting_gate.md, reports/baselines/capacity_horizon_l0_l2/multi_horizon_next_branch_readiness.md

## T11_prior_trajectory_shape - prior-trajectory shape horizon diagnostic

- Area: multi_horizon_capacity
- Primary claim: C27
- Status: `partially_supported`
- Targets: capacity_Ah_kh, delta_capacity_Ah_h
- Split views: condition_fold, c_rate_holdout_fold
- Primary metric: K4/K5 MAE gain versus K2, persistence, and prior-slope references
- Primary result: K5 does not repair all-split horizon-3 capacity and improves only 2 of 4 C-rate horizon-2/3 primary rows
- Best reference: K5 nominal-plus-prior-trajectory HGB diagnostic
- Allowed wording: prior-only trajectory shape is leakage-safe with isolated diagnostic gains but does not pass the repair gate
- Forbidden wording: prior-trajectory shape solves multi-horizon forecasting or justifies sequence/neural/CBAT/policy/causal claims
- Decision: close this branch as partial diagnostic evidence
- Source artifacts: docs/experiments/2026-05-27_prior_trajectory_shape_horizon_gate.md, reports/baselines/capacity_horizon_trajectory_l0_l2/trajectory_shape_claim_readiness.md

## T12_semi_empirical_replicate_checks - semi-empirical comparator and replicate uncertainty checks

- Area: domain_comparators
- Primary claim: C13
- Status: `not_supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, c_rate_holdout_fold, profile_holdout_fold
- Primary metric: MAE gain versus HGB references and replicate spread diagnostics
- Primary result: semi-empirical comparators are useful domain checks but weaker than strongest HGB/stress baselines in C-rate views
- Best reference: semi-empirical ridge-style stress comparator and replicate spread diagnostics
- Allowed wording: semi-empirical comparators and replicate spread are diagnostic checks only
- Forbidden wording: semi-empirical models beat strongest HGB baselines or replicate diagnostics validate calibrated uncertainty
- Decision: keep as domain and uncertainty context, not as positive comparator claim
- Source artifacts: docs/experiments/2026-05-23_semi_empirical_replicate_gate.md, reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md

## T13_minimal_sequence_reopening - minimal fixed-length event-sequence reopening gate

- Area: temporal_order
- Primary claim: C28
- Status: `not_supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: true-sequence condition-mean MAE gain versus shuffled aggregate-event HGB and timestamp-stress HGB controls
- Primary result: CUDA Torch MLP rows run but true-sequence candidates have mean gain -0.227321 versus aggregate-event HGB and -0.190925 versus timestamp-stress HGB with C-rate delta gain -0.159493
- Best reference: aggregate-event HGB and timestamp-weighted stress HGB controls
- Allowed wording: fixed-length event-sequence and CUDA Torch MLP diagnostics do not reopen sequence or neural modeling
- Forbidden wording: sequence models neural models CBAT transformers or policy ranking are justified by current sequence evidence
- Decision: keep sequence and neural branches blocked after the GPU-backed H7 reopening check
- Source artifacts: docs/experiments/2026-05-27_minimal_sequence_reopening_gate.md, reports/baselines/minimal_sequence_reopening/sequence_reopening_claim_readiness.md

## T14_policy_contrast_support - observed policy-contrast support diagnostic

- Area: policy_support
- Primary claim: C29
- Status: `supported_for_diagnostics`
- Targets: capacity_loss_Ah
- Split views: charge_c_rate, temperature, voltage_window, profile
- Primary metric: triplet-supported matched contrasts and observed capacity-loss sign-stable fraction
- Primary result: 234 triplet-supported contrasts across four families with 2943 of 3213 observed capacity-loss rows sign-stable
- Best reference: observed matched contrast registry
- Allowed wording: observed matched policy contrasts support diagnostic degradation-order analysis
- Forbidden wording: policy ranking policy recommendation causal effects same-cell counterfactuals CBAT or calibrated risk are authorized
- Decision: keep as observed support/stability diagnostic; separate predeclared gate required before any ranking baseline
- Source artifacts: docs/experiments/2026-05-27_policy_contrast_support_gate.md, reports/analysis/policy/policy_claim_readiness.md
