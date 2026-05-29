# Data And Code Availability v0.8

## Code Availability

The benchmark source code, tracked reports, release documentation, and
manuscript traceability artifacts are available in the repository release:

- Tag: `benchmark-v0.2-rc1`
- Release URL: `https://github.com/FZWINGEL/CBAT/releases/tag/benchmark-v0.2-rc1`
- Release notes: `docs/RELEASE_NOTES_v0.2-rc1.md`
- Benchmark runbook: `docs/BENCHMARK_RUNBOOK.md`
- Command DAG: `docs/COMMAND_DAG.md`
- Artifact manifest: `reports/synthesis/artifact_manifest_v2.csv`

The executable release check is:

```bash
mbp report check-release-candidate
```

## Data Availability

The release does not redistribute raw battery-aging data. Full reruns require
the user to obtain the Luh-Blank dataset from its original source and place the
local files according to `docs/BENCHMARK_REPRODUCIBILITY.md` and
`docs/BENCHMARK_RUNBOOK.md`.

Generated local products are intentionally excluded from version control,
including:

- raw archives under `data/raw/`;
- interim modality, interval, feature, target, label, and run-event Parquets
  under `data/interim/`;
- split-registry Parquets under `data/splits/`;
- processed prediction Parquets under `data/processed/`.

The tracked artifact manifest lists both tracked reports and ignored local data
products so reruns can be audited without committing large generated files.

## Reproducibility Entry Points

Recommended order for a local rerun:

1. Follow `docs/BENCHMARK_REPRODUCIBILITY.md`.
2. Use `docs/BENCHMARK_RUNBOOK.md` for command order.
3. Use `docs/COMMAND_DAG.md` to inspect dependencies.
4. Confirm expected artifacts with `reports/synthesis/artifact_manifest_v2.csv`.
5. Run `mbp report check-release-candidate` before making release or manuscript
   changes.

## Claim Boundary

The code and data package supports the claims in
`docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`. It does not include or authorize raw
data redistribution, CBAT, neural or sequence models, policy ranking,
detector-knee prediction, causal claims, same-cell counterfactual claims, or
broad multimodal degradation claims.
