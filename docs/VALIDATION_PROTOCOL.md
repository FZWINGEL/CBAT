# Validation Protocol

Milestone 0.5/0.5b/0.5c/0.6/0.6.1/0.6.2/0.6.3 authorizes only scalar capacity baseline work on
interval features. Milestone 0.5b is review and robustness hardening. Milestone
0.5c is synthesis and stress-feature decision work. Milestone 0.6 adds
capacity-only LOG_AGE-derived scalar stress features. Milestone 0.6.1 hardens
those features with current-sign audit evidence, timestamp-weighted dwell, and
event-segmented scalar summaries. Milestone 0.6.2 audits target consistency and
C-rate failure modes without adding new modalities or model classes. Milestone
0.6.3 permits normalized delta-rate target diagnostics, train-fold residual
bias-correction diagnostics, and narrow cold/current stress feature groups.
These milestones are not modality or architecture expansions.

Milestone 0.7 opens PULSE as a separate QA-first resistance endpoint. It
authorizes PULSE QA, canonical PULSE target extraction, PULSE interval target
tables, and scalar grouped PULSE resistance baselines. Milestone 0.7.1 hardens
that endpoint with alignment-threshold sensitivity, direction-specific target
tables, canonical-target missingness reports, and scalar resistance baseline
sensitivity runs. Milestone 0.7.2 evaluates secondary PULSE targets and
claim-readiness for scalar resistance baselines. Milestone 0.8 authorizes
capacity-PULSE scalar coupling diagnostics and prior-PULSE capacity baseline
feature checks. Milestone 0.8.1 authorizes robustness checks for those coupling
diagnostics: canonical-model selection, interval-level aggregation,
condition-level aggregation, parameter-set bootstrap summaries, and simple
confound-control residualization. Milestone 0.9 authorizes only a narrow
non-neural prior-PULSE predictive baseline for `capacity_Ah_k1`, using prior
PULSE state at check-up `k` only and paired grouped comparisons. It does not
authorize EIS modeling, future PULSE state, PULSE deltas as capacity inputs,
broad capacity+PULSE multimodal claims, sequence models, neural models, policy
ranking, or CBAT. Milestone 0.9.1 compares prior-PULSE groups against the
strongest supplied non-PULSE HGB baselines before strengthening the 0.9 claim.
Milestone 1.0 is evidence synthesis and paper-claim lock. It authorizes only
documentation, claim ledgers, figure/table planning, negative-result summaries,
and source-artifact cross-checks. It does not authorize new model training, new
feature engineering, EIS modeling, broad multimodal claims, sequence models,
neural models, policy ranking, or CBAT.
Milestone 1.0.1 is paper artifact QA and manuscript packaging. It authorizes
claim wording refinement, source-artifact checklists, figure/table packaging,
manuscript outline tightening, and reviewer-risk registers. It still does not
authorize new model training, feature engineering, EIS modeling, neural models,
sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 1.1 is manuscript draft package v0.1. It authorizes draft prose,
figure/table specifications, claim-to-section mapping, source traceability, and
reviewer-risk mitigation prose. It is still paper-first work only and does not
authorize new model training, feature engineering, EIS modeling, neural models,
sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 1.2 is figure/table generation and manuscript v0.2 assembly. It
authorizes only generated figures/tables from existing tracked artifacts,
caption drafting, continuous manuscript assembly, source-traceability checks,
and no-overclaim checks. It still does not authorize new model training, new
feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.3 is manuscript v0.3 polish and figure QA. It authorizes manuscript
prose polish, generated figure/table QA, source traceability hardening,
caption/table wording cleanup, and expanded no-overclaim checks across
paper-facing manuscript files. It still does not authorize new model training,
new feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.4 is reader-facing manuscript v0.4 and publication figure pass. It
authorizes reader-facing manuscript assembly, figure/caption polish from
existing artifacts, traceability sidecar updates, and reader-facing
no-overclaim checks. It still does not authorize new model training, new
feature engineering, EIS modeling, neural models, sequence models, policy
ranking, CBAT, or broad multimodal claims.
Milestone 1.4.1 is reader-facing cleanup and check hardening. It authorizes
only removal of remaining internal scaffold language, reader-check hardening,
caption/figure wording cleanup, and no-overclaim checks. It still does not
authorize new model training, new feature engineering, EIS modeling, neural
models, sequence models, policy ranking, CBAT, or broad multimodal claims.
Milestone 2.0 is EIS QA and feature gate. It authorizes EIS coverage
diagnostics, spectrum-quality summaries, valid-frequency mask audits,
alignment-threshold sensitivity, the EIS feature policy, E0/E1/E2/E3 scalar
feature table construction, feature QA, and EIS claim-readiness reporting. It
does not authorize EIS predictive modeling, EIS embeddings, DRT features,
capacity+PULSE+EIS multimodal models, neural models, sequence models, policy
ranking, CBAT, or any EIS improvement claim.
Milestone 2.1 is EIS scalar diagnostic baselines. It authorizes EIS interval
target tables, EIS scalar target QA, non-neural scalar EIS baselines, and
prior-EIS feature groups for PULSE/capacity baselines using check-up `k` EIS
features only. It does not authorize DRT, EIS embeddings, future EIS state or
EIS deltas as capacity/PULSE inputs, neural models, sequence models, CBAT,
policy ranking, capacity+PULSE+EIS multimodal models, or broad EIS improvement
claims.
Milestone 2.1.1 hardens scalar EIS claims with strongest non-EIS comparisons,
parameter-set bootstrap intervals, alignment sensitivity, feature-completeness
sensitivity, and leakage audits. Milestone 2.2 authorizes semi-empirical
stress comparators and condition-triplet replicate uncertainty diagnostics. It
does not authorize neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, capacity+PULSE+EIS architecture work, or causal/mechanistic
overclaims.
Milestone 2.3 authorizes grouped capacity calibration diagnostics:
split-conformal intervals, stressor-family conformal intervals, replicate-aware
hybrid intervals, coverage/width reports, and calibration claim-readiness. It
does not authorize neural models, sequence models, CBAT, DRT, EIS embeddings,
policy ranking, capacity+PULSE+EIS architecture work, causal/mechanistic
claims, or calibrated uncertainty claims unless grouped coverage passes without
test-residual leakage.
Milestone 2.4 authorizes LOG_AGE-derived run-event data products,
event-segmentation QA, interval sequence-feature sidecars, shuffled-order
falsification controls, and aggregate-versus-order-aware non-neural grouped
capacity baselines. It does not authorize neural sequence models,
transformers, CBAT, DRT, EIS embeddings, policy ranking,
capacity+PULSE+EIS architecture work, causal/mechanistic claims, or sequence
model readiness claims unless order-aware features beat aggregate and shuffled
controls under grouped validation.
Milestone 2.5 authorizes capacity trajectory extraction, knee detector
implementation, detector agreement diagnostics, x-axis and smoothing
sensitivity, replicate-triplet knee consistency, exploratory knee-risk labels,
and knee claim-readiness reporting. It does not authorize knee prediction
models, neural models, sequence models, transformers, CBAT, policy ranking,
causal/mechanistic claims, or same-cell counterfactual claims.
Milestone 2.5.1 authorizes knee-label forensics, stable-condition registry
generation, threshold-event label stability diagnostics, and knee-vs-threshold
target-readiness comparisons. It still does not authorize knee prediction
models or any early-warning claim without a later grouped prediction gate.
Milestone 2.6 authorizes prospective threshold-event warning table
construction, threshold-warning QA, non-neural classification baselines,
grouped warning evaluation, leakage audits, and calibration diagnostics for
`capacity_below_80pct_initial`. It does not authorize detector-knee
prediction, neural/sequence models, CBAT, policy ranking, causal claims,
same-cell counterfactual claims, or future interval exposure leakage.
Milestone 3.0 authorizes technical evidence synthesis after all main-project
gates through threshold-warning finalization. It does not authorize new models,
new feature engineering, neural/sequence models, CBAT, DRT, EIS embeddings,
policy ranking, causal claims, same-cell counterfactual claims, or broad
multimodal claims.
Milestone 3.1 authorizes benchmark release and reproducibility hardening:
runbooks, command DAGs, artifact manifests, release-candidate checks,
source-consistency checks, and Codex/developer operating guidance. It does not
authorize new model training, new feature engineering, neural models, sequence
models, transformers, CBAT, DRT, EIS embeddings, policy ranking,
causal/mechanistic claims, same-cell counterfactual claims, or broad multimodal
claims.
Milestone 3.2 authorizes executable benchmark release-candidate validation,
artifact-manifest checks, command-DAG checks, release notes, tag-preparation
docs, no-data-staged checks, and source-consistency checks. It does not
authorize new model training, new feature engineering, neural models, sequence
models, transformers, CBAT, DRT, EIS embeddings, policy ranking,
detector-knee prediction, calibrated risk claims, causal/mechanistic claims,
same-cell counterfactual claims, or broad multimodal claims.
Milestone 3.3 authorizes release polish and GitHub release drafting after the
validated `benchmark-v0.1-rc1` checkpoint. `benchmark-v0.1-rc2` is the
reviewer-facing release archive that includes handoff documents while
preserving rc1 as the validation checkpoint. It authorizes handoff summaries,
release-draft text, final release checklists, and future-branch organization
notes. It does not authorize new model training, new feature engineering,
neural models, sequence models, transformers, CBAT, DRT, EIS embeddings,
policy ranking, detector-knee prediction, calibrated risk claims, causal
claims, same-cell counterfactual claims, or broad multimodal claims.
Milestone 4.0 authorizes manuscript v0.5 benchmark integration from tracked
evidence only. It authorizes reader-facing prose, traceability sidecars,
figure/table refreshes, captions, and no-overclaim checks. It does not
authorize new model training, new feature engineering, neural models, sequence
models, transformers, CBAT, DRT, EIS embeddings, policy ranking,
detector-knee prediction, calibrated risk claims, causal claims,
same-cell counterfactual claims, or broad multimodal claims.
Milestone 4.1 authorizes venue-neutral manuscript v0.6 reviewer-package work
from tracked evidence only. It authorizes reader-facing prose tightening,
supplement scaffolding, figure/table mapping, traceability sidecars, and
manuscript package checks. It does not authorize new model training, new
feature engineering, neural models, sequence models, transformers, CBAT, DRT,
EIS embeddings, policy ranking, detector-knee prediction, calibrated risk
claims, causal claims, same-cell counterfactual claims, or broad multimodal
claims.
Milestone 4.2 authorizes reviewer-risk hardening and submission preflight from
tracked evidence only. It authorizes reviewer-risk registers, response-prep
documents, v0.7 manuscript/supplement tightening, package manifests, and
preflight checks. It does not authorize new model training, new feature
engineering, neural models, sequence models, transformers, CBAT, DRT, EIS
embeddings, policy ranking, detector-knee prediction, calibrated risk claims,
causal claims, same-cell counterfactual claims, or broad multimodal claims.
Milestone 4.3 authorizes venue-neutral submission-bundle and external handoff
work from tracked evidence only. It authorizes title/abstract variants,
cover-letter draft text, data/code availability wording, figure/table
inventories, submission checklists, benchmark/manuscript handoff notes, and
release/manuscript package consistency checks. It does not authorize new model
training, new feature engineering, neural models, sequence models,
transformers, CBAT, DRT, EIS embeddings, policy ranking, detector-knee
prediction, risk-score calibration claims, causal claims, same-cell
counterfactual claims, broad multimodal claims, or any new scientific claim.
Milestone 4.4 authorizes public-facing repository entry point and submission
metadata triage work from tracked evidence only. It authorizes README refresh,
package-description alignment, public-review entry point documentation,
repository metadata checklists, venue-targeting matrices, and submission
readiness triage. It does not authorize new model training, new feature
engineering, neural models, sequence models, transformers, CBAT, DRT, EIS
embeddings, policy ranking, detector-knee prediction, risk-score calibration
claims, causal claims, same-cell counterfactual claims, broad multimodal
claims, or any new scientific claim.
Milestone 5.0 authorizes only grouped threshold-warning probability
calibration for the existing `capacity_below_80pct_initial` warning baseline.
It may fit non-neural post-hoc calibrators on calibration conditions drawn
from the non-test side of each grouped split. It may compare raw HGB W2,
Platt/logistic calibration, and isotonic calibration under all-row and
verified-only label policies. It does not authorize new feature engineering,
detector-knee prediction, policy ranking, CBAT, neural/sequence models, causal
claims, same-cell counterfactual claims, or calibrated-risk wording unless
both grouped and C-rate calibration guardrails pass without leakage.
Milestone 5.1 authorizes only non-neural stressor-axis robust capacity
baselines over existing capacity feature groups. It may fit reference HGB,
condition-balanced HGB, stressor-balanced HGB, condition-bagged HGB, and
train-only internal condition-selected HGB variants under the existing grouped
split views. It may compare C-rate `delta_capacity_Ah` gains against F4 and
the strongest stress-feature R0 references and must require paired
condition-level bootstrap support plus non-degradation outside C-rate before
any robust-capacity wording is strengthened. It does not authorize new feature
engineering, neural/sequence models, CBAT, DRT, EIS embeddings, policy
ranking, calibrated-risk wording, calibrated-uncertainty wording, causal
claims, same-cell counterfactual claims, or broad multimodal claims.
Milestone 5.2 authorizes only calibration metric sensitivity and quantile
endpoint hygiene for existing reports. It may add equal-frequency ECE alongside
fixed-width ECE for threshold-warning baseline, censoring, final-claim, and
probability-calibration diagnostics. It may enforce noncrossing q10/q50/q90
endpoints for independently fitted L3 capacity quantile HGB models by row-wise
post-sort, provided the q50 point prediction is preserved. It may rerun the
existing threshold-warning and capacity calibration reports to refresh metrics.
It does not authorize new feature engineering, new model families, neural or
sequence models, CBAT, DRT, EIS embeddings, policy ranking, calibrated-risk
wording, calibrated-uncertainty wording, causal claims, same-cell
counterfactual claims, robust-capacity wording, or broad multimodal claims.
Milestone 5.3 authorizes correctness hardening of existing calibration and
stressor-robustness gates only. It may fix readiness logic, empty-run guards,
schema metadata, label-policy-specific C-rate checks, fallback-row handling,
calibration partition edge cases, and stressor-robust bagging/selection hygiene
when those fixes prevent silent false support. It may rerun the affected
threshold-warning calibration and stressor-robust capacity reports. It does not
authorize new model families, new feature engineering, neural or sequence
models, CBAT, DRT, EIS embeddings, policy ranking, calibrated-risk wording,
calibrated-uncertainty wording, causal claims, same-cell counterfactual claims,
robust-capacity wording, or broad multimodal claims.
Milestone 5.4 authorizes only stressor-robust capacity forensics and a bounded
Pareto diagnostic grid over the existing non-neural robust HGB variants and
existing F4/F8 feature groups. It may render split/condition degradation
forensics, evaluate predeclared reweighting strengths and bag counts, and
report non-degradation threshold sensitivity. It must keep the predeclared 5%
outside-C-rate non-degradation guardrail intact; lighter or otherwise
non-predeclared settings that pass are diagnostic only. It does not authorize
new feature engineering, neural or sequence models, CBAT, DRT, EIS embeddings,
policy ranking, calibrated-risk wording, calibrated-uncertainty wording,
causal claims, same-cell counterfactual claims, robust-capacity support unless
the predeclared setting passes, or broad multimodal claims.
Milestone 5.5 authorizes only train-only adaptive stressor-robust selection
inside the existing non-neural R2 stressor-balanced HGB family and existing
F4/F8 feature groups. It may use inner grouped validation on the outer training
rows to select a reweighting strength, then evaluate the selected setting on
the untouched outer held-out rows. It must keep the 5% outside-C-rate
non-degradation guardrail unchanged and must report both max-gain and
conservative selection policies if evaluated. It does not authorize new
feature engineering, neural or sequence models, CBAT, DRT, EIS embeddings,
policy ranking, calibrated-risk wording, calibrated-uncertainty wording,
causal claims, same-cell counterfactual claims, C-rate fade-solved wording, or
broad multimodal claims.
Milestone 5.6 authorizes only replication and final claim hardening for the
Milestone 5.5 adaptive stressor-robust selector. It may replicate the
conservative and max-gain selector policies across deterministic seeds, record
deterministic seed reuse when the HGB/no-bagging path is seed-invariant, audit
outer train/test and inner train/validation condition separation, and render
seed/policy sensitivity tables. It must keep the unchanged 5% outside-C-rate
non-degradation guardrail and must not introduce new feature engineering,
new model families, neural or sequence models, CBAT, DRT, EIS embeddings,
policy ranking, calibrated-risk wording, calibrated-uncertainty wording,
causal claims, same-cell counterfactual claims, C-rate fade-solved wording, or
broad multimodal claims.
Milestone 5.7 authorizes only stressor-robust attribution decomposition over
the existing non-neural R0/R2 HGB family and existing F4/F8 feature groups. It
may compare R0/F4, R0/F8, adaptive R2/F4, and adaptive R2/F8 arms under the
existing grouped splits, decompose reweighting-only versus F8
timestamp-weighted stress-feature gains, and audit that adaptive selections use
only outer-training rows. It must keep the unchanged 5% outside-C-rate
non-degradation guardrail. It does not authorize new feature engineering, new
model families, neural or sequence models, CBAT, DRT, EIS embeddings, policy
ranking, calibrated-risk wording, calibrated-uncertainty wording, causal
claims, same-cell counterfactual claims, C-rate fade-solved wording, or broad
multimodal claims.
Milestone 5.8 authorizes only a targeted stressor-family router over existing
Milestone 5.7 attribution arms and predictions. The router may use D2
adaptive R2/F4 for the C-rate transfer view when its train-only adaptive
guardrail passes, and D0 R0/F4 for non-C-rate stressor views. It may
recombine existing outer-fold attribution predictions to avoid redundant model
fits. It must keep the unchanged 5% outside-C-rate non-degradation guardrail
and must not be described as broad robust-capacity support, solved C-rate
fade, F8 attribution support, architecture readiness, policy ranking,
calibrated-risk wording, calibrated-uncertainty wording, causal claims,
sequence/neural modeling, CBAT, or broad multimodal claims.

