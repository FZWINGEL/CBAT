# Repository Status

Last updated: 2026-05-22

Current branch: `main`

Current commit: see `git log -1 --oneline`. This file is updated whenever
significant repository state changes happen, but it intentionally avoids a
self-referential commit hash that would become stale when the status file itself
is committed.

## Executive Summary

The repository is in **Milestone 0.4: Baseline Readiness Gate**. The Gate 2b
LOG_AGE integrity triage is complete, and Milestone 0.4 now adds the policy and
subset artifacts needed to authorize the first baseline ladder in a later work
block.

No model training, baseline leaderboard, neural architecture, policy ranking, or
EIS embedding work has been started.

Current state:

- LOG_AGE monotonicity policy is documented in
  `docs/LOG_AGE_MONOTONICITY_POLICY.md`.
- Interval subset registry generation is implemented with
  `mbp split interval-subsets`.
- `reports/audit/interval_subset_report.json` records strict/tolerant clean
  interval counts under policy version `log_age_monotonicity.v1`.
- Split registry semantics now include corrected voltage-window holdout folds
  derived from `voltage_window_family`, not scalar `age_soc`.
- `pyarrow` and `py7zr` are core dependencies; baseline and GBM packages are
  optional extras only.

## Git And Artifact Hygiene

Large data products and local tool artifacts remain ignored and are not tracked:

- `data/raw/**`
- `data/interim/**`
- `data/processed/**`
- generated Parquet outputs under `data/splits/`
- generated Parquet outputs under `reports/audit/`
- `.antigravitycli/`
- local CodeGraph databases, Python caches, Ruff/Pytest caches, and `.venv/`

Small audit sidecars that are referenced by documentation are tracked:

- `reports/audit/interval_qa_report.json`
- `reports/audit/interval_subset_report.json`
- `reports/audit/log_age_monotonicity_summary.csv`
- `reports/audit/split_registry_report.json`

The large Parquet outputs remain local generated artifacts:

| Artifact | Rows | Tracking |
|---|---:|---|
| `data/interim/modality_table_log_age.parquet` | 904,977,105 | ignored |
| `reports/audit/log_age_monotonicity_violations.parquet` | 7,071 | ignored |
| `data/interim/interval_table.parquet` | 3,827 | ignored |
| `data/splits/split_registry_v1.parquet` | 228 | ignored |
| `data/splits/interval_subset_registry_v1.parquet` | 3,827 | ignored |
| `reports/audit/raw_log_archive_inventory.parquet` | 541 | ignored |

## Gate Status

### Gate 1

Gate 1 remains **GO FOR DATA PRODUCTS**.

Result-package coverage is complete for the 228-cell cohort:

- CFG: complete.
- EOC: complete.
- EIS: complete, but valid-frequency audit is still pending before EIS claims.
- PULSE: complete, but pulse provenance/alignment hardening remains a known
  issue.

BagIt validation for the result package passed.

### Gate 2

Gate 2 ingestion products exist for:

- `cell_condition_table`
- `checkup_event_table`
- `modality_table_eis`
- `modality_table_pulse`
- `modality_table_log_age`
- `split_registry_v1`
- `interval_table`

LOG_AGE ingestion evidence:

- Source archive: `cell_log_age_ultracompr.7z`
- Cohort rows: `904,977,105`
- Cohort cells: `228`
- Auxiliary LOG_AGE CSV records excluded: `48`
- Final Parquet row groups: `257,311`

Strict LOG_AGE QA still reports `7,107` timestamp/EFC monotonicity decreases.
That strict QA failure is preserved as an evidence signal. Milestone 0.4 defines
how those decreases are handled for baseline subset construction.

### Gate 2b

Gate 2b is complete:

- `reports/audit/log_age_monotonicity_violations.parquet` contains `7,071`
  detailed default-tolerance violations.
- `reports/audit/log_age_monotonicity_summary.csv` has `463` lines.
- Summary rows show the observed detailed violations are EFC decreases, with
  zero timestamp decreases in the default-tolerance report.
- Worst detailed EFC drops are approximately `0.0002` EFC.
- `reports/audit/interval_qa_report.json` passes.
- `reports/audit/split_registry_report.json` passes.
- `reports/audit/raw_log_archive_inventory.parquet` inventories raw LOG archive
  members without parsing the full raw LOG corpus.

