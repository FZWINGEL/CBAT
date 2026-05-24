# Milestone 4.1: Manuscript v0.6 Reviewer-Ready Package

Date: 2026-05-24

## Goal

Turn the v0.5 evidence-integration draft into a venue-neutral reviewer-ready
benchmark manuscript package without adding new models, features, data
products, or scientific claims.

## Added Artifacts

- `manuscript/manuscript_v0_6.md`
- `manuscript/manuscript_v0_6_traceability.md`
- `manuscript/supplement_v0_6.md`
- `manuscript/checks/manuscript_v0_6_claim_check.md`
- `manuscript/checks/manuscript_v0_6_reader_check.md`
- `manuscript/checks/manuscript_v0_6_package_check.md`

## Evidence Integrated

- `benchmark-v0.1-rc2` release package
- v2 claim ledger and claim matrix
- grouped validation protocol
- capacity and LOG_AGE baseline ladder
- PULSE and EIS diagnostic endpoint gates
- semi-empirical and replicate-aware comparator gates
- interval-diagnostic gate
- temporal-order and knee/threshold label gates
- threshold-warning censoring finalization

## Claim Posture

The v0.6 package preserves the v2 claim ledger. It supports grouped-validation
benchmark wording, diagnostic PULSE/EIS endpoint wording, and diagnostic 80%
threshold-event forecasting wording. It keeps architecture, sequence/neural,
DRT/embedding, detector-knee, policy, causal, same-cell counterfactual,
risk-score calibration, and broad multimodal branches blocked.

## Validation Summary

Completed before final validation pass:

- manuscript claim check: passed
- manuscript reader check: passed
- forbidden manuscript phrase scan: passed
- release-candidate check: passed
- `git diff --check`: passed
- data/Parquet diff check: passed
