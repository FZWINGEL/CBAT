# 2026-05-23 PULSE Target Robustness Decision

## Scope

Milestone 0.7.2 tests whether canonical RT/50 PULSE is robust enough as a scalar resistance-baseline endpoint. This is not capacity+PULSE multimodal modeling.

## Target Robustness

| Target | Split | Best model | Feature group | Condition mean MAE | Test rows |
|---|---|---|---|---:|---:|
| `delta_pulse_1s_resistance` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00185842 | 143 |
| `delta_pulse_1s_resistance` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000960407 | 3751 |
| `delta_pulse_1s_resistance` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000953406 | 733 |
| `delta_pulse_1s_resistance` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.0010961 | 1756 |
| `delta_pulse_1s_resistance` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00117733 | 3751 |
| `pulse_1s_resistance_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00189616 | 143 |
| `pulse_1s_resistance_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00104973 | 3752 |
| `pulse_1s_resistance_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.000960212 | 734 |
| `pulse_1s_resistance_k1` | `temperature_holdout_fold` | `L1_ridge` | `P5_stress_v1_1` | 0.00112659 | 1756 |
| `pulse_1s_resistance_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P2_state_capacity` | 0.00124448 | 3752 |
| `delta_pulse_10ms_resistance` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | 0.00180642 | 143 |
| `delta_pulse_10ms_resistance` | `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.000910676 | 3751 |
| `delta_pulse_10ms_resistance` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P2_state_capacity` | 0.000882674 | 733 |
| `delta_pulse_10ms_resistance` | `temperature_holdout_fold` | `L1_ridge` | `P5_stress_v1_1` | 0.00103444 | 1756 |
| `delta_pulse_10ms_resistance` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | 0.00111169 | 3751 |
| `pulse_10ms_resistance_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00179792 | 143 |
| `pulse_10ms_resistance_k1` | `condition_fold` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00105917 | 3752 |
| `pulse_10ms_resistance_k1` | `profile_holdout_fold` | `L1_ridge` | `P3_state_nominal` | 0.00106246 | 734 |
| `pulse_10ms_resistance_k1` | `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | 0.00125687 | 1756 |
| `pulse_10ms_resistance_k1` | `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P4_state_log_age_scalar` | 0.00128434 | 3752 |

## Decisions

- `delta_pulse_1s_resistance` remains the canonical first PULSE transition target.
- `delta_pulse_10ms_resistance` behaves similarly and is viable as a secondary diagnostic target.
- `pulse_1s_resistance_k1` and `pulse_10ms_resistance_k1` are useful state-tracking targets, but they should be interpreted separately from transition prediction because persistence/state features can dominate level targets.
- `mean` remains canonical direction handling; for current RT/50 target extraction it is effectively equivalent to `charge`, while discharge adjacent interval deltas are unavailable.
- Alignment filters remain diagnostics. The 24h threshold does not collapse coverage but slightly changes C-rate metrics.
- Missing canonical endpoints remain visible limitations.

## Claim Status

Canonical RT/50 mean PULSE is robust enough for scalar resistance-baseline diagnostics. A broader scientific PULSE claim remains blocked until the claim-readiness memo is reviewed and accepted. Capacity+PULSE multimodal modeling, EIS, sequence models, neural models, policy ranking, and CBAT remain blocked.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
100 passed
```
