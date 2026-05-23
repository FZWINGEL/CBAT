# Figure 05: LOG_AGE Stress-Feature Decision

Claim supported: C01 partially supported LOG_AGE summaries and C02
not-supported C-rate fade solution.

Source artifact:

- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Intended plot type: two-panel comparison of F4 versus best stress feature row
for C-rate `capacity_Ah_k1` and `delta_capacity_Ah`.

Key numbers:

- `capacity_Ah_k1`: F4 `0.125186`, best stress `0.120605`.
- `delta_capacity_Ah`: F4 `0.101133`, best stress `0.102516`.

Risk/limitation:

- Improvement in level prediction does not transfer to fade-rate prediction.

Caption draft:

> LOG_AGE stress-feature decision. Timestamp-weighted and event-segmented stress
> features improve some views and slightly improve C-rate capacity level, but
> they do not beat F4 on C-rate `delta_capacity_Ah`.