Required split discipline:

- Primary evidence uses condition-level grouped splits.
- Replicates from the same parameter-set condition remain together for headline
  claims.
- Random row/cell splits are leakage smoke tests only and are not part of the
  Milestone 0.5 baseline report.
- LOG_AGE inserted diagnostics must remain masked for interval prediction.
- Baseline code must consume `interval_subset_registry_v1.parquet`.
- The primary capacity run uses `baseline_clean_tolerant`.
- Every baseline report must include a sensitivity run excluding
  `sensitivity_flagged_monotonicity == true`.

Required Milestone 3.1 release-hardening artifacts:

- `docs/BENCHMARK_REPRODUCIBILITY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/BENCHMARK_ARTIFACTS.md`
- `docs/BENCHMARK_RELEASE_CHECKLIST.md`
- `docs/COMMAND_DAG.md`
- `docs/CODEX_NEXT_WORK.md`
- `reports/synthesis/artifact_manifest_v2.csv`
- `reports/synthesis/reproducibility_gate_status.md`
- `reports/synthesis/release_candidate_check.md`
- `docs/experiments/2026-05-23_benchmark_release_reproducibility.md`

Required Milestone 3.2 release-candidate validation artifacts:

- `mbp report check-release-candidate`
- `docs/RELEASE_NOTES_v0.1-rc1.md`
- `docs/TAGGING_RELEASE_CANDIDATE.md`
- updated `docs/BENCHMARK_RELEASE_CHECKLIST.md`
- updated `reports/synthesis/release_candidate_check.md`
- `docs/experiments/2026-05-23_benchmark_v0_1_rc_validation.md`

Required Milestone 3.3 release-polish artifacts:

- `docs/BENCHMARK_V0_1_RC1_SUMMARY.md`
- `docs/BENCHMARK_V0_1_RC2_SUMMARY.md`
- `reports/synthesis/benchmark_v0_1_rc1_handoff_check.md`
- `reports/synthesis/benchmark_v0_1_rc2_handoff_check.md`

Required Milestone 5.1 stressor-robust capacity artifacts:

- `src/mbp/baselines/stressor_robust_capacity.py`
- `mbp baseline run-stressor-robust-capacity`
- `mbp baseline diagnose-stressor-robustness`
- `reports/baselines/capacity_stressor_robust_hgb50_report.json`
- `reports/baselines/capacity_stressor_robust_hgb50/robustness_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/paired_condition_gains.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/c_rate_robustness_summary.md`
- `reports/baselines/capacity_stressor_robust_hgb50/stressor_robustness_claim_readiness.md`
- `docs/experiments/2026-05-24_stressor_robust_capacity_gate.md`

Required Milestone 5.2 calibration/quantile hygiene artifacts:

- additive `ece_10_bin_equal_freq` fields in threshold-warning report outputs
- noncrossing L3 capacity quantile endpoints in `mbp baseline run-capacity`
- refreshed `reports/baselines/threshold_warning_l0_l2_report.json`
- refreshed `reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md`
- refreshed `reports/baselines/threshold_warning_calibration_report.json`
- refreshed `reports/baselines/threshold_warning_calibration/c_rate_calibration_summary.md`
- refreshed `reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md`
- refreshed `reports/baselines/capacity_hgb50_focused_report.json`
- refreshed `reports/analysis/calibration_capacity/calibration_claim_readiness.md`
- `docs/experiments/2026-05-24_calibration_quantile_hygiene.md`
- `docs/GITHUB_RELEASE_DRAFT_v0.1-rc1.md`
- `docs/GITHUB_RELEASE_DRAFT_v0.1-rc2.md`
- optional `docs/FUTURE_BRANCHES.md`

Required Milestone 5.3 correctness-hardening artifacts:

- fixed threshold-warning calibration readiness gate requiring both all-row and
  verified-only policies
