# Benchmark v0.1-rc1 Summary

Tag: `benchmark-v0.1-rc1`

Tagged commit: `ff4c8c2`

## Release Scope

This release candidate packages the current grouped-validation benchmark for
battery degradation prediction. It is a source, report, claim-ledger, and
reproducibility release. It does not include raw data, generated interim
Parquets, processed prediction Parquets, or new scientific claims beyond the v2
claim ledger.

## Included Tracked Artifacts

- v2 main-project claim ledger and claim matrix
- gate-status, blocked-claim, decision-matrix, and next-branch reports
- benchmark reproducibility guide
- benchmark runbook and command DAG
- artifact manifest and artifact policy
- executable release-candidate check
- release notes and tag-preparation docs
- manuscript/package artifacts already tracked in the repository
- audit, baseline, analysis, and synthesis reports used by the claim ledger

## Ignored Local Data Artifacts

The release requires local raw data and generated products for full reruns, but
does not commit them. Ignored artifacts include:

- raw archives under `data/raw/`
- interim modality, interval, feature, target, and label Parquets under
  `data/interim/`
- split-registry Parquets under `data/splits/`
- processed prediction Parquets under `data/processed/`

## Supported Claims

- grouped condition validation is required for headline evidence
- C-rate holdout is the hardest capacity generalization view
- RT/50 PULSE is usable as a scalar resistance diagnostic endpoint
- RT/50 EIS scalar endpoints are usable diagnostic targets
- non-neural baselines forecast the 80% capacity-relative threshold event
  diagnostically beyond proximity under verified-only censoring sensitivity

## Diagnostic-Only Claims

- LOG_AGE scalar/stress features help in selected views but remain mixed
- PULSE growth is associated with capacity residual magnitude
- prior PULSE improves capacity level over F4 in selected splits only
- prior EIS has narrow profile-split signal
- semi-empirical comparators are useful domain checks
- replicate spread contextualizes C-rate error
- grouped conformal improves mean coverage but not C-rate coverage

## Blocked Claims

- CBAT validation
- neural or sequence model readiness
- DRT or learned EIS embedding claims
- policy ranking
- detector-knee prediction
- calibrated risk
- calibrated uncertainty
- causal or same-cell counterfactual claims
- broad multimodal degradation improvement claims

## Validation Status

Before tagging `benchmark-v0.1-rc1`:

- `.venv/bin/ruff check . --no-cache`: passed
- `.venv/bin/pytest -p no:cacheprovider`: passed, 148 tests
- `.venv/bin/mbp report check-release-candidate`: passed
- `git diff --check`: passed
- `git status --short`: clean
- no generated data or Parquet artifacts were staged

## Reproduction Entry Points

- `docs/BENCHMARK_REPRODUCIBILITY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/COMMAND_DAG.md`
- `reports/synthesis/artifact_manifest_v2.csv`
- `docs/TAGGING_RELEASE_CANDIDATE.md`
