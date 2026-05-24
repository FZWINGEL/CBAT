# Manuscript v0.5

Working title: Grouped-validation battery degradation benchmarks with operating-history, PULSE, EIS, and threshold-event diagnostics.

This reader-facing draft integrates the validated `benchmark-v0.1-rc2` evidence package. It updates the v0.4 manuscript with the completed EIS, semi-empirical, uncertainty, temporal-order, knee/threshold, threshold-warning, and release-readiness gates while preserving the claim boundaries in a sidecar.

## Abstract

Battery degradation benchmarks often reward interpolation across familiar
conditions rather than generalization to unseen operating regimes. We present a
reproducible grouped-validation benchmark for battery degradation prediction
from capacity check-ups, operating-history features, PULSE resistance, and
quality-gated EIS diagnostics. The benchmark treats the Luh-Blank cohort as 76
parameter-set conditions with three replicate cells each, builds linked
interval and modality data products, and reports condition-level and
stressor-axis holdouts rather than random row splits.

The benchmark now closes the main charter gates from capacity baselines through
threshold-event warning. C-rate transfer remains the dominant unresolved
capacity setting. LOG_AGE scalar and stress features help in selected grouped
views but do not solve C-rate fade. RT/50 PULSE and RT/50 EIS are supported as
scalar diagnostic endpoints, while broad multimodal and architecture claims
remain blocked. Semi-empirical comparators are useful domain checks but do not
beat the strongest grouped HGB/stress baselines in the hardest C-rate views.
Replicate spread, conformal intervals, and raw HGB quantiles contextualize
model error but do not pass the C-rate coverage gate. Event-order summaries do
not justify sequence models. Detector-knee labels are unstable across
replicates, but 80% threshold-event labels are more stable; non-neural
baselines forecast the 80% threshold event diagnostically beyond proximity and
under verified-only censoring sensitivity.

The result is a claim-bounded benchmark release candidate rather than an
architecture paper. The validated `benchmark-v0.1-rc2` package includes the
runbook, command DAG, artifact manifest, release checker, claim ledger, and
source-linked synthesis reports needed to reproduce and audit the evidence.

## Introduction

Battery degradation is path-dependent. Temperature, voltage window, state of
charge, C-rate, current profile, rest, diagnostic burden, and prior age interact
over time. A useful battery benchmark must therefore ask more than whether a
model can fit cells from regimes it has effectively already seen. It must ask
whether the evidence survives held-out condition and stressor families.

This manuscript treats that question as a benchmark and governance problem
before it treats it as a model-architecture problem. The Luh-Blank dataset is
well suited to this task because it combines capacity check-ups, PULSE
resistance, EIS records, and LOG_AGE operating histories across 228 commercial
cells. Those 228 cells represent 76 parameter-set conditions with three
replicates per condition. The benchmark therefore groups replicate triplets for
headline evidence and records negative gates as first-class scientific results.

The v0.5 manuscript integrates all main-project evidence through the
`benchmark-v0.1-rc2` release candidate. Earlier sections established linked
data products, grouped splits, capacity baselines, LOG_AGE stress features,
PULSE resistance diagnostics, and prior-PULSE comparisons. The new synthesis
adds EIS QA and scalar baselines, semi-empirical comparators, replicate and
interval-calibration diagnostics, temporal-order falsification, knee and
threshold-label readiness, threshold-event warning hardening, and release
reproducibility.

Figure 1 summarizes the data-product architecture, Figure 2 summarizes grouped
validation, and Table 6 summarizes the main post-release gate status.

## Data Products and Validation

The benchmark uses linked data products rather than one flattened modeling
table. The interval table remains the modeling spine: one row represents a
transition from check-up `k` to `k+1`, with prior state, future target,
condition metadata, split labels, and quality flags. Large generated Parquets
remain local ignored artifacts; tracked reports and manifests carry the
reviewable evidence.

The release-candidate data-product stack covers:

