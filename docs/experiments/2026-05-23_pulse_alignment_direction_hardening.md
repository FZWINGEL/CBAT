# 2026-05-23 PULSE Alignment, Direction, and Target-Coverage Hardening

## Scope

Milestone 0.7.1 hardens the canonical PULSE RT/50% target before any PULSE
resistance claim. This remains a scalar resistance-baseline milestone only. It
does not authorize EIS modeling, EIS embeddings, knee prediction, sequence
models, neural models, policy ranking, CBAT, or capacity+PULSE multimodal
claims.

## Implementation

Added:

- `mbp pulse alignment-sensitivity`
- `mbp pulse missingness`
- `mbp pulse build-targets --direction mean|charge|discharge`
- `mbp baseline run-pulse --max-alignment-delta-s`
- `pulse_claim_readiness.md` rendering for PULSE baseline report directories

The baseline runner now emits a warning report instead of failing when a target
configuration has no finite target rows. This is used for the diagnostic
discharge-only RT/50 target table.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse alignment-sensitivity \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/pulse_alignment_sensitivity_report.json \
  --coverage-out reports/audit/pulse_alignment_sensitivity_coverage.csv

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse missingness \
  --pulse-targets data/interim/pulse_target_table.parquet \
  --interval-table data/interim/interval_table.parquet \
  --missing-out reports/audit/pulse_missing_canonical_targets.csv \
  --by-condition-out reports/audit/pulse_missingness_by_condition.csv \
  --by-split-out reports/audit/pulse_missingness_by_split.csv

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse build-targets \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/pulse_target_table_mean.parquet \
  --soc-percent 50 \
  --temperature-context RT \
  --direction mean

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse build-targets \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/pulse_target_table_charge.parquet \
  --soc-percent 50 \
  --temperature-context RT \
  --direction charge

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp pulse build-targets \
  --pulse-summary data/interim/modality_table_pulse_summary.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/pulse_target_table_discharge.parquet \
  --soc-percent 50 \
  --temperature-context RT \
  --direction discharge
```

The PULSE resistance baseline was rerun for `mean`, `charge`, and `discharge`
target tables, plus alignment-threshold sensitivity at 24h and 36h.

## Outputs

```text
reports/audit/pulse_alignment_sensitivity_report.json
reports/audit/pulse_alignment_sensitivity_coverage.csv
reports/audit/pulse_missing_canonical_targets.csv
reports/audit/pulse_missingness_by_condition.csv
reports/audit/pulse_missingness_by_split.csv
reports/baselines/pulse_resistance_alignment_sensitivity/baseline_summary.md
reports/baselines/pulse_resistance_alignment_sensitivity/plots/pulse_alignment_threshold_comparison.csv
reports/baselines/pulse_resistance_l0_l3/pulse_resistance_direction_comparison.md
reports/baselines/pulse_resistance_l0_l3/plots/pulse_direction_comparison.csv
```

Generated target and prediction Parquets remain ignored.

## Alignment Findings

Canonical RT/50 alignment-threshold coverage:

| Threshold | Retained intervals | Missing intervals | Retained cells | C-rate rows | Profile rows |
|---|---:|---:|---:|---:|---:|
| `<=6h` | `3,131` | `696` | `220` | `90` | `605` |
| `<=12h` | `3,529` | `298` | `225` | `109` | `697` |
| `<=24h` | `3,748` | `79` | `228` | `143` | `733` |
| `<=36h` | `3,751` | `76` | `228` | `143` | `733` |
| `all` | `3,751` | `76` | `228` | `143` | `733` |

Canonical alignment deltas are less severe than the all-row PULSE QA aggregate:
the canonical RT/50 rows have median `13,455.5 s`, p95 approximately
`51,413 s`, and max `126,990 s`.

Baseline sensitivity:

| Threshold | Condition-fold best MAE | C-rate best MAE | Interpretation |
|---|---:|---:|---|
| `all` | `0.000960407` | `0.00185842` | Reference |
| `<=24h` | `0.000952007` | `0.00194971` | Slight C-rate degradation, full C-rate count retained |
| `<=36h` | `0.000960407` | `0.00185842` | Same as all rows for finite targets |

Decision: alignment filtering does not invalidate the first scalar PULSE
baseline, but it remains a required reporting sensitivity before any PULSE
claim.

## Direction Findings

Direction-specific extraction is diagnostic:

| Direction | Result |
|---|---|
| `mean` | Canonical target; baseline rows match the original 0.7 report. |
| `charge` | Same scalar baseline rows as `mean` for the current RT/50 table. |
| `discharge` | No finite adjacent RT/50 interval deltas; explicit warning report emitted. |

Decision: keep `mean` as the canonical direction handling. Do not promote
charge-only or discharge-only targets until a later target policy changes the
direction rule.

## Missingness Findings

The canonical target table has `76` missing interval endpoint rows:

- `62` outside the C-rate holdout and `14` inside it.
- `57` outside the profile holdout and `19` inside it.
- Missingness spans `34` parameter-set condition groups.

Decision: missing canonical endpoints are not a hard blocker for scalar
diagnostics, but they must remain visible in PULSE reports and claim-readiness
summaries.

## Validation

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check src/mbp/data/products/pulse_targets.py src/mbp/baselines/pulse.py src/mbp/cli.py tests/test_pulse_targets.py tests/test_pulse_baselines.py
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest tests/test_pulse_targets.py tests/test_pulse_baselines.py -q
8 passed
```

Full-suite validation is recorded in `docs/REPO_STATUS.md`.

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
99 passed
```

## Decision

Milestone 0.7.1 supports continuing to treat canonical RT/50 mean PULSE
resistance as a scalar diagnostic endpoint. It still does not authorize a PULSE
scientific claim, capacity+PULSE multimodal modeling, EIS modeling, sequence
models, neural models, policy ranking, or CBAT.
