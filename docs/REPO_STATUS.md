# Repository Status

Last updated: 2026-05-28

Current branch: `main`

Current commit: see `git log -1 --oneline`. This file is updated whenever
significant repository state changes happen, but it intentionally avoids a
self-referential commit hash that would become stale when the status file itself
is committed.

## Executive Summary

The repository is in **Milestone 8.8: reconstruction failure forensics and C-rate branch closure**.
Gate 2b LOG_AGE integrity triage, Milestone 0.4 baseline readiness, the first
bounded Milestone 0.5 capacity baseline ladder, Milestone 0.5b robustness
diagnostics, Milestone 0.5c synthesis, and Milestone 0.6 stress-feature v1 are
complete. Milestone 0.6.1 stress-feature hardening and Milestone 0.6.2 target
consistency diagnostics are complete. Milestone 0.6.3 closed the broad
LOG_AGE-only scalar stress-feature path for the current C-rate delta problem.
Milestone 0.7 opened a scoped PULSE QA-first resistance evidence stream.
Milestone 0.7.1 hardened that stream before any PULSE scientific claim.
Milestone 0.7.2 finalized scalar target robustness and claim-readiness.
Milestone 0.8 opens controlled scalar capacity-PULSE coupling diagnostics.
Milestone 0.8.1 hardens that evidence with canonical-model filtering,
interval-level aggregation, condition-level aggregation, parameter-set bootstrap
summaries, and simple confound-control residualization.
Milestone 0.9 tests a narrow non-neural predictive claim using prior PULSE state
at check-up `k` only.
Milestone 0.9.1 compares that prior-PULSE result against the strongest supplied
non-PULSE HGB baselines on the same PULSE-covered interval population.
Milestone 1.0 consolidates the completed capacity, LOG_AGE stress-feature,
PULSE resistance, coupling, and prior-PULSE evidence into a paper-facing claim
ledger, synthesis report set, figure plan, and paper skeleton.
Milestone 1.0.1 hardens those paper-facing artifacts with wording refinements,
source-artifact checklists, reviewer-risk tracking, and manuscript packaging.
Milestone 1.1 creates a manuscript-ready draft package with prose sections,
figure/table specifications, source traceability, and reviewer response prep.
Milestone 1.2 turns that package into generated manuscript assets and a
continuous v0.2 draft using only existing tracked reports and synthesis
artifacts.
Milestone 1.3 polishes the manuscript assembly, fixes Figure 6 PULSE QA
extraction, adds figure data checks, and expands no-overclaim checks across
paper-facing manuscript files.
Milestone 1.4 converts the internally traceable manuscript into a reader-facing
v0.4 draft, preserving claim/source mapping in sidecar traceability files.
Milestone 1.4.1 removes the last reader-facing scaffold block, hardens checks,
and removes internal draft labels from v0.4 SVG figures.
Milestone 2.0 opens EIS as a gated QA and scalar feature-readiness modality,
not as a modeling or claim milestone.
Milestone 2.1 evaluates RT/50 scalar EIS endpoints and prior-EIS feature groups
under grouped validation while keeping broad EIS claims blocked.
Milestone 2.1.1 hardens those results with strongest non-EIS paired
comparisons, parameter-set bootstrap intervals, alignment sensitivity,
feature-completeness sensitivity, and leakage audits before any EIS claim is
strengthened.
Milestone 2.2 adds charter-required semi-empirical stress comparators and
condition-triplet replicate uncertainty diagnostics before any architecture
work.
Milestone 2.3 evaluates raw HGB quantile coverage, grouped conformal
calibration, stressor-family conformal calibration, and replicate-aware hybrid
interval diagnostics before any calibrated-uncertainty claim is allowed.
Milestone 2.4 builds a LOG_AGE-derived run-event table and interval
sequence-feature sidecar, then tests aggregate event summaries, order-aware
features, and shuffled-order controls under grouped non-neural capacity
baselines before any sequence-model work is allowed.
Milestone 2.5 extracts capacity trajectories and evaluates degradation-knee
candidate labels across detector, x-axis, smoothing, and replicate-triplet
sensitivity before any knee-warning model is allowed.
Milestone 2.5.1 diagnoses the primary knee replicate-consistency failures,
builds a stable-condition registry, and evaluates threshold-event labels as a
possible more stable early-warning target family before any prediction model is
allowed.
Milestone 2.6 builds a prospective leakage-safe `capacity_below_80pct_initial`
warning table and evaluates non-neural grouped classifier baselines before any
threshold-event warning claim is strengthened.
Milestone 2.6.1 hardens that result with distance-to-threshold and
prior-only extrapolation baselines, lead-time/proximity diagnostics,
censoring-policy sensitivity, and probability-calibration checks.
Milestone 2.6.2 adds verified-only censoring sensitivity and final
claim-readiness matrices before locking any threshold-warning wording.
Milestone 3.0 consolidates all completed main-project gates into a refreshed
technical claim ledger, gate-status matrix, blocked-claim review, and
next-branch decision without adding new models or features.
Milestone 3.1 turns that checkpoint into a reproducible release-candidate
package with a runbook, command DAG, artifact manifest, release checklist,
manual release-candidate check, and Codex next-work guide. It adds no new
models, features, or scientific claims.
Milestone 3.2 makes the release-candidate checks executable with
`mbp report check-release-candidate`, adds v0.1-rc1 release notes and tagging
instructions, and keeps the release tag path auditable without adding new
science.
Milestone 3.3 polished the already-tagged release-candidate handoff with a
release summary, handoff checklist, GitHub release draft text, and future
branch organization notes. `benchmark-v0.1-rc2` is the reviewer-facing
release candidate at commit `e499b12`; it includes the release-polish docs and
has been published as a GitHub prerelease. The rc2-specific release notes,
summary, draft text, and handoff check are tracked alongside the original rc1
validation checkpoint notes. Milestone 4.0 integrated that claim-bounded
benchmark evidence into a v0.5 manuscript draft. Milestone 4.1 turned that
draft into a venue-neutral v0.6 reviewer-ready manuscript package with a
supplement scaffold, traceability sidecar, and manuscript package checks.
Milestone 4.2 hardens the v0.6 package against likely reviewer objections and
adds v0.7 submission-preflight materials without adding new science.
Milestone 4.3 packages the validated v0.7 manuscript and
`benchmark-v0.1-rc2` release evidence into a venue-neutral v0.8 submission
bundle for human review, venue selection, or external collaborator handoff
without adding new science.
Milestone 4.4 aligns the root README, package description, public-review
entry point, repository metadata checklist, venue-targeting matrix, and
submission-readiness triage with that release/manuscript handoff package
without adding new science. Milestone 5.0 reopens only the narrow optional
technical branch left by the synthesis decision matrix: grouped post-hoc
probability calibration for the existing non-neural 80% threshold-event
warning baseline. It adds Platt/logistic and isotonic calibration diagnostics
with train/calibration/test condition separation and does not add new feature
engineering, detector-knee prediction, policy ranking, causal claims, CBAT, or
neural/sequence models. Milestone 5.1 tests whether non-neural stressor-axis
robust HGB variants can improve the hard C-rate capacity/fade split without
degrading other grouped views. It finds a strong C-rate `delta_capacity_Ah`
diagnostic improvement for stressor-balanced HGB, but the global robust-capacity
claim remains not supported because the non-degradation guardrail narrowly
fails on another split.
Milestone 5.2 adds review-requested calibration and quantile hygiene: it reports
equal-frequency ECE alongside fixed-width ECE for threshold-warning diagnostics
and enforces noncrossing L3 capacity quantile endpoints by row-wise sorting
while preserving q50 point predictions. The refreshed reports do not unblock
calibrated-risk, calibrated-uncertainty, robust-capacity, policy, or
architecture claims. Milestone 5.3 hardens the existing calibration and
stressor-robustness gates against silent correctness failures: required
all-row/verified-only policy checks are now explicit, C-rate calibration gates
are policy-specific, fallback-raw calibration rows cannot pass strict
readiness, empty metric runs fail instead of writing passed reports, Platt
calibration uses the unpenalized logistic convention, and stressor-robust
readiness no longer treats missing outside-C-rate evidence as support.
Milestone 5.4 diagnoses the stressor-robust near miss and runs a bounded
Pareto grid over existing non-neural robust HGB variants. The predeclared
R2/F8 full-strength setting still improves C-rate `delta_capacity_Ah`, but it
fails the 5% outside-C-rate non-degradation guardrail at `0.0528343`, so the
robust-capacity claim remains diagnostic-only/not supported.
Milestone 5.5 tests whether train-only inner grouped validation can choose a
conservative stressor-balanced weight that keeps the C-rate `delta_capacity_Ah`
gain while satisfying the unchanged 5% outside-C-rate guardrail. The
max-gain adaptive selector improves C-rate but fails the guardrail at
`0.0645764`; the conservative selector passes diagnostically with C-rate gains
of `0.0200436` versus F4 and `0.0214266` versus the stress R0 reference,
paired p05 values above zero, and max outside-C-rate degradation `0.0279117`.
This supports only a narrow train-only adaptive robust-selection diagnostic,
not a claim that C-rate fade is solved or that architecture work is justified.
Milestone 5.6 replicates that adaptive selector result under the deterministic
HGB/no-bagging seed interface. The conservative selector passes all five
logical seeds with deterministic seed reuse recorded explicitly; the max-gain
policy still fails the unchanged outside-C-rate guardrail. The replicated
result supports only the narrow diagnostic C-rate `delta_capacity_Ah`
robust-selection claim.
Milestone 5.7 decomposes the replicated adaptive result into F4/F8 and R0/R2
attribution arms to test whether the C-rate `delta_capacity_Ah` gain comes from
timestamp-weighted stress features, train-only reweighting, or their
combination. F8 adds incremental C-rate delta signal under adaptive selection
(`0.00940756`, paired p05 `6.06012e-05`), and the combined adaptive F8 arm
keeps the Milestone 5.6 C-rate gain (`0.0200436` versus F4), but the
incremental F8 comparison fails the outside-C-rate non-degradation guardrail
because voltage-window `delta_capacity_Ah` degrades heavily
(`0.717391`). The result is attribution-diagnostic only.
Milestone 5.8 evaluates a narrow stressor-family router over existing
attribution arms. The router uses D2 adaptive R2/F4 for the C-rate transfer
view when its train-only adaptive guardrail passes and routes non-C-rate
stressor views to D0 R0/F4. It preserves the reweighting-only C-rate
`delta_capacity_Ah` gain (`0.0106361`, paired p05 `0.00594397`) and has
zero outside-C-rate degradation by construction because non-C-rate views route
to D0. This supports only a targeted diagnostic routing claim, not broad
robust capacity or solved C-rate fade.
Milestone 5.9 adds a charter-required L5-style hierarchical replicate-aware
capacity comparator using train-only residual partial pooling over stressor
families and replicate-variance interval diagnostics. It produces 288 metric
rows and 213,672 ignored prediction rows. The H4/F4 partial-pooling arm gives
only a tiny C-rate `delta_capacity_Ah` gain versus the H3/F4 HGB reference
(`0.000100645`), and paired bootstrap p05 is negative (`-1.88643e-05`), so
the hierarchical C-rate delta result is diagnostic-only. Replicate-variance
interval coverage also fails (`0.312102` for C-rate delta and minimum primary
coverage `0.151596`), so calibrated uncertainty remains blocked.
Milestone 6.0 adds a non-neural multi-horizon capacity forecasting gate for
horizons 1, 2, 3, and 5 check-ups. `capacity_horizon_table_v1.parquet`
contains 13,770 observed horizon rows across 228 cells and 76 parameter sets.
The prospective HGB K2 nominal-condition model beats persistence and
prior-slope baselines for C-rate horizons 2 and 3 on both
`capacity_Ah_kh` and `delta_capacity_Ah_h`, but the all-split capacity-level
horizon-3 row narrowly misses the prior-slope baseline. Therefore the
multi-horizon result is partially supported overall, C-rate multi-horizon and
delta-capacity diagnostics are supported for diagnostics, and K3 future
exposure remains oracle-diagnostic only.
Milestone 6.1 diagnoses that partial result with report-based error forensics:
HGB K2 still beats persistence and prior-slope references for the C-rate
horizon-2/3 rows, but the all-split horizon-3 capacity-level row remains a
near miss. The forensics identify prior-slope failure bins, C-rate condition
hotspots, and K3 oracle gains while keeping K3 non-prospective. The only
possible future technical branch is a predeclared prior-trajectory-shape audit;
sequence/neural models, CBAT, policy ranking, causal claims, and calibrated
risk/uncertainty remain blocked.
Milestone 6.2 runs that predeclared prospective prior-trajectory-shape audit.
`capacity_horizon_trajectory_features_v1.parquet` contains 13,770 prior-only
feature rows and passes leakage/coverage QA. The K5 nominal-plus-trajectory HGB
arm is partially useful in a few rows, but it does not repair all-split
horizon-3 `capacity_Ah_kh` (`0.0981241` versus K2 `0.0935304` and prior slope
`0.0932329`) and does not preserve all C-rate horizon-2/3 target rows. The
trajectory branch is therefore partial/diagnostic only.
Milestone 7.0 freezes the completed evidence base into
`configs/benchmark_tasks_v1.yaml`, validates it with
`mbp report check-benchmark-tasks`, and renders the task-level leaderboard,
task cards, and model-family cards from existing tracked reports only. It adds
no new models, feature engineering, or scientific claims.
Milestone 7.1 reopens the sequence question only as a charter H7 falsification
check: a fixed-length LOG_AGE run-event sequence product is compared against
deterministic shuffled-order controls, aggregate-event HGB, and
timestamp-stress HGB references. CUDA-enabled PyTorch `2.12.0+cu130` was
installed in the project virtualenv and verified on the WSL-visible RTX 5060
Ti. The GPU Torch MLP rows ran, but no true-sequence candidate passed the
predeclared aggregate/stress/C-rate controls; sequence/neural next-gate
readiness, CBAT, and policy ranking remain blocked.
Milestone 7.2 evaluates charter H6/Q4 support before any policy-ranking model:
it builds `policy_contrast_registry_v1.parquet`, support QA, observed
capacity-loss sign-stability diagnostics, and claim-readiness reports from the
existing interval table only. The gate finds 234 triplet-supported observed
contrasts across charge C-rate, temperature, voltage-window, and profile
families, with 2,943 of 3,213 observed capacity-loss rows sign-stable. This
supports only an observed policy-contrast support diagnostic and a possible
future ranking-feasibility gate. It does not authorize policy ranking, policy
recommendations, causal/same-cell counterfactual claims, CBAT, sequence/neural
models, or calibrated risk.
Milestone 7.3 consumes the existing out-of-fold multi-horizon prediction table
and the Milestone 7.2 contrast registry to test whether prospective HGB K2
predictions can order supported observed contrasts. It generates 164,100
pairwise contrast-ordering rows and finds useful but incomplete signal:
primary HGB K2 `delta_capacity_Ah_h` sign accuracy averages 0.780 across
primary horizon/split rows, with C-rate rows at 0.826923 for horizon 2 and
0.888889 for horizon 3, but it fails the strict bootstrap reference gate versus
the prior-slope baseline (`0/10` primary all-family reference checks pass).
The result is therefore only `partially_supported` for supported observed
contrast-ordering diagnostics. Policy recommendation, causal claims, same-cell
counterfactual claims, calibrated risk/utility, CBAT, and sequence/neural
branches remain blocked.
Milestone 7.4 diagnoses that 7.3 failure without retraining models or adding
features. It consumes the existing 7.3 pairwise/by-family/bootstrap CSVs and
writes effect-size-thresholded sign accuracy, rank-correlation, top-k/regret,
and HGB-vs-prior failure-bin diagnostics. The forensics are supported for
diagnostics: oracle K3 rows are excluded from readiness, `0/10` strict
HGB-vs-prior all-family checks still pass, large-effect diagnostics are only
`diagnostic_only`, and policy recommendation, causal/same-cell
counterfactual, calibrated policy risk/utility, CBAT, and sequence/neural
branches remain blocked.
Milestone 8.0 audits support-aware selective reliability over existing
prediction artifacts only. `mbp analysis diagnose-support-reliability`
computes train-only condition-support distances and retention curves for
capacity-horizon forecasts, threshold-warning scores, and supported
contrast-ordering rows. It generates 380 support-distance rows, 2,000
capacity selective rows, 975 threshold-warning selective rows, and 1,680
policy-contrast selective rows. The result supports support-distance auditing
for diagnostics, but selective prediction reliability remains
`diagnostic_only`: 50% retention worsens the primary capacity MAE by
`0.0115957` and threshold-warning Brier by `0.0040389`, while policy sign
accuracy improves by only `0.0173861`. C-rate support reliability is
`not_supported` because primary C-rate capacity MAE worsens by `0.0525537`.
Policy recommendation, causal/same-cell counterfactual claims, calibrated risk,
CBAT readiness, and deployment wording remain blocked.
Milestone 8.1 tests charter Q2/H3 with a leakage-safe non-neural
diagnostic-state distillation gate. Stage-A auxiliary models predict current
PULSE/EIS scalar diagnostic state from check-up-k capacity/state/time/nominal
fields using train-only inner grouped out-of-fold predictions; Stage-B
downstream models receive only those predicted diagnostic-state features. The
real-data run generates 480 downstream metric rows and 72 auxiliary metric
rows. All 12 auxiliary leaderboard rows beat train-mean baselines, but D3
predicted PULSE+EIS state does not improve the all-split primary downstream
tasks: best all-split D3 capacity relative gain is `-0.00790693`, all-split
threshold-warning relative Brier gain is `-0.0620807`, and C-rate
non-collapse fails. Diagnostic-state distillation is therefore
`not_supported`, and capacity+PULSE+EIS architecture, CBAT, calibrated risk,
policy ranking, sequence/neural branches, and causal/same-cell
counterfactual claims remain blocked.
Milestone 8.2 tests whether future PULSE/EIS scalar diagnostic endpoints can
be forecast directly over 1/2/3/5-check-up horizons using only check-up-k
capacity/state/time/nominal fields and current same-diagnostic state. The
diagnostic-horizon table passes QA with 80,878 rows across 228 cells, 76
parameter-set conditions, six scalar diagnostic targets, and four horizons.
The grouped non-neural baseline run generates 2,880 metric rows and 2,176,320
prediction rows. DH3 HGB with capacity plus current same-diagnostic state
shows useful gains in many rows, but the strict claim gate is only
`partially_supported`: 21/24 primary horizon-2/3 rows pass the 10% gain rule,
while 22/24 C-rate rows avoid negative gain. CBAT, broad multimodal
architecture, calibrated-risk/uncertainty, policy ranking, sequence/neural
branches, and causal/same-cell counterfactual claims remain blocked.
Milestone 8.2.1 explains the partial result using the existing diagnostic
horizon report, prediction Parquet, and target table only. It generates
432 endpoint-reference forensics rows, target/horizon gain matrices,
persistence-ceiling diagnostics, condition error hotspots, and endpoint-level
claim readiness. Endpoint-specific diagnostics are strongest for
`eis_z_abs_1kHz`, `nyquist_semicircle_width_proxy`, and
`pulse_10ms_resistance`, which pass the strict endpoint-specific diagnostic
rows. `eis_phase_1kHz`, `nyquist_im_peak_abs`, and `pulse_1s_resistance`
remain partial because at least one primary or C-rate guardrail fails. This
finalizes the gate as selected scalar endpoint diagnostic evidence only.
Milestone 8.3 re-audits the early extraction layer before trusting further ML
results. `mbp audit validate-extraction` rebuilds CFG/EOC/PULSE/EIS products
from raw result archives into an ignored validation directory, compares
current and rebuilt Parquets by row count, schema, and semantic digest, and
renders raw-to-Parquet golden-record checks plus parser-contract evidence. The
full validation passed for `cell_condition_table`, `checkup_event_table`,
canonical PULSE raw/summary, the legacy projected PULSE alias, EIS, EIS
quality products, and LOG_AGE. Full LOG_AGE validation uses a persistent
ignored CSV cache so the archive can be extracted once and reused for repeated
rebuild checks; incomplete caches from stopped runs are rejected unless they
contain at least the expected CSV count. The current and rebuilt LOG_AGE
Parquets matched `904,977,105` rows by streaming pairwise value equality.
Milestone 8.4 opens a report-only C-rate generalization diagnostic over
existing capacity prediction artifacts. `mbp analysis diagnose-c-rate-generalization`
reads the stress-feature HGB report, row-level predictions, interval metadata,
and stress-feature sidecar, then renders C-rate condition hotspots, train-only
support-overlap rows, stress-feature high-error associations, and conservative
claim-readiness. The real-data diagnostic generated 336 condition-hotspot
rows, 76 support-overlap rows, and 30 stress-error association rows. It found
52 of 76 C-rate condition rows below the support-score threshold. This is
root-cause evidence only and does not train or authorize a repair model.
Milestone 8.5 finalizes the repair decision by synthesizing the Milestone 8.4
C-rate support/root-cause report with the existing train-only adaptive
stressor-robust replication result and targeted stressor-family arm-router
result. `mbp analysis finalize-c-rate-repair-feasibility` generates a
decision report and claim-readiness matrix. It supports only narrow diagnostic
C-rate `delta_capacity_Ah` repair wording: train-only adaptive selection and
targeted routing pass their existing non-neural guardrails, while broad robust
capacity, solved C-rate fade, architecture, policy ranking, calibrated risk,
calibrated uncertainty, neural/sequence branches, CBAT, and causal claims
remain blocked.
Milestone 8.6 tests the boundary of that narrow repair claim by rerunning the
existing non-neural adaptive and targeted-router tools with both
`delta_capacity_Ah` and `capacity_Ah_k1`, then diagnosing target transfer,
outside-split guardrails, paired condition support, and support-stratified
gains. The result keeps the claim narrow: `delta_capacity_Ah` repair still
passes, but `capacity_Ah_k1` transfer is not supported. The adaptive R2/F8
C-rate capacity-level row is worse than F4 (`-0.00527031`) and the stress
reference (`-0.00801457`), and the targeted router gives zero C-rate
capacity-level gain. Two-target C-rate repair, broad robust capacity, solved
C-rate fade, architecture, policy ranking, calibrated risk/uncertainty,
neural/sequence branches, CBAT, and causal claims remain blocked.
Milestone 8.7 tests whether the successful `delta_capacity_Ah` repair can be
converted into `capacity_Ah_k1` by the algebraic reconstruction
`capacity_Ah_k + predicted_delta`. The derived capacity path has positive
C-rate gains versus direct capacity references (`0.0440972` adaptive versus
F4 and `0.0346897` router versus F4), but the router-derived capacity path
fails the outside-split guardrail with max degradation `0.293828`. The result
keeps capacity-from-delta transfer, two-target repair, broad robust capacity,
solved C-rate fade, architecture, policy ranking, calibrated risk/uncertainty,
neural/sequence branches, CBAT, and causal claims blocked.
Milestone 8.8 explains that failure with report-only forensics over the same
existing prediction artifacts and interval metadata. It finds two failing
direct-reference outside-split reconstruction comparisons: router-derived
capacity fails the profile holdout (`0.293828` relative degradation), and the
adaptive capacity-from-delta path fails against the direct F4 capacity
reference in the voltage-window holdout (`0.344864`). There are 58 degrading
condition hotspots, support overlap is not available for enough outside-split
hotspots to reopen the branch, and QA flags are diagnostic context rather than
a reason to ignore the guardrail. The capacity-level reconstruction branch is
closed for the current evidence.

