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

## EIS Did Not Support Broad Improvement Claims

Milestones 2.0, 2.1, and 2.1.1 opened and hardened EIS QA, scalar feature
tables, scalar endpoint baselines, and prior-EIS comparisons. EIS is useful as
a scalar diagnostic endpoint and shows narrow profile-split prior-feature
signals, but C-rate capacity, C-rate PULSE, and `delta_capacity_Ah` remain
unsupported.

Decision: no broad EIS improvement claim and no capacity+PULSE+EIS architecture
work.

## Grouped Calibration Did Not Validate Capacity Uncertainty

Milestone 2.3 showed that conformal methods improve mean interval coverage, but
C-rate coverage remains below target. Stressor-family conformal C-rate coverage
is `0.719745` for `capacity_Ah_k1` and `0.726115` for
`delta_capacity_Ah`.

Decision: no global calibrated capacity-uncertainty claim.

## Event Order Did Not Justify Sequence Models

Milestone 2.4 built a full LOG_AGE-derived run-event table and sequence-feature
sidecar, then compared aggregate event, order-aware, shuffled-order, and
timestamp-weighted stress feature groups under grouped HGB-50 validation.
Order-aware features did not beat aggregate features, shuffled controls, or the
stress baseline overall. C-rate order-aware gain was negative on average.

Decision: sequence models remain blocked.

## Knee Labels Did Not Authorize Prediction

Milestone 2.5 generated knee candidates across seven detectors, three x-axis
choices, and two smoothing policies. The primary piecewise-linear detector
produced valid labels for 189 / 228 cells, and x-axis/smoothing median
disagreement was 0 check-ups. However, replicate-triplet consistency did not
pass: only 45 / 64 primary valid parameter-set conditions were consistent
within 2 check-ups across replicates.

Decision: knee-risk labels remain exploratory and knee prediction remains
blocked.

## Detector knees remain weaker than threshold-event labels

Milestone 2.5.1 diagnosed 19 inconsistent primary-valid knee conditions and
found only 40 / 76 conditions pass the default stable-knee rule. The stable
subset is useful for forensics but too narrow for a detector-knee prediction
claim.

Threshold-event labels are more promising: `capacity_below_80pct_initial`
has replicate consistency within 2 check-ups of 0.897 and condition coverage
of 0.763, with median event check-up 8. This supports a possible future
threshold-event label gate, not a current prediction claim.

## Threshold-event warning does not authorize calibrated risk or policy ranking

Milestones 2.6 through 2.6.2 show a leakage-safe non-neural HGB baseline can
forecast the 80% threshold event diagnostically, including beyond simple
distance-to-threshold baselines and under verified-only censoring sensitivity.
For `event_within_3_checkups`, all-row mean Brier is `0.145791` for the
event-rate prior, `0.132711` for the best proximity baseline, and `0.0655751`
for HGB W2. Verified-only mean Brier is `0.178655` for the prior, `0.168492`
for proximity, and `0.090116` for HGB W2. In the verified-only C-rate holdout,
Brier is `0.377495` for the prior, `0.327879` for the logistic distance
baseline, and `0.153370` for HGB W2.

The hardening pass does not authorize calibrated risk or causal early-warning
wording. The all-row C-rate `event_within_3_checkups` HGB W2 ECE is
`0.174673`, verified-only C-rate ECE is `0.194633`, and the censoring audit
records 1,394 right-censored unknown rows for each horizon.
Future interval exposure, future capacity, PULSE/EIS deltas, and detector knees
remain excluded from the warning feature set.

Milestone 5.0 tested the narrow post-hoc calibration branch directly. Platt
and isotonic calibration improve mean ECE for the primary 3-check-up horizon,
but C-rate ECE remains above the 0.10 guardrail: verified-only C-rate ECE is
`0.167813` for Platt and `0.159021` for isotonic.

Milestone 5.2 adds equal-frequency ECE as a binning-sensitivity check rather
than replacing the fixed-width metric. The primary verified-only Platt row has
fixed-width ECE `0.0749807` and equal-frequency ECE `0.072939`, but the
verified-only C-rate Platt row remains above guardrail with fixed-width ECE
`0.167813` and equal-frequency ECE `0.176461`.

Decision: threshold-event forecasting is supported for diagnostics; calibrated
risk, policy ranking, detector-knee prediction, and causal warning claims
remain blocked.

## Quantile Noncrossing Hygiene Does Not Validate Capacity Uncertainty

Milestone 5.2 also enforces noncrossing q10/q50/q90 endpoints for independent
L3 capacity quantile HGB predictions by row-wise post-sort while preserving the
q50 point prediction. This is interval hygiene, not calibration. The refreshed
capacity calibration report still blocks uncertainty wording: raw q10-q90 mean
coverage is `0.701398`, min coverage is `0.00226244`, and C-rate mean coverage
across calibration methods is `0.72293`.

Decision: keep L3 quantile intervals diagnostic only. Do not claim calibrated
capacity uncertainty.

## Stressor-Robust Training Did Not Lock a Global Robust-Capacity Claim

Milestone 5.1 tested non-neural stressor-axis robust HGB variants over existing
F4/F8 capacity feature groups. The result is useful but still claim-bounded:
`R2_stressor_balanced_hgb` with `F8_timestamp_weighted_stress` improves the
hard C-rate `delta_capacity_Ah` row to condition-mean MAE `0.0705429`, versus
F4 R0 `0.101133` and stress-feature R0 `0.102516`. The paired bootstrap p05 is
positive versus F4 (`0.0216868`) and the stress reference (`0.0165793`).

The global robust-capacity claim remains not supported because the selected
candidate narrowly fails the outside-C-rate non-degradation guardrail: maximum
relative degradation outside C-rate is `0.0528343`, above the 5% threshold,
from the voltage-window delta comparison.

Decision: report the stressor-balanced C-rate improvement as diagnostic
robustness evidence only. Do not claim C-rate fade is solved, do not open
architecture work, and do not use this result for policy ranking or causal
claims.

## Milestone 3.0 Blocked-Claim Refresh

The v2 synthesis keeps the following negative boundaries active:

- detector-knee prediction remains blocked by replicate inconsistency;
- threshold-warning calibrated-risk wording remains unsupported after the
  Milestone 5.0 calibration gate and Milestone 5.2 equal-frequency ECE
  sensitivity;
- stressor-robust HGB improves C-rate delta diagnostically but does not pass
  the global non-degradation guardrail;
- sequence models remain blocked by the order-vs-aggregate and
  order-vs-shuffled negative result;
- calibrated uncertainty remains blocked by C-rate coverage failure even after
  quantile noncrossing hygiene;
- CBAT, policy ranking, causal claims, same-cell counterfactuals, DRT, and
  learned EIS embeddings remain blocked.

Decision: return to synthesis/release maintenance unless a new narrow
calibration-method diagnostic is explicitly justified.
