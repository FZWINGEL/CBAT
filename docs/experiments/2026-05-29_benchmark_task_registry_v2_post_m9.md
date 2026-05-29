# Post-Milestone-9 Benchmark Task Registry v2 Alignment

## Purpose

Align the benchmark release-maintenance surfaces after the completed negative
Milestone 9 neural sequence architecture gate. This is source-of-truth
synchronization and reproducibility hardening, not a new modeling branch.

## Changes

- Added C38 to the machine-readable main-project claim matrix.
- Added exact Milestone 9 tracked report, plot, and figure rows to the artifact
  manifest, plus ignored local generated tensor and prediction artifacts.
- Created `configs/benchmark_tasks_v2.yaml` as the post-Milestone-9 task
  registry with `T20_neural_sequence_architecture_gate`.
- Generated v2 task-registry check, leaderboard, task cards, and model cards.
- Kept `benchmark-v0.1-rc2` as the public release anchor and documented the
  distinction between rc2 and current `main`.

## Validation

`mbp report check-benchmark-tasks` passes for the v2 registry with 20 tasks and
no warnings. The Milestone 9 task is `not_supported`, with C38 as its primary
claim and local Parquet artifacts marked as ignored generated data.

## Decision

The repository remains in post-Milestone-9 release maintenance. Neural sequence
next-gate readiness and CBAT prototype readiness remain blocked; allowed follow
up work is synthesis, release alignment, reproducibility maintenance, and
manuscript/package handoff.
