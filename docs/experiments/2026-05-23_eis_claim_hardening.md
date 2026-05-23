# Milestone 2.1.1 - EIS Claim Hardening and Alignment Sensitivity

Date: 2026-05-23

## Scope

Milestone 2.1.1 hardens the scalar EIS baseline opening before any EIS
predictive claim is strengthened. It compares prior-EIS feature groups against
the strongest supplied non-EIS baselines on the same EIS-covered prediction
population, bootstraps paired condition gains by `parameter_set`, quantifies
alignment and feature-completeness sensitivity, and audits leakage.

Still blocked:

- DRT features
- learned EIS embeddings
- EIS neural or sequence models
- future EIS state as capacity/PULSE input
- EIS deltas as capacity/PULSE input
- policy ranking
- CBAT
- capacity+PULSE+EIS multimodal models
- broad EIS improvement claims

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline compare-prior-eis-pulse \
  --non-eis-report reports/baselines/pulse_resistance_l0_l3_report.json \
  --stress-report reports/baselines/pulse_resistance_target_robustness_report.json \
  --prior-eis-report reports/baselines/pulse_with_prior_eis_hgb50_report.json \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --out-dir reports/baselines/pulse_prior_eis_vs_best_noneis

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline compare-prior-eis-capacity \
  --non-eis-reports reports/baselines/capacity_hgb50_focused_report.json,reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --prior-eis-report reports/baselines/capacity_with_prior_eis_hgb50_report.json \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --out-dir reports/baselines/capacity_prior_eis_vs_best_noneis

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline eis-hardening-sensitivity \
  --pulse-non-eis-report reports/baselines/pulse_resistance_l0_l3_report.json \
  --pulse-prior-eis-report reports/baselines/pulse_with_prior_eis_hgb50_report.json \
  --capacity-non-eis-reports reports/baselines/capacity_hgb50_focused_report.json,reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --capacity-prior-eis-report reports/baselines/capacity_with_prior_eis_hgb50_report.json \
  --eis-targets data/interim/eis_target_table_v1.parquet \
  --alignment-out-dir reports/baselines/eis_alignment_sensitivity \
  --feature-completeness-out reports/baselines/eis_feature_completeness_sensitivity.csv \
  --feature-completeness-md reports/baselines/eis_feature_completeness_claim_readiness.md

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline eis-claim-readiness \
  --eis-report reports/baselines/eis_scalar_l0_l3_report.json \
  --self-endpoint-out reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md \
  --leakage-out reports/baselines/eis_leakage_audit.md
```

## Outputs

- `reports/baselines/pulse_prior_eis_vs_best_noneis/`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/`
- `reports/baselines/eis_alignment_sensitivity/`
- `reports/baselines/eis_feature_completeness_sensitivity.csv`
- `reports/baselines/eis_feature_completeness_claim_readiness.md`
- `reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md`
- `reports/baselines/eis_leakage_audit.md`

Generated prediction Parquets and `data/interim/eis_target_table_v1.parquet`
remain ignored data artifacts and are not committed.

## Results

### EIS self-endpoint

EIS scalar endpoints remain supported for diagnostics. HGB improves over
persistence for 12 target/split rows in
`reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md`,
including C-rate and condition-fold rows for `delta_eis_z_abs_1kHz` and
`delta_nyquist_semicircle_width_proxy`.

This is an EIS self-diagnostic statement only. It does not authorize EIS as an
input-improvement claim for capacity or PULSE.

### Prior EIS to PULSE

The prior-EIS PULSE comparison produced 214 paired condition rows.

Key `delta_pulse_1s_resistance` rows:

| Split | Prior-EIS group | Non-EIS group | Mean gain | Bootstrap p05 | Decision |
|---|---|---|---:|---:|---|
| C-rate | `P_E1_nominal_eis` | `P3_state_nominal` | -0.0000939 | -0.000186 | Not supported |
| Profile | `P_E1_nominal_eis` | `P3_state_nominal` | 0.0000307 | 0.00000128 | Narrow split-specific diagnostic |
| Temperature | `P_E3_stress_eis` | `P5_stress_v1_1` | 0.0000247 | -0.0000147 | Not bootstrap-supported |

Prior EIS does not improve PULSE C-rate resistance prediction over the
strongest supplied non-EIS PULSE baseline.

### Prior EIS to capacity

The prior-EIS capacity comparison produced 428 paired condition rows.

Key rows:

| Target | Split | Prior-EIS group | Non-EIS group | Mean gain | Bootstrap p05 | Decision |
|---|---|---|---|---:|---:|---|
| `capacity_Ah_k1` | C-rate | `C_E2_log_age_eis` | `F5_log_age_histograms` | -0.00528 | -0.01394 | Not supported |
| `capacity_Ah_k1` | Profile | `C_E0_state_time_eis` | `F1_state_time` | 0.00677 | 0.00384 | Narrow split-specific diagnostic |
| `capacity_Ah_k1` | Temperature | `C_E3_stress_eis` | `F6_coupled_stress` | -0.000417 | -0.00334 | Not supported |
| `delta_capacity_Ah` | C-rate | `C_E3_stress_eis` | `F4_state_log_age_scalar` | 0.00339 | -0.00894 | Not supported |

Prior EIS does not beat strongest supplied non-EIS baselines for C-rate capacity
level prediction and does not support a C-rate fade-rate claim.

### Alignment sensitivity

Alignment-threshold summaries were written for all finite rows, `<=24h`, and
`<=36h`.

The `<=24h` filter retains:

- 3,752 eligible interval keys
- all 76 parameter sets
- 143 C-rate rows in the EIS target table
- 733 profile rows in the EIS target table

The prior-EIS conclusions do not become broad EIS claims under alignment
filtering. Profile rows remain the only clearly positive split-specific signal;
C-rate remains unsupported.

### Feature-completeness sensitivity

Feature-completeness summaries compare:

- all RT/50 rows
- complete selected-frequency rows only
- `valid_modeling_fraction > 0`
- `valid_modeling_fraction >= 0.7`

Complete selected-frequency filtering retains 3,821 eligible interval keys and
does not change the qualitative claim posture.

### Leakage audit

`reports/baselines/eis_leakage_audit.md` passes. Capacity and PULSE prior-EIS
feature groups use prior EIS `k` scalar fields only. Future EIS `k1`, EIS
deltas, R0/R1 without leakage-safe provenance, DRT fields, and learned
embeddings are absent.

## Decision

EIS is supported as a scalar diagnostic endpoint.

Prior EIS has narrow split-specific diagnostic value:

- PULSE profile holdout shows bootstrap-supported improvement over strongest
  supplied non-EIS PULSE groups.
- Capacity profile holdout shows bootstrap-supported improvement for
  `capacity_Ah_k1`.

The following claims remain blocked:

- prior EIS improves C-rate capacity level prediction;
- prior EIS improves `delta_capacity_Ah`;
- EIS improves capacity or PULSE broadly;
- EIS justifies capacity+PULSE+EIS multimodal modeling;
- DRT, embeddings, neural models, sequence models, policy ranking, or CBAT.

## Validation

Validation commands run for this milestone:

```text
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
All checks passed.

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest tests/test_eis_features.py -p no:cacheprovider
9 passed

UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
123 passed
```
