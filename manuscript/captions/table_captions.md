# Table Captions

## Table 1. Dataset audit summary

Claim IDs: C12. Source artifact: `docs/REPO_STATUS.md`. Allowed interpretation: the benchmark uses a fixed audited cohort and interval population. Limitation: large generated data products remain ignored local artifacts.

## Table 2. Model ladder summary

Claim IDs: C01, C02, C03, C04, C06, C07, C08. Source artifact: `reports/synthesis/model_ladder_summary.csv`. Allowed interpretation: the ladder summarizes major baseline stages. Limitation: best-row metrics are descriptive and claim support follows paired tests.

## Table 3. Split difficulty summary

Claim IDs: C03. Source artifact: `reports/synthesis/split_difficulty_summary.csv`. Allowed interpretation: split views have different difficulty profiles. Limitation: descriptive best rows do not authorize unsupported claims.

## Table 4. Claim matrix

Claim IDs: C01-C12. Source artifact: `reports/synthesis/claim_matrix.csv`. Allowed interpretation: paper claims are status-gated. Limitation: claim wording must still be checked in prose.

## Table 5. Negative results

Claim IDs: C02, C07, C08, C09, C10, C11. Source artifact: `reports/synthesis/negative_results.md`. Allowed interpretation: negative results are part of the benchmark contribution. Limitation: they do not rule out future gated modalities.

## Table 6. Main project gate status

Claim IDs: C01-C19. Source artifact: `reports/synthesis/main_project_gate_status.md`. Allowed interpretation: the benchmark gates separate supported, diagnostic, negative, and blocked claims. Limitation: gate status summarizes the tracked reports and does not replace source artifacts.

## Table 7. Threshold-warning hardening summary

Claim IDs: C18, C19. Source artifact: `reports/baselines/threshold_warning_censoring_sensitivity/censoring_sensitivity_summary.md`. Allowed interpretation: 80% threshold-event forecasting remains diagnostic after verified-only censoring sensitivity. Limitation: probability calibration and policy use remain outside the claim.

## Table 8. Release-candidate artifact summary

Claim IDs: C11, C12, C19. Source artifact: `reports/synthesis/artifact_manifest_v2.csv`; `reports/synthesis/release_candidate_check.md`. Allowed interpretation: the benchmark release package is reproducible and claim bounded. Limitation: the source archive excludes raw data and generated Parquets.
