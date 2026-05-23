# Calibration Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Raw HGB quantiles calibrated | `not_supported` | Q0_hgb_quantile_raw: evaluated 24 rows; min coverage 0; mean coverage 0.676677; C-rate acceptable=False. |
| Grouped conformal intervals calibrated | `partially_supported` | Q1_split_conformal_abs_residual: evaluated 20 rows; min coverage 0.68709; mean coverage 0.885689; C-rate acceptable=False. |
| Stressor-family conformal intervals calibrated | `partially_supported` | Q2_stressor_family_conformal: evaluated 24 rows; min coverage 0.614159; mean coverage 0.875736; C-rate acceptable=False. |
| Replicate-aware hybrid intervals useful | `partially_supported` | Q3_replicate_tolerance_hybrid: evaluated 24 rows; min coverage 0.614159; mean coverage 0.875736; C-rate acceptable=False. |
| C-rate coverage acceptable | `not_supported` | all_methods: evaluated 4 rows; min coverage 0.719745; mean coverage 0.72293; C-rate acceptable=False. |
| delta_capacity_Ah coverage acceptable | `partially_supported` | all_methods: evaluated 24 rows; min coverage 0.659574; mean coverage 0.872963; C-rate acceptable=False. |
| Uncertainty claim readiness | `blocked` | No calibrated uncertainty claim is authorized unless coverage is close to nominal without test-residual leakage and C-rate coverage remains acceptable. |
