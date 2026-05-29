# Manuscript v0.7

Working title: A grouped-validation benchmark for battery degradation from
operating histories and gated diagnostic endpoints.

This venue-neutral draft tightens the v0.6 manuscript for reviewer preflight.
It uses `benchmark-v0.1-rc2` as the reproducibility anchor and keeps claim
traceability in `manuscript/manuscript_v0_7_traceability.md`.

## Abstract

Battery degradation benchmarks can overstate readiness when train and test
data share operating-condition structure. We present a reproducible
grouped-validation benchmark for degradation prediction from capacity
check-ups, LOG_AGE operating histories, PULSE resistance, and quality-gated EIS
diagnostics. The Luh-Blank cohort is treated as 76 parameter-set conditions
with three replicate cells each, and headline evidence uses condition-level and
stressor-axis holdouts rather than random row splits.

The benchmark closes a staged evidence ladder. Capacity and LOG_AGE baselines
show that C-rate transfer is the dominant unresolved capacity setting. RT/50
PULSE and RT/50 EIS are usable scalar diagnostic endpoints, but broad
multimodal and architecture claims remain blocked. Semi-empirical stress
comparators, replicate spread, grouped interval diagnostics, temporal-order
falsification, and knee-label stability tests constrain the claim posture. The
strongest late-stage positive result is narrow: non-neural baselines forecast
the 80% capacity-relative threshold event diagnostically, beyond proximity
baselines and under verified-only censoring sensitivity.

The contribution is a claim-bounded benchmark release candidate, not a new
architecture. The release package includes the runbook, command DAG, artifact
manifest, release checker, claim ledger, and source-linked synthesis reports
needed to audit and reproduce the evidence.

## Introduction

Battery degradation depends on realized stress history, diagnostic state, and
condition context. A useful benchmark must therefore test generalization to
held-out operating families and must separate supported evidence from
unsupported modeling branches.

The Luh-Blank dataset combines capacity check-ups, LOG_AGE operating histories,
PULSE resistance, and EIS records for 228 commercial cells. The design is 76
parameter-set conditions with three replicate cells each, so the benchmark
treats condition triplets as the primary grouping unit. Random splits are
retained only as leakage smoke tests.

This study asks which signals survive grouped validation. It builds versioned
data products, evaluates scalar baselines, opens diagnostic modalities only
after QA gates, challenges flexible models with domain comparators, and records
negative gates before any architecture work. Figure 1 summarizes the linked
data-product architecture, and Figure 2 summarizes grouped validation.

## Data Products and Validation

The interval table is the modeling spine. Each row represents the transition
from check-up `k` to `k+1`, carrying prior state, future target, condition
metadata, split labels, and quality flags. Large generated Parquets stay local
and ignored; tracked reports, manifests, and release checks carry reviewable
evidence.

The release-candidate stack covers 904,977,105 LOG_AGE rows, 3,827 modeled
intervals, grouped split labels, LOG_AGE stress-feature sidecars, RT/50 PULSE
targets, RT/50 EIS features and targets, run-event summaries, sequence
summaries, knee and threshold labels, and threshold-warning tables. Table 1
summarizes the audited cohort and interval population. Table 8 summarizes the
release artifact policy.

Leakage controls are explicit. Inserted future diagnostics are masked for
interval prediction. Target-derived rates remain diagnostic. Prospective
threshold-warning features are restricted to check-up-`k` state, time, and
nominal metadata. Future capacity, future PULSE/EIS state, diagnostic deltas,
and future interval exposure are excluded from warning inputs.

## Capacity and LOG_AGE Baselines

The capacity ladder establishes the core benchmark difficulty. HGB-50 with
state, time, nominal metadata, and LOG_AGE scalar summaries is the main scalar
capacity baseline before stress sidecars and diagnostic modalities are added.
The focused F4 C-rate condition-mean MAE is 0.125186 for `capacity_Ah_k1` and
0.101133 for `delta_capacity_Ah`.

LOG_AGE scalar summaries and stress features help in selected grouped views,
but gains are mixed. Stress-feature v1.1 improves the C-rate capacity-level row
from 0.125186 to 0.120605, while C-rate `delta_capacity_Ah` remains worse than
the F4 threshold at 0.102516. Normalized rate targets, train-fold bias
correction, and narrow cold/current feature groups do not close the C-rate fade
gap.

Figures 3, 4, and 5 summarize the capacity ladder, C-rate failure analysis, and
stress-feature decision. Tables 2, 3, and 5 summarize the model ladder, split
difficulty, and negative results.

## PULSE and EIS Diagnostic Endpoints

PULSE is supported as a scalar resistance diagnostic endpoint. Canonical RT/50
PULSE coverage is sufficient for scalar resistance baselines, and PULSE growth
is associated with capacity residual magnitude in robustness diagnostics.
Prior PULSE improves `capacity_Ah_k1` over the F4 LOG_AGE scalar baseline in
selected grouped splits, but it does not beat the strongest supplied non-PULSE
baseline and does not support a fade-rate claim.

EIS is also gated. EIS QA establishes archive coverage, valid-frequency masks,
SOC/RT-OT coverage, and RT/50 scalar feature readiness. Scalar EIS endpoints
are predictable enough for diagnostics, but prior EIS has only narrow
profile-split signal for non-EIS outcomes. C-rate capacity, C-rate fade, DRT,
learned EIS embeddings, and broad EIS outcome claims remain blocked.

