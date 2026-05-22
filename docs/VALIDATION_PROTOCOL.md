# Validation Protocol

Milestone 0.5 authorizes only the first scalar capacity baseline ladder.

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

Allowed Milestone 0.5 targets:

- `capacity_Ah_k1`
- `delta_capacity_Ah`

Allowed Milestone 0.5 split views:

- `condition_fold`
- `temperature_holdout_fold`
- `c_rate_holdout_fold`
- `profile_holdout_fold`
- `voltage_window_holdout_fold`

Blocked until later milestones:

- EIS and PULSE scientific claims.
- Sequence models, neural models, policy ranking, and CBAT architecture.
