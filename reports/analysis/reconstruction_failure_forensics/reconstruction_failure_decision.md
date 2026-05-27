# Reconstruction Failure Decision

## Scope

This report explains the Milestone 8.7 outside-split failure for capacity-from-delta reconstruction. It consumes existing non-neural prediction artifacts and interval metadata only. It does not train a model, tune a repair, add features, calibrate probabilities, recommend policies, or make causal claims.

## Summary

- Decision scope: `capacity_reconstruction_branch_closed_broad_outside_failure`
- Failing outside comparisons: `2`
- Failing split names: `profile_holdout_fold, voltage_window_holdout_fold`
- Degrading hotspot rows: `58`
- Max outside relative degradation: `0.344864`

## Outside-Split Direct-Reference Comparisons

| Method | Reference | Split | Candidate MAE | Reference MAE | Relative degradation | Passes |
|---|---|---|---:|---:|---:|---|
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `condition_fold` | 0.0426914 | 0.053869 | -0.207495 | `True` |
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `profile_holdout_fold` | 0.0826929 | 0.084368 | -0.0198548 | `True` |
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `temperature_holdout_fold` | 0.0475732 | 0.0692939 | -0.313457 | `True` |
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `voltage_window_holdout_fold` | 0.123301 | 0.0916827 | 0.344864 | `False` |
| adaptive_R2_F8_conservative | `stress_direct_capacity` | `condition_fold` | 0.0426914 | 0.0534803 | -0.201735 | `True` |
| adaptive_R2_F8_conservative | `stress_direct_capacity` | `profile_holdout_fold` | 0.0826929 | 0.0976022 | -0.152755 | `True` |
| adaptive_R2_F8_conservative | `stress_direct_capacity` | `temperature_holdout_fold` | 0.0475732 | 0.0642676 | -0.259764 | `True` |
| adaptive_R2_F8_conservative | `stress_direct_capacity` | `voltage_window_holdout_fold` | 0.123301 | 0.150631 | -0.181439 | `True` |
| targeted_router_D2_F4 | `F4_direct_capacity` | `condition_fold` | 0.0445674 | 0.053869 | -0.172671 | `True` |
| targeted_router_D2_F4 | `F4_direct_capacity` | `profile_holdout_fold` | 0.109158 | 0.084368 | 0.293828 | `False` |
| targeted_router_D2_F4 | `F4_direct_capacity` | `temperature_holdout_fold` | 0.0485748 | 0.0692939 | -0.299004 | `True` |
| targeted_router_D2_F4 | `F4_direct_capacity` | `voltage_window_holdout_fold` | 0.0816836 | 0.0916827 | -0.109062 | `True` |

## Top Failing Hotspots

| Split | Fold | Condition | Reference | Relative degradation | Candidate MAE | Reference MAE | Severe QA rows |
|---|---:|---:|---|---:|---:|---:|---:|
| profile_holdout_fold | 1 | 71 | `F4_direct_capacity` | 0.883276 | 0.0730144 | 0.0387699 | 19 |
| profile_holdout_fold | 1 | 75 | `F4_direct_capacity` | 0.828854 | 0.0629399 | 0.0344149 | 17 |
| profile_holdout_fold | 1 | 69 | `F4_direct_capacity` | 0.800745 | 0.11157 | 0.0619578 | 22 |
| profile_holdout_fold | 1 | 72 | `F4_direct_capacity` | 0.679626 | 0.0767984 | 0.0457235 | 14 |
| profile_holdout_fold | 1 | 74 | `F4_direct_capacity` | 0.596599 | 0.101141 | 0.063348 | 11 |
| profile_holdout_fold | 1 | 65 | `F4_direct_capacity` | 0.579339 | 0.17749 | 0.112383 | 18 |
| profile_holdout_fold | 1 | 68 | `F4_direct_capacity` | 0.561967 | 0.115389 | 0.0738741 | 26 |
| profile_holdout_fold | 1 | 66 | `F4_direct_capacity` | 0.436954 | 0.133082 | 0.0926139 | 27 |
| voltage_window_holdout_fold | 2 | 62 | `F4_direct_capacity` | 7.52765 | 0.180326 | 0.0211461 | 17 |
| voltage_window_holdout_fold | 3 | 14 | `F4_direct_capacity` | 7.39321 | 0.150335 | 0.0179115 | 19 |
| voltage_window_holdout_fold | 3 | 10 | `F4_direct_capacity` | 4.90741 | 0.181836 | 0.0307809 | 26 |
| voltage_window_holdout_fold | 2 | 50 | `F4_direct_capacity` | 4.8405 | 0.198086 | 0.0339159 | 22 |

## Path Error Decomposition

| Method | Reference | Split | Candidate MAE | Reference MAE | Candidate bias | Reference bias |
|---|---|---|---:|---:|---:|---:|
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `c_rate_holdout_fold` | 0.0810892 | 0.125186 | 0.0331181 | 0.105296 |
| adaptive_R2_F8_conservative | `F4_direct_capacity` | `voltage_window_holdout_fold` | 0.123301 | 0.0916827 | -0.0588111 | -0.00748263 |
| adaptive_R2_F8_conservative | `stress_direct_capacity` | `c_rate_holdout_fold` | 0.0810892 | 0.122442 | 0.0331181 | 0.104241 |
| targeted_router_D2_F4 | `F4_direct_capacity` | `c_rate_holdout_fold` | 0.0904967 | 0.125186 | 0.0419459 | 0.105296 |
| targeted_router_D2_F4 | `F4_direct_capacity` | `profile_holdout_fold` | 0.109158 | 0.084368 | -0.0675743 | -0.0325559 |

## Claim Readiness

| Claim area | Status |
|---|---|
| outside-split failure attribution | `supported_for_diagnostics` |
| narrow QA artifact explanation | `diagnostic_only` |
| support-limited explanation | `not_supported` |
| capacity-level reconstruction branch | `blocked` |
| architecture, policy, calibration, sequence, neural, and causality | `blocked` |

## Decision

The current evidence closes the capacity-level reconstruction repair branch unless a future, explicit data-quality correction gate finds a narrow extraction or labeling artifact. The narrow `delta_capacity_Ah` repair remains diagnostic-only; two-target C-rate repair, broad robust capacity, solved C-rate fade, CBAT, neural/sequence models, policy ranking, calibrated risk/uncertainty, and causal claims remain blocked.
