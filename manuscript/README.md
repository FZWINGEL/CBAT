# Manuscript Draft Package v0.1

## Working Title

Grouped-Validation Benchmarks for Battery Degradation Prediction from Operating
Histories, Capacity Check-Ups, and Pulse Resistance

## Current Claim Posture

This manuscript package follows `docs/PAPER_CLAIM_LEDGER.md` and
`reports/synthesis/claim_matrix.csv`.

Supported:

- grouped validation and condition-level reporting are necessary for defensible
  evidence;
- C-rate holdout is the hardest capacity generalization view;
- RT/50 PULSE is usable as a scalar resistance endpoint.

Supported for diagnostics:

- PULSE growth is associated with capacity residual magnitude, especially under
  C-rate holdout.

Partially supported:

- scalar LOG_AGE summaries and stress features help in some grouped views;
- prior PULSE state improves `capacity_Ah_k1` over F4 in selected grouped
  splits.

Not supported:

- LOG_AGE stress features solve C-rate fade prediction;
- prior PULSE beats the strongest supplied non-PULSE baseline;
- prior PULSE improves `delta_capacity_Ah`;
- quantile HGB outputs are not validated as calibrated intervals.

Gated or blocked:

- EIS predictive value;
- CBAT;
- neural/sequence models;
- policy ranking;
- broad multimodal degradation claims.

## Draft Section Order

1. `abstract_v0.md`
2. `introduction_v0.md`
3. `methods_data_products_v0.md`
4. `methods_validation_v0.md`
5. `results_capacity_baselines_v0.md`
6. `results_stress_features_v0.md`
7. `results_pulse_resistance_v0.md`
8. `results_capacity_pulse_coupling_v0.md`
9. `discussion_negative_results_v0.md`
10. `limitations_v0.md`

## Source Artifact Policy

Every claim in the manuscript package must map to:

- a claim ID in `docs/PAPER_CLAIM_LEDGER.md`;
- a source artifact under `docs/` or `reports/`;
- a figure or table spec when it is paper-facing.

Use `manuscript/source_traceability.md` as the section-to-claim map.

## Forbidden Wording

Do not write architecture-forward or overclaiming phrases that imply:

- degradation prediction is solved;
- CBAT has been validated;
- EIS has demonstrated predictive benefit;
- a multimodal model has solved the task;
- PULSE improves capacity fade-rate prediction;
- uncertainty intervals are calibrated.

## Next Drafting Steps

1. Convert figure specs into plot scripts or notebooks only after the prose
   needs are clear.
2. Turn draft sections into a continuous manuscript v0.2.
3. Re-run source traceability after any wording changes.
4. Decide whether the next technical branch is figure generation or EIS QA.
