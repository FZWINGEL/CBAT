# EIS Self-Endpoint Claim Readiness

This report separates EIS scalar endpoint predictability from EIS-as-input improvement claims.

| Target | Split | L0 condition MAE | HGB condition MAE | HGB gain | Status |
|---|---|---:|---:|---:|---|
| `delta_eis_z_abs_1kHz` | `c_rate_holdout_fold` | 0.00176185 | 0.00106538 | 0.000696469 | `supported_for_diagnostics` |
| `delta_eis_z_abs_1kHz` | `condition_fold` | 0.000908449 | 0.000615764 | 0.000292685 | `supported_for_diagnostics` |
| `delta_eis_z_abs_1kHz` | `profile_holdout_fold` | 0.000491252 | 0.00131169 | -0.00082044 | `not_supported` |
| `delta_eis_z_abs_1kHz` | `temperature_holdout_fold` | 0.000507265 | 0.000407831 | 9.94339e-05 | `supported_for_diagnostics` |
| `delta_eis_z_abs_1kHz` | `voltage_window_holdout_fold` | 9.10734e-05 | 0.00173252 | -0.00164145 | `not_supported` |
| `delta_nyquist_semicircle_width_proxy` | `c_rate_holdout_fold` | 0.00201584 | 0.00137558 | 0.000640265 | `supported_for_diagnostics` |
| `delta_nyquist_semicircle_width_proxy` | `condition_fold` | 0.00107363 | 0.000720997 | 0.000352628 | `supported_for_diagnostics` |
| `delta_nyquist_semicircle_width_proxy` | `profile_holdout_fold` | 0.000710408 | 0.00235919 | -0.00164878 | `not_supported` |
| `delta_nyquist_semicircle_width_proxy` | `temperature_holdout_fold` | 0.000698641 | 0.000460025 | 0.000238616 | `supported_for_diagnostics` |
| `delta_nyquist_semicircle_width_proxy` | `voltage_window_holdout_fold` | 0.000249219 | 0.0056645 | -0.00541528 | `not_supported` |
| `eis_z_abs_1kHz_k1` | `c_rate_holdout_fold` | 0.00176185 | 0.00109892 | 0.000662936 | `supported_for_diagnostics` |
| `eis_z_abs_1kHz_k1` | `condition_fold` | 0.000908449 | 0.000714651 | 0.000193798 | `supported_for_diagnostics` |
| `eis_z_abs_1kHz_k1` | `profile_holdout_fold` | 0.000491252 | 0.000814774 | -0.000323523 | `not_supported` |
| `eis_z_abs_1kHz_k1` | `temperature_holdout_fold` | 0.000507265 | 0.000498995 | 8.26998e-06 | `supported_for_diagnostics` |
| `eis_z_abs_1kHz_k1` | `voltage_window_holdout_fold` | 9.10734e-05 | 0.000692378 | -0.000601304 | `not_supported` |
| `nyquist_semicircle_width_proxy_k1` | `c_rate_holdout_fold` | 0.00201584 | 0.00122351 | 0.000792337 | `supported_for_diagnostics` |
| `nyquist_semicircle_width_proxy_k1` | `condition_fold` | 0.00107363 | 0.00071977 | 0.000353855 | `supported_for_diagnostics` |
| `nyquist_semicircle_width_proxy_k1` | `profile_holdout_fold` | 0.000710408 | 0.000879807 | -0.0001694 | `not_supported` |
| `nyquist_semicircle_width_proxy_k1` | `temperature_holdout_fold` | 0.000698641 | 0.000527311 | 0.00017133 | `supported_for_diagnostics` |
| `nyquist_semicircle_width_proxy_k1` | `voltage_window_holdout_fold` | 0.000249219 | 0.00217576 | -0.00192654 | `not_supported` |

Decision: EIS scalar endpoints are supported for diagnostics when HGB improves over persistence under grouped splits. This does not authorize EIS predictive improvement claims for capacity or PULSE.
