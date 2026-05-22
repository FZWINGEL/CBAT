# 2026-05-23 Capacity Target Consistency

## Scope

Milestone 0.6.2 audits why LOG_AGE stress features improved C-rate
`capacity_Ah_k1` but not C-rate `delta_capacity_Ah`. The work is report-level
diagnostics only: no new modalities, no sequence models, no neural models, no
policy ranking, and no CBAT.

## Inputs

```text
reports/baselines/capacity_stress_features_v1_1_hgb50_report.json
data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet
```

The prediction Parquet remains ignored. Diagnostics join predictions back to the
interval table declared in the JSON report to recover `capacity_Ah_k` and derive
the algebraically linked target:

```text
capacity_Ah_k1 = capacity_Ah_k + delta_capacity_Ah
```

## Command

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-target-consistency \
  --report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --predictions data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet \
  --out-dir reports/baselines/capacity_stress_features_v1_1_hgb50
```

## Outputs

```text
reports/baselines/capacity_stress_features_v1_1_hgb50/target_consistency_diagnostics.md
reports/baselines/capacity_stress_features_v1_1_hgb50/c_rate_residual_analysis.md
reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_ablation_summary.md
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/derived_delta_from_capacity_metrics.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/derived_capacity_from_delta_metrics.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/direct_vs_derived_target_metrics.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_parameter_set.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_temperature.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_voltage_window.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_capacity_bin.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_interval_count.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_signed_error_summary.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv
reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv
```

## Findings

C-rate direct-vs-derived target rows:

| Target | Rows | Derived path better by MAE | Derived path better by condition mean MAE |
|---|---:|---:|---:|
| `capacity_Ah_k1` | 14 | 10 | 10 |
| `delta_capacity_Ah` | 14 | 4 | 4 |

Best C-rate condition-mean paths:

| Target interpreted | Best path | Model / feature group | Condition mean MAE |
|---|---|---|---:|
| `capacity_Ah_k1` | derived from direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | derived from direct capacity | `L2_hist_gradient_boosting` / `F5_log_age_histograms` | `0.120605` |

This means the C-rate failure is **not** primarily solved by predicting capacity
and subtracting `capacity_Ah_k`. Direct delta remains the stronger C-rate path.
The surprising part is the opposite direction: deriving capacity from the best
direct delta model beats the best direct capacity model in the C-rate diagnostic.

C-rate residual analysis still concentrates the worst rows in cold/cool
high-C-rate conditions:

- parameter set `36`, 10 C, `approx_10_100`;
- parameter set `32`, 10 C, `approx_0_100`;
- parameter set `20`, 0 C, `approx_0_100`;
- parameter set `24`, 0 C, `approx_10_100`;
- parameter set `60`, 40 C, `approx_10_100`.

The worst residuals are mostly positive bias for `capacity_Ah_k1`, meaning the
selected capacity path tends to overpredict held-out C-rate capacity for those
conditions.

Stress-feature ablation shows the strongest C-rate gains are model-dependent:

- HGB point model gains for C-rate `capacity_Ah_k1` are modest, with
  `F5_log_age_histograms` improving F4 by `0.004581`.
- HGB point model stress groups do not beat F4 for C-rate `delta_capacity_Ah`.
- Quantile HGB rows show larger stress-feature gains, but quantile calibration
  remains diagnostic only and should not be treated as an uncertainty claim.

## Decision

Use **direct delta** as the primary C-rate delta target for now. Do not switch to
derived delta from capacity predictions.

For reporting, keep both target views available:

- report direct `delta_capacity_Ah` for interval-change evidence;
- report `capacity_Ah_k1` both directly and as `capacity_Ah_k + predicted_delta`
  in diagnostics when comparing C-rate transfer.

The next engineering step should not be PULSE/EIS/CBAT. The next decision is
between:

1. a very narrow C-rate delta-focused feature pass;
2. residual/bias correction for cold/cool high-C-rate conditions;
3. stopping stress-feature expansion and considering PULSE as an independent
   evidence stream.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest tests/test_capacity_baselines.py -q
21 passed
```