No DRT features, EIS embeddings, future EIS state or EIS deltas as non-EIS
inputs, capacity+PULSE+EIS multimodal models, unscoped sequence models,
neural architecture, knee prediction, policy ranking, CBAT architecture, or
broad EIS improvement claims have been started. Milestone 7.1 adds only a
minimal CUDA Torch MLP diagnostic as a falsification check, not an architecture
branch.

Current state:

- Milestone 8.8 is a reconstruction failure forensics gate over existing
  Milestone 8.7 prediction artifacts and interval metadata. It adds
  `mbp analysis diagnose-reconstruction-failure`,
  `reports/analysis/reconstruction_failure_forensics/reconstruction_failure_report.json`,
  `reconstruction_failure_decision.md`,
  `reconstruction_failure_claim_readiness.md`,
  `plots/outside_failure_by_split.csv`,
  `plots/failing_condition_hotspots.csv`, and
  `plots/path_error_decomposition.csv`. It confirms that the
  capacity-from-delta transfer failure is broad enough to close the current
  capacity-level repair branch: two outside-split direct-reference comparisons
  fail, 58 condition hotspots degrade, and support/QA context does not
  authorize a repair claim.

- Milestone 8.7 is a target-consistency reconstruction audit over existing
  non-neural C-rate repair predictions. It adds
  `mbp analysis diagnose-target-consistency-reconstruction`,
  `reports/analysis/target_consistency_reconstruction/target_consistency_reconstruction_report.json`,
  `target_consistency_reconstruction_decision.md`,
  `target_consistency_claim_readiness.md`,
  `plots/direct_vs_derived_target_paths.csv`,
  `plots/c_rate_reconstruction_gain.csv`, and
  `plots/outside_split_reconstruction_guardrail.csv`. It confirms that
  capacity-from-delta reconstruction is useful diagnostically on the C-rate
  row but fails the unchanged outside-split guardrail for the targeted router,
  so two-target and capacity-level repair remain unsupported.

- Milestone 8.6 is a boundary audit over existing non-neural C-rate repair
  machinery. It adds `mbp analysis diagnose-c-rate-repair-boundary`,
  `reports/analysis/c_rate_repair_boundary/c_rate_repair_boundary_report.json`,
  `c_rate_repair_boundary_decision.md`,
  `c_rate_repair_boundary_claim_readiness.md`,
  `plots/target_boundary_matrix.csv`,
  `plots/split_guardrail_matrix.csv`, and
  `plots/support_stratum_gain_matrix.csv`. It confirms that the C-rate repair
  wording remains limited to diagnostic `delta_capacity_Ah`; capacity-level
  transfer and two-target repair wording are not supported.

- Milestone 8.5 is a report-only/non-retraining C-rate repair finalization
  gate. It adds `mbp analysis finalize-c-rate-repair-feasibility`,
  `reports/analysis/c_rate_repair_feasibility/c_rate_repair_feasibility_report.json`,
  `c_rate_repair_decision.md`, `c_rate_repair_claim_readiness.md`,
  `plots/c_rate_repair_evidence_matrix.csv`, and
  `plots/c_rate_repair_support_summary.csv`. The gate supports narrow
  diagnostic C-rate `delta_capacity_Ah` repair wording only.
- Milestone 8.4 is a report-only C-rate generalization root-cause gate. It adds
  `mbp analysis diagnose-c-rate-generalization`,
  `reports/analysis/c_rate_generalization/c_rate_failure_report.json`,
  `c_rate_failure_summary.md`, `c_rate_condition_hotspots.csv`,
  `c_rate_support_overlap.csv`, `plots/c_rate_stress_error_bins.csv`, and
  `c_rate_claim_readiness.md`. The diagnostic supports C-rate failure
  forensics only; new repair-model, architecture, policy, calibrated-risk, and
  causal readiness remain blocked.
- Milestone 8.3 is a foundational extraction reproducibility gate. It adds
  `mbp audit validate-extraction`,
  `reports/audit/extraction_validation/extraction_validation_report.json`,
  `extraction_rebuild_hashes.csv`, `raw_to_parquet_golden_records.csv`,
  `parser_contract_audit.csv`, and `extraction_validation_summary.md`. The
  full rebuild passed against current interim products. LOG_AGE matched
  `904,977,105` rows by streaming pairwise value equality while using
  `data/interim/log_age_csv_cache_v2` as an ignored persistent cache with
  `--skip-log-age-extract`, `--keep-log-age-extracted`, and
  `--expected-log-age-csv-count 228` so a partial stopped extraction cannot be
  reused silently.
- Milestone 8.2.1 is a report-only diagnostic-horizon forensics gate over the
  existing 8.2 report, prediction Parquet, and target table. It adds
  `mbp baseline diagnose-diagnostic-horizon`,
  `diagnostic_horizon_forensics.md`,
  `diagnostic_horizon_endpoint_claim_readiness.md`, and plot-ready CSVs for
  endpoint failures, target/horizon gains, C-rate failures, persistence
  ceilings, and condition hotspots. It does not retrain models or create new
  feature/data products.
- Milestone 8.2 is a non-neural multi-horizon diagnostic endpoint forecasting
  gate over existing interval, PULSE target, and EIS target tables. It adds
  `mbp analysis build-diagnostic-horizon-table`,
  `mbp analysis diagnostic-horizon-qa`, and
  `mbp baseline run-diagnostic-horizon`; creates an ignored
  `diagnostic_horizon_table_v1.parquet`, an ignored prediction Parquet, a QA
  report, coverage CSV, baseline JSON, leaderboard, reference-gain CSVs, and
  claim-readiness markdown. The result is partial: current same-diagnostic
  state helps many future diagnostic endpoint rows, but the full primary gain
  and C-rate non-collapse rules do not pass.
- Milestone 8.1 is a non-neural diagnostic-state distillation gate over
  existing capacity-horizon, threshold-warning, PULSE target, and EIS target
  tables. It adds `mbp baseline run-diagnostic-state-distillation`,
  `reports/baselines/diagnostic_state_distillation_report.json`, an ignored
  prediction Parquet, diagnostic-state gain CSVs, auxiliary surrogate accuracy
  CSVs, and claim-readiness markdown. The result is negative for downstream
  Q2/H3 support: predicted diagnostic state is learnable but does not improve
  the primary capacity-horizon or threshold-warning tasks and fails C-rate
  non-collapse.