Interval QA key facts:

- Interval rows: `3,827`
- Expected interval count: `3,827`
- Check-up event rows: `4,055`
- Cells with check-ups: `228`
- LOG_AGE availability fraction: `1.0`
- Intervals with zero LOG_AGE rows: `0`
- Intervals with monotonicity violations: `1,054`
- Non-cohort cells: `0`
- Masked diagnostic rows:
  - `cap_aged_est_Ah`: `4,577`
  - `R0_mOhm`: `4,577`
  - `R1_mOhm`: `4,577`

### Milestone 0.4

Milestone 0.4 data products are implemented:

- Policy: `docs/LOG_AGE_MONOTONICITY_POLICY.md`
- CLI: `mbp split interval-subsets`
- Registry: `data/splits/interval_subset_registry_v1.parquet`
- Report: `reports/audit/interval_subset_report.json`

Interval subset policy counts:

| Subset or exclusion | Count |
|---|---:|
| Full interval table | 3,827 |
| `baseline_clean_strict` | 2,773 |
| `baseline_clean_tolerant` | 3,827 |
| `sensitivity_flagged_monotonicity` | 1,054 |
| `small_efc_jitter` | 1,054 |
| Excluded due to timestamp drop | 0 |
| Excluded due to large EFC drop | 0 |
| Excluded due to missing LOG_AGE | 0 |
| Excluded due to duration error | 0 |

The tolerant subset keeps tiny EFC-only LOG_AGE jitter at or below `0.00025`
EFC. The strict subset excludes all monotonicity-flagged intervals and should be
used as the mandatory sensitivity subset for first baselines.

Split-registry audit key facts after the voltage-window fix:

- Rows: `228`
- Parameter-set triplets remain grouped.
- Condition folds are non-empty.
- Hot temperature holdout uses `40 C`.
- High C-rate holdout includes `5/3 C`.
- Profile holdout contains profile conditions.
- Voltage-window holdout is non-empty:
  - fold `1`: `84` full-window `approx_0_100` cells
  - fold `2`: `96` reduced-window `approx_10_100` / `approx_10_90` cells
  - fold `3`: `48` calendar idle-SOC cells

The legacy `soc_window_holdout_fold` remains present for compatibility but is
now populated from corrected voltage-window semantics. New work should prefer
`voltage_window_holdout_fold`.

## Important Implementation Notes

The interval builder preserves result-table timestamps in the public schema, but
uses per-cell relative LOG_AGE windows internally when scanning reduced logs.
This matters because:

- `checkup_event_table.timestamp` is epoch-like result time.
- `modality_table_log_age.timestamp_s` is relative operating time.

The mismatch is covered by
`test_aligns_epoch_checkups_to_relative_log_age_time`.

The LOG_AGE monotonicity audit writes atomically:

- Details are written to a temporary Parquet path first.
- The final report is replaced only after the writer closes successfully.

This prevents a crash or timeout from leaving a corrupt final Parquet report.

The interval subset registry writes Parquet metadata for:

- schema version
- monotonicity policy version
- EFC jitter threshold
- source interval table path

## Baseline Authorization

Baseline data-product prerequisites now exist, but baseline modeling has not
started in this milestone. The next milestone can begin the first L0-L3 capacity
baseline ladder if explicitly requested.

First baseline work must use:

- primary subset: `baseline_clean_tolerant`
- mandatory sensitivity subset: exclude
  `sensitivity_flagged_monotonicity == true`
- targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- split views: condition, temperature, C-rate, profile, and corrected
  voltage-window holdouts
- no EIS, PULSE, sequence models, neural models, policy ranking, or CBAT
  architecture

EIS and PULSE scientific claims remain blocked by their known audit issues.

## Validation

Latest validation run:

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check .
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest
56 passed, 1 warning.
```

The one warning is the existing `datetime.utcnow()` deprecation warning in
`src/mbp/data/luh_blank/qa_result_data.py`; it is not a Milestone 0.4
correctness failure.

## Recommended Next Step

Start **Milestone 0.5: L0-L3 Baseline Ladder** only after confirming that the
baseline code will consume `interval_subset_registry_v1.parquet` and report
strict-vs-tolerant sensitivity results. Keep the first baseline deliberately
limited to capacity targets and scalar interval features.
