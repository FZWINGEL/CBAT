# Results: Capacity-PULSE Coupling v0

Capacity-PULSE coupling diagnostics test whether PULSE resistance growth helps
explain capacity-model residuals. This is an explanatory diagnostic, not a
capacity+PULSE architecture claim.

The robust coupling analysis filters to canonical
`L2_hist_gradient_boosting + F4_state_log_age_scalar` capacity predictions and
checks interval-level, condition-level, bootstrap, subgroup, and residualized
correlations. PULSE growth remains associated with capacity residual magnitude,
especially in the C-rate split.

Key C-rate interval-level correlations:

| Target | Residual type | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | absolute residual | 143 | `0.857653` | `0.633959` |
| `delta_capacity_Ah` | absolute residual | 143 | `0.647125` | `0.646779` |

The prior-PULSE predictive tests then ask whether prior PULSE state improves
capacity prediction. Against F4, prior PULSE improves `capacity_Ah_k1` in
selected grouped splits:

| Split | Best prior-PULSE group | Mean gain vs F4 | p05 |
|---|---|---:|---:|
| C-rate | `C_P3_stress_pulse` | `0.00669208` | `0.000718651` |
| temperature | `C_P3_stress_pulse` | `0.00509620` | `0.00103230` |
| profile | `C_P0_state_time_pulse` | `0.0214905` | `0.0137834` |

The strongest-non-PULSE comparison blocks a stronger claim. C-rate
`capacity_Ah_k1` gain versus `F5_log_age_histograms` is only `0.000392605` with
p05 `-0.00553843`; temperature/profile mean gains are negative. C-rate
`delta_capacity_Ah` remains unsupported.

Allowed claims:

- C05: PULSE growth is associated with capacity residual magnitude, especially
  in C-rate views.
- C06: prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped
  splits.

Blocked claims:

- C07: prior PULSE beats the strongest supplied non-PULSE capacity baseline.
- C08: prior PULSE improves `delta_capacity_Ah`.
- PULSE growth is causal or independent of confounding.

Source artifacts:

- `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`
- `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`
- `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`

Figure/table references:

- Figure 8: capacity residual versus PULSE growth.
- Figure 9: prior PULSE versus strongest non-PULSE.
- Table 4: claim matrix.

Limitations:

- Coupling is explanatory, not causal.
- Prior PULSE does not solve fade-rate prediction.
- Strongest non-PULSE baselines remain competitive or better.
