# Milestone 2.1 - EIS Scalar Diagnostic Baselines

## Scope

Milestone 2.1 evaluates quality-controlled RT/50 scalar EIS features under
grouped validation. It does not implement DRT, EIS embeddings, neural models,
sequence models, CBAT, policy ranking, capacity+PULSE+EIS multimodal models, or
broad EIS improvement claims.

Allowed EIS inputs for non-EIS targets are prior check-up `k` scalar EIS
features only. Future EIS `k1` features, EIS deltas, R0/R1 without leakage-safe
provenance, DRT, and embeddings are blocked.

## Data Products

Created local ignored target table:

```text
data/interim/eis_target_table_v1.parquet
```

Tracked QA outputs:

```text
reports/audit/eis_target_qa_report.json
reports/audit/eis_target_coverage.csv
```

The target table contains 3,827 interval rows. Target QA reports:

| Item | Count |
|---|---:|
| finite prior EIS rows | 3,821 |
| finite k1 EIS rows | 3,750 |
| missing prior EIS rows | 6 |
| missing k1 EIS rows | 77 |
| finite `delta_eis_z_abs_1kHz` rows | 3,744 |
| finite `delta_eis_z_real_1kHz` rows | 3,744 |
| finite `delta_nyquist_semicircle_width_proxy` rows | 3,744 |

## Commands

```bash
.venv/bin/mbp eis build-targets \
  --eis-features data/interim/eis_feature_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/eis_target_table_v1.parquet \
  --soc-percent 50 \
  --temperature-context RT

.venv/bin/mbp eis target-qa \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/eis_target_qa_report.json \
  --coverage-out reports/audit/eis_target_coverage.csv

.venv/bin/mbp baseline run-eis \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/eis_scalar_l0_l3_report.json \
  --predictions-out data/processed/eis_scalar_l0_l3_predictions.parquet \
  --model-levels L0_persistence,L1_ridge,L2_hist_gradient_boosting \
  --feature-groups E0_persistence,E1_state_time,E2_state_capacity,E3_state_nominal,E4_log_age_scalar,E5_stress_v1_1 \
  --targets delta_eis_z_abs_1kHz,eis_z_abs_1kHz_k1,delta_nyquist_semicircle_width_proxy,nyquist_semicircle_width_proxy_k1 \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50

.venv/bin/mbp baseline run-pulse \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/pulse_with_prior_eis_hgb50_report.json \
  --predictions-out data/processed/pulse_with_prior_eis_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups P3_state_nominal,P5_stress_v1_1,P_E0_prior_eis,P_E1_nominal_eis,P_E2_log_age_eis,P_E3_stress_eis \
  --targets delta_pulse_1s_resistance \
  --hgb-max-iter 50

.venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --out reports/baselines/capacity_with_prior_eis_hgb50_report.json \
  --predictions-out data/processed/capacity_with_prior_eis_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F8_timestamp_weighted_stress,C_E0_state_time_eis,C_E1_nominal_eis,C_E2_log_age_eis,C_E3_stress_eis \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --hgb-max-iter 50
```

## EIS Scalar Endpoint Results

Best primary rows by target/split show that scalar EIS endpoints are predictable
enough for diagnostic baselines:

| Target | Split | Best model/group | Condition-mean MAE |
|---|---|---|---:|
| `delta_eis_z_abs_1kHz` | condition | HGB + `E2_state_capacity` | 0.000307288 |
| `delta_eis_z_abs_1kHz` | C-rate | HGB + `E4_log_age_scalar` | 0.000999892 |
| `eis_z_abs_1kHz_k1` | condition | HGB + `E3_state_nominal` | 0.000316323 |
| `eis_z_abs_1kHz_k1` | C-rate | HGB + `E3_state_nominal` | 0.00103563 |
| `delta_nyquist_semicircle_width_proxy` | condition | HGB + `E5_stress_v1_1` | 0.000413962 |
| `nyquist_semicircle_width_proxy_k1` | condition | HGB + `E3_state_nominal` | 0.000470220 |

Voltage-window rows are dominated by the persistence baseline for the two listed
delta/state pairs, so those should be interpreted as state-tracking diagnostics,
not as proof that richer EIS features help that split.

## EIS to PULSE

For `delta_pulse_1s_resistance`, prior-EIS groups are useful in several splits
but not C-rate:

| Split | Best group | Condition-mean MAE |
|---|---|---:|
| condition | `P5_stress_v1_1` | 0.000725000 |
| temperature | `P_E2_log_age_eis` | 0.000834027 |
| C-rate | `P3_state_nominal` | 0.00193709 |
| profile | `P_E1_nominal_eis` | 0.000922134 |
| voltage window | `P_E1_nominal_eis` | 0.000491196 |

This supports a split-dependent EIS-to-PULSE diagnostic signal, not a broad EIS
improvement claim.

## EIS to Capacity

For `capacity_Ah_k1`, prior-EIS groups win several non-C-rate splits, while the
non-EIS stress baseline wins C-rate:

| Split | Best group | Condition-mean MAE |
|---|---|---:|
| condition | `C_E3_stress_eis` | 0.0388056 |
| temperature | `C_E3_stress_eis` | 0.0595481 |
| C-rate | `F8_timestamp_weighted_stress` | 0.123572 |
| profile | `C_E0_state_time_eis` | 0.0543644 |
| voltage window | `C_E1_nominal_eis` | 0.0343353 |

For `delta_capacity_Ah`, C-rate remains unresolved:

| Split | Best group | Condition-mean MAE |
|---|---|---:|
| condition | `F8_timestamp_weighted_stress` | 0.0306797 |
| temperature | `C_E2_log_age_eis` | 0.0425504 |
| C-rate | `F4_state_log_age_scalar` | 0.0961280 |
| profile | `C_E0_state_time_eis` | 0.0578438 |
| voltage window | `C_E2_log_age_eis` | 0.0176899 |

## Decision

Milestone 2.1 supports:

- EIS is useful as a scalar self-diagnostic endpoint.
- Prior EIS has split-dependent diagnostic value for PULSE resistance.
- Prior EIS has split-dependent capacity-level signal outside the C-rate view.

Milestone 2.1 does not support:

- a broad EIS improvement claim;
- an EIS claim for C-rate `capacity_Ah_k1`;
- an EIS claim for C-rate `delta_capacity_Ah`;
- EIS beating the strongest non-EIS baselines with paired bootstrap support;
- DRT, embeddings, CBAT, or capacity+PULSE+EIS multimodal modeling.

The next technical step, if continuing EIS, should be a claim-hardening pass:
paired strongest-non-EIS comparisons, alignment-threshold sensitivity, and
condition-level bootstrap intervals for prior-EIS gains.
