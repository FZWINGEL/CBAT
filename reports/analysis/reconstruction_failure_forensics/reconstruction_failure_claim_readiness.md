# Reconstruction Failure Claim Readiness

| Claim area | Status | Evidence | Allowed wording | Forbidden wording |
|---|---|---|---|---|
| outside-split failure attribution | `supported_for_diagnostics` | 2 outside-split direct-reference reconstruction comparisons fail the 5pct guardrail. | Use the split and condition forensics to explain why capacity-from-delta transfer remains blocked. | Forensics repair the capacity-level transfer result. |
| narrow QA artifact explanation | `diagnostic_only` | Most degrading hotspots carry severe trajectory or LOG_AGE monotonicity flags. | QA flags may contextualize individual hotspots. | The failed guardrail can be ignored as a QA artifact. |
| support-limited explanation | `not_supported` | Support overlap was not available for enough degrading outside-split hotspots. | Support context can be reported as diagnostic when available. | Support limitation authorizes capacity-level repair or policy ranking. |
| capacity-level reconstruction branch | `blocked` | Capacity-from-delta fails outside-split direct-reference non-degradation; the branch should close unless a future data-quality correction gate is explicitly opened. | Close the capacity-level C-rate repair branch for current evidence. | The delta repair can be broadened to capacity_Ah_k1. |
| architecture, policy, calibration, sequence, neural, and causality | `blocked` | This gate is report-only failure forensics over existing non-neural predictions. | CBAT, neural/sequence models, policy ranking, calibrated risk/uncertainty, and causal claims remain blocked. | Failure forensics authorize architecture, policy, calibrated risk, uncertainty, or causal claims. |
