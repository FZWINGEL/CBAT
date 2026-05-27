# Milestone 8.5 - C-rate Repair Feasibility Finalization Gate

## Scope

This gate finalizes the C-rate repair decision using existing evidence only. It
does not train a new model, add features, recommend policies, or make causal
claims. The goal is to connect the Milestone 8.4 C-rate root-cause/support
diagnostics to the existing train-only adaptive stressor-robust replication and
targeted stressor-family arm-router reports.

## Command

```bash
mbp analysis finalize-c-rate-repair-feasibility \
  --c-rate-report reports/analysis/c_rate_generalization/c_rate_failure_report.json \
  --support-overlap reports/analysis/c_rate_generalization/c_rate_support_overlap.csv \
  --adaptive-replication-report reports/baselines/capacity_stressor_robust_adaptive_replication/replication_summary.json \
  --arm-selector-report reports/baselines/capacity_stressor_robust_arm_selector_report.json \
  --out-dir reports/analysis/c_rate_repair_feasibility
```

## Outputs

- `reports/analysis/c_rate_repair_feasibility/c_rate_repair_feasibility_report.json`
- `reports/analysis/c_rate_repair_feasibility/c_rate_repair_decision.md`
- `reports/analysis/c_rate_repair_feasibility/c_rate_repair_claim_readiness.md`
- `reports/analysis/c_rate_repair_feasibility/plots/c_rate_repair_evidence_matrix.csv`
- `reports/analysis/c_rate_repair_feasibility/plots/c_rate_repair_support_summary.csv`

## Result

The gate supports a narrow diagnostic C-rate `delta_capacity_Ah` repair claim:

- C-rate root-cause diagnostics: `supported_for_diagnostics`
- Train-only support overlap: `supported_for_diagnostics`
- Train-only adaptive conservative repair: `supported_for_diagnostics`
- Targeted stressor-family routing: `supported_for_diagnostics`

The key numeric evidence is:

- 336 C-rate condition-hotspot rows from Milestone 8.4.
- 76 C-rate support-overlap rows, with 52 low-support rows.
- Adaptive conservative repair: minimum C-rate gain versus stress reference
  `0.0214266`, paired p05 `0.00465696`, outside-C-rate degradation
  `0.0279117`.
- Targeted router: C-rate gain versus D0/F4 `0.0106361`, paired p05
  `0.00594397`, outside-C-rate degradation `0`.

## Decision

Allowed wording:

> Existing non-neural train-only adaptive selection and targeted routing support
> a narrow diagnostic repair for C-rate `delta_capacity_Ah` transfer.

Forbidden wording:

- C-rate fade is solved.
- The benchmark has a globally robust capacity model.
- The result authorizes CBAT, policy ranking, calibrated risk, calibrated
  uncertainty, neural/sequence models, or causal claims.

## Remaining blockers

Broad robust capacity remains `not_supported`. Architecture, policy,
calibration, and causality remain `blocked`.
