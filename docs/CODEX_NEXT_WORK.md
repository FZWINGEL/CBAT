# Codex Next Work

Current recommended branch: synthesis/release maintenance, or a narrow
stressor-robustness forensics pass only if explicitly requested.

## Current Phase

Milestone 5.3 is a calibration and stressor-robustness correctness-hardening
gate. It fixes silent readiness-gate failure modes, empty-run guards,
calibration schema metadata, Platt/logistic convention drift, and
stressor-robust bagging/selection hygiene. It is not a new modeling,
architecture, calibration-claim, or policy-ranking branch.

## Current Result

The correctness pass does not change the claim posture. Threshold-warning
probability calibration still blocks calibrated-risk wording: Platt
verified-only primary-horizon mean fixed-width ECE is `0.0748136` and
equal-frequency ECE is `0.0729286`, but C-rate verified-only ECE remains above
the guardrail (`0.167653` fixed-width; `0.176185` equal-frequency). Capacity
uncertainty also remains blocked: raw noncrossing q10-q90 mean coverage is
`0.701398`, and C-rate coverage remains below target.

Milestone 5.1 remains a useful diagnostic robustness result: stressor-balanced
HGB with `F8_timestamp_weighted_stress` improves C-rate `delta_capacity_Ah`,
but the global robust-capacity claim remains `not_supported` because the
outside-C-rate non-degradation guardrail fails.

## Optional Technical Branch

No broader technical branch is currently justified. Future technical work, if
opened, should be a narrow voltage-window/stressor-robustness forensics pass,
release automation task, or documentation synthesis task, not CBAT, policy
ranking, sequence modeling, or new modality expansion.

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
- equal-frequency ECE sensitivity does not unblock calibrated-risk claims
- L3 capacity quantile noncrossing is hygiene only, not calibrated uncertainty
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
