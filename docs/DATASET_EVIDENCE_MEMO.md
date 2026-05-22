# Dataset Evidence Memo

Status: Auto-generated Gate 1.1 Integrity Report plus Gate 2 ingestion evidence
Project: Multimodal Battery Prediction (MBP)
Gate: Gate 1 — Dataset Audit & Provenance Verification

---

## Go/No-Go Decision Gate

> [!TIP]
> **GATE 1 STATUS: GO FOR DATA PRODUCTS**
> Result and reduced-log modalities are observed, BagIt validation passed successfully for the result package, and Gate 2 data-product construction is authorized. Gate 2b interval QA and split-registry audits have passed; modeling remains blocked until a LOG_AGE monotonicity handling policy selects the clean baseline subset.

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
| Generated at UTC | `2026-05-22T12:19:35+00:00` |
| Input data root | `data/raw/Result_Raw_Data_Version_2` |
| Data root exists | `True` |
| Bagging Date | `2024-09-27` |
| External Identifier | `CoNQplSNoVeXExyV` |
| Tool version | `mbp 0.1.0` |
| Preprocessing commit | `1266ccd1026e23d101f2dce8b960ce020a5560a7` |

---

## BagIt Integrity Verification

**Status**: **PASSED**  
All payload and tag files match their MD5 checksum manifests perfectly.

---

## Modality & Cell Coverage Summary

| Modality | Status | Expected Cells | Observed Cells/Files | Coverage % | Replicates (Any) | Replicates (All 3) | Total Size |
|---|---|---|---|---|---|---|---|
| cfg | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 0.39 MB |
| eoc | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 555.95 MB |
| eis | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 179.52 MB |
| pulse | **COMPLETE** | 228 | 228 | 100.0% | 76 | 76 | 263.17 MB |
| log | **OBSERVED** | N/A | 3 | 0.0% | N/A | N/A | 71307.16 MB |
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
| Unique cohort cells | `228` |
| Non-cohort cells in table | `0` |
| Latest QA status | `failed` |
| LOG_AGE monotonicity violations | `7,107` strict QA decreases flagged; `7,071` default-tolerance detailed violations |
| `cap_aged_est_Ah` non-null rows | `4,774` |
| `R0_mOhm` non-null rows | `4,755` |
| `R1_mOhm` non-null rows | `4,755` |

Inserted LOG_AGE diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) are active leakage risks. They may be counted and masked for QA, but must not enter interval features unless they are explicitly prior-to-cutoff values.

---

## Gate 2b Data-Product Hardening Evidence

| Artifact | Status | Key evidence |
|---|---|---|
| LOG_AGE monotonicity report | `generated` | `7,071` detailed violations; `463` summary CSV lines |
| Interval QA report | `passed` | `3,827` intervals; `1,054` monotonicity-flagged; LOG_AGE availability `1.0` |
| Split registry audit | `passed` | `228` cells; hot holdout uses 40 C; high-C-rate holdout includes 5/3 C |
| Raw LOG archive inventory | `generated` | `541` archive members inventoried; sampled header available `True` |

Gate 2b classifies the LOG_AGE monotonicity issue as small EFC decreases in the reduced table and propagates affected rows into interval quality flags. Clean-baseline training remains unauthorized until the handling policy explicitly defines whether flagged intervals are excluded, tolerated, or used only for sensitivity analysis.

---

## Known-Issue Register

| ID | Issue | Severity | Status | Evidence | Handling Decision |
|---|---|---|---|---|---|
| KI001 | EIS coverage and valid-frequency masks | high | `pending_audit` | EIS-like files observed | Do not make EIS-supervised claims until coverage and valid masks pass. |
| KI002 | PULSE provenance | high | `pending_audit` | PULSE-like files observed | Verify pulse source and extraction path before resistance claims. |
| KI003 | LOG gaps and runtime anomalies | medium | `pending_audit` | LOG-like files observed | Quantify gaps, reboots, pool incidents, and EOL truncation from logs. |
| KI004 | LOG_AGE leakage risk | high | `active_mitigation` | 904,977,105 LOG_AGE rows ingested | Mask inserted future diagnostics before interval modeling. |
| KI005 | Version and source metadata | high | `pending_manual_metadata` | 38 local files observed | Record DOI, source URL, archive names, download dates, and SHA-256 hashes. |
| KI006 | LOG_AGE timestamp/EFC monotonicity violations | medium | `flagged_by_qa` | 7,107 timestamp/EFC decreases detected | Investigate or quality-flag affected intervals before treating them as clean exposure evidence. |

---

## Gate 1 Decision

| Decision item | Status | Notes |
|---|---|---|
| Archive hashes recorded | Complete | Requires downloaded archives. |
| File inventory generated | Complete | Generated from observed local files. |
| Dataset manifest generated | Complete | Preliminary manifest only until source metadata is filled. |
| Required modality coverage verified | Complete | Coverage is file-level for raw archives and parser-backed for interim tables with QA. |
| Gate 2 QA status | `failed` | modality_table_log_age: 7107 timestamp/EFC monotonicity violations detected! |
| Gate 2b interval QA | `passed` | 1,054 intervals carry LOG_AGE monotonicity flags. |
| Gate 2b split audit | `passed` | Headline OOD folds are non-empty and parameter-set triplets remain grouped. |
| Known issues register initialized | Complete | Checks remain pending or blocked until data evidence exists. |
| Modeling authorized | No | Gate 2 data products are authorized; model training waits for QA resolution, leakage checks, split provenance, and baseline gates. |
