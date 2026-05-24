# Milestone 4.3: Submission Bundle And External Handoff

Date: 2026-05-24

## Goal

Package the validated v0.7 manuscript and `benchmark-v0.1-rc2` benchmark
release evidence into a venue-neutral v0.8 submission bundle for human review,
venue selection, or external collaborator handoff.

## Added Artifacts

- `manuscript/submission_bundle_v0_8.md`
- `manuscript/title_abstract_options_v0_8.md`
- `manuscript/cover_letter_draft_v0_8.md`
- `manuscript/data_code_availability_v0_8.md`
- `manuscript/figure_table_inventory_v0_8.md`
- `manuscript/submission_checklist_v0_8.md`
- `docs/BENCHMARK_MANUSCRIPT_HANDOFF.md`

## Evidence Integrated

- `benchmark-v0.1-rc2` release notes and summary
- v0.7 manuscript, supplement, traceability, and package manifest
- v2 claim ledger and claim matrix
- reviewer-risk register and response-prep notes
- reproducibility guide, runbook, command DAG, and artifact manifest

## Claim Posture

The bundle adds no new claims. It preserves the existing supported diagnostic
claims for grouped validation, PULSE/EIS scalar endpoints, C-rate difficulty,
and 80% threshold-event forecasting. It keeps CBAT, sequence/neural models,
DRT/embedding, policy ranking, detector-knee prediction, risk-score
calibration, causal claims, same-cell counterfactual claims, and broad
multimodal degradation claims closed.

## Validation Summary

The 4.3 package passed:

- manuscript claim check on `manuscript/manuscript_v0_7.md`;
- reader manuscript check on `manuscript/manuscript_v0_7.md`;
- release-candidate check;
- forbidden phrase scan across new submission-bundle files;
- `ruff check . --no-cache`;
- `pytest -p no:cacheprovider` with 148 passing tests;
- `git diff --check`;
- data/Parquet diff and staged data-artifact checks.

No new model training, feature engineering, data products, raw data, generated
Parquets, or prediction Parquets are part of this milestone.
