# Benchmark Task Cards - benchmark-task-freeze-v2-post-m9

Benchmark version: `benchmark-task-freeze-v2-post-m9`

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

## T15_supported_contrast_ordering - supported observed contrast ordering feasibility diagnostic

- Area: policy_support
- Primary claim: C30
- Status: `partially_supported`
- Targets: delta_capacity_Ah_h, capacity_Ah_kh
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: pairwise observed-versus-predicted contrast sign accuracy and contrast-bootstrap gain versus references
- Primary result: HGB K2 primary delta sign accuracy averages 0.780 and C-rate horizon-2/3 rows reach 0.826923/0.888889, but 0/10 primary all-family bootstrap checks beat prior slope with positive p05
- Best reference: prospective HGB K2 multi-horizon predictions
- Allowed wording: existing prospective forecasts can be evaluated for supported observed contrast-ordering diagnostics but the result is partial
- Forbidden wording: policy ranking policy recommendation causal effects same-cell counterfactuals calibrated policy risk or utility CBAT or sequence neural branches are authorized
- Decision: keep as partial diagnostic evidence because the strict prior-slope bootstrap reference gate fails
- Source artifacts: docs/experiments/2026-05-27_policy_ranking_feasibility_gate.md, reports/analysis/policy/policy_ranking_claim_readiness.md

## T16_policy_ranking_failure_forensics - supported contrast-ordering failure forensics

- Area: policy_support
- Primary claim: C31
- Status: `diagnostic_only`
- Targets: delta_capacity_Ah_h, capacity_Ah_kh
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: effect-size-thresholded sign accuracy, rank correlation, top-k regret, and HGB-vs-prior failure bins
- Primary result: 0 of 10 strict HGB-vs-prior all-family checks pass; large-effect passing families are charge_c_rate and temperature; C-rate medium/large pass rows are 1 of 4; HGB ge_0.02Ah mean sign accuracy is 0.856314
- Best reference: HGB K2 versus prior-slope over existing Milestone 7.3 pairwise metrics
- Allowed wording: effect-size and rank-metric forensics explain the partial supported contrast-ordering signal but remain diagnostic-only
- Forbidden wording: policy ranking policy recommendation causal policy effects same-cell counterfactuals calibrated policy risk or utility CBAT or sequence neural branches are authorized
- Decision: keep policy-response modeling blocked unless a future predeclared large-effect supported-contrast gate is explicitly opened and passes
- Source artifacts: docs/experiments/2026-05-27_policy_ranking_failure_forensics.md, reports/analysis/policy/policy_ranking_failure_claim_readiness.md

## T17_support_reliability - support-aware selective reliability diagnostic

- Area: support_reliability
- Primary claim: C32
- Status: `diagnostic_only`
- Targets: delta_capacity_Ah_h, event_within_3_checkups, supported_policy_contrast_sign
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: 50pct retention gain by train-only support score
- Primary result: support distances are generated for existing artifacts but 50pct retention worsens primary capacity MAE by 0.0115957 and threshold-warning Brier by 0.0040389 while policy sign accuracy improves by only 0.0173861; C-rate capacity support reliability is not supported
- Best reference: existing HGB K2 capacity horizon predictions and HGB W2 threshold-warning predictions
- Allowed wording: train-only support distances can audit existing prediction artifacts and selective retention remains diagnostic-only
- Forbidden wording: support filtering validates deployment reliability calibrated risk policy recommendation causal effects same-cell counterfactuals CBAT or architecture readiness
- Decision: keep as an abstention and support audit; do not proceed to policy or deployment claims
- Source artifacts: docs/experiments/2026-05-27_support_aware_selective_reliability_gate.md, reports/analysis/support_reliability/support_reliability_claim_readiness.md

## T18_diagnostic_state_distillation - non-neural diagnostic-state distillation gate

