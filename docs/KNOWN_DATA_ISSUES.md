# Known Data Issues

This register records known issues, anomalies, and data gaps observed during
dataset audit and ingestion. Evidence is drawn from archive metadata, manifests,
file inventories, parser checks, and the project charter.

## Result Data Package (v2)

| ID | Issue | Affected | Severity | Status | Handling Decision |
|---|---|---|---|---|---|
| KI001 | EIS coverage and valid-frequency masks | All 228 cells | High | `pending_audit` | Do not make EIS-supervised claims until per-spectrum valid-frequency coverage is confirmed. |
| KI002 | PULSE provenance and alignment | All 228 cells | High | `pending_audit` | Verify pulse source extraction path and EOC timestamp alignment before resistance claims. |
| KI005 | Version and source metadata | Entire dataset | High | `pending_manual_metadata` | Record DOI, source URL, archive names, download dates, and SHA-256 hashes for reproducibility. |

## Log Data Package (v2)

| ID | Issue | Affected | Severity | Status | Handling Decision |
|---|---|---|---|---|---|
| KI003 | LOG gaps and runtime anomalies | All cells with operating logs | Medium | `inventory_scaffolded` | `reports/audit/raw_log_archive_inventory.parquet` inventories 541 archive members and samples one header; quantify gap duration from LOG/slave records before final exposure claims. |
| KI004 | LOG_AGE leakage risk | All cells with reduced logs | High | `active_mitigation` | Mask inserted future diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) before interval modeling. |
| KI006 | LOG_AGE timestamp/EFC monotonicity violations | Reduced LOG_AGE table and 1,054 interval rows | Medium | `triaged_and_flagged` | Strict QA detects 7,107 timestamp/EFC decreases; `reports/audit/log_age_monotonicity_violations.parquet` records 7,071 default-tolerance detailed violations, all EFC-only in the summary sample, and `interval_qa_report.json` confirms 1,054 affected intervals are quality-flagged. Define the clean-baseline exclusion/tolerance policy before modeling. |

LOG_AGE ingestion evidence: `data/interim/modality_table_log_age.parquet` contains
`904,977,105` rows in `28,360,384,828` bytes. The ingestion excluded `48`
auxiliary LOG_AGE CSV records outside the 228-cell cohort; see
`reports/audit/excluded_records_report.csv`.

Gate 2b evidence: `reports/audit/interval_qa_report.json` passes with all
`3,827` interval rows LOG_AGE-covered, `1,054` intervals carrying
`LOG_AGE_monotonicity_violation`, and inserted diagnostic rows counted but
masked from features. `reports/audit/split_registry_report.json` passes with
non-empty headline OOD folds and grouped parameter-set triplets.

## Charter-Referenced Anomalies (Evidence Pending)

| Issue | Affected cells/files | Evidence | Severity | Handling Decision |
|---|---|---|---|---|
| Pool temperature incidents | Subset of cells (pool-specific) | Pending pool_log audit | Medium | Flag affected cells/files once pool logs are audited. |
| Peltier failure | Subset of cells (chamber-specific) | Pending slave_log audit | Medium | Flag affected cells/files once slave logs are audited. |
| Ethernet gaps | Subset of time intervals | Pending LOG audit | Low | Quantify gap duration and mark affected intervals. |
| Reboots | Subset of time intervals | Pending LOG audit | Low | Preserve as quality flags in operating log tables. |
| Interpolation | LOG_AGE derived fields | Pending LOG_AGE vs LOG comparison | Medium | Track LOG_AGE interpolation provenance per field. |
| EOL truncation | Subset of cells reaching end-of-life | Pending EOC + LOG cross-check | Medium | Preserve EOL indicators and truncation markers. |
