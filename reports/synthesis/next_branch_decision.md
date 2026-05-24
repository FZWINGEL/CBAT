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
- stressor-axis robust capacity baselines.

The strongest contribution is now a rigorous grouped-validation benchmark that
documents which battery-degradation signals are supported, diagnostic-only,
negative, or blocked. Milestone 5.1 adds a real but claim-bounded C-rate
robustness result: stressor-balanced HGB improves C-rate `delta_capacity_Ah`,
but does not pass the global non-degradation rule.

## Recommended Path

1. Preserve the benchmark/data-methods framing rather than an architecture
   branch.
2. If manuscript work resumes, integrate Milestone 5.0 as a blocked
   calibrated-risk claim and Milestone 5.1 as a diagnostic stressor-robustness
   result.
3. If engineering work resumes, prefer release automation or reproducibility
   checks over new scientific expansion.

## Optional Technical Branch

The narrow threshold-warning calibration branch has now been run. Platt and
isotonic calibration improve mean reliability, but C-rate ECE remains above
the guardrail, so calibrated-risk and policy-ranking claims remain blocked.
Any future calibration work should be scoped as diagnostics only.

The narrow stressor-robust capacity branch has also been run. Stressor-balanced
HGB improves C-rate fade diagnostics, but the global claim remains blocked by
outside-C-rate degradation. Any future work here should be a forensics pass on
the voltage-window regression, not a new architecture.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
