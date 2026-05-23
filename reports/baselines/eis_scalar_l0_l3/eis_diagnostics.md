# EIS Diagnostics

Prior EIS `k` features are allowed for scalar EIS endpoints. Future EIS `k1`, EIS deltas, DRT, embeddings, and R0/R1 without leakage-safe provenance are blocked as non-EIS inputs.

| Target | Split | Model | Feature group | Condition mean MAE | Worst condition MAE |
|---|---|---|---|---:|---:|
| `delta_eis_z_abs_1kHz` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `E2_state_capacity` | 0.000369837 | 0.000913275 |
| `delta_nyquist_semicircle_width_proxy` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `E2_state_capacity` | 0.000448016 | 0.000756289 |
| `eis_z_abs_1kHz_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `E2_state_capacity` | 0.000412968 | 0.00105414 |
| `nyquist_semicircle_width_proxy_k1` | `profile_holdout_fold` | `L2_hist_gradient_boosting` | `E2_state_capacity` | 0.000494169 | 0.000765897 |
