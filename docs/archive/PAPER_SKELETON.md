# Paper Skeleton

## Working Title

Grouped-Validation Benchmarks for Battery Degradation Prediction from Operating
Histories, Capacity Check-Ups, and Pulse Resistance

## Central Story

The paper should present a reproducible, grouped-validation benchmark for the
Luh-Blank battery aging dataset. The main contribution is not a new architecture
yet. The contribution is a disciplined evidence ladder showing where actual
operating-history features and PULSE diagnostics help, where they fail, and why
weak validation would overclaim.

## Abstract Outline

1. Introduce the need for condition-generalizing degradation models.
2. Describe the linked data products: result data, LOG_AGE, interval table,
   split registry, stress features, and PULSE target table.
3. State the validation discipline: 76 parameter-set conditions, grouped
   stressor holdouts, no random-split headline claims.
4. Summarize capacity baselines: HGB improves over persistence, but C-rate is
   hardest.
5. Summarize LOG_AGE stress results: useful in some views, not sufficient for
   C-rate fade prediction.
6. Summarize PULSE findings: RT/50 is robust as a scalar resistance endpoint;
   PULSE growth explains capacity residuals; prior PULSE helps capacity level
   over F4 in selected splits but not over strongest non-PULSE baselines.
7. Close with negative results and gated future modalities.

## Abstract Draft

Battery degradation models are often evaluated under splits that are easier
than the operating-regime shifts they are meant to support. We construct a
reproducible grouped-validation benchmark for the Luh-Blank battery aging
dataset, linking capacity check-ups, LOG_AGE operating histories, scalar stress
features, and RT/50 PULSE resistance targets across 228 cells and 76
parameter-set conditions. Under held-out condition, temperature, C-rate,
profile, and voltage-window splits, HGB baselines show that C-rate transfer is
the hardest capacity setting. Scalar LOG_AGE and stress features help some
views but do not solve C-rate fade prediction. RT/50 PULSE is robust enough as a
scalar resistance endpoint, and PULSE growth is associated with capacity-model
residuals, especially under C-rate holdout. Prior PULSE state improves
`capacity_Ah_k1` over an F4 LOG_AGE scalar baseline in selected grouped splits,
but it does not beat the strongest supplied non-PULSE baselines and does not
improve `delta_capacity_Ah`. The result is a claim-bounded benchmark and
evidence ledger, not a neural architecture or broad multimodal claim.

## Contributions

- A reproducible interval-level data-product stack for grouped battery
  degradation benchmarking.
- A validation protocol that treats the 228 cells as 76 condition triplets and
  rejects random row/cell splits as headline evidence.
- A scalar capacity baseline ladder showing C-rate holdout as the dominant
  unresolved generalization stressor.
- LOG_AGE scalar and stress-feature ablations that document both useful gains
  and negative C-rate fade results.
- A PULSE RT/50 target policy, QA sequence, and scalar resistance baseline.
- Capacity-PULSE coupling diagnostics showing that PULSE growth is associated
  with capacity residual magnitude.
- A prior-PULSE predictive boundary: improvement over F4 in selected
  `capacity_Ah_k1` splits, but no superiority over strongest supplied
  non-PULSE baselines and no `delta_capacity_Ah` claim.
- A paper-facing claim ledger and negative-result matrix to prevent overclaiming.

## Sections

### 1. Motivation

- Battery degradation is path-dependent and regime-dependent.
- Realized exposure histories and diagnostic check-ups should be evaluated under
  held-out operating regimes, not random row splits.
- The study aims to define what is defensible before adding architectures.

### 2. Dataset And Audit

- Dataset basis: Luh-Blank comprehensive battery aging dataset.
- Cohort: 228 cells, 76 parameter-set conditions with 3 replicates each.
- Result modalities: capacity, EIS, PULSE, EOC, LOG_AGE.
- LOG_AGE cohort table: 904,977,105 rows, 228 cells.
- Audit outputs: manifests, schema registry, known issues, split registry,
  interval QA, monotonicity reports.
- EIS remains gated; do not claim EIS value.

### 3. Data Products

- `cell_condition_table`
- `checkup_event_table`
- `modality_table_log_age`
- `split_registry_v1`
- `interval_table`
- `interval_subset_registry_v1`
- `interval_stress_features_v1_1`
- `pulse_target_table`

