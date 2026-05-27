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
but C-rate ECE remains above the 0.10 guardrail. Milestone 5.3 hardens this
gate so all-row and verified-only policies are both required, C-rate is checked
per policy, and fallback-raw calibration rows cannot pass strict readiness.
Verified-only C-rate ECE is `0.167653` for Platt and `0.159021` for isotonic.

Milestone 5.2 adds equal-frequency ECE as a binning-sensitivity check rather
than replacing the fixed-width metric. After the Milestone 5.3 Platt
convention and readiness-gate hardening, the primary verified-only Platt row
has fixed-width ECE `0.0748136` and equal-frequency ECE `0.0729286`, but the
verified-only C-rate Platt row remains above guardrail with fixed-width ECE
`0.167653` and equal-frequency ECE `0.176185`.

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

Milestone 5.4 ran the promised forensics/Pareto follow-up without relaxing the
guardrail. The predeclared R2/F8/weight=1.0 setting remains the strongest
C-rate diagnostic row, with C-rate gains `0.0305899` versus F4 and `0.0319729`
versus the stress R0 reference, and paired p05 values above zero. It still
fails the 5% outside-C-rate guardrail at `0.0528343`. Two lighter
non-predeclared frontier settings pass the 5% threshold diagnostically, but
they do not authorize the predeclared robust-capacity claim.

Milestone 5.5 then converted that Pareto signal into a train-only adaptive
selection test. The max-gain selector failed the outer guardrail with max
outside-C-rate degradation `0.0645764`. The conservative selector passed
diagnostically: C-rate gains are `0.0200436` versus F4 and `0.0214266` versus
the stress R0 reference, paired p05 values are positive, and max outside-C-rate
degradation is `0.0279117`.

Milestone 5.6 replicated the conservative adaptive selector across five
logical seeds and recorded deterministic HGB/no-bagging seed reuse explicitly.
All conservative logical seeds pass the same diagnostic guardrail, while the
max-gain selector still fails outside-C-rate non-degradation at `0.0645764`.

Milestone 5.7 decomposed the adaptive result into R0/F4, R0/F8, adaptive
R2/F4, and adaptive R2/F8 arms. Reweighting-only improves C-rate
`delta_capacity_Ah` by `0.0106361` versus R0/F4 with paired p05 `0.00594397`.
Raw F8 does not improve the same row versus F4 (`-0.00138302`). Incremental F8
under adaptive selection does improve C-rate delta by `0.00940756` with paired
p05 `6.06012e-05`, but it fails the outside-C-rate guardrail because maximum
outside-split degradation is `0.717391`.

Milestone 5.8 tested a targeted stressor-family router over existing
attribution arms. It uses D2 adaptive R2/F4 for the C-rate transfer view when
the train-only D2 guardrail passes and D0 R0/F4 for non-C-rate views. This
preserves the reweighting-only C-rate gain (`0.0106361`, paired p05
`0.00594397`) and makes outside-C-rate degradation `0` because non-C-rate
views are intentionally routed to the reference arm.

Decision: report the conservative adaptive selector as a narrow diagnostic
robustness result for `delta_capacity_Ah`. Report F8 stress-feature
attribution as diagnostic-only rather than independently supported. Report the
Milestone 5.8 router only as targeted stressor-family routing, not as a global
robust model. Do not claim C-rate fade is solved, do not open architecture
work, and do not use this result for policy ranking or causal claims.

## Hierarchical Replicate Baselines Did Not Pass the C-Rate Paired-Support Gate

Milestone 5.9 added the charter-required L5-style hierarchical comparator:
global train mean, Ridge, Ridge with train-only stressor-family residual
partial pooling, HGB reference, HGB with train-only residual partial pooling,
and replicate-variance interval diagnostics.

The H4/F4 partial-pooling arm slightly improves C-rate `delta_capacity_Ah`
versus the H3/F4 HGB reference (`0.000100645`) and keeps max outside-C-rate
relative degradation low (`0.00275483`), but the paired condition bootstrap
p05 is negative (`-1.88643e-05`). This fails the predeclared paired-support
requirement for a new hierarchical robustness claim.

