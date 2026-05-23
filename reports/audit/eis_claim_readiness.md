# EIS Claim Readiness

Milestones 2.0-2.1.1 open EIS as a QA, scalar endpoint, and claim-hardening data product. EIS predictive modeling claims remain blocked unless strongest-baseline, bootstrap, alignment, feature-completeness, and leakage checks support a narrow split-specific statement.

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
| EIS scalar endpoint status | `supported_for_diagnostics` | HGB improves over persistence for several scalar EIS endpoint/split rows; see `reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md`. |
| Prior EIS to PULSE status | `split_specific_diagnostic_only` | Prior EIS beats strongest non-EIS only for PULSE profile holdout with bootstrap p05 > 0; C-rate is negative. |
| Prior EIS to capacity status | `split_specific_diagnostic_only` | Prior EIS beats strongest non-EIS for profile-holdout `capacity_Ah_k1`; C-rate capacity level and C-rate `delta_capacity_Ah` remain unsupported. |
| EIS predictive claim status | `blocked_broad_claims` | No broad EIS improvement claim is authorized. Only narrow, split-specific diagnostics can be discussed from 2.1.1. |

## Blocked Claims

- EIS improves capacity, PULSE, calibration, ranking, or degradation prediction.
- EIS improves C-rate capacity prediction.
- EIS improves `delta_capacity_Ah` or fade-rate prediction.
- DRT features are stable enough for modeling.
- Learned EIS embeddings are ready.
- Capacity+PULSE+EIS multimodal modeling is authorized.
