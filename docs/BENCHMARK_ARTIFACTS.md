# Benchmark Artifacts

This document explains which benchmark outputs are tracked and which remain
local generated data.

## Tracked Reports

Tracked reports include:

- audit reports under `reports/audit/`
- baseline reports under `reports/baselines/`
- analysis reports under `reports/analysis/`
- synthesis reports under `reports/synthesis/`
- experiment memos under `docs/experiments/`
- claim ledgers and policy documents under `docs/`
- benchmark task registry config under `configs/benchmark_tasks_v1.yaml`

Tracked reports should be small enough for review and should preserve
provenance, source paths, row counts, metrics, and claim-readiness decisions.

Milestone 7.0 adds a frozen task-level benchmark interface:

- `configs/benchmark_tasks_v1.yaml`
- `reports/synthesis/benchmark_task_registry_check.md`
- `reports/synthesis/benchmark_leaderboard_v1.csv`
- `reports/synthesis/benchmark_task_cards_v1.md`
- `reports/synthesis/benchmark_model_cards_v1.md`

These artifacts summarize existing evidence only; they do not train models or
change claim status.

Milestone 7.1 adds tracked sequence reopening evidence:

- `reports/audit/interval_event_sequence_qa_report.json`
- `reports/baselines/minimal_sequence_reopening_report.json`
- `reports/baselines/minimal_sequence_reopening/sequence_reopening_claim_readiness.md`
- `docs/experiments/2026-05-27_minimal_sequence_reopening_gate.md`

These artifacts document a negative CUDA-backed H7 reopening check. The local
event-sequence and prediction Parquets remain ignored.

## Ignored Generated Parquets

Generated Parquets under `data/interim/`, `data/splits/`, and
`data/processed/` remain local ignored artifacts. They are large, derived from
raw archives, and should be reproducible from the runbook.

Examples:

- `data/interim/modality_table_log_age.parquet`
- `data/interim/run_event_table_v1.parquet`
- `data/interim/interval_event_sequence_table_v1.parquet`
- `data/interim/eis_feature_table_v1.parquet`
- `data/interim/threshold_warning_table_v1.parquet`
- `data/processed/*_predictions.parquet`

## Prediction Parquets

Prediction Parquets are not source evidence by themselves. The tracked JSON,
CSV, and Markdown reports derived from them are the reviewable artifacts.

## Manuscript Artifacts

Manuscript files and generated SVG/Markdown assets are tracked only when they
are part of the deliberate manuscript package. The benchmark release package is
separate from manuscript polish.

## Why Data Products Are Not Committed

The raw and generated data products are large and can be regenerated from the
local raw archives. Committing them would make review harder, risk accidental
raw-data publication, and weaken the audit boundary between source data,
derived data products, and tracked evidence reports.
