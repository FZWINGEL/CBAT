# C-Rate Repair Feasibility Decision

## Scope

This gate synthesizes existing C-rate root-cause diagnostics with existing train-only non-neural repair artifacts. It does not train a new model, add features, recommend policies, or make causal claims.

## Evidence Matrix

| Evidence area | Status | Metric | Value | Paired p05 | Outside degradation | Passes |
|---|---|---|---:|---:|---:|---|
| c_rate_root_cause | `supported_for_diagnostics` | condition_hotspot_rows | 336 |  |  | `True` |
| train_only_support_overlap | `supported_for_diagnostics` | support_overlap_rows | 76 |  |  | `True` |
| adaptive_conservative_repair | `supported_for_diagnostics` | min_c_rate_gain_vs_stress_reference | 0.0214266 | 0.00465696 | 0.0279117 | `True` |
| targeted_stressor_family_router | `supported_for_diagnostics` | c_rate_gain_vs_d0_f4 | 0.0106361 | 0.00594397 | 0 | `True` |

## Support Context

- C-rate support rows: `76`
- Low-support rows: `52`
- Low-support fraction: `0.684211`
- Median support score: `0.400294`

## Decision

- C-rate diagnosis: `supported_for_diagnostics`
- Adaptive C-rate delta repair: `supported_for_diagnostics`
- Targeted stressor-family routing: `supported_for_diagnostics`
- Broad robust capacity: `not_supported`
- Architecture/policy/calibration/causality: `blocked`

The narrow supported wording is limited to diagnostic C-rate `delta_capacity_Ah` repair with train-only non-neural selection and targeted routing. It does not authorize broad robust-capacity wording, solved C-rate fade, CBAT, policy ranking, calibrated risk, calibrated uncertainty, neural/sequence branches, or causal claims.