- Milestone 8.0 is a report-only support-aware selective reliability gate over
  existing capacity-horizon, threshold-warning, and supported policy-contrast
  prediction artifacts. It adds
  `reports/analysis/support_reliability/support_reliability_report.json`,
  `support_reliability_diagnostics.md`,
  `support_reliability_claim_readiness.md`, and plot-ready CSVs for support
  distances and selective capacity, threshold-warning, and policy-contrast
  performance. The gate supports only support-distance diagnostics; selective
  reliability is diagnostic-only and C-rate support reliability is not
  supported.
- Milestone 7.4 is a report-only forensics gate over the existing Milestone
  7.3 CSVs. It adds
  `reports/analysis/policy/policy_ranking_failure_forensics_report.json`,
  `policy_ranking_failure_forensics.md`, and plot-ready CSVs for
  effect-size thresholds, rank correlations, top-k/regret diagnostics, and
  HGB-vs-prior failure bins. It supports only failure decomposition and does
  not authorize policy recommendation, causal/counterfactual claims,
  calibrated policy risk, CBAT, or sequence/neural work.
- Milestone 7.3 is an existing-prediction feasibility gate for supported
  observed contrast ordering, not a policy-recommendation or causal milestone.
  It joins `policy_contrast_registry_v1.parquet`,
  `capacity_horizon_table_v1.parquet`, and
  `capacity_horizon_l0_l2_predictions.parquet`, writes 164,100 pairwise rows,
  and marks supported observed contrast ordering as `partially_supported`.
  HGB K2 is informative but does not beat the prior-slope reference under the
  strict bootstrap rule, so recommendation, causal, counterfactual, calibrated
  risk/utility, CBAT, and sequence/neural claims remain blocked.
- Milestone 7.2 remains the observed support/stability basis for this gate:
  `policy_contrast_registry_v1.parquet` contains 234 matched
  triplet-supported observed contrasts, and observed capacity-loss sign
  stability is high overall (`2943/3213 = 0.916` rows).

- Milestone 7.1 is a minimal sequence/neural reopening gate. It builds
  `interval_event_sequence_table_v1.parquet` with 3,827 interval rows and
  fixed 64-event vectors from the 79,328,229-row run-event product. QA passes
  with no missing intervals, no vector/mask length errors, and no leakage
  columns; 3,826 intervals are truncated because real event counts are much
  longer than the fixed diagnostic vector.
- The Milestone 7.1 GPU run generated 96 metric rows. CUDA Torch MLP execution
  is supported for diagnostics (`torch 2.12.0+cu130`, CUDA runtime 13.0, RTX
  5060 Ti), but true sequence still does not reopen the sequence/neural gate:
  mean gain versus shuffled is `0.0290673` with `26/48` positive rows, mean
  gain versus aggregate-event HGB is `-0.227321` with `0/48` positive rows,
  mean gain versus timestamp-stress HGB is `-0.190925` with `0/44` positive
  rows, and C-rate `delta_capacity_Ah` has only `1/6` positive comparison rows
  with mean gain `-0.159493`.
- Milestone 7.0 is a benchmark task freeze and leaderboard reproducibility
  gate. It defines 13 frozen tasks spanning capacity, PULSE, EIS, threshold
  warning, calibration, uncertainty, temporal order, stressor robustness,
  hierarchical replicate comparison, multi-horizon capacity, prior-trajectory
  shape, and semi-empirical/replicate checks. The checker passes and keeps the
  task registry aligned with the claim ledger, claim matrix, and artifact
  manifest.
- Milestone 6.2 is a prospective prior-trajectory shape baseline gate. It
  builds a prior-only trajectory sidecar, joins K4/K5 feature groups into the
  existing non-neural capacity-horizon runner, and diagnoses trajectory gains
  against K2, persistence, and prior-slope references. It adds no neural,
  sequence, CBAT, policy, causal, or calibrated-risk claims.
- Milestone 6.1 is a report-based multi-horizon error forensics gate. It
  reads the Milestone 6.0 report, prediction Parquet, and horizon table to
  render split/reference gains, C-rate condition hotspots, prior-slope failure
  bins, oracle-exposure gains by split, and prospective feature-audit rows.
  It adds no new model training, feature engineering, or claim support.
- Milestone 6.0 is a non-neural multi-horizon capacity forecasting gate. It
  builds `capacity_horizon_table_v1.parquet`, runs persistence, prior-slope,
  Ridge, and HGB baselines under grouped splits, and labels K3 k-to-k+h
  exposure features as oracle diagnostics rather than prospective inputs.
- Milestone 5.9 is a train-only hierarchical replicate-aware capacity
  comparator. It adds H0 global train mean, H1 ridge, H2 ridge partial pooling,
  H3 HGB reference, H4 HGB residual partial pooling, and H5
  replicate-variance interval diagnostics. It adds no neural/sequence models,
  CBAT, policy ranking, calibrated-risk claims, calibrated-uncertainty claims,
  causal claims, or architecture claims.
- Milestone 5.8 is a stressor-family routing diagnostic over existing
  non-neural stressor-balanced HGB attribution arms. It adds no feature
  engineering, neural/sequence models, CBAT, policy ranking, calibrated-risk
  claims, calibrated-uncertainty claims, or architecture claims.
- `mbp baseline diagnose-stressor-robust-forensics` adds split/condition
  regression diagnostics for the Milestone 5.1 robust-capacity run. The largest
  regressions are concentrated in non-C-rate views, including profile and
  voltage-window `delta_capacity_Ah` rows for some robust variants.
- `mbp baseline run-stressor-robust-pareto` evaluated 16 bounded settings over
  3,827 intervals, producing 768 metric rows and 663,360 ignored prediction
  rows. The predeclared R2/F8/weight=1.0 setting has C-rate delta gains of
  `0.0305899` versus F4 and `0.0319729` versus the stress R0 reference, but
  its max outside-C-rate relative degradation is `0.0528343`, so it fails the
  5% guardrail.
- Two lighter non-predeclared frontier settings pass the 5% threshold
  diagnostically, but they are not enough to support the predeclared
  robust-capacity claim.
- `mbp baseline run-stressor-robust-adaptive` evaluated R0 and a train-only
  adaptive R2 selector over 3,827 intervals for `delta_capacity_Ah`, producing
  48 metric rows and 41,460 ignored prediction rows per selection policy.
  The max-gain policy fails the unchanged guardrail with max outside-C-rate
  degradation `0.0645764`; the conservative policy passes the outer diagnostic
  rule with max outside-C-rate degradation `0.0279117` and positive C-rate
  paired support.
- `mbp baseline replicate-stressor-robust-adaptive` replicates the adaptive
  selector claim across five logical seeds. Because the evaluated HGB path has
  no bagging and is deterministic for the represented sample sizes, the report
  records `deterministic_hgb_no_bagging_reuse` with effective fit seed `42`.
  Conservative guarded selection passes all five logical seeds with min C-rate
  gains `0.0200436` versus F4 and `0.0214266` versus stress R0, paired p05
  floors `0.00749857` and `0.00465696`, and max outside-C-rate degradation
  `0.0279117`. Max-gain guarded selection fails with outside-C-rate
  degradation `0.0645764`.
- `mbp baseline run-stressor-robust-attribution` compares four arms:
  D0 R0/F4, D1 R0/F8, D2 adaptive R2/F4, and D3 adaptive R2/F8. The
  reweighting-only D2-vs-D0 C-rate delta gain is `0.0106361` with paired p05
  `0.00594397`; raw F8 does not help C-rate delta versus F4 (`-0.00138302`);
  and incremental F8 under adaptive selection improves C-rate delta by
  `0.00940756` with paired p05 above zero. However, incremental F8 fails the
  unchanged outside-C-rate guardrail with max degradation `0.717391`, so F8
  stress-feature attribution remains diagnostic-only and broad fade-solved
  wording remains blocked.
- `mbp baseline run-stressor-robust-arm-selector` now supports a fast
  report-based routing mode from the Milestone 5.7 attribution report and
  prediction parquet. The generated
  `reports/baselines/capacity_stressor_robust_arm_selector_report.json`
  records five final selector comparisons, 20,730 ignored prediction rows,
  and a passed leakage audit. The selector uses D2 only for the C-rate view
  and D0 elsewhere, yielding C-rate gain `0.0106361`, paired p05
  `0.00594397`, and max outside-C-rate degradation `0`.
- `mbp baseline run-hierarchical-capacity` evaluated train-only stressor-family
  residual partial pooling and replicate-variance intervals over 3,827
  intervals. It writes
  `reports/baselines/capacity_hierarchical_replicate_report.json`, diagnostics
  under `reports/baselines/capacity_hierarchical_replicate/`, and an ignored
  prediction Parquet. H4/F4 does not pass the paired-support gate for C-rate
  `delta_capacity_Ah`, and H5 intervals are diagnostic-only due to low grouped
  and C-rate coverage.
- `mbp analysis build-capacity-horizon-table` generated 13,770 multi-horizon
  rows for horizons 1, 2, 3, and 5 from `interval_table.parquet`. QA passes
  with all 228 cells and 76 parameter sets represented, and no missing/censored
  rows among observed possible starts for those horizons.
- `mbp baseline run-capacity-horizon` produced 960 grouped metric rows and an
  ignored prediction Parquet. For C-rate horizon 2, HGB K2 mean MAE is
  `0.183684` for `capacity_Ah_kh` and `0.183020` for
  `delta_capacity_Ah_h`, beating persistence (`0.433943`) and prior-slope
  (`0.299260`). For C-rate horizon 3, HGB K2 mean MAE is `0.221461` for
  `capacity_Ah_kh` and `0.232468` for `delta_capacity_Ah_h`, beating
  persistence (`0.492851`) and prior-slope (`0.302605`). Across all splits,
  HGB K2 beats both references for horizon-2 capacity level and horizons 2/3
  delta capacity, but horizon-3 capacity level is essentially tied and slightly
  worse than prior slope (`0.0935304` versus `0.0932329`), so the overall
  multi-horizon claim remains partially supported.
- `mbp baseline diagnose-capacity-horizon` produced 48 split/reference gain
  rows, 720 C-rate condition-error rows, 1,184 prior-slope failure-mode rows,
  and 48 oracle-exposure gain rows from the existing Milestone 6.0 artifacts.
  The next-branch readiness report keeps global multi-horizon forecasting
  `partially_supported`, C-rate multi-horizon `supported_for_diagnostics`,
  oracle exposure `oracle_diagnostic_only`, and recommends only a possible
  `prior_trajectory_shape_audit` if technical work continues.
- `mbp analysis build-capacity-horizon-trajectory-features` generated 13,770
  trajectory-feature rows. QA passed with zero duplicate, missing, or extra
  horizon keys and no leakage columns; rows at check-up 0 have no prior history
  by construction.
- `mbp baseline run-capacity-horizon` with K4/K5 produced 1,152 metric rows
  and 891,648 ignored prediction rows. K5 does not repair all-split horizon-3
  `capacity_Ah_kh` and does not preserve every C-rate horizon-2/3 row, so
  trajectory-shape forecasting is only `partially_supported`; horizon-3 repair
  and C-rate preservation are `not_supported`.
- Milestone 5.3 remains a correctness-hardening gate for existing calibration
  and stressor-robustness reports. It does not add models, features, or claims.
- Milestone 5.2 added `ece_10_bin_equal_freq` alongside the existing
  fixed-width `ece_10_bin` in threshold-warning baseline, censoring,
  final-claim, and probability-calibration reports; it does not replace
  historical fixed-width ECE values.
- L3 capacity quantile HGB predictions now enforce noncrossing q10/q50/q90
  endpoints by sorting the three evaluated quantile endpoints per row while
  preserving the independent q50 point prediction exactly.
- The refreshed threshold-warning probability calibration report still blocks
  calibrated-risk wording. For the primary 3-check-up horizon, Platt verified-only
  mean fixed-width ECE is `0.0748136` and equal-frequency ECE is `0.0729286`,
  but C-rate verified-only ECE remains above the guardrail (`0.167653`
  fixed-width; `0.176185` equal-frequency).
- The refreshed capacity calibration report still blocks calibrated-capacity
  uncertainty. Raw noncrossing q10-q90 mean coverage is `0.701398`, and C-rate
  mean coverage across calibration methods is `0.72293`, below the nominal
  target.
- Milestone 5.1 remains a diagnostic C-rate robustness result only. The best
  C-rate `delta_capacity_Ah` candidate is `R2_stressor_balanced_hgb` with
  `F8_timestamp_weighted_stress`, but the global robust-capacity claim remains
  `not_supported` because the outside-C-rate non-degradation guardrail narrowly
  fails.
- LOG_AGE monotonicity policy is documented in
  `docs/LOG_AGE_MONOTONICITY_POLICY.md`.
- Interval subset registry generation is implemented with
  `mbp split interval-subsets`.
- `reports/audit/interval_subset_report.json` records strict/tolerant clean
  interval counts under policy version `log_age_monotonicity.v1`.
- Split registry semantics now include corrected voltage-window holdout folds
  derived from `voltage_window_family`, not scalar `age_soc`.
- `pyarrow`, `py7zr`, and `numpy` are core dependencies; `numpy` is required by
  vectorized stress-feature aggregation. Pandas/scikit-learn baseline packages
  and GBM packages remain optional extras.
- `mbp baseline run-capacity` implements the first L0-L3 capacity baseline
  runner and is gated by `interval_subset_registry_v1.parquet`.
- The dependency-free real-data L0 persistence smoke run completed and emitted
  trackable report artifacts under `reports/baselines/capacity_l0_smoke/`.
- The bounded full real-data L0-L3 ladder completed with `--hgb-max-iter 5` and
  emitted trackable report artifacts under `reports/baselines/capacity_l0_l3/`.
- Baseline diagnostics now exist for the full report, scaled Ridge rerun, and
  focused HGB-50 robustness rerun. Focused diagnostics can now compare against
  an L0 reference report.
- A Milestone 0.5c claim-readiness memo and synthesis note document that the
  next engineering direction should be stronger LOG_AGE-derived scalar stress
  features, not PULSE/EIS/CBAT expansion.
- Milestone 0.6 stress-feature tooling is implemented with a modular sidecar
  table, QA report, baseline join path, F5-F7 feature groups, and focused
  HGB-50 stress-feature diagnostics.
- The first non-target-derived stress-feature run produced a mixed result:
  `capacity_Ah_k1` C-rate holdout improved slightly, but `delta_capacity_Ah`
  C-rate holdout degraded versus the HGB-50 F4 baseline.
- Milestone 0.6.1 hardening has been run on real data. The current-sign audit
  gives high-confidence positive-current charge evidence, v1.1 QA passes, and
  the focused HGB-50 stress-feature run remains mixed: C-rate `capacity_Ah_k1`
  improves, but C-rate `delta_capacity_Ah` still fails to beat F4.
- Milestone 0.6.2 target-consistency diagnostics are implemented and run on the
  v1.1 report. Direct delta remains the stronger C-rate delta target path;
  deriving delta from capacity does not solve the failure.
