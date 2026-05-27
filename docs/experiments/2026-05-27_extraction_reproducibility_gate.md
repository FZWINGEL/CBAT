# Milestone 8.3 - Foundational Data Extraction Reproducibility Gate

## Purpose

This gate rechecks the earliest raw-to-Parquet extraction layer because every
later benchmark result depends on those products. The charter requires
reproducible preprocessing and unit/alignment/schema audits before model
results are valid.

This is not a modeling milestone and does not add feature engineering or new
scientific claims.

## Implementation

Added:

```bash
mbp audit validate-extraction
```

The command rebuilds result-data products from raw archives into ignored
validation outputs, then compares them with current canonical interim products:

- `cell_condition_table.parquet`
- `checkup_event_table.parquet`
- `modality_table_pulse_raw.parquet`
- `modality_table_pulse_summary.parquet`
- `modality_table_eis.parquet`
- `eis_spectrum_quality.parquet`
- `modality_table_log_age.parquet` when `--full-log-age` is enabled

It writes:

- `reports/audit/extraction_validation/extraction_validation_report.json`
- `reports/audit/extraction_validation/extraction_validation_summary.md`
- `reports/audit/extraction_validation/extraction_rebuild_hashes.csv`
- `reports/audit/extraction_validation/raw_to_parquet_golden_records.csv`
- `reports/audit/extraction_validation/parser_contract_audit.csv`

## Full Validation Result

Command run:

```bash
.venv/bin/mbp audit validate-extraction \
  --result-root data/raw/Result_Raw_Data_Version_2 \
  --log-age-archive data/raw/Log_Raw_Data_Version_2/10.35097-kww7jv8ajuvchcah/data/dataset/cell_log_age_ultracompr.7z \
  --current-interim data/interim \
  --rebuild-dir data/interim/extraction_validation_8_3 \
  --out-dir reports/audit/extraction_validation \
  --sample-cells P001_1,P038_2,P076_3 \
  --full-log-age \
  --log-age-extract-dir data/interim/log_age_csv_cache_v2 \
  --skip-log-age-extract \
  --keep-log-age-extracted \
  --expected-log-age-csv-count 228 \
  --csv-block-size-bytes 8388608 \
  --log-age-digest-batch-rows 524288 \
  --csv-use-threads
```

Status: `passed`.

The required CFG/EOC/PULSE/EIS products match by row count, schema, and
semantic digest. The optional legacy `modality_table_pulse.parquet` alias also
matches after projecting the rebuilt canonical raw PULSE table to the legacy
narrower schema.

The full LOG_AGE product also passed: the current and rebuilt Parquets both
contain `904,977,105` rows. Because the rebuilt file has different row-group
layout (`8,172` row groups versus `257,311` in the current product), LOG_AGE is
validated by streaming pairwise value equality rather than a row-group-layout
sensitive byte digest.

## Golden Raw-Record Checks

The gate renders representative raw-to-Parquet checks for:

- CFG parameter/replicate/temperature/C-rate/window mapping;
- EOC discharge-row preference and charge/discharge energy handling;
- PULSE nearest-EOC alignment and mOhm-to-Ohm resistance conversion;
- EIS nearest-EOC alignment, mOhm-to-Ohm impedance conversion, NaN handling,
  and modeling-frequency masks;
- LOG_AGE raw-row/null handling when full LOG_AGE validation is run.

The full run rendered 45 passing checks.

## LOG_AGE Workflow

Full LOG_AGE rebuild validation is intentionally separated because the archive
is large. The command now supports a persistent ignored CSV cache:

```bash
.venv/bin/mbp audit validate-extraction \
  --result-root data/raw/Result_Raw_Data_Version_2 \
  --log-age-archive data/raw/Log_Raw_Data_Version_2/10.35097-kww7jv8ajuvchcah/data/dataset/cell_log_age_ultracompr.7z \
  --current-interim data/interim \
  --rebuild-dir data/interim/extraction_validation_8_3 \
  --out-dir reports/audit/extraction_validation \
  --sample-cells P001_1,P038_2,P076_3 \
  --full-log-age \
  --log-age-extract-dir data/interim/log_age_csv_cache_v2 \
  --skip-log-age-extract \
  --keep-log-age-extracted \
  --expected-log-age-csv-count 228 \
  --csv-block-size-bytes 8388608 \
  --log-age-digest-batch-rows 524288 \
  --csv-use-threads
```

If a stopped run leaves a partial cache, the parser rejects it unless at least
the expected CSV count is present. This prevents a partial extraction from
silently becoming evidence. The validator compares full LOG_AGE products by
streaming pairwise value equality so the 904M-row table does not need to be
loaded into memory.

## Validation

Commands run:

```bash
.venv/bin/ruff check src/mbp/audit/extraction_validation.py src/mbp/data/luh_blank/parse_log.py src/mbp/cli.py tests/test_extraction_validation.py --no-cache
.venv/bin/pytest tests/test_extraction_validation.py tests/test_gate3_splitting.py::TestLogAgeIngestion::test_ingest_log_age_parser -q
.venv/bin/pytest -p no:cacheprovider
.venv/bin/mbp audit validate-extraction --result-root data/raw/Result_Raw_Data_Version_2 --current-interim data/interim --rebuild-dir data/interim/extraction_validation_8_3 --out-dir reports/audit/extraction_validation --sample-cells P001_1,P038_2,P076_3
.venv/bin/mbp audit validate-extraction --result-root data/raw/Result_Raw_Data_Version_2 --log-age-archive data/raw/Log_Raw_Data_Version_2/10.35097-kww7jv8ajuvchcah/data/dataset/cell_log_age_ultracompr.7z --current-interim data/interim --rebuild-dir data/interim/extraction_validation_8_3 --out-dir reports/audit/extraction_validation --sample-cells P001_1,P038_2,P076_3 --full-log-age --log-age-extract-dir data/interim/log_age_csv_cache_v2 --skip-log-age-extract --keep-log-age-extracted --expected-log-age-csv-count 228 --csv-block-size-bytes 8388608 --log-age-digest-batch-rows 524288 --csv-use-threads
```

Results:

- ruff: passed;
- targeted tests: passed;
- full test suite: 257 passed;
- real result-data extraction validation: passed;
- full LOG_AGE cached rebuild and streaming value-equality validation: passed.

## Remaining Work

The extraction reproducibility gate is closed for the tracked current products:
CFG, EOC, PULSE, EIS, and LOG_AGE all rebuild to matching canonical products
under the validation policy. This does not remove downstream QA caveats such as
LOG_AGE leakage masking, PULSE/EIS alignment limits, or grouped-validation
claim guardrails.
