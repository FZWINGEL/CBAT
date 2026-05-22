# AGENTS.md - Multimodal Battery Prediction

## Project Rule

This is a baseline-first scientific ML project. Do not implement advanced models before the
data audit, schemas, validation protocol, and baseline ladder are implemented.

## Read First

1. `docs/PROJECT_CHARTER.md`
2. `docs/REPO_STATUS.md`
3. `docs/DATASET_EVIDENCE_MEMO.md`
4. `docs/SCHEMA_REGISTRY.md`
5. `docs/VALIDATION_PROTOCOL.md`
6. `docs/DECISION_LOG.md`

## Current Phase

Gate 2b: LOG_AGE integrity triage and interval-table hardening.

Current state:
- Gate 2b implementation and reports are committed.
- `docs/REPO_STATUS.md` is the concise source of truth for current artifacts,
  validation results, and remaining blockers.
- LOG_AGE monotonicity has been triaged and propagated into interval quality
  flags.
- Baselines remain blocked until the LOG_AGE monotonicity handling policy
  defines the clean interval subset.

Allowed work:
- LOG_AGE monotonicity investigation
- interval-table QA
- quality flags for contaminated intervals
- split-registry audit
- raw LOG audit scaffolding
- documentation/evidence memo updates
- small tests with synthetic fixtures
- LOG_AGE monotonicity handling policy documentation
- clean interval subset definition after policy approval

Forbidden work:
- model training
- baseline leaderboard
- CBAT architecture
- neural models
- policy ranking
- EIS embeddings

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

## CodeGraph

- CodeGraph is initialized and indexed for this codebase.
- Coding agents should primarily use CodeGraph for structural code search and navigation: symbol definitions, signatures, callers, callees, impact analysis, and focused area context.
- Use native search tools such as `rg` for literal text only: strings, comments, documentation prose, log messages, config keys, or when CodeGraph does not cover the file type.
- Do not grep first when looking for where a function, class, method, or module symbol is defined; use CodeGraph symbol/context tools first.
- After editing files, allow for CodeGraph index lag before relying on fresh query results.

## Scientific Guardrails

- Treat 228 cells as 76 condition triplets, not 228 independent regimes.
- EIS is gated and must not be assumed valid until audited.
- LOG_AGE can leak future diagnostics if used carelessly.
- Random splits are not publishable evidence.
- Check-up burden is a confound and must be represented.
