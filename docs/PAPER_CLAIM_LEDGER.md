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
| C09 | Quantile HGB uncertainty is calibrated. | `not_supported` | q10-q90 coverage close to nominal 0.8 across grouped splits. | Mean q10-q90 coverage is about `0.678207`. | Quantile metrics are diagnostics only until calibration is explicitly tested. | HGB quantile intervals are calibrated uncertainty estimates. | `reports/baselines/capacity_hgb50_focused/claim_readiness.md` |
| C10 | EIS improves anything. | `gated` | EIS QA, valid-frequency masks, and grouped predictive evidence. | Milestone 2.0 EIS QA and feature-readiness artifacts now exist, but grouped predictive tests are still pending and EIS improvement claims remain blocked. | EIS is a gated modality with QA and feature-readiness artifacts, but no predictive claim yet. | EIS improves degradation prediction. | `reports/audit/eis_claim_readiness.md` |
| C11 | CBAT architecture is justified. | `blocked` | Baselines, ablations, calibration, and simpler models must justify late-stage architecture work. | Current work is baseline-first evidence synthesis; architecture work remains blocked. | CBAT remains a reserved late-stage architecture label. | CBAT is justified by current evidence. | `docs/PROJECT_CHARTER.md` |
| C12 | Grouped validation is required for publishable evidence. | `supported` | Replicate-aware parameter-set grouping and OOD split reports. | Headline reports use condition/stressor grouped splits; random row/cell splits remain non-publishable. | Claims must be grounded in grouped validation and condition-level summaries. | Random row or cell splits are publishable headline evidence. | `docs/VALIDATION_PROTOCOL.md` |

## Locked Wording

Use:

> The current benchmark supports a conservative story: grouped HGB baselines
> reveal C-rate as the hardest capacity transfer, scalar LOG_AGE and stress
> features help some views but do not solve C-rate fade prediction, RT/50 PULSE
> is a usable scalar resistance endpoint, PULSE growth explains capacity-model
> residuals, and prior PULSE state improves capacity-level prediction over F4 in
> selected splits without beating the strongest supplied non-PULSE baseline.

Do not use:

> The multimodal model solves battery degradation prediction.

> Prior PULSE improves fade-rate prediction.

> CBAT is validated.

> EIS improves capacity prediction.
