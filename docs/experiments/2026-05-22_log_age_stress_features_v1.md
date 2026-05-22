# 2026-05-22 LOG_AGE Stress Features v1

## Scope

Milestone 0.6 tests whether physically motivated scalar LOG_AGE stress features
improve capacity-baseline generalization, especially C-rate holdout. The scope
remains capacity-only and scalar-interval only. No EIS/PULSE modeling, knee
prediction, sequence model, neural model, policy ranking, or CBAT work is
included.

## Implementation

Added a modular sidecar:

```text
data/interim/interval_stress_features_v1.parquet
```

The sidecar has one row per interval and joins by:

```text
cell_id
checkup_k
checkup_k_next
```

Implemented commands:

```bash
mbp features build-stress
mbp features stress-qa
mbp baseline run-capacity --stress-features ...
mbp baseline diagnose-stress-features
```

Stress-feature families:

- voltage dwell bins;
- temperature dwell bins;
- current / C-rate exposure bins;
- SOC dwell bins;
- coupled cold/current, high-voltage/current, and high-SOC/current features;
- diagnostic normalized-rate fields.

Important leakage decision:

`delta_capacity_per_day`, `delta_capacity_per_efc`, and
`delta_capacity_per_Ah_throughput` are written as diagnostics but excluded from
F5-F7 predictive feature groups because they directly encode the interval
capacity target.

Current-sign decision:

The feature policy is
`positive_current_charge_provisional_abs_current_primary`. Charge-specific
features are present but marked provisional because current sign convention is
not yet independently confirmed. Abs-current features are the safer primary
stress features.

## Commands

Build:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp features build-stress \
  --interim-dir data/interim \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/interval_stress_features_v1.parquet
```

QA:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp features stress-qa \
  --stress-features data/interim/interval_stress_features_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/stress_feature_qa_report.json
```

Focused baseline:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
UV_CACHE_DIR=/tmp/uv-cache timeout 7200s .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --stress-features data/interim/interval_stress_features_v1.parquet \
  --out reports/baselines/capacity_stress_features_hgb50_report.json \
  --predictions-out data/processed/capacity_stress_features_hgb50_predictions.parquet \
  --model-levels L2_hist_gradient_boosting,L3_quantile_hist_gradient_boosting \
  --feature-groups F3_state_nominal,F4_state_log_age_scalar,F5_log_age_histograms,F6_coupled_stress,F7_c_rate_focused \
  --split-views c_rate_holdout_fold,condition_fold,temperature_holdout_fold,voltage_window_holdout_fold \
  --hgb-max-iter 50
```

Diagnostics:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline diagnose-stress-features \
  --report reports/baselines/capacity_stress_features_hgb50_report.json \
  --baseline-report reports/baselines/capacity_hgb50_focused_report.json \
  --l0-reference-report reports/baselines/capacity_l0_l3_report.json \
  --out-dir reports/baselines/capacity_stress_features_hgb50
```

## QA Result

`reports/audit/stress_feature_qa_report.json` passed.

Key facts:

| Check | Value |
|---|---:|
| Rows | 3,827 |
| Unique cells | 228 |
| Unique parameter sets | 76 |
| Missing interval keys | 0 |
| Voltage dwell sum failures | 0 |
| Temperature dwell sum failures | 0 |
| SOC dwell sum failures | 0 |
| Current dwell sum failures | 0 |
| Negative nonnegative-feature counts | 0 |

## Baseline Result

The focused stress-feature HGB-50 run produced `440` metric rows.

Success criterion:

| Target | HGB-50 F4 baseline | Best stress row | Gain | Result |
|---|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | 0.125186 | 0.124656 (`F6_coupled_stress`) | 0.000530 | marginal pass |
| `delta_capacity_Ah` C-rate | 0.101133 | 0.110260 (`F5_log_age_histograms`) | -0.009128 | fail |

Condition and temperature folds did not materially degrade:

- `capacity_Ah_k1` condition-fold improved from `0.053927` to `0.050277`;
- `capacity_Ah_k1` temperature-holdout improved from `0.069294` to `0.063644`;
- `delta_capacity_Ah` condition-fold improved from `0.044645` to `0.041693`;
- `delta_capacity_Ah` temperature-holdout improved from `0.048575` to `0.044619`.

## Decision

Milestone 0.6 v1 is a useful negative/mixed result.

The v1 stress features do **not** support a broad claim that stress features
improve C-rate generalization. They marginally improve `capacity_Ah_k1` C-rate
but degrade `delta_capacity_Ah` C-rate relative to the HGB-50 F4 baseline.

Next work should harden stress features before expanding scope:

- confirm LOG_AGE current sign convention;
- audit whether count-weighted dwell is too coarse and should be event/time
  segmented;
- keep target-derived normalized-rate fields out of predictive feature groups;
- inspect why `delta_capacity_Ah` C-rate worsens even when condition and
  temperature folds improve.

PULSE/EIS/CBAT remain blocked.
