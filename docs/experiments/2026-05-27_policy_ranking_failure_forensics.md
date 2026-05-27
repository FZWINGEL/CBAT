# Milestone 7.4 - Policy Ranking Failure Forensics

## Scope

This milestone diagnoses the Milestone 7.3 supported contrast-ordering near
miss. It is a report-only pass over existing 7.3 artifacts:

- `reports/analysis/policy/policy_ranking_pairwise_metrics.csv`
- `reports/analysis/policy/policy_ranking_by_family.csv`
- `reports/analysis/policy/policy_ranking_bootstrap.csv`

No models were trained, no features were added, and no prediction Parquet was
regenerated.

## Command

```bash
mbp analysis diagnose-policy-ranking-feasibility \
  --pairwise-metrics reports/analysis/policy/policy_ranking_pairwise_metrics.csv \
  --by-family reports/analysis/policy/policy_ranking_by_family.csv \
  --bootstrap reports/analysis/policy/policy_ranking_bootstrap.csv \
  --out-dir reports/analysis/policy
```

## Outputs

- `reports/analysis/policy/policy_ranking_failure_forensics_report.json`
- `reports/analysis/policy/policy_ranking_failure_forensics.md`
- `reports/analysis/policy/policy_ranking_failure_claim_readiness.md`
- `reports/analysis/policy/plots/effect_size_threshold_sign_accuracy.csv`
- `reports/analysis/policy/plots/rank_correlation_diagnostics.csv`
- `reports/analysis/policy/plots/topk_regret_diagnostics.csv`
- `reports/analysis/policy/plots/hgb_vs_prior_failure_bins.csv`

## Results

The forensics generated 1,680 effect-threshold rows, 336 rank-correlation rows,
672 top-k/regret rows, and 306 HGB-vs-prior failure-bin rows. K3 oracle rows
were excluded from prospective readiness; 54,700 oracle pairwise rows were
counted only as oracle diagnostics.

The strict Milestone 7.3 prior-slope gate still fails: `0/10` primary
HGB-vs-prior all-family checks pass. Large-effect rows show some signal but not
enough to open a policy branch. The readiness report records large-effect
passing families `charge_c_rate` and `temperature`, C-rate medium/large pass
rows `1/4`, and HGB `ge_0.02Ah` mean sign accuracy `0.856314`. Rank metrics
are also diagnostic only: HGB K2 Spearman exceeds prior slope in three contrast
families, but this does not validate recommendation quality.

## Decision

Milestone 7.4 supports only failure decomposition. It does not authorize policy
ranking, policy recommendation, causal policy effects, same-cell
counterfactuals, calibrated policy risk/utility, CBAT, or sequence/neural
branches.

At most, the result suggests a possible future predeclared large-effect
supported-contrast gate. That gate is not opened here.
