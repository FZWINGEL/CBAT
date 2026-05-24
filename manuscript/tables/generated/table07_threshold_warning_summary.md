# Table 7. Threshold-warning hardening summary

| Policy | Rows | Positives | Negatives | HGB W2 Brier | Event-rate prior Brier | Proximity baseline Brier | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| all rows | 3,827 | 494 | 3,333 | 0.065575 | 0.145791 | 0.132711 | Diagnostic forecast survives proximity comparison. |
| verified only | 2,433 | 494 | 1,939 | 0.090116 | 0.178655 | 0.168492 | Result does not collapse when right-censored unknown rows are removed. |

Source: `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`.

