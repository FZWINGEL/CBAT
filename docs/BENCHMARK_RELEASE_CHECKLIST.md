# Benchmark Release Checklist

Use this checklist before tagging or handing off a release candidate.

- [ ] `ruff check . --no-cache` passes if code changed.
- [ ] `pytest -p no:cacheprovider` passes if code changed.
- [ ] `mbp report check-release-candidate` passes.
- [ ] `git diff --check` passes.
- [ ] `docs/RELEASE_NOTES_v0.1-rc1.md` exists.
- [ ] If creating a reviewer-facing rc2 archive, `docs/RELEASE_NOTES_v0.1-rc2.md`
      and `docs/BENCHMARK_V0_1_RC2_SUMMARY.md` exist.
- [ ] `docs/TAGGING_RELEASE_CANDIDATE.md` exists.
- [ ] No raw data files are staged.
- [ ] No `data/interim`, `data/splits`, or `data/processed` Parquets are
      staged.
- [ ] `docs/REPO_STATUS.md` and `AGENTS.md` name the same current phase.
- [ ] `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` and
      `reports/synthesis/main_project_claim_matrix_v2.csv` agree on supported,
      diagnostic, not-supported, and blocked claims.
- [ ] Blocked claims remain blocked: CBAT, sequence/neural models, DRT, EIS
      embeddings, policy ranking, causal claims, calibrated risk, calibrated
      uncertainty, detector-knee prediction, and broad multimodal claims.
- [ ] All tracked artifacts listed in `reports/synthesis/artifact_manifest_v2.csv`
      exist.
- [ ] Ignored artifact paths in the manifest are under ignored generated data
      locations.
- [ ] The command DAG covers audit, ingestion, intervals, splits, feature
      sidecars, target sidecars, baselines, diagnostics, and synthesis.
- [ ] `reports/synthesis/release_candidate_check.md` has been refreshed.
- [ ] `docs/CODEX_NEXT_WORK.md` reflects the current recommended branch and
      blocked branches.
