# Benchmark v0.2-rc1 Release Notes

Benchmark v0.2-rc1 is a post-Milestone-9 reviewer checkpoint. It packages the
post-rc2 release alignment, C38, benchmark task registry v2, and the negative
Milestone 9 neural-sequence architecture gate.

## Release Identity

- Tag: `benchmark-v0.2-rc1`
- Commit: release tag target (`git rev-list -n 1 benchmark-v0.2-rc1`)
- Release status: GitHub prerelease
- Previous public anchor: `benchmark-v0.1-rc2`

## Summary

Benchmark v0.2-rc1 is a post-Milestone-9 reviewer checkpoint. It adds post-rc2
synthesis alignment, C38, benchmark task registry v2, and the negative
Milestone 9 neural-sequence architecture gate.

Milestone 9 adds a stronger pre-CBAT neural sequence falsification gate. It is
negative: CUDA CNN/TCN/CNN-LSTM true-order candidates do not beat
aggregate-event HGB, timestamp-stress HGB, or C-rate delta controls. This
strengthens the blocked posture for neural sequence and CBAT readiness.

## What Changed Since rc2

- Added post-rc2 status documentation distinguishing the published rc2 anchor
  from `benchmark-v0.2-rc1`.
- Added C38 to the main-project claim ledger/matrix surface.
- Added `configs/benchmark_tasks_v2.yaml` with T20 for the negative pre-CBAT
  neural-sequence architecture gate.
- Added v2 benchmark task registry check outputs, leaderboard, task cards, and
  model-family cards.
- Added Milestone 9 tracked reports, plot CSVs, SVG figures, and ignored local
  Parquet artifacts to the artifact manifest.
- Added release-check coverage for stale Codex phase docs and
  ledger-to-claim-matrix completeness.

## What Is Not Included

This prerelease does not add raw data, generated interim Parquets, split
Parquets, processed prediction Parquets, a CBAT architecture, policy
recommendations, calibrated risk claims, calibrated uncertainty claims, DRT
features, learned EIS embeddings, or causal/counterfactual claims.

## Claim Posture

Supported claims remain the same or narrower. Milestone 9 is negative for
neural sequence architecture readiness and keeps CBAT blocked.

## Validation

The release was finalized using the canonical validation commands in
`docs/POST_M9_REVIEW_CHECKLIST.md`: Ruff, pytest, release-candidate, v2
task-registry, manuscript, reader-manuscript, whitespace, and no staged `data/`
or Parquet artifacts.
