# Source Artifact Checklist

Milestone 1.0.1 uses this checklist instead of adding a new CLI. It records the
source artifacts that paper-facing claims and figures depend on. A future
`mbp report check-synthesis` command can automate this table if needed.

## Claim Matrix Sources

| Claim | Source artifact | Check |
|---|---|---|
| C01 LOG_AGE scalar summaries | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` | exists |
| C02 LOG_AGE stress features | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | exists |
| C03 C-rate holdout difficulty | `docs/experiments/2026-05-22_capacity_baseline_synthesis.md` | exists |
| C04 PULSE scalar endpoint | `docs/experiments/2026-05-23_pulse_target_robustness_decision.md` | exists |
| C05 PULSE residual coupling | `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md` | exists |
| C06 Prior PULSE over F4 | `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md` | exists |
| C07 Prior PULSE vs strongest non-PULSE | `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md` | exists |
| C08 Prior PULSE fade-rate limitation | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md` | exists |
| C09 Quantile calibration | `reports/baselines/capacity_hgb50_focused/claim_readiness.md` | exists |
| C10 EIS gate | `docs/REPO_STATUS.md` | exists |
| C11 CBAT gate | `docs/PROJECT_CHARTER.md` | exists |
| C12 Grouped validation | `docs/VALIDATION_PROTOCOL.md` | exists |

## Figure Plan Sources

| Figure | Source artifact | Check |
|---|---|---|
| Data-product architecture | `docs/SCHEMA_REGISTRY.md`, `docs/REPO_STATUS.md` | exists |
| Grouped validation design | `docs/VALIDATION_PROTOCOL.md`, `reports/audit/split_registry_report.json` | exists |
| Capacity baseline ladder | `reports/synthesis/model_ladder_summary.csv` | exists |
| C-rate failure analysis | `reports/baselines/capacity_hgb50_focused/c_rate_holdout_error_analysis.md`, `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_temperature.csv` | exists |
| LOG_AGE stress-feature decision | `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md` | exists |
| PULSE target QA and coverage | `reports/audit/pulse_qa_report.json`, `reports/baselines/pulse_resistance_alignment_robustness.md`, `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md` | exists |
| PULSE resistance baseline | `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv` | exists |
| Capacity residual versus PULSE growth | `reports/coupling/pulse_capacity_robustness/*/plots/*.csv` | checked by glob during 1.0.1 review |
| Prior PULSE versus strongest non-PULSE | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv` | exists |
| Claim ladder | `reports/synthesis/claim_matrix.csv`, `docs/PAPER_CLAIM_LEDGER.md` | exists |

## Status Guardrails

Manual status checks applied in Milestone 1.0.1:

- No EIS claim is marked `supported`.
- No CBAT claim is marked `supported`.
- No prior-PULSE fade-rate claim is marked `supported`.
- Claim C01 wording no longer implies broad LOG_AGE scalar improvement.
- Descriptive best-known rows are marked as non-authoritative for claim support.

## Next Automation Candidate

If these checks become repetitive, implement:

```bash
mbp report check-synthesis \
  --claim-matrix reports/synthesis/claim_matrix.csv \
  --claim-ledger docs/PAPER_CLAIM_LEDGER.md \
  --figure-plan docs/PAPER_FIGURE_PLAN.md
```

The command should validate path existence and fail on unsupported supported
statuses for EIS, CBAT, prior-PULSE fade rate, or broad multimodal claims.
