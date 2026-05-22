# Repository Status

Last updated: 2026-05-22

Current HEAD: `8ee7642 Complete Gate 2b LOG_AGE triage`

## Executive Summary

The repository is in **Gate 2b: LOG_AGE integrity triage and interval-table
hardening**. Gate 2b implementation is complete enough to support a clean
policy decision, but baseline modeling remains blocked until that policy is
chosen and documented.

The repo now has reproducible commands and committed audit evidence for:

- LOG_AGE monotonicity violation classification.
- Interval table contamination mapping and interval QA.
- Split-registry OOD fold audit.
- Raw LOG archive inventory scaffolding.
- Updated evidence memo, known issues, schema registry, decision log, and
  agent instructions.

No model training, baseline leaderboard, neural architecture, policy ranking, or
EIS embedding work has been started.

## Git And Artifact Hygiene

The Git worktree was clean before this status file was added. The latest Gate 2b
implementation was committed and pushed as:

```text
8ee7642 Complete Gate 2b LOG_AGE triage
```

Large data products and local tool artifacts remain ignored and are not tracked:

- `data/raw/**`
- `data/interim/**`
- `data/processed/**`
- `data/splits/*.parquet`
- `reports/audit/*.parquet`
- `.antigravitycli/`
- local CodeGraph databases, Python caches, Ruff/Pytest caches, and `.venv/`

Small audit sidecars that are referenced by documentation are tracked:

- `reports/audit/interval_qa_report.json`
- `reports/audit/log_age_monotonicity_summary.csv`
- `reports/audit/split_registry_report.json`

The large Parquet outputs remain local generated artifacts:

| Artifact | Rows | Size | Tracking |
|---|---:|---:|---|
| `data/interim/modality_table_log_age.parquet` | 904,977,105 | 28,360,384,828 bytes | ignored |
| `reports/audit/log_age_monotonicity_violations.parquet` | 7,071 | 887,570 bytes | ignored |
| `data/interim/interval_table.parquet` | 3,827 | 632,246 bytes | ignored |
| `data/splits/split_registry_v1.parquet` | 228 | 5,175 bytes | ignored |
| `reports/audit/raw_log_archive_inventory.parquet` | 541 | 13,261 bytes | ignored |

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
That QA failure is intentional and should not be suppressed until the handling
policy is set.

### Gate 2b

Gate 2b is implemented and the current reports pass where expected:

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

Quality flag distribution:

- `LOG_AGE_inserted_diagnostics_masked`: `3,826`
- `LOG_AGE_monotonicity_violation`: `1,054`

Split-registry audit key facts:

- Rows: `228`
- Parameter-set triplets remain grouped.
- Condition folds are non-empty.
- Hot temperature holdout uses `40 C`.
- High C-rate holdout includes `5/3 C`.
- Profile holdout contains profile conditions.
- Headline OOD folds are non-empty.

## Important Implementation Notes

The interval builder preserves result-table timestamps in the public schema, but
uses per-cell relative LOG_AGE windows internally when scanning reduced logs.
This matters because:

- `checkup_event_table.timestamp` is epoch-like result time.
- `modality_table_log_age.timestamp_s` is relative operating time.

The mismatch was fixed before the current interval table was regenerated. The
regression test `test_aligns_epoch_checkups_to_relative_log_age_time` now covers
this behavior.

The LOG_AGE monotonicity audit writes atomically:

- Details are written to a temporary Parquet path first.
- The final report is replaced only after the writer closes successfully.

This prevents a crash or timeout from leaving a corrupt final Parquet report.

## Current Blocker Before Baselines

Do **not** start baseline modeling yet.

The remaining blocker is the monotonicity handling policy for the `1,054`
affected interval rows. The next decision should explicitly choose one of:

- Treat default-tolerance EFC decreases as tiny floating-point jitter and keep
  affected intervals in clean baselines.
- Exclude `LOG_AGE_monotonicity_violation` intervals from clean-baseline
  training and reserve them for sensitivity analysis.
- Add a nonzero EFC tolerance to strict QA, regenerate reports, and document the
  tolerance as a scientific policy.
- Segment or otherwise specially handle affected cell histories if later raw LOG
  evidence shows real discontinuities.

Until this is decided, the repo is ready for policy selection but not clean
baseline training.

## Validation

Latest validation run:

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check .
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest
56 passed, 1 warning.
```

The one warning is the existing `datetime.utcnow()` deprecation warning in
`src/mbp/data/luh_blank/qa_result_data.py`; it is not a Gate 2b correctness
failure.

## Recommended Next Step

Make the LOG_AGE monotonicity handling policy explicit in docs and code. Once
that policy is recorded, the first baseline ladder can begin on the defined
clean interval subset, with a separate sensitivity run including flagged
intervals.
