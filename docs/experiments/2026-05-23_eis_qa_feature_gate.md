# Milestone 2.0 - EIS QA and Feature Gate

## Scope

Milestone 2.0 opens EIS as a gated QA and scalar feature-readiness modality. It
does not implement EIS predictive modeling, DRT features, learned EIS
embeddings, capacity+PULSE+EIS multimodal models, policy ranking, CBAT, or EIS
improvement claims.

## Commands

```bash
.venv/bin/mbp eis qa \
  --eis-table data/interim/modality_table_eis.parquet \
  --eis-quality data/interim/eis_spectrum_quality.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/eis_qa_report.json \
  --coverage-out reports/audit/eis_coverage_report.csv \
  --alignment-out reports/audit/eis_alignment_report.json \
  --frequency-out reports/audit/eis_valid_frequency_report.csv

.venv/bin/mbp eis alignment-sensitivity \
  --eis-quality data/interim/eis_spectrum_quality.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/eis_alignment_sensitivity_report.json \
  --coverage-out reports/audit/eis_alignment_sensitivity_coverage.csv

.venv/bin/mbp eis build-features \
  --eis-table data/interim/modality_table_eis.parquet \
  --eis-quality data/interim/eis_spectrum_quality.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/eis_feature_table_v1.parquet \
  --soc-percent 50 \
  --temperature-context RT

.venv/bin/mbp eis feature-qa \
  --eis-features data/interim/eis_feature_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/eis_feature_qa_report.json

.venv/bin/mbp eis claim-readiness \
  --qa-report reports/audit/eis_qa_report.json \
  --feature-qa-report reports/audit/eis_feature_qa_report.json \
  --out reports/audit/eis_claim_readiness.md
```

## QA Summary

| Item | Result |
|---|---:|
| EIS rows | 1,177,835 |
| Spectrum-quality rows | 39,368 |
| Unique cells | 228 |
| Unique parameter sets | 76 |
| Unique check-up indices | 29 |
| RT spectra | 19,911 |
| OT spectra | 19,457 |
| RT/50 feature rows | 3,983 |

SOC coverage is broad across the expected five contexts:

| SOC | Spectra |
|---:|---:|
| 10 | 7,874 |
| 30 | 7,874 |
| 50 | 7,874 |
| 70 | 7,871 |
| 90 | 7,875 |

## Valid-Frequency Mask

The stored EIS modeling mask matches the Milestone 2.0 policy audit with zero
mask mismatches.

| Frequency bucket | Rows | Policy modeling rows | Mask mismatches |
|---|---:|---:|---:|
| below 0.5 Hz | 121,845 | 0 | 0 |
| 100 Hz excluded | 40,615 | 0 | 0 |
| 208.3 Hz excluded | 40,615 | 0 | 0 |
| 14.7 kHz excluded | 40,615 | 0 | 0 |
| above 5 kHz | 81,230 | 0 | 0 |
| modeling band other | 852,915 | 851,063 | 0 |

The median valid modeling fraction is 0.724137931 and the median valid modeling
frequency count is 21.

## Alignment

Alignment is quantified but remains a reporting sensitivity before any EIS
baseline:

| Statistic | Alignment delta seconds |
|---|---:|
| min | 1,265 |
| median | 40,905 |
| p95 | 107,879.5 |
| max | 192,238 |
| rows > 24 h | 4,940 |

Alignment-threshold sensitivity retained all 228 cells and 76 parameter sets at
all evaluated thresholds:

| Threshold | Retained spectra | C-rate rows | Profile rows |
|---|---:|---:|---:|
| <=6 h | 14,829 | 471 | 2,944 |
| <=12 h | 20,166 | 768 | 3,895 |
| <=24 h | 34,428 | 1,261 | 6,821 |
| <=36 h | 38,071 | 1,664 | 7,392 |
| all | 39,368 | 1,790 | 7,616 |

## Feature Table

`data/interim/eis_feature_table_v1.parquet` is an ignored generated sidecar with
one RT/50 feature row per available cell/check-up context. It contains:

- E1 selected-frequency features at 0.5 Hz, 1 Hz, 10 Hz, 1 kHz, and 5 kHz;
- E2 nullable R0/R1 placeholders marked `unavailable` and
  `r0_r1_leakage_safe = false`;
- E3 geometric Nyquist summaries;
- alignment delta, valid modeling fraction, quality flags, schema version, and
  feature policy version.

Feature QA found 3,983 RT/50 rows, 228 cells, and 76 parameter sets. It warns
that selected-frequency features are missing for a small number of rows
(`0p5Hz`: 15 rows; `1Hz`, `10Hz`, `1kHz`, and `5kHz`: 5 rows each).

## Claim Readiness

EIS is supported for QA and feature-readiness reporting. EIS predictive claims
remain blocked. DRT features and learned EIS embeddings remain blocked. R0/R1
features are diagnostic-only until provenance and leakage safety are explicit.

## Validation

Focused synthetic tests passed:

```bash
.venv/bin/pytest tests/test_eis_features.py -p no:cacheprovider
```

Full validation should include:

```bash
.venv/bin/ruff check . --no-cache
.venv/bin/pytest -p no:cacheprovider
git diff --check
```
