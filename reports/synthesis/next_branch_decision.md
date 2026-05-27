# Next Branch Decision

## Decision

Return to benchmark release maintenance, synthesis refreshes, or manuscript
integration. Do not open a broad new modeling branch.

## Rationale

The project has completed the major baseline-first charter gates:

- capacity grouped baselines;
- LOG_AGE scalar and stress features;
- PULSE diagnostics and coupling;
- prior PULSE comparisons;
- EIS QA, features, scalar baselines, and hardening;
- semi-empirical comparator;
- replicate uncertainty;
- grouped calibration;
- temporal-order falsification;
- knee-label stability;
- threshold-event warning and censoring finalization;
- threshold-warning probability calibration;
- stressor-axis robust capacity baselines;
- calibration metric sensitivity and capacity quantile noncrossing hygiene;
- calibration and robustness gate correctness hardening;
- stressor-robust Pareto forensics and claim finalization;
- train-only adaptive stressor-robust selection;
- adaptive stressor-robust replication and final claim hardening;
- stressor-robust attribution and reweighting decomposition.
- targeted stressor-family routing;
- hierarchical replicate-aware capacity comparators;
- multi-horizon capacity forecasting diagnostics.
- multi-horizon error forensics and prospective feature audit.
- prior-trajectory shape multi-horizon diagnostic.
- benchmark task freeze and leaderboard reproducibility.
- minimal fixed-length event-sequence and CUDA Torch MLP reopening check.
- observed policy-contrast support and sign-stability diagnostics.
- support-bounded contrast-ordering feasibility diagnostics.
- contrast-ordering failure forensics and support-aware selective reliability
  diagnostics.

The strongest contribution is now a rigorous grouped-validation benchmark that
documents which battery-degradation signals are supported, diagnostic-only,
negative, or blocked. Milestone 5.3 closes the correctness requests:
required-policy calibration checks, policy-specific C-rate checks, fallback-row
guardrails, no-empty-run failures, and stressor-robust bagging/readiness
hygiene do not change the blocked status of calibrated-risk,
calibrated-uncertainty, robust-capacity, policy, or architecture claims.
Milestone 5.6 locks the narrow positive diagnostic for conservative train-only
adaptive stressor-balanced selection after deterministic-seed replication, but
it does not change the blocked status of broad fade-solved, policy,
architecture, calibrated-risk, or causal claims.
Milestone 5.7 keeps that result narrow: F8 adds C-rate delta signal under
adaptive selection, but the incremental F8 comparison fails outside-C-rate
non-degradation, so independent stress-feature attribution remains
diagnostic-only.
Milestone 5.8 adds a targeted stressor-family router over existing attribution
arms. It preserves the C-rate reweighting gain while routing non-C-rate views
to D0, but it is a diagnostic routing result rather than a global robust model.
Milestone 5.9 adds the charter-required hierarchical replicate-aware
comparator. It is useful as an L5 diagnostic baseline, but H4/F4 partial
pooling does not pass paired C-rate support and H5 intervals are undercovered.
Milestone 6.0 adds a Q1 multi-horizon capacity forecasting diagnostic. C-rate
and delta-capacity horizons 2/3 are positive for prospective HGB K2, but the
all-split horizon-3 capacity-level row narrowly misses prior slope, so this is
not a solved multi-step forecasting result. Milestone 6.1 diagnoses that result
without new model training: the C-rate rows remain positive, K3 oracle exposure
is useful only as a non-prospective diagnostic, and the only plausible future
technical branch is a predeclared prior-trajectory-shape audit using information
available at check-up `k`. Milestone 6.2 runs that audit and keeps the branch
partial/diagnostic: K5 does not repair all-split horizon-3 capacity and does
not preserve every C-rate horizon-2/3 target row.
Milestone 7.0 freezes the completed evidence base into the benchmark task set, a
task-level leaderboard, task cards, model-family cards, and an executable
task-registry checker. It changes no claim status and adds no new model branch.
Milestone 7.1 tests whether the sequence/neural gate should reopen using real
fixed-length run-event sequences and CUDA Torch MLP rows. GPU execution is now
verified, but true-sequence candidates still fail the aggregate-event HGB,
timestamp-stress HGB, and C-rate `delta_capacity_Ah` controls, so the
sequence/neural branch remains blocked.
Milestone 7.2 then checks whether a policy-response branch even has observed
matched support. It does: 234 triplet-supported contrasts across four families
and 0.916 observed sign-stable capacity-loss rows. This is useful support
evidence, but it is not calibrated risk, not causal evidence, not an
intervention test, and not a ranking model.
Milestone 7.3 then uses existing multi-horizon predictions to test
support-bounded contrast ordering. HGB K2 has partial diagnostic signal, but
it fails the strict prior-slope bootstrap reference gate, so this is still not
policy recommendation, causal evidence, calibrated risk, or a deployment
ranking result.
Milestone 7.4 then diagnoses that failure by effect-size threshold, rank
correlation, and top-k/regret metrics. It explains some of the metric
sensitivity but remains diagnostic-only and does not reopen policy ranking.
Milestone 8.0 then tests whether train-only condition-support scores can
identify reliable subsets of existing capacity, threshold-warning, and
supported contrast-ordering predictions. Support-distance auditing is useful,
but primary capacity and threshold-warning metrics worsen at 50% retention and
C-rate support reliability is not supported. This keeps support filtering as
an abstention diagnostic, not a deployment, calibrated-risk, policy, causal, or
CBAT result.

