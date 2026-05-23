# Table 5. Negative Results

# Negative Results

Milestone 1.0 treats negative results as first-class evidence. These results
block overclaims and define the next scientific boundary.

## LOG_AGE Stress Features Did Not Solve C-Rate Delta

Milestone 0.6 and 0.6.1 added voltage, temperature, SOC, current, coupled
stress, timestamp-weighted dwell, and event-segmented scalar features. The
best v1.1 C-rate `capacity_Ah_k1` row improved from the F4 baseline `0.125186`
to `0.120605`, but the best stress row for C-rate `delta_capacity_Ah` was
`0.102516`, worse than the F4 threshold `0.101133`.

Decision: do not claim LOG_AGE stress features solve C-rate fade prediction.

## Normalized Delta-Rate Targets Failed

Milestone 0.6.3 trained normalized targets and evaluated them back in
`delta_capacity_Ah` units. The best listed normalized day-rate result was
`0.121271` on C-rate, worse than direct F4 delta at `0.101133`.

Decision: keep direct `delta_capacity_Ah` as the primary C-rate delta target.

## Train-Fold Bias Correction Was Neutral

Milestone 0.6.3 fit residual correction only on train rows. It changed the best
C-rate F4 delta result only at numerical-noise scale.

Decision: keep residual correction diagnostic only.

## F11-F13 Cold/Current Groups Did Not Beat F4

Narrow C-rate groups did not beat F4 or F8 on C-rate `delta_capacity_Ah`.
Representative C-rate condition-mean MAE values:

| Feature group | C-rate `delta_capacity_Ah` MAE |
|---|---:|
| `F4_state_log_age_scalar` | `0.101133` |
| `F8_timestamp_weighted_stress` | `0.102516` |
| `F13_sparse_c_rate_context` | `0.147452` |
| `F11_minimal_cold_current` | `0.149436` |
| `F12_voltage_cold_current_interactions` | `0.162640` |

Decision: stop broad LOG_AGE-only scalar stress-feature expansion unless a
concrete bug is found.

## Prior PULSE Did Not Beat Strongest Non-PULSE

Milestone 0.9 showed prior PULSE improves `capacity_Ah_k1` over F4 in selected
splits. Milestone 0.9.1 compared the same prior-PULSE groups against the
strongest supplied non-PULSE HGB baselines and did not support the stronger
claim.

Representative paired gains:

| Target | Split | Mean gain vs strongest non-PULSE | p05 |
|---|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `0.000392605` | `-0.00553843` |
| `capacity_Ah_k1` | temperature | `-0.000753049` | `-0.00294184` |
| `capacity_Ah_k1` | profile | `-0.000697582` | `-0.00281975` |

Decision: claim only prior-PULSE improvement over F4 in selected splits, not
best-available-model superiority.

## Prior PULSE Did Not Improve C-Rate Fade Rate

Against F4, C-rate `delta_capacity_Ah` gain was `-0.00574230`. Against the
strongest supplied non-PULSE baseline, C-rate `delta_capacity_Ah` gain was
`-0.00234428` with p05 `-0.0169742`.

Decision: no fade-rate claim for prior PULSE.

## Quantile HGB Was Not Calibrated

The focused HGB-50 q10-q90 coverage was about `0.678207`, below the nominal
central 0.8 interval.

Decision: quantile predictions remain diagnostics only; no uncertainty claim.

## EIS Is Not Tested Yet

EIS ingestion exists, but valid-frequency masks, spectrum QA, and predictive
tests are still gated.

Decision: no EIS improvement claim and no EIS modeling until an EIS QA gate is
opened and passed.
