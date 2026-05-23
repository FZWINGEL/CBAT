# PULSE Claim Readiness

This memo is a diagnostic gate. It does not authorize capacity+PULSE multimodal claims.

| Claim area | Status | Evidence | Decision |
|---|---|---|---|
| Canonical RT/50 coverage | supported_for_scalar_diagnostics | Target availability is recorded in `row_counts` and PULSE QA reports. | Keep reporting missingness. |
| Alignment robustness | supported_for_scalar_diagnostics_with_reporting_sensitivity | 24h/36h threshold reports are tracked separately. | Keep all/threshold comparisons visible. |
| Direction handling robustness | supported_for_scalar_diagnostics | Current RT/50 `mean` is effectively equivalent to `charge`; discharge adjacent deltas are unavailable. | Keep `mean` canonical. |
| Missingness limitations | partially_supported | Missing canonical endpoints are listed in audit reports; current real-data count is 76 rows. | Report with every claim-readiness memo. |
| C-rate resistance prediction | supported_for_scalar_diagnostics | Best C-rate row `L2_hist_gradient_boosting + P4_state_log_age_scalar` has condition-mean MAE `0.00179792`. | Use as scalar baseline evidence only. |
| Stress-feature contribution | partially_supported | `P5_stress_v1_1` appears in `40` primary leaderboard rows. | Useful in condition/temperature views, not uniformly C-rate. |
| Capacity-state contribution | diagnostic_only | `P2_state_capacity` appears in `40` primary leaderboard rows. | Keep as baseline component. |
| Secondary target readiness | partially_supported | Evaluated targets: `delta_pulse_10ms_resistance, pulse_10ms_resistance_k1, pulse_1s_resistance_k1`. | Compare 1s/10ms and delta/k1 reports. |
| Claim status | scalar_resistance_baseline_ready | Canonical RT/50 mean PULSE passed the scalar diagnostic target-robustness gate. | No capacity+PULSE multimodal claim. |
