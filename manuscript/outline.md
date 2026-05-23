# Manuscript Outline

## Abstract

State the benchmark, the grouped-validation discipline, the main positive
results, the negative results, and the gated future-work boundary.

## Introduction

- Why battery degradation prediction needs held-out operating-regime evidence.
- Why operating histories and diagnostics are promising but easy to overclaim.
- Why this paper is a benchmark and evidence-ladder contribution, not a new
  architecture.

## Dataset And Audit

- Luh-Blank dataset basis.
- 228 cells, 76 parameter-set conditions, 3 replicates each.
- Result modalities and generated data products.
- EIS and CBAT remain gated.

## Linked Data Products

- Cell condition table.
- Check-up event table.
- LOG_AGE table.
- Interval table.
- Split registry.
- Interval subset registry.
- Stress-feature sidecars.
- PULSE target table.

## Grouped Validation Protocol

- Condition-level grouping.
- Stressor holdouts: temperature, C-rate, profile, voltage-window.
- Strict/tolerant LOG_AGE monotonicity sensitivity.
- Leakage controls.
- Condition-level metrics.

## Capacity Baseline Ladder

- L0 persistence, Ridge, HGB.
- State-aware features.
- F4 LOG_AGE scalar baseline.
- C-rate as hardest split.
- Quantile outputs are diagnostics only.

## LOG_AGE Stress-Feature Experiments

- v1 stress sidecar.
- v1.1 current sign, timestamp-weighted dwell, event features.
- Mixed capacity-level gains.
- Failure to solve C-rate `delta_capacity_Ah`.
- Final 0.6.3 negative pass.

## PULSE QA And Resistance Baseline

- Canonical RT/50 target policy.
- Alignment and direction hardening.
- Missingness limitations.
- 1s and 10ms robustness.
- Scalar resistance baseline only.

## Capacity-PULSE Coupling Diagnostics

- Coupling table.
- Residual versus PULSE growth correlations.
- Interval/condition robustness.
- Residualized diagnostics.
- Explanatory, not causal or predictive architecture evidence.

## Prior-PULSE Predictive Boundary

- Prior PULSE over F4 for selected `capacity_Ah_k1` splits.
- Strongest non-PULSE comparison blocks stronger claim.
- `delta_capacity_Ah` remains unsupported.

## Negative Results And Limitations

- Stress features did not solve C-rate fade.
- Normalized delta-rate targets failed.
- Bias correction was neutral.
- F11-F13 did not beat F4.
- Prior PULSE did not beat strongest non-PULSE.
- Prior PULSE did not improve fade-rate prediction.
- Quantile HGB was not calibrated.
- EIS not tested yet.

## Claim Ladder

Summarize `docs/PAPER_CLAIM_LEDGER.md` and
`reports/synthesis/claim_matrix.csv`.

## Future Work

- Paper-first consolidation.
- Figure generation.
- Separately gated EIS QA.
- No CBAT/neural/policy work until evidence gates justify it.
