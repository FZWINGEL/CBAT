# C-Rate Repair Boundary Decision

## Scope

This gate tests whether the existing non-neural C-rate repair diagnostics transfer from `delta_capacity_Ah` to `capacity_Ah_k1`. It consumes existing grouped reports and prediction artifacts. It does not train a new model, add features, recommend policies, calibrate risk, or make causal claims.

## Target Boundary Matrix

| Method | Target | Gain vs F4 | Gain vs stress | p05 vs F4 | p05 vs stress | Outside degradation | Leakage | Passes |
|---|---|---:|---:|---:|---:|---:|---|---|
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | -0.00527031 | -0.00801457 | -0.0166214 | -0.0161765 | 0.0102366 | `passed` | `False` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | 0 |  | 0 |  | 0 | `passed` | `False` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | 0.0200436 | 0.0214266 | 0.00749857 | 0.00465696 | 0.0279117 | `passed` | `True` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | 0.0106361 |  | 0.00594397 |  | 0 | `passed` | `True` |

## Split Guardrail

- Split guardrail rows: `20`
- Support-stratified gain rows: `6`

## Decision

- C-rate delta repair boundary: `supported_for_diagnostics`
- Capacity-level transfer boundary: `not_supported`
- Two-target C-rate repair wording: `not_supported`
- Support-stratified repair context: `diagnostic_only`
- Architecture/policy/calibration/causality: `blocked`

The decision remains claim-gated. Passing `delta_capacity_Ah` does not by itself authorize capacity-level, broad robust-capacity, policy, architecture, calibrated-risk, calibrated-uncertainty, neural/sequence, CBAT, or causal wording.
