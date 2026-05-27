# Extraction Validation Summary

- Status: `passed`
- Schema version: `gate83.extraction_validation.v1`
- Full LOG_AGE rebuild: `True`
- Result root: `data/raw/Result_Raw_Data_Version_2`
- Rebuild directory: `data/interim/extraction_validation_8_3`

## Table Comparisons

| Table | Status | Current rows | Rebuilt rows | Schema | Digest |
|---|---:|---:|---:|---:|---:|
| cell_condition_table | passed | 228 | 228 | True | True |
| checkup_event_table | passed | 4055 | 4055 | True | True |
| modality_table_pulse_raw | passed | 2475563 | 2475563 | True | True |
| modality_table_pulse_alias | passed | 2475563 | 2475563 | True | True |
| modality_table_pulse_summary | passed | 39365 | 39365 | True | True |
| modality_table_eis | passed | 1177835 | 1177835 | True | True |
| eis_spectrum_quality | passed | 39368 | 39368 | True | True |
| modality_table_log_age | passed | 904977105 | 904977105 | True | True |

## Golden Raw-Record Checks

- Checks rendered: `45`

## Failures

- None

## Warnings

- None

## Interpretation

This gate verifies parser reproducibility and raw-to-Parquet contracts. It does not add models, feature groups, or scientific claim support.
