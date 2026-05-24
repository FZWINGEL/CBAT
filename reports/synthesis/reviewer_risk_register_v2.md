# Reviewer Risk Register v2

This register updates the original reviewer-risk file after the EIS,
semi-empirical, replicate, calibration, temporal-order, knee/threshold,
threshold-warning, release, and v0.6 manuscript gates.

| Risk | Current mitigation | Source artifact | Remaining limitation |
|---|---|---|---|
| Reviewers may expect random split scores. | The validation protocol defines condition and stressor holdouts as headline evidence; random splits are leakage smoke tests only. | `docs/VALIDATION_PROTOCOL.md` | Main text must explain that 228 cells are 76 condition triplets. |
| C-rate evidence has limited condition count. | Reports aggregate by parameter set and keep C-rate fade claims blocked. | `reports/synthesis/main_project_gate_status.md` | C-rate remains a hard, dataset-limited stressor view. |
| LOG_AGE features may leak future diagnostics. | Inserted diagnostics are masked; target-derived rates stay diagnostic; warning features use check-up-k state only. | `docs/VALIDATION_PROTOCOL.md`; `reports/baselines/threshold_warning_l0_l2/threshold_warning_leakage_audit.md` | Manuscript must keep diagnostic columns and predictive inputs separate. |
| Stress features do not solve C-rate fade. | Negative result is documented and used as a benchmark boundary. | `reports/synthesis/negative_results.md` | The result should be framed as evidence, not omitted. |
| PULSE alignment or direction handling may confound resistance claims. | Alignment sensitivity and direction policy are documented; PULSE claims remain scalar and diagnostic. | `docs/experiments/2026-05-23_pulse_target_robustness_decision.md` | No discharge-specific adjacent-delta claim is made. |
| Prior PULSE does not beat strongest non-PULSE baselines. | Strongest-baseline comparison is explicit and negative. | `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md` | Main text must separate F4 gains from strongest-baseline results. |
| EIS appears central but has narrow predictive value. | EIS QA, scalar endpoints, and hardening are included; broad EIS outcome claims remain blocked. | `docs/experiments/2026-05-23_eis_claim_hardening.md` | EIS wording must stay diagnostic and split-specific. |
| Semi-empirical baselines could be seen as weak or unfair. | Ridge-style stress comparators are documented as interpretable domain checks, not mechanism identification. | `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md` | They do not replace electrochemical mechanism models. |
| Replicate diagnostics may be mistaken for validated intervals. | Replicate spread is framed as diagnostic context only. | `reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md` | No global interval-reliability claim is authorized. |
| Grouped conformal methods do not pass C-rate coverage. | Calibration report keeps interval reliability blocked globally. | `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md` | Main text must avoid implying deployable interval estimates. |
| Temporal-order product is large but sequence value is negative. | Run-event QA and order-vs-shuffled diagnostics are documented; sequence models remain blocked. | `docs/experiments/2026-05-23_temporal_history_value_gate.md` | Run-event QA warning remains a limitation. |
| Detector-knee labels are unstable. | Knee-label gate and forensics show detector-knee prediction is blocked. | `docs/experiments/2026-05-23_knee_label_stability_gate.md`; `docs/experiments/2026-05-23_knee_threshold_label_forensics.md` | Knee labels remain exploratory diagnostics. |
| Threshold-event warning may be confused with calibrated risk or policy guidance. | Verified-only censoring and proximity hardening support only diagnostic threshold-event forecasting. | `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md` | Risk-score calibration, policy use, and causality remain blocked. |
| Release excludes raw/generated data. | Runbook, command DAG, artifact manifest, and release checker define local reproducibility. | `reports/synthesis/release_candidate_check.md`; `reports/synthesis/artifact_manifest_v2.csv` | Full reruns require local data access and substantial compute. |
| Best-row tables may be overinterpreted. | Captions and traceability distinguish descriptive best rows from claim-readiness tests. | `manuscript/manuscript_v0_7_traceability.md` | Reviewer-facing captions must keep the caveat visible. |

## Preflight Rule

No reviewer response, cover note, abstract, or future-branch plan may present
blocked claims as supported without a new gated milestone and source-linked
evidence.
