# Milestone 7.0 - Benchmark Task Freeze and Leaderboard Reproducibility Gate

## Scope

Milestone 7.0 freezes the completed benchmark evidence base into a task
registry and task-level synthesis artifacts. This is benchmark infrastructure:
it uses existing tracked reports only and does not train models, engineer
features, or introduce scientific claims.

## Commands

```bash
mbp report check-benchmark-tasks \
  --task-registry configs/benchmark_tasks_v1.yaml \
  --out reports/synthesis/benchmark_task_registry_check.md \
  --leaderboard-out reports/synthesis/benchmark_leaderboard_v1.csv \
  --task-cards-out reports/synthesis/benchmark_task_cards_v1.md \
  --model-cards-out reports/synthesis/benchmark_model_cards_v1.md
```

## Outputs

- `configs/benchmark_tasks_v1.yaml`
- `reports/synthesis/benchmark_task_registry_check.md`
- `reports/synthesis/benchmark_leaderboard_v1.csv`
- `reports/synthesis/benchmark_task_cards_v1.md`
- `reports/synthesis/benchmark_model_cards_v1.md`

The registry freezes 12 task definitions:

- next-check-up capacity generalization;
- PULSE RT/50 scalar diagnostic endpoint;
- gated EIS scalar diagnostic endpoint;
- 80% threshold-event forecasting diagnostic;
- threshold-warning probability calibration;
- grouped capacity uncertainty calibration;
- temporal-order value falsification;
- adaptive stressor-robust C-rate delta diagnostic;
- hierarchical replicate-aware capacity comparator;
- multi-horizon capacity forecasting diagnostic;
- prior-trajectory shape horizon diagnostic;
- semi-empirical comparator and replicate uncertainty checks.

## Validation Result

`mbp report check-benchmark-tasks` passed after validating:

- all task primary claim IDs exist in the v2 claim ledger and claim matrix;
- task statuses match the primary claim status in
  `reports/synthesis/main_project_claim_matrix_v2.csv`;
- source artifacts exist;
- local generated data artifacts are listed only under ignored `data/`
  locations;
- supported task wording does not mark blocked CBAT, policy, causal,
  calibrated-risk, calibrated-uncertainty, sequence/neural, DRT, EIS embedding,
  or broad multimodal claims as supported.

## Decision

The benchmark is now frozen as a task-level ML research artifact. Use the task
registry and leaderboard as the interface for future release maintenance,
external review, or manuscript integration.

Do not open CBAT, neural/sequence models, policy ranking, causal claims,
calibrated risk, calibrated uncertainty, or broad multimodal claims from this
milestone. Any future technical work requires a fresh predeclared question.