The H5 replicate-variance interval diagnostic also fails coverage: C-rate
`delta_capacity_Ah` coverage is `0.312102`, and the minimum primary coverage
across target/split rows is `0.151596`.

Decision: keep hierarchical replicate-aware partial pooling as an L5 diagnostic
comparator. Do not claim C-rate fade is solved, do not claim calibrated
uncertainty, and do not use this as architecture or policy-ranking evidence.

## Multi-Horizon Capacity Forecasting Is Partial, Not Solved

Milestone 6.0 built `capacity_horizon_table_v1.parquet` with 13,770 observed
rows for horizons 1, 2, 3, and 5 check-ups. The C-rate multi-horizon rows are
positive: prospective HGB K2 beats both persistence and prior-slope baselines
for horizons 2 and 3 on both `capacity_Ah_kh` and `delta_capacity_Ah_h`.

The overall capacity-level claim does not fully pass. For horizon-3
`capacity_Ah_kh` across all grouped split rows, HGB K2 mean MAE is `0.0935304`,
slightly worse than the prior-slope baseline at `0.0932329`. This is a near
tie, but it blocks broad multi-horizon capacity-forecasting wording.

K3 oracle exposure diagnostics improve several rows, but those fields aggregate
the actual k-to-k+h exposure and therefore cannot be used as prospective
forecasting inputs.

Decision: report C-rate and delta-capacity multi-horizon forecasting as
diagnostic positives, keep the overall multi-horizon capacity claim partial,
and do not claim solved C-rate fade, architecture readiness, policy ranking,
or prospective value from future exposure fields.

Milestone 6.1 forensics keep this decision unchanged. The C-rate horizon-2/3
rows remain diagnostic positives, but the global result remains partial. The
largest HGB-versus-prior-slope regressions appear in specific prior-state bins,
including late-life and low-SOH cases, and K3 oracle exposure improves many
rows only by using non-prospective k-to-k+h exposure. If technical work
continues, the only defensible branch is a predeclared prior-trajectory-shape
audit using information available at check-up `k`.

## Prior-Trajectory Shape Does Not Repair the Multi-Horizon Gap

Milestone 6.2 built `capacity_horizon_trajectory_features_v1.parquet` with
13,770 prior-only feature rows. QA passed with zero duplicate, missing, or
extra horizon keys and no leakage columns.

The repair gate fails. For all-split horizon-3 `capacity_Ah_kh`, K5
nominal-plus-trajectory HGB has MAE `0.0981241`, worse than both K2
(`0.0935304`) and the prior-slope baseline (`0.0932329`). K5 also fails full
C-rate preservation: it improves C-rate horizon-2 `capacity_Ah_kh` and
horizon-3 `delta_capacity_Ah_h`, but worsens C-rate horizon-3 `capacity_Ah_kh`
and horizon-2 `delta_capacity_Ah_h` relative to K2.

Decision: keep prior-trajectory shape as partial/diagnostic only. Do not claim
that trajectory shape solves multi-horizon forecasting or justifies
sequence/neural models, CBAT, policy ranking, causal claims, calibrated risk,
or calibrated uncertainty.

## Minimal Sequence/Neural Reopening Did Not Pass H7 Controls

Milestone 7.1 built `interval_event_sequence_table_v1.parquet` with 3,827
fixed-length true and shuffled event-sequence rows from the streamed run-event
table. QA passed with no missing intervals, no vector/mask length errors, and
no leakage columns. The WSL GPU environment was verified with PyTorch
`2.12.0+cu130` on the RTX 5060 Ti, and the Torch MLP rows were evaluated on
CUDA.

