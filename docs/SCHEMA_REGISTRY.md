# Schema Registry

Schema version prefix: `gate1.audit.v1`

| Data product | Status | Owner module | Required provenance |
|---|---|---|---|
| `file_inventory` | Implemented | `mbp.audit.inventory` | data root, tool, generated timestamp, schema version, SHA-256 |
| `DATASET_MANIFEST.json` | Implemented | `mbp.audit.manifest` | data root, tool version, preprocessing commit, generated timestamp |
| `MANIFEST.sha256` | Implemented | `mbp.audit.manifest` | relative path and SHA-256 per observed file |
| `modality_coverage.csv` | Placeholder implemented | `mbp.audit.coverage` | modality family, observed files, rows, status |
| `known_issues.csv` | Placeholder implemented | `mbp.audit.known_issues` | issue ID, severity, status, evidence |
| `cell_condition_table` | Implemented | `mbp.data.luh_blank.parse_cfg` | source files, parser version, schema version |
| `checkup_event_table` | Implemented | `mbp.data.luh_blank.parse_eoc` | source files, parser version, schema version |
| `run_event_table` | Not implemented | `mbp.data.products.run_event_table` | source files, parser version, schema version |
| `modality_table_eis` | Implemented | `mbp.data.luh_blank.parse_eis` | source files, parser version, EIS validity masks |
| `modality_table_pulse` | Implemented | `mbp.data.luh_blank.parse_pulse` | source files, parser version, pulse provenance |
| `modality_table_log_age` | Implemented | `mbp.data.luh_blank.parse_log` | source archive, source file, cohort exclusion report, diagnostic masking rules |
| `split_registry_v1` | Implemented | `mbp.data.splitting` | condition table, deterministic seed, grouped parameter-set folds |
| `interval_table` | Implemented MVP | `mbp.data.products.interval_table` | joined inputs, split registry SHA-256, LOG_AGE row-group exposure scan, monotonicity report path, leakage checks |

## Gate 2/3 Schema Contracts

- `MODALITY_TABLE_LOG_AGE_SCHEMA` contains reduced operating-log signals plus nullable inserted diagnostics. The inserted diagnostic values are not interval features by default.
- `INTERVAL_TABLE_SCHEMA` is one row per adjacent `checkup_event_table` transition. It includes condition metadata, split labels, prior/post capacity targets, LOG_AGE exposure summaries, masked diagnostic-row counts, monotonicity violation counts/drop magnitudes, `LOG_AGE_monotonicity_clean`, quality flags, and schema provenance.
- `SPLIT_REGISTRY_SCHEMA` keeps replicates of each 76-parameter condition triplet grouped for headline validation.