- policy-specific C-rate calibration readiness summary
- fallback-raw calibration rows blocked from strict passing status
- unpenalized Platt/logistic calibration convention
- calibration prediction Parquet schema metadata
- no-empty-metric guards for affected runners
- fixed stressor-robust non-degradation missing-evidence handling
- stable stressor-robust bagging encoder and balanced per-condition row draws
- explicit stressor-robust R4 tie-break policy
- refreshed `reports/baselines/threshold_warning_calibration_report.json`
- refreshed `reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md`
- refreshed `reports/baselines/capacity_stressor_robust_hgb50_report.json`
- refreshed `reports/baselines/capacity_stressor_robust_hgb50/stressor_robustness_claim_readiness.md`
- `docs/experiments/2026-05-24_calibration_robustness_correctness_hardening.md`

Required Milestone 5.4 stressor-robust Pareto/forensics artifacts:

- `mbp baseline diagnose-stressor-robust-forensics`
- `mbp baseline run-stressor-robust-pareto`
- `reports/baselines/capacity_stressor_robust_hgb50/stressor_failure_forensics.md`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/degradation_by_split_target_feature.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/degradation_by_condition.csv`
- `reports/baselines/capacity_stressor_robust_hgb50/plots/worst_regression_conditions.csv`
- `reports/baselines/capacity_stressor_robust_pareto_report.json`
- `reports/baselines/capacity_stressor_robust_pareto/robustness_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_pareto/paired_condition_gains.csv`
- `reports/baselines/capacity_stressor_robust_pareto/plots/pareto_frontier.csv`
- `reports/baselines/capacity_stressor_robust_pareto/plots/non_degradation_threshold_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_pareto/stressor_robust_pareto_claim_readiness.md`
- `docs/experiments/2026-05-24_stressor_robust_pareto_forensics.md`

Milestone 5.4 claim rules:

- If the predeclared R2/F8/weight=1.0 setting passes C-rate gain, paired p05,
  and <=5% outside-C-rate non-degradation, a narrow robust-capacity diagnostic
  claim may be supported.
- If only lighter or otherwise non-predeclared settings pass, report them as
  Pareto diagnostics only.
- If the predeclared setting fails the 5% guardrail, keep robust-capacity
  support blocked even if the miss is narrow.
- Architecture, policy, causal, calibrated-risk, calibrated-uncertainty,
  sequence/neural, and CBAT claims remain blocked.

Required Milestone 5.5 train-only adaptive stressor-robust artifacts:

- `mbp baseline run-stressor-robust-adaptive`
- `reports/baselines/capacity_stressor_robust_adaptive_report.json`
- `reports/baselines/capacity_stressor_robust_adaptive/stressor_robust_adaptive_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive/plots/adaptive_frontier.csv`
- `reports/baselines/capacity_stressor_robust_adaptive/adaptive_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative_report.json`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/stressor_robust_adaptive_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/plots/adaptive_frontier.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_conservative/adaptive_selection_summary.csv`
- `docs/experiments/2026-05-24_train_only_stressor_robust_adaptive_selection.md`

Milestone 5.5 claim rules:

- If the outer held-out conservative train-only adaptive selector on F8 has
  positive C-rate `delta_capacity_Ah` gain versus F4 and stress R0 references,
  paired p05 above zero for both references, and <=5% outside-C-rate
  degradation, a narrow adaptive robust-selection diagnostic claim may be
  supported.
- If a max-gain selector improves C-rate but fails the 5% guardrail, report it
  as a failed high-gain policy, not as a supported robustness result.
- A passing adaptive diagnostic does not imply that C-rate fade is solved
  globally, that probability/risk outputs are calibrated, that policy ranking
  is valid, or that architecture work is justified.

Required Milestone 5.6 adaptive replication artifacts:

- `mbp baseline replicate-stressor-robust-adaptive`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/replication_summary.json`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/adaptive_replication_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/seed_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/policy_sensitivity.csv`
- `reports/baselines/capacity_stressor_robust_adaptive_replication/plots/outside_split_degradation.csv`
- `docs/experiments/2026-05-24_adaptive_stressor_robust_replication.md`

Milestone 5.6 claim rules:

- Replicated diagnostic support requires every required conservative guarded
  logical seed to pass positive C-rate gain versus F4 and stress R0
  references, positive paired p05 against both references, <=5%
  outside-C-rate degradation, and a passed leakage audit.
- Deterministic seed reuse is permitted only when recorded explicitly and when
  the evaluated path has no stochastic bagging or held-out-data-dependent
  selection. The report must list the effective fit seed and logical seeds.
- If the max-gain selector improves C-rate but fails the 5% guardrail, it is a
  failed high-gain policy, not a supported robustness result.
- Replicated diagnostic support remains target-specific to
  `delta_capacity_Ah` and does not authorize C-rate fade-solved, architecture,
  calibrated-risk, calibrated-uncertainty, policy, causal, or broad
  multimodal claims.

Required Milestone 5.7 stressor-robust attribution artifacts:

- `mbp baseline run-stressor-robust-attribution`
- `reports/baselines/capacity_stressor_robust_attribution_report.json`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_leaderboard.csv`
- `reports/baselines/capacity_stressor_robust_attribution/attribution_comparisons.csv`
- `reports/baselines/capacity_stressor_robust_attribution/adaptive_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/c_rate_attribution.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/f4_vs_f8_adaptive_gain.csv`
- `reports/baselines/capacity_stressor_robust_attribution/plots/outside_split_degradation.csv`
- `docs/experiments/2026-05-27_stressor_robust_attribution_gate.md`

Milestone 5.7 claim rules:

- Stress-feature attribution support requires adaptive R2/F8 to beat adaptive
  R2/F4 on C-rate `delta_capacity_Ah`, paired p05 above zero, <=5%
  outside-C-rate degradation for that incremental comparison, and a passed
  leakage audit.
- If adaptive R2/F8 improves C-rate but fails outside-C-rate
  non-degradation, the result is attribution-diagnostic only.
- If adaptive R2/F4 explains most or all of the C-rate gain, attribute the
  result to train-only reweighting/selection rather than F8 stress features.
- No Milestone 5.7 outcome authorizes C-rate fade-solved, architecture,
  calibrated-risk, calibrated-uncertainty, policy, causal, sequence/neural,
  CBAT, or broad multimodal claims.

Required Milestone 5.8 stressor-family arm-router artifacts:

- `mbp baseline run-stressor-robust-arm-selector`
- `reports/baselines/capacity_stressor_robust_arm_selector_report.json`
- `reports/baselines/capacity_stressor_robust_arm_selector/arm_selector_claim_readiness.md`
- `reports/baselines/capacity_stressor_robust_arm_selector/arm_selection_summary.csv`
- `reports/baselines/capacity_stressor_robust_arm_selector/plots/c_rate_selector_gain.csv`
- `reports/baselines/capacity_stressor_robust_arm_selector/plots/outside_split_degradation.csv`
- `docs/experiments/2026-05-27_stressor_robust_arm_selector_gate.md`

Milestone 5.8 claim rules:

- Targeted router support requires selector-vs-D0 C-rate `delta_capacity_Ah`
  gain, paired p05 above zero, <=5% outside-C-rate degradation, and a passed
  leakage audit.
- A passing result authorizes only stressor-family routing wording: D2 for
  known C-rate transfer and D0 elsewhere.
- It does not authorize global robust-capacity wording, C-rate fade-solved
  wording, stress-feature attribution, architecture, policy ranking,
  calibrated-risk, calibrated-uncertainty, causal, sequence/neural, CBAT, or
  broad multimodal claims.

Required Milestone 4.0 manuscript-integration artifacts:

- `manuscript/manuscript_v0_5.md`
- `manuscript/manuscript_v0_5_traceability.md`
- refreshed v0.5 figure/table captions
- refreshed generated manuscript figures/tables for post-v0.4 gates
- `manuscript/checks/manuscript_v0_5_claim_check.md`
- `manuscript/checks/manuscript_v0_5_reader_check.md`
- `docs/experiments/2026-05-24_manuscript_v0_5_benchmark_integration.md`

Required Milestone 4.1 reviewer-package artifacts:

- `manuscript/manuscript_v0_6.md`
- `manuscript/manuscript_v0_6_traceability.md`
- `manuscript/supplement_v0_6.md`
- `manuscript/checks/manuscript_v0_6_claim_check.md`
- `manuscript/checks/manuscript_v0_6_reader_check.md`
- `manuscript/checks/manuscript_v0_6_package_check.md`
- `docs/experiments/2026-05-24_manuscript_v0_6_reviewer_package.md`

Required Milestone 4.2 submission-preflight artifacts:

- `reports/synthesis/reviewer_risk_register_v2.md`
- `manuscript/reviewer_response_prep_v2.md`
- `manuscript/submission_preflight_v0_7.md`
- `manuscript/manuscript_v0_7.md`
- `manuscript/manuscript_v0_7_traceability.md`
- `manuscript/supplement_v0_7.md`
- `manuscript/manuscript_package_v0_7_manifest.md`
- `manuscript/checks/manuscript_v0_7_claim_check.md`
- `manuscript/checks/manuscript_v0_7_reader_check.md`
- `manuscript/checks/manuscript_v0_7_package_check.md`
- `docs/experiments/2026-05-24_manuscript_v0_7_submission_preflight.md`

Required Milestone 4.3 submission-bundle artifacts:

- `manuscript/submission_bundle_v0_8.md`
- `manuscript/title_abstract_options_v0_8.md`
- `manuscript/cover_letter_draft_v0_8.md`
- `manuscript/data_code_availability_v0_8.md`
- `manuscript/figure_table_inventory_v0_8.md`
- `manuscript/submission_checklist_v0_8.md`
- `docs/BENCHMARK_MANUSCRIPT_HANDOFF.md`
- `docs/experiments/2026-05-24_submission_bundle_external_handoff.md`

Required Milestone 4.4 public-entrypoint artifacts:

- refreshed `README.md`
- refreshed project description in `pyproject.toml`
- `docs/PUBLIC_REVIEW_ENTRYPOINT.md`
- `docs/REPOSITORY_METADATA_CHECKLIST.md`
- `manuscript/venue_targeting_matrix_v0_9.md`
- `manuscript/submission_readiness_v0_9.md`
- `docs/experiments/2026-05-24_public_entrypoint_submission_metadata.md`

Required Milestone 5.0 threshold-warning probability-calibration artifacts:

- `mbp baseline calibrate-threshold-warning`
- `reports/baselines/threshold_warning_calibration_report.json`
- `reports/baselines/threshold_warning_calibration/calibration_metric_summary.csv`
- `reports/baselines/threshold_warning_calibration/reliability_by_split.csv`
- `reports/baselines/threshold_warning_calibration/reliability_bins.csv`
- `reports/baselines/threshold_warning_calibration/c_rate_calibration_summary.md`
- `reports/baselines/threshold_warning_calibration/threshold_warning_calibration_claim_readiness.md`
- `docs/experiments/2026-05-24_threshold_warning_probability_calibration.md`

Required Milestone 1.0 synthesis artifacts:

- `docs/experiments/2026-05-23_evidence_synthesis.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `docs/PAPER_FIGURE_PLAN.md`
- `docs/PAPER_SKELETON.md`
- `reports/synthesis/claim_matrix.csv`
- `reports/synthesis/evidence_matrix.md`
- `reports/synthesis/model_ladder_summary.csv`
- `reports/synthesis/split_difficulty_summary.csv`
- `reports/synthesis/negative_results.md`

