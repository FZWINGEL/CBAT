# Benchmark v0.1-rc1 - Grouped-Validation Battery Degradation Benchmark

This release candidate packages a reproducible grouped-validation benchmark for
battery degradation prediction from capacity check-ups, operating-history
features, PULSE resistance, and gated EIS diagnostics. It includes claim-ledger
governance, strict condition-level validation, diagnostic PULSE/EIS endpoints,
negative-result gates, threshold-event warning diagnostics, and release
reproducibility documentation. It does not include raw data or generated
Parquet data products.

## Highlights

- Validated release-candidate tag: `benchmark-v0.1-rc1`
- Tagged commit: `ff4c8c2`
- Executable release check: `mbp report check-release-candidate`
- Grouped validation and condition-level reporting are the headline evidence
  standard.
- PULSE and EIS are supported as scalar diagnostic endpoints, not broad
  multimodal improvement claims.
- Non-neural baselines support a diagnostic 80% threshold-event forecasting
  claim beyond proximity and under verified-only censoring sensitivity.
- Negative-result gates remain explicit for C-rate fade, calibrated
  uncertainty, temporal order/sequence readiness, detector-knee prediction, and
  broad multimodal claims.

## What Is Included

- source code and tests
- v2 claim ledger and claim matrix
- benchmark runbook and command DAG
- artifact manifest and artifact policy
- release-candidate check output
- audit, baseline, analysis, and synthesis reports
- release notes and tag-preparation docs

## What Is Not Included

- raw dataset archives
- generated interim Parquets
- processed prediction Parquets
- CBAT architecture
- neural or sequence models
- DRT or learned EIS embeddings
- policy ranking
- calibrated risk claims
- detector-knee prediction
- causal or same-cell counterfactual claims

## Validation

The following checks passed before tagging:

- `.venv/bin/ruff check . --no-cache`
- `.venv/bin/pytest -p no:cacheprovider` with 148 tests
- `.venv/bin/mbp report check-release-candidate`
- `git diff --check`
- `git status --short`
- staged data-artifact check for `data/` and `.parquet` paths

## Known Limitations

- Full reruns require local raw data and sufficient compute for large
  LOG_AGE-derived products.
- The command DAG is a documented execution map, not a workflow executor.
- Calibrated risk and calibrated uncertainty remain unsupported.
- Sequence models, CBAT, DRT/embeddings, policy ranking, and causal claims
  remain blocked by the current evidence.

## Recommended Next Branch

Default: return to benchmark/manuscript integration.

Optional technical branch: narrow threshold-warning calibration only, with
grouped calibration and no policy ranking, detector-knee prediction, CBAT,
neural models, sequence models, or causal claims.
