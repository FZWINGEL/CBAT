# Main Project Gate Status v2

| Gate | Status | Evidence | Blocked claims | Next action |
|---|---|---|---|---|
| Capacity | Supported benchmark foundation | C-rate remains hardest: `capacity_Ah_k1` MAE `0.125186`, `delta_capacity_Ah` MAE `0.101133`. | Uniform generalization. | Use as central benchmark story. |
| LOG_AGE stress | Mixed / partially supported | Stress features help some views but C-rate delta best stress row `0.102516` is worse than F4 `0.101133`. | Stress features solve C-rate fade. | Keep as mixed result. |
| Stressor-robust capacity | Narrow replicated adaptive diagnostic supported / stressor-family routing diagnostic supported / attribution diagnostic-only / broad solved-fade claim blocked | Fixed-weight stressor-balanced HGB improves C-rate delta but the predeclared R2/F8/w1 setting fails outside-C-rate degradation at `0.0528343`; conservative train-only adaptive R2/F8 selection replicates across five logical deterministic seeds with C-rate gains `0.0200436` vs F4 and `0.0214266` vs stress R0, paired p05 above zero, and max outside-C-rate degradation `0.0279117`. Milestone 5.7 shows incremental F8 value under adaptive selection for C-rate delta (`0.00940756`, paired p05 `6.06012e-05`), but the incremental comparison fails outside-C-rate non-degradation (`0.717391`), while reweighting-only also contributes (`0.0106361`). Milestone 5.8 routes C-rate transfer to D2 adaptive R2/F4 and non-C-rate views to D0, preserving C-rate gain `0.0106361` with paired p05 `0.00594397` and max outside-C-rate degradation `0`. | C-rate fade solved; architecture justified; adaptive gain wholly attributed to F8 stress features; global robust capacity. | Lock C22 and C24 as narrow diagnostics; keep F8 attribution diagnostic-only. |
| Hierarchical replicate capacity | Implemented L5 comparator / partial-pooling improvement diagnostic-only | H4/F4 train-only residual partial pooling gives a tiny C-rate `delta_capacity_Ah` gain versus H3/F4 (`0.000100645`) with max outside-C-rate degradation `0.00275483`, but paired bootstrap p05 is negative (`-1.88643e-05`). H5 replicate-variance intervals are undercovered: C-rate delta coverage `0.312102`, minimum primary coverage `0.151596`. | Hierarchical partial pooling solves C-rate fade; calibrated uncertainty; architecture justified. | Keep as negative/diagnostic L5 comparator. |
| Multi-horizon capacity | Partially supported overall / C-rate and delta diagnostics supported | `capacity_horizon_table_v1` has 13,770 observed rows across 228 cells and 76 parameter sets. HGB K2 beats persistence and prior slope for C-rate horizons 2/3 on both `capacity_Ah_kh` and `delta_capacity_Ah_h`, and beats both references for all-split `delta_capacity_Ah_h` horizons 2/3. Overall capacity-level support is partial because horizon-3 `capacity_Ah_kh` HGB K2 MAE `0.0935304` is slightly worse than prior-slope `0.0932329`. Milestone 6.1 forensics keep this posture and recommend only a possible prior-trajectory-shape audit. | Multi-horizon forecasting solved globally; K3 oracle exposure as prospective input; architecture/policy readiness. | Lock scoped diagnostic wording only. |
| PULSE | Supported for diagnostics | Canonical RT/50 PULSE target robustness and scalar baselines pass. | Broad multimodal claims. | Include scalar endpoint only. |
| Capacity-PULSE coupling | Explanatory diagnostic | C-rate residual correlations remain strong after robustness checks. | Causal or predictive capacity+PULSE claim. | Use as explanatory diagnostic. |
| EIS | Diagnostic / partially supported | QA, masks, scalar endpoints, and narrow profile prior-EIS signals pass; C-rate and fade claims fail. | Broad EIS improvement, DRT, embeddings. | Keep diagnostic unless new gate is opened. |
| Semi-empirical comparator | Useful negative comparator | Semi-empirical ridge baselines are weaker than HGB/stress in C-rate views. | Domain baseline superiority. | Include as benchmark comparator. |
| Replicate uncertainty | Diagnostic only | Triplet spread contextualizes error but does not validate intervals. | Calibrated uncertainty. | Keep as uncertainty context. |
| Grouped calibration | Not supported globally | Noncrossing quantile hygiene raises raw q10-q90 mean coverage to `0.701398`, but C-rate coverage remains below target. | Calibrated capacity uncertainty. | Keep blocked. |
| Temporal order | Not supported | Order-aware features do not beat aggregate/shuffled controls. | Sequence model justification. | Keep sequence models blocked. |
| Detector knee labels | Not supported | Only 45 / 64 primary-valid conditions are replicate-consistent within 2 check-ups. | Detector-knee prediction. | Keep diagnostic only. |
| Threshold warning | Supported for diagnostics | Verified-only HGB W2 Brier `0.090116` beats prior `0.178655` and proximity `0.168492`. | Calibrated risk, causal warning, policy ranking. | Lock diagnostic claim. |
| Threshold-warning calibration | Not supported for calibrated risk | Equal-frequency ECE sensitivity is reported; corrected Platt verified-only primary ECE is `0.0748136` fixed and `0.0729286` equal-frequency, but policy-specific C-rate remains above guardrail (`0.167653` fixed; `0.176185` equal-frequency). | Calibrated risk. | Keep probabilities diagnostic. |
| Policy ranking | Blocked | No calibrated risk, no causal evidence, no intervention test. | Policy ranking. | Do not open. |
| CBAT | Blocked | Simpler gates do not justify architecture. | CBAT validation. | Do not open. |

## Summary Decision

The main technical program has reached a coherent benchmark checkpoint.
Milestone 5.6 locks one narrow positive diagnostic: conservative train-only
adaptive stressor-balanced selection replicates across the deterministic seed
interface and passes the C-rate gain and outside-C-rate non-degradation gate
for `delta_capacity_Ah`. Milestone 5.7 then shows that F8 adds C-rate delta
signal under adaptive selection but fails outside-C-rate attribution
guardrails, so the adaptive result should not be described as independently
explained by stress features. Milestone 5.8 adds a targeted stressor-family
router over existing arms: D2 for C-rate transfer and D0 otherwise. This
supports diagnostic routing only, not a global robust model. No milestone
authorizes calibrated-risk,
calibrated-uncertainty, broad robust-capacity, policy, architecture, causal, or
broad multimodal claims. Milestone 5.9 adds the charter-required hierarchical
replicate-aware comparator, but it remains diagnostic-only because paired
C-rate support and interval coverage do not pass.
Milestone 6.0 adds a fresh Q1 forecasting diagnostic: C-rate and
delta-capacity multi-horizon rows are positive, but the overall capacity-level
claim is only partial and future horizon exposure remains oracle-only.
Further modeling should not be opened without a new gated technical rationale.
