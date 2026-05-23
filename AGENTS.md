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

Milestone 0.7.2: PULSE target robustness and claim-readiness finalization.

Current state:
- Gate 2b implementation and reports are committed.
- Milestone 0.4 baseline-readiness artifacts are committed: LOG_AGE policy,
  interval subset registry, split audit, and dependency metadata.
- Milestone 0.5 bounded capacity baseline reports exist and remain limited to
  interval scalar features.
- Milestone 0.5b diagnostics, Ridge scaling, HGB-50 robustness, and quantile
  metrics are implemented.
- Milestone 0.5c synthesis and claim-readiness artifacts are committed.
- Milestone 0.7 opened a scoped PULSE evidence stream after the LOG_AGE-only
  C-rate delta pass failed to beat the F4 threshold. Milestone 0.7.1 hardened
  that stream with alignment-threshold sensitivity, direction-specific target
  extraction, canonical-target missingness reports, and scalar resistance
  baseline sensitivity runs. Milestone 0.7.2 finalizes target robustness and
  claim-readiness for scalar PULSE resistance baselines before any coupling or
  multimodal work.
- `docs/REPO_STATUS.md` is the concise source of truth for current artifacts,
  validation results, and remaining blockers.
- LOG_AGE monotonicity has been triaged and propagated into interval quality
  flags.
- Capacity baseline code must consume `interval_subset_registry_v1.parquet` and
  report strict-vs-tolerant monotonicity sensitivity.

Allowed work:
- small tests with synthetic fixtures
- capacity-only baseline runner execution
- capacity-baseline report hardening
- baseline diagnostics and robustness reruns
- capacity-only stress-feature engineering
- scalar LOG_AGE interval features
- current-sign audit
- timestamp-weighted dwell features
- event-segmented scalar stress features
- stress-feature QA and schema hardening
- capacity target consistency diagnostics
- C-rate failure-mode analysis
- scalar stress-feature ablation diagnostics
- target normalization experiments
- train-fold residual/bias correction diagnostics
- narrow cold/current scalar feature groups
- HGB/Ridge capacity reruns
- reference L0 comparison hardening
- C-rate holdout grouped diagnostics
- claim-readiness summaries
- capacity targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- scalar interval features
- condition-level grouped validation
- strict/tolerant interval subset sensitivity reporting
- baseline evaluation cards / leaderboard summaries
- Ridge numeric standardization and bounded HGB robustness checks
- LOG_AGE-derived stress feature diagnostics
- documentation/evidence memo updates
- PULSE QA
- PULSE target policy
- PULSE alignment diagnostics
- PULSE alignment-threshold sensitivity
- PULSE direction-specific QA
- PULSE target coverage diagnostics
- PULSE target robustness diagnostics
- secondary PULSE target baselines
- PULSE claim-readiness summaries
- PULSE interval target table construction
- PULSE resistance baselines

Forbidden work:
- EIS modeling
- EIS embeddings
- knee prediction
- sequence models
- neural models
- CBAT architecture
- policy ranking
- capacity+PULSE multimodal claims
- PULSE scientific claims beyond scalar resistance baselines

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
