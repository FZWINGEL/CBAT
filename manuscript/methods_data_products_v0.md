# Methods: Data Products v0

The benchmark is built from linked data products rather than ad hoc notebook
joins. The core cohort contains 228 cells, interpreted as 76 parameter-set
conditions with three replicates per condition. The current linked data-product
stack includes cell condition metadata, check-up events, LOG_AGE operating
history, interval tables, grouped split labels, monotonicity-aware interval
subsets, LOG_AGE stress-feature sidecars, and canonical RT/50 PULSE target
tables.

The LOG_AGE cohort table contains 904,977,105 rows across all 228 cells.
Capacity targets are organized around 3,827 check-up intervals derived from
4,055 check-up events. The interval table is the modeling spine: one row
represents a transition from check-up `k` to `k+1`, with prior state at `k`,
future target at `k+1`, condition metadata, split labels, and quality flags.

LOG_AGE monotonicity issues are handled through an explicit policy rather than
silently dropped. The tolerant baseline subset keeps all 3,827 intervals while
flagging 1,054 intervals for monotonicity sensitivity. The strict subset has
2,773 intervals. Baseline reports therefore use the tolerant subset as primary
and retain strict exclusion as a sensitivity view.

Stress features are modular sidecars keyed by `cell_id`, `checkup_k`, and
`checkup_k_next`. The v1.1 sidecar uses timestamp-weighted dwell, coverage/gap
diagnostics, current-sign audit evidence, and scalar event summaries. Target
derived diagnostics such as capacity loss per day or EFC are not allowed as
predictive input features.

PULSE targets are also sidecars. The canonical resistance transition target is
RT/50 `delta_pulse_1s_resistance`, with RT/50 `delta_pulse_10ms_resistance` as
a secondary diagnostic. Alignment, direction handling, and missingness are
reported explicitly. PULSE targets remain resistance endpoints and scalar
diagnostic features; future PULSE state and PULSE deltas are not allowed as
capacity inputs.

Allowed claim:

- C12: grouped validation and condition-level reporting are required for
  publishable evidence.

Blocked claims:

- C10: EIS has demonstrated predictive value.
- C11: CBAT architecture is justified.

Source artifacts:

- `docs/REPO_STATUS.md`
- `docs/SCHEMA_REGISTRY.md`
- `docs/LOG_AGE_MONOTONICITY_POLICY.md`
- `docs/PULSE_TARGET_POLICY.md`
- `reports/audit/interval_subset_report.json`
- `reports/audit/stress_feature_v1_1_qa_report.json`
- `reports/audit/pulse_qa_report.json`

Figure/table references:

- Figure 1: data-product architecture.
- Table 1: dataset audit.
