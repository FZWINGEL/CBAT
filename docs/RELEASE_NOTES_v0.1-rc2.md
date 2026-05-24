# Benchmark v0.1-rc2 Release Notes

Release title: Benchmark v0.1-rc2 release-polished grouped-validation battery
degradation benchmark.

## Release Identity

- Tag: `benchmark-v0.1-rc2`
- Tagged commit: `e499b12`
- GitHub release: `https://github.com/FZWINGEL/CBAT/releases/tag/benchmark-v0.1-rc2`
- Release status: published prerelease

`benchmark-v0.1-rc1` remains the pure validation checkpoint at commit
`ff4c8c2`. `benchmark-v0.1-rc2` is the reviewer-facing handoff archive that
adds release-polish documents without changing the scientific evidence base.

## Included

- grouped capacity baseline ladder and split diagnostics
- LOG_AGE scalar/stress-feature reports
- PULSE scalar resistance diagnostics and capacity-coupling diagnostics
- EIS QA, scalar feature readiness, scalar diagnostic baselines, and claim hardening
- semi-empirical comparator reports
- replicate uncertainty and grouped interval-calibration diagnostics
- LOG_AGE run-event and temporal-order falsification reports
- knee-label stability and threshold-event label readiness reports
- 80% threshold-event warning diagnostic baseline and censoring hardening
- v2 claim ledger, claim matrix, gate status, blocked-claim register, and next-branch decision
- benchmark reproducibility docs, runbook, command DAG, artifact manifest, release checks, and handoff docs

## Supported Claims

- grouped condition validation is required for headline evidence
- C-rate holdout is the hardest capacity generalization view
- RT/50 PULSE is usable as a scalar resistance diagnostic endpoint
- RT/50 EIS scalar endpoints are usable diagnostic targets
- non-neural baselines forecast the 80% capacity-relative threshold event diagnostically beyond proximity under verified-only censoring sensitivity

## Diagnostic-Only Claims

- LOG_AGE scalar/stress features help in selected views but remain mixed
- PULSE growth is associated with capacity residual magnitude
- prior PULSE improves capacity level over F4 in selected splits only
- prior EIS has narrow profile-split signal
- semi-empirical comparators are useful domain checks
- replicate spread contextualizes C-rate error
- grouped conformal improves mean coverage but not C-rate coverage

## Not-Supported Claims

- LOG_AGE stress features solve C-rate fade
- prior PULSE beats the strongest supplied non-PULSE baseline
- prior PULSE improves `delta_capacity_Ah`
- prior EIS improves C-rate capacity or fade broadly
- semi-empirical baselines beat strongest HGB/stress baselines
- ordered event structure justifies sequence models
- detector-knee labels are stable enough for prediction
- raw HGB quantiles or conformal intervals validate global interval reliability

## Blocked Claims

- CBAT validation
- neural or sequence model readiness
- DRT or learned EIS embedding claims
- policy ranking
- detector-knee prediction
- calibrated risk
- causal or same-cell counterfactual claims
- broad multimodal degradation improvement claims

## Required Local Data Artifacts

The release does not include raw data or generated Parquets. Local reruns need
the raw dataset and generated products described in `docs/BENCHMARK_RUNBOOK.md`
and `reports/synthesis/artifact_manifest_v2.csv`.

## Validation Commands

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
mbp report check-release-candidate
git diff --check
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

## Known Limitations

- Full raw-to-synthesis reruns require substantial local storage and memory.
- The command DAG is documented and checked for command coverage, but it is not a workflow executor.
- Calibrated risk and global interval reliability remain blocked.
- Sequence, CBAT, policy, and causal branches remain blocked.
