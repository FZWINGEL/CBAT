# Figure 03: Capacity Baseline Ladder

Claim supported: C03 C-rate difficulty and C12 grouped reporting.

Source artifacts:

- `reports/synthesis/model_ladder_summary.csv`
- `reports/baselines/capacity_hgb50_focused/plots/best_by_target_split.csv`

Intended plot type: grouped bar chart by model family, target, and split.

Key numbers:

- HGB F4 C-rate `capacity_Ah_k1`: `0.125186`.
- HGB F4 C-rate `delta_capacity_Ah`: `0.101133`.
- L0 C-rate reference: `0.334853996`.

Risk/limitation:

- Best-row metrics are descriptive; claim support depends on paired comparison
  reports and the claim ledger.

Caption draft:

> Capacity baseline ladder under grouped validation. HGB baselines improve over
> persistence, but C-rate remains the hardest capacity split for both
> `capacity_Ah_k1` and `delta_capacity_Ah`.
