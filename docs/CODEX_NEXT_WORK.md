# Codex Next Work

Current recommended branch: grouped threshold-warning probability calibration gate.

## Current Phase

Milestone 5.0 evaluates whether the supported non-neural 80% threshold-event
warning diagnostic can support calibrated probability wording. It is limited
to grouped post-hoc calibration of the existing HGB W2 warning baseline with
separate fit, calibration, and test condition groups.

## Current Result

Platt/logistic and isotonic calibration improve mean ECE for the primary
3-check-up threshold-warning horizon, but C-rate ECE remains above the
guardrail. Treat threshold-warning probabilities as diagnostic scores, not
calibrated risk.

## Optional Technical Branch

No broader technical branch is currently justified. Future technical work, if
opened, should be a narrowly scoped calibration-method comparison or release
automation task, not CBAT, policy ranking, sequence modeling, or new modality
expansion.

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

Forbidden current wording:

- CBAT-ready
- sequence model justified
- calibrated risk
- detector-knee prediction
- causal early warning
- broad multimodal improvement

## Avoiding Data Artifact Commits

Before committing:

```bash
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

This should return no generated data products. If it returns a data path,
unstage it and commit only source, documentation, and tracked reports.
