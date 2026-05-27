# Milestone 8.6 - C-rate Repair Boundary and Transfer Audit

## Scope

This gate tests whether the narrow Milestone 8.5 C-rate repair result transfers
from `delta_capacity_Ah` to `capacity_Ah_k1`. It uses existing non-neural
stressor-robust machinery only. It does not add features, model families,
neural/sequence models, CBAT, policy ranking, calibrated-risk claims,
calibrated-uncertainty claims, or causal claims.

## Commands

```bash
mbp baseline run-stressor-robust-adaptive \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stressor_robust_adaptive_boundary_report.json \
  --predictions-out data/processed/capacity_stressor_robust_adaptive_boundary_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_adaptive_boundary \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --selection-policy conservative_guarded \
  --hgb-max-iter 50

mbp baseline run-stressor-robust-arm-selector \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --attribution-report reports/baselines/capacity_stressor_robust_attribution_report.json \
  --attribution-predictions data/processed/capacity_stressor_robust_attribution_predictions.parquet \
  --out reports/baselines/capacity_stressor_robust_arm_selector_boundary_report.json \
  --predictions-out data/processed/capacity_stressor_robust_arm_selector_boundary_predictions.parquet \
  --out-dir reports/baselines/capacity_stressor_robust_arm_selector_boundary \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --hgb-max-iter 50

mbp analysis diagnose-c-rate-repair-boundary \
  --adaptive-report reports/baselines/capacity_stressor_robust_adaptive_boundary_report.json \
  --adaptive-predictions data/processed/capacity_stressor_robust_adaptive_boundary_predictions.parquet \
  --arm-selector-report reports/baselines/capacity_stressor_robust_arm_selector_boundary_report.json \
  --arm-selector-predictions data/processed/capacity_stressor_robust_arm_selector_boundary_predictions.parquet \
  --support-overlap reports/analysis/c_rate_generalization/c_rate_support_overlap.csv \
  --out-dir reports/analysis/c_rate_repair_boundary
```

## Outputs

- `reports/baselines/capacity_stressor_robust_adaptive_boundary_report.json`
- `reports/baselines/capacity_stressor_robust_arm_selector_boundary_report.json`
- `reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_report.json`
- `reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_decision.md`
- `reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_claim_readiness.md`
- `reports/analysis/c_rate_repair_boundary/plots/target_boundary_matrix.csv`
- `reports/analysis/c_rate_repair_boundary/plots/split_guardrail_matrix.csv`
- `reports/analysis/c_rate_repair_boundary/plots/support_stratum_gain_matrix.csv`

The prediction Parquets under `data/processed/` are generated artifacts and
remain ignored.

## Result

The boundary audit keeps the repair claim narrow.

| Method | Target | C-rate gain vs F4 | C-rate gain vs stress | p05 vs F4 | p05 vs stress | Outside degradation | Pass |
|---|---:|---:|---:|---:|---:|---:|---|
| adaptive R2/F8 | `delta_capacity_Ah` | `0.0200436` | `0.0214266` | `0.00749857` | `0.00465696` | `0.0279117` | yes |
| targeted router | `delta_capacity_Ah` | `0.0106361` | n/a | `0.00594397` | n/a | `0` | yes |
| adaptive R2/F8 | `capacity_Ah_k1` | `-0.00527031` | `-0.00801457` | `-0.0166214` | `-0.0161765` | `0.0102366` | no |
| targeted router | `capacity_Ah_k1` | `0` | n/a | `0` | n/a | `0` | no |

Support-stratified rows are available for diagnostics, but the matched C-rate
prediction rows land in the higher-support stratum for this boundary run. They
do not change the target decision: delta-capacity gains are positive, while
capacity-level gains are negative or zero.

## Decision

Allowed wording:

> Existing non-neural adaptive selection and targeted routing support a narrow
> diagnostic C-rate `delta_capacity_Ah` repair, and Milestone 8.6 confirms that
> this should not be broadened to `capacity_Ah_k1`.

Forbidden wording:

- C-rate fade is solved.
- C-rate capacity-level transfer is repaired.
- The benchmark has a globally robust capacity model.
- Two-target C-rate repair is supported.
- Architecture, CBAT, policy ranking, calibrated risk, calibrated uncertainty,
  neural/sequence models, or causal claims are authorized.

## Remaining blockers

Broad robust capacity remains `not_supported`. Capacity-level C-rate transfer
remains `not_supported`. Architecture, policy, calibration, neural/sequence,
CBAT, and causality remain `blocked`.
