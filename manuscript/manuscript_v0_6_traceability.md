# Manuscript v0.6 Traceability

This sidecar maps the reader-facing v0.6 manuscript to the v2 claim ledger and
tracked source artifacts. It keeps claim-control details out of
`manuscript/manuscript_v0_6.md`.

| Manuscript section | Claim IDs | Figures/tables | Evidence artifacts | Allowed wording | Do-not-say summary |
|---|---|---|---|---|---|
| Abstract | C01-C19 | Table 6 | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`; `reports/synthesis/main_project_claim_matrix_v2.csv` | The release is a claim-bounded grouped-validation benchmark. | Do not present the work as architecture validation or policy support. |
| Introduction | C01, C11, C12 | Figure 1, Figure 2 | `docs/PROJECT_CHARTER.md`; `docs/VALIDATION_PROTOCOL.md` | Condition triplets and stressor holdouts define headline evidence. | Do not use random row splits as paper-facing support. |
| Data Products and Validation | C12 | Figure 1, Figure 2, Table 1, Table 8 | `docs/BENCHMARK_RUNBOOK.md`; `reports/synthesis/artifact_manifest_v2.csv`; `reports/synthesis/release_candidate_check.md` | The release is reproducible from tracked reports and local ignored data products. | Do not imply raw data or generated Parquets are included. |
| Capacity and LOG_AGE Baselines | C01, C02, C03 | Figure 3, Figure 4, Figure 5, Table 2, Table 3, Table 5 | `reports/synthesis/model_ladder_summary.csv`; `reports/synthesis/split_difficulty_summary.csv`; `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_gain_by_feature_group.csv` | C-rate remains hardest; scalar LOG_AGE and stress features are mixed. | Do not claim C-rate fade is solved. |
| PULSE and EIS Diagnostic Endpoints | C04-C10 | Figure 6, Figure 7, Figure 8, Figure 9, Figure 11 | `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`; `docs/experiments/2026-05-23_eis_claim_hardening.md` | PULSE and EIS are scalar diagnostic endpoints with bounded prior-feature signals. | Do not claim broad multimodal or broad EIS outcome benefit. |
| Domain Comparators and Reliability Gates | C09, C13, C14, C15 | Figure 12, Table 6 | `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`; `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md` | Semi-empirical comparators are useful; C-rate interval coverage remains insufficient. | Do not claim validated global interval reliability. |
| Temporal Order, Knee Labels, and Threshold Events | C16, C17, C18 | Figure 13, Table 6 | `docs/experiments/2026-05-23_temporal_history_value_gate.md`; `docs/experiments/2026-05-23_knee_threshold_label_forensics.md` | Sequence readiness and detector-knee prediction remain blocked; threshold labels are the stronger label family. | Do not claim sequence or detector-knee prediction readiness. |
| Threshold-Event Warning | C18, C19 | Figure 14, Table 7 | `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`; `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md` | Non-neural baselines forecast the 80% threshold event diagnostically beyond proximity and verified-only sensitivity. | Do not claim risk calibration, policy use, or causal warning. |
| Release Package and Reproducibility | C11, C12, C19 | Figure 14, Table 8 | `reports/synthesis/release_candidate_check.md`; `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md`; GitHub release `benchmark-v0.1-rc2` | The rc2 package is a reproducible release candidate and handoff archive. | Do not imply release packaging adds new science. |
| Discussion and Limitations | C02, C07-C11, C14-C17 | Table 5, Table 6 | `reports/synthesis/blocked_claims_v2.md`; `reports/synthesis/next_branch_decision.md` | Negative and blocked results are part of the benchmark contribution. | Do not reopen CBAT, sequence, policy, DRT, embedding, detector-knee, or causal branches without a new gate. |

## Reader-Facing Prose Guardrails

The v0.6 manuscript body should remain reader-facing. Claim IDs, source maps,
and wording controls belong in this sidecar and supplement, not in the main
text.

The manuscript must avoid unsupported assertions about architecture validation,
risk-score calibration, global interval reliability, sequence readiness,
detector-knee prediction, policy ranking, same-cell counterfactuals, and broad
multimodal benefit.
