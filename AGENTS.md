# AGENTS.md - Multimodal Battery Prediction

## Project Rule

This is a baseline-first scientific ML project. Do not implement advanced models before the
data audit, schemas, validation protocol, and baseline ladder are implemented.

## Read First

1. `docs/PROJECT_CHARTER.md`
2. `docs/DATASET_EVIDENCE_MEMO.md`
3. `docs/SCHEMA_REGISTRY.md`
4. `docs/VALIDATION_PROTOCOL.md`
5. `docs/DECISION_LOG.md`

## Current Phase

Gate 1: Dataset audit and provenance verification.

Allowed work:
- repo scaffolding
- dataset inventory
- manifest generation
- file hashing
- schema definitions
- audit reports
- small tests with synthetic fixtures
- documentation templates

Forbidden work:
- neural models
- CBAT architecture
- EIS embeddings
- training loops
- hyperparameter optimization
- claims about performance

## Coding Standards

- Use Python 3.11+.
- Use `uv` for dependency management.
- Use `ruff`, `pytest`, and type hints.
- Prefer structured models for metadata.
- Do not commit raw data.
- All paths must be configurable.
- Every data product must include provenance and schema version.
- Every CLI command must be testable without the full dataset.

## GitHub CLI

- Use `gh` for GitHub operations in this repository.
- The local Codex sandbox restricts network access, so networked `gh` commands may need to be run with tool escalation even when `gh auth status` works in the user's terminal.
- `gh` is authenticated for the `FZWINGEL` account; if a command cannot infer the repository from the local checkout, pass `--repo OWNER/REPO` explicitly.

## Scientific Guardrails

- Treat 228 cells as 76 condition triplets, not 228 independent regimes.
- EIS is gated and must not be assumed valid until audited.
- LOG_AGE can leak future diagnostics if used carelessly.
- Random splits are not publishable evidence.
- Check-up burden is a confound and must be represented.
