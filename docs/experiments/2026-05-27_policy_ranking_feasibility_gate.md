# Milestone 7.3 - Support-Bounded Contrast-Ordering Feasibility Gate

## Scope

This gate tests whether existing out-of-fold multi-horizon capacity predictions
can order matched observed policy contrasts from Milestone 7.2. It does not
train a ranking model, recommend policies, estimate causal effects, create
same-cell counterfactuals, or use K3 future-exposure rows as prospective
evidence.

## Command

```bash
mbp analysis evaluate-policy-ranking-feasibility \
  --contrast-registry data/interim/policy_contrast_registry_v1.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --predictions data/processed/capacity_horizon_l0_l2_predictions.parquet \
  --out-dir reports/analysis/policy \
  --targets delta_capacity_Ah_h,capacity_Ah_kh \
  --horizons 2,3 \
  --model-levels MH0_persistence,MH1_prior_slope_linear,MH2_ridge,MH3_hist_gradient_boosting \
  --feature-groups persistence,prior_slope,K2_nominal_condition,K3_oracle_exposure_diagnostic \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --bootstrap-count 200
```

## Outputs

- `reports/analysis/policy/policy_ranking_feasibility_report.json`
- `reports/analysis/policy/policy_ranking_pairwise_metrics.csv`
- `reports/analysis/policy/policy_ranking_by_family.csv`
- `reports/analysis/policy/policy_ranking_bootstrap.csv`
- `reports/analysis/policy/policy_ranking_claim_readiness.md`

## Result

The evaluator joined 225,744 selected prediction rows and generated 164,100
pairwise supported contrast-ordering rows from the 234 triplet-supported
contrasts. The primary prospective candidate was HGB K2
(`MH3_hist_gradient_boosting` / `K2_nominal_condition`) on
`delta_capacity_Ah_h` horizons 2 and 3.

Primary HGB K2 sign accuracy was informative but not strong enough for a
ranking claim:

| Split | Horizon | Pairwise rows | Sign accuracy |
|---|---:|---:|---:|
| c_rate_holdout_fold | 2 | 52 | 0.826923 |
| c_rate_holdout_fold | 3 | 27 | 0.888889 |
| condition_fold | 2 | 2874 | 0.797627 |
| condition_fold | 3 | 2647 | 0.790212 |
| profile_holdout_fold | 2 | 462 | 0.742424 |
| profile_holdout_fold | 3 | 432 | 0.679070 |
| temperature_holdout_fold | 2 | 867 | 0.860880 |
| temperature_holdout_fold | 3 | 793 | 0.851206 |
| voltage_window_holdout_fold | 2 | 2874 | 0.655914 |
| voltage_window_holdout_fold | 3 | 2647 | 0.707893 |

The strict bootstrap reference gate failed. For all-family
`delta_capacity_Ah_h` horizon-2/3 rows, HGB K2 passed `0/10` primary bootstrap
checks against the prior-slope reference. Several gains were negative; for
example, C-rate horizon 2 was `-0.0740741` versus prior slope with p05
`-0.190476`.

K3 future-exposure rows were retained only as `oracle_diagnostic_only` and are
not prospective evidence.

## Decision

Supported observed contrast ordering is `partially_supported`: existing HGB K2
forecasts contain useful ordering signal, including C-rate rows, but they do
not beat the prior-slope reference under the strict contrast-bootstrap rule.

Allowed wording:

> Existing prospective forecasts can be evaluated for supported observed
> contrast-ordering diagnostics, and HGB K2 shows partial diagnostic signal.

Forbidden wording:

> Policy ranking, policy recommendation, causal policy effects, same-cell
> counterfactuals, calibrated policy risk/utility, CBAT, or sequence/neural
> architecture work are authorized.

## Remaining Blockers

- HGB K2 does not pass the strict prior-slope bootstrap reference gate.
- C-rate rows are strong diagnostically but cannot authorize optimization or
  recommendation.
- K3 includes future exposure and remains oracle-diagnostic only.
- Calibration gates still block calibrated risk/utility wording.
- There is no randomized or same-cell counterfactual policy design.
