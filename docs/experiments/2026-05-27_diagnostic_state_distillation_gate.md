# Milestone 8.1 - Non-Neural Diagnostic-State Distillation Gate

Date: 2026-05-27

## Question

This gate tests charter Q2/H3 without opening a capacity+PULSE+EIS architecture
branch:

> Can current PULSE/EIS scalar diagnostic state be predicted from check-up-k
> capacity/state/time/nominal fields, and do those predicted diagnostic-state
> features improve downstream capacity-horizon or 80% threshold-warning
> forecasts under grouped validation?

This is not CBAT, not a neural/sequence model, not policy ranking, and not a
calibrated-risk or causal claim.

## Command

```bash
mbp baseline run-diagnostic-state-distillation \
  --capacity-horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --threshold-warning-table data/interim/threshold_warning_table_v1.parquet \
  --pulse-target-table data/interim/pulse_target_table.parquet \
  --eis-target-table data/interim/eis_target_table_v1.parquet \
  --out reports/baselines/diagnostic_state_distillation_report.json \
  --predictions-out data/processed/diagnostic_state_distillation_predictions.parquet \
  --out-dir reports/baselines/diagnostic_state_distillation \
  --hgb-max-iter 50 \
  --auxiliary-model-level A0_ridge
```

The prediction Parquet is a local generated artifact and must remain ignored.

## Method

Stage A fits leakage-safe auxiliary diagnostic-state surrogates:

- PULSE targets: `pulse_1s_resistance_k`, `pulse_10ms_resistance_k`
- EIS targets: `eis_z_abs_1kHz_k`, `eis_phase_1kHz_k`,
  `nyquist_im_peak_abs_k`, `nyquist_semicircle_width_proxy_k`
- training rows use inner grouped out-of-fold predictions inside each
  outer-training partition;
- held-out rows use models fit only on the corresponding outer-training rows.

Stage B compares downstream non-neural baselines:

- `D0_capacity_state_reference`
- `D1_predicted_pulse_state`
- `D2_predicted_eis_state`
- `D3_predicted_pulse_eis_state`

Downstream features may use check-up-k capacity/state/time/nominal fields plus
predicted diagnostic-state features only. True PULSE/EIS values, future
PULSE/EIS values, diagnostic deltas, future interval exposure, target values,
detector-knee labels, policy contrast labels, and K3 oracle exposure fields are
forbidden.

## Outputs

- `reports/baselines/diagnostic_state_distillation_report.json`
- `reports/baselines/diagnostic_state_distillation/diagnostic_state_distillation_summary.md`
- `reports/baselines/diagnostic_state_distillation/diagnostic_state_distillation_claim_readiness.md`
- `reports/baselines/diagnostic_state_distillation/leaderboard.csv`
- `reports/baselines/diagnostic_state_distillation/plots/auxiliary_target_accuracy.csv`
- `reports/baselines/diagnostic_state_distillation/plots/diagnostic_state_downstream_gains.csv`
- `reports/baselines/diagnostic_state_distillation/plots/c_rate_diagnostic_state_gains.csv`
- `reports/baselines/diagnostic_state_distillation/plots/stage_a_prediction_modes.csv`

## Results

Auxiliary diagnostic-state surrogates are learnable:

- `12` of `12` auxiliary leaderboard rows beat train-mean baselines.
- The strongest relative auxiliary gains are for PULSE resistance and
  Nyquist-width proxy targets.

Downstream diagnostic-state value does not pass:

- Best all-split D3 capacity primary relative gain: `-0.00790693`
- All-split threshold-warning D3 relative Brier gain: `-0.0620807`
- C-rate threshold-warning D3 relative Brier gain: `-0.0740460`
- C-rate `delta_capacity_Ah_h` horizon 3 has an isolated positive D3 gain
  (`0.0724454`), but horizon 2 is negative and the C-rate non-collapse rule
  fails overall.

The claim-readiness report marks:

- diagnostic-state distillation: `not_supported`
- auxiliary surrogate prediction: `supported_for_diagnostics`
- capacity-horizon gain: `not_supported`
- threshold-warning gain: `not_supported`
- C-rate non-collapse: `not_supported`
- leakage audit: `passed`
- CBAT architecture: `blocked`
- neural or sequence models: `blocked`
- policy ranking: `blocked`
- calibrated risk or uncertainty: `blocked`

## Decision

PULSE/EIS current diagnostic-state surrogates can be predicted from prior
state and nominal metadata, but those predicted surrogate states do not improve
downstream capacity-horizon or threshold-warning baselines enough to support a
multimodal-state or architecture claim.

Allowed wording:

> PULSE/EIS diagnostic-state surrogates are learnable under grouped validation,
> but predicted diagnostic-state features do not currently improve downstream
> capacity-horizon or threshold-warning baselines enough for a multimodal-state
> claim.

Forbidden wording:

- capacity+PULSE+EIS architecture is validated;
- CBAT is justified;
- broad multimodal state learning is supported;
- calibrated risk or calibrated uncertainty is supported;
- policy ranking is authorized;
- causal or same-cell counterfactual claims are supported;
- sequence or neural branches are reopened.

## Next Action

Close the broad diagnostic-state distillation branch as a negative gate. Keep
PULSE and EIS as auxiliary diagnostic endpoints. Any future ML work should be a
new predeclared charter question, not an architecture expansion from this
result.
