# Figure 09: Prior PULSE Versus Strongest Non-PULSE

Claim supported: C06 selected F4 gains and C07 not-supported strongest
non-PULSE claim.

Source artifact:

- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`

Intended plot type: paired gain forest plot with bootstrap p05/p50/p95.

Key numbers:

- C-rate `capacity_Ah_k1` gain versus strongest non-PULSE: `0.000392605`, p05
  `-0.00553843`.
- temperature `capacity_Ah_k1` gain: `-0.000753049`.
- profile `capacity_Ah_k1` gain: `-0.000697582`.
- C-rate `delta_capacity_Ah` gain: `-0.00234428`.

Risk/limitation:

- Prior PULSE improves over F4 in selected splits, but not over strongest
  supplied non-PULSE baselines.

Caption draft:

> Prior PULSE predictive boundary. Prior PULSE improves capacity level over F4
> in selected splits, but paired comparisons against the strongest supplied
> non-PULSE HGB baselines do not support a stronger predictive claim.