## Recommended Path

1. Preserve the benchmark/data-methods framing rather than an architecture
   branch.
2. If manuscript work resumes, integrate Milestones 5.0/5.2/5.3 as blocked
   calibrated-risk and calibrated-uncertainty evidence, and Milestone 5.1 as a
   diagnostic stressor-robustness result hardened by 5.3 correctness checks
   and narrowed by the Milestone 5.6 replicated adaptive-selection result plus
   the Milestone 5.8 targeted routing diagnostic, and the Milestone 5.9
   hierarchical comparator as a negative/diagnostic L5 baseline. Integrate
   Milestone 6.0 as a scoped multi-horizon diagnostic, not as architecture
   readiness.
3. If engineering work resumes, prefer release automation, task-registry
   maintenance, or reproducibility checks over new scientific expansion.
4. If ML research continues, do not continue the policy branch unless a new
   predeclared diagnostic objective is stronger than the already-failed
   Milestone 7.3 prior-slope bootstrap gate and the Milestone 7.4
   diagnostic-only forensics and also survives the Milestone 8.0
   support-reliability limitation. Do not treat Milestone 7.2, 7.3, 7.4, or
   8.0 as a policy result.

## Optional Technical Branch

The narrow threshold-warning calibration branch has now been run. Platt and
isotonic calibration improve mean reliability, but C-rate ECE remains above
the guardrail, so calibrated-risk and policy-ranking claims remain blocked.
Milestone 5.2 adds equal-frequency ECE sensitivity and Milestone 5.3 hardens
the readiness logic; both reach the same decision. Any future calibration work
should be scoped as diagnostics only.

The narrow stressor-robust capacity branch, Pareto forensics, and adaptive
selector follow-up have also been run. Stressor-balanced HGB improves C-rate
fade diagnostics. The fixed predeclared R2/F8/w1 claim remains blocked by
outside-C-rate degradation (`0.0528343` versus the 5% guardrail), but the
conservative train-only adaptive selector now replicates diagnostically for
`delta_capacity_Ah` with max outside-C-rate degradation `0.0279117`; the
max-gain policy still fails at `0.0645764`. Further work here is lower value
than synthesis/release maintenance unless a fresh predeclared question is
needed. The Milestone 5.7 attribution decomposition does not create that next
question: reweighting-only and adaptive F8 both contribute C-rate delta signal,
but F8 attribution fails the outside-split guardrail.
Milestone 5.8 answers the obvious routing follow-up: targeted D2-for-C-rate and
D0-elsewhere routing passes diagnostically. More work here should not broaden
the claim without a new independent validation design.

The hierarchical replicate-aware capacity branch has now also been run. It
does not create a stronger next branch: the mean C-rate delta gain is tiny,
paired p05 is negative, and interval coverage fails. Treat it as a completed
charter comparator rather than a reason to tune more partial-pooling variants.

The multi-horizon capacity branch, error forensics, and prior-trajectory-shape
follow-up have now also been run. The K5 prior-trajectory feature group has
isolated diagnostic gains, but it does not repair the all-split horizon-3
capacity near miss and does not preserve all C-rate horizon-2/3 rows. This
branch is complete as diagnostic evidence and does not justify sequence/neural
models, policy ranking, or CBAT.

The minimal sequence/neural reopening check has also been run with CUDA
PyTorch. It is a useful negative H7 test, not a reason to start transformers or
CBAT: true event order does not beat the stronger aggregate-event or
timestamp-stress HGB references under the required grouped controls.

The observed policy-contrast support gate has also been run. It establishes
that matched triplet contrasts exist and observed degradation ordering is often
stable, but it does not authorize policy recommendation, causal intervention,
same-cell counterfactual, or deployment ranking claims.

The support-bounded contrast-ordering feasibility gate has also been run. It
finds partial HGB K2 ordering signal from existing multi-horizon predictions,
including strong C-rate sign accuracy, but it fails the strict bootstrap
comparison against prior slope. Treat this as partial diagnostic evidence, not
as a branch-opening result.

The contrast-ordering failure-forensics gate has also been run. It decomposes
the failure by effect size and rank metric, but large-effect and rank
diagnostics remain diagnostic-only.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models beyond the completed minimal CUDA reopening
  diagnostic.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
