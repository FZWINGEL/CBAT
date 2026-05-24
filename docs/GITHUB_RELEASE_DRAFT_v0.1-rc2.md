# Benchmark v0.1-rc2 - Release-Polished Grouped-Validation Battery Degradation Benchmark

This release candidate packages a reproducible grouped-validation benchmark for
battery degradation prediction from capacity check-ups, operating-history
features, PULSE resistance, and gated EIS diagnostics. It includes claim-ledger
governance, strict condition-level validation, diagnostic PULSE/EIS endpoints,
negative-result gates, threshold-event warning diagnostics, and release
reproducibility documentation. It does not include raw data or generated
Parquet data products.

`benchmark-v0.1-rc1` remains the validation checkpoint at `ff4c8c2`.
`benchmark-v0.1-rc2` points to `e499b12` and includes the release-polish
handoff files.

## Highlights

- Reviewer-facing release tag: `benchmark-v0.1-rc2`
- Tagged commit: `e499b12`
- Validation checkpoint tag: `benchmark-v0.1-rc1` at `ff4c8c2`
- Executable release check: `mbp report check-release-candidate`
- Grouped validation and condition-level reporting are the headline evidence standard.
- PULSE and EIS are supported as scalar diagnostic endpoints, not broad multimodal improvement claims.
- Non-neural baselines support a diagnostic 80% threshold-event forecasting claim beyond proximity and under verified-only censoring sensitivity.
- Negative-result gates remain explicit for C-rate fade, global interval reliability, temporal order/sequence readiness, detector-knee prediction, and broad multimodal claims.

## What Is Included

- source code and tests
- v2 claim ledger and claim matrix
- benchmark runbook and command DAG
- artifact manifest and artifact policy
- executable release-candidate check
- release notes and tag-preparation docs
- audit, baseline, analysis, and synthesis reports
- release-polish handoff documents

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

The following checks passed before the validation checkpoint tag:

- `.venv/bin/ruff check . --no-cache`
- `.venv/bin/pytest -p no:cacheprovider` with 148 tests
- `.venv/bin/mbp report check-release-candidate`
- `git diff --check`
- `git status --short`
- staged data-artifact check for `data/` and `.parquet` paths

The rc2 release was published as a GitHub prerelease at:
`https://github.com/FZWINGEL/CBAT/releases/tag/benchmark-v0.1-rc2`.

## Known Limitations

- Full reruns require local raw data and sufficient compute for large LOG_AGE-derived products.
- The command DAG is a documented execution map, not a workflow executor.
- Calibrated risk and global interval reliability remain unsupported.
- Sequence models, CBAT, DRT/embeddings, policy ranking, and causal claims remain blocked by the current evidence.

## Recommended Next Branch

Default: manuscript integration from `benchmark-v0.1-rc2`.

Optional technical branch: narrow threshold-warning calibration only, with
grouped calibration and no policy ranking, detector-knee prediction, CBAT,
neural models, sequence models, or causal claims.
