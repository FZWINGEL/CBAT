# Figure 07: PULSE Resistance Baseline

Claim supported: C04 PULSE scalar resistance diagnostics.

Source artifact:

- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`

Intended plot type: grouped bar chart for 1s/10ms and delta/k1 targets across
split views.

Key numbers:

- `delta_pulse_1s_resistance` C-rate MAE: `0.00185842`.
- `delta_pulse_1s_resistance` condition-fold MAE: `0.000960407`.
- `delta_pulse_10ms_resistance` is viable secondary diagnostic.

Risk/limitation:

- k1 state targets and delta transition targets should be interpreted
  separately.

Caption draft:

> Scalar PULSE resistance baselines. RT/50 1s and 10ms resistance targets are
> predictable enough for grouped diagnostic reporting, but they remain scalar
> resistance endpoints rather than multimodal capacity claims.
