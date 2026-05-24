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

It has been refreshed after Milestones 5.0, 5.1, 5.2, 5.3, 5.4, and 5.5 to
include threshold-warning probability calibration, stressor-axis robust
capacity, calibration/quantile hygiene, calibration/robustness
correctness-hardening, Pareto forensics, and train-only adaptive robust
selection results.

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
- adaptive stressor-robust diagnostics justify architecture or policy;
- quantile noncrossing validates calibrated uncertainty;
- equal-frequency ECE validates calibrated risk;
- same-cell counterfactual claims;
- DRT and learned EIS embeddings.

## Forbidden Wording Check

Status: `passed`

The synthesis does not authorize:

- calibrated risk;
- calibrated capacity uncertainty;
- detector-knee prediction;
- CBAT validation;
- policy ranking;
- causal early-warning claims;
- same-cell counterfactual claims.

## Remaining Risk

The threshold-warning diagnostic result is strong enough for diagnostic
forecasting wording, but its probabilities remain uncalibrated after
equal-frequency ECE sensitivity. Capacity quantile endpoints are now
noncrossing, but capacity uncertainty remains undercovered. Milestone 5.5 adds
a narrow conservative train-only adaptive stressor-balanced diagnostic that
passes the C-rate gain and outside-C-rate non-degradation gate for
`delta_capacity_Ah`, but the broad C-rate fade-solved claim remains blocked.
Any future calibrated-risk, calibrated-uncertainty, policy, architecture, or
broad robust-capacity claim requires a separate gated milestone.
