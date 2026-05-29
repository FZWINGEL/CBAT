# Benchmark v0.2-rc1 Finalization

## Scope

Finalize the post-Milestone-9 reviewer checkpoint as `benchmark-v0.2-rc1`.

This is release packaging only. It adds no new modeling, no new data products,
and no new scientific claims.

## Included

- C38 in the claim ledger and claim matrix.
- Benchmark task registry v2 with T20.
- Milestone 9 artifact-manifest coverage.
- Post-M9 review checklist.
- v0.2-rc1 release notes and GitHub release draft.
- Manuscript/submission bundle aligned to v2 task-registry validation.

## Claim Posture

Milestone 9 remains a negative architecture gate. Neural sequence next-gate
readiness and CBAT prototype readiness remain blocked.

## Validation

Final validation on the release-finalization branch:

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check . --no-cache`: passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider -q`: passed,
  286 tests.
- `.venv/bin/mbp report check-release-candidate`: passed; 247 tracked
  artifacts, 38 ignored artifacts, and 38 claim rows checked.
- `.venv/bin/mbp report check-benchmark-tasks --task-registry
  configs/benchmark_tasks_v2.yaml --claim-ledger
  docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --claim-matrix
  reports/synthesis/main_project_claim_matrix_v2.csv --artifact-manifest
  reports/synthesis/artifact_manifest_v2.csv --out
  reports/synthesis/benchmark_task_registry_check_v2.md --leaderboard-out
  reports/synthesis/benchmark_leaderboard_v2.csv --task-cards-out
  reports/synthesis/benchmark_task_cards_v2.md --model-cards-out
  reports/synthesis/benchmark_model_cards_v2.md`: passed; 20 tasks, 38 claim
  rows, and 285 artifact-manifest rows checked.
- `.venv/bin/mbp report check-manuscript --manuscript
  manuscript/manuscript_v0_7.md --claim-ledger
  docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability
  manuscript/manuscript_v0_7_traceability.md`: passed with the existing
  reader-facing warning that no explicit claim IDs appear in the manuscript
  text.
- `.venv/bin/mbp report check-reader-manuscript --manuscript
  manuscript/manuscript_v0_7.md --claim-ledger
  docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability
  manuscript/manuscript_v0_7_traceability.md`: passed.
- `git diff --check`: passed.
- `git diff --cached --name-only | rg '(^data/|\.parquet$)' && exit 1 ||
  true`: passed with no staged generated data artifacts.

## Decision

Tag `benchmark-v0.2-rc1` as a GitHub prerelease after human approval and after
the release-finalization PR is merged.
