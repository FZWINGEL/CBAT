# Source Consistency Check v2

Date: 2026-05-27

## Scope

This check covers the Milestone 3.0 synthesis artifacts:

- `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
- `reports/synthesis/main_project_claim_matrix_v2.csv`
- `reports/synthesis/main_project_gate_status.md`
- `reports/synthesis/technical_decision_matrix_v2.md`
- `reports/synthesis/blocked_claims_v2.md`
- `reports/synthesis/next_branch_decision.md`

It has been refreshed after Milestones 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6,
5.7, 5.8, 5.9, 6.0, 7.1, 7.2, 7.3, 7.4, and 8.8 to
include threshold-warning probability calibration, stressor-axis robust
capacity, calibration/quantile hygiene, calibration/robustness
correctness-hardening, Pareto forensics, and train-only adaptive robust
selection, replication, attribution-decomposition, stressor-family routing,
hierarchical replicate-aware capacity comparator results, multi-horizon
capacity forecasting diagnostics, the minimal CUDA sequence reopening check,
observed policy-contrast support diagnostics, and support-bounded
contrast-ordering feasibility and failure-forensics diagnostics.
It now also records reconstruction-failure forensics that close the current
capacity-level C-rate repair branch.

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
- neural sequence reopening;
- CBAT;
- policy ranking;
- policy recommendation;
- broad multimodal improvement;
- broad EIS improvement;
- prior-PULSE strongest-baseline dominance;
- fade-rate solved;
- stressor-robust training solves C-rate fade globally;
- adaptive stressor-robust gain is independently attributable to F8 stress
  features;
- stressor-family routing is a global robust-capacity model;
- hierarchical partial pooling solves C-rate fade;
- hierarchical replicate intervals validate calibrated uncertainty;
- multi-horizon capacity forecasting is solved globally;
- future k-to-k+h exposure is prospective forecasting input;
- adaptive stressor-robust diagnostics justify architecture or policy;
- quantile noncrossing validates calibrated uncertainty;
- equal-frequency ECE validates calibrated risk;
- same-cell counterfactual claims;
- DRT and learned EIS embeddings.
- observed policy-contrast support is diagnostic only and does not authorize
  policy recommendation, causal effects, or same-cell counterfactual effects.
- supported contrast ordering is only partially supported and does not
  authorize recommendation, causal effects, calibrated policy risk/utility, or
  deployment ranking claims.
- contrast-ordering failure forensics are diagnostic-only and do not reopen
  policy ranking.
- support-aware selective reliability is diagnostic-only and does not authorize
  deployment reliability, calibrated risk, policy recommendation, causal
  effects, same-cell counterfactual effects, CBAT, or architecture readiness.
- reconstruction failure forensics do not authorize ignoring the failed
  outside-split guardrail, reopening capacity-level repair, two-target C-rate
  repair, broad robust capacity, solved C-rate fade, architecture, policy,
  calibrated-risk/uncertainty, neural/sequence, CBAT, or causal claims.

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
noncrossing, but capacity uncertainty remains undercovered. Milestone 5.6
locks a narrow conservative train-only adaptive stressor-balanced diagnostic
that replicates across deterministic logical seeds and passes the C-rate gain
and outside-C-rate non-degradation gate for `delta_capacity_Ah`, but the broad
C-rate fade-solved claim remains blocked. Milestone 5.7 shows incremental F8
value under adaptive selection for C-rate delta, but that attribution fails
outside-C-rate non-degradation and remains diagnostic-only. Milestone 5.8
adds targeted D2-for-C-rate/D0-elsewhere routing, but this is not a global
robust-capacity model. Milestone 5.9 implements the hierarchical
replicate-aware comparator required by the charter, but its partial-pooling
gain is diagnostic-only and its interval coverage fails. Milestone 6.0
implements a multi-horizon capacity forecasting gate, but overall
capacity-level support remains partial and K3 future exposure is
oracle-diagnostic only.
Milestone 7.1 verifies CUDA Torch MLP execution but keeps sequence/neural
readiness blocked because true-sequence candidates fail aggregate-event HGB,
timestamp-stress HGB, and C-rate delta controls.
Milestone 7.2 verifies observed matched policy-contrast support and sign
stability, but policy recommendation, causal, counterfactual, and deployment
ranking claims remain blocked.
Milestone 7.3 verifies partial HGB K2 supported contrast-ordering signal from
existing multi-horizon predictions, but the strict prior-slope bootstrap
reference gate fails, so recommendation, causal, counterfactual, calibrated
policy risk/utility, CBAT, and sequence/neural claims remain blocked.
Milestone 7.4 decomposes that failure by effect size, rank metric, and
top-k/regret diagnostics, but large-effect ordering remains diagnostic-only
and does not authorize policy ranking or recommendation.
Milestone 8.0 adds support-aware selective reliability diagnostics, but support
filtering worsens primary capacity and threshold-warning metrics at 50%
retention and C-rate support reliability is not supported. It remains an audit
and abstention diagnostic only.
Milestone 8.8 explains the Milestone 8.7 reconstruction failure and closes the
current capacity-level branch: two outside-split direct-reference comparisons
fail, with 58 degrading condition hotspots. QA flags are context only, and
support-overlap evidence is insufficient for the outside-split hotspots.
Any future calibrated-risk, calibrated-uncertainty, policy, architecture, or
broad robust-capacity claim requires a separate gated milestone.
