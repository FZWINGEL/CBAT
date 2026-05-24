# Threshold-Warning Probability Calibration Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Raw HGB W2 probabilities calibrated | `not_supported` | Raw probabilities are the diagnostic reference, not a calibrated-risk claim. |
| Platt calibration | `partially_supported` | Method result is summarized below. |
| Isotonic calibration | `partially_supported` | Method result is summarized below. |
| Grouped probability calibration | `not_supported` | Strict passing method: `None`. |
| C-rate calibration | `not_supported` | C-rate must pass ECE <= 0.10 for the primary horizon. |
| Calibrated risk | `not_supported` | A calibrated-risk diagnostic requires all-row and verified-only ECE gains, no material Brier/log-loss degradation, C-rate ECE <= 0.10, and no leakage. |
| Detector-knee prediction | `blocked` | Detector-knee labels remain unstable. |
| Policy ranking | `blocked` | No intervention or ranking task is tested. |

## Primary-Horizon Method Summary

| Method | Label policy | Raw ECE | Method ECE | ECE gain | Brier gain | Log-loss gain | Passes ECE | Brier guardrail | Log-loss guardrail |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| `C1_platt_logistic` | `all_rows` | `0.065169` | `0.0607504` | `0.00441857` | `0.00230842` | `0.0276846` | `True` | `True` | `True` |
| `C1_platt_logistic` | `verified_only` | `0.0973711` | `0.0749807` | `0.0223904` | `0.0150357` | `0.0804388` | `True` | `True` | `True` |
| `C2_isotonic` | `all_rows` | `0.065169` | `0.0562111` | `0.00895786` | `0.00382006` | `-0.128242` | `True` | `True` | `False` |
| `C2_isotonic` | `verified_only` | `0.0973711` | `0.0725802` | `0.0247909` | `0.0157882` | `-0.0559272` | `True` | `True` | `False` |

Allowed wording must stay tied to grouped threshold-warning probability calibration diagnostics.
Forbidden wording: policy ranking, causal early-warning claims, detector-knee prediction, CBAT validation, or broad calibrated-risk claims outside the tested target and splits.
