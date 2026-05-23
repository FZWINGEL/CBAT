# Benchmark v0.1-rc1 Handoff Check

| Check | Status | Evidence |
|---|---|---|
| Tag exists locally | pass | `benchmark-v0.1-rc1` |
| Tag pushed | pass | pushed to `origin/benchmark-v0.1-rc1` |
| Tagged commit | pass | `ff4c8c2` |
| Release checker passed | pass | `.venv/bin/mbp report check-release-candidate` |
| Ruff passed | pass | `.venv/bin/ruff check . --no-cache` |
| Pytest passed | pass | `.venv/bin/pytest -p no:cacheprovider`, 148 tests |
| Git diff check passed | pass | `git diff --check` |
| Worktree clean before release polish | pass | `git status --short` returned no paths before 3.3 edits |
| No data/Parquet artifacts staged | pass | staged data-artifact check returned no matches before tagging |
| Release notes exist | pass | `docs/RELEASE_NOTES_v0.1-rc1.md` |
| Runbook exists | pass | `docs/BENCHMARK_RUNBOOK.md` |
| Artifact manifest exists | pass | `reports/synthesis/artifact_manifest_v2.csv` |
| Claim ledger v2 exists | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Blocked claims remain blocked | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`; `reports/synthesis/release_candidate_check.md` |

## Handoff Decision

`benchmark-v0.1-rc1` is ready for a GitHub release draft. The release is a
claim-bounded benchmark package, not a model-architecture or policy-ranking
release.

## Still Blocked

- CBAT
- neural models
- sequence models
- transformers
- DRT
- learned EIS embeddings
- policy ranking
- detector-knee prediction
- calibrated risk
- causal or same-cell counterfactual claims
- broad multimodal degradation claims