Required Milestone 1.0.1 paper-QA artifacts:

- `docs/MANUSCRIPT_PACKAGE_PLAN.md`
- `reports/synthesis/source_artifact_checklist.md`
- `reports/synthesis/reviewer_risk_register.md`

Required Milestone 1.1 manuscript package artifacts:

- `manuscript/README.md`
- `manuscript/outline.md`
- `manuscript/abstract_v0.md`
- `manuscript/introduction_v0.md`
- `manuscript/methods_data_products_v0.md`
- `manuscript/methods_validation_v0.md`
- `manuscript/results_capacity_baselines_v0.md`
- `manuscript/results_stress_features_v0.md`
- `manuscript/results_pulse_resistance_v0.md`
- `manuscript/results_capacity_pulse_coupling_v0.md`
- `manuscript/discussion_negative_results_v0.md`
- `manuscript/limitations_v0.md`
- `manuscript/source_traceability.md`
- `manuscript/reviewer_response_prep.md`
- `manuscript/figures/*.md`
- `manuscript/tables/*.md`

Required Milestone 1.2 manuscript asset artifacts:

- `manuscript/manuscript_v0_2.md`
- `manuscript/figures/generated/*.svg`
- `manuscript/tables/generated/*.md`
- `manuscript/captions/figure_captions.md`
- `manuscript/captions/table_captions.md`
- `manuscript/checks/manuscript_claim_check.md`
- `manuscript/checks/figure_source_check.md`
- `docs/experiments/2026-05-23_manuscript_v0_2_assets.md`

Required Milestone 1.3 manuscript polish artifacts:

- `manuscript/manuscript_v0_3.md`
- corrected `manuscript/figures/generated/fig06_pulse_qa_coverage.svg`
- `manuscript/checks/figure_data_check.md`
- updated caption files with "what not to infer" notes
- `docs/experiments/2026-05-23_manuscript_v0_3_polish.md`

Required Milestone 1.4 reader-facing artifacts:

- `manuscript/manuscript_v0_4.md`
- `manuscript/manuscript_v0_4_traceability.md`
- `manuscript/captions/figure_captions_v0_4.md`
- `manuscript/captions/table_captions_v0_4.md`
- `manuscript/checks/manuscript_v0_4_claim_check.md`
- `manuscript/checks/manuscript_v0_4_reader_check.md`
- `manuscript/figures/generated_v0_4/*.svg`
- `docs/experiments/2026-05-23_manuscript_v0_4_reader_polish.md`

Required Milestone 1.4.1 cleanup artifacts:

- cleaned `manuscript/manuscript_v0_4.md` without `Forbidden wording:`
- updated `manuscript/manuscript_v0_4_traceability.md` with prose guardrails
- regenerated `manuscript/figures/generated_v0_4/*.svg` without internal draft
  labels
- `docs/experiments/2026-05-23_manuscript_v0_4_1_reader_cleanup.md`

Required Milestone 2.0 EIS QA artifacts:

- `docs/EIS_FEATURE_POLICY.md`
- `reports/audit/eis_qa_report.json`
- `reports/audit/eis_coverage_report.csv`
- `reports/audit/eis_alignment_report.json`
- `reports/audit/eis_alignment_sensitivity_report.json`
- `reports/audit/eis_alignment_sensitivity_coverage.csv`
- `reports/audit/eis_spectrum_quality_summary.csv`
- `reports/audit/eis_valid_frequency_report.csv`
- `data/interim/eis_feature_table_v1.parquet` (ignored generated artifact)
- `reports/audit/eis_feature_qa_report.json`
- `reports/audit/eis_claim_readiness.md`
- `docs/experiments/2026-05-23_eis_qa_feature_gate.md`

Required Milestone 2.1 EIS scalar diagnostic artifacts:

- `data/interim/eis_target_table_v1.parquet` (ignored generated artifact)
- `reports/audit/eis_target_qa_report.json`
- `reports/audit/eis_target_coverage.csv`
- `reports/baselines/eis_scalar_l0_l3_report.json`
- `reports/baselines/eis_scalar_l0_l3/leaderboard.csv`
- `reports/baselines/eis_scalar_l0_l3/baseline_summary.md`
- `reports/baselines/eis_scalar_l0_l3/eis_diagnostics.md`
- `reports/baselines/pulse_with_prior_eis_hgb50_report.json`
- `reports/baselines/capacity_with_prior_eis_hgb50_report.json`
- `reports/baselines/eis_prior_feature_claim_readiness.md`
- `docs/experiments/2026-05-23_eis_scalar_diagnostic_baselines.md`

Required Milestone 2.1.1 EIS claim-hardening artifacts:

- `reports/baselines/pulse_prior_eis_vs_best_noneis/paired_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/split_level_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/bootstrap_gain_vs_best_noneis.csv`
- `reports/baselines/pulse_prior_eis_vs_best_noneis/prior_eis_pulse_claim_readiness.md`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/paired_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/split_level_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/bootstrap_gain_vs_best_noneis.csv`
- `reports/baselines/capacity_prior_eis_vs_best_noneis/prior_eis_capacity_claim_readiness.md`
- `reports/baselines/eis_alignment_sensitivity/pulse_prior_eis_alignment_summary.csv`
- `reports/baselines/eis_alignment_sensitivity/capacity_prior_eis_alignment_summary.csv`
- `reports/baselines/eis_alignment_sensitivity/eis_alignment_claim_readiness.md`
- `reports/baselines/eis_feature_completeness_sensitivity.csv`
- `reports/baselines/eis_feature_completeness_claim_readiness.md`
- `reports/baselines/eis_scalar_l0_l3/eis_self_endpoint_claim_readiness.md`
- `reports/baselines/eis_leakage_audit.md`
- `docs/experiments/2026-05-23_eis_claim_hardening.md`

Required Milestone 2.2 semi-empirical and replicate-gate artifacts:

- `reports/baselines/semi_empirical_capacity_report.json`
- `reports/baselines/semi_empirical_capacity/leaderboard.csv`
- `reports/baselines/semi_empirical_capacity/baseline_summary.md`
- `reports/baselines/semi_empirical_capacity/semi_empirical_claim_readiness.md`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_hgb_f4.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/paired_gain_vs_best_stress.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison_summary.csv`
- `reports/baselines/semi_empirical_capacity/comparisons/semi_empirical_comparison.md`
- `reports/analysis/replicate_uncertainty/replicate_spread_by_condition.csv`
- `reports/analysis/replicate_uncertainty/model_error_vs_replicate_spread.csv`
- `reports/analysis/replicate_uncertainty/condition_tolerance_intervals.csv`
- `reports/analysis/replicate_uncertainty/c_rate_replicate_uncertainty.md`
- `reports/analysis/replicate_uncertainty/replicate_uncertainty_summary.md`
- `reports/analysis/replicate_uncertainty/uncertainty_claim_readiness.md`
- `docs/experiments/2026-05-23_semi_empirical_replicate_gate.md`

Required Milestone 2.3 grouped calibration artifacts:

- `reports/analysis/calibration_capacity/calibration_report.json`
- `reports/analysis/calibration_capacity/coverage_by_split.csv`
- `reports/analysis/calibration_capacity/coverage_by_condition.csv`
- `reports/analysis/calibration_capacity/interval_width_summary.csv`
- `reports/analysis/calibration_capacity/c_rate_calibration_summary.md`
- `reports/analysis/calibration_capacity/calibration_claim_readiness.md`
- `docs/experiments/2026-05-23_grouped_calibration_replicate_uncertainty.md`

Required Milestone 2.4 temporal-history artifacts:

- `reports/audit/run_event_qa_report.json`
- `reports/audit/run_event_coverage.csv`
- `reports/audit/sequence_feature_qa_report.json`
- `reports/baselines/capacity_sequence_value_hgb50_report.json`
- `reports/baselines/capacity_sequence_value_hgb50/sequence_value_diagnostics.md`
- `reports/baselines/capacity_sequence_value_hgb50/sequence_value_claim_readiness.md`
- `reports/baselines/capacity_sequence_value_hgb50/plots/aggregate_vs_order_gain.csv`
- `reports/baselines/capacity_sequence_value_hgb50/plots/order_vs_shuffled_gain.csv`
- `reports/baselines/capacity_sequence_value_hgb50/plots/c_rate_sequence_value.csv`
- `docs/experiments/2026-05-23_temporal_history_value_gate.md`

Required Milestone 2.5 knee-label stability artifacts:

- `reports/analysis/knee/knee_detector_agreement.csv`
- `reports/analysis/knee/knee_label_stability_report.json`
- `reports/analysis/knee/knee_by_condition.csv`
- `reports/analysis/knee/knee_replicate_consistency.csv`
- `reports/analysis/knee/knee_claim_readiness.md`
- `docs/experiments/2026-05-23_knee_label_stability_gate.md`

Required Milestone 2.5.1 knee forensics and threshold-event artifacts:

- `reports/analysis/knee/knee_inconsistent_conditions.csv`
- `reports/analysis/knee/knee_inconsistency_forensics.md`
- `reports/analysis/knee/knee_stable_condition_report.json`
- `reports/analysis/knee/knee_stable_condition_coverage.csv`
- `reports/analysis/knee/threshold_event_stability.csv`
- `reports/analysis/knee/threshold_event_by_condition.csv`
- `reports/analysis/knee/threshold_event_claim_readiness.md`
- `reports/analysis/knee/knee_vs_threshold_decision.md`
- `docs/experiments/2026-05-23_knee_threshold_label_forensics.md`

Required Milestone 2.6 threshold-warning artifacts:

- `reports/analysis/knee/threshold_warning_qa_report.json`
- `reports/analysis/knee/threshold_warning_class_balance.csv`
- `reports/analysis/knee/threshold_warning_split_coverage.csv`
- `reports/baselines/threshold_warning_l0_l2_report.json`
- `reports/baselines/threshold_warning_l0_l2/leaderboard.csv`
- `reports/baselines/threshold_warning_l0_l2/baseline_summary.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_leakage_audit.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_claim_readiness.md`
- `docs/experiments/2026-05-23_threshold_event_warning_baseline.md`

Required Milestone 1.2 checks:

- `mbp report build-manuscript-assets`
- `mbp report check-manuscript`
- `git diff --check`
- `ruff check . --no-cache` and `pytest -p no:cacheprovider` when reporting
  code is added or changed.

Milestone 1.3 `mbp report check-manuscript` must scan the continuous
manuscript, captions, generated tables, figure specifications, and source
traceability file.

Milestone 1.4 `mbp report check-reader-manuscript` must fail if reader-facing
prose contains raw claim IDs, allowed/blocked claim blocks, source-artifact
blocks, referenced-asset notes, or forbidden overclaim wording.
Milestone 1.4.1 extends that rule to fail on `Forbidden wording:` in the
reader-facing manuscript body.

Milestone 2.0 EIS validation commands:

