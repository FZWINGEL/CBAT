# Benchmark Reproducibility

Milestone 3.1 turns the completed benchmark evidence into a reproducible
release-candidate package. This document describes how to rerun the benchmark
locally without adding new scientific claims.

## Scope

This release-hardening pass covers existing data products, grouped baselines,
diagnostics, and synthesis reports. It does not authorize new model training
beyond rerunning documented commands, new feature engineering, CBAT, neural or
sequence models, DRT, EIS embeddings, policy ranking, causal claims, same-cell
counterfactual claims, or broad multimodal claims.

## Environment

Use Python 3.11+ and `uv`.

```bash
uv sync --extra dev --extra baseline
```

If the local cache location is constrained, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev --extra baseline
```

Validation commands for the release package:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
git diff --check
```

For a docs-only release-hardening change, `git diff --check` is the required
minimum validation. Run `ruff` and `pytest` whenever code changes.

## Raw Data Placement

Raw archives and generated Parquets remain local. The benchmark assumes the
local data tree described by the existing audit and ingest commands, but raw
data must not be committed.

Expected local generated products include:

- `data/interim/interval_table.parquet`
- `data/splits/interval_subset_registry_v1.parquet`
- `data/interim/interval_stress_features_v1_1.parquet`
- `data/interim/run_event_table_v1.parquet`
- `data/interim/interval_sequence_features_v1.parquet`
- `data/interim/pulse_target_table.parquet`
- `data/interim/eis_feature_table_v1.parquet`
- `data/interim/eis_target_table_v1.parquet`
- `data/interim/knee_candidate_table_v1.parquet`
- `data/interim/threshold_event_label_table_v1.parquet`
- `data/interim/threshold_warning_table_v1.parquet`
- `data/processed/*_predictions.parquet`

## Artifact Policy

Tracked artifacts:

- source code
- configuration and schema documentation
- audit reports
- baseline reports
- diagnostic reports
- synthesis reports
- manuscript assets that are intentionally tracked

Ignored artifacts:

- raw data
- interim Parquet data products
- processed prediction Parquets
- local cache files
- generated data artifacts not explicitly committed as reports

Before committing:

```bash
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

This should return no generated data products.

## Report Policy

Reports should be provenance-bearing and source-linked. If a report supports a
claim, it should be listed in `reports/synthesis/artifact_manifest_v2.csv` and
referenced by `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` or
`reports/synthesis/main_project_claim_matrix_v2.csv`.

Blocked claims remain blocked unless a later milestone explicitly changes the
claim ledger with supporting grouped evidence.
