# Diagnostic-State Distillation Summary

Schema version: `gate81.diagnostic_state_distillation.v1`

The run predicts current PULSE/EIS diagnostic-state scalars from check-up-k capacity/state/nominal features, then feeds only those predicted diagnostic-state values into downstream non-neural baselines.

Claim readiness: `not_supported`.

Best capacity downstream row: `delta_capacity_Ah_h` horizon `3` split `c_rate_holdout_fold` feature `D3_predicted_pulse_eis_state` relative gain `0.0724454`.
Best threshold-warning downstream row: `event_within_3_checkups` split `condition_fold` feature `D2_predicted_eis_state` relative Brier gain `0.0825232`.
Auxiliary surrogate targets beating train-mean baselines: `12` / `12`.

This is a falsification gate for charter Q2/H3, not an architecture milestone.
