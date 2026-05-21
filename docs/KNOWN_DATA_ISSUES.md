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

## Log Data Package (v2, downloading)

| ID | Issue | Affected | Severity | Status | Handling Decision |
|---|---|---|---|---|---|
| KI003 | LOG gaps and runtime anomalies | All cells with operating logs | Medium | `blocked_missing_evidence` | Quantify gap duration from LOG/slave records once download completes. |
| KI004 | LOG_AGE leakage risk | All cells with reduced logs | High | `blocked_missing_evidence` | Mask inserted future diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) before interval modeling. |

## Charter-Referenced Anomalies (Evidence Pending)

| Issue | Affected cells/files | Evidence | Severity | Handling Decision |
|---|---|---|---|---|
| Pool temperature incidents | Subset of cells (pool-specific) | Pending pool_log audit | Medium | Flag affected cells/files once pool logs are audited. |
| Peltier failure | Subset of cells (chamber-specific) | Pending slave_log audit | Medium | Flag affected cells/files once slave logs are audited. |
| Ethernet gaps | Subset of time intervals | Pending LOG audit | Low | Quantify gap duration and mark affected intervals. |
| Reboots | Subset of time intervals | Pending LOG audit | Low | Preserve as quality flags in operating log tables. |
| Interpolation | LOG_AGE derived fields | Pending LOG_AGE vs LOG comparison | Medium | Track LOG_AGE interpolation provenance per field. |
| EOL truncation | Subset of cells reaching end-of-life | Pending EOC + LOG cross-check | Medium | Preserve EOL indicators and truncation markers. |
