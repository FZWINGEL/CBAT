# Milestone 7.2 - Policy-Contrast Support and Observed Ranking Feasibility Gate

## Purpose

This gate checks whether the dataset has enough matched observed condition
contrasts to support a later, separately gated policy-ranking feasibility task.
It does not train a ranking model, recommend policies, estimate causal effects,
or make same-cell counterfactual claims.

## Commands

```bash
.venv/bin/mbp analysis build-policy-contrast-registry \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/policy_contrast_registry_v1.parquet

.venv/bin/mbp analysis policy-contrast-qa \
  --contrast-registry data/interim/policy_contrast_registry_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/analysis/policy/policy_contrast_support_report.json \
  --registry-out reports/analysis/policy/policy_contrast_registry.csv \
  --family-out reports/analysis/policy/policy_contrast_by_family.csv

.venv/bin/mbp analysis evaluate-observed-policy-contrasts \
  --contrast-registry data/interim/policy_contrast_registry_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out-dir reports/analysis/policy
```

## Outputs

- `data/interim/policy_contrast_registry_v1.parquet` (ignored generated data)
- `reports/analysis/policy/policy_contrast_support_report.json`
- `reports/analysis/policy/policy_contrast_registry.csv`
- `reports/analysis/policy/policy_contrast_by_family.csv`
- `reports/analysis/policy/observed_policy_contrast_report.json`
- `reports/analysis/policy/observed_policy_ranking_stability.csv`
- `reports/analysis/policy/policy_ranking_feasibility.md`
- `reports/analysis/policy/policy_claim_readiness.md`

## Result

The registry contains 234 matched observed contrasts. All 234 have triplet
support. Family support is:

| Family | Contrasts | Median common check-ups |
|---|---:|---:|
| charge_c_rate | 36 | 5 |
| profile | 12 | 16 |
| temperature | 114 | 14 |
| voltage_window | 72 | 15 |

Observed capacity-loss sign stability is high:

- observed stability rows: 3,213;
- sign-stable rows: 2,943;
- sign-stable fraction: 0.916.

Family-level sign-stable fractions range from 0.893985 for temperature to
0.954464 for voltage-window contrasts.

## Decision

Matched observed policy-contrast support is `supported_for_diagnostics`, and
observed capacity-loss sign stability is `supported_for_diagnostics`.

This only authorizes observed support and degradation-order diagnostics. A
future ranking-feasibility baseline is only a possible next gate and would need
its own predeclared validation, uncertainty, and no-overclaim rules.

Still blocked:

- policy ranking;
- policy recommendation;
- causal intervention claims;
- same-cell counterfactual claims;
- CBAT;
- calibrated risk;
- sequence/neural architecture work.
