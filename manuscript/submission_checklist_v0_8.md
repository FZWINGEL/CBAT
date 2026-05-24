# Submission Checklist v0.8

This checklist is venue-neutral. Complete it before applying target-venue
formatting.

| Check | Status | Evidence |
|---|---|---|
| Main manuscript exists | pass | `manuscript/manuscript_v0_7.md` |
| Supplement exists | pass | `manuscript/supplement_v0_7.md` |
| Traceability sidecar exists | pass | `manuscript/manuscript_v0_7_traceability.md` |
| Reviewer-risk register exists | pass | `reports/synthesis/reviewer_risk_register_v2.md` |
| Reviewer response prep exists | pass | `manuscript/reviewer_response_prep_v2.md` |
| Release anchor exists | pass | `benchmark-v0.1-rc2`; `docs/RELEASE_NOTES_v0.1-rc2.md` |
| Claim ledger v2 exists | pass | `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md` |
| Claim matrix v2 exists | pass | `reports/synthesis/main_project_claim_matrix_v2.csv` |
| Artifact manifest exists | pass | `reports/synthesis/artifact_manifest_v2.csv` |
| Runbook exists | pass | `docs/BENCHMARK_RUNBOOK.md` |
| Command DAG exists | pass | `docs/COMMAND_DAG.md` |
| Title/abstract options exist | pass | `manuscript/title_abstract_options_v0_8.md` |
| Cover-letter draft exists | pass | `manuscript/cover_letter_draft_v0_8.md` |
| Data/code availability wording exists | pass | `manuscript/data_code_availability_v0_8.md` |
| Figure/table inventory exists | pass | `manuscript/figure_table_inventory_v0_8.md` |

## Required Validation Commands

Run before venue-specific formatting or submission packaging:

```bash
mbp report check-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md

mbp report check-reader-manuscript \
  --manuscript manuscript/manuscript_v0_7.md \
  --claim-ledger docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md \
  --traceability manuscript/manuscript_v0_7_traceability.md

mbp report check-release-candidate

git diff --check

git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

Use `.venv/bin/` prefixes when running inside the project virtual environment.

## Human Review Checklist

- Confirm target venue scope fits a benchmark/data-methods contribution.
- Confirm raw data redistribution terms before any public submission package.
- Confirm figure count and supplement split after venue selection.
- Confirm author list, acknowledgements, funding, and competing-interest text.
- Confirm all threshold-warning wording remains diagnostic, not causal.
- Confirm detector-knee prediction, policy ranking, sequence/neural models,
  CBAT, and risk-score calibration claims remain closed.

## Stop Conditions

Stop and revise before submission if:

- a blocked claim is stated as supported;
- a generated Parquet or raw data artifact is staged;
- a reviewer-facing file implies architecture readiness;
- a claim lacks a source artifact in the traceability sidecar;
- the release checker fails.
