# 2026-05-22 Capacity Baseline Ladder Experiments

## Scope

Milestone 0.5 allows capacity-only baselines on the interval table. The work in
this note is limited to:

- targets: `capacity_Ah_k1` and `delta_capacity_Ah`
- scalar interval features
- grouped split evaluation
- strict-vs-tolerant LOG_AGE monotonicity sensitivity
- baseline report artifacts

The work explicitly does not include EIS/PULSE modeling, knee prediction,
sequence models, neural models, CBAT architecture, or policy ranking.

## Experiment 1: Milestone 0.5 Agent Guidance Check

Question: does `AGENTS.md` still block the now-authorized capacity baseline
work?

Finding: `AGENTS.md` already identified Milestone 0.5 as the current phase, so
the review text describing it as Milestone 0.4 was stale. The allowed and
forbidden work lists were still tightened to make the capacity-only boundary
explicit.

Decision:

- Keep Milestone 0.5 authorized for capacity-only baseline execution and report
  hardening.
- Continue blocking EIS/PULSE modeling, knee prediction, sequence models,
  neural models, CBAT architecture, and policy ranking.

## Experiment 2: Prior-Capacity State Feature Correction

Question: should learned capacity baselines use `capacity_Ah_k`?

Finding: `capacity_Ah_k` is the observed check-up state at the start of the
interval. It is not future leakage for either `capacity_Ah_k1` or
`delta_capacity_Ah`. Excluding it would make L1-L3 baselines artificially weak
relative to a normal state-aware forecasting setup.

Decision:

- Keep `F0_time_only` as a deliberately weak sanity feature group.
- Replace the previous non-persistence feature groups with state-aware groups:
  - `F1_state_time`
  - `F2_state_exposure`
  - `F3_state_nominal`
  - `F4_state_log_age_scalar`
- Include `capacity_Ah_k` in all non-persistence feature groups.
- Keep inserted LOG_AGE diagnostics out of every feature group:
  `cap_aged_est_Ah`, `R0_mOhm`, and `R1_mOhm`.

## Experiment 3: L0 Persistence Smoke Run

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --out reports/baselines/capacity_l0_smoke_report.json \
  --predictions-out data/processed/capacity_l0_smoke_predictions.parquet \
  --model-levels L0_persistence
