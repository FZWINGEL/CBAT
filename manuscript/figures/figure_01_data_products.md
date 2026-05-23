# Figure 01: Data-Product Architecture

Claim supported: C12 grouped benchmark foundation.

Source artifacts:

- `docs/SCHEMA_REGISTRY.md`
- `docs/REPO_STATUS.md`

Intended plot type: pipeline diagram.

Key content:

- result data and LOG_AGE inputs;
- `cell_condition_table`;
- `checkup_event_table`;
- `interval_table`;
- `split_registry_v1`;
- `interval_subset_registry_v1`;
- `interval_stress_features_v1_1`;
- `pulse_target_table`;
- reports and claim ledger.

Risk/limitation:

- Generated Parquet artifacts are local and ignored; the figure should describe
  reproducible data products, not imply they are committed.

Caption draft:

> Linked data-product architecture. Result data and LOG_AGE operating histories
> are converted into condition metadata, check-up events, interval rows, grouped
> split labels, monotonicity-aware interval subsets, stress-feature sidecars,
> and RT/50 PULSE target tables before any paper-facing baseline is evaluated.