- Milestone 0.6.3 normalized-rate target checks, train-fold bias-correction
  diagnostics, and narrow F11-F13 cold/current feature groups are implemented
  and run. None beats the F4 C-rate `delta_capacity_Ah` threshold.
- Milestone 0.7 PULSE target policy, PULSE QA, canonical RT/50% SOC interval
  target table, and first grouped scalar PULSE resistance baseline are
  implemented and run.
- Milestone 0.7.1 PULSE alignment-threshold sensitivity, direction-specific
  target extraction, missing canonical endpoint reports, and scalar resistance
  baseline sensitivity runs are implemented and run.
- Milestone 0.7.2 PULSE target robustness is implemented and run across
  `delta_pulse_1s_resistance`, `pulse_1s_resistance_k1`,
  `delta_pulse_10ms_resistance`, and `pulse_10ms_resistance_k1`.
- Milestone 0.8 capacity-PULSE coupling diagnostics are implemented and run:
  capacity residuals are joined to PULSE growth, and HGB-50 capacity baselines
  are rerun with prior PULSE state only.
- Milestone 0.8.1 coupling robustness diagnostics are implemented and run for
  canonical `L2_hist_gradient_boosting + F4_state_log_age_scalar` capacity
  predictions. The association survives interval- and condition-level
  aggregation, but remains explanatory and does not authorize a capacity+PULSE
  predictive claim.
- Milestone 0.9 prior-PULSE predictive comparison is implemented and run. It
  supports a narrow `capacity_Ah_k1` level-prediction claim for selected OOD
  splits, while `delta_capacity_Ah` remains a negative guardrail.
- Milestone 0.9.1 strongest non-PULSE comparison is implemented and run. It
  does not support the stronger claim that prior PULSE beats the best supplied
  non-PULSE HGB baseline.
- Milestone 1.0 evidence synthesis locked supported, partially supported,
  not-supported, gated, and blocked claims before EIS and later main-project
  gates were opened.
- Milestone 1.0.1 is the active paper-artifact QA workstream. It does not add
  models or features; it prepares the synthesis artifacts for manuscript
  drafting.
- Milestone 1.4.1 completed the reader-facing manuscript cleanup patch.
- Milestone 2.0 opened EIS as a gated QA and feature-readiness modality. It
  added the EIS feature policy, QA/coverage/alignment/frequency-mask reports,
  alignment-threshold sensitivity, an RT/50 scalar EIS feature sidecar, feature
  QA, and EIS claim-readiness reporting while keeping EIS predictive modeling,
  DRT, embeddings, capacity+PULSE+EIS multimodal models, CBAT,
  neural/sequence models, policy ranking, and EIS improvement claims blocked.
- The real EIS QA run covers 1,177,835 EIS rows, 39,368 spectra, 228 cells,
  76 parameter sets, and 29 check-up indices. The valid-frequency audit reports
  zero stored-mask mismatches while confirming 100 Hz, 208.3 Hz, and 14.7 kHz
  are excluded from the modeling mask.
- EIS alignment remains a reporting sensitivity: median alignment delta is
  40,905 s, p95 is 107,879.5 s, max is 192,238 s, and 4,940 spectra exceed
  24 h. Alignment-threshold coverage retains all 228 cells and 76 parameter
  sets at every threshold from 6 h through all rows.
- The canonical RT/50 EIS feature sidecar contains 3,983 rows, 228 cells, and
  76 parameter sets. Feature QA warns about a small number of missing selected
  frequencies, so EIS is ready for QA/feature-readiness discussion only, not
  predictive claims.
- Milestone 2.1 adds `eis_target_table_v1.parquet`, EIS target QA, scalar EIS
  endpoint baselines, and focused prior-EIS HGB-50 PULSE/capacity reruns. The
  EIS target table has 3,827 interval rows, 3,821 finite prior-EIS rows, 3,750
  finite k1 rows, and 3,744 finite delta rows for the primary scalar EIS
  targets.
- Scalar EIS endpoints are predictable enough for diagnostics:
  `delta_eis_z_abs_1kHz` best condition-fold condition-mean MAE is 0.000307288
  and best C-rate condition-mean MAE is 0.000999892.
- Prior EIS shows split-dependent signal. It wins some PULSE and capacity
  level splits, but not PULSE C-rate, capacity C-rate level, or C-rate
  `delta_capacity_Ah`. Broad EIS improvement claims remain blocked until paired
  strongest-non-EIS and alignment-sensitivity claim-hardening is done.
- Milestone 2.1.1 is implemented and run. Prior-EIS PULSE comparisons produce
  214 paired condition rows and show one profile-holdout split with bootstrap
  p05 above zero, while C-rate remains negative. Prior-EIS capacity comparisons
  produce 428 paired condition rows and show profile-holdout support for
  `capacity_Ah_k1`, but not C-rate level prediction and not C-rate
  `delta_capacity_Ah`. Alignment and selected-frequency completeness
  sensitivities are quantified, leakage audit passes, and broad EIS improvement
  claims remain blocked.
- Milestone 2.2 is implemented and run. `mbp baseline run-semi-empirical`
  evaluates SE0-SE4 ridge-style domain comparators under grouped validation,
  and `mbp analysis replicate-uncertainty` quantifies condition-triplet spread,
  empirical tolerance intervals, and HGB model error versus replicate spread.
  Semi-empirical baselines do not beat HGB F4 or the strongest stress-feature
  baseline in C-rate capacity/fade views; they only show a limited profile
  holdout advantage against F4. Replicate diagnostics quantify spread but do
  not authorize calibrated-uncertainty claims.
- Milestone 2.3 is implemented and run. `mbp analysis calibrate-capacity`
  compares raw HGB q10/q90 intervals, split-conformal intervals,
  stressor-family conformal intervals, and replicate-aware hybrid intervals
  from existing grouped capacity predictions. Raw quantiles remain
  undercovered. Conformal methods improve mean coverage, but C-rate coverage
  remains below target, so no global calibrated-uncertainty claim is
  authorized.
- Milestone 2.4 is implemented and run. `mbp features build-run-events`
  streams the full LOG_AGE Parquet row-group by row-group and writes
  `run_event_table_v1.parquet` without materializing the 904M-row source table
  or 79M-row event table in memory. The real run processed 899,831,845
  interval-window LOG_AGE rows and wrote 79,328,229 run-event rows.
- Run-event QA covers all 3,827 intervals but is in warning status because
  751 intervals have event-duration sums more than 24 h from the interval
  duration. This is reported as a real data-product limitation rather than
  hidden or treated as a clean pass.
- `interval_sequence_features_v1.parquet` contains 3,827 rows and passes
  sequence-feature QA with no missing intervals, no NaN counts, and a
  target-derived-rate leakage check marked passed.
- The Milestone 2.4 non-neural HGB-50 sequence-value comparison does not
  support temporal order value. Order-aware features do not beat aggregate
  event features overall, do not beat shuffled-order controls overall, do not
  beat the timestamp-weighted stress baseline overall, and do not improve the
  C-rate view. Sequence models remain blocked.
- Milestone 2.5 is implemented and run. `mbp analysis knee-labels` generates
  9,576 candidate knee rows across 228 cells, seven detectors, three x-axis
  choices, and two smoothing policies. The primary `piecewise_linear_bic`
  check-up-index/no-smoothing detector produces valid labels for 189 / 228
  cells.
- Knee-label stability is mixed. X-axis and smoothing sensitivity are
  partially supported diagnostically: median disagreement is 0 check-ups for
  both, with agreement within 2 check-ups of 0.892 for x-axis sensitivity and
  0.951 for smoothing sensitivity. Replicate consistency is not supported:
  only 45 / 64 primary valid parameter-set conditions are consistent within
  2 check-ups across replicates.
- `mbp analysis build-knee-risk-labels` generates 3,827 exploratory interval
  risk-label rows. The labels are explicitly exploratory; knee prediction
  remains blocked.
- Milestone 2.5.1 is implemented and run. `mbp analysis knee-forensics` finds
  19 inconsistent primary-valid conditions; `mbp analysis
  knee-stable-registry` classifies 40 / 76 conditions as stable, 23 as
  unstable, and 13 as insufficient-label under the default stable-knee rule.
- `mbp analysis threshold-event-labels` generates 22,962 exploratory
  threshold-event interval-label rows. The best target-readiness label by the
  current policy is `capacity_below_80pct_initial`, with replicate consistency
  within 2 check-ups of 0.897, condition coverage of 0.763, and median event
  check-up 8. This is stronger than detector-knee replicate consistency, but
  it authorizes only a possible next label gate, not a prediction model.
- Milestone 2.6 is implemented and run. `mbp analysis
  build-threshold-warning-table` generates 3,827 prospective warning rows for
  `capacity_below_80pct_initial` using only check-up-k state/time/nominal
  fields. The table excludes future capacity, capacity deltas, future interval
  exposure, and future PULSE/EIS fields as model inputs.
- Threshold-warning QA passes. Positive rates are 0.045205 for
  `event_within_1_checkup`, 0.090410 for `event_within_2_checkups`, and
  0.129083 for `event_within_3_checkups`.
- The non-neural threshold-warning hardening run produces 468 grouped metric rows.
  HGB with W2 nominal/state features beats the event-rate prior on all
  horizons. For `event_within_3_checkups`, mean Brier improves from 0.145791
  to 0.065575. C-rate holdout has 80 positives and 77 negatives for the
  3-check-up horizon, and Brier improves from 0.407317 to 0.159930. This
  supports diagnostic threshold-event forecasting, not calibrated risk or
  policy ranking.
- Distance-to-threshold hardening shows the best HGB warning baseline is not
  merely matching a simple proximity detector. For `event_within_3_checkups`,
  the best proximity baseline (`B3_logistic_distance_baseline`) has mean Brier
  0.132711, while HGB W2 has mean Brier 0.065575. In the C-rate holdout, HGB
  W2 Brier is 0.159930 versus 0.355265 for the logistic distance baseline.
- Lead-time/proximity diagnostics and censoring sensitivity are now reported
  under `reports/baselines/threshold_warning_l0_l2/`. The censoring audit
  records 1,394 right-censored unknown rows for each horizon; verified-only
  sensitivity must be interpreted before any stronger early-warning claim.
- Probability calibration remains not supported. For the C-rate
  `event_within_3_checkups` HGB W2 row, ECE is 0.174673, so probabilities are
  diagnostic scores, not calibrated risk estimates.
- Milestone 2.6.2 is implemented and run. Verified-only evaluation excludes
  the 1,394 right-censored unknown rows for `event_within_3_checkups`, leaving
  2,433 verified rows with 494 positives and 1,939 negatives. HGB W2 remains
  better than both the event-rate prior and the logistic distance baseline:
  verified-only mean Brier is 0.090116 versus 0.178655 for the prior and
  0.168492 for the proximity baseline.
- The C-rate verified-only row also remains positive: HGB W2 Brier is
  0.153370 versus 0.377495 for the prior and 0.327879 for the logistic
  distance baseline. The final claim readiness supports a narrow diagnostic
  threshold-event forecasting claim, including C-rate diagnostic wording, while
  keeping early-warning wording exploratory and calibrated-risk claims blocked.
- Milestone 5.0 threshold-warning probability calibration is implemented and
  run. `mbp baseline calibrate-threshold-warning` evaluates raw HGB W2,
  Platt/logistic calibration, and isotonic calibration under all-row and
  verified-only label policies with held-out condition groups. Milestone 5.2
  refreshes those diagnostics with equal-frequency ECE sensitivity. Milestone
  5.3 hardens the required-policy, C-rate, fallback-row, and Platt-calibration
  gate logic. Platt and
  isotonic improve mean ECE for `event_within_3_checkups`, but C-rate ECE
  remains above the 0.10 guardrail under verified-only (`0.167653` fixed-width
  and `0.176185` equal-frequency for Platt; `0.159021` for isotonic), so
  calibrated-risk claims remain not supported. Threshold-warning probabilities
  remain diagnostic scores.
- Experiment notes are tracked under `docs/experiments/`.

## Git And Artifact Hygiene

Large data products and local tool artifacts remain ignored and are not tracked:

- `data/raw/**`
- `data/interim/**`
- `data/processed/**`
- generated Parquet outputs under `data/splits/`
- generated Parquet outputs under `reports/audit/`
- `.antigravitycli/`
- local CodeGraph databases, Python caches, Ruff/Pytest caches, and `.venv/`

Latest cleanup note:

- `docs/experiments/2026-05-22_repo_cleanup.md`
- Removed disposable Python, Pytest, Ruff, and empty `.antigravitycli/` local
  artifacts.
- Preserved `.venv/`, `.codegraph/`, raw/interim/processed data products, split
  Parquets, and generated audit Parquets because they are ignored local
  reproducibility or development artifacts.

Small audit sidecars that are referenced by documentation are tracked:

- `reports/audit/interval_qa_report.json`
- `reports/audit/interval_subset_report.json`
- `reports/audit/log_age_monotonicity_summary.csv`
- `reports/audit/split_registry_report.json`
- `reports/audit/stress_feature_qa_report.json`
- `reports/audit/eis_qa_report.json`
- `reports/audit/eis_coverage_report.csv`
- `reports/audit/eis_alignment_report.json`
- `reports/audit/eis_alignment_sensitivity_report.json`
- `reports/audit/eis_alignment_sensitivity_coverage.csv`
- `reports/audit/eis_spectrum_quality_summary.csv`
- `reports/audit/eis_valid_frequency_report.csv`
- `reports/audit/eis_feature_qa_report.json`
- `reports/audit/eis_claim_readiness.md`
- `reports/audit/eis_target_qa_report.json`
- `reports/audit/eis_target_coverage.csv`
- `reports/audit/run_event_qa_report.json`
- `reports/audit/run_event_coverage.csv`
- `reports/audit/sequence_feature_qa_report.json`
- `reports/analysis/knee/knee_detector_agreement.csv`
- `reports/analysis/knee/knee_label_stability_report.json`
- `reports/analysis/knee/knee_by_condition.csv`
- `reports/analysis/knee/knee_replicate_consistency.csv`
- `reports/analysis/knee/knee_claim_readiness.md`
- `reports/analysis/knee/knee_inconsistent_conditions.csv`
- `reports/analysis/knee/knee_inconsistency_forensics.md`
- `reports/analysis/knee/knee_stable_condition_report.json`
- `reports/analysis/knee/knee_stable_condition_coverage.csv`
- `reports/analysis/knee/threshold_event_stability.csv`
- `reports/analysis/knee/threshold_event_by_condition.csv`
- `reports/analysis/knee/threshold_event_claim_readiness.md`
- `reports/analysis/knee/knee_vs_threshold_decision.md`
- `reports/analysis/knee/threshold_warning_qa_report.json`
- `reports/analysis/knee/threshold_warning_class_balance.csv`
- `reports/analysis/knee/threshold_warning_split_coverage.csv`
- `reports/baselines/threshold_warning_l0_l2_report.json`
- `reports/baselines/threshold_warning_l0_l2/leaderboard.csv`
- `reports/baselines/threshold_warning_l0_l2/baseline_summary.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_leakage_audit.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/lead_time_diagnostics.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_c_rate.md`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_calibration_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_by_split.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_censoring_report.json`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_reliability.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/lead_time_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/proximity_bin_performance.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/c_rate_lead_time_performance.csv`
- `reports/baselines/threshold_warning_verified_only_report.json`
- `reports/baselines/threshold_warning_verified_only/leaderboard.csv`
- `reports/baselines/threshold_warning_verified_only/baseline_summary.md`
- `reports/baselines/threshold_warning_verified_only/threshold_warning_calibration.md`
- `reports/baselines/threshold_warning_verified_only/threshold_warning_leakage_audit.md`
- `reports/baselines/threshold_warning_verified_only/threshold_warning_claim_readiness.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`
- `reports/baselines/threshold_warning_censoring_sensitivity/threshold_warning_censoring_sensitivity_report.json`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_metric_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_split_comparison.csv`
- `reports/baselines/threshold_warning_censoring_sensitivity/plots/censoring_policy_c_rate_comparison.csv`
- `reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md`
- `reports/baselines/threshold_warning_l0_l2/plots/final_lead_time_claim_matrix.csv`
- `reports/baselines/threshold_warning_l0_l2/plots/final_c_rate_warning_matrix.csv`
- `reports/analysis/support_reliability/support_reliability_report.json`
- `reports/analysis/support_reliability/support_reliability_diagnostics.md`
- `reports/analysis/support_reliability/support_reliability_claim_readiness.md`
- `reports/analysis/support_reliability/plots/support_distance_by_split.csv`
- `reports/analysis/support_reliability/plots/selective_capacity_performance.csv`
- `reports/analysis/support_reliability/plots/selective_threshold_warning_performance.csv`
- `reports/analysis/support_reliability/plots/selective_policy_contrast_performance.csv`
- `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
- `reports/synthesis/main_project_claim_matrix_v2.csv`
- `reports/synthesis/main_project_gate_status.md`
- `reports/synthesis/technical_decision_matrix_v2.md`
- `reports/synthesis/blocked_claims_v2.md`
- `reports/synthesis/next_branch_decision.md`
- `reports/synthesis/source_consistency_check_v2.md`

