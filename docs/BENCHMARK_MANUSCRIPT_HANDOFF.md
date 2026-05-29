# Benchmark And Manuscript Handoff

This note is for an external reviewer, collaborator, or future maintainer who
needs the current benchmark and manuscript state without reading the full
development history.

## Current Package

- Benchmark release: `benchmark-v0.2-rc1`
- Release URL: `https://github.com/FZWINGEL/CBAT/releases/tag/benchmark-v0.2-rc1`
- Main manuscript: `manuscript/manuscript_v0_7.md`
- Supplement: `manuscript/supplement_v0_7.md`
- Submission bundle: `manuscript/submission_bundle_v0_8.md`

## What The Project Is

The project is a reproducible grouped-validation benchmark for battery
degradation prediction from capacity check-ups, operating-history products,
PULSE scalar resistance diagnostics, and gated EIS scalar diagnostics. It uses
claim-ledger governance to distinguish supported results, diagnostic-only
results, negative results, and blocked future branches.

## What The Project Is Not

The current package is not:

- a CBAT architecture release;
- a neural or sequence-model release;
- a policy-ranking tool;
- a detector-knee prediction package;
- a causal or same-cell counterfactual analysis;
- a raw-data distribution.

## Fast Review Order

1. `docs/RELEASE_NOTES_v0.2-rc1.md`
2. `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
3. `reports/synthesis/main_project_gate_status.md`
4. `manuscript/manuscript_v0_7.md`
5. `manuscript/manuscript_v0_7_traceability.md`
6. `manuscript/submission_bundle_v0_8.md`

## Reproduction Entry Points

- Setup and artifact policy: `docs/BENCHMARK_REPRODUCIBILITY.md`
- Ordered commands: `docs/BENCHMARK_RUNBOOK.md`
- Dependency map: `docs/COMMAND_DAG.md`
- Artifact manifest: `reports/synthesis/artifact_manifest_v2.csv`
- Release check: `mbp report check-release-candidate`

## Current Claim Boundary

Use these phrases:

- grouped-validation benchmark;
- diagnostic PULSE and EIS scalar endpoints;
- C-rate holdout as the dominant unresolved capacity transfer stressor;
- diagnostic 80% capacity-relative threshold-event forecasting beyond
  proximity baselines.

Avoid implying:

- architecture readiness;
- broad EIS or PULSE predictive dominance;
- interval-reliability or risk-score calibration readiness;
- detector-knee prediction readiness;
- policy ranking;
- causal or same-cell counterfactual conclusions.

## Next Work Options

Default next work is venue-specific manuscript formatting and human coauthor
review. The only optional technical branch currently consistent with the claim
ledger is a narrow grouped calibration branch for the threshold-event warning
score. Do not open CBAT, sequence/neural, DRT/embedding, policy-ranking, or
causal branches from the current evidence.