- `mbp eis qa`
- `mbp eis alignment-sensitivity`
- `mbp eis build-features`
- `mbp eis feature-qa`
- `mbp eis claim-readiness`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.1.1 EIS validation commands:

- `mbp baseline compare-prior-eis-pulse`
- `mbp baseline compare-prior-eis-capacity`
- `mbp baseline eis-hardening-sensitivity`
- `mbp baseline eis-claim-readiness`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.2 validation commands:

- `mbp baseline run-semi-empirical`
- `mbp baseline compare-semi-empirical`
- `mbp analysis replicate-uncertainty`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.3 validation commands:

- `mbp analysis calibrate-capacity`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.4 validation commands:

- `mbp features build-run-events`
- `mbp features run-events-qa`
- `mbp features build-sequence-features`
- `mbp features sequence-qa`
- `mbp baseline run-capacity` with F14-F17 sequence-value feature groups
- `mbp baseline diagnose-sequence-value`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.5 validation commands:

- `mbp analysis knee-labels`
- `mbp analysis build-knee-risk-labels`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.5.1 validation commands:

- `mbp analysis knee-forensics`
- `mbp analysis knee-stable-registry`
- `mbp analysis threshold-event-labels`
- `mbp analysis knee-vs-threshold`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 2.6 validation commands:

- `mbp analysis build-threshold-warning-table`
- `mbp analysis threshold-warning-qa`
- `mbp baseline run-threshold-warning`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 5.0 validation commands:

- `mbp baseline calibrate-threshold-warning`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`
- generated calibrated prediction Parquets under `data/processed/` must remain
  untracked

Milestone 5.2 validation commands:

- focused tests for threshold-warning and capacity baseline helpers
- `mbp baseline run-threshold-warning`
- `mbp baseline compare-threshold-warning-censoring`
- `mbp baseline finalize-threshold-warning-claim`
- `mbp baseline calibrate-threshold-warning`
- focused `mbp baseline run-capacity` over L2/L3 HGB groups
- `mbp analysis calibrate-capacity`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `mbp report check-release-candidate`
- `git diff --check`
- generated prediction Parquets under `data/processed/` must remain untracked

Milestone 5.3 validation commands:

- focused tests for threshold-warning calibration and stressor-robust capacity
  gate helpers
- `mbp baseline calibrate-threshold-warning`
- `mbp baseline run-stressor-robust-capacity`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `mbp report check-release-candidate`
- `git diff --check`
- generated prediction Parquets under `data/processed/` must remain untracked

Milestone 5.7 validation commands:

- focused tests for stressor-robust attribution helpers
- `mbp baseline run-stressor-robust-attribution`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `mbp report check-release-candidate`
- `git diff --check`
- generated attribution prediction Parquets under `data/processed/` must
  remain untracked

Milestone 5.8 validation commands:

- focused tests for stressor-robust arm-selector helpers
- `mbp baseline run-stressor-robust-arm-selector`
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `mbp report check-release-candidate`
- `git diff --check`
- generated arm-selector prediction Parquets under `data/processed/` must
  remain untracked

Milestone 2.1 EIS validation commands:

- `mbp eis build-targets`
- `mbp eis target-qa`
- `mbp baseline run-eis`
- focused `mbp baseline run-pulse` with prior-EIS groups
- focused `mbp baseline run-capacity` with prior-EIS groups
- `ruff check . --no-cache`
- `pytest -p no:cacheprovider`
- `git diff --check`

Milestone 1.0 claim statuses must distinguish supported claims,
partially-supported claims, not-supported claims, gated claims, and blocked
claims. Unsupported claims must not be promoted by wording in paper-facing docs.

Allowed Milestone 0.5 targets:

- `capacity_Ah_k1`
- `delta_capacity_Ah`

Allowed Milestone 0.5 feature groups:

- `F0_time_only`
- `F1_state_time`
- `F2_state_exposure`
- `F3_state_nominal`
- `F4_state_log_age_scalar`

Allowed Milestone 0.6 stress-feature groups:

- `F5_log_age_histograms`
- `F6_coupled_stress`
- `F7_c_rate_focused`

Allowed Milestone 0.6.1 stress-feature groups:

- `F8_timestamp_weighted_stress`
- `F9_event_segmented_stress`
- `F10_c_rate_v1_1`

Allowed Milestone 0.6.3 narrow C-rate feature groups:

- `F11_minimal_cold_current`
- `F12_voltage_cold_current_interactions`
- `F13_sparse_c_rate_context`

`F0_time_only` is intentionally weak. Non-persistence learned baselines must
include prior check-up state through `capacity_Ah_k` in at least one state-aware
feature group.

Allowed Milestone 0.5 split views:

- `condition_fold`
- `temperature_holdout_fold`
- `c_rate_holdout_fold`
- `profile_holdout_fold`
- `voltage_window_holdout_fold`

Required Milestone 0.5 report artifacts:

- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`

Required Milestone 0.5b diagnostic artifacts:

- `baseline_diagnostics.md`
- `c_rate_holdout_error_analysis.md`
- `claim_readiness.md`
- `plots/feature_gain_by_split.csv`
- `plots/best_by_target_split.csv`
- `plots/c_rate_holdout_errors.csv`
- `plots/c_rate_holdout_by_condition.csv`
- `plots/c_rate_grouped_summaries.csv`

Milestone 0.5b linear baselines use train-fold numeric standardization for
`L1_ridge`. The standardization statistics must be fit on train rows only.

Milestone 0.5b quantile diagnostics for `L3_quantile_hist_gradient_boosting`
include:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Milestone 0.5c diagnostics for focused reports should compare against an L0
reference report when the focused report does not include persistence rows.
Missing references must be rendered explicitly as `reference_missing`; silent
`NA` values are not acceptable for L0 comparison fields.

Milestone 0.5c claim-readiness summaries are allowed to recommend the next
feature-engineering direction, but they do not authorize new modalities or
advanced models.

Milestone 0.6 stress-feature data products must remain modular sidecars keyed by
`cell_id`, `checkup_k`, and `checkup_k_next`. The baseline runner may join them
through `--stress-features`; the core interval table should remain stable.

Target-derived stress diagnostics such as `delta_capacity_per_day`,
`delta_capacity_per_efc`, and `delta_capacity_per_Ah_throughput` must not enter
predictive feature groups because they encode the capacity target.

Required Milestone 0.6 stress-feature artifacts:

- `data/interim/interval_stress_features_v1.parquet` (ignored generated data)
- `reports/audit/stress_feature_qa_report.json`
- `reports/baselines/capacity_stress_features_hgb50_report.json`
- `reports/baselines/capacity_stress_features_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_gain_by_split.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/c_rate_stress_feature_errors.csv`
- `reports/baselines/capacity_stress_features_hgb50/plots/stress_feature_claim_readiness.csv`

Milestone 0.6 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.125186`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`.

Required Milestone 0.6.1 hardening artifacts:

- `reports/audit/current_sign_audit_report.json`
- `data/interim/interval_stress_features_v1_1.parquet` (ignored generated data)
- `reports/audit/stress_feature_v1_1_qa_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Milestone 0.6.1 success criterion:

- improve C-rate `capacity_Ah_k1` condition-mean MAE below `0.124656`;
- improve C-rate `delta_capacity_Ah` condition-mean MAE below `0.101133`;
- avoid material degradation in `condition_fold` and
  `temperature_holdout_fold`;
- do not promote sign-dependent charge features unless current-sign evidence is
  high confidence.

Required Milestone 0.6.2 diagnostic artifacts:

- `target_consistency_diagnostics.md`
- `c_rate_residual_analysis.md`
- `stress_feature_ablation_summary.md`
- `plots/derived_delta_from_capacity_metrics.csv`
- `plots/derived_capacity_from_delta_metrics.csv`
- `plots/direct_vs_derived_target_metrics.csv`
- `plots/c_rate_residuals_by_parameter_set.csv`
- `plots/c_rate_residuals_by_temperature.csv`
- `plots/c_rate_residuals_by_voltage_window.csv`
- `plots/c_rate_residuals_by_capacity_bin.csv`
- `plots/c_rate_residuals_by_interval_count.csv`
- `plots/c_rate_signed_error_summary.csv`
- `plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`
- `plots/c_rate_gain_by_feature_group.csv`

Milestone 0.6.2 must not retrain by default. It should use existing row-level
prediction Parquet files and JSON reports to decide whether direct delta,
derived delta from capacity, or both target paths should be reported.

Required Milestone 0.6.3 diagnostic artifacts:

- `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
- `reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_c_rate_bias_corrected_report.json`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/c_rate_bias_before_after.csv`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`

Milestone 0.6.3 may train on normalized target modes
`delta_capacity_per_day_target` and `delta_capacity_per_efc_target`, but the
report metrics must evaluate predictions back in `delta_capacity_Ah` units. The
true target-derived rates must never enter predictive input feature groups.
Residual correction must be fit inside each train fold only; test-fold
residuals must not be used for correction.

Required Milestone 0.7 PULSE artifacts:

- `docs/PULSE_TARGET_POLICY.md`
- `reports/audit/pulse_qa_report.json`
- `reports/audit/pulse_alignment_report.json`
- `reports/audit/pulse_target_coverage.csv`
- `data/interim/pulse_target_table.parquet` (ignored generated data)
- `reports/baselines/pulse_resistance_l0_l3_report.json`
- `reports/baselines/pulse_resistance_l0_l3/leaderboard.csv`
- `reports/baselines/pulse_resistance_l0_l3/baseline_summary.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md`

Allowed Milestone 0.7 PULSE targets:

- `delta_pulse_1s_resistance`
- `pulse_1s_resistance_k1`
- `delta_pulse_10ms_resistance`
- `pulse_10ms_resistance_k1`

Allowed Milestone 0.7 PULSE feature groups:

- `P0_persistence`
- `P1_state_time`
- `P2_state_capacity`
- `P3_state_nominal`
- `P4_state_log_age_scalar`
- `P5_stress_v1_1`

Milestone 0.7 reports must use grouped split views and report target coverage.
PULSE results are resistance-baseline diagnostics only; they are not evidence
for a capacity+PULSE multimodal claim.

Required Milestone 0.7.1 PULSE hardening artifacts:

- `reports/audit/pulse_alignment_sensitivity_report.json`
- `reports/audit/pulse_alignment_sensitivity_coverage.csv`
- `reports/audit/pulse_missing_canonical_targets.csv`
- `reports/audit/pulse_missingness_by_condition.csv`
- `reports/audit/pulse_missingness_by_split.csv`
- `data/interim/pulse_target_table_mean.parquet` (ignored generated data)
- `data/interim/pulse_target_table_charge.parquet` (ignored generated data)
- `data/interim/pulse_target_table_discharge.parquet` (ignored generated data)
- `reports/baselines/pulse_resistance_alignment_24h_report.json`
- `reports/baselines/pulse_resistance_alignment_36h_report.json`
- `reports/baselines/pulse_resistance_alignment_sensitivity/baseline_summary.md`
- `reports/baselines/pulse_resistance_alignment_sensitivity/plots/pulse_alignment_threshold_comparison.csv`
- `reports/baselines/pulse_resistance_direction_mean_report.json`
- `reports/baselines/pulse_resistance_direction_charge_report.json`
- `reports/baselines/pulse_resistance_direction_discharge_report.json`
- `reports/baselines/pulse_resistance_l0_l3/pulse_resistance_direction_comparison.md`
- `reports/baselines/pulse_resistance_l0_l3/plots/pulse_direction_comparison.csv`

