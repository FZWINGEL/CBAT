# Diagnostic-Horizon Claim Readiness

This gate forecasts future PULSE/EIS scalar diagnostic endpoints. It does not use future diagnostic values as features.

| Claim area | Status | Evidence |
|---|---|---|
| Diagnostic endpoint forecasting | `partially_supported` | DH3 must beat persistence and capacity-state references on primary horizon-2/3 rows by at least 10% and avoid C-rate collapse. |
| Primary reference gains | `not_supported` | `21/24` primary rows pass the 10% gain rule; best relative gain `0.465846087624688`, minimum `-0.14707080358918656`. |
| C-rate non-collapse | `not_supported` | `22/24` C-rate rows have non-negative gain; best relative gain `0.5218213829914101`, minimum gain `-5.13632984596858e-05`. |
| Leakage audit | `passed` | Feature groups exclude future diagnostic values and diagnostic deltas. |
| CBAT architecture | `blocked` | Not tested. |
| Policy ranking | `blocked` | Not tested. |
| Calibrated risk or uncertainty | `blocked` | Not tested. |

Allowed wording must stay limited to non-neural diagnostic endpoint forecasting under grouped validation.
