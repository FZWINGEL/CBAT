# Main Project Gate Status v2

| Gate | Status | Evidence | Blocked claims | Next action |
|---|---|---|---|---|
| Capacity | Supported benchmark foundation | C-rate remains hardest: `capacity_Ah_k1` MAE `0.125186`, `delta_capacity_Ah` MAE `0.101133`. | Uniform generalization. | Use as central benchmark story. |
| LOG_AGE stress | Mixed / partially supported | Stress features help some views but C-rate delta best stress row `0.102516` is worse than F4 `0.101133`. | Stress features solve C-rate fade. | Keep as mixed result. |
| Stressor-robust capacity | Narrow replicated adaptive diagnostic supported / attribution diagnostic-only / broad solved-fade claim blocked | Fixed-weight stressor-balanced HGB improves C-rate delta but the predeclared R2/F8/w1 setting fails outside-C-rate degradation at `0.0528343`; conservative train-only adaptive R2/F8 selection replicates across five logical deterministic seeds with C-rate gains `0.0200436` vs F4 and `0.0214266` vs stress R0, paired p05 above zero, and max outside-C-rate degradation `0.0279117`. Milestone 5.7 shows incremental F8 value under adaptive selection for C-rate delta (`0.00940756`, paired p05 `6.06012e-05`), but the incremental comparison fails outside-C-rate non-degradation (`0.717391`), while reweighting-only also contributes (`0.0106361`). | C-rate fade solved; architecture justified; adaptive gain wholly attributed to F8 stress features. | Lock C22 as narrow diagnostic; keep F8 attribution diagnostic-only. |
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
explained by stress features. Neither milestone authorizes calibrated-risk,
calibrated-uncertainty, broad robust-capacity, policy, architecture, causal, or
broad multimodal claims.
Further modeling should not be opened without a new gated technical rationale.
