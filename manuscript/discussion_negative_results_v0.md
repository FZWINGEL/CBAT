# Discussion: Negative Results v0

The negative results are part of the contribution because they prevent the
benchmark from becoming an overclaiming exercise.

## LOG_AGE Stress Features

The stress-feature path improved some condition and temperature metrics, but it
did not solve C-rate `delta_capacity_Ah`. The v1.1 C-rate `delta_capacity_Ah`
best stress row was `0.102516`, worse than the F4 threshold `0.101133`.
Normalized delta-rate targets, train-fold residual correction, and F11-F13
cold/current feature groups did not reverse that conclusion.

Interpretation: scalar stress summaries provide useful diagnostic signal, but
the current formulation is not sufficient for C-rate fade prediction.

## Prior PULSE

Prior PULSE state improved `capacity_Ah_k1` over F4 in selected grouped splits,
but did not beat the strongest supplied non-PULSE baselines. It also did not
improve C-rate `delta_capacity_Ah`.

Interpretation: prior PULSE is useful as a capacity-level diagnostic feature in
defined comparisons, but it is not the best current feature path and does not
support a fade-rate claim.

## Quantile HGB

The q10-q90 interval coverage was about `0.678207`, below the nominal central
0.8 interval.

Interpretation: quantile outputs are diagnostic and cannot be described as
validated calibrated intervals.

## EIS

EIS products exist in the data-product stack, but EIS valid-frequency QA and
predictive tests are not complete.

Interpretation: EIS remains a future gated modality and should not be included
in current performance claims.

Allowed claims:

- Negative results constrain the paper's claim ladder.
- The current benchmark is useful because it identifies what does not yet work
  under grouped validation.

Blocked claims:

- Stress features solve C-rate fade prediction.
- Prior PULSE supports a capacity fade-rate claim.
- Quantile HGB provides validated calibrated intervals.
- EIS has demonstrated predictive value.

Source artifacts:

- `reports/synthesis/negative_results.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `reports/synthesis/reviewer_risk_register.md`

Figure/table references:

- Table 5: negative results.
- Figure 10: claim ladder.
