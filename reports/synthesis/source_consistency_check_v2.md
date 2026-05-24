# Source Consistency Check v2

Date: 2026-05-24

## Scope

This check covers the Milestone 3.0 synthesis artifacts:

- `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
- `reports/synthesis/main_project_claim_matrix_v2.csv`
- `reports/synthesis/main_project_gate_status.md`
- `reports/synthesis/technical_decision_matrix_v2.md`
- `reports/synthesis/blocked_claims_v2.md`
- `reports/synthesis/next_branch_decision.md`

It has been refreshed after Milestones 5.0 and 5.1 to include threshold-warning
probability calibration and stressor-axis robust capacity results.

## Source Artifact Existence

Status: `passed`

All referenced source artifacts in the v2 claim ledger were present in the
working tree when checked.

## Blocked-Claim Check

Status: `passed`

No blocked claim is marked supported in the v2 synthesis. The following remain
blocked or not supported:

- calibrated risk;
- calibrated capacity uncertainty;
- detector-knee prediction;
- sequence models;
- CBAT;
- policy ranking;
- broad multimodal improvement;
- broad EIS improvement;
- prior-PULSE strongest-baseline dominance;
- fade-rate solved;
- stressor-robust training solves C-rate fade globally;
- same-cell counterfactual claims;
- DRT and learned EIS embeddings.

## Forbidden Wording Check

Status: `passed`

The synthesis does not authorize:

- calibrated risk;
- detector-knee prediction;
- CBAT validation;
- policy ranking;
- causal early-warning claims;
- same-cell counterfactual claims.

## Remaining Risk

The threshold-warning diagnostic result is strong enough for diagnostic
forecasting wording, but its probabilities remain uncalibrated. Milestone 5.1
adds a real C-rate stressor-balanced diagnostic improvement, but the global
robust-capacity claim remains unsupported because the non-degradation guardrail
fails. Any future calibrated-risk, policy, or robust-capacity claim requires a
separate gated milestone.
