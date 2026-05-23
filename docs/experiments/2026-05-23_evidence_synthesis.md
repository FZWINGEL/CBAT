# 2026-05-23 Evidence Synthesis And Paper-Claim Lock

## Scope

Milestone 1.0 consolidates the completed capacity, LOG_AGE stress-feature,
PULSE resistance, capacity-PULSE coupling, and prior-PULSE comparison evidence
into a paper-facing claim set.

This milestone does not add new model training, feature engineering, EIS
modeling, sequence models, neural models, policy ranking, or CBAT architecture.

## Outputs

```text
docs/PAPER_CLAIM_LEDGER.md
docs/PAPER_FIGURE_PLAN.md
docs/PAPER_SKELETON.md
reports/synthesis/claim_matrix.csv
reports/synthesis/evidence_matrix.md
reports/synthesis/model_ladder_summary.csv
reports/synthesis/split_difficulty_summary.csv
reports/synthesis/negative_results.md
```

## Dataset And Data-Product Status

The repo now has a linked data-product stack sufficient for grouped scalar
baseline evidence:

- LOG_AGE cohort table: `904,977,105` rows across `228` cells.
- Interval table: `3,827` interval rows.
- Check-up events: `4,055`.
- Split registry: 228 cohort cells with condition/stressor split labels.
- Interval subset registry: tolerant primary subset `3,827`; strict subset
  `2,773`; monotonicity sensitivity intervals `1,054`.
- Stress sidecars: v1 and v1.1 remain modular generated artifacts.
- PULSE target table: canonical RT/50 target table remains a generated sidecar.

EIS result products exist, but EIS remains gated until valid-frequency QA and
predictive tests are implemented.

## Capacity Baseline Ladder

The capacity ladder establishes a usable grouped benchmark:

- Persistence is the reference.
- Ridge is retained as a linear sanity baseline.
- HGB-50 with `F4_state_log_age_scalar` is the main scalar capacity baseline.
- The best focused HGB-50 F4 C-rate rows remain:
  - `capacity_Ah_k1`: `0.125186` condition-mean MAE.
  - `delta_capacity_Ah`: `0.101133` condition-mean MAE.

The C-rate holdout remains the hardest capacity generalization view. Worst
conditions cluster around cold/cool high-C-rate parameter sets and wide voltage
windows.

## LOG_AGE Stress-Feature Path

The LOG_AGE stress-feature path produced a useful mixed result:

- v1.1 current-sign audit gave high-confidence positive-current charge evidence.
- Timestamp-weighted dwell and event features improved several condition and
  temperature views.
- C-rate `capacity_Ah_k1` improved from F4 `0.125186` to `0.120605`.
- C-rate `delta_capacity_Ah` did not beat F4: best stress row `0.102516` versus
  F4 `0.101133`.

The final 0.6.3 pass tested normalized delta-rate targets, train-fold residual
correction, and F11-F13 narrow cold/current groups. None beat the F4 C-rate
delta threshold.

Decision: stop broad LOG_AGE-only scalar stress-feature expansion unless a
concrete bug is found.

## PULSE QA And Target Robustness

The PULSE stream is robust enough for scalar resistance-baseline diagnostics:

- Canonical target: RT/50 `delta_pulse_1s_resistance`.
- Secondary target: RT/50 `delta_pulse_10ms_resistance`.
- Direction policy: `mean` remains canonical; for current RT/50 extraction it
  is effectively equivalent to charge because finite adjacent discharge deltas
  are unavailable.
- Alignment and missingness remain required reporting sensitivities.

Target robustness results include:

| Target | C-rate best MAE | Condition-fold best MAE | Interpretation |
|---|---:|---:|---|
| `delta_pulse_1s_resistance` | `0.00185842` | `0.000960407` | canonical transition target |
| `delta_pulse_10ms_resistance` | `0.00180642` | `0.000910676` | viable secondary diagnostic |
| `pulse_1s_resistance_k1` | `0.00189616` | `0.00104973` | state-tracking target |
| `pulse_10ms_resistance_k1` | `0.00179792` | `0.00105917` | state-tracking target |

