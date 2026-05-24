# Milestone 4.2: Reviewer-Risk Hardening and Submission Preflight

Date: 2026-05-24

## Goal

Harden the venue-neutral v0.6 manuscript package against likely reviewer
objections and create a v0.7 submission-preflight package without adding new
models, features, data products, or scientific claims.

## Added Artifacts

- `reports/synthesis/reviewer_risk_register_v2.md`
- `manuscript/reviewer_response_prep_v2.md`
- `manuscript/submission_preflight_v0_7.md`
- `manuscript/manuscript_v0_7.md`
- `manuscript/manuscript_v0_7_traceability.md`
- `manuscript/supplement_v0_7.md`
- `manuscript/manuscript_package_v0_7_manifest.md`
- `manuscript/checks/manuscript_v0_7_claim_check.md`
- `manuscript/checks/manuscript_v0_7_reader_check.md`
- `manuscript/checks/manuscript_v0_7_package_check.md`

## Evidence Integrated

- v2 claim ledger and claim matrix
- blocked-claim register
- main-project gate status
- reviewer-facing `benchmark-v0.1-rc2` release package
- v0.6 manuscript, supplement, and traceability package

## Claim Posture

The v0.7 package preserves the v2 claim ledger. It supports grouped-validation
benchmark wording, diagnostic PULSE/EIS endpoint wording, and diagnostic 80%
threshold-event forecasting wording. It keeps architecture, sequence/neural,
DRT/embedding, detector-knee, policy, causal, same-cell counterfactual,
risk-score calibration, and broad multimodal branches blocked.

## Validation Summary

Completed before final validation pass:

- manuscript claim check: passed
- manuscript reader check: passed
- forbidden manuscript phrase scan: passed
- `git diff --check`: passed
- release-candidate check: passed
- data/Parquet diff check: passed
