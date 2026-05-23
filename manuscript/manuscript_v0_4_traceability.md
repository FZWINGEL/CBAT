# Manuscript v0.4 Traceability

This sidecar preserves the claim, figure/table, source artifact, allowed wording, and forbidden wording mappings that were removed from the reader-facing v0.4 body.

| Manuscript section | Claim ID | Figure/table | Source artifact | Allowed wording | Forbidden wording |
|---|---|---|---|---|---|
| Abstract | C01 | Figure 5 | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` | Scalar LOG_AGE summaries help nonlinear models in some views, but gains are mixed. | LOG_AGE scalar summaries broadly solve operating-history generalization. |
| Abstract | C02 | Figure 5, Table 5 | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | Stress features do not solve C-rate fade prediction. | Stress features solve C-rate fade prediction. |
| Abstract | C03 | Figure 3, Figure 4, Table 3 | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` | C-rate holdout is the hardest capacity generalization view. | The model generalizes uniformly across stressor holdouts. |
| Abstract | C04 | Figure 6, Figure 7 | `docs/experiments/2026-05-23_pulse_target_robustness_decision.md` | RT/50 PULSE is usable as a scalar resistance endpoint. | PULSE target robustness proves broad multimodal modeling. |
| Abstract | C05 | Figure 8 | `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md` | PULSE growth is associated with capacity residual magnitude. | PULSE growth is causal. |
| Abstract | C06 | Figure 9 | `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md` | Prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped splits. | Prior PULSE improves all capacity targets. |
| Abstract | C07 | Figure 9, Table 4 | `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md` | Prior PULSE does not beat strongest supplied non-PULSE baselines. | Prior PULSE is the best available non-neural capacity feature path. |
| Abstract | C08 | Figure 9, Table 5 | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md` | `delta_capacity_Ah` remains unresolved. | Prior PULSE supports a fade-rate claim. |
| Methods: data products | C12 | Figure 1, Table 1 | `docs/SCHEMA_REGISTRY.md` | Data products are linked and provenance-bearing. | Data products imply model validity without validation. |
| Methods: validation | C12 | Figure 2 | `docs/VALIDATION_PROTOCOL.md` | Grouped validation is required for headline claims. | Random row/cell splits are headline evidence. |
| Results: capacity baselines | C03 | Figure 3, Figure 4, Table 2 | `reports/baselines/capacity_hgb50_focused/plots/best_by_target_split.csv` | C-rate is the hardest capacity split. | Uniform generalization across splits. |
| Results: stress features | C01, C02 | Figure 5, Table 5 | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | Stress features help some views but not C-rate fade. | Stress features solve fade. |
| Results: PULSE resistance | C04 | Figure 6, Figure 7 | `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv` | PULSE is a scalar resistance diagnostic endpoint. | PULSE authorizes broad multimodal claims. |
| Results: capacity-PULSE coupling | C05, C06, C07, C08 | Figure 8, Figure 9 | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv` | PULSE is explanatory and prior PULSE improves over F4 only in selected splits. | PULSE is strongest or solves fade. |
| Discussion | C09 | Table 5 | `reports/baselines/capacity_hgb50_focused/claim_readiness.md` | Quantile outputs are diagnostics only. | Calibration claim. |
| Discussion | C10 | Table 4, Table 5 | `docs/REPO_STATUS.md` | EIS is gated. | EIS has demonstrated predictive value. |
| Discussion | C11 | Table 4 | `docs/PROJECT_CHARTER.md` | CBAT is reserved for late-stage work. | CBAT is validated. |
