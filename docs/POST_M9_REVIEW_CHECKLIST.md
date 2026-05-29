# Post-Milestone-9 Review Checklist

This checklist is for external reviewers, collaborators, or maintainers
reviewing current `main` after the negative Milestone 9 neural-sequence
architecture gate. It is a review path, not a new evidence claim.

## Review Path

1. `README.md`
2. `docs/POST_RC2_MAIN_STATUS.md`
3. `docs/PUBLIC_REVIEW_ENTRYPOINT.md`
4. `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
5. `reports/synthesis/main_project_claim_matrix_v2.csv`
6. `configs/benchmark_tasks_v2.yaml`
7. `reports/synthesis/benchmark_task_cards_v2.md`
8. `docs/experiments/2026-05-28_neural_sequence_architecture_gate.md`
9. `manuscript/submission_bundle_v0_8.md`

## Review Questions

- Are supported claims stated narrowly enough?
- Are blocked claims consistently blocked?
- Is the distinction between `benchmark-v0.1-rc2` and latest `main` clear?
- Does the v2 task registry capture all claim-bearing gates?
- Are generated data artifacts excluded?
- Is Milestone 9 represented as a negative architecture gate, not as CBAT
  progress?

## Required Local Checks

- `ruff check . --no-cache`
- `pytest -p no:cacheprovider -q`
- `mbp report check-release-candidate`
- `mbp report check-benchmark-tasks --task-registry configs/benchmark_tasks_v2.yaml --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --claim-matrix reports/synthesis/main_project_claim_matrix_v2.csv --artifact-manifest reports/synthesis/artifact_manifest_v2.csv --out reports/synthesis/benchmark_task_registry_check_v2.md --leaderboard-out reports/synthesis/benchmark_leaderboard_v2.csv --task-cards-out reports/synthesis/benchmark_task_cards_v2.md --model-cards-out reports/synthesis/benchmark_model_cards_v2.md`
- `mbp report check-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md`
- `mbp report check-reader-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md`

## Data Policy Check

Generated data artifacts must remain unstaged:

```bash
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

The command should return no paths before any commit or release preparation.
