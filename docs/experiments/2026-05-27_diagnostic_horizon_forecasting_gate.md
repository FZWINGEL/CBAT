# Milestone 8.2 - Diagnostic Horizon Forecasting Gate

## Purpose

Milestone 8.2 tests whether future PULSE/EIS scalar diagnostic endpoints are
forecastable over 1/2/3/5-check-up horizons using only check-up-k state,
nominal metadata, and current same-diagnostic state. This is a diagnostic
endpoint forecasting gate, not CBAT, not a capacity+PULSE+EIS architecture
test, and not calibrated-risk or policy work.

## Commands

```bash
mbp analysis build-diagnostic-horizon-table \
  --interval-table data/interim/interval_table.parquet \
  --pulse-target-table data/interim/pulse_target_table.parquet \
  --eis-target-table data/interim/eis_target_table_v1.parquet \
  --out data/interim/diagnostic_horizon_table_v1.parquet

mbp analysis diagnostic-horizon-qa \
  --diagnostic-horizon-table data/interim/diagnostic_horizon_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/analysis/diagnostic_horizon/diagnostic_horizon_qa_report.json \
  --coverage-out reports/analysis/diagnostic_horizon/diagnostic_horizon_coverage.csv

mbp baseline run-diagnostic-horizon \
  --diagnostic-horizon-table data/interim/diagnostic_horizon_table_v1.parquet \
  --out reports/baselines/diagnostic_horizon_l0_l2_report.json \
  --predictions-out data/processed/diagnostic_horizon_l0_l2_predictions.parquet \
  --out-dir reports/baselines/diagnostic_horizon_l0_l2 \
  --hgb-max-iter 50
```

## Artifacts

- `data/interim/diagnostic_horizon_table_v1.parquet` (ignored)
- `data/processed/diagnostic_horizon_l0_l2_predictions.parquet` (ignored)
- `reports/analysis/diagnostic_horizon/diagnostic_horizon_qa_report.json`
- `reports/analysis/diagnostic_horizon/diagnostic_horizon_coverage.csv`
- `reports/baselines/diagnostic_horizon_l0_l2_report.json`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_claim_readiness.md`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_summary.md`
- `reports/baselines/diagnostic_horizon_l0_l2/leaderboard.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/diagnostic_horizon_reference_gains.csv`

## Result

The diagnostic-horizon table QA passed:

- rows: `80,878`
- cells: `228`
- parameter sets: `76`
- targets: `6`
- horizons: `1, 2, 3, 5`
- leakage columns: none

The grouped baseline run generated:

- metric rows: `2,880`
- prediction rows: `2,176,320`

DH3 HGB with capacity plus current same-diagnostic state is useful in many
rows, but the strict claim gate does not fully pass:

- primary horizon-2/3 rows passing the 10% gain rule: `21/24`
- C-rate horizon-2/3 rows with non-negative gain: `22/24`
- best primary relative gain: `0.465846087624688`
- minimum primary relative gain: `-0.14707080358918656`
- best C-rate relative gain: `0.5218213829914101`
- minimum C-rate gain: `-5.13632984596858e-05`

## Decision

Milestone 8.2 is `partially_supported`.

Allowed wording:

> Future PULSE/EIS scalar diagnostic endpoints are forecastable in many grouped
> rows using check-up-k state and current same-diagnostic state, but the broad
> diagnostic endpoint forecasting gate does not fully pass.

Forbidden wording:

- diagnostic endpoint forecasting is solved globally;
- capacity+PULSE+EIS architecture is justified;
- CBAT is ready;
- calibrated risk or calibrated uncertainty is supported;
- policy ranking is authorized;
- sequence/neural branches are justified;
- causal or same-cell counterfactual claims are supported.

## Next Action

Keep this as partial diagnostic endpoint evidence. Do not open architecture,
CBAT, policy, causal, calibrated-risk, or broad multimodal branches from this
gate. Further work would need a fresh, predeclared narrow question.
