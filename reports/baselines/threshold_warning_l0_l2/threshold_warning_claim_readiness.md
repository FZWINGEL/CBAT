# Threshold-Warning Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Threshold label stability | `partially_supported` | Milestone 2.5.1 selected `capacity_below_80pct_initial` as the strongest threshold target candidate. |
| Warning baseline feasibility | `partially_supported` | Best model mean Brier gain versus event-rate prior is `0.0279227`. |
| Beats distance-to-threshold baseline | `partially_supported` | Best HGB mean Brier gain versus best proximity baseline is `0.0246722`. |
| Lead-time usefulness | `exploratory_only` | Lead-time stratified diagnostics are reported separately and do not yet authorize an early-warning claim. |
| Censoring robustness | `exploratory_only` | Censoring sensitivity is reported; verified-only conclusions require review. |
| Grouped warning performance | `supported_for_diagnostics` | Grouped metrics beat event-rate priors, but this remains threshold-event forecasting, not detector-knee prediction. |
| C-rate warning performance | `exploratory_only` | C-rate rows require separate review for positive counts and performance. |
| Calibration | `not_supported` | Probability outputs are diagnostic; no calibrated-risk claim is authorized. |
| Detector-knee prediction | `blocked` | Detector-knee labels failed replicate consistency in Milestone 2.5. |
| Policy ranking | `blocked` | No intervention or ranking claim is tested. |
