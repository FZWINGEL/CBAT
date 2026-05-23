# EIS Claim Readiness

Milestone 2.0 opens EIS as a QA and feature-readiness data product only. It does not authorize EIS predictive modeling or EIS improvement claims.

| Claim area | Status | Evidence |
|---|---|---|
| EIS archive/cell coverage | `supported_for_qa` | 228 cells |
| Valid-frequency mask | `supported_for_qa` | 0.5-5000 Hz with 100 Hz, 208.3 Hz, and 14.7 kHz excluded |
| SOC/RT-OT coverage | `supported_for_qa` | SOC counts {'10': 7874, '30': 7874, '50': 7874, '70': 7871, '90': 7875} and temperature counts {'OT': 19457, 'RT': 19911} |
| Alignment robustness | `diagnostic_only` | Alignment sensitivity is quantified before any EIS baseline. |
| Feature table completeness | `supported_for_qa` | 3983 canonical rows |
| R0/R1 leakage safety | `diagnostic_only` | R0/R1 are unavailable in the v1 feature sidecar and remain blocked as predictive inputs until provenance is explicit. |
| DRT readiness | `blocked` | DRT remains blocked by policy. |
| Learned embedding readiness | `blocked` | Learned EIS embeddings remain blocked by policy. |
| EIS predictive claim status | `blocked` | No EIS predictive claim is authorized until grouped baseline evidence exists. |

## Blocked Claims

- EIS improves capacity, PULSE, calibration, ranking, or degradation prediction.
- DRT features are stable enough for modeling.
- Learned EIS embeddings are ready.
- Capacity+PULSE+EIS multimodal modeling is authorized.
