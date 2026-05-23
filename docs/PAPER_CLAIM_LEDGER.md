# Paper Claim Ledger

This ledger is the Milestone 1.0 source of truth for paper-facing wording. It
separates supported claims from partial, negative, gated, and blocked claims.

Status values:

- `supported`
- `partially_supported`
- `supported_for_diagnostics`
- `supported_for_explanatory_diagnostics`
- `supported_for_selected_splits`
- `not_supported`
- `gated`
- `blocked`

| ID | Claim | Status | Required evidence | Actual evidence | Allowed wording | Forbidden wording | Source artifact |
|---|---|---|---|---|---|---|---|
| C01 | Current scalar LOG_AGE summaries help nonlinear models in some grouped views, but gains are mixed. | `partially_supported` | Grouped split gains beyond state/time and nominal protocol. | HGB F3 to F4 mean gain is `0.000085`, median `0.001124`, positive rows `10 / 20`; best focused HGB rows often use F4. | Current scalar LOG_AGE summaries help nonlinear models in some grouped views, but the effect is mixed. | LOG_AGE scalar summaries broadly solve operating-history generalization. | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` |
| C02 | LOG_AGE stress features solve C-rate fade prediction. | `not_supported` | C-rate `delta_capacity_Ah` below F4 threshold `0.101133` without degrading other folds. | v1.1 stress features improve capacity level to `0.120605`, but C-rate delta best stress row is `0.102516`, worse than F4. | Stress features are useful diagnostics and help some folds, but do not solve C-rate fade transfer. | LOG_AGE stress features solve C-rate fade prediction. | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` |
| C03 | C-rate holdout is the hardest capacity generalization view. | `supported` | C-rate remains worse than other split views under grouped validation. | Best focused HGB-50 C-rate MAE is `0.125186` for `capacity_Ah_k1` and `0.101133` for `delta_capacity_Ah`; worst rows cluster in cold/cool high-C-rate conditions. | C-rate holdout is the dominant unresolved capacity generalization stressor. | The baseline generalizes uniformly across stressor axes. | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` |
| C04 | PULSE RT/50 is usable as a scalar resistance endpoint. | `supported_for_diagnostics` | QA, target coverage, alignment sensitivity, direction policy, grouped resistance baselines. | Canonical RT/50 target passed scalar diagnostic robustness; `delta_pulse_1s_resistance` condition-fold MAE is `0.000960407`, C-rate MAE is `0.00185842`. | Canonical RT/50 PULSE is robust enough for scalar resistance-baseline diagnostics. | PULSE target robustness proves broad multimodal degradation modeling. | `docs/experiments/2026-05-23_pulse_target_robustness_decision.md` |
| C05 | PULSE growth explains capacity residuals. | `supported_for_explanatory_diagnostics` | Correlations survive canonical-model filtering and interval/condition aggregation. | C-rate interval absolute-residual correlations remain strong: Pearson `0.857653` for `capacity_Ah_k1`, `0.647125` for `delta_capacity_Ah`; residualization weakens but does not erase C-rate association. | PULSE growth is associated with capacity residual magnitude, especially in C-rate views. | PULSE growth is causal or independent of all confounding. | `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md` |
| C06 | Prior PULSE improves capacity-level prediction over F4. | `supported_for_selected_splits` | Paired grouped gains over F4 with bootstrap support. | `capacity_Ah_k1` gains vs F4: C-rate `0.00669208`, temperature `0.00509620`, profile `0.0214905`; p05 values are positive for those splits. | Prior PULSE state improves `capacity_Ah_k1` over F4 in selected grouped splits. | Prior PULSE improves all targets and all splits. | `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md` |
| C07 | Prior PULSE beats the strongest supplied non-PULSE capacity baseline. | `not_supported` | Prior-PULSE gains over strongest non-PULSE with p05 above zero in key splits. | C-rate `capacity_Ah_k1` gain is `0.000392605` with p05 `-0.00553843`; temperature and profile mean gains are negative. | Prior PULSE improves over F4, but not over the strongest supplied non-PULSE HGB baselines. | Prior PULSE is the strongest available non-neural capacity feature path. | `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md` |
| C08 | Prior PULSE improves `delta_capacity_Ah`. | `not_supported` | Positive paired gains for C-rate fade-rate prediction. | C-rate delta gain vs F4 is `-0.00574230`; gain vs strongest non-PULSE is `-0.00234428`. | `delta_capacity_Ah` remains an unresolved guardrail limitation. | Prior PULSE improves capacity fade-rate prediction. | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md` |
| C09 | Quantile HGB uncertainty is calibrated. | `not_supported` | q10-q90 coverage close to nominal 0.8 across grouped splits. | Milestone 2.3 raw HGB q10/q90 coverage remains under target: mean coverage `0.676677`, minimum split/fold coverage `0`, and C-rate coverage remains unacceptable. | Raw HGB quantile intervals are undercovered and remain diagnostics only. | HGB quantile intervals are calibrated uncertainty estimates. | `reports/analysis/calibration_capacity/calibration_claim_readiness.md` |
| C10 | EIS improves anything. | `partially_supported` | EIS QA, valid-frequency masks, grouped predictive evidence, strongest non-EIS comparisons, alignment sensitivity, and leakage audit. | Milestone 2.1.1 supports EIS as a scalar diagnostic endpoint and shows narrow profile-split prior-EIS gains for PULSE and `capacity_Ah_k1`, but C-rate capacity, C-rate PULSE, and `delta_capacity_Ah` remain unsupported. | EIS is a scalar diagnostic endpoint with narrow split-specific prior-feature signals; broad EIS improvement claims remain blocked. | EIS broadly improves degradation prediction. | `docs/experiments/2026-05-23_eis_claim_hardening.md` |
| C11 | CBAT architecture is justified. | `blocked` | Baselines, ablations, calibration, and simpler models must justify late-stage architecture work. | Current work is baseline-first evidence synthesis; architecture work remains blocked. | CBAT remains a reserved late-stage architecture label. | CBAT is justified by current evidence. | `docs/PROJECT_CHARTER.md` |
| C12 | Grouped validation is required for publishable evidence. | `supported` | Replicate-aware parameter-set grouping and OOD split reports. | Headline reports use condition/stressor grouped splits; random row/cell splits remain non-publishable. | Claims must be grounded in grouped validation and condition-level summaries. | Random row or cell splits are publishable headline evidence. | `docs/VALIDATION_PROTOCOL.md` |
| C13 | Semi-empirical stress baselines beat the strongest grouped HGB capacity baselines. | `not_supported` | Paired condition-level gains over HGB F4 and strongest stress-feature HGB baselines under grouped splits. | Milestone 2.2 semi-empirical ridge comparators are worse than HGB F4 and strongest stress-feature HGB in C-rate capacity/fade views; profile holdout shows only a limited gain against F4. | Semi-empirical stress comparators are useful domain baselines, but they do not beat the strongest supplied grouped HGB baselines in the current C-rate capacity/fade tests. | Semi-empirical stress models outperform the ML baselines. | `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md` |
| C14 | Replicate-aware diagnostics validate calibrated uncertainty. | `not_supported` | Prediction or tolerance intervals with demonstrated grouped coverage and calibration. | Milestone 2.2 quantifies condition-triplet spread and model error versus replicate spread, but the reports are diagnostic and do not validate calibrated uncertainty. | Replicate diagnostics quantify triplet variability and contextualize model error; calibrated uncertainty remains unproven. | Replicate-aware intervals are validated calibrated uncertainty estimates. | `reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md` |
| C15 | Grouped conformal calibration validates capacity uncertainty. | `not_supported` | Empirical coverage near nominal, acceptable condition-level coverage, and no C-rate collapse without test-residual leakage. | Milestone 2.3 conformal methods improve mean coverage, but C-rate coverage remains below target: stressor-family conformal C-rate coverage is `0.719745` for `capacity_Ah_k1` and `0.726115` for `delta_capacity_Ah`. | Grouped conformal calibration is partially useful diagnostically, but no global calibrated capacity-uncertainty claim is authorized. | Grouped conformal intervals validate calibrated capacity uncertainty across all stressor holdouts. | `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md` |
| C16 | Ordered LOG_AGE event structure justifies sequence models. | `not_supported` | Order-aware features beat aggregate event features, shuffled-order controls, and stress baselines under grouped validation. | Milestone 2.4 order-aware features have overall mean gain `-0.000575091` vs aggregate, `-0.000564409` vs shuffled controls, and `-0.000470028` vs timestamp-weighted stress; C-rate mean gain is `-0.00131991`. | Ordered event summaries are useful falsification diagnostics, but current evidence does not justify sequence models. | Temporal order adds robust predictive value and sequence models are justified. | `docs/experiments/2026-05-23_temporal_history_value_gate.md` |
| C17 | Knee labels are stable enough for knee prediction. | `not_supported` | Detector, x-axis, smoothing, and replicate-triplet stability pass before prediction. | Milestone 2.5 primary labels are valid for 189 / 228 cells and x-axis/smoothing median disagreement is 0 check-ups, but only 45 / 64 primary valid conditions are replicate-consistent within 2 check-ups. | Knee labels are useful exploratory diagnostics, but knee prediction remains blocked until replicate consistency improves or claim scope is narrowed. | Knee-risk prediction is authorized by current labels. | `docs/experiments/2026-05-23_knee_label_stability_gate.md` |
| C18 | Threshold-event labels are a more stable early-warning target family than detector knees. | `partially_supported` | Threshold events have better replicate consistency and usable condition coverage without being treated as prediction evidence. | Milestone 2.5.1 finds `capacity_below_80pct_initial` has replicate consistency within 2 check-ups of `0.897`, condition coverage `0.763`, and median event check-up `8`, compared with primary detector-knee consistency `0.703`. | Threshold-event labels are more stable than detector knees and may be considered for a later non-neural label baseline gate. | Threshold-event prediction is authorized, or threshold labels are validated early-warning targets. | `docs/experiments/2026-05-23_knee_threshold_label_forensics.md` |
| C19 | Non-neural baselines can forecast the 80% threshold event under grouped validation. | `supported_for_diagnostics` | A leakage-safe prospective warning table and grouped non-neural baselines beat event-rate priors and simple proximity baselines under all-row and verified-only censoring policies. | Milestone 2.6.2 uses only check-up-k state/nominal features. For `event_within_3_checkups`, all-row HGB W2 improves mean Brier from `0.145791` for the event-rate prior and `0.132711` for the best proximity baseline to `0.0655751`; verified-only HGB W2 improves from `0.178655` for the prior and `0.168492` for proximity to `0.090116`. C-rate verified-only Brier improves from `0.377495` for the prior and `0.327879` for proximity to `0.153370`. Calibration remains unsupported. | Non-neural baselines can forecast `capacity_below_80pct_initial` threshold events diagnostically under grouped validation, beyond simple proximity baselines and under verified-only sensitivity. | Calibrated risk, policy ranking, detector-knee prediction, or causal early-warning claims are authorized. | `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md` |

