# Codex Next Work

Current recommended branch: synthesis/release maintenance. The adaptive
stressor-robust replication check has been run and should not be broadened
without a fresh gated question.

## Current Phase

Milestone 5.6 is an adaptive stressor-robust replication and generalization
gate. It replicates the Milestone 5.5 conservative R2 stressor-balanced HGB
selector across the deterministic HGB/no-bagging seed interface and keeps the
unchanged outer C-rate gain plus outside-C-rate non-degradation guardrail. It
is not a new architecture, calibration-claim, or policy-ranking branch.

## Current Result

The correctness pass does not change the claim posture. Threshold-warning
probability calibration still blocks calibrated-risk wording: Platt
verified-only primary-horizon mean fixed-width ECE is `0.0748136` and
equal-frequency ECE is `0.0729286`, but C-rate verified-only ECE remains above
the guardrail (`0.167653` fixed-width; `0.176185` equal-frequency). Capacity
uncertainty also remains blocked: raw noncrossing q10-q90 mean coverage is
`0.701398`, and C-rate coverage remains below target.

Milestone 5.6 supports a narrow replicated diagnostic robustness result:
conservative train-only adaptive R2 selection with
`F8_timestamp_weighted_stress` improves C-rate `delta_capacity_Ah` while
passing the 5% outside-C-rate non-degradation guardrail across five logical
deterministic seeds. The report records deterministic seed reuse explicitly
with effective fit seed `42`. The result is target-specific and diagnostic
only; it does not solve C-rate fade globally or justify architecture work.

## Optional Technical Branch

No broader technical branch is currently justified. Future technical work, if
opened, should be release automation or documentation synthesis unless a fresh
predeclared question is created. Do not open CBAT, policy ranking, sequence
modeling, or new modality expansion from the Milestone 5.6 result.

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
- conservative train-only adaptive R2 selection supports a narrow diagnostic
  C-rate `delta_capacity_Ah` robustness result

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
