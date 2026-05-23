# Manuscript v0.4 Reader Polish

Date: 2026-05-23

Milestone 1.4 converts the internally traceable v0.3 draft into a reader-facing v0.4 manuscript while preserving claim traceability in a sidecar.

## Changed From v0.3

- Removed raw claim IDs from the main manuscript body.
- Removed allowed-claim, blocked-claim, source-artifact, and referenced-asset scaffolding from reader prose.
- Added `manuscript/manuscript_v0_4_traceability.md` for claim/source mapping.
- Added v0.4 reader-facing captions.
- Added `manuscript/figures/generated_v0_4/*.svg` draft figure assets.

## Validation Summary

- `mbp report check-reader-manuscript`: `passed`
- `ruff check . --no-cache`: `passed`
- `pytest -p no:cacheprovider`: `114 passed`
- `git diff --check`: `passed`
- No new model training, feature engineering, EIS modeling, or architecture work was performed.

## Remaining Tasks

- Convert v0.4 into target venue format.
- Improve final figure visual design if needed.
- Decide whether traceability belongs in supplement or repository-only material.
