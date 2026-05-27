# Main Project Gate Status v2

| Gate | Status | Evidence | Blocked claims | Next action |
|---|---|---|---|---|
| Capacity | Supported benchmark foundation | C-rate remains hardest: `capacity_Ah_k1` MAE `0.125186`, `delta_capacity_Ah` MAE `0.101133`. | Uniform generalization. | Use as central benchmark story. |
| LOG_AGE stress | Mixed / partially supported | Stress features help some views but C-rate delta best stress row `0.102516` is worse than F4 `0.101133`. | Stress features solve C-rate fade. | Keep as mixed result. |
| Stressor-robust capacity | Narrow replicated adaptive diagnostic supported / stressor-family routing diagnostic supported / attribution diagnostic-only / broad solved-fade claim blocked | Fixed-weight stressor-balanced HGB improves C-rate delta but the predeclared R2/F8/w1 setting fails outside-C-rate degradation at `0.0528343`; conservative train-only adaptive R2/F8 selection replicates across five logical deterministic seeds with C-rate gains `0.0200436` vs F4 and `0.0214266` vs stress R0, paired p05 above zero, and max outside-C-rate degradation `0.0279117`. Milestone 5.7 shows incremental F8 value under adaptive selection for C-rate delta (`0.00940756`, paired p05 `6.06012e-05`), but the incremental comparison fails outside-C-rate non-degradation (`0.717391`), while reweighting-only also contributes (`0.0106361`). Milestone 5.8 routes C-rate transfer to D2 adaptive R2/F4 and non-C-rate views to D0, preserving C-rate gain `0.0106361` with paired p05 `0.00594397` and max outside-C-rate degradation `0`. | C-rate fade solved; architecture justified; adaptive gain wholly attributed to F8 stress features; global robust capacity. | Lock C22 and C24 as narrow diagnostics; keep F8 attribution diagnostic-only. |
| Hierarchical replicate capacity | Implemented L5 comparator / partial-pooling improvement diagnostic-only | H4/F4 train-only residual partial pooling gives a tiny C-rate `delta_capacity_Ah` gain versus H3/F4 (`0.000100645`) with max outside-C-rate degradation `0.00275483`, but paired bootstrap p05 is negative (`-1.88643e-05`). H5 replicate-variance intervals are undercovered: C-rate delta coverage `0.312102`, minimum primary coverage `0.151596`. | Hierarchical partial pooling solves C-rate fade; calibrated uncertainty; architecture justified. | Keep as negative/diagnostic L5 comparator. |
| Multi-horizon capacity | Partially supported overall / C-rate and delta diagnostics supported | `capacity_horizon_table_v1` has 13,770 observed rows across 228 cells and 76 parameter sets. HGB K2 beats persistence and prior slope for C-rate horizons 2/3 on both `capacity_Ah_kh` and `delta_capacity_Ah_h`, and beats both references for all-split `delta_capacity_Ah_h` horizons 2/3. Overall capacity-level support is partial because horizon-3 `capacity_Ah_kh` HGB K2 MAE `0.0935304` is slightly worse than prior-slope `0.0932329`. Milestone 6.2 tests prior-only trajectory shape: K5 fails to repair all-split horizon-3 capacity (`0.0981241`) and fails full C-rate preservation, so trajectory shape is partial/diagnostic only. | Multi-horizon forecasting solved globally; K3 oracle exposure as prospective input; trajectory shape repairs the gap; architecture/policy readiness. | Lock scoped diagnostic wording only. |
| Benchmark task freeze | Supported for reproducibility | `configs/benchmark_tasks_v1.yaml` now tracks 19 gated tasks and `mbp report check-benchmark-tasks` validates task statuses against the v2 claim matrix and source artifacts. | New scientific claims; unregistered model expansion. | Use task registry and leaderboard as benchmark interface. |
| PULSE | Supported for diagnostics | Canonical RT/50 PULSE target robustness and scalar baselines pass. | Broad multimodal claims. | Include scalar endpoint only. |
| Capacity-PULSE coupling | Explanatory diagnostic | C-rate residual correlations remain strong after robustness checks. | Causal or predictive capacity+PULSE claim. | Use as explanatory diagnostic. |
| EIS | Diagnostic / partially supported | QA, masks, scalar endpoints, and narrow profile prior-EIS signals pass; C-rate and fade claims fail. | Broad EIS improvement, DRT, embeddings. | Keep diagnostic unless new gate is opened. |
| Semi-empirical comparator | Useful negative comparator | Semi-empirical ridge baselines are weaker than HGB/stress in C-rate views. | Domain baseline superiority. | Include as benchmark comparator. |
| Replicate uncertainty | Diagnostic only | Triplet spread contextualizes error but does not validate intervals. | Calibrated uncertainty. | Keep as uncertainty context. |
| Grouped calibration | Not supported globally | Noncrossing quantile hygiene raises raw q10-q90 mean coverage to `0.701398`, but C-rate coverage remains below target. | Calibrated capacity uncertainty. | Keep blocked. |
| Temporal order | Not supported | Order-aware features do not beat aggregate/shuffled controls. | Sequence model justification. | Keep sequence models blocked. |
| Minimal sequence reopening | Not supported | `interval_event_sequence_table_v1` covers all 3,827 intervals and CUDA Torch MLP rows run on PyTorch `2.12.0+cu130`, but true-sequence candidates fail aggregate-event HGB (`-0.227321` mean gain, `0/48` positive rows), timestamp-stress HGB (`-0.190925`, `0/44`), and C-rate `delta_capacity_Ah` (`1/6` positive rows, `-0.159493`). | Sequence/neural model justification; CBAT; policy ranking. | Keep sequence/neural work blocked. |
| Observed policy-contrast support | Supported for diagnostics | `policy_contrast_registry_v1` contains 234 triplet-supported observed contrasts across charge C-rate, temperature, voltage-window, and profile families; 2,943 of 3,213 observed capacity-loss rows are sign-stable (`0.916`). | Policy ranking; policy recommendation; causal intervention; same-cell counterfactual; calibrated risk. | Keep as observed support diagnostics; any ranking feasibility baseline requires a separate gate. |
| Supported contrast ordering | Partially supported diagnostic | Existing multi-horizon predictions generate 164,100 pairwise rows. HGB K2 primary `delta_capacity_Ah_h` sign accuracy averages `0.780`; C-rate horizon 2/3 rows are `0.826923`/`0.888889`, but `0/10` primary all-family bootstrap checks beat prior slope with positive p05. | Policy ranking; policy recommendation; causal intervention; same-cell counterfactual; calibrated policy risk/utility; CBAT. | Keep as partial diagnostic evidence only. |
| Contrast-ordering failure forensics | Diagnostic only | Effect-size and rank forensics over the existing 7.3 CSVs generate 306 HGB-vs-prior failure-bin rows. The strict prior-slope gate still has `0/10` all-family checks passing; large-effect passing families are `charge_c_rate` and `temperature`, C-rate medium/large pass rows are `1/4`, and HGB `ge_0.02Ah` mean sign accuracy is `0.856314`. | Policy ranking; policy recommendation; causal intervention; same-cell counterfactual; calibrated policy risk/utility; CBAT. | Keep as failure decomposition only; do not open a policy branch unless a future predeclared large-effect gate is explicitly requested. |
| Support-aware selective reliability | Diagnostic only | Milestone 8.0 generates 380 train-only support-distance rows and selective retention curves for existing capacity-horizon, threshold-warning, and supported contrast-ordering artifacts. At 50% retention, primary capacity MAE gain is `-0.0115957`, threshold-warning Brier gain is `-0.0040389`, policy sign-accuracy gain is `0.0173861`, and C-rate primary capacity gain is `-0.0525537`. | Deployment reliability; calibrated risk; policy recommendation; causal intervention; same-cell counterfactual; CBAT. | Keep as support/audit and abstention diagnostics only. |
| Diagnostic-state distillation | Not supported for downstream multimodal-state value | Stage-A train-only predicted PULSE/EIS scalar diagnostic state beats train-mean auxiliary baselines in `12/12` rows, but downstream D3 predicted PULSE+EIS state worsens the primary all-split capacity-horizon and threshold-warning rows. Best D3 capacity primary relative gain is `-0.00790693`, threshold-warning all-split relative Brier gain is `-0.0620807`, and C-rate non-collapse fails. | Capacity+PULSE+EIS architecture; broad multimodal state learning; calibrated risk or uncertainty; policy ranking; causal or same-cell counterfactual claims; CBAT. | Keep PULSE/EIS state as auxiliary diagnostics only; do not open broad architecture or multimodal branches from this result. |
| Diagnostic endpoint horizon forecasting | Partially supported | `diagnostic_horizon_table_v1` passes QA with 80,878 rows across 228 cells, 76 parameter-set conditions, six scalar PULSE/EIS targets, and horizons 1/2/3/5. DH3 HGB capacity plus current same-diagnostic state passes `21/24` primary horizon-2/3 10% gain rows and `22/24` C-rate non-collapse rows, so the strict endpoint forecasting gate does not fully pass. | Broad diagnostic endpoint forecasting; capacity+PULSE+EIS architecture; CBAT; calibrated risk or uncertainty; policy ranking; sequence/neural branches; causal or same-cell counterfactual claims. | Keep as partial diagnostic endpoint-forecasting evidence only. |
| Detector knee labels | Not supported | Only 45 / 64 primary-valid conditions are replicate-consistent within 2 check-ups. | Detector-knee prediction. | Keep diagnostic only. |
| Threshold warning | Supported for diagnostics | Verified-only HGB W2 Brier `0.090116` beats prior `0.178655` and proximity `0.168492`. | Calibrated risk, causal warning, policy ranking. | Lock diagnostic claim. |
| Threshold-warning calibration | Not supported for calibrated risk | Equal-frequency ECE sensitivity is reported; corrected Platt verified-only primary ECE is `0.0748136` fixed and `0.0729286` equal-frequency, but policy-specific C-rate remains above guardrail (`0.167653` fixed; `0.176185` equal-frequency). | Calibrated risk. | Keep probabilities diagnostic. |
| Policy ranking | Blocked / possible future feasibility gate only | Milestone 7.2 finds observed matched contrast support and sign stability, but there is still no calibrated risk, no causal evidence, no intervention test, and no ranking model gate. | Policy ranking; policy recommendation. | Do not open without a separate predeclared feasibility baseline. |
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
Milestone 6.2 tests the only authorized prior-trajectory follow-up and keeps
that branch partial/diagnostic because it does not repair horizon-3 capacity
or preserve all C-rate rows.
Milestone 7.0 freezes these completed gates into benchmark tasks and an
executable registry check without changing any claim status.
Milestone 7.1 then tests a stricter sequence/neural reopening challenge with
fixed-length event sequences and CUDA Torch MLP rows. The environment executes
on GPU, but the true-sequence candidates still lose to aggregate-event and
timestamp-stress HGB references, so the H7 reopening condition fails and
sequence/neural branches remain blocked.
Milestone 7.2 adds observed policy-contrast support diagnostics: the dataset
has matched triplet support and stable observed degradation ordering for many
contrasts, but this is not policy ranking or causal evidence. A future ranking
feasibility baseline is only a possible separate gate.
Milestone 7.3 runs that separate feasibility gate using existing multi-horizon
predictions only. It finds partial supported contrast-ordering signal but
fails the strict prior-slope bootstrap reference rule, so recommendation,
causal, counterfactual, calibrated-risk, policy, CBAT, and sequence/neural
claims remain blocked.
Milestone 7.4 decomposes that failure by effect size, rank metric, and
top-k/regret diagnostics, but remains diagnostic-only and does not reopen
policy ranking.
Milestone 8.0 adds train-only support-aware selective reliability diagnostics.
Support scores are useful for auditing where predictions are inside observed
condition support, but selective retention does not improve the primary
capacity or threshold-warning metrics and C-rate support reliability is not
supported. It therefore remains an abstention/support audit only.
Milestone 8.1 tests a stricter Q2/H3 multimodal-state question without opening
architecture: can check-up-k state predict PULSE/EIS diagnostic scalars, and
do those predicted states improve capacity-horizon or threshold-warning
forecasts? The auxiliary surrogate step works, but downstream gains do not
pass. Diagnostic-state distillation is therefore a negative gate and does not
authorize capacity+PULSE+EIS architecture, CBAT, broad multimodal learning,
calibrated risk, policy ranking, or causal claims.
Milestone 8.2 tests future PULSE/EIS endpoint forecasting directly. The
horizon table and leakage audit pass, and DH3 has useful gains in many rows,
but the strict primary and C-rate guardrails do not fully pass, so the result
is partial diagnostic endpoint evidence rather than architecture readiness.
Further modeling should not be opened without a new gated technical rationale.
