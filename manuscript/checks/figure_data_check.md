# Figure Data Check

| Figure | Kind | Source | Rows consumed | Key values | Warnings |
|---|---|---|---:|---|---|
| Figure 1 | schematic | `docs/PAPER_FIGURE_PLAN.md` | 0 | schematic data-product flow | none |
| Figure 2 | schematic | `docs/VALIDATION_PROTOCOL.md` | 0 | 228 cells; 76 condition triplets | none |
| Figure 3 | data-driven | `reports/synthesis/model_ladder_summary.csv` | 8 | C-rate capacity and delta ladder metrics | none |
| Figure 4 | data-driven | `reports/synthesis/split_difficulty_summary.csv` | 5 | best-known capacity_Ah_k1 by split | none |
| Figure 5 | data-driven | `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv` | 12 | F4-to-stress C-rate gains | does not imply stress features solve C-rate fade |
| Figure 6 | data-driven | `reports/audit/pulse_qa_report.json` | 5 | summary rows=39365; unique cells=228; available checkups=3980; missing checkups=75; duplicate checkups=0 | none |
| Figure 7 | data-driven | `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv` | 10 | 1s and 10ms RT/50 transition-target rows | none |
| Figure 8 | data-driven | `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/condition_level_pulse_capacity_correlation.csv` | 8 | condition-level Pearson correlations | diagnostic association, not causality |
| Figure 9 | data-driven | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/plots/split_level_gain_vs_best_nonpulse.csv` | 10 | prior-PULSE paired gains versus strongest non-PULSE | does not support prior PULSE beating strongest non-PULSE |
| Figure 10 | data-driven | `reports/synthesis/claim_matrix.csv` | 12 | claim status counts | none |
