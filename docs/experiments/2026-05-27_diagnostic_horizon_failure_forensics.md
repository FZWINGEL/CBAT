# Milestone 8.2.1 - Diagnostic-Horizon Failure Forensics

Date: 2026-05-27

## Scope

This milestone explains the partial Milestone 8.2 diagnostic endpoint
forecasting result using existing artifacts only:

- `reports/baselines/diagnostic_horizon_l0_l2_report.json`
- `data/processed/diagnostic_horizon_l0_l2_predictions.parquet`
- `data/interim/diagnostic_horizon_table_v1.parquet`

No models were retrained, no feature groups were added, and no generated
Parquet data product is committed.

## Command

```bash
mbp baseline diagnose-diagnostic-horizon \
  --report reports/baselines/diagnostic_horizon_l0_l2_report.json \
  --predictions data/processed/diagnostic_horizon_l0_l2_predictions.parquet \
  --diagnostic-horizon-table data/interim/diagnostic_horizon_table_v1.parquet \
  --out-dir reports/baselines/diagnostic_horizon_l0_l2
```

## Outputs

- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_forensics_report.json`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_forensics.md`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_endpoint_claim_readiness.md`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/endpoint_reference_failure_matrix.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/target_horizon_gain_matrix.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/c_rate_endpoint_failure_matrix.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/persistence_ceiling_diagnostics.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/condition_error_hotspots.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/diagnostic_horizon_endpoint_claim_readiness.csv`

## Result

The overall Milestone 8.2 gate remains partial:

- primary horizon-2/3 10% gain rows passing: `21/24`;
- C-rate non-collapse rows passing: `22/24`;
- endpoint-reference forensics rows rendered: `432`;
- C-rate endpoint failure rows rendered: `72`.

Endpoint-specific readiness is narrower:

| Endpoint | Status | Reason |
|---|---|---|
| `eis_z_abs_1kHz` | `supported_for_diagnostics` | `4/4` primary rows and `4/4` C-rate rows pass. |
| `nyquist_semicircle_width_proxy` | `supported_for_diagnostics` | `4/4` primary rows and `4/4` C-rate rows pass. |
| `pulse_10ms_resistance` | `supported_for_diagnostics` | `4/4` primary rows and `4/4` C-rate rows pass. |
| `eis_phase_1kHz` | `partially_supported` | `3/4` primary rows pass; C-rate rows pass. |
| `nyquist_im_peak_abs` | `partially_supported` | `2/4` primary rows pass; C-rate rows pass. |
| `pulse_1s_resistance` | `partially_supported` | Primary rows pass, but only `2/4` C-rate rows avoid negative gain. |

The weakest primary rows are `nyquist_im_peak_abs` versus persistence at
horizons 2 and 3 and `eis_phase_1kHz` versus persistence at horizon 2. The
weakest C-rate rows are `pulse_1s_resistance` versus the capacity-state
reference at horizons 2 and 3.

## Decision

Allowed wording:

> Selected scalar PULSE/EIS endpoints can be forecast diagnostically from
> check-up-k state and current same-diagnostic state under grouped validation.

Forbidden wording:

- broad diagnostic endpoint forecasting is solved globally;
- capacity+PULSE+EIS architecture is justified;
- CBAT is ready;
- endpoint forecasts are calibrated risk or calibrated uncertainty;
- policy ranking is authorized;
- causal or same-cell counterfactual claims are supported.

The next default step remains synthesis/release maintenance unless a new
predeclared narrow ML gate is opened for a charter question.
