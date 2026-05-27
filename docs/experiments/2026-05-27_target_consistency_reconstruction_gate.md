# Milestone 8.7 - Target-Consistency Reconstruction Audit

## Purpose

Milestone 8.7 tests one narrow follow-up to the C-rate repair boundary result:
whether the successful `delta_capacity_Ah` repair can be reconstructed into a
capacity-level forecast with:

```text
capacity_Ah_k1_pred = capacity_Ah_k + predicted_delta_capacity_Ah
```

This is a report-only diagnostic over existing prediction artifacts. It does
not train a model, add features, relax guardrails, calibrate risk, recommend
policies, or make causal claims.

## Inputs

- `data/interim/interval_table.parquet`
- `data/processed/capacity_stressor_robust_adaptive_boundary_predictions.parquet`
- `data/processed/capacity_stressor_robust_arm_selector_boundary_predictions.parquet`
- `reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_report.json`

## Command

```bash
mbp analysis diagnose-target-consistency-reconstruction \
  --interval-table data/interim/interval_table.parquet \
  --adaptive-predictions data/processed/capacity_stressor_robust_adaptive_boundary_predictions.parquet \
  --arm-selector-predictions data/processed/capacity_stressor_robust_arm_selector_boundary_predictions.parquet \
  --boundary-report reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_report.json \
  --out-dir reports/analysis/target_consistency_reconstruction
```

## Outputs

- `reports/analysis/target_consistency_reconstruction/target_consistency_reconstruction_report.json`
- `reports/analysis/target_consistency_reconstruction/target_consistency_reconstruction_decision.md`
- `reports/analysis/target_consistency_reconstruction/target_consistency_claim_readiness.md`
- `reports/analysis/target_consistency_reconstruction/plots/direct_vs_derived_target_paths.csv`
- `reports/analysis/target_consistency_reconstruction/plots/c_rate_reconstruction_gain.csv`
- `reports/analysis/target_consistency_reconstruction/plots/outside_split_reconstruction_guardrail.csv`

## Result

The direct delta repair remains supported for diagnostics:

- adaptive direct-delta C-rate gain versus F4: `0.0200436`
- adaptive direct-delta paired p05 versus F4: `0.00749857`
- router direct-delta C-rate gain versus F4: `0.0106361`
- router direct-delta paired p05 versus F4: `0.00594397`

Capacity reconstructed from predicted delta improves the C-rate capacity row:

- adaptive `capacity_Ah_k + predicted_delta` gain versus direct F4 capacity:
  `0.0440972`
- adaptive reconstructed-capacity gain versus direct stress capacity:
  `0.041353`
- router reconstructed-capacity gain versus direct F4 capacity: `0.0346897`

However, the router reconstructed-capacity path fails the outside-split
non-degradation guardrail:

- router reconstructed-capacity max outside-split degradation: `0.293828`
- required guardrail: `<=0.05`

## Decision

- Delta target-path consistency: `supported_for_diagnostics`
- Capacity-from-delta transfer versus direct references: `not_supported`
- Capacity-from-delta transfer versus derived references: `diagnostic_only`
- Two-target C-rate repair wording: `not_supported`
- Architecture, policy, calibration, and causality: `blocked`

## Claim posture

Allowed:

> C-rate `delta_capacity_Ah` repair remains a narrow diagnostic result, and
> capacity-from-delta reconstruction is useful for target-path forensics,
> especially for derived-vs-derived comparisons.

Forbidden:

- capacity-level repair is supported;
- two-target C-rate repair is supported;
- broad robust capacity is supported;
- C-rate fade is solved;
- CBAT, policy ranking, calibrated risk/uncertainty, neural/sequence, or
  causal claims are authorized.
