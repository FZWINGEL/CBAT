# Submission Preflight v0.7

This preflight checklist is venue-neutral and source-linked. It is intended to
be run before choosing journal-specific formatting.

| Area | Status | Evidence |
|---|---|---|
| Main manuscript exists | pass | `manuscript/manuscript_v0_7.md` |
| Supplement exists | pass | `manuscript/supplement_v0_7.md` |
| Traceability sidecar exists | pass | `manuscript/manuscript_v0_7_traceability.md` |
| Reviewer-risk register refreshed | pass | `reports/synthesis/reviewer_risk_register_v2.md` |
| Reviewer response prep refreshed | pass | `manuscript/reviewer_response_prep_v2.md` |
| Package manifest exists | pass | `manuscript/manuscript_package_v0_7_manifest.md` |
| Claim ledger anchor exists | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Release anchor exists | pass | `benchmark-v0.1-rc2`; `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md` |
| Raw/generated data excluded | pass | `reports/synthesis/artifact_manifest_v2.csv` |
| Blocked claims remain blocked | pass | `reports/synthesis/blocked_claims_v2.md` |

## Required Validation Before Submission Formatting

- manuscript claim check
- reader manuscript check
- release-candidate check
- `git diff --check`
- staged data-artifact check

## Still Not Authorized

- CBAT
- sequence or neural models
- DRT or learned EIS embeddings
- policy ranking
- detector-knee prediction
- risk-score calibration claims
- causal or same-cell counterfactual claims
- broad multimodal degradation claims
