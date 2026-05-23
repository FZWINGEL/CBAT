# Figure Captions v0.4

## Figure 1. Data product architecture

Linked result-data products are transformed into interval tables, LOG_AGE stress-feature sidecars, PULSE target sidecars, grouped baselines, and paper-facing claim checks.
Source: `docs/PAPER_FIGURE_PLAN.md`.

## Figure 2. Grouped validation design

The benchmark treats 228 cells as 76 parameter-set conditions with replicate-aware grouped evaluation, then reports stressor-axis holdouts at condition level.
Source: `docs/VALIDATION_PROTOCOL.md`.

## Figure 3. Capacity baseline ladder

The C-rate capacity ladder shows that learned HGB baselines improve over persistence, while C-rate remains a difficult out-of-distribution split.
Source: `reports/synthesis/model_ladder_summary.csv`.

## Figure 4. C-rate failure analysis

Split-level best-known rows show C-rate as the dominant unresolved capacity generalization view.
Source: `reports/synthesis/split_difficulty_summary.csv`.

## Figure 5. Stress-feature decision

LOG_AGE stress-feature gains are mixed on the C-rate holdout, with some capacity-level gains and persistent fade-rate failures.
Source: `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv`.
Limitation: do not infer that stress features solve C-rate fade prediction.

## Figure 6. PULSE QA coverage

Canonical RT/50 PULSE target coverage includes 39,365 summary rows, 228 cells, 3,980 available canonical check-ups, 75 missing check-ups, and no duplicate canonical check-ups.
Source: `reports/audit/pulse_qa_report.json`.

## Figure 7. PULSE resistance baseline

Scalar PULSE resistance targets are predictable enough for diagnostic baselines under grouped validation.
Source: `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`.

## Figure 8. Capacity-PULSE coupling

PULSE growth is associated with capacity-model residual magnitude in condition-level diagnostics.
Source: `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv`.
Limitation: do not infer causality or independence from all confounding.

## Figure 9. Prior PULSE versus strongest non-PULSE

Prior PULSE does not beat the strongest supplied non-PULSE baseline in paired condition-level comparisons.
Source: `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv`.
Limitation: do not infer that prior PULSE is the strongest non-neural capacity feature path.

## Figure 10. Claim ladder

The claim ladder separates supported, partially supported, diagnostic, negative, gated, and blocked claims.
Source: `reports/synthesis/claim_matrix.csv`.
