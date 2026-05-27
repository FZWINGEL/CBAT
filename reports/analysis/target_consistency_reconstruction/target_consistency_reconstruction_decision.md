# Target-Consistency Reconstruction Decision

## Scope

This gate tests whether existing C-rate `delta_capacity_Ah` repair predictions can be translated into `capacity_Ah_k1` by adding the predicted delta to observed check-up-k capacity. It consumes existing prediction artifacts and does not train a new model, add features, recommend policies, calibrate risk, or make causal claims.

## C-Rate Reconstruction Gain Rows

| Method | Eval target | Candidate path | Reference | Gain | p05 | Passes |
|---|---|---|---|---:|---:|---|
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `F4_capacity_from_delta` | 0.0200436 | 0.00749857 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `F4_direct_capacity` | 0.0440972 | 0.0207746 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `stress_capacity_from_delta` | 0.0214266 | 0.00465696 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `stress_direct_capacity` | 0.041353 | 0.0206205 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `direct_capacity` | `F4_capacity_from_delta` | -0.0293239 | -0.0512436 | `False` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `direct_capacity` | `F4_direct_capacity` | -0.00527031 | -0.0166214 | `False` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `direct_capacity` | `stress_capacity_from_delta` | -0.0279409 | -0.0424329 | `False` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `direct_capacity` | `stress_direct_capacity` | -0.00801457 | -0.0161765 | `False` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `capacity_from_delta` | `F4_capacity_from_delta` | 0.0106361 | 0.00594397 | `True` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `capacity_from_delta` | `F4_direct_capacity` | 0.0346897 | 0.0120686 | `True` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `direct_capacity` | `F4_capacity_from_delta` | -0.0240536 | -0.0479568 | `False` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `direct_capacity` | `F4_direct_capacity` | 0 | 0 | `False` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | `delta_from_capacity` | `F4_direct_delta` | -0.0293239 | -0.0512436 | `False` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | `direct_delta` | `F4_direct_delta` | 0.0200436 | 0.00749857 | `True` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | `delta_from_capacity` | `F4_direct_delta` | -0.0240536 | -0.0479568 | `False` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | `direct_delta` | `F4_direct_delta` | 0.0106361 | 0.00594397 | `True` |

## Outside-Split Guardrail

| Method | Eval target | Candidate path | Reference | Max degradation | Passes |
|---|---|---|---|---:|---|
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `outside_direct_reference` | -0.152755 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `capacity_from_delta` | `outside_derived_reference` | 0.0252769 | `True` |
| adaptive_R2_F8_conservative | `capacity_Ah_k1` | `direct_capacity` | `outside_direct_reference` | 0.0102366 | `True` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `capacity_from_delta` | `outside_direct_reference` | 0.293828 | `False` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `capacity_from_delta` | `outside_derived_reference` | 0 | `True` |
| targeted_router_D2_F4 | `capacity_Ah_k1` | `direct_capacity` | `outside_direct_reference` | 0 | `True` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | `delta_from_capacity` | `outside_direct_reference` | 0.333619 | `False` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | `delta_from_capacity` | `outside_derived_reference` | 0.0102366 | `True` |
| adaptive_R2_F8_conservative | `delta_capacity_Ah` | `direct_delta` | `outside_direct_reference` | 0.0252769 | `True` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | `delta_from_capacity` | `outside_direct_reference` | 0.426541 | `False` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | `delta_from_capacity` | `outside_derived_reference` | 0 | `True` |
| targeted_router_D2_F4 | `delta_capacity_Ah` | `direct_delta` | `outside_direct_reference` | 0 | `True` |

## Decision

- Delta target-path consistency: `supported_for_diagnostics`
- Capacity-from-delta transfer versus direct references: `not_supported`
- Capacity-from-delta transfer versus derived references: `diagnostic_only`
- Two-target C-rate repair wording: `not_supported`
- Architecture/policy/calibration/causality: `blocked`

The decision remains claim-gated. Derived capacity paths are useful diagnostics, but they do not authorize capacity-level or two-target repair unless they beat the existing direct capacity references under the same grouped guardrails.
