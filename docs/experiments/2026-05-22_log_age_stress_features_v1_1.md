# 2026-05-22 LOG_AGE Stress Features v1.1

## Scope

Milestone 0.6.1 hardens the Milestone 0.6 stress-feature sidecar before any
scope expansion. The work remains capacity-only, scalar-interval only, and
LOG_AGE-derived only. EIS/PULSE modeling, knee prediction, sequence models,
neural models, policy ranking, and CBAT remain blocked.

## Motivation

The v1 stress-feature result was mixed:

| Target | F4 HGB-50 baseline | v1 best stress row | Result |
|---|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` | marginal pass |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` | fail |

The main v1 weaknesses were:

- dwell features were count-weighted by row count rather than timestamp-weighted;
- current sign convention was provisional;
- no scalar event features represented continuous high-stress bursts;
- target-derived normalized-rate diagnostics had to remain excluded from
  predictive feature groups.

## Implementation

Added:

```text
src/mbp/data/products/current_sign_audit.py
mbp features current-sign-audit
```

The audit streams LOG_AGE row groups, computes voltage/SOC derivatives by
current sign, and writes:

```text
reports/audit/current_sign_audit_report.json
```

Updated:

```text
src/mbp/data/products/stress_features.py
```

The stress-feature builder now emits schema version
`gate6.interval_stress_features.v1_1` and feature policy
`log_age_stress_features.v1_1_timestamp_event`.

New v1.1 fields:

- `stress_observed_duration_h`
- `stress_coverage_fraction`
- `median_log_age_dt_s`
- `max_log_age_gap_s`
- `log_age_gap_count_gt_60s`
- `log_age_gap_count_gt_300s`
- charge/discharge/rest event counts and max event durations
- max high-current and coupled-stress event durations

Added feature groups:

- `F8_timestamp_weighted_stress`
- `F9_event_segmented_stress`
- `F10_c_rate_v1_1`

Target-derived diagnostics remain excluded from F5-F10:

- `delta_capacity_per_day`
- `delta_capacity_per_efc`
- `delta_capacity_per_Ah_throughput`

## Commands

Current-sign audit:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp features current-sign-audit \
  --log-age data/interim/modality_table_log_age.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/current_sign_audit_report.json
```

Build v1.1 sidecar:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp features build-stress \
  --interim-dir data/interim \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/interval_stress_features_v1_1.parquet \
  --current-sign-report reports/audit/current_sign_audit_report.json
```

QA:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp features stress-qa \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/stress_feature_v1_1_qa_report.json
```

Focused baseline:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
UV_CACHE_DIR=/tmp/uv-cache timeout 7200s .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1_1.parquet \
  --out reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --predictions-out data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting,L3_quantile_hist_gradient_boosting \
  --feature-groups F4_state_log_age_scalar,F5_log_age_histograms,F6_coupled_stress,F7_c_rate_focused,F8_timestamp_weighted_stress,F9_event_segmented_stress,F10_c_rate_v1_1 \
  --split-views c_rate_holdout_fold,condition_fold,temperature_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50
```

Diagnostics:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-stress-features \
  --report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --baseline-report reports/baselines/capacity_hgb50_focused_report.json \
  --l0-reference-report reports/baselines/capacity_l0_l3_report.json \
  --out-dir reports/baselines/capacity_stress_features_v1_1_hgb50
```

## Real-Data Run

Current-sign audit:

- Report: `reports/audit/current_sign_audit_report.json`
- Row groups sampled: `5,000`, evenly across the LOG_AGE Parquet.
- Evidence rows:
  - positive current: `5,516,237`
  - negative current: `5,909,947`
- Result: `positive_current_charge`
- Confidence: `high`

Key derivative evidence:

| Statistic | Positive current | Negative current |
|---|---:|---:|
| Median dSOC/dt | `0.010000` | `-0.005000` |
| Median dV/dt | `0.000100` | `-0.000650` |

Sidecar build:

- Output: `data/interim/interval_stress_features_v1_1.parquet`
- Rows: `3,827`
- Schema version: `gate6.interval_stress_features.v1_1`
- Feature policy: `log_age_stress_features.v1_1_timestamp_event`
- Current sign policy: `positive_current_charge_confirmed`
- Sign-dependent features provisional: `False`

QA:

- Report: `reports/audit/stress_feature_v1_1_qa_report.json`
- Status: passed.
- Missing interval keys: `0`
- Voltage/temperature/SOC/current dwell failures against observed duration: `0`
- Negative feature counts: none.
- Features exceeding duration: none.

Focused baseline:

- Report: `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- Metrics: `616`
- Feature groups: `F4` through `F10`
- Models: `L2_hist_gradient_boosting`, `L3_quantile_hist_gradient_boosting`
- Splits: C-rate, condition, temperature, voltage-window.

Diagnostics:

- Directory: `reports/baselines/capacity_stress_features_v1_1_hgb50/`
- Stress diagnostics:
  `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

## Result

Success criterion:

| Target | F4 HGB-50 baseline | v1 best stress row | v1.1 best stress row | v1.1 gain vs F4 | Result |
|---|---:|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` | `0.120605` (`F5_log_age_histograms`) | `0.004581` | improved, but below 0.005 materiality threshold |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` | `0.102516` (`F8_timestamp_weighted_stress`) | `-0.001383` | fail |

Other split checks:

- `capacity_Ah_k1` condition-fold improved slightly versus F4:
  `0.053927 -> 0.052930`.
- `capacity_Ah_k1` temperature-holdout improved:
  `0.069294 -> 0.064116`.
- `delta_capacity_Ah` condition-fold improved:
  `0.044645 -> 0.041700`.
- `delta_capacity_Ah` temperature-holdout improved slightly:
  `0.048575 -> 0.048072`.
- `capacity_Ah_k1` voltage-window holdout degraded versus F4:
  `0.084413 -> 0.093799`.

## Decision

Milestone 0.6.1 is a useful hardening result, but it still does **not** support
a broad claim that LOG_AGE stress features improve C-rate generalization.

Interpretation:

- Current-sign convention is now high-confidence positive-current charge for the
  sampled LOG_AGE evidence.
- Timestamp-weighted dwell and event features improved the v1 C-rate
  `delta_capacity_Ah` failure substantially (`0.110260 -> 0.102516`) but did not
  beat the F4 baseline (`0.101133`).
- `capacity_Ah_k1` C-rate improved over both F4 and v1, but the absolute gain
  versus F4 is `0.004581`, just below the suggested materiality threshold.
- Condition and temperature splits remain stable or improved.
- Voltage-window transfer should be watched because v1.1 degraded
  `capacity_Ah_k1` there.

PULSE/EIS/CBAT remain blocked. The next decision should be whether to stop
stress-feature expansion and inspect target formulation / C-rate failure modes,
or to do one very narrow v1.2 pass focused only on C-rate `delta_capacity_Ah`
and voltage-window degradation.

## Validation

Synthetic tests cover:

- current-sign audit on a trace with positive-current charging evidence;
- timestamp-weighted dwell differing from count-weighted dwell under uneven
  timestamp gaps;
- dwell bins summing to observed duration;
- coverage fraction;
- event counts and max event durations;
- baseline sidecar joins;
- target-derived diagnostic exclusion from F5-F10.

Real-data validation run:

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
85 passed, 1 warning.
```
