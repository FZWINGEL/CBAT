# Milestone 8.0 - Support-Aware Selective Reliability Gate

## Question

Can train-only condition-support scores identify more reliable subsets of the
existing capacity-horizon, threshold-warning, and supported contrast-ordering
predictions?

This is an abstention and support-audit diagnostic. It does not retrain models,
create predictor features, recommend policies, estimate causal effects,
validate calibrated risk, or justify CBAT.

## Command

```bash
mbp analysis diagnose-support-reliability \
  --interval-table data/interim/interval_table.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --capacity-predictions data/processed/capacity_horizon_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --warning-predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --policy-pairwise reports/analysis/policy/policy_ranking_pairwise_metrics.csv \
  --out-dir reports/analysis/support_reliability
```

## Outputs

- `reports/analysis/support_reliability/support_reliability_report.json`
- `reports/analysis/support_reliability/support_reliability_diagnostics.md`
- `reports/analysis/support_reliability/support_reliability_claim_readiness.md`
- `reports/analysis/support_reliability/plots/support_distance_by_split.csv`
- `reports/analysis/support_reliability/plots/selective_capacity_performance.csv`
- `reports/analysis/support_reliability/plots/selective_threshold_warning_performance.csv`
- `reports/analysis/support_reliability/plots/selective_policy_contrast_performance.csv`

## Result

The report generated:

| Artifact | Rows |
|---|---:|
| support-distance rows | 380 |
| capacity selective rows | 2,000 |
| threshold-warning selective rows | 975 |
| policy-contrast selective rows | 1,680 |

At 50% support-score retention, the primary diagnostic gains are mixed:

| Area | 50% retention effect |
|---|---:|
| capacity-horizon MAE gain | -0.0115957 |
| threshold-warning Brier gain | -0.0040389 |
| policy sign-accuracy gain | 0.0173861 |
| C-rate primary capacity MAE gain | -0.0525537 |

Positive gain means support filtering improved the metric. The capacity and
threshold-warning primary metrics worsen, while policy sign accuracy improves
slightly. C-rate support reliability fails.

## Decision

Support-distance diagnostics are `supported_for_diagnostics` as an audit layer.
Selective prediction reliability is `diagnostic_only`. C-rate support
reliability is `not_supported`.

This does not authorize:

- policy recommendation;
- causal or same-cell counterfactual claims;
- calibrated risk;
- deployment reliability;
- CBAT or architecture readiness;
- sequence/neural model reopening.

## Next Action

Keep support scoring as an audit and abstention diagnostic only. Do not open a
policy, deployment, calibrated-risk, or CBAT branch from this evidence. A future
support-aware branch would need a predeclared gate that improves primary
capacity, threshold-warning, and C-rate reliability without using outcome-based
selection.
