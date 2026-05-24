# Stressor-Robust Pareto Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Pareto robust-capacity claim | `diagnostic_only` | Predeclared setting passes 5% gate: `False`. |
| C-rate gain | `diagnostic` | Gain vs F4 `0.0305899`; gain vs stress reference `0.0319729`. |
| Other split non-degradation | `not_supported` | Max degradation for predeclared setting `0.0528343`. |
| Architecture readiness | `blocked` | This is a non-neural Pareto diagnostic only. |
| Policy ranking | `blocked` | No calibrated risk or intervention task is tested. |

Support requires the predeclared R2/F8/weight=1.0 setting to retain positive C-rate delta gains versus F4 and stress references, paired p05 above zero for both references, and <=5% outside-C-rate degradation. Other passing frontier points are diagnostic only.

## Nondominated Frontier Rows

| Setting | Model | Feature | Gain vs F4 | Gain vs stress | Max outside-C-rate degradation | Predeclared |
|---|---|---|---:|---:|---:|---|
| `R2_stressor_balanced_hgb__w1` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0305899` | `0.0319729` | `0.0528343` | `True` |
| `R2_stressor_balanced_hgb__w0p25` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0200436` | `0.0214266` | `0.0279117` | `False` |
| `R2_stressor_balanced_hgb__w0p5` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0214501` | `0.0228331` | `0.047683` | `False` |
| `R2_stressor_balanced_hgb__w0p75` | `R2_stressor_balanced_hgb` | `F8_timestamp_weighted_stress` | `0.0312177` | `0.0326007` | `0.110101` | `False` |

Metric rows evaluated: `768`.
Decision: passing non-predeclared frontier rows are diagnostic only.
