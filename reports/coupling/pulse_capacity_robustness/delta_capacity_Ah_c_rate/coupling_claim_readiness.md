# Capacity-PULSE Coupling Claim Readiness

| Claim area | Status | Evidence | Decision |
|---|---|---|---|
| Interval-level association | supported_for_explanatory_diagnostics | Spearman `0.646779` over `143` intervals | Explanatory diagnostic only |
| Condition-level association | supported_for_explanatory_diagnostics | Spearman `0.881119` over `12` conditions | Do not inflate prediction-row evidence |
| C-rate/cold-rate association | supported_for_explanatory_diagnostics | C-rate Spearman `0.646779`, cold C-rate Spearman `0.58661` | Keep subgroup diagnostics |
| Confound-controlled association | partially_supported | Residualized Spearman `0.44761` | Diagnostic, not causal evidence |
| Prior-PULSE capacity gain | partially_supported | Prior PULSE helps `capacity_Ah_k1` in 0.8 but not C-rate `delta_capacity_Ah` | Predictive claim not authorized |
| Leakage safety | supported_for_explanatory_diagnostics | Capacity feature groups allow `pulse_1s_resistance_k` only | Future PULSE targets remain blocked |
| Coverage limitation | partially_supported | PULSE-covered capacity rows drop one tolerant interval versus capacity-only | Report coverage in any follow-up |
| Predictive claim readiness | predictive_claim_not_authorized | Coupling remains diagnostic and delta target is unresolved | No broad capacity+PULSE claim |