The large Parquet outputs remain local generated artifacts:

| Artifact | Rows | Tracking |
|---|---:|---|
| `data/interim/modality_table_log_age.parquet` | 904,977,105 | ignored |
| `reports/audit/log_age_monotonicity_violations.parquet` | 7,071 | ignored |
| `data/interim/interval_table.parquet` | 3,827 | ignored |
| `data/splits/split_registry_v1.parquet` | 228 | ignored |
| `data/splits/interval_subset_registry_v1.parquet` | 3,827 | ignored |
| `data/interim/interval_stress_features_v1.parquet` | 3,827 | ignored |
| `data/interim/interval_stress_features_v1_1.parquet` | 3,827 | ignored |
| `data/interim/eis_feature_table_v1.parquet` | 3,983 | ignored |
| `data/interim/eis_target_table_v1.parquet` | 3,827 | ignored |
| `data/interim/run_event_table_v1.parquet` | 79,328,229 | ignored |
| `data/interim/interval_sequence_features_v1.parquet` | 3,827 | ignored |
| `data/interim/interval_event_sequence_table_v1.parquet` | 3,827 | ignored |
| `data/interim/knee_candidate_table_v1.parquet` | 9,576 | ignored |
| `data/interim/knee_risk_label_table_v1.parquet` | 3,827 | ignored |
| `data/interim/knee_stable_condition_registry_v1.parquet` | 76 | ignored |
| `data/interim/threshold_event_label_table_v1.parquet` | 22,962 | ignored |
| `data/interim/threshold_warning_table_v1.parquet` | 3,827 | ignored |
| `reports/audit/raw_log_archive_inventory.parquet` | 541 | ignored |

Milestone 0.5 generated predictions are also ignored by default:

- `data/processed/capacity_baseline_predictions.parquet`
- `data/processed/capacity_l0_smoke_predictions.parquet`
- `data/processed/capacity_l0_l3_predictions.parquet`
- `data/processed/capacity_l1_scaled_predictions.parquet`
- `data/processed/capacity_hgb50_focused_predictions.parquet`
- `data/processed/capacity_stress_features_hgb50_predictions.parquet`
- `data/processed/capacity_stress_features_v1_1_hgb50_predictions.parquet`

Milestone 0.5 small report artifacts under `reports/baselines/` are trackable:

- baseline metrics JSON
- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- plot-ready CSV summaries

## Gate Status

### Gate 1

Gate 1 remains **GO FOR DATA PRODUCTS**.

Result-package coverage is complete for the 228-cell cohort:

- CFG: complete.
- EOC: complete.
- EIS: complete, with Milestone 2.0 QA and valid-frequency audit now run.
- PULSE: complete, but pulse provenance/alignment hardening remains a known
  issue.

BagIt validation for the result package passed.

### Gate 2

Gate 2 ingestion products exist for:

- `cell_condition_table`
- `checkup_event_table`
- `modality_table_eis`
- `modality_table_pulse`
- `modality_table_log_age`
- `split_registry_v1`
- `interval_table`

LOG_AGE ingestion evidence:

- Source archive: `cell_log_age_ultracompr.7z`
- Cohort rows: `904,977,105`
- Cohort cells: `228`
- Auxiliary LOG_AGE CSV records excluded: `48`
- Final Parquet row groups: `257,311`

Strict LOG_AGE QA still reports `7,107` timestamp/EFC monotonicity decreases.
That strict QA failure is preserved as an evidence signal. Milestone 0.4 defines
how those decreases are handled for baseline subset construction.

### Gate 2b

Gate 2b is complete:

- `reports/audit/log_age_monotonicity_violations.parquet` contains `7,071`
  detailed default-tolerance violations.
- `reports/audit/log_age_monotonicity_summary.csv` has `463` lines.
- Summary rows show the observed detailed violations are EFC decreases, with
  zero timestamp decreases in the default-tolerance report.
- Worst detailed EFC drops are approximately `0.0002` EFC.
- `reports/audit/interval_qa_report.json` passes.
- `reports/audit/split_registry_report.json` passes.
- `reports/audit/raw_log_archive_inventory.parquet` inventories raw LOG archive
  members without parsing the full raw LOG corpus.

Interval QA key facts:

- Interval rows: `3,827`
- Expected interval count: `3,827`
- Check-up event rows: `4,055`
- Cells with check-ups: `228`
- LOG_AGE availability fraction: `1.0`
- Intervals with zero LOG_AGE rows: `0`
- Intervals with monotonicity violations: `1,054`
- Non-cohort cells: `0`
- Masked diagnostic rows:
  - `cap_aged_est_Ah`: `4,577`
  - `R0_mOhm`: `4,577`
  - `R1_mOhm`: `4,577`

### Milestone 0.4

Milestone 0.4 data products are implemented:

- Policy: `docs/LOG_AGE_MONOTONICITY_POLICY.md`
- CLI: `mbp split interval-subsets`
- Registry: `data/splits/interval_subset_registry_v1.parquet`
- Report: `reports/audit/interval_subset_report.json`

Interval subset policy counts:

| Subset or exclusion | Count |
|---|---:|
| Full interval table | 3,827 |
| `baseline_clean_strict` | 2,773 |
| `baseline_clean_tolerant` | 3,827 |
| `sensitivity_flagged_monotonicity` | 1,054 |
| `small_efc_jitter` | 1,054 |
| Excluded due to timestamp drop | 0 |
| Excluded due to large EFC drop | 0 |
| Excluded due to missing LOG_AGE | 0 |
| Excluded due to duration error | 0 |

The tolerant subset keeps tiny EFC-only LOG_AGE jitter at or below `0.00025`
EFC. The strict subset excludes all monotonicity-flagged intervals and should be
used as the mandatory sensitivity subset for first baselines.

Split-registry audit key facts after the voltage-window fix:

- Rows: `228`
- Parameter-set triplets remain grouped.
- Condition folds are non-empty.
- Hot temperature holdout uses `40 C`.
- High C-rate holdout includes `5/3 C`.
- Profile holdout contains profile conditions.
- Voltage-window holdout is non-empty:
  - fold `1`: `84` full-window `approx_0_100` cells
  - fold `2`: `96` reduced-window `approx_10_100` / `approx_10_90` cells
  - fold `3`: `48` calendar idle-SOC cells

The legacy `soc_window_holdout_fold` remains present for compatibility but is
now populated from corrected voltage-window semantics. New work should prefer
`voltage_window_holdout_fold`.

### Milestone 0.5

Milestone 0.5 baseline tooling is implemented:

- CLI: `mbp baseline run-capacity`
- Runner: `mbp.baselines.capacity`
- Prediction schema: `BASELINE_PREDICTION_SCHEMA`
- Default primary subset: `baseline_clean_tolerant`
- Mandatory sensitivity scope: exclude
  `sensitivity_flagged_monotonicity == true`
- Targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- Split views:
  - `condition_fold`
  - `temperature_holdout_fold`
  - `c_rate_holdout_fold`
  - `profile_holdout_fold`
  - `voltage_window_holdout_fold`

Implemented model levels:

- `L0_persistence`
- `L1_ridge`
- `L2_hist_gradient_boosting`
- `L3_quantile_hist_gradient_boosting`

`L0_persistence` is dependency-free. L1-L3 require the optional baseline extra
(`uv sync --extra baseline`). The current local `.venv` was restored with
`uv sync --extra dev --extra baseline`, so both validation tooling and baseline
dependencies are available in this working environment.

Implemented feature groups:

- `F0_time_only`
- `F1_state_time`
- `F2_state_exposure`
- `F3_state_nominal`
- `F4_state_log_age_scalar`

Inserted LOG_AGE diagnostics (`cap_aged_est_Ah`, `R0_mOhm`, `R1_mOhm`) are not
eligible baseline features. `F0_time_only` remains a deliberately weak sanity
feature set; learned non-persistence state-aware feature groups include
`capacity_Ah_k`.

Milestone 0.5 report rendering emits:

- `leaderboard.csv`
- `baseline_summary.md`
- `evaluation_cards/*.json`
- `plots/mae_by_model_and_feature.csv`
- `plots/worst_condition_errors.csv`
- `plots/strict_vs_tolerant_delta.csv`

Completed Milestone 0.5 experiment artifacts:

- `docs/experiments/2026-05-22_capacity_baseline_ladder.md`
- `reports/baselines/capacity_l0_smoke_report.json`
- `reports/baselines/capacity_l0_smoke/leaderboard.csv`
- `reports/baselines/capacity_l0_smoke/baseline_summary.md`
- `reports/baselines/capacity_l0_smoke/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_smoke/plots/*.csv`
- `reports/baselines/capacity_l0_l3_report.json`
- `reports/baselines/capacity_l0_l3/leaderboard.csv`
- `reports/baselines/capacity_l0_l3/baseline_summary.md`
- `reports/baselines/capacity_l0_l3/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_l3/plots/*.csv`
- `reports/baselines/capacity_l1_scaled_report.json`
- `reports/baselines/capacity_l1_scaled/leaderboard.csv`
- `reports/baselines/capacity_l1_scaled/baseline_summary.md`
- `reports/baselines/capacity_l1_scaled/evaluation_cards/*.json`
- `reports/baselines/capacity_l1_scaled/plots/*.csv`
- `reports/baselines/capacity_hgb50_focused_report.json`
- `reports/baselines/capacity_hgb50_focused/leaderboard.csv`
- `reports/baselines/capacity_hgb50_focused/baseline_summary.md`
- `reports/baselines/capacity_hgb50_focused/evaluation_cards/*.json`
- `reports/baselines/capacity_hgb50_focused/plots/*.csv`

The L0 smoke report produced `48` metric rows on the real interval table. It
confirmed `3,827` tolerant-clean rows, `2,773` strict-clean rows, and `1,054`
monotonicity-flagged sensitivity intervals.

The bounded L0-L3 report produced `768` metric rows, `320` leaderboard rows,
and `160` evaluation cards. It used `hgb_max_iter=5`, so it is a valid first
full-ladder artifact but not a final tuned gradient-boosting run.

Primary-run baseline highlights:

- Best `capacity_Ah_k1` condition-mean MAE: `0.078735`, from `L1_ridge` with
  `F2_state_exposure` on `profile_holdout_fold`.
- Best `delta_capacity_Ah` condition-mean MAE: `0.069939`, from
  `L2_hist_gradient_boosting` with `F1_state_time` on `profile_holdout_fold`.
- Hardest split by best available condition-mean MAE:
  `c_rate_holdout_fold` at `0.175406`.
- Strict-vs-tolerant sensitivity was small on average: mean
  primary-minus-sensitivity condition-mean MAE was approximately `-0.000087`.

### Milestone 0.5b

Milestone 0.5b diagnostics and robustness artifacts are implemented:

- CLI: `mbp baseline diagnose-capacity`
- Optional reference comparison: `--reference-report`
- Diagnostics memo: `baseline_diagnostics.md`
- C-rate analysis memo: `c_rate_holdout_error_analysis.md`
- Claim-readiness memo: `claim_readiness.md`
- Diagnostic CSVs:
  - `plots/feature_gain_by_split.csv`
  - `plots/best_by_target_split.csv`
  - `plots/c_rate_holdout_errors.csv`
  - `plots/c_rate_holdout_by_condition.csv`
  - `plots/c_rate_grouped_summaries.csv`

`L1_ridge` now uses train-fold numeric standardization. Reports record
`numeric_standardization = train_fold_mean_std` and
`numeric_standardization_applies_to = ["L1_ridge"]`.

Quantile diagnostics are implemented for `L3_quantile_hist_gradient_boosting`:

- `q10_q90_interval_coverage`
- `q10_q90_interval_width_mean`
- `pinball_loss_q10`
- `pinball_loss_q50`
- `pinball_loss_q90`

Scaled Ridge rerun:

- Report: `reports/baselines/capacity_l1_scaled_report.json`
- Metric rows: `288`
- Best `capacity_Ah_k1`: `L1_ridge` with `F2_state_exposure` on
  `profile_holdout_fold`, condition-mean MAE `0.077580`.
- Scaling modestly improves several Ridge rows but does not resolve C-rate
  holdout difficulty.

Focused HGB-50 robustness rerun:

