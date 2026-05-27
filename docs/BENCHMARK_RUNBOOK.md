# Benchmark Runbook

This runbook records the current end-to-end benchmark command order. It is a
release-candidate guide, not authorization for new scientific work. Generated
Parquet outputs are local ignored artifacts unless explicitly documented
otherwise.

## 0. Audit

```bash
mbp audit manifest --data-root data/raw --out reports/audit/DATASET_MANIFEST.json
mbp audit result-data --data-root data/raw --out reports/audit/result_data_audit.json
mbp audit split-registry --out reports/audit/split_registry_report.json
```

Inputs: local raw archives and metadata.

Outputs: tracked audit JSON/CSV/Markdown reports.

## 1. Ingestion

```bash
mbp ingest eoc --out data/interim/modality_table_eoc.parquet
mbp ingest pulse --out data/interim/modality_table_pulse.parquet
mbp ingest eis --out data/interim/modality_table_eis.parquet --quality-out data/interim/eis_spectrum_quality.parquet
mbp ingest log-age --out data/interim/modality_table_log_age.parquet
```

Inputs: raw BagIt/result-data archives.

Outputs: ignored interim Parquets. The LOG_AGE table has 904,977,105 rows in
the current local run.

## 2. Intervals and Splits

```bash
mbp intervals build --out data/interim/interval_table.parquet
mbp split interval-subsets --interval-table data/interim/interval_table.parquet --out data/splits/interval_subset_registry_v1.parquet --report reports/audit/interval_subset_report.json
```

Inputs: ingested modality tables.

Outputs: ignored interval/split Parquets and tracked audit reports. The current
interval table has 3,827 rows.

## 3. Stress, Run-Event, and Sequence Products

```bash
mbp features build-stress --interval-table data/interim/interval_table.parquet --out data/interim/interval_stress_features_v1_1.parquet --qa-out reports/audit/stress_features_v1_1_qa_report.json
mbp features build-run-events --log-age data/interim/modality_table_log_age.parquet --interval-table data/interim/interval_table.parquet --out data/interim/run_event_table_v1.parquet
mbp features run-events-qa --run-events data/interim/run_event_table_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/run_event_qa_report.json --coverage-out reports/audit/run_event_coverage.csv
mbp features build-sequence-features --run-events data/interim/run_event_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/interval_sequence_features_v1.parquet
mbp features sequence-qa --sequence-features data/interim/interval_sequence_features_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/sequence_feature_qa_report.json
mbp features build-event-sequences --run-events data/interim/run_event_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/interval_event_sequence_table_v1.parquet --max-events 64 --seed 42
mbp features event-sequences-qa --event-sequences data/interim/interval_event_sequence_table_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/interval_event_sequence_qa_report.json
```

Outputs: ignored feature Parquets and tracked QA reports. The current run-event
table has 79,328,229 rows, the aggregate/order sequence sidecar has 3,827
rows, and the fixed-length event-sequence sidecar has 3,827 rows.

## 4. PULSE Products

```bash
mbp pulse qa --pulse-table data/interim/modality_table_pulse.parquet --out reports/audit/pulse_qa_report.json
mbp pulse build-targets --pulse-table data/interim/modality_table_pulse.parquet --interval-table data/interim/interval_table.parquet --out data/interim/pulse_target_table.parquet
```

Outputs: ignored target Parquet and tracked QA reports.

## 5. EIS Products

