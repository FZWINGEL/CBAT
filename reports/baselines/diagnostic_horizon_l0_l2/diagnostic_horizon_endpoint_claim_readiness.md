# Diagnostic-Horizon Endpoint Claim Readiness

Endpoint-specific statuses are conservative and do not override the overall Milestone 8.2 partial result.

| Target | Status | Primary rows | C-rate rows | Allowed wording |
|---|---|---:|---:|---|
| `eis_phase_1kHz` | `partially_supported` | `3/4` | `4/4` | `eis_phase_1kHz` has partial endpoint-forecasting signal but misses at least one strict guardrail |
| `eis_z_abs_1kHz` | `supported_for_diagnostics` | `4/4` | `4/4` | `eis_z_abs_1kHz` supports endpoint-specific diagnostic forecasting under the Milestone 8.2 grouped checks |
| `nyquist_im_peak_abs` | `partially_supported` | `2/4` | `4/4` | `nyquist_im_peak_abs` has partial endpoint-forecasting signal but misses at least one strict guardrail |
| `nyquist_semicircle_width_proxy` | `supported_for_diagnostics` | `4/4` | `4/4` | `nyquist_semicircle_width_proxy` supports endpoint-specific diagnostic forecasting under the Milestone 8.2 grouped checks |
| `pulse_10ms_resistance` | `supported_for_diagnostics` | `4/4` | `4/4` | `pulse_10ms_resistance` supports endpoint-specific diagnostic forecasting under the Milestone 8.2 grouped checks |
| `pulse_1s_resistance` | `partially_supported` | `4/4` | `2/4` | `pulse_1s_resistance` has partial endpoint-forecasting signal but misses at least one strict guardrail |
| `capacity_plus_pulse_eis_architecture` | `blocked` | `0/0` | `0/0` | architecture remains blocked |
| `calibrated_risk_or_uncertainty` | `blocked` | `0/0` | `0/0` | calibration was not tested in this gate |

Forbidden wording remains: broad endpoint forecasting, capacity+PULSE+EIS architecture, CBAT, calibrated risk or uncertainty, policy ranking, causal effects, and same-cell counterfactuals.
