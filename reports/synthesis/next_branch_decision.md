# Next Branch Decision

## Decision

Return to synthesis/manuscript integration and benchmark release preparation.

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
- threshold-event warning and censoring finalization.

The strongest contribution is now a rigorous grouped-validation benchmark that
documents which battery-degradation signals are supported, diagnostic-only,
negative, or blocked.

## Recommended Path

1. Integrate Milestone 2.0-2.6.2 evidence into the manuscript package.
2. Refresh figures/tables around EIS, temporal-order, knee/threshold, and
   threshold-warning results.
3. Prepare a benchmark/data-methods framing rather than an architecture paper.

## Optional Technical Branch

Only open a narrow threshold-warning calibration branch if calibrated
probability scores are needed:

- grouped Platt/isotonic calibration only;
- no policy ranking;
- no detector-knee prediction;
- no CBAT;
- no neural/sequence models;
- no causal claims.

## Explicitly Rejected Branches

- CBAT architecture.
- Neural or sequence models.
- DRT or learned EIS embeddings.
- Policy ranking.
- Causal or same-cell counterfactual analysis.
- Broad multimodal degradation model claims.
