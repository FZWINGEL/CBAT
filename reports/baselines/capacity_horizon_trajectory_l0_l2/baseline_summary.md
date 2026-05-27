# Capacity Horizon Baseline Summary

Rows: 13770
Metric rows: 1152

This gate evaluates non-neural multi-check-up capacity forecasting. Prospective claims may use K0-K2 and prior-only K4/K5 trajectory features when supplied; K3 is oracle diagnostic.

| Target | Horizon | Model | Feature group | Mean MAE |
| --- | ---: | --- | --- | ---: |
| capacity_Ah_kh | 1 | MH1_prior_slope_linear | prior_slope | 0.043048 |
| capacity_Ah_kh | 1 | MH3_hist_gradient_boosting | K2_nominal_condition | 0.046704 |
| capacity_Ah_kh | 1 | MH3_hist_gradient_boosting | K5_nominal_plus_trajectory_shape | 0.0481428 |
| capacity_Ah_kh | 1 | MH2_ridge | K1_prior_state_time | 0.0486403 |
| capacity_Ah_kh | 1 | MH2_ridge | K4_prior_trajectory_shape | 0.0492637 |
| capacity_Ah_kh | 1 | MH2_ridge | K2_nominal_condition | 0.0508914 |
| capacity_Ah_kh | 1 | MH3_hist_gradient_boosting | K1_prior_state_time | 0.0527355 |
| capacity_Ah_kh | 1 | MH3_hist_gradient_boosting | K4_prior_trajectory_shape | 0.0527441 |
| capacity_Ah_kh | 1 | MH3_hist_gradient_boosting | K0_prior_capacity | 0.0542973 |
| capacity_Ah_kh | 1 | MH2_ridge | K5_nominal_plus_trajectory_shape | 0.0564876 |
| capacity_Ah_kh | 1 | MH2_ridge | K0_prior_capacity | 0.070796 |
| capacity_Ah_kh | 1 | MH0_persistence | persistence | 0.0789195 |
| capacity_Ah_kh | 2 | MH3_hist_gradient_boosting | K5_nominal_plus_trajectory_shape | 0.0764613 |
| capacity_Ah_kh | 2 | MH3_hist_gradient_boosting | K2_nominal_condition | 0.0773609 |
| capacity_Ah_kh | 2 | MH1_prior_slope_linear | prior_slope | 0.0793428 |
| capacity_Ah_kh | 2 | MH2_ridge | K4_prior_trajectory_shape | 0.0833041 |
| capacity_Ah_kh | 2 | MH3_hist_gradient_boosting | K4_prior_trajectory_shape | 0.0861313 |
| capacity_Ah_kh | 2 | MH3_hist_gradient_boosting | K1_prior_state_time | 0.086434 |
| capacity_Ah_kh | 2 | MH2_ridge | K1_prior_state_time | 0.090765 |
| capacity_Ah_kh | 2 | MH2_ridge | K2_nominal_condition | 0.0930684 |
