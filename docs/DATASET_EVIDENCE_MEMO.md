# Dataset Evidence Memo

Status: Gate 1.1 Integrity Report plus Gate 2 ingestion evidence
Project: Multimodal Battery Prediction (MBP)
Gate: Gate 1 — Dataset Audit & Provenance Verification

---

## Go/No-Go Decision Gate

> [!TIP]
> **GATE 1 STATUS: GO FOR DATA PRODUCTS**
> Result and reduced-log modalities are observed, BagIt validation passed successfully for the result package, and Gate 2 data-product construction is authorized. Modeling remains blocked until interval tables, leakage checks, split provenance, and baseline gates are complete.

---

## Dataset Metadata & Provenance

**Title**: Comprehensive battery aging dataset: capacity and impedance fade measurements of a lithium-ion NMC/C-SiO cell [dataset – version 2: result data]  
**DOI**: 10.35097/1969  
**Creators**: Luh, Matthias, Blank, Thomas  
**Publication Year**: 2024  
**Rights / License**: CC BY 4.0 Attribution  

| Field | Value |
|---|---|
| Schema version | `gate1.audit.v1` |
| Generated at UTC | `2026-05-21T19:16:49+00:00` |
| Input data root | `data/raw/Result_Raw_Data_Version_2` |
| Data root exists | `True` |
| Bagging Date | `2024-09-27` |
| External Identifier | `CoNQplSNoVeXExyV` |
| Tool version | `mbp 0.1.0` |
| Preprocessing commit | `e140dd346e9ece936b2ed53cbde7efab233b7b64` |

---

## BagIt Integrity Verification

**Status**: **PASSED**  
All payload and tag files match their MD5 checksum manifests perfectly.

---

## Modality & Cell Coverage Summary

| Modality | Status | Expected Cells | Observed Cells | Coverage % | Replicates (Any) | Replicates (All 3) | Total Size |
|---|---|---|---|---|---|---|---|
| cfg | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 0.39 MB |
| eoc | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 555.95 MB |
| eis | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 179.52 MB |
| pulse | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 263.17 MB |
| log | **OBSERVED** | N/A | 2 | 0.0% | N/A | N/A | 4693.34 MB |
| log_age | **OBSERVED** | N/A | 1 | 0.0% | N/A | N/A | 6808.05 MB |

---

## LOG_AGE Ingestion Evidence

`mbp ingest log-age` has produced the reduced operating-history table at
`data/interim/modality_table_log_age.parquet`.

| Field | Value |
|---|---|
| Source package path | `data/raw/Log_Raw_Data_Version_2` |
| Source archive | `cell_log_age_ultracompr.7z` |
| Log package DOI path | `10.35097-kww7jv8ajuvchcah` |
| Ingested rows | `904,977,105` |
| Parquet size | `28,360,384,828 bytes` |
| Parquet row groups | `257,311` |
| Cohort exclusions | `48` auxiliary LOG_AGE CSV records |
| Exclusion report | `reports/audit/excluded_records_report.csv` |
| Latest QA status | `failed` on LOG_AGE monotonicity check |
| LOG_AGE monotonicity violations | `7,107` timestamp/EFC decreases flagged |

Inserted LOG_AGE diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) are active leakage risks. They may be counted and masked for QA, but must not enter interval features unless they are explicitly prior-to-cutoff values.

---

## Known-Issue Register

| ID | Issue | Severity | Status | Evidence | Handling Decision |
|---|---|---|---|---|---|
| KI001 | EIS coverage and valid-frequency masks | high | `pending_audit` | EIS-like files observed | Do not make EIS-supervised claims until coverage and valid masks pass. |
| KI002 | PULSE provenance | high | `pending_audit` | PULSE-like files observed | Verify pulse source and extraction path before resistance claims. |
| KI003 | LOG gaps and runtime anomalies | medium | `pending_audit` | LOG-like files observed | Quantify gaps, reboots, pool incidents, and EOL truncation from logs. |
| KI004 | LOG_AGE leakage risk | high | `active_mitigation` | 904,977,105 LOG_AGE rows ingested | Mask inserted future diagnostics before interval modeling. |
| KI005 | Version and source metadata | high | `pending_manual_metadata` | 37 local files observed | Record DOI, source URL, archive names, download dates, and SHA-256 hashes. |

---

## Gate 1 Decision

| Decision item | Status | Notes |
|---|---|---|
| Archive hashes recorded | Complete | Requires downloaded archives. |
| File inventory generated | Complete | Generated from observed local files. |
| Dataset manifest generated | Complete | Preliminary manifest only until source metadata is filled. |
| Required modality coverage verified | Complete | Coverage is file-level only until parsers exist. |
| Known issues register initialized | Complete | Checks remain pending or blocked until data evidence exists. |
| Modeling authorized | No | Gate 2 data products are authorized; model training waits for interval tables, leakage QA, split provenance, and baseline gates. |

## Audit Warnings

- Raw LOG remains pending for final exposure traceability; LOG_AGE is acceptable for the first interval-exposure MVP with diagnostic masking.
