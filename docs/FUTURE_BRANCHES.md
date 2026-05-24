# Future Branches

These are organization notes for future work. They do not open any branch by
themselves and do not authorize new claims.

## Future: Threshold-Warning Calibration Branch

Purpose: test whether the 80% threshold-event diagnostic score can be
calibrated under grouped validation.

Allowed scope:

- grouped Platt or isotonic calibration
- threshold-warning target only
- calibration curves and ECE/Brier diagnostics

Blocked:

- policy ranking
- detector-knee prediction
- CBAT
- neural or sequence models
- causal claims

## Future: Manuscript Integration from benchmark-v0.1-rc2

Purpose: integrate the validated reviewer-facing benchmark release-candidate
evidence into the manuscript package.

Allowed scope:

- claim-ledger-aligned manuscript updates
- figure/table refresh from tracked reports
- no-overclaim checks

Blocked:

- new modeling
- new feature engineering
- broad multimodal claims

## Future: Release Automation / Benchmark Command Executor

Purpose: convert the documented command DAG into a runnable workflow if manual
reproducibility becomes too fragile.

Allowed scope:

- command orchestration
- artifact freshness checks
- resumable pipeline execution

Blocked:

- changing scientific claim posture
- adding model families
- committing generated data products
