# PULSE Claim Readiness

This memo is a diagnostic gate. It does not authorize capacity+PULSE multimodal claims.

| Claim area | Status | Evidence | Decision |
|---|---|---|---|
| Canonical RT/50 coverage | partially_supported | Target availability is recorded in `row_counts` and PULSE QA reports. | Keep reporting missingness. |
| Alignment robustness | diagnostic_only | Alignment-threshold sensitivity is required before a PULSE claim. | Do not claim yet. |
| Direction averaging robustness | diagnostic_only | Direction-specific tables are diagnostic until policy v2. | Compare charge/discharge. |
| C-rate resistance prediction | diagnostic_only | Best C-rate row `L2_hist_gradient_boosting + P3_state_nominal` has condition-mean MAE `0.00185842`. | Harden before claim. |
| Scientific PULSE claim | blocked_by_alignment | Large alignment deltas remain visible warnings. | No claim yet. |
