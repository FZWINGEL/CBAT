# Schema Registry

Schema version prefix: `gate1.audit.v1`

| Data product | Status | Owner module | Required provenance |
|---|---|---|---|
| `file_inventory` | Implemented | `mbp.audit.inventory` | data root, tool, generated timestamp, schema version, SHA-256 |
| `DATASET_MANIFEST.json` | Implemented | `mbp.audit.manifest` | data root, tool version, preprocessing commit, generated timestamp |
| `MANIFEST.sha256` | Implemented | `mbp.audit.manifest` | relative path and SHA-256 per observed file |
| `modality_coverage.csv` | Placeholder implemented | `mbp.audit.coverage` | modality family, observed files, rows, status |
| `known_issues.csv` | Placeholder implemented | `mbp.audit.known_issues` | issue ID, severity, status, evidence |
| `cell_condition_table` | Not implemented | `mbp.data.products.condition_table` | source files, parser version, schema version |
| `checkup_event_table` | Not implemented | `mbp.data.products.checkup_event_table` | source files, parser version, schema version |
| `run_event_table` | Not implemented | `mbp.data.products.run_event_table` | source files, parser version, schema version |
| `modality_table_eis` | Not implemented | `mbp.data.products.modality_tables` | source files, parser version, EIS validity masks |
| `modality_table_pulse` | Not implemented | `mbp.data.products.modality_tables` | source files, parser version, pulse provenance |
| `interval_table` | Not implemented | `mbp.data.products.interval_table` | joined inputs, alignment version, leakage checks |

