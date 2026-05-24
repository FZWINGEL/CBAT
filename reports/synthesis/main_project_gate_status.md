# Main Project Gate Status v2

| Gate | Status | Evidence | Blocked claims | Next action |
|---|---|---|---|---|
| Capacity | Supported benchmark foundation | C-rate remains hardest: `capacity_Ah_k1` MAE `0.125186`, `delta_capacity_Ah` MAE `0.101133`. | Uniform generalization. | Use as central benchmark story. |
| LOG_AGE stress | Mixed / partially supported | Stress features help some views but C-rate delta best stress row `0.102516` is worse than F4 `0.101133`. | Stress features solve C-rate fade. | Keep as mixed result. |
| Stressor-robust capacity | Diagnostic improvement / global claim not supported | Stressor-balanced HGB improves C-rate delta to `0.0705429` with paired p05 above zero versus F4 and stress R0, but max outside-C-rate degradation is `0.0528343`. | C-rate fade solved; architecture justified. | Keep diagnostic or run narrow voltage-window forensics. |
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
Milestone 5.3 closes calibration and robustness gate correctness hardening. It
does not authorize calibrated-risk, calibrated-uncertainty, robust-capacity,
policy, architecture, causal, or broad multimodal claims.
Further modeling should not be opened without a new gated technical rationale.
