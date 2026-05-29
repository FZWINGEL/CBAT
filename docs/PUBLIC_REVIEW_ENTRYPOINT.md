# Public Review Entry Point

This is the shortest route through the current benchmark and manuscript
package for an external reviewer or collaborator.

`benchmark-v0.1-rc2` remains the stable external-review anchor. Current `main`
also contains post-rc2 maintenance and the completed negative Milestone 9
neural sequence architecture gate; see `docs/POST_RC2_MAIN_STATUS.md` for that
addendum.

## Start Here

| Need | File |
|---|---|
| Release summary | `docs/BENCHMARK_V0_1_RC2_SUMMARY.md` |
| Release notes | `docs/RELEASE_NOTES_v0.1-rc2.md` |
| Post-rc2 main status | `docs/POST_RC2_MAIN_STATUS.md` |
| Post-M9 review checklist | `docs/POST_M9_REVIEW_CHECKLIST.md` |
| Claim boundaries | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Gate status | `reports/synthesis/main_project_gate_status.md` |
| Manuscript | `manuscript/manuscript_v0_7.md` |
| Supplement | `manuscript/supplement_v0_7.md` |
| Submission bundle | `manuscript/submission_bundle_v0_8.md` |
| Traceability | `manuscript/manuscript_v0_7_traceability.md` |
| Reproduction guide | `docs/BENCHMARK_REPRODUCIBILITY.md` |
| Command runbook | `docs/BENCHMARK_RUNBOOK.md` |

## What The Package Contains

- benchmark code and tests;
- tracked audit, baseline, analysis, synthesis, and manuscript reports;
- claim ledger and blocked-claim register;
- release-check tooling;
- reproducibility guide, runbook, command DAG, and artifact manifest;
- venue-neutral manuscript and handoff material.

## What The Package Excludes

- raw dataset archives;
- generated interim Parquets;
- processed prediction Parquets;
- venue-specific submission metadata;
- final author, funding, acknowledgement, and license decisions.

## Claim Boundary

Current supported wording:

- grouped-validation battery-degradation benchmark;
- diagnostic scalar PULSE and EIS endpoints;
- C-rate as the hardest capacity generalization view;
- diagnostic 80% capacity-relative threshold-event forecasting beyond
  proximity baselines.
- negative Milestone 9 neural sequence architecture gate evidence that keeps
  neural sequence and CBAT readiness blocked.

Current closed wording:

- CBAT architecture release;
- neural or sequence model readiness;
- DRT or learned EIS embedding claims;
- policy ranking;
- detector-knee prediction;
- risk-score calibration claims;
- causal or same-cell counterfactual claims;
- broad multimodal degradation claims.

## Recommended Review Order

1. Read `README.md` for project orientation.
2. Read `docs/BENCHMARK_V0_1_RC2_SUMMARY.md` for release scope.
3. Read `docs/POST_M9_REVIEW_CHECKLIST.md` for the post-Milestone-9 review path.
4. Read `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` for allowed wording.
5. Read `manuscript/manuscript_v0_7.md` for the paper narrative.
6. Use `manuscript/manuscript_v0_7_traceability.md` to audit claims.
7. Use `manuscript/submission_readiness_v0_9.md` before venue formatting.

## Validation Commands

```bash
mbp report check-release-candidate
mbp report check-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md
mbp report check-reader-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md
```

Use `.venv/bin/` prefixes if running inside the project virtual environment.
