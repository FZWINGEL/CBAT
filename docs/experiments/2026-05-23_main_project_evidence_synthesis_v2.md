# Milestone 3.0 Main-Project Evidence Synthesis v2

Date: 2026-05-23

## Scope

This synthesis refresh consolidates all completed main-project gates after
Milestone 2.6.2. It is a technical decision layer, not a manuscript polish pass
and not a new modeling milestone.

No new model training, feature engineering, neural models, sequence models,
transformers, CBAT, DRT, EIS embeddings, policy ranking, causal claims, or
same-cell counterfactual claims were added.

## Evidence Summary

| Track | Result | Claim posture |
|---|---|---|
| Capacity baseline ladder | Grouped HGB baselines identify C-rate as the hardest capacity transfer view. | Supported for grouped benchmark evidence. |
| LOG_AGE scalar/stress features | Scalar/stress summaries help some views, but C-rate fade remains unresolved. | Partially supported; C-rate fade claim not supported. |
| PULSE QA/resistance | Canonical RT/50 PULSE is usable as a scalar resistance endpoint. | Supported for diagnostics. |
| Capacity-PULSE coupling | PULSE growth is associated with capacity residual magnitude, especially in C-rate views. | Explanatory diagnostic only. |
| Prior PULSE | Improves `capacity_Ah_k1` over F4 in selected splits, but not strongest non-PULSE and not `delta_capacity_Ah`. | Selected-split support only. |
| EIS QA/features/baselines | EIS RT/50 is QA-ready and scalar endpoints are diagnostic; prior-EIS signal is narrow and profile-split limited. | Diagnostic and partially supported only. |
| Semi-empirical comparator | Ridge-style stress comparators are valid domain checks but do not beat strongest HGB/stress baselines in C-rate views. | Comparator useful; superiority not supported. |
| Replicate uncertainty | Condition-triplet spread contextualizes errors but does not validate intervals. | Diagnostic only. |
| Grouped calibration | Conformal methods improve mean coverage, but C-rate coverage fails. | Calibrated uncertainty blocked. |
| Temporal history gate | Order-aware event features do not beat aggregate/shuffled controls. | Sequence models blocked. |
| Detector-knee labels | Detector knees are not replicate-consistent enough for prediction. | Knee prediction blocked. |
| Threshold warning | 80% threshold-event forecasting survives proximity and verified-only censoring sensitivity. | Supported for diagnostic forecasting. |

## Locked Supported Claims

- Grouped validation and condition-level reporting are necessary for defensible evidence.
- C-rate holdout is the dominant unresolved capacity generalization view.
- PULSE RT/50 is usable as a scalar resistance endpoint.
- EIS RT/50 scalar endpoints are usable diagnostic targets.
- Non-neural baselines can forecast the 80% capacity-relative threshold event diagnostically under grouped validation, beyond proximity baselines and under verified-only sensitivity.

## Diagnostic or Partial Claims

- LOG_AGE scalar and stress features help in some grouped views.
- PULSE growth explains capacity residual magnitude, especially under C-rate holdout.
- Prior PULSE improves capacity level over F4 in selected splits.
- Prior EIS has narrow profile-split diagnostic signal.
- Semi-empirical comparators are useful domain checks.
- Replicate spread contextualizes C-rate error.
- Grouped conformal improves mean coverage but not C-rate coverage.

## Not-Supported Claims

- LOG_AGE stress features solve C-rate fade.
- Prior PULSE beats the strongest non-PULSE baseline.
- Prior PULSE improves `delta_capacity_Ah`.
- Prior EIS improves C-rate capacity/fade.
- Semi-empirical stress models beat strongest HGB/stress baselines.
- Ordered event structure justifies sequence models.
- Detector-knee labels are stable enough for prediction.
- HGB quantile or conformal uncertainty is globally calibrated.

## Blocked Claims

- CBAT validation.
- Neural or sequence model justification.
- Policy ranking.
- DRT or learned EIS embeddings.
- Detector-knee prediction.
- Calibrated risk.
- Causal or same-cell counterfactual claims.
- Broad multimodal degradation claims.

## Next-Branch Decision

Recommended next branch: return to synthesis/manuscript integration and
benchmark release preparation.

Only one technical branch remains plausibly justified: a narrow
threshold-warning calibration branch. It must remain non-neural, grouped,
prospective, and explicitly separate calibrated-risk claims from diagnostic
forecasting scores.

Do not open CBAT, sequence/neural models, DRT, EIS embeddings, policy ranking,
or causal/same-cell counterfactual work from the current evidence.