- Area: diagnostic_state
- Primary claim: C33
- Status: `not_supported`
- Targets: capacity_Ah_kh, delta_capacity_Ah_h, event_within_3_checkups, pulse_1s_resistance_k, pulse_10ms_resistance_k, eis_z_abs_1kHz_k, eis_phase_1kHz_k, nyquist_im_peak_abs_k, nyquist_semicircle_width_proxy_k
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: D3 predicted diagnostic-state gain versus D0 capacity-state reference under grouped HGB-50 plus auxiliary MAE gain versus train-mean reference
- Primary result: auxiliary surrogates beat train mean in 12 of 12 rows but D3 worsens primary all-split downstream rows; best all-split capacity primary relative gain is -0.00790693 and all-split threshold-warning Brier relative gain is -0.0620807 while C-rate non-collapse fails
- Best reference: D0 capacity-state reference downstream baseline and train-mean auxiliary reference
- Allowed wording: predicted PULSE/EIS diagnostic-state surrogates are learnable but do not improve downstream capacity-horizon or threshold-warning enough for a multimodal-state claim
- Forbidden wording: capacity plus PULSE plus EIS architecture CBAT broad multimodal learning calibrated risk calibrated uncertainty policy ranking causal effects or same-cell counterfactuals are authorized
- Decision: close broad diagnostic-state distillation as a negative gate and keep PULSE/EIS auxiliary only
- Source artifacts: docs/experiments/2026-05-27_diagnostic_state_distillation_gate.md, reports/baselines/diagnostic_state_distillation/diagnostic_state_distillation_claim_readiness.md

## T19_diagnostic_horizon_forecasting - multi-horizon scalar diagnostic endpoint forecasting gate

- Area: diagnostic_horizon
- Primary claim: C34
- Status: `partially_supported`
- Targets: pulse_1s_resistance, pulse_10ms_resistance, eis_z_abs_1kHz, eis_phase_1kHz, nyquist_im_peak_abs, nyquist_semicircle_width_proxy
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: DH3 HGB mean MAE gain versus persistence and capacity-state references for horizons 2 and 3
- Primary result: diagnostic horizon table QA passed with 80878 rows; DH3 passes 21 of 24 primary 10pct gain rows and 22 of 24 C-rate non-collapse rows; endpoint forensics support eis_z_abs_1kHz, nyquist_semicircle_width_proxy, and pulse_10ms_resistance diagnostics while broad endpoint forecasting remains partial
- Best reference: persistence and DH1 capacity-state HGB references
- Allowed wording: selected future PULSE/EIS scalar endpoints support diagnostic forecasting, while broad endpoint and architecture claims remain unsupported
- Forbidden wording: diagnostic endpoint forecasting is solved globally capacity plus PULSE plus EIS architecture CBAT calibrated risk calibrated uncertainty policy ranking causal effects or same-cell counterfactuals are authorized
- Decision: keep as selected endpoint diagnostic evidence plus partial broad endpoint evidence and do not open architecture or broad multimodal branches
- Source artifacts: docs/experiments/2026-05-27_diagnostic_horizon_forecasting_gate.md, docs/experiments/2026-05-27_diagnostic_horizon_failure_forensics.md, reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_claim_readiness.md, reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_endpoint_claim_readiness.md

## T20_neural_sequence_architecture_gate - pre-CBAT neural sequence architecture gate

- Area: neural_sequence
- Primary claim: C38
- Status: `not_supported`
- Targets: capacity_Ah_k1, delta_capacity_Ah
- Split views: condition_fold, temperature_holdout_fold, c_rate_holdout_fold, profile_holdout_fold, voltage_window_holdout_fold
- Primary metric: grouped true-order neural MAE gain versus shuffled order, aggregate-event HGB, timestamp-stress HGB, and C-rate delta controls
- Primary result: true-order neural candidates do not beat aggregate-event HGB, timestamp-stress HGB, or C-rate controls; C-rate delta has 0/10 positive primary rows and mean gain -0.435394
- Best reference: aggregate-event HGB and timestamp-stress HGB controls
- Allowed wording: CUDA CNN TCN and CNN-LSTM event-sequence diagnostics do not justify neural sequence or CBAT next-gate readiness
- Forbidden wording: sequence models neural models transformers or CBAT prototypes are justified by current evidence
- Decision: keep neural sequence and CBAT readiness blocked; return to synthesis or open only a fresh predeclared diagnostic question
- Source artifacts: docs/experiments/2026-05-28_neural_sequence_architecture_gate.md, reports/baselines/neural_sequence_gate/neural_sequence_claim_readiness.md