- 904,977,105 LOG_AGE rows in the local ingested cohort;
- 3,827 modeled check-up intervals;
- grouped split labels over condition, temperature, C-rate, profile, and
  voltage-window views;
- LOG_AGE stress-feature sidecars;
- RT/50 PULSE target sidecars;
- RT/50 EIS feature and target sidecars;
- run-event and sequence-feature sidecars;
- knee, threshold-event, and threshold-warning label products.

The validation protocol treats condition triplets as the headline grouping
unit. Random splits are not used as paper-facing evidence. Leakage controls
mask inserted future diagnostics, exclude target-derived rates from predictive
feature groups, and restrict prospective threshold-warning features to
check-up-`k` state and metadata.

The release package records this design in the benchmark reproducibility guide,
runbook, command DAG, artifact manifest, release checker, and release notes.
Table 8 summarizes the release-candidate artifact policy.

## Capacity and LOG_AGE Evidence

The capacity ladder establishes the benchmark baseline. HGB-50 with state,
time, nominal metadata, and LOG_AGE scalar summaries is the primary scalar
capacity baseline before stress sidecars and diagnostic modalities enter. The
C-rate holdout remains the hardest view: the focused F4 C-rate condition-mean
MAE is 0.125186 for `capacity_Ah_k1` and 0.101133 for `delta_capacity_Ah`.

LOG_AGE scalar summaries help some nonlinear grouped views, but the effect is
mixed. Stress-feature v1.1 improves the C-rate capacity-level row from 0.125186
to 0.120605, but C-rate `delta_capacity_Ah` remains worse than the F4
threshold at 0.102516. Normalized rate targets, train-fold bias correction, and
narrow cold/current groups do not solve the C-rate fade problem.

These results set the first major benchmark boundary: operating-history scalar
features are useful and scientifically relevant, but the current scalar
features do not close the C-rate fade gap.

## PULSE and EIS Diagnostic Endpoints

PULSE is supported as a scalar resistance diagnostic endpoint. Canonical RT/50
PULSE coverage is sufficient for scalar resistance baselines, and PULSE growth
is associated with capacity residual magnitude in robustness diagnostics.
Prior PULSE improves `capacity_Ah_k1` over the F4 LOG_AGE scalar baseline in
selected grouped splits, but it does not beat the strongest supplied non-PULSE
baseline and does not support a fade-rate claim.

EIS is also a gated diagnostic modality. Milestone 2.0 established EIS QA,
coverage, valid-frequency masks, and RT/50 scalar feature readiness. Milestone
2.1 showed scalar EIS endpoints are predictable enough for diagnostic
baselines. Milestone 2.1.1 then compared prior EIS against strongest non-EIS
baselines and found only narrow profile-split prior-feature signal. C-rate
capacity, C-rate fade, DRT, learned EIS embeddings, and broad EIS outcome
claims remain blocked.

Figure 11 summarizes the EIS diagnostic gate.

## Domain Comparators, Replicates, and Interval Calibration

The charter requires domain and replicate-aware comparators before architecture
work. Semi-empirical ridge-style stress baselines provide that domain check.
They do not beat the strongest grouped HGB/stress baselines in the hardest
C-rate capacity and fade views, although they remain useful for interpreting
what flexible ML baselines add beyond simple physical stress terms.

Replicate diagnostics quantify within-condition triplet spread. For focused
HGB F4 C-rate rows, model error is close to empirical triplet spread for both
capacity level and delta targets. This contextualizes C-rate error, but it does
not turn the model intervals into validated uncertainty estimates.

Grouped conformal and replicate-hybrid intervals improve mean coverage but
still fail the C-rate coverage gate. Raw HGB q10/q90 intervals are
undercovered. These results keep global interval-reliability wording blocked.

Figure 12 summarizes the replicate and interval-calibration gate.

## Temporal Order, Knee Labels, and Threshold Events

