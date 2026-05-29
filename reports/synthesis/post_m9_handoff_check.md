# Post-Milestone-9 Handoff Check

Status: `draft-preflight`

This report summarizes the post-Milestone-9 reviewer checkpoint. It adds no
model training, no generated data products, and no new positive scientific
claims.

## Scientific Posture

- C38 records the negative CUDA CNN/TCN/CNN-LSTM event-sequence architecture
  gate.
- Milestone 9 v2 tensor QA and CUDA execution are diagnostic successes.
- True-order neural sequence candidates do not beat the required shuffled,
  aggregate-event HGB, timestamp-stress HGB, or C-rate controls.
- Neural sequence next-gate readiness and CBAT prototype readiness remain
  blocked.

## Registry And Manifest Coverage

- `reports/synthesis/main_project_claim_matrix_v2.csv` contains 38 claim rows,
  including C38.
- `configs/benchmark_tasks_v2.yaml` contains 20 tasks, including
  `T20_neural_sequence_architecture_gate`.
- `reports/synthesis/artifact_manifest_v2.csv` lists Milestone 9 tracked
  reports, plot CSVs, SVG figures, and ignored generated local Parquet
  products. The current release-candidate check covers 244 tracked artifacts
  and 38 ignored artifacts.
- The current v2 benchmark task-registry check covers 20 tasks, 38 claim-matrix
  rows, and 282 artifact-manifest rows with no warnings or errors.
- `docs/POST_RC2_MAIN_STATUS.md` distinguishes the published
  `benchmark-v0.1-rc2` anchor from latest `main`.

## Checks To Refresh

The canonical validation commands for this preflight branch are:

- `ruff check . --no-cache`
- `pytest -p no:cacheprovider -q`
- `mbp report check-release-candidate`
- `mbp report check-benchmark-tasks --task-registry configs/benchmark_tasks_v2.yaml --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --claim-matrix reports/synthesis/main_project_claim_matrix_v2.csv --artifact-manifest reports/synthesis/artifact_manifest_v2.csv --out reports/synthesis/benchmark_task_registry_check_v2.md --leaderboard-out reports/synthesis/benchmark_leaderboard_v2.csv --task-cards-out reports/synthesis/benchmark_task_cards_v2.md --model-cards-out reports/synthesis/benchmark_model_cards_v2.md`
- `mbp report check-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md`
- `mbp report check-reader-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md`
- `git diff --check`
- `git diff --cached --name-only | rg '(^data/|\.parquet$)'`

## Release Boundary

`docs/RELEASE_NOTES_v0.2-rc1_DRAFT.md` and
`docs/GITHUB_RELEASE_DRAFT_v0.2-rc1_DRAFT.md` are draft-only. No tag has been
created, and `benchmark-v0.1-rc2` remains the published release anchor unless a
human explicitly approves `benchmark-v0.2-rc1`.
