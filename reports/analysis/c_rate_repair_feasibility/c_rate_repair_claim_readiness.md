# C-Rate Repair Claim Readiness

| Claim area | Status | Evidence | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| C-rate failure and support diagnosis | `supported_for_diagnostics` | C-rate root-cause diagnostics and train-only support overlap are present. | C-rate failures can be localized to held-out condition/support regimes. | Support diagnostics prove out-of-distribution reliability. |
| train-only adaptive C-rate delta repair | `supported_for_diagnostics` | min gain vs F4 `0.0200436`, min gain vs stress `0.0214266`, paired p05 floors `0.00749857`/`0.00465696`, outside degradation `0.0279117`, leakage `passed`. | A narrow non-neural train-only adaptive selector improves C-rate delta capacity diagnostics. | C-rate fade is solved globally. |
| targeted stressor-family routing | `supported_for_diagnostics` | C-rate gain `0.0106361`, paired p05 `0.00594397`, outside degradation `0`, leakage `passed`. | A targeted report-based router preserves the C-rate delta diagnostic gain without outside-split degradation. | The router is a deployable policy recommendation system. |
| broad robust capacity | `not_supported` | The repair evidence is scoped to C-rate delta capacity and does not solve capacity level, all targets, or all stressor views. | Broad robust-capacity wording remains unsupported. | The benchmark now has a globally robust capacity model. |
| architecture, policy, calibration, and causality | `blocked` | This finalization consumes existing non-neural reports and adds no calibrated-risk, policy, causal, neural, sequence, or CBAT evidence. | CBAT, policy ranking, calibrated risk/uncertainty, causal claims, and broad sequence/neural branches remain blocked. | The repair gate authorizes CBAT, policy ranking, causal effects, or calibrated risk. |