```bash
mbp eis qa --eis-table data/interim/modality_table_eis.parquet --eis-quality data/interim/eis_spectrum_quality.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/eis_qa_report.json --coverage-out reports/audit/eis_coverage_report.csv --alignment-out reports/audit/eis_alignment_report.json --frequency-out reports/audit/eis_valid_frequency_report.csv
mbp eis alignment-sensitivity --eis-quality data/interim/eis_spectrum_quality.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/eis_alignment_sensitivity_report.json --coverage-out reports/audit/eis_alignment_sensitivity_coverage.csv
mbp eis build-features --eis-table data/interim/modality_table_eis.parquet --eis-quality data/interim/eis_spectrum_quality.parquet --interval-table data/interim/interval_table.parquet --out data/interim/eis_feature_table_v1.parquet --soc-percent 50 --temperature-context RT
mbp eis feature-qa --eis-features data/interim/eis_feature_table_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/eis_feature_qa_report.json
mbp eis build-targets --eis-features data/interim/eis_feature_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/eis_target_table_v1.parquet --soc-percent 50 --temperature-context RT
mbp eis target-qa --eis-targets data/interim/eis_target_table_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/audit/eis_target_qa_report.json --coverage-out reports/audit/eis_target_coverage.csv
```

Outputs: ignored EIS Parquets and tracked QA reports. Current RT/50 EIS feature
rows: 3,983. Current EIS target rows: 3,827.

## 6. Capacity, PULSE, EIS, and Domain Baselines