Milestone 0.7.1 direction policy:

- `mean` remains the canonical PULSE target direction handling.
- `charge` and `discharge` target tables are diagnostic until a later policy
  accepts direction-specific targets.
- If a direction-specific table has no finite adjacent interval targets, the
  baseline report must emit an explicit warning rather than silently passing.

Milestone 0.7.1 alignment policy:

- Baselines may use `--max-alignment-delta-s` to filter intervals where either
  endpoint exceeds the threshold.
- Alignment-threshold reports must include retained interval counts, retained
  cell/parameter-set counts, and split coverage.
- Large-alignment rows are still warnings, not silent exclusions, unless a
  later PULSE target policy changes the canonical target definition.

Required Milestone 0.7.2 PULSE robustness artifacts:

- `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- `reports/baselines/pulse_resistance_target_robustness_report.json`
- `reports/baselines/pulse_resistance_target_robustness/leaderboard.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_1s_vs_10ms_comparison.csv`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_delta_vs_k1_comparison.csv`
- `reports/baselines/pulse_resistance_alignment_robustness.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`
- `reports/audit/pulse_missingness_interpretation.md`
- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`

Milestone 0.7.2 target policy:

- `delta_pulse_1s_resistance` remains the canonical first PULSE transition
  target unless target robustness shows a clear replacement.
- `delta_pulse_10ms_resistance`, `pulse_1s_resistance_k1`, and
  `pulse_10ms_resistance_k1` may be evaluated as scalar diagnostic targets.
- k1 resistance-level targets must be interpreted as state-tracking targets,
  not direct transition prediction.
- Direction-specific claims remain blocked; current RT/50 `mean` is documented
  as effectively equivalent to `charge` in the available generated target table.

Required Milestone 0.8 coupling artifacts:

- `data/interim/capacity_pulse_coupling_table.parquet` (ignored generated data)
- `reports/coupling/pulse_capacity/pulse_capacity_correlation.md`
- `reports/coupling/pulse_capacity/plots/capacity_residual_vs_delta_pulse.csv`
- `reports/coupling/pulse_capacity/plots/capacity_residual_by_pulse_growth_bin.csv`
- `reports/coupling/pulse_capacity/plots/c_rate_capacity_residual_by_pulse_growth.csv`
- `reports/coupling/pulse_capacity/plots/pulse_growth_by_capacity_error_decile.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50_report.json`
- `reports/baselines/capacity_with_prior_pulse_hgb50/pulse_feature_gain.md`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/capacity_pulse_feature_gain_by_split.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/c_rate_capacity_pulse_feature_gain.csv`
- `reports/baselines/capacity_with_prior_pulse_hgb50/plots/pulse_feature_gain_claim_readiness.csv`
- `docs/experiments/2026-05-23_capacity_pulse_coupling_diagnostics.md`

Milestone 0.8 feature policy:

- Capacity baselines may use prior PULSE state at check-up `k`.
- `pulse_1s_resistance_k1`, `delta_pulse_1s_resistance`,
  `pulse_10ms_resistance_k1`, and `delta_pulse_10ms_resistance` must not enter
  capacity predictive feature groups.
- Any apparent gain from future PULSE deltas is leakage and is not publishable
  evidence.

Required Milestone 0.8.1 coupling robustness artifacts:

- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/`
- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/`
- `canonical_model_correlation.md`
- `interval_level_correlation.md`
- `condition_level_correlation.md`
- `bootstrap_correlation_summary.md`
- `residualized_correlation.md`
- `subgroup_coupling_summary.md`
- `coupling_claim_readiness.md`
- `plots/canonical_model_residual_vs_pulse.csv`
- `plots/canonical_model_correlation_by_split.csv`
- `plots/interval_level_pulse_capacity_correlation.csv`
- `plots/condition_level_pulse_capacity_correlation.csv`
- `plots/pulse_capacity_correlation_bootstrap.csv`
- `plots/residualized_pulse_capacity_correlation.csv`
- `plots/subgroup_pulse_capacity_correlation.csv`
- `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`

Milestone 0.8.1 decision rule:

- Coupling evidence may be described as scalar explanatory diagnostics when it
  survives canonical-model filtering and interval/condition aggregation.
- Predictive capacity+PULSE claims remain blocked unless a later non-neural
  baseline demonstrates grouped predictive gains without future PULSE leakage.

Required Milestone 0.9 prior-PULSE predictive artifacts:

- `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_report.json`
- `reports/baselines/capacity_prior_pulse_predictive/paired_condition_gain.csv`
- `reports/baselines/capacity_prior_pulse_predictive/split_level_gain_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/c_rate_gain_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/coverage_effect_summary.csv`
- `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_claim_readiness.md`
- `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`

Milestone 0.9 claim rules:

- Primary target: `capacity_Ah_k1`.
- Secondary guardrail: `delta_capacity_Ah`.
- If `capacity_Ah_k1` gains are positive and robust while
  `delta_capacity_Ah` gains are not, only a narrow capacity-level prediction
  claim is allowed.
- Do not claim interval fade-rate improvement unless `delta_capacity_Ah`
  improves under paired grouped validation.
- Future PULSE state and PULSE deltas invalidate the result if they enter
  capacity feature groups.

Required Milestone 0.9.1 strongest non-PULSE comparison artifacts:

- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_report.json`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/paired_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/c_rate_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/bootstrap_gain_vs_best_nonpulse.csv`
- `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`
- `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`

Milestone 0.9.1 claim rules:

- If prior PULSE beats the strongest supplied non-PULSE baseline for
  `capacity_Ah_k1` with bootstrap p05 above zero in C-rate and at least one
  other OOD split, a narrow prior-PULSE level-prediction claim is allowed.
- If prior PULSE beats F4 but not the strongest supplied non-PULSE baseline,
  report only the F4 improvement.
- If `delta_capacity_Ah` remains negative, fade-rate prediction claims remain
  blocked.

Blocked until later milestones:

- EIS claims and PULSE scientific claims beyond scalar resistance baselines.
- Sequence models, neural models, policy ranking, and CBAT architecture.

## Milestone 2.6.1 Threshold-Warning Hardening

Milestone 2.6.1 evaluates the `capacity_below_80pct_initial` threshold-warning
baseline as a prospective grouped diagnostic. Inputs are restricted to
check-up-`k` state/time/nominal metadata. The warning feature policy continues
to exclude `capacity_Ah_k1`, `delta_capacity_Ah`, future interval exposure,
future PULSE/EIS state, and PULSE/EIS deltas.

Required hardening artifacts:

- `reports/baselines/threshold_warning_l0_l2_report.json`
- `reports/baselines/threshold_warning_l0_l2/leaderboard.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/lead_time_diagnostics.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_report.json`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_reliability.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_c_rate.md`
- `reports/baselines/threshold_warning_l0_l2/plots/lead_time_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/proximity_bin_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/c_rate_lead_time_performance.csv`
- `docs/experiments/2026-05-23_threshold_warning_hardening.md`

Claim rules:

- If HGB beats event-rate and distance-to-threshold baselines, a narrow
  threshold-event forecasting diagnostic claim is allowed.
- If performance is mostly near-threshold or censoring-sensitive, do not call
  the result early warning.
- If calibration diagnostics fail, probabilities are diagnostic scores only,
  not calibrated risk estimates.
- Detector-knee prediction, policy ranking, causal warning claims, sequence
  models, neural models, and CBAT remain blocked.

## Milestone 2.6.2 Censoring-Aware Finalization

Milestone 2.6.2 evaluates the threshold-warning result under both all-row and
verified-only censoring policies before final claim wording is locked.

Label policies:

- `all_rows`: current Boolean horizon labels, equivalent to treating
  right-censored unknown rows as negative.
- `verified_only`: excludes `right_censored_unknown` rows for each horizon.
- `censored_as_negative`: explicit sensitivity alias for the current Boolean
  behavior.

Required artifacts:

- `reports/baselines/threshold_warning_verified_only_report.json`
- `reports/baselines/threshold_warning_verified_only/leaderboard.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/threshold_warning_censoring_sensitivity_report.json`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_metric_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_split_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_c_rate_comparison.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/plots/final_lead_time_claim_matrix.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/final_c_rate_warning_matrix.csv`
- `docs/experiments/2026-05-23_threshold_warning_censoring_finalization.md`

Claim rules:

- If all-row and verified-only policies both show HGB W2 beating event-rate and
  proximity baselines, allow a narrow threshold-event forecasting diagnostic
  claim.
- If C-rate also beats both references with adequate class support, allow
  C-rate threshold-warning diagnostic wording.
- If verified-only performance collapses, keep warning claims exploratory.
- Calibration remains separate; poor ECE blocks calibrated-risk wording.
- Detector-knee prediction, causal early-warning claims, policy ranking,
  neural/sequence models, and CBAT remain blocked.

## Milestone 3.0 Main-Project Evidence Synthesis

Milestone 3.0 is a documentation and source-traceability checkpoint. It
consolidates all completed main-project gates after threshold-warning
censoring finalization and decides the next branch.

Required artifacts:

