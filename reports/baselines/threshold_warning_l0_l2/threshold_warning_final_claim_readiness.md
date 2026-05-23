# Threshold-Warning Final Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Threshold-event forecasting diagnostic | `supported_for_diagnostics` | HGB W2 gain vs prior `0.080216` and vs proximity `0.067136`; all-row and verified-only policies pass: `True`. |
| Threshold detection only | `not_supported` | HGB W2 beats the proximity baseline, so the result is not only a current-threshold detector. |
| Early-warning diagnostic | `exploratory_only` | Lead-time bins are reported separately; this wording remains exploratory. |
| C-rate threshold warning | `supported_for_diagnostics` | C-rate HGB W2 gain vs prior `0.247388` and vs proximity `0.195335`. |
| Calibrated risk | `not_supported` | C-rate ECE is `0.174673` and grouped calibration remains claim-gated. |
| Detector-knee prediction | `blocked` | Detector-knee replicate consistency failed in Milestone 2.5. |
| Policy ranking | `blocked` | No intervention or ranking task is tested. |

Censoring counts for `event_within_3_checkups`:

| Label status | Count |
|---|---:|
| `negative_observed` | `1939` |
| `positive_observed` | `494` |
| `right_censored_unknown` | `1394` |

Allowed wording: non-neural baselines can forecast the 80% capacity-relative threshold event diagnostically under grouped validation, including under verified-only sensitivity.
Forbidden wording: calibrated risk, detector-knee prediction, causal early-warning claims, policy ranking, or CBAT validation.
