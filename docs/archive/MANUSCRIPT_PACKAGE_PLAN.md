# Manuscript Package Plan

Milestone 1.0.1 prepares the paper-facing package for drafting. It does not
authorize new modeling, EIS modeling, feature engineering, neural/sequence
models, policy ranking, CBAT, or broad multimodal claims.

## Main Narrative

The manuscript should be a grouped-validation benchmark paper. Its central
message is that strict held-out-condition evaluation changes the scientific
story: operating-history and PULSE diagnostics contain useful signal, but they
do not justify broad multimodal or architecture claims yet.

Recommended one-sentence framing:

> We build a reproducible grouped-validation benchmark for battery degradation
> prediction and show where LOG_AGE operating-history features and RT/50 PULSE
> diagnostics help, where they fail, and which multimodal claims remain gated.

## Exact Allowed Headline Claims

- The repo implements a reproducible interval-level grouped-validation benchmark
  over 228 cells and 76 parameter-set conditions.
- C-rate holdout is the hardest capacity generalization view in the current
  scalar benchmark.
- Current scalar LOG_AGE summaries help nonlinear models in some grouped views,
  but gains are mixed.
- LOG_AGE stress features improve some condition/temperature metrics but do not
  solve C-rate `delta_capacity_Ah`.
- Canonical RT/50 PULSE is robust enough for scalar resistance-baseline
  diagnostics.
- PULSE growth is associated with capacity residual magnitude, especially in
  C-rate views.
- Prior PULSE state improves `capacity_Ah_k1` over F4 in selected grouped
  splits.
- Prior PULSE does not beat the strongest supplied non-PULSE HGB baselines and
  does not improve `delta_capacity_Ah`.

## Exact Forbidden Claims

- LOG_AGE stress features solve C-rate fade prediction.
- Prior PULSE improves capacity fade-rate prediction.
- Prior PULSE is the strongest available non-neural capacity feature path.
- PULSE growth is causal or independent of all confounding.
- PULSE target robustness authorizes broad capacity+PULSE multimodal claims.
- Quantile HGB intervals are calibrated.
- EIS improves prediction.
- CBAT, neural, sequence, or policy-ranking models are justified by the current
  evidence.

## Figure And Table Package

| Package item | Artifact source | Draft use |
|---|---|---|
| Data-product architecture figure | `docs/SCHEMA_REGISTRY.md`, `docs/REPO_STATUS.md` | Methods overview |
| Grouped validation figure | `docs/VALIDATION_PROTOCOL.md`, `reports/audit/split_registry_report.json` | Validation protocol |
| Capacity ladder table/figure | `reports/synthesis/model_ladder_summary.csv` | Results: capacity baselines |
| Split difficulty table | `reports/synthesis/split_difficulty_summary.csv` | Results: generalization stressors |
| C-rate failure figure | `reports/baselines/capacity_hgb50_focused/c_rate_holdout_error_analysis.md` | Results: failure analysis |
| LOG_AGE stress decision figure | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | Results: stress-feature ablation |
| PULSE target QA table | `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv` | Results: resistance endpoint |
| Coupling figure | `reports/coupling/pulse_capacity_robustness/*/plots/*.csv` | Results: residual diagnostics |
| Prior PULSE comparison figure | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv` | Results: predictive boundary |
| Claim ladder table | `reports/synthesis/claim_matrix.csv` | Discussion |
| Negative-result table | `reports/synthesis/negative_results.md` | Discussion and limitations |

## First Draft Order

1. Methods: dataset audit, data products, schema/split registry, leakage
   controls.
2. Methods: validation protocol and condition-level aggregation.
3. Results: capacity baseline ladder and C-rate difficulty.
4. Results: LOG_AGE scalar and stress-feature experiments.
5. Results: PULSE QA and scalar resistance baseline.
6. Results: capacity-PULSE residual coupling.
7. Results: prior PULSE over F4 and strongest-non-PULSE boundary.
8. Discussion: negative results and claim ladder.
9. Limitations: C-rate condition count, PULSE alignment/direction, no EIS, no
   calibration claim, no counterfactuals.
10. Future work: EIS QA gate or paper-first benchmark extension.

## Reviewer-Risk Checklist

Use `reports/synthesis/reviewer_risk_register.md` while drafting. The highest
priority risks to address in the first draft are:

- grouped split justification;
- small C-rate condition count;
- PULSE alignment and direction policy;
- leakage prevention for LOG_AGE/PULSE features;
- prior PULSE not beating strongest non-PULSE;
- uncalibrated quantile outputs;
- EIS gated but not tested.

## No-Overclaim Language

Use this pattern in the abstract and conclusion:

> These results support scalar diagnostic and benchmark claims, not a broad
> multimodal architecture claim. Prior PULSE improves capacity-level prediction
> over a defined F4 baseline in selected splits, but it does not beat the
> strongest supplied non-PULSE baselines and does not improve fade-rate
> prediction.

Do not use architecture-forward language such as "CBAT solves degradation
modeling" or "multimodal prediction is validated."
