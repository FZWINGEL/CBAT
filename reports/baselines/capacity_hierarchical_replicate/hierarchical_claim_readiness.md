# Hierarchical Replicate Capacity Claim Readiness

| Claim area | Status / value |
|---|---|
| L5 hierarchical comparator | supported_for_diagnostics |
| HGB partial pooling C-rate delta | diagnostic_only |
| C-rate delta gain vs HGB reference | 0.000100645 |
| C-rate paired gain mean | 0.000100645 |
| C-rate paired gain p05 | -1.88643e-05 |
| C-rate paired conditions | 12 |
| Max outside-C-rate relative degradation | 0.00275483 |
| Replicate-variance interval | diagnostic_only |
| Minimum primary interval coverage | 0.151596 |
| C-rate interval coverage | 0.312102 |
| Calibrated uncertainty | blocked |
| Hierarchical C-rate delta diagnostic | diagnostic_only |
| Global robust capacity claim | not_supported |
| Architecture readiness | blocked |
| Policy ranking | blocked |

## Claim Rule

A narrow hierarchical diagnostic claim requires H4/F4 to improve C-rate delta_capacity_Ah versus H3/F4, have paired condition bootstrap p05 above zero, and keep max outside-C-rate relative degradation at or below 5%. Intervals remain diagnostic unless grouped and C-rate coverage pass.

## Leakage Policy

Residual offsets, shrinkage factors, and interval radii are computed from outer training rows only. Parameter-set effects are never fit; held-out parameter sets fall back to stressor-family or global train residual offsets.
