# Manuscript v0.2


Working title: Grouped-validation battery degradation benchmarks with operating-history and PULSE diagnostics.


This draft is assembled from the Milestone 1.1 section files. Figure and table callouts point to generated assets under `manuscript/figures/generated/` and `manuscript/tables/generated/`.



## Abstract


# Abstract v0

Battery degradation models are often evaluated under splits that are easier
than the operating-regime shifts they are intended to support. We build a
reproducible grouped-validation benchmark for battery degradation prediction
from operating histories, capacity check-ups, and pulse resistance using the
Luh-Blank aging dataset. The benchmark links result-data products, LOG_AGE
operating histories, interval tables, stress-feature sidecars, split registries,
and RT/50 PULSE resistance targets across 228 cells organized as 76
parameter-set conditions with three replicates each.

Under condition-level and stressor-axis holdouts, scalar HGB baselines show that
C-rate transfer is the dominant unresolved capacity generalization setting.
Current scalar LOG_AGE summaries and stress features help in some grouped views,
especially for nonlinear models, but they do not solve C-rate
`delta_capacity_Ah` prediction. Canonical RT/50 PULSE is robust enough for
scalar resistance-baseline diagnostics, and PULSE growth is associated with
capacity-model residual magnitude, especially under C-rate holdout. Prior PULSE
state improves `capacity_Ah_k1` over an F4 LOG_AGE scalar baseline in selected
grouped splits, but it does not beat the strongest supplied non-PULSE baselines
and does not improve `delta_capacity_Ah`.

The result is a claim-bounded benchmark and evidence ledger. It supports
grouped validation, scalar diagnostic, and negative-result claims, while keeping
EIS predictive value, neural/sequence models, policy ranking, and CBAT as gated
future work.

Claim IDs: C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12.


Referenced assets: [Figure 10], [Table 4].


## Introduction


# Introduction v0

Battery degradation is path-dependent: temperature, voltage window, state of
charge, C-rate, current profile, rest periods, and prior age interact over time.
Open aging datasets increasingly include operating histories and diagnostic
check-ups, but the central modeling question is not whether a model can fit
cells from familiar regimes. The harder question is whether it can generalize
to held-out operating regimes.

This manuscript treats that question as a benchmark-design problem before it is
an architecture problem. The Luh-Blank dataset provides a useful setting because
it combines capacity check-ups, PULSE resistance, EIS records, and LOG_AGE
operating histories across 228 cells. Those 228 cells represent 76
parameter-set conditions with three replicates each, so condition-level grouping
is essential. Random row or cell splits would overstate evidence by mixing
replicates and operating regimes across train and test.

The study builds a linked interval-level data-product stack and evaluates
capacity and resistance baselines under condition and stressor holdouts. It
tests whether scalar LOG_AGE summaries, physically motivated stress features,
and prior PULSE state add useful information beyond simpler state and protocol
features. It also records negative results as part of the contribution:
stress-feature engineering does not solve C-rate fade prediction, prior PULSE
does not beat the strongest supplied non-PULSE capacity baseline, and quantile
HGB outputs are not calibrated.

Allowed claims:

- C03: C-rate holdout is the hardest capacity generalization view.
- C04: RT/50 PULSE is usable as a scalar resistance endpoint.
- C05: PULSE growth is associated with capacity residual magnitude.
- C06: prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped splits.

Blocked claims:

- C07: prior PULSE beats the strongest supplied non-PULSE capacity baseline.
- C08: prior PULSE improves `delta_capacity_Ah`.
- C10: EIS has demonstrated predictive value.
- C11: CBAT architecture is justified.

Source artifacts:

