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

Milestone 2.1: EIS scalar diagnostic baselines.

Current state:
- Gate 2b LOG_AGE integrity triage and Milestones 0.4-1.4.1 are implemented
  and documented.
- Milestone 1.0 produced a paper-facing claim ledger, figure plan, paper
  skeleton, evidence matrix, model ladder summary, split difficulty summary,
  and negative-result summary. Milestone 1.0.1 hardened that package with
  source-artifact checks, reviewer-risk tracking, and a manuscript package plan.
  Milestone 1.1 created the manuscript draft package with prose sections,
  figure/table specifications, source traceability, and reviewer response prep.
  Milestone 1.2 generated the continuous v0.2 manuscript, SVG figures, tables,
  captions, and manuscript checks. Milestone 1.3 cleaned v0.3 assembly, fixed
  Figure 6 PULSE QA extraction, and expanded figure/manuscript QA. Milestone
  1.4 created the reader-facing manuscript v0.4 and traceability sidecar.
- The strongest current prior-PULSE result is deliberately narrow: prior PULSE
  state improves `capacity_Ah_k1` over F4 in selected grouped splits, but it
  does not beat the strongest supplied non-PULSE HGB baselines and does not
  improve `delta_capacity_Ah`.
- The current main-project track evaluates EIS as a scalar diagnostic endpoint
  and prior-state feature under grouped validation. EIS remains non-neural,
  scalar, and gated; no broad EIS improvement claim is authorized.
- `docs/REPO_STATUS.md` is the concise source of truth for current artifacts,
  validation results, and remaining blockers.

Allowed work:
- EIS scalar target tables
- EIS target QA
- EIS scalar baselines
- prior-EIS feature groups using check-up `k` features only
- grouped baseline comparisons
- EIS claim-readiness updates
- documentation/evidence memo updates
- lightweight report formatting or consistency fixes
- small tests with synthetic EIS fixtures

Forbidden work:
- new model training
- new capacity/PULSE feature engineering
- broad EIS predictive claims
- EIS embeddings
- DRT features
- future EIS state as capacity/PULSE input
- EIS deltas as capacity/PULSE input
- knee prediction
- sequence models
- neural models
- CBAT architecture
- policy ranking
- capacity+PULSE+EIS multimodal models
- EIS improvement claims
- capacity+PULSE multimodal claims
- broad multimodal claims
- PULSE scientific claims beyond the Milestone 1.0 claim ledger
- future PULSE state as capacity input
- PULSE deltas as capacity input features

## Coding Standards

- Use Python 3.11+.
- Use `uv` for dependency management.
- Use `ruff`, `pytest`, and type hints.
- Prefer structured models for metadata.
- Do not commit raw data.
- All paths must be configurable.
- Every data product must include provenance and schema version.
- Every CLI command must be testable without the full dataset.
- Update `docs/REPO_STATUS.md` whenever significant repo state changes happen:
  new gates completed, validation status changes, major artifacts are created,
  blockers are resolved or introduced, or the recommended next step changes.
- Document experiments, findings, and decisions under `docs/experiments/`
  whenever baseline runs, data-product experiments, policy checks, or other
  scientifically meaningful implementation trials are performed.

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
