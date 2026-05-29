# GitHub Release Draft: Benchmark v0.2-rc1

Title: Benchmark v0.2-rc1: post-Milestone-9 negative neural-sequence
architecture gate and release-alignment package.

## Release Body

This prerelease packages the post-rc2 repository state after the completed
negative Milestone 9 neural-sequence architecture gate.

## Release Identity

- Tag: `benchmark-v0.2-rc1`
- Commit: release tag target (`git rev-list -n 1 benchmark-v0.2-rc1`)
- Release status: GitHub prerelease
- Previous public anchor: `benchmark-v0.1-rc2`

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

This prerelease was finalized using the canonical validation command list in
`docs/POST_M9_REVIEW_CHECKLIST.md`. It covers release, v2 task-registry,
manuscript, reader-manuscript, whitespace, and no-data-staged checks. The
no-data-staged check must return no paths.