- Report: `reports/baselines/capacity_hgb50_focused_report.json`
- Metric rows: `384`
- `hgb_max_iter`: `50`
- Best `capacity_Ah_k1`: `L2_hist_gradient_boosting` with
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.053927`.
- Best `delta_capacity_Ah`: `L2_hist_gradient_boosting` with
  `F4_state_log_age_scalar` on `condition_fold`, condition-mean MAE `0.044645`.
- Best C-rate `delta_capacity_Ah`: `0.101133`, from
  `L2_hist_gradient_boosting` with `F4_state_log_age_scalar`.
- Mean q10-q90 coverage for HGB-50 quantile rows: approximately `0.664674`.

Milestone 0.5b interpretation:

- C-rate holdout remains the hardest generalization split.
- Ridge remains sensitive to feature scaling and LOG_AGE scalar features are not
  a stable Ridge win.
- HGB-50 suggests LOG_AGE scalar summaries can help nonlinear baselines, so the
  `hgb_max_iter=5` run should be treated as a bounded smoke artifact, not as a
  final HGB conclusion.
- Nominal protocol features remain consistently useful.

### Milestone 0.5c

Milestone 0.5c synthesis artifacts are implemented:

- `docs/experiments/2026-05-22_capacity_baseline_synthesis.md`
- `reports/baselines/capacity_hgb50_focused/claim_readiness.md`
- `reports/baselines/capacity_hgb50_focused/plots/c_rate_grouped_summaries.csv`

Focused HGB-50 diagnostics were regenerated with
`--reference-report reports/baselines/capacity_l0_l3_report.json`, so the best
row table and C-rate condition table now report L0 persistence comparisons
instead of `NA`.

Milestone 0.5c key findings:

- HGB-50 improves over L0 persistence across all target/split best rows in the
  focused report.
- Best C-rate condition-mean MAE remains higher than other splits:
  `0.125186` for `capacity_Ah_k1` and `0.101133` for `delta_capacity_Ah`.
- C-rate difficulty is strongest around cold/cool high-C-rate conditions:
  grouped mean best error is `0.154004` at `10 C` and `0.132982` at `0 C`,
  versus `0.068380` at `25 C`.
- Voltage-window grouping suggests `approx_0_100` and `approx_10_100` remain
  harder than `approx_10_90` in the current C-rate diagnostic.
- Primary HGB-50 quantile q10-q90 coverage is approximately `0.678207`, below
  nominal 0.8, so no uncertainty-calibration claim is authorized.

Milestone 0.5c decision:

- Do not expand to PULSE, EIS, sequence modeling, neural modeling, policy
  ranking, or CBAT yet.
- The recommended next milestone is LOG_AGE-derived scalar stress-feature
  engineering focused on C-rate generalization.

### Milestone 0.6

Milestone 0.6 stress-feature tooling is implemented:

- CLI: `mbp features build-stress`
- CLI: `mbp features stress-qa`
- CLI: `mbp baseline diagnose-stress-features`
- Sidecar schema: `INTERVAL_STRESS_FEATURES_SCHEMA`
- Sidecar table: `data/interim/interval_stress_features_v1.parquet` (`ignored`)
- QA report: `reports/audit/stress_feature_qa_report.json`
- Baseline join option: `mbp baseline run-capacity --stress-features ...`
- Feature groups:
  - `F5_log_age_histograms`
  - `F6_coupled_stress`
  - `F7_c_rate_focused`

Stress-feature QA passed:

- Rows: `3,827`
- Unique cells: `228`
- Unique parameter sets: `76`
- Intervals missing stress features: `0`
- Dwell-bin duration consistency failures: `0`
- Negative nonnegative-feature counts: `0`
- Current-sign policy: `positive_current_charge_provisional_abs_current_primary`
- Sign-dependent features remain provisional because the current sign convention
  is not yet independently confirmed.

Target-derived diagnostic rates are excluded from F5-F7 predictive feature
groups:

- `delta_capacity_per_day`
- `delta_capacity_per_efc`
- `delta_capacity_per_Ah_throughput`

Focused stress-feature HGB-50 run:

- Report: `reports/baselines/capacity_stress_features_hgb50_report.json`
- Metric rows: `440`
- `hgb_max_iter`: `50`
- Feature groups: `F3`, `F4`, `F5`, `F6`, `F7`
- Split views: C-rate, condition, temperature, voltage-window

Milestone 0.6 success-criterion result:

| Target | HGB-50 F4 baseline | Best non-target-derived stress row | Gain | Status |
|---|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` (`F6_coupled_stress`) | `0.000530` | marginal pass |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` (`F5_log_age_histograms`) | `-0.009128` | fail |

Stress features did not materially degrade condition-fold or
temperature-holdout performance, but the C-rate success criterion is only
partially met. The result does **not** support a broad claim that stress
features improve C-rate generalization yet.

Milestone 0.6 decision:

- Keep PULSE/EIS/CBAT blocked.
- Do not claim stress-feature improvement from v1.
- Review stress-feature formulation, current-sign convention, and event
  segmentation before expanding scope.

### Milestone 0.6.1

Milestone 0.6.1 stress-feature hardening is implemented, covered by synthetic
tests, and run on real data. The hardening keeps the scope capacity-only and
scalar-feature only.

Implemented hardening:

- CLI: `mbp features current-sign-audit`
- Stress-feature builder now emits schema version
  `gate6.interval_stress_features.v1_1`.
- Dwell features are timestamp-weighted from consecutive LOG_AGE timestamps,
  not count-weighted by row count.
- Gap and coverage fields are added:
  - `stress_observed_duration_h`
  - `stress_coverage_fraction`
  - `median_log_age_dt_s`
  - `max_log_age_gap_s`
  - `log_age_gap_count_gt_60s`
  - `log_age_gap_count_gt_300s`
- Event-segmented scalar features are added for charge, discharge, rest,
  high-current, cold/high-current, high-voltage/high-current, and
  high-SOC/high-current durations.
- New feature groups are defined:
  - `F8_timestamp_weighted_stress`
  - `F9_event_segmented_stress`
  - `F10_c_rate_v1_1`

Real-data v1.1 artifacts:

- Current-sign audit: `reports/audit/current_sign_audit_report.json`
- QA report: `reports/audit/stress_feature_v1_1_qa_report.json`
- Baseline report:
  `reports/baselines/capacity_stress_features_v1_1_hgb50_report.json`
- Diagnostics:
  `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_diagnostics.md`

Current-sign audit result:

- Row groups sampled evenly across LOG_AGE: `5,000`
- Positive-current evidence rows: `5,516,237`
- Negative-current evidence rows: `5,909,947`
- Convention: `positive_current_charge`
- Confidence: `high`

Stress-feature v1.1 QA result:

- Rows: `3,827`
- Unique cells: `228`
- Unique parameter sets: `76`
- Missing interval keys: `0`
- Dwell-bin failures against `stress_observed_duration_h`: `0`
- Current sign policy in sidecar: `positive_current_charge_confirmed`

Milestone 0.6.1 success-criterion result:

| Target | F4 HGB-50 baseline | v1 best stress row | v1.1 best stress row | v1.1 gain vs F4 | Status |
|---|---:|---:|---:|---:|---|
| `capacity_Ah_k1` C-rate | `0.125186` | `0.124656` | `0.120605` (`F5_log_age_histograms`) | `0.004581` | improved but marginal |
| `delta_capacity_Ah` C-rate | `0.101133` | `0.110260` | `0.102516` (`F8_timestamp_weighted_stress`) | `-0.001383` | fail |

Decision:

- Do not claim broad stress-feature C-rate improvement from v1.1.
- Keep PULSE/EIS/CBAT blocked.
- Treat v1.1 as a useful hardening result: current sign is now evidenced,
  timestamp-weighted dwell repaired most of the v1 delta-capacity degradation,
  but it still does not beat F4 on the main delta target.

### Milestone 0.6.2

Milestone 0.6.2 target-consistency and C-rate failure diagnostics are
implemented and run on the v1.1 stress-feature report. No new model training was
performed.

Implemented command:

- CLI: `mbp baseline diagnose-target-consistency`

Real-data outputs:

- `reports/baselines/capacity_stress_features_v1_1_hgb50/target_consistency_diagnostics.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/c_rate_residual_analysis.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/stress_feature_ablation_summary.md`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/direct_vs_derived_target_metrics.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/c_rate_residuals_by_parameter_set.csv`
- `reports/baselines/capacity_stress_features_v1_1_hgb50/plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`

Target-consistency finding:

| Target | C-rate rows | Derived path better by MAE | Derived path better by condition mean MAE |
|---|---:|---:|---:|
| `capacity_Ah_k1` | `14` | `10` | `10` |
| `delta_capacity_Ah` | `14` | `4` | `4` |

Best C-rate target paths by condition-mean MAE:

| Target interpreted | Best path | Model / feature group | Condition mean MAE |
|---|---|---|---:|
| `capacity_Ah_k1` | derived from direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | direct delta | `L2_hist_gradient_boosting` / `F4_state_log_age_scalar` | `0.101133` |
| `delta_capacity_Ah` | derived from direct capacity | `L2_hist_gradient_boosting` / `F5_log_age_histograms` | `0.120605` |

Decision:

- Keep direct `delta_capacity_Ah` as the primary C-rate delta target.
- Do not switch to derived delta from capacity predictions.
- Report derived capacity-from-delta as a diagnostic because it can outperform
  direct capacity on C-rate.
- Keep PULSE/EIS/CBAT blocked until the C-rate delta failure mode is understood.

### Milestone 0.6.3

Milestone 0.6.3 tests one final narrow LOG_AGE-only C-rate delta pass before
changing evidence streams. It adds normalized delta-rate target modes,
train-fold residual/bias correction diagnostics, and compact cold/current
feature groups F11-F13.

Implemented changes:

- Target modes:
  - `delta_capacity_per_day_target`
  - `delta_capacity_per_efc_target`
- Train-fold-only residual correction via `mbp baseline run-capacity
  --bias-correction`.
- Narrow feature groups:
  - `F11_minimal_cold_current`
  - `F12_voltage_cold_current_interactions`
  - `F13_sparse_c_rate_context`

Real-data outputs:

- `reports/baselines/capacity_delta_rate_targets_hgb50_report.json`
- `reports/baselines/capacity_delta_rate_targets_hgb50/plots/rate_target_vs_direct_delta.csv`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50_report.json`
- `reports/baselines/capacity_c_rate_delta_v1_2_hgb50/stress_feature_diagnostics.md`
- `reports/baselines/capacity_c_rate_bias_corrected_report.json`
- `reports/baselines/capacity_c_rate_bias_corrected/plots/bias_correction_by_split.csv`
- `docs/experiments/2026-05-23_c_rate_delta_failure_decision.md`

C-rate `delta_capacity_Ah` result:

| Approach | Best C-rate condition-mean MAE | Beats `0.101133` F4 threshold |
|---|---:|---|
| Direct F4 baseline | `0.101133` | reference |
| Normalized rate targets | `0.121271` best rate target | no |
| Narrow F11-F13 groups | `0.147452` best narrow group | no |
| Train-fold bias correction | effectively unchanged from direct F4 | no |

Decision:

- Keep direct `delta_capacity_Ah` as the primary delta target.
- Do not use normalized rate targets as the next primary target path.
- Do not promote F11-F13 narrow cold/current groups as evidence.
- Treat train-fold residual correction as neutral diagnostics, not a headline
  model.
- Stop broad LOG_AGE scalar stress-feature expansion unless a future review
  identifies a concrete bug. The next recommended evidence stream is PULSE
  QA/baseline work, while EIS/PULSE supervised claims remain blocked until that
  milestone is explicitly opened.

### Milestone 0.7

Milestone 0.7 opens PULSE as a QA-first resistance endpoint. It does not
authorize EIS, sequence/neural models, policy ranking, CBAT, or capacity+PULSE
multimodal claims.

Implemented artifacts:

- Policy: `docs/PULSE_TARGET_POLICY.md`
- CLI: `mbp pulse qa`
- CLI: `mbp pulse build-targets`
- CLI: `mbp baseline run-pulse`
- QA report: `reports/audit/pulse_qa_report.json`
- Alignment report: `reports/audit/pulse_alignment_report.json`
- Coverage table: `reports/audit/pulse_target_coverage.csv`
- Target table: `data/interim/pulse_target_table.parquet` (ignored generated data)
- Baseline report: `reports/baselines/pulse_resistance_l0_l3_report.json`
- Diagnostics: `reports/baselines/pulse_resistance_l0_l3/pulse_diagnostics.md`
- Experiment note: `docs/experiments/2026-05-23_pulse_qa_resistance_baseline.md`

PULSE QA findings:

| Field | Value |
|---|---:|
| PULSE summary rows | `39,365` |
| Unique cells | `228` |
| Canonical RT/50% cell-checkups available | `3,980` |
| Canonical RT/50% cell-checkups missing | `75` |
| Duplicate canonical cell-checkups | `0` |
| Large alignment-delta rows > 1 day | `5,060` |

Canonical target-table findings:

| Field | Finite intervals |
|---|---:|
| `pulse_1s_resistance_k` | `3,826` |
| `pulse_1s_resistance_k1` | `3,752` |
| `delta_pulse_1s_resistance` | `3,751` |
| `delta_pulse_10ms_resistance` | `3,751` |

First PULSE baseline result for `delta_pulse_1s_resistance`:

| Split | Best model | Feature group | Condition-mean MAE |
|---|---|---|---:|
| `condition_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.000960407` |
| `temperature_holdout_fold` | `L2_hist_gradient_boosting` | `P5_stress_v1_1` | `0.00109610` |
| `c_rate_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.00185842` |
| `profile_holdout_fold` | `L2_hist_gradient_boosting` | `P3_state_nominal` | `0.000953406` |
| `voltage_window_holdout_fold` | `L2_hist_gradient_boosting` | `P1_state_time` | `0.00117733` |

Decision:

- PULSE RT/50% target coverage is good enough for first baseline diagnostics,
  but missing canonical endpoints and large alignment deltas must remain visible
  in reports.
- The first PULSE resistance baseline is diagnostic only; no scientific PULSE
  claim or capacity+PULSE multimodal claim is authorized yet.
- Next work should harden PULSE alignment/target coverage interpretation before
  considering broader PULSE target sets.

### Milestone 0.7.1

Milestone 0.7.1 hardens the canonical PULSE target before any resistance claim.
It does not authorize EIS, sequence/neural models, policy ranking, CBAT,
capacity+PULSE multimodal claims, or PULSE claims beyond scalar resistance
baselines.

Implemented artifacts:

- CLI: `mbp pulse alignment-sensitivity`
- CLI: `mbp pulse missingness`
- CLI option: `mbp pulse build-targets --direction mean|charge|discharge`
- CLI option: `mbp baseline run-pulse --max-alignment-delta-s`
- Alignment sensitivity report:
  `reports/audit/pulse_alignment_sensitivity_report.json`
- Alignment sensitivity coverage:
  `reports/audit/pulse_alignment_sensitivity_coverage.csv`
- Missing endpoint reports:
  `reports/audit/pulse_missing_canonical_targets.csv`,
  `reports/audit/pulse_missingness_by_condition.csv`, and
  `reports/audit/pulse_missingness_by_split.csv`
- Direction-specific target tables:
  `data/interim/pulse_target_table_mean.parquet`,
  `data/interim/pulse_target_table_charge.parquet`, and
  `data/interim/pulse_target_table_discharge.parquet` (ignored generated data)
- Alignment-threshold baseline reports:
  `reports/baselines/pulse_resistance_alignment_24h_report.json` and
  `reports/baselines/pulse_resistance_alignment_36h_report.json`
- Direction sensitivity reports:
  `reports/baselines/pulse_resistance_direction_mean_report.json`,
  `reports/baselines/pulse_resistance_direction_charge_report.json`, and
  `reports/baselines/pulse_resistance_direction_discharge_report.json`
- Combined summaries:
  `reports/baselines/pulse_resistance_alignment_sensitivity/baseline_summary.md`
  and
  `reports/baselines/pulse_resistance_l0_l3/pulse_resistance_direction_comparison.md`

Canonical RT/50 alignment-threshold coverage:

| Threshold | Retained intervals | Missing intervals | Retained cells | C-rate rows | Profile rows |
|---|---:|---:|---:|---:|---:|
| `<=6h` | `3,131` | `696` | `220` | `90` | `605` |
| `<=12h` | `3,529` | `298` | `225` | `109` | `697` |
| `<=24h` | `3,748` | `79` | `228` | `143` | `733` |
| `<=36h` | `3,751` | `76` | `228` | `143` | `733` |
| `all` | `3,751` | `76` | `228` | `143` | `733` |

Alignment-threshold baseline sensitivity:

| Threshold | Split | Best feature group | Condition-mean MAE |
|---|---|---|---:|
| `all` | `condition_fold` | `P5_stress_v1_1` | `0.000960407` |
| `all` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00185842` |
| `<=24h` | `condition_fold` | `P5_stress_v1_1` | `0.000952007` |
| `<=24h` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00194971` |
| `<=36h` | `condition_fold` | `P5_stress_v1_1` | `0.000960407` |
| `<=36h` | `c_rate_holdout_fold` | `P3_state_nominal` | `0.00185842` |

Direction sensitivity:

- `mean` remains the canonical PULSE target direction handling.
- `charge` produced the same scalar baseline rows as `mean` for the current
  canonical RT/50 target table.
- `discharge` produced no finite adjacent RT/50 interval deltas and now emits
  an explicit warning report: `no_finite_target_rows_for_selected_configuration`.

Missing canonical endpoints:

- Missing endpoint rows: `76`
- Missing rows in C-rate holdout: `14`
- Missing rows in profile holdout: `19`
- Missingness spans `34` parameter-set condition groups and remains a reporting
  limitation rather than a silent exclusion.

Decision:

- Alignment filtering at `<=24h` changes the C-rate condition-mean MAE slightly
  and keeps all parameter sets represented; `<=36h` is identical to all rows for
  the current finite target set.
- Direction-specific discharge is not usable as a current canonical baseline
  target because adjacent finite RT/50 discharge deltas are absent.
- The canonical `mean` target remains acceptable for scalar resistance-baseline
  diagnostics, but no PULSE scientific claim or capacity+PULSE multimodal claim
  is authorized.

### Milestone 0.7.2

Milestone 0.7.2 finalizes scalar PULSE target robustness before any
capacity+PULSE coupling work. It does not authorize EIS, sequence/neural
models, policy ranking, CBAT, capacity+PULSE multimodal claims, or PULSE claims
beyond scalar resistance baselines.

Implemented artifacts:

- Target robustness report:
  `reports/baselines/pulse_resistance_target_robustness_report.json`
- Target robustness directory:
  `reports/baselines/pulse_resistance_target_robustness/`
- Claim-readiness memo:
  `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- Alignment robustness memo:
  `reports/baselines/pulse_resistance_alignment_robustness.md`
