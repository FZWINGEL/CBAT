# Evidence Matrix

Milestone 1.0 consolidates completed evidence. It does not add new model
training, feature engineering, EIS modeling, neural modeling, policy ranking, or
CBAT work.

| Area | Status | Primary evidence | Interpretation |
|---|---|---|---|
| Data products | supported | LOG_AGE table has 904,977,105 rows; interval table has 3,827 rows; split and subset registries exist. | The project has a reproducible interval spine for grouped baseline evidence. |
| LOG_AGE monotonicity policy | supported | `baseline_clean_tolerant` has 3,827 intervals; `baseline_clean_strict` has 2,773; 1,054 intervals are sensitivity-flagged. | Tiny EFC jitter is tolerated for primary baselines with strict sensitivity retained. |
| Capacity baseline ladder | supported | HGB-50 F4 improves over L0 across target/split views; C-rate remains hardest. | Scalar capacity baselines are strong enough for benchmark reporting. |
| State-aware capacity baselines | supported | `F1_state_time` and later groups include `capacity_Ah_k`; weak `F0_time_only` is deliberately retained as sanity check. | Prior capacity state is necessary for fair forecasting baselines. |
| Nominal protocol features | supported | `F2_state_exposure -> F3_state_nominal` mean gain is 0.008439 with 19/20 positive rows. | Nominal temperature, C-rate, voltage window, and aging mode remain important. |
| LOG_AGE scalar summaries | partially_supported | `F3_state_nominal -> F4_state_log_age_scalar` is mixed: mean gain 0.000085, positive rows 10/20. | Current scalar LOG_AGE summaries help nonlinear models in some views, but gains are mixed and do not justify broad exposure claims. |
| LOG_AGE stress features | not_supported_for_c_rate_delta | v1.1 C-rate `capacity_Ah_k1` improves to 0.120605, but C-rate `delta_capacity_Ah` remains worse than F4 at 0.102516 vs 0.101133. | Stress features are useful diagnostics but do not solve fade-rate transfer. |
| C-rate capacity failure | supported | Best F4 C-rate MAE is 0.125186 for `capacity_Ah_k1` and 0.101133 for `delta_capacity_Ah`; worst rows cluster in cold/cool high-C-rate conditions. | C-rate holdout is the central unresolved generalization regime. |
| PULSE target robustness | supported_for_scalar_diagnostics | RT/50 canonical target is robust enough for scalar diagnostics; `delta_pulse_10ms_resistance` is viable secondary. | PULSE can be reported as a scalar resistance endpoint, with missingness and alignment sensitivity disclosed. |
| PULSE resistance baseline | supported_for_scalar_diagnostics | `delta_pulse_1s_resistance` best condition-fold MAE is 0.000960407; best C-rate MAE is 0.00185842. | PULSE resistance growth is predictable enough for baseline diagnostics. |
| Capacity-PULSE coupling | supported_for_explanatory_diagnostics | C-rate interval correlations between absolute capacity residuals and PULSE growth remain positive after canonical-model filtering. | PULSE growth explains where capacity-only models struggle, especially C-rate, but is not causal evidence. |
| Prior PULSE over F4 | supported_for_selected_splits | `capacity_Ah_k1` gains vs F4 are 0.00669208 C-rate, 0.00509620 temperature, and 0.0214905 profile. | Prior PULSE state helps capacity-level prediction over F4 in selected OOD splits. |
| Prior PULSE vs strongest non-PULSE | not_supported | C-rate `capacity_Ah_k1` gain is 0.000392605 with p05 -0.00553843; temperature/profile mean gains are negative. | Prior PULSE is not the strongest available non-neural capacity feature path. |
| Prior PULSE for fade rate | not_supported | C-rate `delta_capacity_Ah` gain vs strongest non-PULSE is -0.00234428. | Fade-rate prediction remains unresolved. |
| Quantile uncertainty | not_supported | q10-q90 coverage is about 0.678207 versus nominal 0.8. | Quantile rows are diagnostics only, not calibrated uncertainty claims. |
| EIS | gated | EIS ingestion coverage exists, but valid-frequency masks and EIS QA remain pending for any EIS claim. | EIS QA may be a future gated path; EIS modeling is not authorized. |
| CBAT | blocked | The charter reserves CBAT for late-stage models after data products, baselines, splits, ablations, and calibration are stable. | CBAT architecture is not justified by the current evidence state. |
