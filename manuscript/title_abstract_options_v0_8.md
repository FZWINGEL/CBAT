# Title And Abstract Options v0.8

These options are venue-neutral. Choose one title and one abstract, then adapt
length and style to the target journal or conference.

## Title Options

### Option 1: Benchmark-Focused

Grouped-Validation Benchmark for Battery Degradation Prediction from Operating
Histories and Diagnostic Check-Ups

### Option 2: Methods And Data-Product Focused

Reproducible Data Products and Grouped Baselines for Multimodal Battery Aging
Benchmarks

### Option 3: Diagnostic-Endpoint Focused

Diagnostic PULSE and EIS Endpoints in a Claim-Gated Battery Degradation
Benchmark

## Abstract Option A: Concise Journal Style

Reliable battery-degradation prediction requires evidence that models
generalize beyond the operating regimes represented in training data. We
present a reproducible grouped-validation benchmark for the Luh-Blank
commercial-cell aging dataset, treating the study design as 76 operating
conditions with three replicate cells each. The benchmark links capacity
check-ups, operating-history summaries, PULSE resistance diagnostics, and
quality-controlled EIS scalar endpoints through condition-level validation,
claim-ledger governance, and release-candidate reproducibility checks. Across
capacity baselines, LOG_AGE stress features, PULSE and EIS diagnostics,
semi-empirical comparators, replicate uncertainty, grouped interval checks,
temporal-order falsification, knee-label stability, and threshold-event
forecasting, the results support a bounded benchmark narrative. C-rate holdout
remains the hardest capacity generalization view. PULSE and EIS are useful as
scalar diagnostic endpoints, while broad multimodal and architecture claims are
not supported. A non-neural model forecasts the 80% capacity-relative threshold
event diagnostically under grouped validation, beyond proximity baselines and
under verified-only censoring sensitivity, but risk-score calibration and
policy claims remain closed. The release package provides code, reports,
claim-ledger artifacts, and reproducibility documentation, while excluding raw
data and generated Parquet products.

## Abstract Option B: Extended Reviewer Style

Battery aging datasets increasingly provide rich diagnostic and operating
history records, but predictive claims can be overstated when validation ignores
condition structure, replicate variability, or modality readiness. We introduce
a claim-gated benchmark package for multimodal degradation prediction using the
Luh-Blank comprehensive aging dataset. The workflow starts from audited data
products and uses grouped splits over operating-condition triplets, not random
row or cell splits. It then evaluates a ladder of capacity baselines, scalar
LOG_AGE exposure and stress features, PULSE resistance targets, EIS QA and
scalar endpoints, semi-empirical stress comparators, replicate uncertainty,
grouped interval checks, temporal-order falsification, degradation-knee label
stability, and 80% threshold-event warning diagnostics.

The resulting evidence is deliberately mixed. C-rate holdout is the dominant
capacity generalization stressor. LOG_AGE stress features help some views but
do not resolve C-rate fade. PULSE RT/50 and RT/50 EIS features are useful
scalar diagnostic endpoints, but prior PULSE and EIS do not support broad
non-EIS predictive claims. Semi-empirical comparators are valuable domain
checks but are weaker than the strongest grouped HGB baselines in the hardest
views. Grouped interval methods improve average coverage but fail the C-rate
gate, so interval-reliability claims remain closed. Event-order summaries do
not beat aggregate and shuffled controls robustly, blocking sequence-model
readiness. Detector-based knee labels are too replicate-inconsistent for
prediction. The one positive prediction-like result is a narrow diagnostic:
non-neural baselines forecast the 80% capacity-relative threshold event beyond
event-rate and proximity baselines, including under verified-only censoring
sensitivity. The benchmark is released with source-linked reports, a v2 claim
ledger, a command runbook, an artifact manifest, release checks, and manuscript
traceability so future work can extend the benchmark without weakening the
claim boundaries.
