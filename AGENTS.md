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

Milestone 6.0: Multi-horizon capacity forecasting gate.

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
- Milestone 5.0 evaluated whether the supported diagnostic 80%
  threshold-event warning result can be turned into calibrated probability
  diagnostics under grouped splits. It did not authorize calibrated-risk
  wording because C-rate calibration remained above the guardrail.
- Milestone 5.1 evaluated non-neural stressor-axis robust HGB variants. It
  found a diagnostic C-rate `delta_capacity_Ah` improvement, but did not
  support a global robust-capacity claim because the outside-C-rate
  non-degradation guardrail narrowly failed.
- Milestone 5.3 hardened existing calibration and stressor-robustness checks
  against silent false support.
- Milestone 5.4 diagnosed where the Milestone 5.1 outside-C-rate
  non-degradation guardrail failed and evaluated a small bounded Pareto grid of
  existing non-neural robust HGB settings. The predeclared R2/F8 full-strength
  setting still failed the 5% guardrail.
- Milestone 5.5 tested train-only adaptive stressor-robust selection. The
  conservative selector passed diagnostically, while the max-gain selector
  failed the unchanged outside-C-rate non-degradation guardrail.
- Milestone 5.6 replicated the conservative adaptive stressor-robust result
  across the deterministic HGB/no-bagging seed interface and locked only a
  narrow diagnostic `delta_capacity_Ah` robustness claim.
- Milestone 5.7 decomposed whether the Milestone 5.6 gain is attributable to
  F8 timestamp-weighted stress features, train-only reweighting, or their
  combination. F8 attribution remains diagnostic-only because the incremental
  F8 comparison fails outside-C-rate non-degradation.
- Milestone 5.8 evaluated a narrow stressor-family router over existing
  attribution arms: use train-only D2 adaptive R2/F4 for C-rate transfer when
  its inner guardrail passes, and route non-C-rate stressor views to D0 R0/F4.
  It must not be described as broad robust capacity, solved C-rate fade,
  architecture readiness, policy ranking, calibrated risk, calibrated
  uncertainty, or causal evidence.
- Milestone 6.0 evaluates non-neural multi-check-up capacity forecasting as a
  charter-aligned Q1 extension. It separates prospective check-up-k state,
  time, history, and nominal-condition features from K3 oracle k-to-k+h
  exposure diagnostics, which are never valid early-forecasting inputs.
- `docs/REPO_STATUS.md` is the concise source of truth for current artifacts,
  validation results, and remaining blockers.

Allowed work:
- multi-horizon capacity target table construction from existing interval rows
- multi-horizon capacity target QA and split coverage diagnostics
- non-neural multi-horizon capacity baselines under grouped validation
- prospective prior-state/time/nominal multi-horizon feature groups
- oracle future-exposure diagnostics clearly labeled as non-prospective
- multi-horizon capacity claim-readiness reporting
- additive equal-frequency ECE diagnostics alongside fixed-width ECE
- L3 capacity quantile noncrossing post-sort hygiene
- rerunning existing threshold-warning calibration and capacity calibration reports
- calibration/quantile hygiene claim-readiness reporting
- calibration readiness gate correctness fixes
- stressor-robust readiness gate correctness fixes
- no-empty-metric runner guards
- report refreshes caused by corrected readiness logic
- stressor-axis robust non-neural capacity baselines
- condition-balanced and stressor-balanced HGB sample weighting
- condition-bagged HGB diagnostics
- train-only internal condition model selection
- paired condition-level robustness diagnostics
- stressor-robust capacity claim-readiness reporting
- stressor-robust failure forensics
- bounded stressor-robust Pareto diagnostics over existing robust HGB variants
- non-degradation threshold sensitivity reporting without relaxing the
  predeclared 5% guardrail
- train-only adaptive stressor-balanced weight selection using inner grouped
  validation on outer training rows only
- conservative adaptive robust-selection claim-readiness reporting
- adaptive stressor-robust replication across deterministic seeds
- adaptive selector leakage and seed-reuse diagnostics
- stressor-robust attribution decomposition over existing F4/F8 and R0/R2 arms
- train-only reweighting-only versus stress-feature attribution diagnostics
- attribution leakage audits using only outer-training rows for selection
- stressor-family routing over existing D0/D2 attribution arms
- report-based recombination of existing outer-fold attribution predictions
- arm-router leakage audits and claim-readiness reporting
- hierarchical replicate-aware capacity baselines
- train-only stressor-family residual partial pooling
- replicate-variance interval diagnostics
- hierarchical leakage audits and claim-readiness reporting
- grouped threshold-warning probability calibration
- Platt/logistic and isotonic post-hoc calibration fitted on calibration
  conditions only
- train/calibration/test condition partitioning checks
- C-rate and verified-only calibration diagnostics
- threshold-warning calibration claim-readiness reporting
- public README refresh
- repository metadata triage
- public-review entry point documentation
- venue-targeting matrix
- submission-readiness triage
- venue-neutral submission bundle packaging
- title and abstract variants
- cover-letter draft text
- data and code availability statements
- figure/table inventories
- external handoff checklists
- benchmark/manuscript handoff notes
- reviewer-risk register refresh
- reviewer response preparation
- manuscript v0.7 submission-preflight package
- manuscript and supplement tightening from tracked evidence
- manuscript v0.6 reviewer-ready integration
- venue-neutral supplement scaffolding
- manuscript package checks
- manuscript v0.5 integration from tracked evidence
- manuscript traceability sidecars
- figure/table refresh from tracked reports
- manuscript no-overclaim checks
- release handoff summaries
- GitHub release draft text
- release checklist finalization
- future-branch organization notes
- release-candidate validation
- executable artifact and claim checks
- release notes and tag-preparation docs
- no-data-staged checks
- benchmark runbooks and reproducibility documentation
- command DAG documentation
- artifact manifests
- release-candidate checks
- source-artifact consistency checks
- Codex/developer operating guide updates
- capacity trajectory extraction
- knee detector implementation
- detector agreement diagnostics
- x-axis and smoothing sensitivity
- replicate-triplet knee consistency
- knee-label forensics
- stable-condition registry generation
- threshold-event label stability diagnostics
- knee-vs-threshold target-readiness comparisons
- threshold-event warning table construction
- threshold-warning QA and class-balance diagnostics
- non-neural threshold-warning classification baselines
- grouped warning evaluation
- distance-to-threshold and prior-only extrapolation baselines
- lead-time and proximity-bin diagnostics
- censoring-policy sensitivity
- verified-only threshold-warning evaluation
- final threshold-warning claim-readiness reporting
- technical evidence synthesis
- claim ledger refresh
- blocked-claim review
- next-branch decision
- source-artifact consistency checks
- probability calibration diagnostics
- exploratory candidate knee label tables
- knee claim-readiness reporting
- documentation/evidence memo updates
- lightweight report formatting or consistency fixes
- small tests with synthetic fixtures

Forbidden work:
- new model training outside the scoped hierarchical/stressor-robust diagnostic gates
- new feature engineering outside the scoped hierarchical/stressor-robust diagnostic gates
- knee prediction models
- neural models
- sequence models
- transformers
- CBAT architecture
- DRT features
- EIS embeddings
- policy ranking
- capacity+PULSE+EIS architecture work
- causal or mechanistic overclaims
- same-cell counterfactual claims
- future interval exposure leakage
- calibrated risk claims unless grouped probability calibration passes
- calibrated uncertainty claims unless grouped coverage passes
- broad EIS predictive claims
- future EIS state as capacity/PULSE input
- EIS deltas as capacity/PULSE input
- knee prediction
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