- Direction policy summary:
  `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`
- Missingness interpretation:
  `reports/audit/pulse_missingness_interpretation.md`
- Decision memo:
  `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`

Best target-robustness rows:

| Target | C-rate best MAE | Condition-fold best MAE | Interpretation |
|---|---:|---:|---|
| `delta_pulse_1s_resistance` | `0.00185842` | `0.000960407` | canonical transition target |
| `delta_pulse_10ms_resistance` | `0.00180642` | `0.000910676` | viable secondary diagnostic |
| `pulse_1s_resistance_k1` | `0.00189616` | `0.00104973` | state-tracking target |
| `pulse_10ms_resistance_k1` | `0.00179792` | `0.00105917` | state-tracking target |

Decision:

- `delta_pulse_1s_resistance` remains the canonical first PULSE transition
  target.
- `delta_pulse_10ms_resistance` behaves similarly and is viable as a secondary
  diagnostic target.
- k1 resistance targets should be interpreted as state-tracking targets, not
  direct transition prediction.
- Current RT/50 `mean` direction handling is effectively equivalent to
  `charge`; discharge adjacent interval deltas are unavailable.
- Canonical RT/50 mean PULSE is robust enough for scalar resistance-baseline
  diagnostics. A broader PULSE scientific claim and capacity+PULSE multimodal
  modeling remain blocked until explicitly opened.

### Milestone 0.8

Milestone 0.8 tests whether scalar canonical PULSE signals explain capacity
baseline failures. It is not architecture work and does not authorize
capacity+PULSE multimodal claims.

Implemented artifacts:

- Coupling table:
  `data/interim/capacity_pulse_coupling_table.parquet` (ignored generated data)
- Coupling diagnostics:
  `reports/coupling/pulse_capacity/pulse_capacity_correlation.md`
- Coupling plot tables under `reports/coupling/pulse_capacity/plots/`
- Prior-PULSE capacity report:
  `reports/baselines/capacity_with_prior_pulse_hgb50_report.json`
- Prior-PULSE capacity diagnostics:
  `reports/baselines/capacity_with_prior_pulse_hgb50/pulse_feature_gain.md`
- Decision memo:
  `docs/experiments/2026-05-23_capacity_pulse_coupling_diagnostics.md`

Capacity residual/PULSE-growth correlations from the focused HGB-50 capacity
report:

| Scope | Target | Residual | Pearson | Spearman |
|---|---|---|---:|---:|
| all | `capacity_Ah_k1` | absolute residual | `0.559997` | `0.236657` |
| all | `delta_capacity_Ah` | absolute residual | `0.604807` | `0.304910` |
| C-rate | `capacity_Ah_k1` | absolute residual | `0.894547` | `0.664034` |
| C-rate | `delta_capacity_Ah` | absolute residual | `0.822463` | `0.639033` |
| cold C-rate | `capacity_Ah_k1` | absolute residual | `0.877023` | `0.824406` |
| cold C-rate | `delta_capacity_Ah` | absolute residual | `0.769408` | `0.723490` |

Best prior-PULSE capacity gains versus F4 on the PULSE-covered interval
population:

| Target | Split | Best prior-PULSE group | Gain vs F4 |
|---|---|---|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `0.00669208` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `-0.00574230` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `0.00509620` |
| `delta_capacity_Ah` | condition | `C_P3_stress_pulse` | `0.00249507` |

Decision:

- PULSE growth is strongly associated with capacity residual magnitude,
  especially in C-rate and cold C-rate views.
- Prior PULSE state improves `capacity_Ah_k1` on C-rate, temperature, profile,
  and most other views.
- Prior PULSE state does not solve the C-rate `delta_capacity_Ah` failure; the
  best C-rate delta prior-PULSE row is worse than F4.
- The result supports PULSE as an explanatory scalar diagnostic endpoint, but
  not yet a capacity+PULSE predictive claim or multimodal architecture.

### Milestone 0.8.1

Milestone 0.8.1 checks whether the 0.8 prediction-row coupling signal survives
canonical-model filtering, interval-level aggregation, condition-level
aggregation, parameter-set bootstrap, and simple confound-control
residualization.

Implemented artifacts:

- CLI: `mbp coupling pulse-capacity-robustness`
- Capacity target robustness directory:
  `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/`
- Delta target robustness directory:
  `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/`
- C-rate split robustness directories:
  `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/` and
  `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/`
- Decision memo:
  `docs/experiments/2026-05-23_capacity_pulse_coupling_robustness.md`

Canonical all-split interval/condition results for
`L2_hist_gradient_boosting + F4_state_log_age_scalar`:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 3,751 | `0.593280` | `0.304567` |
| `capacity_Ah_k1` | condition abs residual | 76 | `0.903834` | `0.905345` |
| `delta_capacity_Ah` | interval abs residual | 3,751 | `0.485245` | `0.314490` |
| `delta_capacity_Ah` | condition abs residual | 76 | `0.779516` | `0.773069` |

Canonical C-rate-split results:

| Target | Level | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | interval abs residual | 143 | `0.857653` | `0.633959` |
| `capacity_Ah_k1` | condition abs residual | 12 | `0.956599` | `0.979021` |
| `delta_capacity_Ah` | interval abs residual | 143 | `0.647125` | `0.646779` |
| `delta_capacity_Ah` | condition abs residual | 12 | `0.903590` | `0.881119` |

Residualized diagnostic correlations after controlling for observed state and
condition metadata:

| Target | Scope | n | Pearson | Spearman |
|---|---|---:|---:|---:|
| `capacity_Ah_k1` | all intervals | 3,751 | `0.451220` | `0.251932` |
| `capacity_Ah_k1` | C-rate split | 143 | `0.838145` | `0.627044` |
| `delta_capacity_Ah` | all intervals | 3,751 | `0.330324` | `0.182004` |
| `delta_capacity_Ah` | C-rate split | 143 | `0.519771` | `0.447610` |

Decision:

- PULSE growth remains associated with capacity residual magnitude after
  canonical-model filtering and interval-level aggregation.
- The association is stronger at parameter-set condition level, especially in
  C-rate views, but the C-rate condition sample is small.
- Basic residualization weakens the all-interval association, especially for
  `delta_capacity_Ah`, but C-rate split associations remain visible.
- The result strengthens PULSE as an explanatory scalar diagnostic endpoint.
- A capacity+PULSE predictive claim remains blocked because prior PULSE did not
  solve C-rate `delta_capacity_Ah`, and this milestone is diagnostic rather than
  a predictive benchmark.

### Milestone 0.9

Milestone 0.9 compares the F4 HGB capacity baseline against prior-PULSE feature
groups on the same PULSE-covered interval population. The only allowed PULSE
capacity input is `pulse_1s_resistance_k`. Future PULSE states and PULSE deltas
remain forbidden.

Implemented artifacts:

- CLI: `mbp baseline compare-prior-pulse-capacity`
- Report directory:
  `reports/baselines/capacity_prior_pulse_predictive/`
- Paired condition gains:
  `reports/baselines/capacity_prior_pulse_predictive/paired_condition_gain.csv`
- Split-level bootstrap summary:
  `reports/baselines/capacity_prior_pulse_predictive/split_level_gain_summary.csv`
- C-rate summary:
  `reports/baselines/capacity_prior_pulse_predictive/c_rate_gain_summary.csv`
- Coverage effects:
  `reports/baselines/capacity_prior_pulse_predictive/coverage_effect_summary.csv`
- Claim readiness:
  `reports/baselines/capacity_prior_pulse_predictive/prior_pulse_predictive_claim_readiness.md`
- Decision memo:
  `docs/experiments/2026-05-23_prior_pulse_capacity_prediction.md`

Paired condition-level gain summary:

| Target | Split | Best prior-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | 12 | `0.00669208` | `0.000718651` | `0.00678842` | `0.0131255` | `0.666667` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | 38 | `0.00509620` | `0.00103230` | `0.00493892` | `0.00974339` | `0.605263` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | 12 | `0.0214905` | `0.0137834` | `0.0214668` | `0.0299696` | `0.916667` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | 12 | `-0.00574230` | `-0.0203466` | `-0.00552136` | `0.00835579` | `0.5` |

Coverage effect:

- Capacity-only selected rows: `3,827`
- PULSE-covered selected rows: `3,826`
- Dropped intervals from requiring prior PULSE: `1`
- PULSE-covered parameter sets: `76`
- C-rate interval coverage is unchanged for both capacity targets.

Decision:

- Prior PULSE state supports a narrow non-neural `capacity_Ah_k1`
  level-prediction claim in C-rate, temperature, and profile split diagnostics.
- Prior PULSE does not support a `delta_capacity_Ah` fade-rate claim; C-rate
  delta gain remains negative.
- Coverage loss is small and does not change parameter-set coverage.
- Broad multimodal claims, future-PULSE inputs, EIS, sequence/neural models,
  policy ranking, and CBAT remain blocked.

### Milestone 0.9.1

Milestone 0.9.1 compares prior-PULSE feature groups against the strongest
supplied non-PULSE HGB baselines on the same PULSE-covered interval population.
The non-PULSE pool used the focused HGB-50 report and the v1.1 stress-feature
HGB-50 report.

Implemented artifacts:

- CLI: `mbp baseline compare-prior-pulse-vs-best-nonpulse`
- Report directory:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/`
- Paired gains:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/paired_gain_vs_best_nonpulse.csv`
- Split-level bootstrap summary:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/split_level_gain_vs_best_nonpulse.csv`
- C-rate summary:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/c_rate_gain_vs_best_nonpulse.csv`
- Claim readiness:
  `reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`
- Decision memo:
  `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`

Paired gains versus strongest supplied non-PULSE baselines:

| Target | Split | Prior-PULSE group | Best non-PULSE group | Mean gain | p05 | p50 | p95 | Win rate |
|---|---|---|---|---:|---:|---:|---:|---:|
| `capacity_Ah_k1` | C-rate | `C_P3_stress_pulse` | `F5_log_age_histograms` | `0.000392605` | `-0.00553843` | `0.000727887` | `0.00645520` | `0.5` |
| `capacity_Ah_k1` | temperature | `C_P3_stress_pulse` | `F6_coupled_stress` | `-0.000753049` | `-0.00294184` | `-0.000680351` | `0.00123690` | `0.552632` |
| `capacity_Ah_k1` | profile | `C_P0_state_time_pulse` | `F1_state_time` | `-0.000697582` | `-0.00281975` | `-0.000582270` | `0.00111274` | `0.583333` |
| `delta_capacity_Ah` | C-rate | `C_P3_stress_pulse` | `F4_state_log_age_scalar` | `-0.00234428` | `-0.0169742` | `-0.00185231` | `0.0119867` | `0.583333` |

Decision:

- Prior PULSE still improves over F4 in Milestone 0.9, but the stronger
  “beats best supplied non-PULSE baseline” claim is not supported.
- The best non-PULSE C-rate `capacity_Ah_k1` baseline is
  `F5_log_age_histograms`; prior PULSE is only marginally better on mean gain
  and has a bootstrap interval crossing zero.
- Temperature/profile `capacity_Ah_k1` gains versus strongest non-PULSE are
  negative on average.
- `delta_capacity_Ah` remains unsupported.
- Keep only the narrow “prior PULSE improves over F4” statement. Do not claim
  prior PULSE is the best available non-neural capacity feature path.

### Milestone 1.0

Milestone 1.0 is evidence synthesis and paper-claim lock. It adds no new model
training or feature engineering. The active goal is to convert the completed
baseline sequence into paper-facing artifacts that separate supported claims
from partial, negative, gated, and blocked claims.

Implemented synthesis artifacts:

