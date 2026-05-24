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
- threshold-warning probability calibration.

The strongest contribution is now a rigorous grouped-validation benchmark that
documents which battery-degradation signals are supported, diagnostic-only,
negative, or blocked.

## Recommended Path

1. Preserve the benchmark/data-methods framing rather than an architecture
   branch.
2. If manuscript work resumes, integrate the Milestone 5.0 calibration result
   as a blocked calibrated-risk claim.
3. If engineering work resumes, prefer release automation or reproducibility
   checks over new scientific expansion.

## Optional Technical Branch

The narrow threshold-warning calibration branch has now been run. Platt and
isotonic calibration improve mean reliability, but C-rate ECE remains above
the guardrail, so calibrated-risk and policy-ranking claims remain blocked.
Any future calibration work should be scoped as diagnostics only.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
