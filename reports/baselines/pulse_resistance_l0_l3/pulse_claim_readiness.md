# PULSE Claim Readiness

This memo is a diagnostic gate. It does not authorize capacity+PULSE multimodal claims.

| Claim area | Status | Evidence | Decision |
|---|---|---|---|
| Canonical RT/50 coverage | supported_for_scalar_diagnostics | Target availability is recorded in `row_counts` and PULSE QA reports. | Keep reporting missingness. |
| Alignment robustness | partially_supported | Alignment-threshold sensitivity is required before a PULSE claim. | Keep all/threshold comparisons visible. |
| Direction handling robustness | partially_supported | Direction-specific tables are diagnostic until policy v2. | Keep `mean` canonical. |
| Missingness limitations | partially_supported | Missing canonical endpoints are listed in audit reports. | Report with every claim-readiness memo. |
| C-rate resistance prediction | diagnostic_only | Best C-rate row `L2_hist_gradient_boosting + P3_state_nominal` has condition-mean MAE `0.00185842`. | Harden before claim. |
| Stress-feature contribution | diagnostic_only | `P5_stress_v1_1` appears in `10` primary leaderboard rows. | Compare against state/nominal rows. |
| Capacity-state contribution | diagnostic_only | `P2_state_capacity` appears in `10` primary leaderboard rows. | Keep as baseline component. |
| Secondary target readiness | diagnostic_only | Secondary targets not evaluated in this report. | Compare 1s/10ms and delta/k1 reports. |
| Claim status | diagnostic_only | Scalar PULSE reports are generated, but target robustness must be synthesized. | No capacity+PULSE multimodal claim. |
