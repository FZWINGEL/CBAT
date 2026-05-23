# Introduction v0

Battery degradation is path-dependent: temperature, voltage window, state of
charge, C-rate, current profile, rest periods, and prior age interact over time.
Open aging datasets increasingly include operating histories and diagnostic
check-ups, but the central modeling question is not whether a model can fit
cells from familiar regimes. The harder question is whether it can generalize
to held-out operating regimes.

This manuscript treats that question as a benchmark-design problem before it is
an architecture problem. The Luh-Blank dataset provides a useful setting because
it combines capacity check-ups, PULSE resistance, EIS records, and LOG_AGE
operating histories across 228 cells. Those 228 cells represent 76
parameter-set conditions with three replicates each, so condition-level grouping
is essential. Random row or cell splits would overstate evidence by mixing
replicates and operating regimes across train and test.

The study builds a linked interval-level data-product stack and evaluates
capacity and resistance baselines under condition and stressor holdouts. It
tests whether scalar LOG_AGE summaries, physically motivated stress features,
and prior PULSE state add useful information beyond simpler state and protocol
features. It also records negative results as part of the contribution:
stress-feature engineering does not solve C-rate fade prediction, prior PULSE
does not beat the strongest supplied non-PULSE capacity baseline, and quantile
HGB outputs are not calibrated.

Allowed claims:

- C03: C-rate holdout is the hardest capacity generalization view.
- C04: RT/50 PULSE is usable as a scalar resistance endpoint.
- C05: PULSE growth is associated with capacity residual magnitude.
- C06: prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped splits.

Blocked claims:

- C07: prior PULSE beats the strongest supplied non-PULSE capacity baseline.
- C08: prior PULSE improves `delta_capacity_Ah`.
- C10: EIS has demonstrated predictive value.
- C11: CBAT architecture is justified.

Source artifacts:

- `docs/PROJECT_CHARTER.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `reports/synthesis/claim_matrix.csv`
