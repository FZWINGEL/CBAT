# Milestone 3.2: Benchmark v0.1-rc1 Validation

Date: 2026-05-23

## Goal

Make the benchmark release package executable and tag-ready without adding new
scientific claims, new feature engineering, or new model runs.

## Executable Checks Added

- `mbp report check-release-candidate`
- required release-file existence checks
- AGENTS/REPO_STATUS phase alignment check
- tracked artifact path existence check
- ignored artifact location check
- blocked-claim supported-status check
- claim matrix ID versus claim ledger check
- runbook/command-DAG major command mention check
- CLI command family/name registration check

## Release Documents

- `docs/RELEASE_NOTES_v0.1-rc1.md`
- `docs/TAGGING_RELEASE_CANDIDATE.md`
- updated `docs/BENCHMARK_RELEASE_CHECKLIST.md`
- updated `reports/synthesis/release_candidate_check.md`

## Validation Summary

- `.venv/bin/ruff check . --no-cache`: passed.
- `.venv/bin/pytest -p no:cacheprovider`: passed, 148 tests.
- `.venv/bin/mbp report check-release-candidate`: passed.
- `git diff --check`: passed after regenerating the release-candidate report.
- no generated `data/` or `.parquet` artifacts are intentionally staged.

## Remaining Release Risks

- The release checker validates release metadata and command coverage; it does
  not execute the full raw-to-synthesis pipeline.
- Full reruns still depend on local raw data and local compute resources.
- Tagging should happen only after the worktree is clean and the release checks
  pass.

## Scope Boundary

No new modeling, feature engineering, neural models, sequence models, CBAT,
DRT, EIS embeddings, policy ranking, detector-knee prediction, calibrated risk,
causal claims, same-cell counterfactual claims, or broad multimodal claims were
introduced.
