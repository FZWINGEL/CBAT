# Release Candidate Check

Milestone 3.1 uses a manual release-candidate check rather than adding checker
code. This keeps the milestone documentation-only.

## Required Files

Status: pass.

- `docs/BENCHMARK_REPRODUCIBILITY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/BENCHMARK_ARTIFACTS.md`
- `docs/BENCHMARK_RELEASE_CHECKLIST.md`
- `docs/COMMAND_DAG.md`
- `docs/CODEX_NEXT_WORK.md`
- `reports/synthesis/artifact_manifest_v2.csv`
- `reports/synthesis/reproducibility_gate_status.md`
- `reports/synthesis/release_candidate_check.md`
- `docs/experiments/2026-05-23_benchmark_release_reproducibility.md`

## Claim Guardrails

Status: pass.

The release package does not mark blocked branches as supported. CBAT,
sequence/neural models, DRT, EIS embeddings, policy ranking, detector-knee
prediction, calibrated risk, calibrated uncertainty, causal claims, same-cell
counterfactual claims, and broad multimodal claims remain blocked.

## Artifact Policy

Status: pass.

The artifact manifest separates tracked reports from ignored generated
Parquets. Ignored generated artifacts are listed under `data/interim/`,
`data/splits/`, or `data/processed/`.

## Phase Alignment

Status: pass.

`AGENTS.md` and `docs/REPO_STATUS.md` both identify Milestone 3.1 as benchmark
release and reproducibility hardening.

## Validation

Required before commit:

```bash
git diff --check
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

For this documentation-only pass, no code was added. If code changes are added
later, run:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
```
