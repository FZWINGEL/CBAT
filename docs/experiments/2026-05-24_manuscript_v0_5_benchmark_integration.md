# Milestone 4.0: Manuscript v0.5 Benchmark Integration

Date: 2026-05-24

## Goal

Integrate the validated `benchmark-v0.1-rc2` evidence package into a
reader-facing manuscript draft without adding new models, new feature
engineering, or new scientific claims.

## Added Artifacts

- `docs/RELEASE_NOTES_v0.1-rc2.md`
- `docs/GITHUB_RELEASE_DRAFT_v0.1-rc2.md`
- `docs/BENCHMARK_V0_1_RC2_SUMMARY.md`
- `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md`
- `manuscript/manuscript_v0_5.md`
- `manuscript/manuscript_v0_5_traceability.md`
- `manuscript/captions/figure_captions_v0_5.md`
- `manuscript/captions/table_captions_v0_5.md`
- `manuscript/figures/generated/fig11_eis_scalar_gate.svg`
- `manuscript/figures/generated/fig12_uncertainty_calibration_gate.svg`
- `manuscript/figures/generated/fig13_temporal_knee_threshold_gate.svg`
- `manuscript/figures/generated/fig14_threshold_warning_release_gate.svg`
- `manuscript/tables/generated/table06_main_project_gate_status.md`
- `manuscript/tables/generated/table07_threshold_warning_summary.md`
- `manuscript/tables/generated/table08_release_artifact_summary.md`

## Evidence Integrated

- EIS QA, scalar endpoints, and prior-feature hardening
- semi-empirical comparator results
- replicate uncertainty and interval-calibration diagnostics
- temporal-order falsification
- detector-knee and threshold-label stability
- threshold-event warning censoring finalization
- benchmark release-candidate validation and rc2 publication

## Claim Posture

The v0.5 draft preserves the v2 claim ledger. It supports grouped validation,
diagnostic PULSE/EIS endpoints, and diagnostic 80% threshold-event forecasting.
It keeps architecture, policy, sequence, DRT/embedding, detector-knee,
risk-calibration, causal, and broad multimodal branches blocked.

## Validation Summary

Completed before commit:

- manuscript claim check: passed
- manuscript reader check: passed
- release-candidate check: passed
- `git diff --check`: passed
- generated data or Parquet artifact staging check: to be rerun before commit

## Notes

The manuscript update is a synthesis and release-integration pass only. It does
not add new modeling, new feature engineering, new labels, or new scientific
claims beyond the v2 claim ledger.