- `docs/PROJECT_CHARTER.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `reports/synthesis/claim_matrix.csv`


Referenced assets: [Figure 2], [Table 4].


## Dataset and Linked Data Products


# Methods: Data Products v0

The benchmark is built from linked data products rather than ad hoc notebook
joins. The core cohort contains 228 cells, interpreted as 76 parameter-set
conditions with three replicates per condition. The current linked data-product
stack includes cell condition metadata, check-up events, LOG_AGE operating
history, interval tables, grouped split labels, monotonicity-aware interval
subsets, LOG_AGE stress-feature sidecars, and canonical RT/50 PULSE target
tables.

The LOG_AGE cohort table contains 904,977,105 rows across all 228 cells.
Capacity targets are organized around 3,827 check-up intervals derived from
4,055 check-up events. The interval table is the modeling spine: one row
represents a transition from check-up `k` to `k+1`, with prior state at `k`,
future target at `k+1`, condition metadata, split labels, and quality flags.

LOG_AGE monotonicity issues are handled through an explicit policy rather than
silently dropped. The tolerant baseline subset keeps all 3,827 intervals while
flagging 1,054 intervals for monotonicity sensitivity. The strict subset has
2,773 intervals. Baseline reports therefore use the tolerant subset as primary
and retain strict exclusion as a sensitivity view.

Stress features are modular sidecars keyed by `cell_id`, `checkup_k`, and
`checkup_k_next`. The v1.1 sidecar uses timestamp-weighted dwell, coverage/gap
diagnostics, current-sign audit evidence, and scalar event summaries. Target
derived diagnostics such as capacity loss per day or EFC are not allowed as
predictive input features.

PULSE targets are also sidecars. The canonical resistance transition target is
RT/50 `delta_pulse_1s_resistance`, with RT/50 `delta_pulse_10ms_resistance` as
a secondary diagnostic. Alignment, direction handling, and missingness are
reported explicitly. PULSE targets remain resistance endpoints and scalar
diagnostic features; future PULSE state and PULSE deltas are not allowed as
capacity inputs.

Allowed claim:

- C12: grouped validation and condition-level reporting are required for
  publishable evidence.

Blocked claims:

- C10: EIS has demonstrated predictive value.
- C11: CBAT architecture is justified.

Source artifacts:

- `docs/REPO_STATUS.md`
- `docs/SCHEMA_REGISTRY.md`
- `docs/LOG_AGE_MONOTONICITY_POLICY.md`
- `docs/PULSE_TARGET_POLICY.md`
- `reports/audit/interval_subset_report.json`
- `reports/audit/stress_feature_v1_1_qa_report.json`
- `reports/audit/pulse_qa_report.json`

Figure/table references:

- Figure 1: data-product architecture.
- Table 1: dataset audit.


Referenced assets: [Figure 1], [Table 1].


## Grouped Validation Protocol


# Methods: Grouped Validation v0

The validation protocol treats the experimental design as 76 parameter-set
conditions with three replicate cells, not 228 independent regimes. Headline
evidence uses grouped validation so that replicates from the same condition do
not appear on both sides of a headline split.

The benchmark uses five grouped split views:

- `condition_fold`;
- `temperature_holdout_fold`;
- `c_rate_holdout_fold`;
- `profile_holdout_fold`;
- `voltage_window_holdout_fold`.

The C-rate, temperature, profile, and voltage-window splits test stressor-axis
generalization. Random row or random cell splits are not used as paper-facing
evidence because they can overstate performance by sharing condition structure
between train and test.

Capacity metrics are reported at row level and condition level. The central
paper-facing metric is condition-mean MAE, with worst-condition MAE used to
identify failure regimes. PULSE resistance baselines use the same grouped split
discipline and report target coverage counts. Paired comparisons, such as prior
PULSE versus F4 or prior PULSE versus strongest non-PULSE, aggregate by
parameter set and bootstrap over parameter-set conditions.

Leakage controls are part of the validation protocol. Inserted LOG_AGE
diagnostics are masked for interval prediction. Target-derived stress rates are
diagnostic only. For capacity prediction, prior `pulse_1s_resistance_k` is
allowed, but future PULSE state and PULSE deltas are forbidden.

Allowed claims:

- C12: grouped validation is required for publishable evidence.
- C03: C-rate holdout is the hardest capacity generalization view.

Blocked claims:

- Random row/cell splits are publishable headline evidence.
- Future PULSE state or PULSE deltas can be used as capacity input features.

Source artifacts:

- `docs/VALIDATION_PROTOCOL.md`
- `reports/audit/split_registry_report.json`
- `reports/synthesis/split_difficulty_summary.csv`

Figure/table references:

- Figure 2: grouped validation design.
- Table 3: split difficulty.


Referenced assets: [Figure 2].


## Capacity Baseline Ladder


# Results: Capacity Baseline Ladder v0

The capacity baseline ladder establishes the first benchmark evidence. L0
persistence provides the reference. Ridge is retained as a linear sanity
baseline. HGB-50 with `F4_state_log_age_scalar` is the main scalar capacity
baseline before stress features and PULSE diagnostics are introduced.

The focused HGB-50 report shows that learning improves over persistence across
capacity targets and split views. For the central C-rate holdout, the best F4
condition-mean MAE values are:

| Target | Split | Best F4 condition-mean MAE |
|---|---|---:|
| `capacity_Ah_k1` | C-rate | `0.125186` |
| `delta_capacity_Ah` | C-rate | `0.101133` |

C-rate remains harder than the condition, temperature, profile, and
voltage-window views. Worst C-rate rows cluster in cold/cool high-C-rate
conditions and wide voltage-window families. This motivates the later
stress-feature and PULSE diagnostic analyses, but it also sets a strict boundary
for claims: later additions must beat strong grouped baselines, not only weak
or persistence baselines.

Allowed claims:

- C03: C-rate holdout is the dominant unresolved capacity generalization
  stressor.
- C12: headline evidence must use grouped validation and condition-level
  summaries.

Blocked claims:

- The baseline generalizes uniformly across stressor axes.
- Quantile HGB outputs are validated as calibrated intervals.

Key numbers:

- HGB F4 C-rate `capacity_Ah_k1`: `0.125186` condition-mean MAE.
- HGB F4 C-rate `delta_capacity_Ah`: `0.101133` condition-mean MAE.
- q10-q90 coverage: about `0.678207`, below nominal 0.8.

Source artifacts:

- `reports/baselines/capacity_hgb50_focused/plots/best_by_target_split.csv`
- `reports/baselines/capacity_hgb50_focused/claim_readiness.md`
- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`

