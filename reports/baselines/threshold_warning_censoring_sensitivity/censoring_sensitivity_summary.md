# Threshold-Warning Censoring Sensitivity

This report compares all-row and verified-only threshold-warning evaluation. It does not authorize calibrated risk or detector-knee prediction.

both_policies_pass: true

| Label policy | Target rows | Positives | Negatives | HGB Brier | Prior Brier | Proximity Brier | Gain vs prior | Gain vs proximity | Passes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `all_rows` | `3827` | `494` | `3333` | `0.0655751` | `0.145791` | `0.132711` | `0.080216` | `0.067136` | `True` |
| `verified_only` | `2433` | `494` | `1939` | `0.090116` | `0.178655` | `0.168492` | `0.0885393` | `0.0783761` | `True` |

If verified-only performance collapses, threshold-warning claims remain exploratory. If both policies pass, a narrow diagnostic threshold-event forecasting claim is allowed.
