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

Tracked reports should be small enough for review and should preserve
provenance, source paths, row counts, metrics, and claim-readiness decisions.

## Ignored Generated Parquets

Generated Parquets under `data/interim/`, `data/splits/`, and
`data/processed/` remain local ignored artifacts. They are large, derived from
raw archives, and should be reproducible from the runbook.

Examples:

- `data/interim/modality_table_log_age.parquet`
- `data/interim/run_event_table_v1.parquet`
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
