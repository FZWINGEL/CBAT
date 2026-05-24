# Benchmark v0.1-rc2 Handoff Check

| Check | Status | Evidence |
|---|---|---|
| Tag exists locally | pass | `benchmark-v0.1-rc2` |
| Tag pushed | pass | pushed to `origin/benchmark-v0.1-rc2` |
| Tagged commit | pass | `e499b12` |
| GitHub release published | pass | `https://github.com/FZWINGEL/CBAT/releases/tag/benchmark-v0.1-rc2` |
| GitHub release status | pass | draft false; prerelease true |
| Release checker passed | pass | `.venv/bin/mbp report check-release-candidate` |
| Ruff passed | pass | `.venv/bin/ruff check . --no-cache` |
| Pytest passed | pass | `.venv/bin/pytest -p no:cacheprovider`, 148 tests |
| Git diff check passed | pass | `git diff --check` |
| Validation checkpoint preserved | pass | `benchmark-v0.1-rc1` remains tagged at `ff4c8c2` |
| No data/Parquet artifacts staged | pass | staged data-artifact check returned no matches before release tags |
| Release notes exist | pass | `docs/RELEASE_NOTES_v0.1-rc2.md` |
| Runbook exists | pass | `docs/BENCHMARK_RUNBOOK.md` |
| Artifact manifest exists | pass | `reports/synthesis/artifact_manifest_v2.csv` |
| Claim ledger v2 exists | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Blocked claims remain blocked | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`; `reports/synthesis/release_candidate_check.md` |

## Handoff Decision

`benchmark-v0.1-rc2` is the reviewer-facing release candidate. It preserves the
validated benchmark evidence while including the release-polish documents in
the source archive. It is a claim-bounded benchmark package, not a
model-architecture or policy-ranking release.

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
