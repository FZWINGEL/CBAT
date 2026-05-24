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

| Method | Label policy | Raw fixed ECE | Method fixed ECE | Fixed ECE gain | Raw equal-freq ECE | Method equal-freq ECE | Equal-freq ECE gain | Brier gain | Log-loss gain | Evaluated rows | Fallback rows | Passes fixed ECE | Brier guardrail | Log-loss guardrail |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `C1_platt_logistic` | `all_rows` | `0.065169` | `0.0606585` | `0.00451044` | `0.0627156` | `0.0617218` | `0.000993801` | `0.00225542` | `0.0268082` | `12` | `0` | `True` | `True` | `True` |
| `C1_platt_logistic` | `verified_only` | `0.0973711` | `0.0748136` | `0.0225575` | `0.090753` | `0.0729286` | `0.0178244` | `0.0149813` | `0.08008` | `12` | `0` | `True` | `True` | `True` |
| `C2_isotonic` | `all_rows` | `0.065169` | `0.0562111` | `0.00895786` | `0.0627156` | `0.0565418` | `0.00617374` | `0.00382006` | `-0.128242` | `12` | `0` | `True` | `True` | `False` |
| `C2_isotonic` | `verified_only` | `0.0973711` | `0.0725802` | `0.0247909` | `0.090753` | `0.0706746` | `0.0200784` | `0.0157882` | `-0.0559272` | `12` | `0` | `True` | `True` | `False` |

## Required C-Rate Policy Summary

| Method | Label policy | Fixed-width ECE | Equal-frequency ECE | Brier | Evaluated rows | Fallback rows | Passes fixed ECE | No fallback |
|---|---|---:|---:|---:|---:|---:|---|---|
| `C1_platt_logistic` | `all_rows` | `0.208801` | `0.211407` | `0.174222` | `1` | `0` | `False` | `True` |
| `C1_platt_logistic` | `verified_only` | `0.167653` | `0.176185` | `0.148704` | `1` | `0` | `False` | `True` |
| `C2_isotonic` | `all_rows` | `0.192354` | `0.186487` | `0.163916` | `1` | `0` | `False` | `True` |
| `C2_isotonic` | `verified_only` | `0.159021` | `0.159021` | `0.147795` | `1` | `0` | `False` | `True` |

Allowed wording must stay tied to grouped threshold-warning probability calibration diagnostics.
Forbidden wording: policy ranking, causal early-warning claims, detector-knee prediction, CBAT validation, or broad calibrated-risk claims outside the tested target and splits.
