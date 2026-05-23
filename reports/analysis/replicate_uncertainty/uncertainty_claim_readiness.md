# Uncertainty Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Replicate spread is quantified | `supported_for_diagnostics` | Condition-triplet spread and tolerance rows are generated. |
| HGB calibrated uncertainty | `not_supported` | This diagnostic compares errors with empirical triplet spread; it does not calibrate HGB intervals. |
| Replicate-aware intervals | `diagnostic_only` | Empirical min/max triplet tolerance intervals are reported, not validated predictive intervals. |