```bash
mbp baseline run-capacity --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --out reports/baselines/capacity_l0_l3_report.json --predictions-out data/processed/capacity_l0_l3_predictions.parquet
mbp baseline run-pulse --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --pulse-targets data/interim/pulse_target_table.parquet --out reports/baselines/pulse_resistance_l0_l3_report.json --predictions-out data/processed/pulse_resistance_l0_l3_predictions.parquet
mbp baseline run-eis --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --eis-targets data/interim/eis_target_table_v1.parquet --out reports/baselines/eis_scalar_l0_l3_report.json --predictions-out data/processed/eis_scalar_l0_l3_predictions.parquet
mbp baseline run-semi-empirical --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/semi_empirical_capacity_report.json --predictions-out data/processed/semi_empirical_capacity_predictions.parquet
mbp baseline run-stressor-robust-capacity --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/capacity_stressor_robust_hgb50_report.json --predictions-out data/processed/capacity_stressor_robust_hgb50_predictions.parquet
mbp baseline run-stressor-robust-pareto --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/capacity_stressor_robust_pareto_report.json --predictions-out data/processed/capacity_stressor_robust_pareto_predictions.parquet --out-dir reports/baselines/capacity_stressor_robust_pareto
mbp baseline run-stressor-robust-adaptive --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/capacity_stressor_robust_adaptive_conservative_report.json --predictions-out data/processed/capacity_stressor_robust_adaptive_conservative_predictions.parquet --out-dir reports/baselines/capacity_stressor_robust_adaptive_conservative --selection-policy conservative_guarded
mbp baseline replicate-stressor-robust-adaptive --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out-dir reports/baselines/capacity_stressor_robust_adaptive_replication
mbp baseline run-stressor-robust-attribution --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/capacity_stressor_robust_attribution_report.json --predictions-out data/processed/capacity_stressor_robust_attribution_predictions.parquet --out-dir reports/baselines/capacity_stressor_robust_attribution
mbp baseline run-stressor-robust-arm-selector --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --attribution-report reports/baselines/capacity_stressor_robust_attribution_report.json --attribution-predictions data/processed/capacity_stressor_robust_attribution_predictions.parquet --out reports/baselines/capacity_stressor_robust_arm_selector_report.json --predictions-out data/processed/capacity_stressor_robust_arm_selector_predictions.parquet --out-dir reports/baselines/capacity_stressor_robust_arm_selector
mbp baseline run-hierarchical-capacity --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --stress-features data/interim/interval_stress_features_v1_1.parquet --out reports/baselines/capacity_hierarchical_replicate_report.json --predictions-out data/processed/capacity_hierarchical_replicate_predictions.parquet --out-dir reports/baselines/capacity_hierarchical_replicate --targets capacity_Ah_k1,delta_capacity_Ah --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold --hgb-max-iter 50
mbp baseline run-minimal-sequence-reopening --interval-table data/interim/interval_table.parquet --interval-subsets data/splits/interval_subset_registry_v1.parquet --event-sequences data/interim/interval_event_sequence_table_v1.parquet --out reports/baselines/minimal_sequence_reopening_report.json --predictions-out data/processed/minimal_sequence_reopening_predictions.parquet --out-dir reports/baselines/minimal_sequence_reopening --reference-sequence-report reports/baselines/capacity_sequence_value_hgb50_report.json --reference-stress-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json --model-levels S0_ridge_true_sequence,S1_ridge_shuffled_sequence,S2_torch_mlp_true_sequence,S3_torch_mlp_shuffled_sequence --targets capacity_Ah_k1,delta_capacity_Ah --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold --mlp-max-iter 200
mbp analysis build-capacity-horizon-table --interval-table data/interim/interval_table.parquet --out data/interim/capacity_horizon_table_v1.parquet --horizons 1,2,3,5
mbp analysis capacity-horizon-qa --horizon-table data/interim/capacity_horizon_table_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/analysis/capacity_horizon/capacity_horizon_qa_report.json --coverage-out reports/analysis/capacity_horizon/capacity_horizon_coverage.csv
mbp analysis build-capacity-horizon-trajectory-features --horizon-table data/interim/capacity_horizon_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/capacity_horizon_trajectory_features_v1.parquet
mbp analysis capacity-horizon-trajectory-qa --trajectory-features data/interim/capacity_horizon_trajectory_features_v1.parquet --horizon-table data/interim/capacity_horizon_table_v1.parquet --out reports/analysis/capacity_horizon/capacity_horizon_trajectory_qa_report.json --coverage-out reports/analysis/capacity_horizon/capacity_horizon_trajectory_coverage.csv
mbp baseline run-capacity-horizon --horizon-table data/interim/capacity_horizon_table_v1.parquet --out reports/baselines/capacity_horizon_l0_l2_report.json --predictions-out data/processed/capacity_horizon_l0_l2_predictions.parquet --out-dir reports/baselines/capacity_horizon_l0_l2 --targets capacity_Ah_kh,delta_capacity_Ah_h --horizons 1,2,3,5 --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting --feature-groups K0_prior_capacity,K1_prior_state_time,K2_nominal_condition,K3_oracle_exposure_diagnostic --hgb-max-iter 50
mbp baseline diagnose-capacity-horizon --report reports/baselines/capacity_horizon_l0_l2_report.json --predictions data/processed/capacity_horizon_l0_l2_predictions.parquet --horizon-table data/interim/capacity_horizon_table_v1.parquet --out-dir reports/baselines/capacity_horizon_l0_l2
mbp baseline run-capacity-horizon --horizon-table data/interim/capacity_horizon_table_v1.parquet --trajectory-features data/interim/capacity_horizon_trajectory_features_v1.parquet --out reports/baselines/capacity_horizon_trajectory_l0_l2_report.json --predictions-out data/processed/capacity_horizon_trajectory_l0_l2_predictions.parquet --out-dir reports/baselines/capacity_horizon_trajectory_l0_l2 --targets capacity_Ah_kh,delta_capacity_Ah_h --horizons 1,2,3,5 --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting --feature-groups K0_prior_capacity,K1_prior_state_time,K2_nominal_condition,K4_prior_trajectory_shape,K5_nominal_plus_trajectory_shape --hgb-max-iter 50
mbp baseline diagnose-capacity-horizon-trajectory --report reports/baselines/capacity_horizon_trajectory_l0_l2_report.json --predictions data/processed/capacity_horizon_trajectory_l0_l2_predictions.parquet --horizon-table data/interim/capacity_horizon_table_v1.parquet --out-dir reports/baselines/capacity_horizon_trajectory_l0_l2
mbp analysis build-policy-contrast-registry --interval-table data/interim/interval_table.parquet --out data/interim/policy_contrast_registry_v1.parquet
mbp analysis policy-contrast-qa --contrast-registry data/interim/policy_contrast_registry_v1.parquet --interval-table data/interim/interval_table.parquet --out reports/analysis/policy/policy_contrast_support_report.json --registry-out reports/analysis/policy/policy_contrast_registry.csv --family-out reports/analysis/policy/policy_contrast_by_family.csv
mbp analysis evaluate-observed-policy-contrasts --contrast-registry data/interim/policy_contrast_registry_v1.parquet --interval-table data/interim/interval_table.parquet --out-dir reports/analysis/policy
mbp analysis evaluate-policy-ranking-feasibility --contrast-registry data/interim/policy_contrast_registry_v1.parquet --horizon-table data/interim/capacity_horizon_table_v1.parquet --predictions data/processed/capacity_horizon_l0_l2_predictions.parquet --out-dir reports/analysis/policy --targets delta_capacity_Ah_h,capacity_Ah_kh --horizons 2,3 --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting --feature-groups persistence,prior_slope,K2_nominal_condition,K3_oracle_exposure_diagnostic --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold --bootstrap-count 200
mbp analysis diagnose-policy-ranking-feasibility --pairwise-metrics reports/analysis/policy/policy_ranking_pairwise_metrics.csv --by-family reports/analysis/policy/policy_ranking_by_family.csv --bootstrap reports/analysis/policy/policy_ranking_bootstrap.csv --out-dir reports/analysis/policy
mbp analysis diagnose-support-reliability --interval-table data/interim/interval_table.parquet --horizon-table data/interim/capacity_horizon_table_v1.parquet --capacity-predictions data/processed/capacity_horizon_l0_l2_predictions.parquet --warning-table data/interim/threshold_warning_table_v1.parquet --warning-predictions data/processed/threshold_warning_l0_l2_predictions.parquet --policy-pairwise reports/analysis/policy/policy_ranking_pairwise_metrics.csv --out-dir reports/analysis/support_reliability
```

