# Submission Readiness v0.9

This file summarizes what is ready, what needs human input, and what remains
closed before venue-specific submission packaging.

## Ready Now

| Item | Status | Evidence |
|---|---|---|
| Benchmark release anchor | ready | `benchmark-v0.2-rc1` |
| Post-rc2 status addendum | ready | `docs/POST_RC2_MAIN_STATUS.md` |
| Post-M9 review checklist | ready | `docs/POST_M9_REVIEW_CHECKLIST.md` |
| Benchmark task registry v2 | ready | `configs/benchmark_tasks_v2.yaml` |
| Release notes | ready | `docs/RELEASE_NOTES_v0.2-rc1.md` |
| Public README | ready | `README.md` |
| Claim ledger | ready | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Manuscript draft | ready for human review | `manuscript/manuscript_v0_7.md` |
| Supplement draft | ready for human review | `manuscript/supplement_v0_7.md` |
| Submission handoff bundle | ready | `manuscript/submission_bundle_v0_8.md` |
| Title and abstract options | ready for selection | `manuscript/title_abstract_options_v0_8.md` |
| Data/code availability draft | ready for legal and venue review | `manuscript/data_code_availability_v0_8.md` |
| Reviewer-risk prep | ready | `reports/synthesis/reviewer_risk_register_v2.md` |

## Needs Human Input

| Item | Needed decision |
|---|---|
| Target venue | Select venue family and exact target. |
| License | Choose repository code license. |
| Citation metadata | Confirm final title, authors, affiliations, and release identity. |
| DOI/archive | Decide whether to archive the release outside GitHub. |
| Author list | Confirm names, order, affiliations, and ORCID IDs. |
| Funding and acknowledgements | Provide final text. |
| Competing interests | Provide final declaration. |
| Figure/table selection | Trim after venue limits are known. |
| Supplement split | Adapt after venue instructions are known. |

## Closed For Current Submission

- new model training;
- new feature engineering;
- CBAT architecture;
- neural or sequence models beyond completed negative diagnostic gates;
- DRT or learned EIS embeddings;
- policy ranking;
- detector-knee prediction;
- risk-score calibration claims;
- causal or same-cell counterfactual claims;
- broad multimodal degradation claims.

## Pre-Submission Validation

Run these before venue-specific formatting and again before final submission:

```bash
mbp report check-release-candidate
mbp report check-benchmark-tasks \
  --task-registry configs/benchmark_tasks_v2.yaml \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --claim-matrix reports/synthesis/main_project_claim_matrix_v2.csv \
  --artifact-manifest reports/synthesis/artifact_manifest_v2.csv \
  --out reports/synthesis/benchmark_task_registry_check_v2.md \
  --leaderboard-out reports/synthesis/benchmark_leaderboard_v2.csv \
  --task-cards-out reports/synthesis/benchmark_task_cards_v2.md \
  --model-cards-out reports/synthesis/benchmark_model_cards_v2.md
mbp report check-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md
mbp report check-reader-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md
git diff --check
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

Use `.venv/bin/` prefixes when running inside the project virtual environment.

## Recommended Next Human Action

Choose the venue family first. The recommended default is a benchmark/data
methods venue or battery-aging methods venue, not an architecture-first venue.