## Locked Wording

Use:

> The current benchmark supports a conservative story: grouped HGB baselines
> reveal C-rate as the hardest capacity transfer, scalar LOG_AGE and stress
> features help some views but do not solve C-rate fade prediction, RT/50 PULSE
> is a usable scalar resistance endpoint, PULSE growth explains capacity-model
> residuals, and prior PULSE state improves capacity-level prediction over F4 in
> selected splits without beating the strongest supplied non-PULSE baseline.
> EIS is a scalar diagnostic endpoint with narrow profile-split prior-feature
> signals, and semi-empirical stress comparators do not beat the strongest
> supplied grouped HGB baselines in the current C-rate capacity/fade tests.
> Grouped conformal calibration improves mean interval coverage, but C-rate
> coverage still fails, so calibrated uncertainty remains blocked. LOG_AGE
> event-order summaries do not beat aggregate or shuffled controls overall, so
> sequence models remain blocked. Knee-label diagnostics are exploratory
> because replicate consistency does not pass, so knee prediction remains
> blocked. Threshold-event labels, especially 80% capacity-relative crossing,
> are more replicate-consistent than detector knees. A non-neural
> threshold-event baseline can forecast the 80% threshold event diagnostically,
> including beyond simple proximity baselines and under verified-only
> censoring sensitivity, but calibrated risk, detector-knee prediction, causal
> early-warning claims, and policy ranking remain blocked.

Do not use:

> The multimodal model solves battery degradation prediction.

> Prior PULSE improves fade-rate prediction.

> CBAT is validated.

> EIS improves capacity prediction.

> Grouped conformal intervals validate calibrated uncertainty across all
> stressor holdouts.

> Sequence models are justified by temporal-order value.

> Knee-risk prediction is authorized by current labels.

> Threshold-event prediction is authorized by current labels.

> Threshold-event probabilities are calibrated risk estimates.
