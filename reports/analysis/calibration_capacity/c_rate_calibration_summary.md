# C-Rate Calibration Summary

Intervals are calibrated without using C-rate test residuals.

| Method | Target | Coverage | Width | Conditions | Calibration conditions | Status |
|---|---|---:|---:|---:|---:|---|
| `Q0_hgb_quantile_raw` | `capacity_Ah_k1` | 0.751592 | 0.298217 | 12 | 0 | `evaluated` |
| `Q1_split_conformal_abs_residual` | `capacity_Ah_k1` | NA | NA | 0 | 0 | `insufficient` |
| `Q2_stressor_family_conformal` | `capacity_Ah_k1` | 0.719745 | 0.221049 | 12 | 64 | `evaluated` |
| `Q3_replicate_tolerance_hybrid` | `capacity_Ah_k1` | 0.719745 | 0.221049 | 12 | 64 | `evaluated` |
| `Q0_hgb_quantile_raw` | `delta_capacity_Ah` | 0.624204 | 0.225389 | 12 | 0 | `evaluated` |
| `Q1_split_conformal_abs_residual` | `delta_capacity_Ah` | NA | NA | 0 | 0 | `insufficient` |
| `Q2_stressor_family_conformal` | `delta_capacity_Ah` | 0.726115 | 0.219931 | 12 | 64 | `evaluated` |
| `Q3_replicate_tolerance_hybrid` | `delta_capacity_Ah` | 0.726115 | 0.219931 | 12 | 64 | `evaluated` |