```

Result:

- Status: passed.
- Metric rows: 48.
- Full interval rows: 3,827.
- Primary tolerant rows: 3,827.
- Strict clean rows: 2,773.
- Sensitivity rows after excluding monotonicity-flagged intervals: 2,773.
- Monotonicity-flagged sensitivity rows: 1,054.
- Selected cells: 228.
- Selected parameter sets: 76.

Generated artifacts:

- `reports/baselines/capacity_l0_smoke_report.json`
- `reports/baselines/capacity_l0_smoke/leaderboard.csv`
- `reports/baselines/capacity_l0_smoke/baseline_summary.md`
- `reports/baselines/capacity_l0_smoke/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_smoke/plots/*.csv`
- `data/processed/capacity_l0_smoke_predictions.parquet` (ignored)

Decision:

- The CLI, subset join, split iteration, report renderer, and prediction writer
  work on real data for the dependency-free persistence baseline.
- Keep prediction Parquet files ignored under `data/processed/`.
- Track small report artifacts under `reports/baselines/`.

## Experiment 4: Baseline Dependency Setup

Commands:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/python -m uv sync --extra baseline
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/python -m uv sync --extra dev --extra baseline
```

Finding:

- The first non-escalated dependency sync hit sandbox network resolution
  limits.
- Escalated sync succeeded.
- Syncing only `--extra baseline` removed dev dependencies from the local venv.
- Running `--extra dev --extra baseline` restored both test/lint tooling and
  baseline packages.

Decision:

- Use `.venv/bin/python -m uv` when `uv` is not available as a shell command.
- Use `UV_CACHE_DIR=/tmp/uv-cache` in this environment.
- Keep dev and baseline extras installed together when validation will follow
  a baseline run.

## Experiment 5: Full L0-L3 Capacity Baseline Run

Command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 \
UV_CACHE_DIR=/tmp/uv-cache timeout 7200s .venv/bin/mbp baseline run-capacity \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --out reports/baselines/capacity_l0_l3_report.json \
  --predictions-out data/processed/capacity_l0_l3_predictions.parquet \
  --hgb-max-iter 5
```

Status: passed.

Observed behavior:

- The first default full-ladder attempt produced no stdout after several
  minutes and did not write the final report artifacts before a bounded rerun
  was chosen.
- A bounded rerun with `--hgb-max-iter 5` was started, then the user stopped the
  still-running terminals before completion.
- After the stop, no real `mbp baseline run-capacity` Python process was visible
  from the sandbox process checks; the remaining `pgrep` match was the search
  command itself.
- A later full run with `--hgb-max-iter 5`, a 7,200 second timeout, and four
  thread caps completed successfully.

Results:

- Report status: `passed`.
- Metric rows: `768`.
- Leaderboard rows: `320`.
- Evaluation cards: `160`.
- Full interval rows: `3,827`.
- Primary tolerant rows: `3,827`.
- Strict clean rows: `2,773`.
- Sensitivity rows after excluding monotonicity-flagged intervals: `2,773`.
- Monotonicity-flagged sensitivity rows: `1,054`.
- `hgb_max_iter`: `5`.

Generated artifacts:

- `reports/baselines/capacity_l0_l3_report.json` (`~496K`)
- `reports/baselines/capacity_l0_l3/leaderboard.csv`
- `reports/baselines/capacity_l0_l3/baseline_summary.md`
- `reports/baselines/capacity_l0_l3/evaluation_cards/*.json`
- `reports/baselines/capacity_l0_l3/plots/*.csv`
- `data/processed/capacity_l0_l3_predictions.parquet` (`~4.5M`, ignored)

Primary-run findings:

- Best `capacity_Ah_k1` primary row by condition-mean MAE:
  `L1_ridge` with `F2_state_exposure` on `profile_holdout_fold`
  (`0.078735` condition-mean MAE, `0.213675` worst-condition MAE).
- Best `delta_capacity_Ah` primary row by condition-mean MAE:
  `L2_hist_gradient_boosting` with `F1_state_time` on
  `profile_holdout_fold` (`0.069939` condition-mean MAE, `0.231796`
  worst-condition MAE).
- Hardest split by best available condition-mean MAE was
  `c_rate_holdout_fold` (`0.175406` condition-mean MAE), where
  `L1_ridge` with `F3_state_nominal` was best for `delta_capacity_Ah`.
- Strict-vs-tolerant sensitivity deltas were small on average:
  mean primary-minus-sensitivity condition-mean MAE was approximately
  `-0.000087`, with median approximately `0.000346`.

Decision:

- The CLI exposes `--hgb-max-iter` so later runs can increase iterations without
  code changes.
- Treat the first full L0-L3 report as a bounded baseline artifact because HGB
  used `max_iter=5`.
- Use the report to guide hardening and follow-up reruns before expanding to
  EIS/PULSE, sequence models, neural models, policy ranking, or CBAT.

## Current Findings And Decisions

- `capacity_Ah_k` is allowed and required for the state-aware learned baseline
  feature groups.
- `F0_time_only` remains intentionally weak and does not include
  `capacity_Ah_k`.
- Inserted LOG_AGE diagnostic fields remain blocked from all feature groups.
- The mandatory primary subset is `baseline_clean_tolerant`.
- The mandatory sensitivity scope excludes
  `sensitivity_flagged_monotonicity == true`.
- Baseline artifacts are split by tracking policy:
  - small reports under `reports/baselines/` are trackable
  - generated predictions under `data/processed/` are ignored
- The real-data L0 smoke baseline and bounded real-data L0-L3 ladder both
  completed.
- All future experiments and scientific implementation trials should be
  documented under `docs/experiments/`.

## Validation

Commands:

```bash
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check .
UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest
```

Result:

- Ruff: passed.
- Pytest: `69 passed, 1 warning`.
- Warning: existing `datetime.utcnow()` deprecation warning in
  `src/mbp/data/luh_blank/qa_result_data.py`.
