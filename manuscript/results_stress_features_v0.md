# Results: LOG_AGE Stress Features v0

LOG_AGE scalar summaries and stress features were tested after the baseline
capacity ladder. The central question was whether actual operating-history
features improve held-out generalization beyond state/time and nominal protocol
features, especially on the C-rate split.

The scalar LOG_AGE F4 result is mixed. The adjacent HGB feature gain from
`F3_state_nominal` to `F4_state_log_age_scalar` has mean gain `0.000085`,
median gain `0.001124`, and positive rows in `10 / 20` primary views. This
supports cautious wording: current scalar LOG_AGE summaries help nonlinear
models in some grouped views, but gains are mixed.

The v1/v1.1 stress-feature path added voltage, temperature, SOC, current,
coupled-stress, timestamp-weighted dwell, current-sign audit, and scalar event
features. It improved several condition and temperature views and improved
C-rate `capacity_Ah_k1` from F4 `0.125186` to `0.120605`. However, C-rate
`delta_capacity_Ah` did not beat the F4 threshold:

| Target | F4 baseline | Best v1.1 stress row | Outcome |
|---|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.120605` | improved but below materiality threshold |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.102516` | not supported |

Milestone 0.6.3 then tested normalized delta-rate targets, train-fold residual
correction, and narrow cold/current feature groups. None beat the F4 C-rate
`delta_capacity_Ah` threshold.

Allowed claims:

- C01: current scalar LOG_AGE summaries help nonlinear models in some grouped
  views, but gains are mixed.
- Stress features are useful diagnostics and help some folds.

Blocked claims:

- C02: LOG_AGE stress features solve C-rate fade prediction.

Key numbers:

- F3 to F4 mean gain: `0.000085`, positive rows `10 / 20`.
- v1.1 C-rate `capacity_Ah_k1`: `0.120605`.
- v1.1 C-rate `delta_capacity_Ah`: `0.102516` versus F4 `0.101133`.

Source artifacts:

- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`
- `docs/experiments/2026-05-22_log_age_stress_features_v1_1.md`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`
- `reports/synthesis/negative_results.md`

Figure/table references:

- Figure 5: LOG_AGE stress-feature decision.
- Table 5: negative results.

Limitations:

- Stress features are scalar interval summaries, not sequence models.
- The C-rate fade result remains unresolved.
