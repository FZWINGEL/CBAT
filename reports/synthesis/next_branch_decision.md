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
not a solved multi-step forecasting result.

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
3. If engineering work resumes, prefer release automation or reproducibility
   checks over new scientific expansion.

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

The multi-horizon capacity branch has now also been run. It creates a useful
diagnostic result, especially for C-rate horizons 2 and 3, but it does not
justify sequence/neural models, policy ranking, or CBAT. If continued, the only
defensible follow-up would be a predeclared error-analysis or prospective
feature audit, not post-hoc tuning around the near-tied horizon-3
capacity-level row.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