The scientific gate still fails. True-sequence candidates have positive mean
gain versus shuffled order (`0.0290673`, `26/48` positive rows), but they do
not beat stronger references: mean gain is `-0.227321` versus aggregate-event
HGB (`0/48` positive rows) and `-0.190925` versus timestamp-stress HGB
(`0/44` positive rows). C-rate `delta_capacity_Ah` reopening also fails with
only `1/6` positive comparison rows and mean gain `-0.159493`.

Decision: report Milestone 7.1 as a negative H7 reopening check. GPU execution
worked, but sequence/neural next-gate readiness remains blocked. Do not open
transformers, CBAT, policy ranking, or broad neural architecture work from
this result.

## Supported Contrast Ordering Does Not Authorize Recommendations

Milestone 7.3 joined the 234 triplet-supported observed contrasts from
Milestone 7.2 to existing out-of-fold multi-horizon capacity predictions. It
generated 164,100 pairwise contrast-ordering rows without retraining any
model.

The signal is useful but not decisive. HGB K2 reaches primary
`delta_capacity_Ah_h` sign accuracy of `0.826923` for C-rate horizon 2 and
`0.888889` for C-rate horizon 3, with mean primary sign accuracy `0.780`
across horizon-2/3 split rows. However, the strict bootstrap reference gate
fails: HGB K2 passes `0/10` all-family primary checks against the prior-slope
reference with positive p05. C-rate horizon 2 is negative versus prior slope
(`-0.0740741`, p05 `-0.190476`), and multiple non-C-rate rows are also
negative.

Decision: treat supported contrast ordering as partially supported diagnostic
evidence only. Do not claim policy recommendations, causal effects, same-cell
counterfactuals, calibrated policy risk/utility, CBAT readiness, or sequence
and neural readiness.

## Policy contrast-ordering forensics do not reopen policy ranking

Milestone 7.4 decomposed the Milestone 7.3 failure using existing 7.3 CSV
artifacts only. It added effect-size-thresholded sign accuracy, rank
correlation, top-k/regret diagnostics, and HGB-vs-prior failure bins without
training a model or adding features.

The forensics explain the near miss but do not reverse it. The strict
HGB-vs-prior all-family gate still passes `0/10` checks. Large-effect rows are
only diagnostic: passing contrast families are `charge_c_rate` and
`temperature`, C-rate medium/large pass rows are `1/4`, and HGB `ge_0.02Ah`
mean sign accuracy is `0.856314`. Rank metrics are also diagnostic only.

Decision: keep policy-response modeling blocked. At most, this motivates a
future predeclared large-effect supported-contrast gate if explicitly opened;
it does not authorize recommendation, causal/counterfactual, calibrated
policy-risk, CBAT, or sequence/neural claims.

## Milestone 3.0 Blocked-Claim Refresh

The v2 synthesis keeps the following negative boundaries active:

- detector-knee prediction remains blocked by replicate inconsistency;
- threshold-warning calibrated-risk wording remains unsupported after the
  Milestone 5.0 calibration gate and Milestone 5.2 equal-frequency ECE
  sensitivity;
- conservative train-only stressor-robust HGB improves C-rate delta
  diagnostically, replicates under deterministic seed reuse, and passes the
  outside-split guardrail for `delta_capacity_Ah`, but broad C-rate
  fade-solved and architecture claims remain blocked;
- F8 stress-feature attribution remains diagnostic-only because incremental F8
  under adaptive selection fails outside-C-rate non-degradation despite a
  positive C-rate delta gain;
- stressor-family routing can preserve the C-rate reweighting gain without
  non-C-rate degradation, but this is not a global robust-capacity model;
- hierarchical replicate-aware partial pooling is implemented but diagnostic
  only because paired C-rate support and interval coverage fail;
- multi-horizon capacity forecasting is only partially supported overall,
  despite positive C-rate and delta-capacity diagnostics, because all-split
  horizon-3 capacity level narrowly misses the prior-slope baseline; Milestone
  6.1 forensics recommend only a possible prior-trajectory-shape audit, not
  tuning, architecture, or future-exposure features; Milestone 6.2 runs that
  audit and finds trajectory shape does not repair the gap;
