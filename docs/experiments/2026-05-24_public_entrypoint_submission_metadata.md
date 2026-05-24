# Milestone 4.4: Public Entry Point And Submission Metadata Triage

Date: 2026-05-24

## Goal

Align the public repository entry point and submission metadata triage with the
validated v0.7 manuscript, v0.8 handoff bundle, and `benchmark-v0.1-rc2`
release package.

## Added Or Updated Artifacts

- refreshed `README.md`
- refreshed project description in `pyproject.toml`
- `docs/PUBLIC_REVIEW_ENTRYPOINT.md`
- `docs/REPOSITORY_METADATA_CHECKLIST.md`
- `manuscript/venue_targeting_matrix_v0_9.md`
- `manuscript/submission_readiness_v0_9.md`

## Evidence Integrated

- `benchmark-v0.1-rc2` release notes and summary
- v2 claim ledger and claim matrix
- v0.7 manuscript and traceability package
- v0.8 submission bundle
- benchmark reproducibility guide, runbook, command DAG, and artifact manifest

## Claim Posture

No new scientific claims were added. The public entry point preserves the
existing grouped-validation benchmark framing, diagnostic PULSE/EIS endpoint
wording, C-rate difficulty wording, and diagnostic 80% threshold-event
forecasting wording. CBAT, sequence/neural models, DRT/embedding, policy
ranking, detector-knee prediction, risk-score calibration, causal claims,
same-cell counterfactual claims, and broad multimodal degradation claims remain
closed.

## Validation Summary

The 4.4 package passed:

- release-candidate check;
- manuscript claim check on `manuscript/manuscript_v0_7.md`;
- reader manuscript check on `manuscript/manuscript_v0_7.md`;
- blocked-phrase scan across new public-entrypoint and venue-triage files;
- `ruff check . --no-cache`;
- `pytest -p no:cacheprovider` with 148 passing tests;
- `git diff --check`;
- data/Parquet diff and staged data-artifact checks.