- Claim ledger: `docs/PAPER_CLAIM_LEDGER.md`
- Figure/table plan: `docs/PAPER_FIGURE_PLAN.md`
- Paper skeleton: `docs/PAPER_SKELETON.md`
- Experiment synthesis:
  `docs/experiments/2026-05-23_evidence_synthesis.md`
- Claim matrix: `reports/synthesis/claim_matrix.csv`
- Evidence matrix: `reports/synthesis/evidence_matrix.md`
- Model ladder summary: `reports/synthesis/model_ladder_summary.csv`
- Split difficulty summary: `reports/synthesis/split_difficulty_summary.csv`
- Negative-result summary: `reports/synthesis/negative_results.md`

Locked claim posture:

- LOG_AGE scalar features and stress features are partially supported, but they
  do not solve C-rate `delta_capacity_Ah`.
- C-rate holdout is the hardest capacity generalization view.
- Canonical RT/50 PULSE is ready for scalar resistance-baseline diagnostics.
- PULSE growth is supported as an explanatory diagnostic for capacity residuals,
  especially in C-rate views.
- Prior PULSE improves `capacity_Ah_k1` over F4 in selected grouped splits, but
  it does not beat the strongest supplied non-PULSE HGB baselines and does not
  improve `delta_capacity_Ah`.
- Quantile HGB uncertainty is not calibrated.
- EIS and CBAT remain gated/blocked.

### Milestone 1.0.1

Milestone 1.0.1 is paper artifact QA and manuscript packaging. It keeps the
project documentation-only and does not authorize model training, new feature
engineering, EIS modeling, neural/sequence models, policy ranking, CBAT, or
broad multimodal claims.

Implemented paper-QA artifacts:

- Manuscript package plan: `docs/MANUSCRIPT_PACKAGE_PLAN.md`
- Source artifact checklist:
  `reports/synthesis/source_artifact_checklist.md`
- Reviewer-risk register:
  `reports/synthesis/reviewer_risk_register.md`

Consistency updates:

- Claim C01 is tightened to:
  "Current scalar LOG_AGE summaries help nonlinear models in some grouped
  views, but gains are mixed."
- `reports/synthesis/split_difficulty_summary.csv` now states that best-known
  rows are descriptive and do not override paired claim-readiness tests.
- The evidence synthesis memo now explicitly states that descriptive prior-PULSE
  best-row delta results do not authorize a fade-rate claim.

### Milestone 1.1

Milestone 1.1 is manuscript draft package v0.1. It is writing and
source-traceability work only. It does not add model training, feature
engineering, EIS modeling, neural/sequence models, policy ranking, CBAT, or
broad multimodal claims.

Implemented manuscript package:

- Package README: `manuscript/README.md`
- Manuscript outline: `manuscript/outline.md`
- Draft sections:
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
- Figure specs: `manuscript/figures/*.md`
- Table specs: `manuscript/tables/*.md`
- Source traceability: `manuscript/source_traceability.md`
- Reviewer response prep: `manuscript/reviewer_response_prep.md`
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_draft_package.md`

The manuscript package uses the Milestone 1.0/1.0.1 claim posture:

- supported: grouped validation benchmark, C-rate difficulty, RT/50 PULSE
  scalar endpoint;
- diagnostic: PULSE growth as residual explanatory signal;
- partial: mixed LOG_AGE value and prior-PULSE-over-F4 level prediction;
- not supported: stress features solving C-rate fade, prior PULSE beating
  strongest non-PULSE, prior PULSE improving `delta_capacity_Ah`, calibrated
  HGB uncertainty;
- gated/blocked: EIS, CBAT, neural/sequence models, policy ranking, and broad
  multimodal claims.

### Milestone 1.2

Milestone 1.2 is figure/table generation and manuscript v0.2 assembly. It is
paper-first reproducibility work only: generated assets are built from existing
tracked reports, synthesis artifacts, and manuscript section drafts. It does
not add model training, feature engineering, EIS modeling, neural/sequence
models, policy ranking, CBAT, or broad multimodal claims.

Implemented manuscript v0.2 assets:

- Reporting CLI:
  - `mbp report build-manuscript-assets`
  - `mbp report check-manuscript`
- Continuous draft: `manuscript/manuscript_v0_2.md`
- Generated SVG figures: `manuscript/figures/generated/*.svg`
- Generated Markdown tables: `manuscript/tables/generated/*.md`
- Captions:
  - `manuscript/captions/figure_captions.md`
  - `manuscript/captions/table_captions.md`
- Manuscript checks:
  - `manuscript/checks/manuscript_claim_check.md`
  - `manuscript/checks/figure_source_check.md`
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_v0_2_assets.md`

Milestone 1.2 checks enforce:

- every manuscript claim ID maps to the paper claim ledger;
- forbidden wording is absent from `manuscript/manuscript_v0_2.md`;
- every figure/table callout has a generated or specification artifact;
- EIS and CBAT claims remain gated or blocked;
- prior-PULSE fade-rate and calibrated-uncertainty claims remain blocked.

### Milestone 1.3

Milestone 1.3 is manuscript v0.3 polish and figure QA. It remains paper-first
and uses existing tracked reports only.

Implemented polish updates:

- Fixed Figure 6 PULSE QA extraction to read canonical RT/50 counts from
  `canonical_target.available_cell_checkups`,
  `canonical_target.missing_cell_checkups`, and
  `canonical_target.duplicate_cell_checkups`.
- Generated `manuscript/manuscript_v0_3.md` with source-section top-level
  headings stripped during assembly.
- Added `manuscript/checks/figure_data_check.md` with source files, consumed
  row counts, key values, and schematic/data-driven status for each figure.
- Extended `mbp report check-manuscript` to scan the continuous manuscript,
  captions, generated tables, figure specs, and source traceability.
- Updated captions with explicit "what not to infer" notes for stress-feature,
  coupling, and prior-PULSE comparison figures.
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_v0_3_polish.md`

### Milestone 1.4

Milestone 1.4 is reader-facing manuscript v0.4 and publication figure pass. It
remains paper-first and uses existing tracked reports only.

Implemented reader-facing updates:

- Generated `manuscript/manuscript_v0_4.md` with raw claim IDs, allowed/blocked
  claim blocks, source-artifact blocks, and referenced-asset notes removed from
  the main body.
- Added `manuscript/manuscript_v0_4_traceability.md` to preserve section,
  claim, figure/table, source artifact, allowed wording, and forbidden wording
  mappings.
- Added reader-facing captions:
  - `manuscript/captions/figure_captions_v0_4.md`
  - `manuscript/captions/table_captions_v0_4.md`
- Added draft v0.4 figure assets under `manuscript/figures/generated_v0_4/`.
- Added reader-facing checks:
  - `mbp report check-reader-manuscript`
  - `manuscript/checks/manuscript_v0_4_claim_check.md`
  - `manuscript/checks/manuscript_v0_4_reader_check.md`
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_v0_4_reader_polish.md`

### Milestone 1.4.1

Milestone 1.4.1 is a reader-facing cleanup and check-hardening patch.

Implemented cleanup updates:

- Removed the remaining `Forbidden wording:` block from
  `manuscript/manuscript_v0_4.md`.
- Added reader-facing prose guardrails to
  `manuscript/manuscript_v0_4_traceability.md`.
- Hardened `mbp report check-reader-manuscript` to fail on `Forbidden wording:`
  in the reader-facing manuscript body.
- Regenerated `manuscript/figures/generated_v0_4/*.svg` without internal
  "Reader-facing draft asset" labels.
- Experiment note:
  `docs/experiments/2026-05-23_manuscript_v0_4_1_reader_cleanup.md`

## Important Implementation Notes

The interval builder preserves result-table timestamps in the public schema, but
uses per-cell relative LOG_AGE windows internally when scanning reduced logs.
This matters because:

- `checkup_event_table.timestamp` is epoch-like result time.
- `modality_table_log_age.timestamp_s` is relative operating time.

The mismatch is covered by
`test_aligns_epoch_checkups_to_relative_log_age_time`.

The LOG_AGE monotonicity audit writes atomically:

- Details are written to a temporary Parquet path first.
- The final report is replaced only after the writer closes successfully.

This prevents a crash or timeout from leaving a corrupt final Parquet report.

The interval subset registry writes Parquet metadata for:

- schema version
- monotonicity policy version
- EFC jitter threshold
- source interval table path

## Baseline Authorization

Baseline data-product prerequisites and the first capacity baseline runner now
exist. First baseline work must use:

- primary subset: `baseline_clean_tolerant`
- mandatory sensitivity subset: exclude
  `sensitivity_flagged_monotonicity == true`
- targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- split views: condition, temperature, C-rate, profile, and corrected
  voltage-window holdouts
- no EIS, sequence models, neural models, policy ranking, CBAT architecture, or
  capacity+PULSE multimodal claims

EIS claims and PULSE scientific claims beyond scalar resistance baselines remain
blocked by their known audit issues. EIS modeling, capacity+PULSE multimodal
claims, sequence/neural models, policy ranking, and CBAT remain blocked.

## Validation

Latest validation run:

```text
.venv/bin/ruff check . --no-cache
All checks passed.

.venv/bin/pytest -p no:cacheprovider
148 passed.

.venv/bin/mbp report check-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md
Manuscript check passed.

.venv/bin/mbp report check-reader-manuscript --manuscript manuscript/manuscript_v0_7.md --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md --traceability manuscript/manuscript_v0_7_traceability.md
Reader manuscript check passed.

.venv/bin/mbp report check-release-candidate
Release candidate check passed.

blocked-phrase scan across v0.9 public-entrypoint and venue-triage files
passed.

git diff --check
passed.

data/Parquet diff and staged checks
passed.
```

Milestone 2.2 report commands were also run successfully:

```text
mbp baseline run-semi-empirical
Semi-empirical capacity report generated: 240 metric rows written to reports/baselines/semi_empirical_capacity_report.json

mbp baseline compare-semi-empirical
Semi-empirical comparison generated: 428 paired F4 rows

mbp analysis replicate-uncertainty
Replicate uncertainty report generated: 3424 model-error rows
```

Milestone 2.3 report command was also run successfully:

```text
mbp analysis calibrate-capacity
Capacity calibration report generated: 96 split-level rows
```

Milestone 2.4 report commands were also run successfully:

```text
mbp features build-run-events
Run-event table generated: 79328229 rows written to data/interim/run_event_table_v1.parquet

mbp features run-events-qa
Run-event QA warning: rows=79328229 covered=3827

mbp features build-sequence-features
Sequence-feature table generated: 3827 rows written to data/interim/interval_sequence_features_v1.parquet

mbp features sequence-qa
Sequence-feature QA passed: rows=3827

mbp baseline run-capacity
Capacity baseline report generated: 288 metric rows written to reports/baselines/capacity_sequence_value_hgb50_report.json

mbp baseline diagnose-sequence-value
Sequence-value diagnostics generated: 24 aggregate/order rows
```

Milestone 2.5 report commands were also run successfully:

```text
mbp analysis knee-labels
Knee label stability report generated: 9576 candidate rows

mbp analysis build-knee-risk-labels
Knee risk label table generated: 3827 rows written to data/interim/knee_risk_label_table_v1.parquet
```

Milestone 2.5.1 report commands were also run successfully:

```text
mbp analysis knee-forensics
Knee inconsistency forensics generated: 19 inconsistent conditions

mbp analysis knee-stable-registry
Knee stable-condition registry generated: 40 stable conditions

mbp analysis threshold-event-labels
Threshold-event labels generated: 22962 interval-label rows

mbp analysis knee-vs-threshold
Knee-vs-threshold decision written to reports/analysis/knee/knee_vs_threshold_decision.md
```

Milestone 2.6 and 2.6.1 report commands were run successfully:

```text
mbp analysis build-threshold-warning-table
Threshold-warning table generated: 3827 rows written to data/interim/threshold_warning_table_v1.parquet

mbp analysis threshold-warning-qa
Threshold-warning QA passed: rows=3827

mbp baseline run-threshold-warning
Threshold-warning baseline report generated: 468 metric rows written to reports/baselines/threshold_warning_l0_l2_report.json
```

Milestone 2.6.2 report commands were also run successfully:

```text
mbp baseline run-threshold-warning --label-policy verified_only
Threshold-warning baseline report generated: 468 metric rows written to reports/baselines/threshold_warning_verified_only_report.json

mbp baseline compare-threshold-warning-censoring
Threshold-warning censoring comparison generated: 18 metric rows

mbp baseline finalize-threshold-warning-claim
Threshold-warning final claim readiness generated: reports/baselines/threshold_warning_l0_l2/threshold_warning_final_claim_readiness.md
```

Milestone 2.1.1 report commands were also run successfully:

```text
mbp baseline compare-prior-eis-pulse
Prior-EIS PULSE comparison generated: 214 paired condition rows

mbp baseline compare-prior-eis-capacity
Prior-EIS capacity comparison generated: 428 paired condition rows

mbp baseline eis-hardening-sensitivity
EIS hardening sensitivity written: passed

mbp baseline eis-claim-readiness
EIS claim-readiness reports written: 12 supported self-endpoint rows; leakage passed
```

Milestone 1.0 adds documentation and tracked synthesis CSV/Markdown artifacts
only. No new code or generated Parquet data products are introduced by this
synthesis step.

Milestone 1.1 adds manuscript Markdown files only. No new code, model training,
feature engineering, generated Parquet data products, or prediction artifacts
are introduced by the manuscript draft package. Milestone 1.1 validation checks
are limited to Markdown/CSV consistency, claim-ID mapping, source-artifact
existence, and forbidden-wording scans.

Milestone 1.2 adds lightweight report-generation code and generated manuscript
Markdown/SVG assets only. The generated figures are first-pass, source-linked
manuscript assets, not publication-polished visual design.

Milestone 1.3 updates that reporting code and generated manuscript package only.
It does not add model training, feature engineering, generated Parquet data
products, prediction artifacts, EIS modeling, or architecture work.

Milestone 1.4 updates reader-facing manuscript/caption/check generation only.
It does not add model training, feature engineering, generated Parquet data
products, prediction artifacts, EIS modeling, or architecture work.

Milestone 1.4.1 updates reader-facing manuscript/check/figure wording only. It
does not add model training, feature engineering, generated Parquet data
products, prediction artifacts, EIS modeling, or architecture work.

The previous `datetime.utcnow()` deprecation warning in
`src/mbp/data/luh_blank/qa_result_data.py` has been fixed.

## Recommended Next Step

Treat the Milestone 8.5 C-rate repair decision as a narrow diagnostic
`delta_capacity_Ah` endpoint, not a reason to open architecture work. Milestone
8.8 closes the current capacity-level reconstruction repair branch. The safest
next work is synthesis, benchmark maintenance, or a new explicitly scoped gate
only if it answers a different charter question.
Do not open knee prediction models, broad neural/sequence models, CBAT, DRT,
EIS embeddings, policy ranking, capacity+PULSE+EIS multimodal architecture,
calibrated-risk claims, calibrated-uncertainty claims, solved C-rate fade
claims, or broad causal/mechanistic claims from the Milestone 8.2/8.2.1/8.3/
8.4/8.5 results.