- `docs/experiments/2026-05-23_main_project_evidence_synthesis_v2.md`
- `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
- `reports/synthesis/main_project_claim_matrix_v2.csv`
- `reports/synthesis/main_project_gate_status.md`
- `reports/synthesis/technical_decision_matrix_v2.md`
- `reports/synthesis/blocked_claims_v2.md`
- `reports/synthesis/next_branch_decision.md`
- `reports/synthesis/source_consistency_check_v2.md`

Validation:

- All referenced source artifacts must exist.
- No blocked claim may be marked supported.
- No calibrated-risk, detector-knee prediction, CBAT, policy-ranking, causal,
  or same-cell counterfactual claim may appear as supported.
- If no code is added, `git diff --check` is sufficient.

Decision rule:

- Default recommendation is to return to synthesis/manuscript integration and
  benchmark release preparation.
- If additional technical work is selected, it should be limited to a narrow
  threshold-warning calibration branch.
- New model training, feature engineering, neural/sequence models, DRT, EIS
  embeddings, policy ranking, CBAT, causal claims, and same-cell
  counterfactual claims remain blocked.

## Milestone 5.9 Hierarchical Replicate-Aware Capacity Baseline Gate

Milestone 5.9 evaluates L5-style non-neural hierarchical/partial-pooling
capacity comparators under the same grouped split discipline. Residual offsets,
shrinkage estimates, and interval radii must be computed from outer-training
rows only.

Required artifacts:

- `reports/baselines/capacity_hierarchical_replicate_report.json`
- `reports/baselines/capacity_hierarchical_replicate/leaderboard.csv`
- `reports/baselines/capacity_hierarchical_replicate/hierarchical_claim_readiness.md`
- `reports/baselines/capacity_hierarchical_replicate/plots/c_rate_hierarchical_gain.csv`
- `reports/baselines/capacity_hierarchical_replicate/plots/c_rate_paired_condition_gains.csv`
- `reports/baselines/capacity_hierarchical_replicate/plots/outside_split_degradation.csv`
- `docs/experiments/2026-05-27_hierarchical_replicate_baseline_gate.md`

Claim rules:

- A hierarchical comparator can be reported as implemented if it runs under
  grouped validation with a passed train/test parameter-set leakage audit.
- A narrow C-rate `delta_capacity_Ah` hierarchical diagnostic requires H4/F4 to
  beat H3/F4 on the C-rate split, paired condition bootstrap p05 above zero,
  and maximum outside-C-rate relative degradation no greater than 5%.
- Replicate-variance intervals are diagnostic only unless grouped and C-rate
  coverage both pass. They do not authorize calibrated-uncertainty wording.
- The gate never authorizes global robust-capacity, solved C-rate fade,
  architecture, policy-ranking, causal, calibrated-risk, or CBAT claims.

## Milestone 6.0 Multi-Horizon Capacity Forecasting Gate

Milestone 6.0 evaluates whether non-neural models can forecast capacity over
multiple future check-up horizons under the same grouped validation discipline.
It is a Q1 forecasting gate, not architecture work.

Required artifacts:

- `data/interim/capacity_horizon_table_v1.parquet` (ignored generated data)
- `reports/analysis/capacity_horizon/capacity_horizon_qa_report.json`
- `reports/analysis/capacity_horizon/capacity_horizon_coverage.csv`
- `reports/baselines/capacity_horizon_l0_l2_report.json`
- `reports/baselines/capacity_horizon_l0_l2/leaderboard.csv`
- `reports/baselines/capacity_horizon_l0_l2/capacity_horizon_claim_readiness.md`
- `reports/baselines/capacity_horizon_l0_l2/plots/horizon_performance.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/c_rate_horizon_performance.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/oracle_exposure_gain.csv`
- `docs/experiments/2026-05-27_multi_horizon_capacity_forecasting_gate.md`

Claim rules:

- Prospective feature groups may use only check-up-k state, prior trajectory,
  cumulative history available at k, and nominal condition metadata.
- K3 oracle exposure features aggregate k-to-k+h exposure and are diagnostic
  only. They cannot support early forecasting, policy, causal, or architecture
  claims.
- A multi-horizon diagnostic claim requires HGB K2 to beat both persistence and
  prior-slope baselines for the predeclared horizons 2 and 3 under grouped
  validation.
- C-rate wording must be split-specific. It is not evidence that C-rate fade is
  solved globally.
- The gate does not authorize calibrated uncertainty, calibrated risk, policy
  ranking, sequence/neural models, CBAT, or causal claims.

## Milestone 6.1 Multi-Horizon Error Forensics Gate

Milestone 6.1 diagnoses the Milestone 6.0 partial multi-horizon result using
existing report, prediction, and horizon-table artifacts only. It is not a
model-training, feature-engineering, architecture, policy, or causal milestone.

Required artifacts:

- `reports/baselines/capacity_horizon_l0_l2/capacity_horizon_forensics_report.json`
- `reports/baselines/capacity_horizon_l0_l2/multi_horizon_error_forensics.md`
- `reports/baselines/capacity_horizon_l0_l2/multi_horizon_next_branch_readiness.md`
- `reports/baselines/capacity_horizon_l0_l2/plots/horizon_reference_gain_by_split.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/c_rate_condition_horizon_errors.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/prior_slope_failure_modes.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/oracle_exposure_gain_by_split.csv`
- `reports/baselines/capacity_horizon_l0_l2/plots/prospective_feature_audit.csv`
- `docs/experiments/2026-05-27_multi_horizon_error_forensics.md`

Claim rules:

- The diagnostics may narrow or explain the Milestone 6.0 claim posture, but
  they do not create a new supported claim by themselves.
- K3 oracle-exposure gains remain non-prospective, even if they improve MAE.
- Any future feature branch must use only information available at or before
  check-up `k`, or scheduled protocol metadata demonstrably known before the
  forecast horizon.
- Sequence/neural models, CBAT, policy ranking, causal claims, calibrated
  risk, and calibrated uncertainty remain blocked.

## Milestone 6.2 Prior-Trajectory Shape Baseline Gate

Milestone 6.2 tests whether capacity trajectory shape observed at or before
check-up `k` improves non-neural multi-horizon capacity forecasting. It is a
prospective feature-sidecar and baseline gate, not sequence modeling,
architecture work, policy ranking, or causal analysis.

Required artifacts:

- `data/interim/capacity_horizon_trajectory_features_v1.parquet` (ignored generated data)
- `reports/analysis/capacity_horizon/capacity_horizon_trajectory_qa_report.json`
- `reports/analysis/capacity_horizon/capacity_horizon_trajectory_coverage.csv`
- `reports/baselines/capacity_horizon_trajectory_l0_l2_report.json`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/trajectory_shape_diagnostics.md`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/trajectory_shape_claim_readiness.md`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/plots/trajectory_gain_by_split.csv`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/plots/horizon3_capacity_repair.csv`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/plots/c_rate_trajectory_gain.csv`
- `reports/baselines/capacity_horizon_trajectory_l0_l2/plots/trajectory_leakage_audit.csv`
- `docs/experiments/2026-05-27_prior_trajectory_shape_horizon_gate.md`

Claim rules:

- Prior-trajectory features may use only capacity history and derived slopes,
  volatility, and curvature available at or before check-up `k`.
- A new trajectory-shape diagnostic claim requires K5 HGB to repair all-split
  horizon-3 `capacity_Ah_kh` against both K2 and prior-slope references while
  preserving C-rate horizon-2/3 performance for both primary targets.
- If K5 helps only isolated rows, report split/target-specific diagnostic
  value only.
- K3 actual k-to-k+h exposure remains oracle-only and cannot be used to
  justify prospective forecasting, architecture, policy, or causal claims.

## Milestone 7.0 Benchmark Task Freeze Gate

Milestone 7.0 freezes the completed benchmark evidence into a task registry and
executable consistency check. It is a reproducibility and benchmark-interface
gate, not a new modeling or feature-engineering milestone.

Required artifacts:

- `configs/benchmark_tasks_v1.yaml`
- `reports/synthesis/benchmark_task_registry_check.md`
- `reports/synthesis/benchmark_leaderboard_v1.csv`
- `reports/synthesis/benchmark_task_cards_v1.md`
- `reports/synthesis/benchmark_model_cards_v1.md`
- `docs/experiments/2026-05-27_benchmark_task_freeze.md`

Validation rules:

- Every frozen task must identify a primary claim ID, status, source artifact,
  target, split view, primary metric, allowed wording, forbidden wording, and
  decision.
- Task statuses must match the primary claim status in
  `reports/synthesis/main_project_claim_matrix_v2.csv`.
- Source artifacts must exist; generated Parquet data products may appear only
  as ignored local artifacts under `data/raw/`, `data/interim/`,
  `data/splits/`, or `data/processed/`.
- Supported task wording must not mark CBAT, policy ranking, causal claims,
  detector-knee prediction, calibrated risk, calibrated uncertainty, neural or
  sequence models, DRT, EIS embeddings, or broad multimodal claims as
  supported.

## Milestone 7.1 Minimal Sequence/Neural Reopening Gate

Milestone 7.1 reopens H7 only as a narrow falsification check. It may build a
fixed-length LOG_AGE run-event sequence table, compare true order against a
deterministic shuffled-order control, and evaluate Ridge plus a tiny CUDA-only
Torch MLP against frozen aggregate-event and timestamp-stress HGB references.
It is not a transformer, CBAT, multimodal architecture, policy-ranking, or
causal milestone.

Required artifacts:

- `data/interim/interval_event_sequence_table_v1.parquet` (ignored generated data)
- `reports/audit/interval_event_sequence_qa_report.json`
- `reports/baselines/minimal_sequence_reopening_report.json`
- `reports/baselines/minimal_sequence_reopening/leaderboard.csv`
- `reports/baselines/minimal_sequence_reopening/minimal_sequence_reopening_diagnostics.md`
- `reports/baselines/minimal_sequence_reopening/sequence_reopening_claim_readiness.md`
- `reports/baselines/minimal_sequence_reopening/plots/sequence_vs_shuffled.csv`
- `reports/baselines/minimal_sequence_reopening/plots/sequence_vs_aggregate.csv`
- `reports/baselines/minimal_sequence_reopening/plots/sequence_vs_stress.csv`
- `reports/baselines/minimal_sequence_reopening/plots/c_rate_sequence_reopening.csv`
- `docs/experiments/2026-05-27_minimal_sequence_reopening_gate.md`

Validation rules:

- Neural rows must run on CUDA. CPU fallback is invalid for this gate.
- True-sequence candidates must beat shuffled-order controls, aggregate-event
  HGB, and timestamp-stress HGB for C-rate `delta_capacity_Ah` and at least one
  non-C-rate grouped view before any later sequence baseline can be opened.
- Event-sequence vectors must exclude future diagnostic fields, capacity
  targets, capacity deltas, PULSE/EIS future state, and PULSE/EIS deltas.
- A passing Torch/GPU environment check is only execution evidence. It does not
  authorize neural architecture, transformers, CBAT, policy ranking, or broad
  multimodal claims.

## Milestone 7.2 Policy-Contrast Support and Observed Ranking Feasibility Gate

Milestone 7.2 tests charter H6/Q4 support before any policy-ranking model. It
may build matched observed contrasts between parameter-set triplets that differ
on one nominal policy/stressor axis while holding the other key condition
metadata fixed. It may summarize observed capacity-loss sign stability across
replicates and check-ups. It must not train a ranking model, recommend an
operating policy, estimate intervention effects, or make same-cell
counterfactual claims.

Required artifacts:

- `data/interim/policy_contrast_registry_v1.parquet` (ignored generated data)
- `reports/analysis/policy/policy_contrast_support_report.json`
- `reports/analysis/policy/policy_contrast_registry.csv`
- `reports/analysis/policy/policy_contrast_by_family.csv`
- `reports/analysis/policy/observed_policy_contrast_report.json`
- `reports/analysis/policy/observed_policy_ranking_stability.csv`
- `reports/analysis/policy/policy_ranking_feasibility.md`
- `reports/analysis/policy/policy_claim_readiness.md`
- `docs/experiments/2026-05-27_policy_contrast_support_gate.md`

Validation rules:

- Contrast families are diagnostic only: charge C-rate, temperature, voltage
  window, and profile.
- A registry contrast must vary one family field and match the remaining
  nominal fields used by that family.
- Triplet support means both arms have at least three replicate cells.
- Observed sign stability may be reported only as an observed capacity-loss
  ordering diagnostic, never as a causal, counterfactual, or deployment policy.
- A future policy-ranking baseline can only be considered as a separate gate
  after observed support and stability are documented. Milestone 7.2 itself
  does not authorize policy ranking.

## Milestone 7.3 Support-Bounded Contrast-Ordering Feasibility Gate

