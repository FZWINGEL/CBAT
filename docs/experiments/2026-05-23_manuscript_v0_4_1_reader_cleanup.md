# Manuscript v0.4.1 Reader Cleanup

Date: 2026-05-23

Milestone 1.4.1 removes the remaining internal scaffold wording from the reader-facing manuscript, hardens the reader check, and removes internal draft labels from v0.4 SVGs.

## Changed From v0.4

- Removed the remaining `Forbidden wording:` block from the reader-facing manuscript.
- Moved reader-facing prose guardrails into `manuscript/manuscript_v0_4_traceability.md`.
- Hardened `check-reader-manuscript` to fail on `Forbidden wording:` in the manuscript body.
- Removed internal draft labels from `manuscript/figures/generated_v0_4/*.svg`.

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
