# Multimodal Battery Prediction

Reproducible grouped-validation benchmark for battery degradation prediction
from capacity check-ups, LOG_AGE operating-history products, scalar PULSE
resistance diagnostics, and gated EIS scalar diagnostics.

The current public release anchor is `benchmark-v0.1-rc2`, a reviewer-facing
release candidate for the benchmark and manuscript handoff package. It includes
tracked code, reports, release checks, claim-ledger artifacts, and manuscript
traceability. It does not include raw data, generated interim Parquets, or
processed prediction Parquets.

## Current Package

Current `main` also includes post-rc2 maintenance and the completed negative
Milestone 9 neural sequence architecture gate. See
`docs/POST_RC2_MAIN_STATUS.md` for the distinction between the published rc2
prerelease and the latest main branch.

- Release: `benchmark-v0.1-rc2`
- Release notes: `docs/RELEASE_NOTES_v0.1-rc2.md`
- Public review entry point: `docs/PUBLIC_REVIEW_ENTRYPOINT.md`
- Benchmark handoff: `docs/BENCHMARK_MANUSCRIPT_HANDOFF.md`
- Manuscript handoff bundle: `manuscript/submission_bundle_v0_8.md`
- Claim ledger: `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`
- Runbook: `docs/BENCHMARK_RUNBOOK.md`
- Command DAG: `docs/COMMAND_DAG.md`
- Artifact manifest: `reports/synthesis/artifact_manifest_v2.csv`

## What This Repository Supports

- grouped condition validation as the headline evidence standard;
- C-rate holdout as the dominant unresolved capacity-transfer stressor;
- RT/50 PULSE as a scalar resistance diagnostic endpoint;
- RT/50 EIS scalar endpoints as diagnostic targets;
- diagnostic 80% capacity-relative threshold-event forecasting beyond
  proximity baselines and under verified-only censoring sensitivity;
- negative fixed-length event-sequence, CUDA Torch MLP, and Milestone 9 CUDA
  CNN/TCN/CNN-LSTM diagnostics showing that sequence/neural reopening is not
  currently justified.

## What Remains Closed

- CBAT architecture work;
- neural or sequence models beyond the completed diagnostic gates;
- DRT or learned EIS embeddings;
- policy ranking;
- detector-knee prediction;
- risk-score calibration claims;
- causal or same-cell counterfactual claims;
- broad multimodal degradation claims.

## Reproducing The Benchmark

1. Install the project in a Python 3.11+ environment.
2. Obtain the Luh-Blank dataset from the original source; raw data are not
   redistributed here.
3. Follow `docs/BENCHMARK_REPRODUCIBILITY.md`.
4. Run commands in the order documented by `docs/BENCHMARK_RUNBOOK.md`.
5. Use `docs/COMMAND_DAG.md` to inspect dependencies.
6. Check tracked and ignored outputs against
   `reports/synthesis/artifact_manifest_v2.csv`.

Useful validation commands:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
mbp report check-release-candidate
git diff --check
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

Use `.venv/bin/` prefixes if running from the project virtual environment.

## Data Policy

The repository tracks source code, documentation, reports, synthesis artifacts,
and manuscript handoff files. It intentionally excludes:

- raw archives under `data/raw/`;
- interim modality, feature, target, label, and run-event Parquets under
  `data/interim/`;
- split-registry Parquets under `data/splits/`;
- processed prediction Parquets under `data/processed/`.

The artifact manifest lists expected local generated products so reruns can be
audited without committing large data artifacts.

## For Reviewers And Collaborators

Start with `docs/PUBLIC_REVIEW_ENTRYPOINT.md`. It gives the shortest route
through the release, claim ledger, manuscript package, and reproducibility
materials without requiring the full development history.