Figure/table references:

- Figure 3: capacity baseline ladder.
- Figure 4: C-rate failure analysis.
- Table 2: model ladder.
- Table 3: split difficulty.

Limitations:

- C-rate holdout has fewer held-out parameter-set conditions than the full
  condition fold.
- Quantile outputs are diagnostic only.


Referenced assets: [Figure 3], [Table 2], [Table 3].


## LOG_AGE Stress-Feature Experiments


# Results: LOG_AGE Stress Features v0

LOG_AGE scalar summaries and stress features were tested after the baseline
capacity ladder. The central question was whether actual operating-history
features improve held-out generalization beyond state/time and nominal protocol
features, especially on the C-rate split.

The scalar LOG_AGE F4 result is mixed. The adjacent HGB feature gain from
`F3_state_nominal` to `F4_state_log_age_scalar` has mean gain `0.000085`,
median gain `0.001124`, and positive rows in `10 / 20` primary views. This
supports cautious wording: current scalar LOG_AGE summaries help nonlinear
models in some grouped views, but gains are mixed.

The v1/v1.1 stress-feature path added voltage, temperature, SOC, current,
coupled-stress, timestamp-weighted dwell, current-sign audit, and scalar event
features. It improved several condition and temperature views and improved
C-rate `capacity_Ah_k1` from F4 `0.125186` to `0.120605`. However, C-rate
`delta_capacity_Ah` did not beat the F4 threshold:

| Target | F4 baseline | Best v1.1 stress row | Outcome |
|---|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.120605` | improved but below materiality threshold |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.102516` | not supported |

Milestone 0.6.3 then tested normalized delta-rate targets, train-fold residual
correction, and narrow cold/current feature groups. None beat the F4 C-rate
`delta_capacity_Ah` threshold.

Allowed claims:

- C01: current scalar LOG_AGE summaries help nonlinear models in some grouped
  views, but gains are mixed.
- Stress features are useful diagnostics and help some folds.

Blocked claims:

- C02: LOG_AGE stress features solve C-rate fade prediction.

Key numbers:

- F3 to F4 mean gain: `0.000085`, positive rows `10 / 20`.
- v1.1 C-rate `capacity_Ah_k1`: `0.120605`.
- v1.1 C-rate `delta_capacity_Ah`: `0.102516` versus F4 `0.101133`.

Source artifacts:

- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`
- `docs/experiments/2026-05-22_log_age_stress_features_v1_1.md`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`
- `reports/synthesis/negative_results.md`

Figure/table references:

- Figure 5: LOG_AGE stress-feature decision.
- Table 5: negative results.

Limitations:

- Stress features are scalar interval summaries, not sequence models.
- The C-rate fade result remains unresolved.


Referenced assets: [Figure 5], [Table 5].


## PULSE QA and Resistance Baseline


