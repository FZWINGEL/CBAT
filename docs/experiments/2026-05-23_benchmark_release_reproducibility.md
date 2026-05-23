# Milestone 3.1: Benchmark Release and Reproducibility Hardening

Date: 2026-05-23

## Goal

Create a release-candidate reproducibility layer for the completed benchmark
without adding new scientific claims, new feature engineering, or new model
runs.

## Created Artifacts

- `docs/BENCHMARK_REPRODUCIBILITY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/BENCHMARK_ARTIFACTS.md`
- `docs/BENCHMARK_RELEASE_CHECKLIST.md`
- `docs/COMMAND_DAG.md`
- `docs/CODEX_NEXT_WORK.md`
- `reports/synthesis/artifact_manifest_v2.csv`
- `reports/synthesis/reproducibility_gate_status.md`
- `reports/synthesis/release_candidate_check.md`

## Scope

This milestone is documentation and consistency hardening only. It does not add
or rerun model training, new feature engineering, CBAT, neural models, sequence
models, DRT, EIS embeddings, policy ranking, causal claims, or broad multimodal
claims.

## Validation Summary

- `git diff --check`: passed.
- No raw, interim, processed, or prediction Parquets are intentionally staged.
- The release-candidate check is manual in
  `reports/synthesis/release_candidate_check.md`; no checker code was added.

## Remaining Release Risks

- The command DAG is documentation, not a machine executor.
- Full raw-to-synthesis reruns require local raw data and enough disk/memory for
  large LOG_AGE-derived products.
- If the artifact manifest becomes hard to maintain manually, a later
  docs-only or small reporting milestone can add a generator/checker CLI.