Key design decision: stress features and PULSE targets are sidecars, not
mutations of the core interval spine.

### 4. Validation Protocol

- Headline evidence uses grouped condition and stressor splits:
  `condition_fold`, `temperature_holdout_fold`, `c_rate_holdout_fold`,
  `profile_holdout_fold`, and `voltage_window_holdout_fold`.
- Random row/cell splits are not publishable evidence.
- LOG_AGE monotonicity is handled with tolerant primary and strict sensitivity
  subsets.
- Target leakage rules: inserted LOG_AGE diagnostics, target-derived stress
  rates, future PULSE state, and PULSE deltas are forbidden as capacity inputs.

### 5. Capacity Baselines

- L0 persistence, Ridge, and HGB ladder.
- State-aware feature groups include prior capacity.
- HGB F4 improves over L0 across targets and split views.
- C-rate is the hardest capacity split.
- Quantile HGB remains uncalibrated.

### 6. LOG_AGE Stress-Feature Experiments

- v1 added dwell and coupled-stress features; v1.1 added current-sign audit,
  timestamp-weighted dwell, coverage/gap diagnostics, and event features.
- v1.1 improved some capacity level and condition/temperature metrics.
- C-rate `delta_capacity_Ah` did not beat F4.
- Normalized delta-rate targets, train-fold bias correction, and F11-F13
  cold/current groups failed to solve the C-rate delta problem.

### 7. PULSE QA And Resistance Baseline

- PULSE target policy: canonical RT/50 `delta_pulse_1s_resistance`; 10ms is a
  secondary diagnostic.
- Alignment, direction, and missingness sensitivity are explicit.
- RT/50 mean is effectively charge for current adjacent interval deltas.
- PULSE resistance baselines are scalar diagnostics, not multimodal capacity
  claims.

### 8. Capacity-PULSE Coupling

- Coupling table joins capacity residuals with PULSE growth.
- PULSE growth correlates with capacity residual magnitude at prediction,
  interval, and condition levels.
- Residualization weakens global associations, so the result is explanatory and
  not causal.
- C-rate associations remain visible and are scientifically useful.

### 9. Prior-PULSE Predictive Tests

- Prior `pulse_1s_resistance_k` improves `capacity_Ah_k1` over F4 in C-rate,
  temperature, and profile splits.
- Requiring prior PULSE drops only one selected interval and retains all 76
  parameter sets.
- Prior PULSE does not improve C-rate `delta_capacity_Ah`.
- Prior PULSE does not beat the strongest supplied non-PULSE HGB baselines.

### 10. Negative Results And Limitations

- LOG_AGE stress features do not solve C-rate fade prediction.
- Normalized rate targets and train-fold bias correction did not solve C-rate
  delta.
- Quantile HGB is not calibrated.
- PULSE is not yet a broad predictive multimodal feature claim.
- EIS and CBAT remain gated.

Limitations paragraph:

The current benchmark is intentionally conservative. C-rate conclusions depend
on small held-out condition counts, PULSE RT/50 alignment remains a reported
sensitivity, and the current PULSE direction policy is effectively charge-only
for adjacent RT/50 deltas. LOG_AGE stress features and prior PULSE do not solve
C-rate `delta_capacity_Ah`, quantile HGB outputs are not calibrated, and EIS has
not passed a predictive QA gate. The study therefore supports grouped benchmark
and scalar diagnostic claims, not causal, counterfactual, policy-ranking, neural
architecture, or CBAT claims.

No-overclaim language:

> The benchmark identifies signals and limits under grouped validation. It does
> not establish a general multimodal architecture, a calibrated uncertainty
> model, or a same-cell counterfactual policy engine.

### 11. Claim Ladder

Use `docs/PAPER_CLAIM_LEDGER.md` as the table source. The paper should separate:

- supported claims;
- partially supported claims;
- not-supported claims;
- gated claims;
- blocked claims.

### 12. Future Work

Preferred near-term path:

1. Paper-first benchmark consolidation.
2. If adding a new evidence stream, open EIS QA and feature validation.
3. Only after new gates pass, consider non-neural multimodal baselines.
4. Neural, sequence, policy-ranking, and CBAT work remain late-stage.
