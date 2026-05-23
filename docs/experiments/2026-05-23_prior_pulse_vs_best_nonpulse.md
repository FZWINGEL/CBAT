# 2026-05-23 Prior-PULSE vs Strongest Non-PULSE Baseline

## Scope

Milestone 0.9.1 hardens the prior-PULSE capacity-level result by comparing
prior-PULSE feature groups against the strongest supplied non-PULSE HGB
baselines on the same PULSE-covered interval population.

This is still non-neural and baseline-only. Future PULSE state, PULSE deltas,
EIS, sequence models, neural models, policy ranking, CBAT, and broad multimodal
claims remain blocked.

## Command

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline compare-prior-pulse-vs-best-nonpulse \
  --nonpulse-reports reports/baselines/capacity_hgb50_focused_report.json,reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --prior-pulse-report reports/baselines/capacity_with_prior_pulse_hgb50_report.json \
  --out-dir reports/baselines/capacity_prior_pulse_vs_best_nonpulse \
  --bootstrap-resamples 1000 \
  --seed 42
```

## Outputs

```text
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_report.json
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/paired_gain_vs_best_nonpulse.csv
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/c_rate_gain_vs_best_nonpulse.csv
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/bootstrap_gain_vs_best_nonpulse.csv
reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md
```

## Results

Positive gain means the selected prior-PULSE group beat the strongest supplied
non-PULSE group on paired parameter-set condition errors.

| Target | Split | Prior-PULSE group | Best non-PULSE group | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `F5_log_age_histograms` | `0.000392605` | `-0.00553843` | `0.000727887` | `0.00645520` | `0.5` |
| `capacity_Ah_k1` | condition | `C_P2_log_age_pulse` | `F6_coupled_stress` | `-0.000362470` | `-0.00302473` | `-0.000320961` | `0.00225552` | `0.473684` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | `F1_state_time` | `-0.000697582` | `-0.00281975` | `-0.000582270` | `0.00111274` | `0.583333` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `F6_coupled_stress` | `-0.000753049` | `-0.00294184` | `-0.000680351` | `0.00123690` | `0.552632` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `F4_state_log_age_scalar` | `-0.00234428` | `-0.0169742` | `-0.00185231` | `0.0119867` | `0.583333` |

## Decision

- Prior PULSE does not beat the strongest supplied non-PULSE baseline with
  bootstrap support.
- For C-rate `capacity_Ah_k1`, prior PULSE is only marginally better on mean
  gain than `F5_log_age_histograms`, and the bootstrap p05 is negative.
- For temperature and profile `capacity_Ah_k1`, the strongest non-PULSE
  baselines are better on average.
- `delta_capacity_Ah` remains unsupported.
- The 0.9 claim should be narrowed to: prior PULSE improves over F4, not over
  the strongest supplied non-PULSE capacity baseline.

## Claim Status

Allowed:

```text
Prior PULSE state improves capacity_Ah_k1 over F4 under selected grouped splits.
```

Not allowed:

```text
Prior PULSE beats the strongest non-PULSE baseline.
Prior PULSE improves delta_capacity_Ah.
Broad capacity+PULSE multimodal claims.
```

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
107 passed
```