Decision: PULSE RT/50 is ready for scalar resistance-baseline diagnostics, not
for broad multimodal claims.

## Capacity-PULSE Coupling

PULSE growth is supported as an explanatory diagnostic for capacity residuals.
The robust coupling analysis filters to canonical
`L2_hist_gradient_boosting + F4_state_log_age_scalar` predictions and checks
interval, condition, bootstrap, subgroup, and residualized correlations.

Key C-rate interval-level results:

| Target | Residual type | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | absolute residual | 143 | `0.857653` | `0.633959` |
| `delta_capacity_Ah` | absolute residual | 143 | `0.647125` | `0.646779` |

Residualization weakens global associations, especially for
`delta_capacity_Ah`, but C-rate associations remain visible.

Decision: PULSE growth explains capacity-model residual structure, especially
C-rate, but this is not causal evidence and does not by itself authorize a
predictive multimodal claim.

## Prior-PULSE Predictive Comparison

Milestone 0.9 supports a narrow F4 comparison:

| Target | Split | Best prior-PULSE group | Mean gain vs F4 | p05 |
|---|---|---|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `0.00669208` | `0.000718651` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `0.00509620` | `0.00103230` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | `0.0214905` | `0.0137834` |

Coverage does not explain the result: requiring prior PULSE drops one selected
interval and retains all 76 parameter sets.

Milestone 0.9.1 blocks the stronger claim:

| Target | Split | Prior-PULSE group | Best non-PULSE group | Mean gain | p05 |
|---|---|---|---|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `F5_log_age_histograms` | `0.000392605` | `-0.00553843` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `F6_coupled_stress` | `-0.000753049` | `-0.00294184` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | `F1_state_time` | `-0.000697582` | `-0.00281975` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `F4_state_log_age_scalar` | `-0.00234428` | `-0.0169742` |

Decision: prior PULSE improves `capacity_Ah_k1` over F4 in selected splits, but
it does not beat the strongest supplied non-PULSE baselines and does not improve
fade-rate prediction.

## Best-Row Metric Caveat

The synthesis tables include descriptive "best known row" metrics to orient
readers across many reports. These rows are useful for split-difficulty
summaries, but they do not override paired claim-readiness tests.

In particular, the prior-PULSE report contains a descriptive best row for
C-rate `delta_capacity_Ah`, but the paired F4 and strongest-non-PULSE
comparisons still block any fade-rate claim. Paper-facing claims must follow
`docs/PAPER_CLAIM_LEDGER.md` and `reports/synthesis/claim_matrix.csv`, not a
single best-row table in isolation.

## Final Claim Status

Supported:

- Grouped validation and condition-level summaries are required for headline
  evidence.
- C-rate holdout is the hardest capacity generalization view.
- PULSE RT/50 is usable as a scalar resistance endpoint.

Partially supported:

- Current scalar LOG_AGE features help nonlinear models in some views.
- LOG_AGE stress features help some condition/temperature capacity metrics.
- Prior PULSE helps `capacity_Ah_k1` over F4 in selected grouped splits.

Supported for explanatory diagnostics:

- PULSE growth is associated with capacity residual magnitude, especially in
  C-rate views.

Not supported:

- LOG_AGE stress features solve C-rate `delta_capacity_Ah`.
- Prior PULSE beats strongest supplied non-PULSE baselines.
- Prior PULSE improves `delta_capacity_Ah`.
- Quantile HGB uncertainty is calibrated.

Gated or blocked:

- EIS predictive claims are gated by EIS QA.
- Neural/sequence/CBAT/policy-ranking work remains blocked.

## Recommended Next Research Direction

Preferred next path:

1. Paper-first benchmark synthesis from the current evidence.
2. If opening a new technical stream, start with EIS QA and feature validation,
   not EIS modeling.
3. Do not start CBAT, sequence models, neural models, policy ranking, or broad
   multimodal claims from the current evidence state.

## Validation

No code was added in Milestone 1.0. Validation was limited to source-artifact
cross-checking and Markdown/CSV consistency checks.