Figures 6 through 9 summarize the PULSE QA, resistance endpoint, coupling, and
strongest non-PULSE comparison. Figure 11 summarizes the EIS scalar diagnostic
gate.

## Domain Comparators and Reliability Gates

Semi-empirical ridge-style stress baselines provide the charter-required domain
check before architecture work. They do not beat the strongest grouped
HGB/stress baselines in the hardest C-rate capacity and fade views, but they
remain useful reference points for interpreting flexible ML baselines.

Replicate diagnostics quantify within-condition triplet spread. In the focused
HGB F4 C-rate rows, model error is close to empirical triplet spread for both
capacity level and delta targets. This contextualizes failure modes without
turning model intervals into deployment-style reliability.

Raw HGB q10/q90 intervals are undercovered. Grouped conformal and
replicate-hybrid intervals improve average coverage but still fail the C-rate
coverage gate. Global interval-reliability wording remains blocked. Figure 12
summarizes the replicate and interval-diagnostic gate, and Table 6 places this
result in the full gate matrix.

## Temporal Order, Knee Labels, and Threshold Events

Sequence models are justified only if temporal order adds information beyond
aggregate exposure. The run-event table and sequence-feature sidecar enabled
aggregate, order-aware, and shuffled-order comparisons. Ordered event
summaries do not beat aggregate or shuffled controls overall and do not improve
the C-rate view. Sequence models remain blocked.

Detector-based knee labels are useful degradation-acceleration diagnostics but
not stable enough for prediction. Under the primary detector policy, only 45 of
64 primary-valid parameter-set conditions have replicate knees within two
check-ups. Threshold events are more stable: `capacity_below_80pct_initial`
reaches replicate consistency within two check-ups of 0.897, condition coverage
of 0.763, and median event check-up 8.

Figure 13 summarizes the temporal-order and knee/threshold gates.

## Threshold-Event Warning

The threshold-warning branch is the one late-stage track that supports a new
diagnostic forecasting statement. The prospective warning table uses only
check-up-`k` state, time, and nominal metadata. It excludes future capacity,
capacity deltas, future interval exposure, future PULSE/EIS state, and
diagnostic deltas.

The primary target is the 3-check-up horizon for
`capacity_below_80pct_initial`. HGB W2 beats both the event-rate prior and the
proximity baseline under all-row and verified-only censoring policies. Under
verified-only evaluation, HGB W2 has Brier 0.090116 versus 0.178655 for the
event-rate prior and 0.168492 for the proximity baseline. The C-rate view also
remains strong after verified-only sensitivity.

This supports diagnostic threshold-event forecasting. It does not authorize
risk-score calibration, policy ranking, detector-knee prediction, or causal
warning wording. Table 7 summarizes the warning hardening result, and Figure
14 links the warning result to the release gate.

## Release Package and Reproducibility

The release track separates the validation checkpoint from the reviewer-facing
handoff archive. `benchmark-v0.1-rc1` remains the validation checkpoint at
commit `ff4c8c2`. `benchmark-v0.1-rc2` is the release-polished handoff archive
at commit `e499b12` and is published as a GitHub prerelease.

The release package includes the benchmark reproducibility guide, runbook,
command DAG, artifact manifest, release checker, release notes, claim ledger,
and synthesis reports. It excludes raw data and generated Parquets. The v0.7
manuscript package changes presentation and review readiness, not the
scientific evidence.
Latest `main` also includes a post-rc2 status addendum and benchmark task
registry v2 for the completed negative Milestone 9 neural-sequence gate.

## Discussion

The benchmark's main contribution is disciplined evidence separation. Capacity
and LOG_AGE baselines define the core C-rate generalization problem. PULSE and
EIS provide scalar diagnostic endpoints but not broad multimodal claims.
Semi-empirical and replicate-aware comparators force flexible ML results to
compete against interpretable references. Interval diagnostics, temporal-order
falsification, and knee-label stability tests prevent unsupported interval,
sequence, and knee-prediction claims. Threshold-event forecasting is the
strongest late-stage positive result, but it remains diagnostic and
support-bounded.

The next scientific branch should not be CBAT, sequence models, DRT, EIS
embeddings, detector-knee prediction, policy ranking, or causal analysis. If a
technical branch is opened later, it should be limited to threshold-warning
calibration and should preserve the current claim gates.
A post-rc2 pre-CBAT neural-sequence architecture gate tested v2 fixed-length
event tensors with CUDA CNN/TCN/CNN-LSTM baselines. It did not pass the
predeclared shuffled-order, aggregate-event HGB, timestamp-stress HGB, or C-rate
controls, so neural sequence and CBAT readiness remain blocked.

## Limitations

The benchmark uses a laboratory cohort and does not establish field-deployment
readiness. The 228 cells represent 76 operating conditions rather than 228
independent regimes. EIS alignment deltas and selected-frequency missingness
remain reported limitations. Run-event QA covers all intervals but has
duration-sum warnings for a subset of intervals. Detector-knee labels remain
exploratory. Threshold-warning probabilities are diagnostic scores, not
validated risks. Policy ranking, same-cell counterfactuals, and architecture
claims remain outside the supported evidence.
The post-rc2 Milestone 9 architecture gate is negative evidence, not CBAT
progress.
