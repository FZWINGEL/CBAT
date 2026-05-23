# Reproducibility Gate Status

Milestone 3.1 status: release-candidate documentation package created.

| Gate | Status | Evidence | Next action |
|---|---|---|---|
| Benchmark reproducibility guide | supported_for_release_candidate | `docs/BENCHMARK_REPRODUCIBILITY.md` | Keep updated when dependencies or raw-data layout changes. |
| Command runbook | supported_for_release_candidate | `docs/BENCHMARK_RUNBOOK.md` | Convert to machine executor only if needed later. |
| Command DAG | supported_for_release_candidate | `docs/COMMAND_DAG.md` | Keep aligned with new CLI additions. |
| Artifact manifest | supported_for_release_candidate | `reports/synthesis/artifact_manifest_v2.csv` | Add generator/checker if manual upkeep becomes fragile. |
| Artifact policy | supported_for_release_candidate | `docs/BENCHMARK_ARTIFACTS.md` | Keep generated Parquets ignored. |
| Release checklist | supported_for_release_candidate | `docs/BENCHMARK_RELEASE_CHECKLIST.md` | Use before release tags. |
| Source/claim consistency | supported_for_release_candidate | `reports/synthesis/source_consistency_check_v2.md`; `reports/synthesis/release_candidate_check.md` | Keep blocked claims blocked. |
| Current branch decision | supported_for_release_candidate | `reports/synthesis/next_branch_decision.md`; `docs/CODEX_NEXT_WORK.md` | Default to release/manuscript integration. |
| New science | blocked | Milestone 3.1 scope | Open a new milestone before any new model or feature work. |

## Blocked During 3.1

- new model training
- new feature engineering
- CBAT
- neural models
- sequence models
- transformers
- DRT
- EIS embeddings
- policy ranking
- causal or mechanistic claims
- same-cell counterfactual claims
- broad multimodal claims
