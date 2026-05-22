# Capacity Baseline Claim Readiness

This table is a Milestone 0.5c synthesis aid. It does not authorize
EIS/PULSE modeling, knee prediction, sequence models, neural models,
policy ranking, or CBAT.

| Claim | Status | Evidence | Decision |
|---|---|---|---|
| State-aware baselines beat weak time-only baselines | Supported | `F1_state_time` and later groups include prior capacity state and dominate the weak `F0_time_only` sanity baseline in the capacity ladder. | Keep state-aware groups as the first forecast baseline. |
| Nominal protocol features help | Supported | `F2_state_exposure -> F3_state_nominal` mean gain 0.0265703 across 10 primary rows. | Keep nominal protocol features. |
| LOG_AGE scalar features help | Partially supported | `F3_state_nominal -> F4_state_log_age_scalar` mean gain -0.103305; the benefit is model-dependent and strongest in focused HGB. | Build stronger log-derived stress features before adding modalities. |
| C-rate holdout is hardest | Supported | Best C-rate condition-mean MAE max 0.177045, other split best max 0.0893865. | Focus next engineering on C-rate/stress exposure. |
| Monotonicity policy changes conclusions | Not supported | Mean absolute strict-vs-tolerant delta 0.00369243. | Keep tolerant subset as primary with strict sensitivity. |
| Quantile HGB is calibrated | Not supported | Mean q10-q90 coverage NA; nominal central coverage is 0.8. | Treat quantile metrics as diagnostics only. |

C-rate condition rows used for stress analysis: `24`.