# Results: PULSE QA And Resistance Baseline v0

PULSE was opened as a QA-first scalar resistance endpoint after the LOG_AGE-only
C-rate delta path failed to beat the F4 threshold. The canonical target policy
uses RT/50 `delta_pulse_1s_resistance` as the first transition target and
RT/50 `delta_pulse_10ms_resistance` as a secondary diagnostic target.

PULSE target robustness checks support the canonical RT/50 endpoint for scalar
diagnostics. Alignment sensitivity, direction handling, and missingness remain
part of the reporting package. The current RT/50 `mean` extraction is
effectively charge-direction for adjacent interval deltas because finite
discharge adjacent deltas are unavailable.

Target robustness results:

| Target | C-rate best MAE | Condition-fold best MAE | Interpretation |
|---|---:|---:|---|
| `delta_pulse_1s_resistance` | `0.00185842` | `0.000960407` | canonical transition target |
| `delta_pulse_10ms_resistance` | `0.00180642` | `0.000910676` | viable secondary diagnostic |
| `pulse_1s_resistance_k1` | `0.00189616` | `0.00104973` | state-tracking target |
| `pulse_10ms_resistance_k1` | `0.00179792` | `0.00105917` | state-tracking target |

Allowed claims:

- C04: canonical RT/50 PULSE is robust enough for scalar resistance-baseline
  diagnostics.
- PULSE resistance is predictable enough for scalar baseline diagnostics.

Blocked claims:

- PULSE target robustness proves broad capacity+PULSE multimodal modeling.
- Direction-specific claims from discharge RT/50 adjacent deltas.

Source artifacts:

- `docs/PULSE_TARGET_POLICY.md`
- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`
- `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`

Figure/table references:

- Figure 6: PULSE QA and coverage.
- Figure 7: PULSE resistance baseline.

Limitations:

- Alignment deltas and missing canonical endpoints must remain disclosed.
- RT/50 `mean` is effectively charge in the current adjacent-delta extraction.


Referenced assets: [Figure 6], [Figure 7].


## Capacity-PULSE Coupling Diagnostics


# Results: Capacity-PULSE Coupling v0

Capacity-PULSE coupling diagnostics test whether PULSE resistance growth helps
explain capacity-model residuals. This is an explanatory diagnostic, not a
capacity+PULSE architecture claim.

The robust coupling analysis filters to canonical
`L2_hist_gradient_boosting + F4_state_log_age_scalar` capacity predictions and
checks interval-level, condition-level, bootstrap, subgroup, and residualized
correlations. PULSE growth remains associated with capacity residual magnitude,
especially in the C-rate split.

Key C-rate interval-level correlations:

| Target | Residual type | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | absolute residual | 143 | `0.857653` | `0.633959` |
| `delta_capacity_Ah` | absolute residual | 143 | `0.647125` | `0.646779` |

The prior-PULSE predictive tests then ask whether prior PULSE state improves
capacity prediction. Against F4, prior PULSE improves `capacity_Ah_k1` in
selected grouped splits:

| Split | Best prior-PULSE group | Mean gain vs F4 | p05 |
|---|---|---:|---:|
| C-rate | `C_P3_stress_pulse` | `0.00669208` | `0.000718651` |
| temperature | `C_P3_stress_pulse` | `0.00509620` | `0.00103230` |
| profile | `C_P0_state_time_pulse` | `0.0214905` | `0.0137834` |

The strongest-non-PULSE comparison blocks a stronger claim. C-rate
`capacity_Ah_k1` gain versus `F5_log_age_histograms` is only `0.000392605` with
p05 `-0.00553843`; temperature/profile mean gains are negative. C-rate
`delta_capacity_Ah` remains unsupported.

Allowed claims:

- C05: PULSE growth is associated with capacity residual magnitude, especially
  in C-rate views.
- C06: prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped
  splits.

Blocked claims:

- C07: prior PULSE beats the strongest supplied non-PULSE capacity baseline.
- C08: prior PULSE improves `delta_capacity_Ah`.
- PULSE growth is causal or independent of confounding.

Source artifacts:

- `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`
- `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`
- `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`

Figure/table references:

- Figure 8: capacity residual versus PULSE growth.
- Figure 9: prior PULSE versus strongest non-PULSE.
- Table 4: claim matrix.

Limitations:

- Coupling is explanatory, not causal.
- Prior PULSE does not solve fade-rate prediction.
- Strongest non-PULSE baselines remain competitive or better.


Referenced assets: [Figure 8], [Figure 9].


## Negative Results and Limitations


# Discussion: Negative Results v0

The negative results are part of the contribution because they prevent the
benchmark from becoming an overclaiming exercise.

## LOG_AGE Stress Features

The stress-feature path improved some condition and temperature metrics, but it
did not solve C-rate `delta_capacity_Ah`. The v1.1 C-rate `delta_capacity_Ah`
best stress row was `0.102516`, worse than the F4 threshold `0.101133`.
Normalized delta-rate targets, train-fold residual correction, and F11-F13
cold/current feature groups did not reverse that conclusion.

Interpretation: scalar stress summaries provide useful diagnostic signal, but
the current formulation is not sufficient for C-rate fade prediction.

## Prior PULSE

Prior PULSE state improved `capacity_Ah_k1` over F4 in selected grouped splits,
but did not beat the strongest supplied non-PULSE baselines. It also did not
improve C-rate `delta_capacity_Ah`.

Interpretation: prior PULSE is useful as a capacity-level diagnostic feature in
defined comparisons, but it is not the best current feature path and does not
support a fade-rate claim.

## Quantile HGB

The q10-q90 interval coverage was about `0.678207`, below the nominal central
0.8 interval.

Interpretation: quantile outputs are diagnostic and cannot be described as
validated calibrated intervals.

## EIS

EIS products exist in the data-product stack, but EIS valid-frequency QA and
predictive tests are not complete.

Interpretation: EIS remains a future gated modality and should not be included
in current performance claims.

Allowed claims:

- Negative results constrain the paper's claim ladder.
- The current benchmark is useful because it identifies what does not yet work
  under grouped validation.

Blocked claims:

- Stress features solve C-rate fade prediction.
- Prior PULSE supports a capacity fade-rate claim.
- Quantile HGB provides validated calibrated intervals.
- EIS has demonstrated predictive value.

Source artifacts:

- `reports/synthesis/negative_results.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `reports/synthesis/reviewer_risk_register.md`

