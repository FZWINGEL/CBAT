# Diagnostic-Horizon Failure Forensics

This report explains the Milestone 8.2 partial result using existing diagnostic-horizon artifacts only.

## Inputs

- Metric rows: `2880`
- Prediction rows: `2176320`

## Gate Summary

- Primary 10% gain rows passed: `21/24`
- C-rate non-collapse rows passed: `22/24`
- Architecture, calibrated risk, policy, causal, same-cell counterfactual, and CBAT claims remain blocked.

## Weakest Primary Rows

| Target | Horizon | Reference | Relative gain | Gain | Reason |
|---|---:|---|---:|---:|---|
| `nyquist_im_peak_abs` | `3` | `persistence` | `-0.14707080358918656` | `-3.043879415699476e-05` | `primary_gain_below_10pct` |
| `nyquist_im_peak_abs` | `2` | `persistence` | `-0.10531507242033532` | `-1.9743915025291855e-05` | `primary_gain_below_10pct` |
| `eis_phase_1kHz` | `2` | `persistence` | `0.096622745123255` | `0.03471872895511635` | `primary_gain_below_10pct` |
| `eis_phase_1kHz` | `3` | `persistence` | `0.10042786814361278` | `0.03710340039183868` | `passes_gate_row` |
| `pulse_10ms_resistance` | `3` | `capacity_state` | `0.1818721737670873` | `0.0002455148084946719` | `passes_gate_row` |

## Weakest C-Rate Rows

| Target | Horizon | Reference | Relative gain | Gain | Reason |
|---|---:|---|---:|---:|---|
| `pulse_1s_resistance` | `3` | `capacity_state` | `-0.02443787142756398` | `-5.13632984596858e-05` | `c_rate_negative_gain` |
| `pulse_1s_resistance` | `2` | `capacity_state` | `-0.01852039874061038` | `-4.315098060067796e-05` | `c_rate_negative_gain` |
| `pulse_10ms_resistance` | `3` | `capacity_state` | `0.002871235240601689` | `5.6983411793822165e-06` | `passes_gate_row` |
| `nyquist_im_peak_abs` | `3` | `persistence` | `0.06255803062568312` | `2.2561293741415024e-05` | `passes_gate_row` |
| `eis_z_abs_1kHz` | `3` | `capacity_state` | `0.028470216230741367` | `4.3843839466467483e-05` | `passes_gate_row` |

## Strongest Capacity-State Gains

| Target | Horizon | Mean relative gain | Positive rows |
|---|---:|---:|---:|
| `eis_z_abs_1kHz` | `1` | `0.5806821583360975` | `1/1` |
| `nyquist_im_peak_abs` | `1` | `0.5465075039654073` | `1/1` |
| `nyquist_im_peak_abs` | `2` | `0.465846087624688` | `1/1` |
| `nyquist_im_peak_abs` | `3` | `0.4061054432999812` | `1/1` |
| `nyquist_semicircle_width_proxy` | `1` | `0.402526949067629` | `1/1` |

## Low-Movement Endpoint Diagnostics

| Target | Horizon | Median abs delta from current | Persistence MAE |
|---|---:|---:|---:|
| `nyquist_im_peak_abs` | `1` | `9.60000000000006e-05` | `0.00015344172467976152` |
| `nyquist_im_peak_abs` | `2` | `0.00010399999999999993` | `0.00018747473245320104` |
| `nyquist_im_peak_abs` | `3` | `0.00011300000000000025` | `0.0002069669398286526` |
| `eis_z_abs_1kHz` | `1` | `0.00011399999999999952` | `0.0004535565272426793` |
| `nyquist_im_peak_abs` | `5` | `0.00013400000000000044` | `0.000242154533630051` |

## Condition Hotspots

| Split | Target | Horizon | Model | Feature | Parameter set | Mean abs error |
|---|---|---:|---|---|---:|---:|
| `temperature_holdout_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH2_prior_same_diagnostic_state` | `23` | `1.7683749163607996` |
| `condition_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH3_capacity_plus_prior_same_diagnostic` | `23` | `1.7419103443173103` |
| `temperature_holdout_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH3_capacity_plus_prior_same_diagnostic` | `23` | `1.707461684853597` |
| `condition_fold` | `eis_phase_1kHz` | `2` | `DM0_persistence` | `persistence` | `23` | `1.676` |
| `temperature_holdout_fold` | `eis_phase_1kHz` | `2` | `DM0_persistence` | `persistence` | `23` | `1.676` |
| `voltage_window_holdout_fold` | `eis_phase_1kHz` | `2` | `DM0_persistence` | `persistence` | `23` | `1.676` |
| `c_rate_holdout_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH1_capacity_state` | `36` | `1.6487497865140002` |
| `condition_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH2_prior_same_diagnostic_state` | `23` | `1.5974204737659055` |
| `temperature_holdout_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH1_capacity_state` | `23` | `1.582015403396998` |
| `c_rate_holdout_fold` | `eis_phase_1kHz` | `2` | `DM3_hist_gradient_boosting` | `DH3_capacity_plus_prior_same_diagnostic` | `36` | `1.5467033969650699` |

Decision: the Milestone 8.2 result remains partial diagnostic endpoint evidence. Do not broaden to architecture or calibrated-risk wording.