Outputs: tracked JSON/CSV/Markdown reports and ignored prediction Parquets.
The adaptive replication command emits tracked reports only and records
deterministic seed reuse explicitly for the HGB/no-bagging path.
The attribution command emits tracked decomposition reports and an ignored
prediction Parquet.
The hierarchical command emits tracked L5 comparator reports and an ignored
prediction Parquet.
The minimal-sequence reopening command emits tracked sequence reopening reports
and an ignored prediction Parquet. Torch MLP rows require CUDA-enabled PyTorch;
CPU neural fallback is invalid for that gate.
The capacity-horizon commands emit a tracked QA report, a tracked grouped
baseline report, tracked forensics reports, and ignored horizon/prediction
Parquets. K3 horizon exposure features are oracle diagnostics, not prospective
forecast inputs. The trajectory commands emit a tracked QA report, tracked
K4/K5 diagnostics, and ignored trajectory/prediction Parquets.
The policy-contrast commands emit an ignored observed contrast registry and
tracked support/stability diagnostics. They do not train a model or authorize
policy recommendations. The supported contrast-ordering feasibility command
uses existing multi-horizon predictions only; it does not retrain models, and
K3 rows remain oracle-diagnostic only. The failure-forensics command consumes
the 7.3 CSV reports only and decomposes the strict prior-slope failure by
effect size, rank metric, and top-k/regret diagnostics. The support-reliability
command consumes existing prediction/report artifacts only and writes tracked
support-distance and selective-retention diagnostics; it does not train a
model or authorize deployment, calibrated-risk, policy, causal, or CBAT claims.

## 7. Diagnostics

```bash
mbp analysis replicate-uncertainty --interval-table data/interim/interval_table.parquet --capacity-report reports/baselines/capacity_hgb50_focused_report.json --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet --out-dir reports/analysis/replicate_uncertainty
mbp analysis calibrate-capacity --capacity-report reports/baselines/capacity_hgb50_focused_report.json --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet --interval-table data/interim/interval_table.parquet --replicate-spread reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv --out-dir reports/analysis/calibration_capacity
mbp baseline diagnose-sequence-value --report reports/baselines/capacity_sequence_value_hgb50_report.json --baseline-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json --out-dir reports/baselines/capacity_sequence_value_hgb50
mbp baseline diagnose-stressor-robust-forensics --report reports/baselines/capacity_stressor_robust_hgb50_report.json --predictions data/processed/capacity_stressor_robust_hgb50_predictions.parquet --out-dir reports/baselines/capacity_stressor_robust_hgb50
```

