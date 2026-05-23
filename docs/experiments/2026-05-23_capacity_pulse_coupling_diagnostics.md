# 2026-05-23 Capacity-PULSE Coupling Diagnostics

## Scope

Milestone 0.8 tests whether canonical RT/50 PULSE resistance provides scalar
diagnostic information about capacity-model failures. This is not a
capacity+PULSE multimodal architecture milestone. EIS modeling, sequence models,
neural models, policy ranking, CBAT, and broad multimodal claims remain blocked.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp coupling pulse-capacity \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/coupling/pulse_capacity \
  --coupling-table-out data/interim/capacity_pulse_coupling_table.parquet

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --out reports/baselines/capacity_with_prior_pulse_hgb50_report.json \
  --predictions-out data/processed/capacity_with_prior_pulse_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,C_P0_state_time_pulse,C_P1_nominal_pulse,C_P2_log_age_pulse,C_P3_stress_pulse \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50
```

Generated prediction and coupling Parquets remain ignored.

## Outputs

```text
reports/coupling/pulse_capacity/pulse_capacity_correlation.md
reports/coupling/pulse_capacity/plots/capacity_residual_vs_delta_pulse.csv
reports/coupling/pulse_capacity/plots/capacity_residual_by_pulse_growth_bin.csv
reports/coupling/pulse_capacity/plots/c_rate_capacity_residual_by_pulse_growth.csv
reports/coupling/pulse_capacity/plots/pulse_growth_by_capacity_error_decile.csv
reports/baselines/capacity_with_prior_pulse_hgb50_report.json
reports/baselines/capacity_with_prior_pulse_hgb50/pulse_feature_gain.md
reports/baselines/capacity_with_prior_pulse_hgb50/plots/capacity_pulse_feature_gain_by_split.csv
reports/baselines/capacity_with_prior_pulse_hgb50/plots/c_rate_capacity_pulse_feature_gain.csv
reports/baselines/capacity_with_prior_pulse_hgb50/plots/pulse_feature_gain_claim_readiness.csv
```

## Coupling Findings

Capacity residuals from the focused HGB-50 capacity report correlate strongly
with canonical PULSE resistance growth in C-rate views:

| Scope | Target | Residual | Pearson | Spearman |
|---|---|---|---:|---:|
| all | `capacity_Ah_k1` | absolute residual | `0.559997` | `0.236657` |
| all | `delta_capacity_Ah` | absolute residual | `0.604807` | `0.304910` |
| C-rate | `capacity_Ah_k1` | absolute residual | `0.894547` | `0.664034` |
| C-rate | `delta_capacity_Ah` | absolute residual | `0.822463` | `0.639033` |
| cold C-rate | `capacity_Ah_k1` | absolute residual | `0.877023` | `0.824406` |
| cold C-rate | `delta_capacity_Ah` | absolute residual | `0.769408` | `0.723490` |

Interpretation: PULSE growth is a strong explanatory diagnostic for where the
capacity-only HGB-50 model struggles, especially in the C-rate and cold C-rate
views. This is not yet predictive evidence that PULSE improves capacity models.

## Prior-PULSE Capacity Baseline

Prior PULSE state was added only as `pulse_1s_resistance_k`. Future PULSE state
and transition targets were excluded from capacity inputs:

```text
pulse_1s_resistance_k1
delta_pulse_1s_resistance
pulse_10ms_resistance_k1
delta_pulse_10ms_resistance
```

Best gains versus F4 on the PULSE-covered interval population:

| Target | Split | Best prior-PULSE group | Gain vs F4 |
|---|---|---|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `0.00669208` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `-0.00574230` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `0.00509620` |
| `delta_capacity_Ah` | condition | `C_P3_stress_pulse` | `0.00249507` |

The row-count effect from requiring prior PULSE is small but visible:

```text
baseline_clean_tolerant selected rows: 3,826
baseline_clean_strict selected rows: 2,772
```

## Decision

- Capacity residuals correlate with PULSE growth, especially in C-rate and cold
  C-rate views.
- Prior PULSE state improves `capacity_Ah_k1` C-rate performance versus F4.
- Prior PULSE state does not improve C-rate `delta_capacity_Ah`; the best
  prior-PULSE row is worse than F4 for that target.
- PULSE is useful as a scalar explanatory diagnostic endpoint.
- A capacity+PULSE predictive or multimodal claim is not yet authorized.

## Next Step

Do not move to CBAT or neural multimodal modeling. The next decision should be
whether to run a narrow non-neural capacity+PULSE baseline focused on
`capacity_Ah_k1`, or keep PULSE as an explanatory endpoint while addressing the
remaining C-rate `delta_capacity_Ah` failure separately.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
103 passed
```