The charter permits sequence models only if temporal order adds value beyond
aggregate exposure. Milestone 2.4 built a real LOG_AGE run-event table and
interval sequence-feature sidecar, then compared aggregate event summaries,
order-aware features, and shuffled-order controls. Ordered event summaries do
not beat aggregate or shuffled controls overall and do not improve the C-rate
view. Sequence models therefore remain blocked.

The degradation-acceleration track first evaluated detector-based knees. The
detector system produces many candidate labels, but replicate consistency is
not strong enough for prediction. Under the primary detector policy, only 45 of
64 primary-valid parameter-set conditions have replicate knees within two
check-ups.

Threshold-event labels are more stable. The best current candidate is
`capacity_below_80pct_initial`, with replicate consistency within two check-ups
of 0.897, condition coverage of 0.763, and median event check-up 8. Threshold
labels alone do not authorize a prediction claim, but they support the later
prospective warning baseline.

Figure 13 summarizes the temporal-order and knee/threshold gates.

## Threshold-Event Warning

The threshold-warning branch is the only late-stage track that produced a new
diagnostic forecasting signal. The prospective warning table uses only
check-up-`k` state, time, and nominal metadata. It excludes future capacity,
capacity deltas, future interval exposure, future PULSE/EIS state, and
diagnostic deltas.

The 3-check-up horizon is the primary threshold-warning result. HGB W2 beats
the event-rate prior and proximity baseline under both all-row and
verified-only censoring policies. Under verified-only evaluation, HGB W2 has
Brier 0.090116 versus 0.178655 for the event-rate prior and 0.168492 for the
proximity baseline. The C-rate view also remains strong after verified-only
sensitivity.

This supports diagnostic threshold-event forecasting. It does not authorize
probability calibration, policy ranking, detector-knee prediction, or causal
warning wording. Table 7 summarizes the threshold-warning hardening results,
and Figure 14 links the warning result to the release gate.

## Release-Candidate Reproducibility

The benchmark release track separates the pure validation checkpoint from the
reviewer-facing handoff archive. `benchmark-v0.1-rc1` remains the validation
checkpoint at commit `ff4c8c2`. `benchmark-v0.1-rc2` is the release-polished
handoff archive at commit `e499b12`; it includes the release summary, GitHub
release draft, future-branch notes, and handoff checklist.

Before tagging, the release checker passed, ruff passed, all 148 tests passed,
`git diff --check` passed, the worktree was clean, and no generated data or
Parquet artifacts were staged. The GitHub rc2 release is published as a
pre-release and points to `benchmark-v0.1-rc2`.

The release package is meant to support external review and future manuscript
work. It does not include raw data or generated Parquets, and it does not
change the scientific claim posture.

## Discussion

The strongest contribution is the benchmark discipline itself. The project
shows which signals survive grouped validation and which tempting branches
should remain closed. Capacity and LOG_AGE features define the core
generalization problem. PULSE and EIS add scalar diagnostic endpoints but do
not authorize broad multimodal claims. Semi-empirical and replicate-aware
comparators strengthen the benchmark by setting interpretable reference
points. Interval-calibration, temporal-order, and detector-knee gates block
overreach. Threshold-event forecasting provides a narrow diagnostic success,
but not policy or causal support.

The next substantive step is manuscript integration and venue targeting, not
CBAT, sequence models, DRT, EIS embeddings, or policy ranking. If another
technical branch is opened later, it should be limited to threshold-warning
calibration and should not change policy or causal claim boundaries unless a
new gated milestone supports it.

## Limitations

The benchmark is based on a laboratory dataset and should not be treated as
field-deployment evidence. The cohort is large for a detailed aging dataset but
still represents 76 operating conditions rather than hundreds of independent
regimes. EIS alignment deltas and missing selected-frequency rows remain
reported limitations. Run-event QA covers all intervals but has duration-sum
warnings for a subset of intervals. Detector-knee labels remain exploratory.
Threshold-warning probabilities are diagnostic scores, not calibrated risk
estimates. Policy ranking, same-cell counterfactuals, and architecture claims
remain outside the supported evidence.

