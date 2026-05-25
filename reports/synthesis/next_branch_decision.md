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
- adaptive stressor-robust replication and final claim hardening.

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

## Recommended Path

1. Preserve the benchmark/data-methods framing rather than an architecture
   branch.
2. If manuscript work resumes, integrate Milestones 5.0/5.2/5.3 as blocked
   calibrated-risk and calibrated-uncertainty evidence, and Milestone 5.1 as a
   diagnostic stressor-robustness result hardened by 5.3 correctness checks
   and narrowed by the Milestone 5.6 replicated adaptive-selection result.
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
needed.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
