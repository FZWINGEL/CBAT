# GitHub Release Draft: Benchmark v0.2-rc1

Draft title: Benchmark v0.2-rc1 draft: post-Milestone-9 negative
neural-sequence architecture gate and release-alignment package.

This file is draft-only. Do not create or push a release tag from this document
unless a human explicitly approves publishing `benchmark-v0.2-rc1`.

## Draft Release Body

This proposed prerelease packages the post-rc2 repository state after the
completed negative Milestone 9 neural-sequence architecture gate.

It adds C38, benchmark task registry v2, post-rc2 status documentation,
Milestone 9 artifact-manifest coverage, and release-check hardening. It does
not open a new modeling branch or strengthen any scientific claim.

Milestone 9 tested v2 fixed-length event tensors with CUDA CNN/TCN/CNN-LSTM
baselines. True-order candidates did not pass the predeclared shuffled-order,
aggregate-event HGB, timestamp-stress HGB, or C-rate controls. Neural sequence
next-gate readiness and CBAT prototype readiness remain blocked.

## Included

- Source code and tests.
- Claim ledger, claim matrix, blocked-claim register, and synthesis reports.
- `configs/benchmark_tasks_v2.yaml` plus v2 task cards and model cards.
- Tracked Milestone 9 reports, plot CSVs, and SVG figures.
- Release/reproducibility docs and manuscript handoff docs.

## Excluded

- Raw archives under `data/raw/`.
- Generated interim Parquets under `data/interim/`.
- Split Parquets under `data/splits/`.
- Processed prediction Parquets under `data/processed/`.
- CBAT architecture.
- Policy recommendation.
- Calibrated risk or calibrated uncertainty claims.
- Causal or same-cell counterfactual claims.

## Validation

Run the current release and manuscript checks before publishing:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider -q
mbp report check-release-candidate
mbp report check-benchmark-tasks --task-registry configs/benchmark_tasks_v2.yaml --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --claim-matrix reports/synthesis/main_project_claim_matrix_v2.csv --artifact-manifest reports/synthesis/artifact_manifest_v2.csv --out reports/synthesis/benchmark_task_registry_check_v2.md --leaderboard-out reports/synthesis/benchmark_leaderboard_v2.csv --task-cards-out reports/synthesis/benchmark_task_cards_v2.md --model-cards-out reports/synthesis/benchmark_model_cards_v2.md
mbp report check-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md
mbp report check-reader-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md
git diff --check
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

The final command should return no paths.
