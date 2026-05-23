# Table 4. Claim Matrix

| claim_id | claim_area | claim | status | allowed_wording |
| --- | --- | --- | --- | --- |
| C01 | LOG_AGE capacity baselines | Current scalar LOG_AGE summaries help nonlinear models in some grouped views, but gains are mixed | partially_supported | Current scalar LOG_AGE summaries help nonlinear models in some grouped views, but gains are mixed. |
| C02 | LOG_AGE stress features | LOG_AGE stress features solve C-rate fade prediction | not_supported | Stress features improved some folds but did not solve C-rate delta_capacity_Ah. |
| C03 | Capacity split difficulty | C-rate holdout is the hardest capacity generalization view | supported | C-rate holdout is the dominant unresolved capacity generalization stressor. |
| C04 | PULSE target QA | PULSE RT/50 is usable as scalar resistance endpoint | supported_for_diagnostics | Canonical RT/50 PULSE is robust enough for scalar resistance-baseline diagnostics. |
| C05 | PULSE coupling | PULSE growth explains capacity residuals | supported_for_explanatory_diagnostics | PULSE growth is associated with capacity residual magnitude, especially in C-rate views. |
| C06 | Prior PULSE over F4 | Prior PULSE improves capacity-level prediction over F4 | supported_for_selected_splits | Prior PULSE state improves capacity_Ah_k1 over F4 in selected grouped splits. |
| C07 | Prior PULSE vs best non-PULSE | Prior PULSE beats strongest supplied non-PULSE capacity baseline | not_supported | Prior PULSE improves over F4, but not over the strongest supplied non-PULSE HGB baselines. |
| C08 | Capacity fade target | Prior PULSE improves delta_capacity_Ah | not_supported | delta_capacity_Ah remains an unresolved guardrail limitation. |
| C09 | Quantile diagnostics | Quantile HGB uncertainty is calibrated | not_supported | Quantile metrics are diagnostics only until calibration is tested. |
| C10 | EIS gate | EIS improves any non-EIS outcome | gated | EIS remains gated and untested for predictive claims. |
| C11 | CBAT gate | CBAT architecture is justified | blocked | CBAT remains a reserved late-stage architecture label. |
| C12 | Validation discipline | Grouped condition validation is required for publishable evidence | supported | Headline claims must use grouped validation and replicate-aware condition summaries. |