Milestone 7.3 tests whether existing out-of-fold multi-horizon capacity
predictions can order the Milestone 7.2 supported observed contrasts. It is a
report-only feasibility gate: it may consume
`capacity_horizon_l0_l2_predictions.parquet`, but it must not retrain models,
add feature engineering, optimize policies, estimate causal effects, or create
same-cell counterfactuals.

Required artifacts:

- `reports/analysis/policy/policy_ranking_feasibility_report.json`
- `reports/analysis/policy/policy_ranking_pairwise_metrics.csv`
- `reports/analysis/policy/policy_ranking_by_family.csv`
- `reports/analysis/policy/policy_ranking_bootstrap.csv`
- `reports/analysis/policy/policy_ranking_claim_readiness.md`
- `docs/experiments/2026-05-27_policy_ranking_feasibility_gate.md`

Validation rules:

- Only `has_triplet_support=True` contrasts may enter pairwise metrics.
- The primary prospective candidate is HGB K2
  (`MH3_hist_gradient_boosting` / `K2_nominal_condition`) on
  `delta_capacity_Ah_h` horizons 2 and 3.
- Severity is positive degradation: `-delta_capacity_Ah_h` for delta targets
  and `-capacity_Ah_kh` for capacity-level diagnostics.
- K3 future-exposure rows must be labeled `oracle_diagnostic_only` and cannot
  support prospective wording.
- A diagnostic ordering claim requires HGB K2 to beat persistence and
  prior-slope references with positive contrast-bootstrap lower bounds, at
  least two contrast families passing, and no C-rate collapse.
- If the reference/bootstrap gate fails, supported observed contrast ordering
  remains partial or diagnostic only. Policy recommendation, causal claims,
  same-cell counterfactual claims, calibrated policy risk/utility, CBAT, and
  sequence/neural branches remain blocked.

## Milestone 7.4 Contrast-Ordering Failure Forensics and Metric Robustness

Milestone 7.4 diagnoses the Milestone 7.3 strict prior-slope bootstrap failure
without retraining models or adding features. It consumes only the existing
7.3 pairwise, by-family, and bootstrap CSV artifacts and reports whether the
failure is concentrated in near-zero effects, rank metrics, C-rate rows, or
specific contrast families.

Required artifacts:

- `reports/analysis/policy/policy_ranking_failure_forensics_report.json`
- `reports/analysis/policy/policy_ranking_failure_forensics.md`
- `reports/analysis/policy/policy_ranking_failure_claim_readiness.md`
- `reports/analysis/policy/plots/effect_size_threshold_sign_accuracy.csv`
- `reports/analysis/policy/plots/rank_correlation_diagnostics.csv`
- `reports/analysis/policy/plots/topk_regret_diagnostics.csv`
- `reports/analysis/policy/plots/hgb_vs_prior_failure_bins.csv`
- `docs/experiments/2026-05-27_policy_ranking_failure_forensics.md`

Validation rules:

- The diagnostic command must be report-only: no new model training, no new
  feature engineering, and no regenerated prediction table.
- K3 future-exposure rows must be excluded from prospective readiness and kept
  oracle-diagnostic only.
- Effect-size-thresholded gains may support only metric forensics unless a
  future predeclared gate shows HGB beats prior slope on large-effect
  contrasts across at least two families without C-rate collapse.
- Rank-correlation and top-k/regret rows are support-bounded diagnostics; they
  are not policy optimization or recommendation metrics.
- Policy recommendation, causal or same-cell counterfactual claims, calibrated
  policy risk/utility, CBAT, and sequence/neural branches remain blocked.

## Milestone 8.0 Support-Aware Selective Reliability Gate

Milestone 8.0 audits whether train-only condition-support scores identify
more reliable subsets of existing prediction artifacts. It is a report-only
diagnostic gate over capacity-horizon forecasts, threshold-warning scores, and
supported contrast-ordering rows.

Required command:

```bash
mbp analysis diagnose-support-reliability \
  --interval-table data/interim/interval_table.parquet \
  --horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --capacity-predictions data/processed/capacity_horizon_l0_l2_predictions.parquet \
  --warning-table data/interim/threshold_warning_table_v1.parquet \
  --warning-predictions data/processed/threshold_warning_l0_l2_predictions.parquet \
  --policy-pairwise reports/analysis/policy/policy_ranking_pairwise_metrics.csv \
  --out-dir reports/analysis/support_reliability
```

Required artifacts:

- `reports/analysis/support_reliability/support_reliability_report.json`
- `reports/analysis/support_reliability/support_reliability_diagnostics.md`
- `reports/analysis/support_reliability/support_reliability_claim_readiness.md`
- `reports/analysis/support_reliability/plots/support_distance_by_split.csv`
- `reports/analysis/support_reliability/plots/selective_capacity_performance.csv`
- `reports/analysis/support_reliability/plots/selective_threshold_warning_performance.csv`
- `reports/analysis/support_reliability/plots/selective_policy_contrast_performance.csv`

Validation rules:

- Support scores must be computed from condition metadata and training-side
  conditions for each grouped split; held-out test rows must not define their
  own support.
- Selective curves may retain rows by support score only. They must not use
  observed errors, labels, outcomes, or future interval exposure to decide
  which rows to retain.
- The gate must not train a model, tune a model, create predictor features, or
  regenerate prediction Parquets.
- K3 oracle future-exposure rows remain non-prospective and must not drive
  support-readiness wording.
- Passing support-distance diagnostics can support only audit/abstention
  wording. They do not authorize calibrated risk, deployment reliability,
  policy recommendation, causal or same-cell counterfactual claims, CBAT, or
  architecture readiness.

## Milestone 8.1 Non-Neural Diagnostic-State Distillation Gate

Milestone 8.1 tests charter Q2/H3 without opening a multimodal architecture
branch. It asks whether current PULSE/EIS scalar diagnostic state can be
predicted from check-up-k capacity/state/time/nominal fields and whether those
train-only predicted diagnostic-state features improve downstream
capacity-horizon or 80% threshold-warning forecasts.

Required command:

```bash
mbp baseline run-diagnostic-state-distillation \
  --capacity-horizon-table data/interim/capacity_horizon_table_v1.parquet \
  --threshold-warning-table data/interim/threshold_warning_table_v1.parquet \
  --pulse-target-table data/interim/pulse_target_table.parquet \
  --eis-target-table data/interim/eis_target_table_v1.parquet \
  --out reports/baselines/diagnostic_state_distillation_report.json \
  --predictions-out data/processed/diagnostic_state_distillation_predictions.parquet \
  --out-dir reports/baselines/diagnostic_state_distillation \
  --hgb-max-iter 50 \
  --auxiliary-model-level A0_ridge
```

Required artifacts:

- `reports/baselines/diagnostic_state_distillation_report.json`
- `reports/baselines/diagnostic_state_distillation/diagnostic_state_distillation_summary.md`
- `reports/baselines/diagnostic_state_distillation/diagnostic_state_distillation_claim_readiness.md`
- `reports/baselines/diagnostic_state_distillation/plots/auxiliary_target_accuracy.csv`
- `reports/baselines/diagnostic_state_distillation/plots/diagnostic_state_downstream_gains.csv`
- `reports/baselines/diagnostic_state_distillation/plots/c_rate_diagnostic_state_gains.csv`

Validation rules:

- Stage-A auxiliary predictions for training rows must be generated by inner
  grouped out-of-fold prediction on the outer-training conditions only.
- Stage-A auxiliary predictions for held-out rows must be generated from models
  fit only on outer-training rows.
- Stage-B downstream models may use only check-up-k capacity/state/time/nominal
  fields plus predicted diagnostic-state features.
- True current PULSE/EIS scalar values, future PULSE/EIS values, PULSE/EIS
  deltas, future interval exposure, target values, detector-knee labels,
  policy contrast labels, and K3 oracle exposure fields are forbidden as
  downstream features.
- Claim support requires a primary downstream gain of at least 10%, no C-rate
  collapse, and auxiliary targets beating train-mean references. Otherwise the
  result is partial, diagnostic, or not supported.
- This gate does not authorize CBAT, capacity+PULSE+EIS architecture, neural or
  sequence models, policy ranking, calibrated risk/uncertainty, causal claims,
  or same-cell counterfactual claims.

## Milestone 8.2 Multi-Horizon Diagnostic Endpoint Forecasting Gate

Milestone 8.2 tests charter Q2/H3 from the opposite direction of Milestone 8.1:
instead of asking whether predicted PULSE/EIS state helps downstream capacity
or threshold tasks, it asks whether future scalar PULSE/EIS diagnostic
endpoints are themselves forecastable from check-up-k state and current
same-diagnostic state.

Required commands:

```bash
mbp analysis build-diagnostic-horizon-table \
  --interval-table data/interim/interval_table.parquet \
  --pulse-target-table data/interim/pulse_target_table.parquet \
  --eis-target-table data/interim/eis_target_table_v1.parquet \
  --out data/interim/diagnostic_horizon_table_v1.parquet

mbp analysis diagnostic-horizon-qa \
  --diagnostic-horizon-table data/interim/diagnostic_horizon_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/analysis/diagnostic_horizon/diagnostic_horizon_qa_report.json \
  --coverage-out reports/analysis/diagnostic_horizon/diagnostic_horizon_coverage.csv

mbp baseline run-diagnostic-horizon \
  --diagnostic-horizon-table data/interim/diagnostic_horizon_table_v1.parquet \
  --out reports/baselines/diagnostic_horizon_l0_l2_report.json \
  --predictions-out data/processed/diagnostic_horizon_l0_l2_predictions.parquet \
  --out-dir reports/baselines/diagnostic_horizon_l0_l2 \
  --hgb-max-iter 50
```

Required artifacts:

- `reports/analysis/diagnostic_horizon/diagnostic_horizon_qa_report.json`
- `reports/analysis/diagnostic_horizon/diagnostic_horizon_coverage.csv`
- `reports/baselines/diagnostic_horizon_l0_l2_report.json`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_summary.md`
- `reports/baselines/diagnostic_horizon_l0_l2/diagnostic_horizon_claim_readiness.md`
- `reports/baselines/diagnostic_horizon_l0_l2/leaderboard.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/diagnostic_horizon_reference_gains.csv`
- `reports/baselines/diagnostic_horizon_l0_l2/plots/c_rate_diagnostic_horizon_performance.csv`

Validation rules:

- The horizon table may include only observed future diagnostic endpoint values
  as targets. `diagnostic_value_kh`, `delta_diagnostic_value_h`, future
  capacity values, future interval exposure, and event labels are forbidden as
  predictor features.
- Current same-diagnostic state at check-up `k` is allowed as a diagnostic
  endpoint forecasting input. This is not a downstream capacity/PULSE/EIS
  multimodal architecture claim.
- Headline evaluation uses grouped condition/stressor splits. Parameter-set
  leakage across train/test folds must fail.
- Claim support requires DH3 HGB with capacity plus current same-diagnostic
  state to beat persistence and capacity-state references by at least 10% on
  all primary horizon-2/3 rows and avoid negative C-rate gains.
- Partial gains may support only cautious diagnostic endpoint forecasting
  wording. They do not authorize CBAT, broad multimodal architecture,
  calibrated risk/uncertainty, policy ranking, sequence/neural branches,
  causal claims, or same-cell counterfactual claims.
