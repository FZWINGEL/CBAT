# Milestone 2.3: Grouped Calibration And Replicate-Aware Uncertainty Gate

Date: 2026-05-23

## Scope

Milestone 2.3 evaluates whether existing grouped capacity baselines can support
calibrated, replicate-aware uncertainty claims. It uses existing focused HGB-50
capacity predictions and Milestone 2.2 replicate-spread diagnostics. It does not
add architecture, neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, or capacity+PULSE+EIS multimodal work.

## Command

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp analysis calibrate-capacity \
  --capacity-report reports/baselines/capacity_hgb50_focused_report.json \
  --capacity-predictions data/processed/capacity_hgb50_focused_predictions.parquet \
  --interval-table data/interim/interval_table.parquet \
  --replicate-spread reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv \
  --out-dir reports/analysis/calibration_capacity
```

The command uses existing prediction Parquet and replicate-spread CSV inputs.
It does not write prediction Parquets or train new models.

## Outputs

- `reports/analysis/calibration_capacity/calibration_report.json`
- `reports/analysis/calibration_capacity/coverage_by_split.csv`
- `reports/analysis/calibration_capacity/coverage_by_condition.csv`
- `reports/analysis/calibration_capacity/interval_width_summary.csv`
- `reports/analysis/calibration_capacity/c_rate_calibration_summary.md`
- `reports/analysis/calibration_capacity/calibration_claim_readiness.md`

## Methods

Four interval families were evaluated:

| Method | Description |
|---|---|
| `Q0_hgb_quantile_raw` | Existing HGB q10/q90 interval outputs. |
| `Q1_split_conformal_abs_residual` | Split-local conformal absolute-residual intervals using disjoint calibration parameter sets. |
| `Q2_stressor_family_conformal` | Cross-split stressor-family conformal fallback excluding test parameter sets. |
| `Q3_replicate_tolerance_hybrid` | Hybrid interval using the larger of conformal radius and calibration-set replicate-spread diagnostic radius. |

The conformal methods exclude test parameter sets from calibration residuals.
C-rate and profile views have only one non-zero held-out fold, so the
split-local Q1 method is insufficient there; Q2/Q3 provide cross-split
diagnostic fallback intervals while still excluding test parameter sets.

## Results

Claim-readiness summary:

| Claim area | Status | Evidence |
|---|---|---|
| Raw HGB quantiles calibrated | `not_supported` | Mean coverage `0.676677`; minimum split/fold coverage `0`; C-rate unacceptable. |
| Grouped conformal intervals calibrated | `partially_supported` | Mean coverage `0.885689`, but minimum coverage is `0.68709` and C-rate is not acceptable. |
| Stressor-family conformal intervals calibrated | `partially_supported` | Mean coverage `0.875736`, but minimum coverage is `0.614159` and C-rate is not acceptable. |
| Replicate-aware hybrid intervals useful | `partially_supported` | Mean coverage matches stressor-family conformal in this run; C-rate remains unacceptable. |
| C-rate coverage acceptable | `not_supported` | C-rate stressor-family/hybrid coverage is approximately `0.72`, below the nominal target. |
| `delta_capacity_Ah` coverage acceptable | `partially_supported` | Mean coverage improves, but C-rate remains below target. |
| Uncertainty claim readiness | `blocked` | No calibrated uncertainty claim is authorized. |

C-rate coverage:

| Method | Target | Coverage | Mean width | Calibration conditions |
|---|---|---:|---:|---:|
| `Q0_hgb_quantile_raw` | `capacity_Ah_k1` | 0.751592 | 0.298217 | 0 |
| `Q2_stressor_family_conformal` | `capacity_Ah_k1` | 0.719745 | 0.221049 | 64 |
| `Q3_replicate_tolerance_hybrid` | `capacity_Ah_k1` | 0.719745 | 0.221049 | 64 |
| `Q0_hgb_quantile_raw` | `delta_capacity_Ah` | 0.624204 | 0.225389 | 0 |
| `Q2_stressor_family_conformal` | `delta_capacity_Ah` | 0.726115 | 0.219931 | 64 |
| `Q3_replicate_tolerance_hybrid` | `delta_capacity_Ah` | 0.726115 | 0.219931 | 64 |

## Interpretation

Raw HGB quantile intervals remain undercovered and cannot be described as
calibrated uncertainty. Grouped conformal methods improve average coverage, but
the hard C-rate split still fails the coverage gate. The replicate-aware hybrid
is useful as a diagnostic comparison, but in this run it does not solve the
C-rate interval problem.

The safe claim is:

> Grouped conformal calibration improves mean interval coverage, but C-rate
> coverage remains below target, so calibrated capacity-uncertainty claims
> remain blocked.

## Validation

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
128 passed.

git diff --check
passed.
```

## Decision

Milestone 2.3 does not authorize calibrated uncertainty claims, policy ranking,
CBAT, neural models, sequence models, DRT, EIS embeddings, or
capacity+PULSE+EIS architecture work. The uncertainty path remains a
baseline-first diagnostic stream until C-rate and condition-level coverage pass
without test-residual leakage.
