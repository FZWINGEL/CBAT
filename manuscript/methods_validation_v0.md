# Methods: Grouped Validation v0

The validation protocol treats the experimental design as 76 parameter-set
conditions with three replicate cells, not 228 independent regimes. Headline
evidence uses grouped validation so that replicates from the same condition do
not appear on both sides of a headline split.

The benchmark uses five grouped split views:

- `condition_fold`;
- `temperature_holdout_fold`;
- `c_rate_holdout_fold`;
- `profile_holdout_fold`;
- `voltage_window_holdout_fold`.

The C-rate, temperature, profile, and voltage-window splits test stressor-axis
generalization. Random row or random cell splits are not used as paper-facing
evidence because they can overstate performance by sharing condition structure
between train and test.

Capacity metrics are reported at row level and condition level. The central
paper-facing metric is condition-mean MAE, with worst-condition MAE used to
identify failure regimes. PULSE resistance baselines use the same grouped split
discipline and report target coverage counts. Paired comparisons, such as prior
PULSE versus F4 or prior PULSE versus strongest non-PULSE, aggregate by
parameter set and bootstrap over parameter-set conditions.

Leakage controls are part of the validation protocol. Inserted LOG_AGE
diagnostics are masked for interval prediction. Target-derived stress rates are
diagnostic only. For capacity prediction, prior `pulse_1s_resistance_k` is
allowed, but future PULSE state and PULSE deltas are forbidden.

Allowed claims:

- C12: grouped validation is required for publishable evidence.
- C03: C-rate holdout is the hardest capacity generalization view.

Blocked claims:

- Random row/cell splits are publishable headline evidence.
- Future PULSE state or PULSE deltas can be used as capacity input features.

Source artifacts:

- `docs/VALIDATION_PROTOCOL.md`
- `reports/audit/split_registry_report.json`
- `reports/synthesis/split_difficulty_summary.csv`

Figure/table references:

- Figure 2: grouped validation design.
- Table 3: split difficulty.
