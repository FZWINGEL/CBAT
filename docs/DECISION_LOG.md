# Decision Log

| Date | Decision | Rationale | Consequences |
|---|---|---|---|
| 2026-05-21 | Gate 1 work is limited to audit, provenance, and skeleton data products. | Charter blocks modeling until dataset evidence is reproducible. | No training loops or model code in initial repo bootstrap. |
| 2026-05-21 | Inventory and manifest commands must run without real dataset files. | Dataset may not be downloaded yet. | Missing data roots produce provenance-bearing empty audit outputs. |
| 2026-05-22 | LOG_AGE is accepted for the first interval-exposure MVP. | `modality_table_log_age.parquet` is ingested with 904,977,105 rows, while raw LOG traceability is still needed for final exposure claims. | Interval features may use LOG_AGE exposure summaries, but inserted diagnostics are masked and counted only as leakage-risk QA signals. |
| 2026-05-22 | Split registry provenance is part of the interval table. | Frozen grouped splits are required before baseline evidence is meaningful. | `interval_table.parquet` records the split registry SHA-256 in Parquet metadata. |
| 2026-05-22 | LOG_AGE monotonicity violations remain a QA failure. | Full-data QA found 7,107 timestamp/EFC decreases in the 904,977,105-row LOG_AGE table. | Affected exposure intervals require investigation or quality flags before they can support clean baseline evidence. |
