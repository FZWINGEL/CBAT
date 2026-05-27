# Capacity Horizon Trajectory-Shape Diagnostics

Milestone 6.2 tests prior-only trajectory-shape features under the existing non-neural grouped multi-horizon capacity runner. K4/K5 features use only capacity history observed at or before check-up k.

Metric rows: 1152
Trajectory status: `partially_supported`

## Horizon-3 Capacity Repair

| Feature group | Candidate MAE | K2 MAE | Prior-slope MAE | Gain vs K2 | Gain vs prior | Beats all |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| K4_prior_trajectory_shape | 0.103741 | 0.0935304 | 0.0932329 | -0.0102109 | -0.0105084 | False |
| K5_nominal_plus_trajectory_shape | 0.0981241 | 0.0935304 | 0.0932329 | -0.00459367 | -0.00489117 | False |

## C-Rate Horizon 2/3 Preservation

| Target | Horizon | Feature group | Candidate MAE | K2 MAE | Gain vs K2 | Beats all |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| capacity_Ah_kh | 2 | K4_prior_trajectory_shape | 0.23067 | 0.183684 | -0.0469861 | False |
| capacity_Ah_kh | 2 | K5_nominal_plus_trajectory_shape | 0.180306 | 0.183684 | 0.00337836 | True |
| capacity_Ah_kh | 3 | K4_prior_trajectory_shape | 0.247917 | 0.221461 | -0.0264552 | False |
| capacity_Ah_kh | 3 | K5_nominal_plus_trajectory_shape | 0.225614 | 0.221461 | -0.00415229 | False |
| delta_capacity_Ah_h | 2 | K4_prior_trajectory_shape | 0.246843 | 0.18302 | -0.063823 | False |
| delta_capacity_Ah_h | 2 | K5_nominal_plus_trajectory_shape | 0.190892 | 0.18302 | -0.00787165 | False |
| delta_capacity_Ah_h | 3 | K4_prior_trajectory_shape | 0.252722 | 0.232468 | -0.0202535 | False |
| delta_capacity_Ah_h | 3 | K5_nominal_plus_trajectory_shape | 0.226924 | 0.232468 | 0.00554458 | True |

## Largest K5 Gains vs K2

| Split | Target | Horizon | Gain vs K2 | Beats all |
| --- | --- | ---: | ---: | --- |
| all | capacity_Ah_kh | 1 | -0.00143882 | False |
| all | capacity_Ah_kh | 2 | 0.000899667 | True |
| all | capacity_Ah_kh | 3 | -0.00459367 | False |
| all | capacity_Ah_kh | 5 | -0.00179467 | False |
| all | delta_capacity_Ah_h | 1 | -0.00174714 | False |
| all | delta_capacity_Ah_h | 2 | -0.00204076 | False |
| all | delta_capacity_Ah_h | 3 | -0.00709093 | False |
| all | delta_capacity_Ah_h | 5 | -0.0100545 | False |
| c_rate_holdout_fold | capacity_Ah_kh | 1 | -0.00304723 | False |
| c_rate_holdout_fold | capacity_Ah_kh | 2 | 0.00337836 | True |
| c_rate_holdout_fold | capacity_Ah_kh | 3 | -0.00415229 | False |
| c_rate_holdout_fold | capacity_Ah_kh | 5 | 0.0113428 | True |

## Claim Posture

- Prior-trajectory shape is prospective only when built from check-up-k history.
- K3 actual horizon exposure remains oracle-diagnostic only.
- Sequence/neural models, CBAT, policy ranking, causal claims, calibrated risk, and calibrated uncertainty remain blocked.
