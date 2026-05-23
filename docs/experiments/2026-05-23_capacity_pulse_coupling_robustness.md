# 2026-05-23 Capacity-PULSE Coupling Robustness

## Scope

Milestone 0.8.1 hardens the 0.8 capacity-PULSE coupling result. The 0.8 report
showed strong prediction-row correlations between capacity residuals and PULSE
resistance growth, but those rows repeated physical intervals across
model/feature/split predictions. This experiment filters to a canonical
capacity model and checks interval-level, condition-level, bootstrap, subgroup,
and residualized diagnostics.

This remains coupling diagnostics only. It does not authorize EIS modeling,
sequence models, neural models, policy ranking, CBAT, or broad capacity+PULSE
predictive claims.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp coupling pulse-capacity-robustness \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/coupling/pulse_capacity_robustness/capacity_Ah_k1 \
  --coupling-table-out data/interim/capacity_pulse_coupling_table.parquet \
  --model-level L2_hist_gradient_boosting \
  --feature-group F4_state_log_age_scalar \
  --target capacity_Ah_k1 \
  --split all \
  --bootstrap-resamples 1000 \
  --seed 42

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp coupling pulse-capacity-robustness \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/coupling/pulse_capacity_robustness/delta_capacity_Ah \
  --model-level L2_hist_gradient_boosting \
  --feature-group F4_state_log_age_scalar \
  --target delta_capacity_Ah \
  --split all \
  --bootstrap-resamples 1000 \
  --seed 42

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp coupling pulse-capacity-robustness \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate \
  --model-level L2_hist_gradient_boosting \
  --feature-group F4_state_log_age_scalar \
  --target capacity_Ah_k1 \
  --split c_rate_holdout_fold \
  --bootstrap-resamples 1000 \
  --seed 42

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp coupling pulse-capacity-robustness \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate \
  --model-level L2_hist_gradient_boosting \
  --feature-group F4_state_log_age_scalar \
  --target delta_capacity_Ah \
  --split c_rate_holdout_fold \
  --bootstrap-resamples 1000 \
  --seed 42
```

The generated coupling Parquet remains ignored.

## Outputs

```text
reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/
reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/
reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/
reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/
```

Each directory contains:

```text
canonical_model_correlation.md
interval_level_correlation.md
condition_level_correlation.md
bootstrap_correlation_summary.md
residualized_correlation.md
subgroup_coupling_summary.md
coupling_claim_readiness.md
plots/*.csv
```

## Findings

Canonical all-split interval/condition correlations for
`L2_hist_gradient_boosting + F4_state_log_age_scalar`:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 3,751 | `0.593280` | `0.304567` |
| `capacity_Ah_k1` | condition abs residual | 76 | `0.903834` | `0.905345` |
| `delta_capacity_Ah` | interval abs residual | 3,751 | `0.485245` | `0.314490` |
| `delta_capacity_Ah` | condition abs residual | 76 | `0.779516` | `0.773069` |

Canonical C-rate split correlations:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 143 | `0.857653` | `0.633959` |
| `capacity_Ah_k1` | condition abs residual | 12 | `0.956599` | `0.979021` |
| `delta_capacity_Ah` | interval abs residual | 143 | `0.647125` | `0.646779` |
| `delta_capacity_Ah` | condition abs residual | 12 | `0.903590` | `0.881119` |

Parameter-set bootstrap on the C-rate split kept the interval-level association
positive. For `capacity_Ah_k1`, bootstrap Spearman for PULSE 1s growth versus
absolute residual had mean `0.634652`, p05 `0.481109`, p50 `0.637743`, and p95
`0.769496`. For `delta_capacity_Ah`, the same bootstrap had mean `0.633413`,
p05 `0.508631`, p50 `0.640653`, and p95 `0.735068`.

Residualized diagnostics weaken the all-interval association, especially for
`delta_capacity_Ah`, but the C-rate split remains associated:

| Target | Scope | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | all intervals | 3,751 | `0.451220` | `0.251932` |
| `capacity_Ah_k1` | C-rate split | 143 | `0.838145` | `0.627044` |
| `delta_capacity_Ah` | all intervals | 3,751 | `0.330324` | `0.182004` |
| `delta_capacity_Ah` | C-rate split | 143 | `0.519771` | `0.447610` |

## Decision

- PULSE growth remains associated with capacity residual magnitude after
  canonical-model filtering.
- The association survives interval-level aggregation.
- The condition-level association is strong, especially for C-rate, but C-rate
  condition-level evidence has only 12 parameter-set conditions.
- Basic residualization weakens the global association, so the result should not
  be interpreted as causal or independent of age/state/stress confounding.
- C-rate split associations remain visible after residualization.
- Prior PULSE state remains useful for `capacity_Ah_k1`, but the C-rate
  `delta_capacity_Ah` forecast failure remains unresolved.

## Claim Status

PULSE is supported as a scalar explanatory diagnostic endpoint for capacity
residual analysis, especially in C-rate views. A capacity+PULSE predictive claim
or broad multimodal claim is still not authorized.

## Validation

Validation after implementation:

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
104 passed
```
