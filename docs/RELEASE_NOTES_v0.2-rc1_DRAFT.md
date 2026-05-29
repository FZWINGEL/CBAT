# Benchmark v0.2-rc1 Draft Release Notes

Draft title: Benchmark v0.2-rc1 draft: post-Milestone-9 negative
neural-sequence architecture gate and release-alignment package.

This is a draft-only release note for a proposed post-Milestone-9 reviewer
checkpoint. No tag has been created, and `benchmark-v0.1-rc2` remains the
published public release anchor until a human explicitly approves a new tag.

## Summary

Benchmark v0.2-rc1 is a proposed post-Milestone-9 reviewer checkpoint. It adds
post-rc2 synthesis alignment, C38, benchmark task registry v2, and the negative
Milestone 9 neural-sequence architecture gate.

Milestone 9 adds a stronger pre-CBAT neural sequence falsification gate. It is
negative: CUDA CNN/TCN/CNN-LSTM true-order candidates do not beat
aggregate-event HGB, timestamp-stress HGB, or C-rate delta controls. This
strengthens the blocked posture for neural sequence and CBAT readiness.

## What Changed Since rc2

- Added post-rc2 status documentation distinguishing the published rc2 anchor
  from latest `main`.
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

This draft does not add raw data, generated interim Parquets, split Parquets,
processed prediction Parquets, a CBAT architecture, policy recommendations,
calibrated risk claims, calibrated uncertainty claims, DRT features, learned
EIS embeddings, or causal/counterfactual claims.

## Claim Posture

Supported claims remain the same or narrower. Milestone 9 is negative for
neural sequence architecture readiness and keeps CBAT blocked.

## Validation To Run Before Tagging

Use the canonical validation commands in `docs/POST_M9_REVIEW_CHECKLIST.md`
before tagging. The required check families are Ruff, pytest,
release-candidate, v2 task-registry, manuscript, reader-manuscript, whitespace,
and no staged `data/` or Parquet artifacts.