- sequence models remain blocked by the order-vs-aggregate and
  order-vs-shuffled negative result plus the Milestone 7.1 CUDA Torch MLP
  fixed-length sequence reopening failure;
- calibrated uncertainty remains blocked by C-rate coverage failure even after
  quantile noncrossing hygiene;
- CBAT, policy ranking, causal claims, same-cell counterfactuals, DRT, and
  learned EIS embeddings remain blocked.
- Milestone 7.2 adds positive observed support for matched policy contrasts
  (234 triplet-supported contrasts and 0.916 sign-stable capacity-loss rows),
  but policy ranking remains blocked because this is not calibrated risk, not
  causal evidence, not a same-cell counterfactual design, and not a policy
  recommendation model.
- Milestone 7.3 adds partial existing-prediction contrast-ordering signal, but
  it fails the strict prior-slope bootstrap reference gate and therefore still
  blocks recommendation, causal, counterfactual, calibrated-risk, CBAT, and
  sequence/neural claims.
- Milestone 7.4 explains that failure by effect size and rank metric, but
  large-effect and rank diagnostics remain diagnostic-only and do not reopen
  policy ranking.
- Milestone 8.0 adds support-aware selective reliability diagnostics, but
  support filtering does not improve the primary capacity or threshold-warning
  rows at 50% retention and C-rate support reliability is not supported. This
  keeps deployment reliability, calibrated-risk, policy, causal, and CBAT
  claims blocked.
- Milestone 8.1 adds train-only diagnostic-state distillation from
  check-up-k capacity/state/time/nominal fields to current PULSE/EIS scalar
  diagnostic-state surrogates. The auxiliary state is learnable (`12/12`
  auxiliary rows beat train-mean baselines), but predicted diagnostic-state
  features do not improve downstream capacity-horizon or threshold-warning
  baselines enough to pass the gate. The best D3 all-split capacity primary
  relative gain is `-0.00790693`, the all-split threshold-warning relative
  Brier gain is `-0.0620807`, and C-rate non-collapse fails. This blocks
  capacity+PULSE+EIS architecture, CBAT, broad multimodal state-learning,
  calibrated-risk/uncertainty, policy, causal, and same-cell counterfactual
  claims from the diagnostic-state path.
- Milestone 8.2 adds direct future scalar diagnostic endpoint forecasting for
  PULSE/EIS horizons 1/2/3/5. The table and leakage audit pass, but DH3 HGB
  does not satisfy the strict broad endpoint gate: only `21/24` primary
  horizon-2/3 rows pass the 10% reference-gain rule and only `22/24` C-rate
  rows avoid negative gain. This keeps broad endpoint forecasting,
  capacity+PULSE+EIS architecture, CBAT, calibrated-risk/uncertainty, policy,
  sequence/neural, causal, and same-cell counterfactual claims blocked.
- Milestone 8.2.1 diagnoses that partial result with endpoint-specific
  forensics. `eis_z_abs_1kHz`, `nyquist_semicircle_width_proxy`, and
  `pulse_10ms_resistance` pass selected scalar endpoint diagnostic checks, but
  `eis_phase_1kHz`, `nyquist_im_peak_abs`, and `pulse_1s_resistance` remain
  partial because at least one primary or C-rate guardrail fails. This supports
  only selected endpoint diagnostic wording and still blocks broad endpoint
  forecasting, architecture, CBAT, calibrated risk/uncertainty, policy,
  causal, and same-cell counterfactual claims.
- Milestone 8.5 finalizes C-rate repair feasibility by combining the 8.4
  support/root-cause report with existing adaptive and router artifacts. It
  supports only narrow diagnostic C-rate `delta_capacity_Ah` repair wording.
  Broad robust capacity, solved C-rate fade, architecture, CBAT, policy
  ranking, calibrated risk/uncertainty, sequence/neural, and causal claims
  remain blocked.

Decision: return to synthesis/release maintenance unless a new narrow
calibration-method diagnostic is explicitly justified.
