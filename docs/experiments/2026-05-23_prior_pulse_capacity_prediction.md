# 2026-05-23 Prior-PULSE Capacity Prediction

## Scope

Milestone 0.9 tests a narrow non-neural predictive claim:

> Prior PULSE state at check-up `k` improves `capacity_Ah_k1` prediction under
> grouped validation.

The primary target is `capacity_Ah_k1`. `delta_capacity_Ah` is a secondary
guardrail because prior PULSE did not solve the C-rate delta failure in 0.8.

This is not a broad multimodal milestone. Future PULSE state, PULSE deltas, EIS,
sequence models, neural models, policy ranking, and CBAT remain blocked.

## Cleanup

The Milestone 0.8.1 bootstrap markdown renderer was fixed before this run. The
bootstrap summary now renders one row per correlation type with explicit
`Mean`, `p05`, `p50`, and `p95` columns instead of repeated ambiguous rows.

## Command

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline compare-prior-pulse-capacity \
  --baseline-report reports/baselines/capacity_hgb50_focused_report.json \
  --prior-pulse-report reports/baselines/capacity_with_prior_pulse_hgb50_report.json \
  --out-dir reports/baselines/capacity_prior_pulse_predictive \
  --bootstrap-resamples 1000 \
  --seed 42
```

## Outputs

```text
reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_report.json
reports/baselines/capacity_prior_pulse_predictive/paired_condition_gain.csv
reports/baselines/capacity_prior_pulse_predictive/split_level_gain_summary.csv
reports/baselines/capacity_prior_pulse_predictive/c_rate_gain_summary.csv
reports/baselines/capacity_prior_pulse_predictive/coverage_effect_summary.csv
reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_claim_readiness.md
```

## Paired Gain Results

Positive gain means the selected prior-PULSE feature group reduced
condition-level MAE versus F4 on the same PULSE-covered interval population.

| Target | Split | Best prior-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | 12 | `0.00669208` | `0.000718651` | `0.00678842` | `0.0131255` | `0.666667` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | 38 | `0.00509620` | `0.00103230` | `0.00493892` | `0.00974339` | `0.605263` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | 12 | `0.0214905` | `0.0137834` | `0.0214668` | `0.0299696` | `0.916667` |
| `capacity_Ah_k1` | condition | `C_P2_log_age_pulse` | 76 | `0.000252864` | `-0.000847874` | `0.000275611` | `0.00134236` | `0.539474` |
| `capacity_Ah_k1` | voltage-window | `C_P2_log_age_pulse` | 76 | `0.000314337` | `-0.00152649` | `0.000310583` | `0.00201887` | `0.631579` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | 12 | `-0.00574230` | `-0.0203466` | `-0.00552136` | `0.00835579` | `0.5` |
| `delta_capacity_Ah` | condition | `C_P3_stress_pulse` | 76 | `0.00244457` | `-0.00118799` | `0.00256572` | `0.00605267` | `0.592105` |
| `delta_capacity_Ah` | temperature | `C_P3_stress_pulse` | 38 | `0.00103130` | `-0.00421893` | `0.00104477` | `0.00649051` | `0.5` |

## Coverage

Requiring prior `pulse_1s_resistance_k` has a small coverage effect:

| Quantity | Value |
|---|---:|
| Capacity-only selected rows | `3,827` |
| PULSE-covered selected rows | `3,826` |
| Dropped intervals | `1` |
| PULSE-covered parameter sets | `76` |
| C-rate interval rows dropped | `0` |

Coverage loss does not explain the C-rate or temperature gains.

## Leakage Audit

Allowed capacity input:

```text
pulse_1s_resistance_k
```

Forbidden capacity inputs:

```text
pulse_1s_resistance_k1
delta_pulse_1s_resistance
pulse_10ms_resistance_k1
delta_pulse_10ms_resistance
```

The comparison command fails if forbidden PULSE future/delta fields appear in
capacity feature groups.

## Decision

- Prior PULSE supports a narrow non-neural `capacity_Ah_k1` level-prediction
  claim for C-rate, temperature, and profile split diagnostics.
- Prior PULSE does not support a `delta_capacity_Ah` fade-rate claim.
- Condition and voltage-window gains for `capacity_Ah_k1` are small and have
  bootstrap intervals crossing zero.
- C-rate `delta_capacity_Ah` remains an unresolved limitation.
- Broad multimodal claims, future PULSE features, EIS, sequence models, neural
  models, policy ranking, and CBAT remain blocked.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
106 passed
```