Figure/table references:

- Table 5: negative results.
- Figure 10: claim ladder.


Referenced assets: [Table 5].


## Limitations


# Limitations v0

The benchmark is deliberately conservative. Its limitations should appear in
the abstract, discussion, and figure captions where relevant.

## C-Rate Condition Count

C-rate holdout is central to the story, but several C-rate analyses use only 12
held-out parameter-set conditions and 143 PULSE-covered C-rate intervals. Claims
therefore need condition-level aggregation, bootstrap intervals where available,
and cautious wording.

## PULSE Alignment And Direction Policy

PULSE alignment sensitivity is quantified, but alignment remains a reporting
sensitivity rather than a perfect temporal guarantee. The current RT/50 `mean`
target is effectively charge-direction for adjacent interval deltas because
finite discharge adjacent deltas are unavailable.

## LOG_AGE And PULSE Leakage Risk

The repo explicitly masks inserted LOG_AGE diagnostics, excludes target-derived
stress rates from predictive feature groups, and forbids future PULSE state or
PULSE deltas as capacity inputs. The manuscript must keep diagnostic variables
separate from predictive features.

## Fade-Rate Prediction

The benchmark has stronger evidence for capacity level than for
`delta_capacity_Ah`. LOG_AGE stress features, normalized rate targets, residual
correction, and prior PULSE do not solve C-rate fade prediction.

## Quantile Calibration

HGB quantile outputs are not calibrated. The paper can report quantile
diagnostics only if it labels them as uncalibrated.

## EIS And CBAT

EIS is not tested as a predictive modality in the current evidence set. CBAT,
neural/sequence models, and policy ranking remain blocked.

## Counterfactual And Causal Limits

The benchmark is based on grouped observational experimental conditions, not
same-cell counterfactual interventions. PULSE growth correlations are
explanatory diagnostics, not causal proof.

Source artifacts:

- `reports/synthesis/reviewer_risk_register.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `docs/VALIDATION_PROTOCOL.md`

Forbidden wording:

- "validated calibrated intervals";
- "EIS has demonstrated predictive benefit";
- "PULSE supports fade-rate prediction";
- "CBAT has been validated";
- "same-cell counterfactual".


Referenced assets: [Figure 10].
