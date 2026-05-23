# EIS Prior Feature Claim Readiness

Milestone 2.1 evaluates RT/50 scalar EIS features as diagnostic baselines and as
prior-state features for PULSE and capacity. This memo is not an EIS improvement
claim; it records whether the first scalar checks justify later claim-hardening.

| Claim area | Status | Evidence | Decision |
|---|---|---|---|
| EIS scalar endpoint predictability | `supported_for_diagnostics` | `delta_eis_z_abs_1kHz` best condition-fold condition-mean MAE is `0.000307288`; C-rate best is `0.000999892`. | EIS scalar endpoints are usable for grouped diagnostic baselines. |
| EIS selected-frequency feature availability | `partially_supported` | Target QA has 3,821 intervals with finite prior EIS and 3,744 finite EIS delta rows; feature QA still reports small selected-frequency missingness. | Report missingness with every EIS result. |
| EIS alignment robustness | `diagnostic_only` | Milestone 2.0 alignment deltas remain large; 2.1 does not filter by alignment threshold. | Keep alignment sensitivity visible before any headline claim. |
| Prior EIS helps PULSE resistance | `partially_supported` | Prior-EIS groups win temperature, profile, and voltage-window PULSE splits; non-EIS groups still win condition and C-rate. | EIS-to-PULSE signal is split-dependent and needs paired strongest-baseline testing. |
| Prior EIS helps capacity level | `partially_supported` | Prior-EIS groups win condition, temperature, profile, and voltage-window `capacity_Ah_k1`; non-EIS F8 wins C-rate. | Potential capacity-level signal, but no broad claim. |
| Prior EIS helps capacity fade-rate | `partially_supported` | Prior-EIS groups win profile, temperature, and voltage-window `delta_capacity_Ah`; F4/F8 win C-rate and condition. | Fade-rate claim remains blocked, especially for C-rate. |
| Leakage safety | `supported_for_diagnostics` | Feature groups use prior EIS `k` fields only; future EIS `k1`, EIS deltas, R0/R1, DRT, and embedding fields are blocked. | Keep leakage audit mandatory for future runs. |
| EIS predictive claim status | `not_authorized` | No paired strongest-non-EIS bootstrap or alignment-threshold robustness has been run for EIS feature gains. | Do not claim EIS improves non-EIS outcomes yet. |

## Blocked Claims

- EIS improves capacity prediction.
- EIS improves PULSE resistance prediction broadly.
- EIS improves `delta_capacity_Ah` or solves C-rate fade prediction.
- EIS scalar features beat the strongest non-EIS baseline.
- DRT or learned EIS embeddings are ready.
- Capacity+PULSE+EIS multimodal modeling is authorized.
