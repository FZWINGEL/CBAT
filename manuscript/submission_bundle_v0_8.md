# Submission Bundle v0.8

This is a venue-neutral handoff bundle for the current manuscript package. It
does not replace `manuscript/manuscript_v0_7.md`; it points a human reviewer,
coauthor, or venue-specific formatter to the files needed to inspect and adapt
the package.

## Release And Manuscript Anchors

| Item | Path or tag | Purpose |
|---|---|---|
| Benchmark release tag | `benchmark-v0.1-rc2` | Reviewer-facing source archive with release-polish docs. |
| Release notes | `docs/RELEASE_NOTES_v0.1-rc2.md` | External release description and limitations. |
| Main manuscript | `manuscript/manuscript_v0_7.md` | Current venue-neutral manuscript draft. |
| Supplement | `manuscript/supplement_v0_7.md` | Current venue-neutral supplementary package. |
| Traceability sidecar | `manuscript/manuscript_v0_7_traceability.md` | Claim-to-source mapping and guarded wording. |
| Reviewer-risk register | `reports/synthesis/reviewer_risk_register_v2.md` | Likely reviewer objections and mitigation evidence. |
| Response preparation | `manuscript/reviewer_response_prep_v2.md` | Draft response language for common objections. |
| Package manifest | `manuscript/manuscript_package_v0_7_manifest.md` | Inventory of the v0.7 manuscript package. |

## Submission-Bundle Files

| File | Use |
|---|---|
| `manuscript/title_abstract_options_v0_8.md` | Venue-neutral title and abstract alternatives. |
| `manuscript/cover_letter_draft_v0_8.md` | Reusable cover-letter draft. |
| `manuscript/data_code_availability_v0_8.md` | Data and code availability wording. |
| `manuscript/figure_table_inventory_v0_8.md` | Figure/table inventory and source mapping. |
| `manuscript/submission_checklist_v0_8.md` | Final handoff checklist before venue formatting. |
| `docs/BENCHMARK_MANUSCRIPT_HANDOFF.md` | External handoff guide for the benchmark and manuscript. |

## Claim Boundary

The bundle preserves the v2 claim ledger. It supports:

- grouped-validation benchmark wording;
- diagnostic PULSE and EIS endpoint wording;
- C-rate as the hardest capacity generalization view;
- a diagnostic 80% capacity-relative threshold-event forecasting result.

It keeps the following closed:

- CBAT architecture;
- neural or sequence models;
- DRT or learned EIS embeddings;
- policy ranking;
- detector-knee prediction;
- risk-score calibration claims;
- causal or same-cell counterfactual claims;
- broad multimodal degradation claims.

## Recommended Handoff Flow

1. Read `docs/BENCHMARK_V0_1_RC2_SUMMARY.md`.
2. Read `manuscript/manuscript_v0_7.md`.
3. Check guarded wording in `manuscript/manuscript_v0_7_traceability.md`.
4. Review `reports/synthesis/reviewer_risk_register_v2.md`.
5. Select a title/abstract option from `manuscript/title_abstract_options_v0_8.md`.
6. Adapt `manuscript/cover_letter_draft_v0_8.md` to the target venue.
7. Run the validation commands listed in `manuscript/submission_checklist_v0_8.md`.

## Package Status

This is a handoff package only. It adds no model training, feature engineering,
data products, raw data, generated Parquets, prediction Parquets, or new
scientific claims.
