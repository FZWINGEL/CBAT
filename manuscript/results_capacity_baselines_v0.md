# Results: Capacity Baseline Ladder v0

The capacity baseline ladder establishes the first benchmark evidence. L0
persistence provides the reference. Ridge is retained as a linear sanity
baseline. HGB-50 with `F4_state_log_age_scalar` is the main scalar capacity
baseline before stress features and PULSE diagnostics are introduced.

The focused HGB-50 report shows that learning improves over persistence across
capacity targets and split views. For the central C-rate holdout, the best F4
condition-mean MAE values are:

| Target | Split | Best F4 condition-mean MAE |
|---|---|---:|
| `capacity_Ah_k1` | C-rate | `0.125186` |
| `delta_capacity_Ah` | C-rate | `0.101133` |

C-rate remains harder than the condition, temperature, profile, and
voltage-window views. Worst C-rate rows cluster in cold/cool high-C-rate
conditions and wide voltage-window families. This motivates the later
stress-feature and PULSE diagnostic analyses, but it also sets a strict boundary
for claims: later additions must beat strong grouped baselines, not only weak
or persistence baselines.

Allowed claims:

- C03: C-rate holdout is the dominant unresolved capacity generalization
  stressor.
- C12: headline evidence must use grouped validation and condition-level
  summaries.

Blocked claims:

- The baseline generalizes uniformly across stressor axes.
- Quantile HGB outputs are validated as calibrated intervals.

Key numbers:

- HGB F4 C-rate `capacity_Ah_k1`: `0.125186` condition-mean MAE.
- HGB F4 C-rate `delta_capacity_Ah`: `0.101133` condition-mean MAE.
- q10-q90 coverage: about `0.678207`, below nominal 0.8.

Source artifacts:

- `reports/baselines/capacity_hgb50_focused/plots/best_by_target_split.csv`
- `reports/baselines/capacity_hgb50_focused/claim_readiness.md`
- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`

Figure/table references:

- Figure 3: capacity baseline ladder.
- Figure 4: C-rate failure analysis.
- Table 2: model ladder.
- Table 3: split difficulty.

Limitations:

- C-rate holdout has fewer held-out parameter-set conditions than the full
  condition fold.
- Quantile outputs are diagnostic only.
