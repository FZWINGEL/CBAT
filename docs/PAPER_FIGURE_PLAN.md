# Paper Figure And Table Plan

Milestone 1.0 figure planning is paper-facing but not yet manuscript production.
Every figure must be traceable to a tracked artifact or a reproducible generated
data product.

## Main Figures

| Figure | Working title | Purpose | Primary artifacts | Claim supported |
|---|---|---|---|---|
| 1 | Data-product architecture | Show the audit-to-interval pipeline: result data, LOG_AGE, split registry, interval table, stress sidecars, PULSE target table. | `docs/SCHEMA_REGISTRY.md`, `docs/REPO_STATUS.md` | Reproducible grouped benchmark foundation. |
| 2 | Grouped validation design | Explain condition, temperature, C-rate, profile, and voltage-window holdouts, with 76 parameter-set condition grouping. | `docs/VALIDATION_PROTOCOL.md`, `reports/audit/split_registry_report.json` | Random splits are not headline evidence. |
| 3 | Capacity baseline ladder by split | Compare L0, Ridge, HGB F4, stress features, and prior-PULSE variants across capacity targets. | `reports/synthesis/model_ladder_summary.csv` | C-rate is hardest; prior PULSE is narrow. |
| 4 | C-rate failure analysis | Show worst C-rate condition errors by temperature and voltage-window family. | `reports/baselines/capacity_hgb50_focused/c_rate_holdout_error_analysis.md`, `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_temperature.csv` | C-rate failure is concentrated in cold/cool high-current regimes. |
| 5 | LOG_AGE stress-feature decision | Show F4 versus stress-feature gains for C-rate capacity and delta targets. | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | Stress features are mixed and do not solve C-rate delta. |
| 6 | PULSE target QA and coverage | Show RT/50 coverage, alignment sensitivity, missing canonical endpoints, and direction policy. | `reports/audit/pulse_qa_report.json`, `reports/baselines/pulse_resistance_alignment_robustness.md`, `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md` | PULSE RT/50 is usable for scalar diagnostics. |
| 7 | PULSE resistance baseline | Compare PULSE 1s and 10ms delta/k1 targets across grouped splits. | `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv` | PULSE resistance is predictable enough for scalar baseline diagnostics. |
| 8 | Capacity residual versus PULSE growth | Plot residual magnitude against PULSE growth at interval and condition levels, with C-rate highlighting. | `reports/coupling/pulse_capacity_robustness/*/plots/*.csv` | PULSE growth explains capacity residuals, especially C-rate. |
| 9 | Prior PULSE versus strongest non-PULSE | Show paired condition-level gains and bootstrap intervals. | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv` | Prior PULSE beats F4 in selected splits but not strongest non-PULSE. |
| 10 | Claim ladder | Summarize supported, partial, not-supported, gated, and blocked claims. | `reports/synthesis/claim_matrix.csv`, `docs/PAPER_CLAIM_LEDGER.md` | Prevent overclaiming and frame future work. |

## Core Tables

| Table | Contents | Source |
|---|---|---|
| Dataset audit table | Row counts, cells, modality coverage, generated artifacts. | `docs/REPO_STATUS.md` |
| Model ladder table | Best metric by model family, target, and split. | `reports/synthesis/model_ladder_summary.csv` |
| Split difficulty table | Best known capacity and PULSE metrics by split. | `reports/synthesis/split_difficulty_summary.csv` |
| Claim matrix | Claim, status, metric, artifact, allowed wording, blocked wording. | `reports/synthesis/claim_matrix.csv` |
| Negative results | Failed hypotheses and decisions. | `reports/synthesis/negative_results.md` |

## Plot Rules

- Use condition-level grouped metrics for headline plots.
- Show C-rate results separately from aggregate condition-fold results.
- Keep `capacity_Ah_k1` and `delta_capacity_Ah` visually distinct; do not imply
  that level-prediction gains transfer to fade-rate prediction.
- Label PULSE coupling plots as explanatory diagnostics, not causal evidence.
- Label quantile plots as uncalibrated diagnostics unless a future calibration
  milestone changes that status.
- Do not include EIS performance figures until an EIS QA and predictive gate is
  opened and passed.
