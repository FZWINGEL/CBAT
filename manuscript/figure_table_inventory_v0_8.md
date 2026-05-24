# Figure And Table Inventory v0.8

This inventory maps manuscript display items to source artifacts and claim
areas. It is intended for venue selection and final figure/table trimming.

## Main Figures

| Item | Current source | Claim area | Status |
|---|---|---|---|
| Figure 1: data-product architecture | `manuscript/figures/generated/fig01_data_product_architecture.svg` | Study design and linked artifacts | Main-text ready after venue sizing. |
| Figure 2: grouped validation design | `manuscript/figures/generated/fig02_grouped_validation_design.svg` | Condition-triplet validation discipline | Main-text ready. |
| Figure 3: capacity baseline ladder | `manuscript/figures/generated/fig03_capacity_baseline_ladder.svg` | Scalar capacity benchmark and split difficulty | Main-text ready. |
| Figure 4: C-rate failure analysis | `manuscript/figures/generated/fig04_c_rate_failure_analysis.svg` | C-rate capacity and fade generalization difficulty | Main-text ready. |
| Figure 5: stress-feature decision | `manuscript/figures/generated/fig05_stress_feature_decision.svg` | Mixed LOG_AGE stress-feature gains | Main-text or supplement depending on space. |
| Figure 6: PULSE QA coverage | `manuscript/figures/generated/fig06_pulse_qa_coverage.svg` | PULSE scalar endpoint readiness | Main-text ready. |
| Figure 7: PULSE resistance baseline | `manuscript/figures/generated/fig07_pulse_resistance_baseline.svg` | PULSE RT/50 scalar diagnostic endpoint | Main-text ready. |
| Figure 8: PULSE-capacity coupling | `manuscript/figures/generated/fig08_pulse_capacity_coupling.svg` | PULSE residual association diagnostics | Main-text or supplement. |
| Figure 9: prior PULSE comparison | `manuscript/figures/generated/fig09_prior_pulse_vs_nonpulse.svg` | Prior PULSE strongest-baseline guardrail | Main-text or supplement. |
| Figure 10: claim ladder | `manuscript/figures/generated/fig10_claim_ladder.svg` | Claim governance | Main-text or graphical summary. |
| Figure 11: EIS scalar gate | `manuscript/figures/generated/fig11_eis_scalar_gate.svg` | EIS QA and scalar endpoint diagnostics | Main-text or supplement depending on venue. |
| Figure 12: interval-reliability gate | `manuscript/figures/generated/fig12_uncertainty_calibration_gate.svg` | Replicate and interval diagnostics | Main-text or supplement. |
| Figure 13: temporal, knee, and threshold gates | `manuscript/figures/generated/fig13_temporal_knee_threshold_gate.svg` | Temporal-order and label-stability gates | Main-text ready. |
| Figure 14: threshold-warning release gate | `manuscript/figures/generated/fig14_threshold_warning_release_gate.svg` | Diagnostic 80% threshold-event forecasting and release boundary | Main-text ready with guarded caption. |

If exact generated filenames differ after venue formatting, keep the source
artifact mapping in `manuscript/manuscript_v0_7_traceability.md` authoritative.

## Core Tables

| Item | Current source | Claim area | Status |
|---|---|---|---|
| Table 1: dataset audit | `manuscript/tables/generated/table01_dataset_audit.md` | Audited cohort and interval population | Main-text ready. |
| Table 2: model ladder | `manuscript/tables/generated/table02_model_ladder.md` | Baseline ladder and blocked architecture boundary | Main-text ready. |
| Table 3: split difficulty | `manuscript/tables/generated/table03_split_difficulty.md` | C-rate difficulty and grouped split evidence | Main-text ready. |
| Table 4: claim matrix | `manuscript/tables/generated/table04_claim_matrix.md`; `reports/synthesis/main_project_claim_matrix_v2.csv` | Supported, diagnostic-only, not-supported, and blocked claims | Main-text ready. |
| Table 5: negative results | `manuscript/tables/generated/table05_negative_results.md` | Explicit negative-result gates | Main-text or supplement. |
| Table 6: main-project gate status | `manuscript/tables/generated/table06_main_project_gate_status.md` | Capacity, LOG_AGE, PULSE, EIS, interval checks, temporal order, knee/threshold, threshold warning | Main-text or supplement. |
| Table 7: threshold-warning summary | `manuscript/tables/generated/table07_threshold_warning_summary.md` | Diagnostic 80% threshold-event forecasting | Main-text ready. |
| Table 8: release artifact summary | `manuscript/tables/generated/table08_release_artifact_summary.md`; `reports/synthesis/artifact_manifest_v2.csv` | Reproducibility and handoff | Supplement ready. |

## Evidence Versus Schematic Items

| Item class | Interpretation |
|---|---|
| Workflow diagrams | Descriptive schematics; they do not prove a claim by themselves. |
| Baseline performance figures | Evidence-bearing; must retain grouped-split context. |
| Claim ledger tables | Governance artifacts; they define allowed wording. |
| Release/reproducibility tables | Engineering evidence for rerun readiness, not model-performance evidence. |

## Figure-Caption Guardrails

- Describe PULSE and EIS as scalar diagnostic endpoints.
- Describe threshold warning as diagnostic threshold-event forecasting.
- Describe interval methods as failing the C-rate gate for global interval
  reliability.
- Do not imply CBAT, policy ranking, sequence-model readiness, detector-knee
  prediction, or causal conclusions.