Outputs: tracked diagnostic reports.

## 8. Knee and Threshold Labels

```bash
mbp analysis knee-labels --interval-table data/interim/interval_table.parquet --out-dir reports/analysis/knee --candidate-out data/interim/knee_candidate_table_v1.parquet
mbp analysis build-knee-risk-labels --knee-candidates data/interim/knee_candidate_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/knee_risk_label_table_v1.parquet
mbp analysis knee-forensics --knee-candidates data/interim/knee_candidate_table_v1.parquet --interval-table data/interim/interval_table.parquet --out-dir reports/analysis/knee
mbp analysis threshold-event-labels --interval-table data/interim/interval_table.parquet --out-dir reports/analysis/knee --labels-out data/interim/threshold_event_label_table_v1.parquet
mbp analysis build-threshold-warning-table --threshold-labels data/interim/threshold_event_label_table_v1.parquet --interval-table data/interim/interval_table.parquet --out data/interim/threshold_warning_table_v1.parquet --threshold capacity_below_80pct_initial
mbp analysis threshold-warning-qa --warning-table data/interim/threshold_warning_table_v1.parquet --out reports/analysis/knee/threshold_warning_qa_report.json --class-balance-out reports/analysis/knee/threshold_warning_class_balance.csv --split-coverage-out reports/analysis/knee/threshold_warning_split_coverage.csv
```

Outputs: ignored label/warning Parquets and tracked QA/readiness reports.

## 9. Threshold Warning

```bash
mbp baseline run-threshold-warning --warning-table data/interim/threshold_warning_table_v1.parquet --out reports/baselines/threshold_warning_l0_l2_report.json --predictions-out data/processed/threshold_warning_l0_l2_predictions.parquet
mbp baseline run-threshold-warning --warning-table data/interim/threshold_warning_table_v1.parquet --label-policy verified_only --out reports/baselines/threshold_warning_verified_only_report.json --predictions-out data/processed/threshold_warning_verified_only_predictions.parquet
mbp baseline compare-threshold-warning-censoring --all-rows-report reports/baselines/threshold_warning_l0_l2_report.json --verified-only-report reports/baselines/threshold_warning_verified_only_report.json --out-dir reports/baselines/threshold_warning_censoring_sensitivity
mbp baseline finalize-threshold-warning-claim --report reports/baselines/threshold_warning_l0_l2_report.json --predictions data/processed/threshold_warning_l0_l2_predictions.parquet --warning-table data/interim/threshold_warning_table_v1.parquet --censoring-sensitivity reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md --out-dir reports/baselines/threshold_warning_l0_l2
```

Outputs: tracked reports and ignored prediction Parquets.

## 10. Synthesis

The current synthesis artifacts are tracked under `docs/` and
`reports/synthesis/`. Milestone 3.1 adds the release package documented in
`docs/BENCHMARK_REPRODUCIBILITY.md`, `docs/COMMAND_DAG.md`, and
`reports/synthesis/artifact_manifest_v2.csv`.

```bash
mbp report check-release-candidate
mbp report check-benchmark-tasks --task-registry configs/benchmark_tasks_v1.yaml --out reports/synthesis/benchmark_task_registry_check.md --leaderboard-out reports/synthesis/benchmark_leaderboard_v1.csv --task-cards-out reports/synthesis/benchmark_task_cards_v1.md --model-cards-out reports/synthesis/benchmark_model_cards_v1.md
```

Outputs: tracked release/task consistency checks and frozen task-level
benchmark synthesis artifacts. These commands do not train models or generate
data products.
