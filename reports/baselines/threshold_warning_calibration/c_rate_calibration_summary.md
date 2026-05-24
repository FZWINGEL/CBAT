# C-Rate Threshold-Warning Probability Calibration

This report checks probability calibration for the C-rate holdout only. It does not authorize policy ranking or causal risk claims.

| Label policy | Calibration method | Mean Brier | Mean ECE | Mean log loss | Fallback rows |
|---|---|---:|---:|---:|---:|
| `all_rows` | `C0_raw_hgb_w2` | `0.19858` | `0.222194` | `0.741715` | `0` |
| `all_rows` | `C1_platt_logistic` | `0.174262` | `0.208924` | `0.551993` | `0` |
| `all_rows` | `C2_isotonic` | `0.163916` | `0.192354` | `0.544811` | `0` |
| `verified_only` | `C0_raw_hgb_w2` | `0.190892` | `0.214827` | `0.739378` | `0` |
| `verified_only` | `C1_platt_logistic` | `0.148773` | `0.167813` | `0.460775` | `0` |
| `verified_only` | `C2_isotonic` | `0.147795` | `0.159021` | `0.499373` | `0` |

C-rate calibrated-risk wording remains blocked unless this split passes the grouped ECE guardrail.
