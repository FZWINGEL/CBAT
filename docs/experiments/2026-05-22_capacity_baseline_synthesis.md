# 2026-05-22 Capacity Baseline Synthesis

## Scope

Milestone 0.5c turns the completed scalar capacity baseline diagnostics into a
decision-ready synthesis. It does not add EIS/PULSE features, knee labels,
sequence models, neural models, policy ranking, or CBAT architecture.

Primary artifacts:

- `reports/baselines/capacity_hgb50_focused/baseline_diagnostics.md`
- `reports/baselines/capacity_hgb50_focused/c_rate_holdout_error_analysis.md`
- `reports/baselines/capacity_hgb50_focused/claim_readiness.md`
- `reports/baselines/capacity_hgb50_focused/plots/best_by_target_split.csv`
- `reports/baselines/capacity_hgb50_focused/plots/feature_gain_by_split.csv`
- `reports/baselines/capacity_hgb50_focused/plots/c_rate_grouped_summaries.csv`

## Reference Comparison

Focused HGB-50 diagnostics were regenerated with the full bounded L0-L3 report
as the persistence reference:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-capacity \
  --report reports/baselines/capacity_hgb50_focused_report.json \
  --reference-report reports/baselines/capacity_l0_l3_report.json \
  --out-dir reports/baselines/capacity_hgb50_focused
```

This fills the HGB-50 `Improvement vs L0`, `Persistence error`, and
`Improvement` fields that were previously unavailable because the focused
HGB-50 report did not include `L0_persistence`.

## Synthesis Questions

### Does learning beat persistence?

Yes for the focused HGB-50 best rows. With the L0 reference report attached,
the best HGB-50 rows improve over persistence for every target/split view.

Selected improvements over L0 condition-mean MAE:

| Target | Split | Best row | Improvement vs L0 |
|---|---|---|---:|
| `capacity_Ah_k1` | `condition_fold` | `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` | 0.084084 |
| `delta_capacity_Ah` | `condition_fold` | `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` | 0.093366 |
| `capacity_Ah_k1` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` | 0.209668 |
| `delta_capacity_Ah` | `c_rate_holdout_fold` | `L2_hist_gradient_boosting` + `F4_state_log_age_scalar` | 0.233721 |

### Does prior capacity state matter?

Yes. `capacity_Ah_k` is an observed check-up state at the interval start and is
included in `F1_state_time` and all later non-persistence feature groups. The
baseline ladder should continue to keep `F0_time_only` as a weak sanity
baseline, but headline learned baselines should be state-aware.

### Do exposure deltas help?

Not consistently by themselves in the focused HGB-50 report.

`F1_state_time -> F2_state_exposure` primary condition-mean MAE gain:

- mean: `-0.002655`
- median: `-0.000247`
- positive rows: `10 / 20`

The current EFC/Ah deltas alone are not enough to explain the remaining OOD
stress gap.

### Do nominal protocol features help?

Yes. Nominal protocol features are the most consistent adjacent feature gain in
the focused HGB-50 report.

`F2_state_exposure -> F3_state_nominal` primary condition-mean MAE gain:

- mean: `0.008439`
- median: `0.006469`
- positive rows: `19 / 20`

Keep `aging_mode`, nominal temperature, voltage-window family, and nominal
C-rate features in the first publishable capacity baseline.

### Do LOG_AGE scalar features help?

Partially. The answer is model-dependent.

For focused HGB-50, `F3_state_nominal -> F4_state_log_age_scalar` primary
condition-mean MAE gain was:

- mean: `0.000085`
- median: `0.001124`
- positive rows: `10 / 20`

The best focused HGB-50 rows for condition, temperature, voltage-window, and
C-rate splits often use `F4_state_log_age_scalar`. This changes the
interpretation from "LOG_AGE scalar features do not help" to "current scalar
LOG_AGE features help nonlinear models in some views, but are too weak and
mixed for a broad exposure-feature claim."

### Is C-rate still hardest?

Yes. The best focused HGB-50 C-rate errors remain larger than the other best
split rows:

- `capacity_Ah_k1` C-rate condition-mean MAE: `0.125186`
- `delta_capacity_Ah` C-rate condition-mean MAE: `0.101133`

Worst C-rate conditions are concentrated in cold/cool high-C-rate settings:

| Parameter set | Target | Temperature C | Voltage family | Error | Persistence error | Improvement |
|---:|---|---:|---|---:|---:|---:|
| 36 | `capacity_Ah_k1` | 10 | `approx_10_100` | 0.276435 | 0.557172 | 0.280737 |
| 32 | `capacity_Ah_k1` | 10 | `approx_0_100` | 0.247365 | 0.556422 | 0.309057 |
| 20 | `delta_capacity_Ah` | 0 | `approx_0_100` | 0.193506 | 0.484002 | 0.290497 |
| 20 | `capacity_Ah_k1` | 0 | `approx_0_100` | 0.176425 | 0.484002 | 0.307577 |

C-rate grouped diagnostics:

- by temperature, mean best error is highest at `10 C` (`0.154004`) and next
  highest at `0 C` (`0.132982`);
- by voltage window, `approx_0_100` (`0.146666`) and `approx_10_100`
  (`0.135481`) are harder than `approx_10_90` (`0.057331`);
- smaller interval-count buckets remain harder than `>20` interval conditions.

This points to high-current transfer interacting with cold/cool conditions,
voltage window, and sparse interval histories.

### Does strict-vs-tolerant monotonicity sensitivity alter conclusions?

Not materially. The HGB-50 focused report has mean primary-minus-sensitivity
condition-mean MAE `-0.002432` and median `-0.002194`. The tolerant subset
remains acceptable as the primary subset, with strict exclusion retained as a
mandatory sensitivity check.

### Are quantile intervals calibrated?

No calibration claim is supported. Primary HGB-50 q10-q90 coverage is
approximately `0.678207`, below the nominal 0.8 central interval. Quantile
metrics should remain diagnostics only until calibration is explicitly tested.

## Decision

Do not expand to PULSE, EIS, sequence models, neural models, policy ranking, or
CBAT yet.

The next engineering milestone should be **LOG_AGE-derived scalar stress
features**, targeted at C-rate generalization. Candidate feature families:

- voltage dwell and voltage-bin exposure;
- cold/hot temperature dwell;
- current and C-rate-bin exposure;
- coupled cold x high-charge-current exposure;
- high-voltage x high-temperature exposure;
- SOC-bin exposure and high-SOC dwell;
- rate-normalized degradation features such as capacity loss per EFC, Ah, and
  day.

Success criterion for the next milestone:

> Improve C-rate holdout condition-mean MAE over the current HGB-50
> `F4_state_log_age_scalar` baseline without degrading condition-fold and
> temperature-fold performance.

## Follow-Up

Milestone 0.6 stress-feature v1 is documented in
`docs/experiments/2026-05-22_log_age_stress_features_v1.md`.

The v1 result is mixed after target-derived normalized-rate fields were excluded
from predictive feature groups: `capacity_Ah_k1` C-rate improved marginally, but
`delta_capacity_Ah` C-rate degraded. The project should harden stress features
before expanding to PULSE/EIS/CBAT.
