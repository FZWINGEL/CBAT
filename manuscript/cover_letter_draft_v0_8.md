# Cover Letter Draft v0.8

Dear Editor,

We are pleased to submit our manuscript, "Grouped-Validation Benchmark for
Battery Degradation Prediction from Operating Histories and Diagnostic
Check-Ups," for consideration.

This work presents a reproducible, claim-gated benchmark for battery
degradation prediction using the Luh-Blank comprehensive aging dataset. Rather
than centering the contribution on a new architecture, the study asks which
signals remain defensible under condition-level validation, replicate-aware
diagnostics, modality-readiness checks, and explicit negative-result gates.

The manuscript contributes:

- a grouped-validation benchmark treating the dataset as 76 operating
  conditions with three replicate cells each;
- source-linked data products and reports for capacity, LOG_AGE, PULSE, and
  gated EIS diagnostics;
- semi-empirical, replicate, interval-reliability, temporal-order, knee-label,
  and threshold-warning gates;
- a v2 claim ledger distinguishing supported, diagnostic-only, not-supported,
  and blocked claims;
- a reproducible release package at `benchmark-v0.1-rc2`.

The results are intentionally bounded. The evidence supports diagnostic PULSE
and EIS scalar endpoints, identifies C-rate holdout as the hardest capacity
generalization view, and supports a narrow non-neural 80% threshold-event
forecasting diagnostic beyond proximity baselines. It does not support CBAT,
neural or sequence models, DRT or learned EIS embeddings, policy ranking,
detector-knee prediction, causal statements, or broad multimodal degradation
claims.

We believe the manuscript will be useful to readers who need a reproducible
benchmark for battery degradation modeling, including the negative results and
claim boundaries needed to prevent architecture-first overinterpretation.

Sincerely,

[Authors]
