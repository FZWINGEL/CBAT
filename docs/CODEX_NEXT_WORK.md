# Codex Next Work

Current recommended branch: stressor-robustness forensics or synthesis/release maintenance.

## Current Phase

Milestone 5.1 evaluates whether non-neural stressor-axis robust HGB variants
can improve the hard C-rate capacity/fade split without degrading other
grouped views. It is limited to existing capacity feature groups and grouped
validation; it is not an architecture or policy-ranking branch.

## Current Result

Stressor-balanced HGB with `F8_timestamp_weighted_stress` improves C-rate
`delta_capacity_Ah` to condition-mean MAE `0.0705429`, versus F4 R0
`0.101133` and stress R0 `0.102516`, with paired bootstrap p05 above zero
against both references. The global robust-capacity claim is still
`not_supported` because outside-C-rate relative degradation reaches
`0.0528343`, above the 5% guardrail.

## Optional Technical Branch

No broader technical branch is currently justified. Future technical work, if
opened, should be a narrow voltage-window/stressor-robustness forensics pass or
release automation task, not CBAT, policy ranking, sequence modeling, or new
modality expansion.

## Blocked Branches

Do not open:

- CBAT architecture
- neural models
- sequence models
- transformers
- DRT
- learned EIS embeddings
- policy ranking
- detector-knee prediction
- causal or mechanistic claims
- same-cell counterfactual claims
- broad multimodal degradation claims
- calibrated risk or calibrated uncertainty claims without grouped evidence
- robust-capacity/fade-solved claims without passing non-degradation guardrails

## Updating Phase Docs

When a phase changes, update:

- `AGENTS.md`
- `docs/REPO_STATUS.md`
- `docs/VALIDATION_PROTOCOL.md`
- `docs/DECISION_LOG.md`

For scientific work, also update the relevant experiment memo, claim ledger,
claim matrix, and source artifacts.

## Avoiding Overclaims

Use the v2 claim ledger and claim matrix as the source of truth. If a claim is
blocked or not supported there, do not restate it as supported in a new report.

Allowed current wording:

- grouped validation benchmark
- diagnostic PULSE and EIS endpoints
- threshold-event forecasting diagnostic
- negative result for temporal-order sequence readiness
- calibrated uncertainty and calibrated risk remain blocked
- threshold-warning post-hoc calibration improves mean reliability but does
  not pass C-rate calibrated-risk guardrails
- stressor-balanced HGB improves C-rate delta diagnostics but does not support
  a global robust-capacity claim

Forbidden current wording:

- CBAT-ready
- sequence model justified
- calibrated risk
- detector-knee prediction
- causal early warning
- broad multimodal improvement
- C-rate fade solved

## Avoiding Data Artifact Commits

Before committing:

```bash
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

This should return no generated data products. If it returns a data path,
unstage it and commit only source, documentation, and tracked reports.
