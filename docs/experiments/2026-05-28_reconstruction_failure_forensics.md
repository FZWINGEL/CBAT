# Milestone 8.8: Reconstruction Failure Forensics and C-Rate Branch Closure

## Question

Milestone 8.7 showed that `capacity_Ah_k + predicted_delta_capacity_Ah`
improves the C-rate `capacity_Ah_k1` row, but it still fails outside-split
non-degradation. This follow-up asks whether that failure is a narrow artifact
or broad enough to close the capacity-level C-rate repair branch.

This is report-only forensics over existing prediction artifacts. No models are
trained, no features are added, and the 5% outside-split guardrail is unchanged.

## Command

```bash
mbp analysis diagnose-reconstruction-failure \
  --reconstruction-report reports/analysis/target_consistency_reconstruction/target_consistency_reconstruction_report.json \
  --reconstruction-dir reports/analysis/target_consistency_reconstruction \
  --interval-table data/interim/interval_table.parquet \
  --support-overlap reports/analysis/c_rate_generalization/c_rate_support_overlap.csv \
  --out-dir reports/analysis/reconstruction_failure_forensics
```

## Outputs

- `reports/analysis/reconstruction_failure_forensics/reconstruction_failure_report.json`
- `reports/analysis/reconstruction_failure_forensics/reconstruction_failure_decision.md`
- `reports/analysis/reconstruction_failure_forensics/reconstruction_failure_claim_readiness.md`
- `reports/analysis/reconstruction_failure_forensics/plots/outside_failure_by_split.csv`
- `reports/analysis/reconstruction_failure_forensics/plots/failing_condition_hotspots.csv`
- `reports/analysis/reconstruction_failure_forensics/plots/path_error_decomposition.csv`

## Result

The failure is not narrow enough to reopen the capacity-level repair branch.
Two outside-split direct-reference reconstruction comparisons fail:

| Method | Split | Reference | Relative degradation |
|---|---|---|---:|
| `targeted_router_D2_F4` | `profile_holdout_fold` | direct F4 capacity | `0.293828` |
| `adaptive_R2_F8_conservative` | `voltage_window_holdout_fold` | direct F4 capacity | `0.344864` |

The report identifies 88 condition-hotspot rows and 58 degrading hotspot rows.
QA flags and LOG_AGE monotonicity flags appear in many hotspots, so they are
useful context, but this gate does not show a single narrow data artifact that
can waive the failed guardrail. Support-overlap evidence is also not available
for enough outside-split hotspots to explain the failure as a support-only
issue.

## Interpretation

The C-rate row itself remains informative: capacity-from-delta improves the
hard C-rate capacity view. But that improvement does not transfer safely across
the non-C-rate held-out views. The main failure modes are:

- profile holdout for the targeted router;
- voltage-window holdout when comparing the adaptive capacity-from-delta path
  against direct F4 capacity;
- many condition-level degrading hotspots rather than one isolated condition.

Therefore the current branch cannot support capacity-level or two-target
C-rate repair wording.

## Claim Readiness

| Claim area | Status |
|---|---|
| outside-split failure attribution | `supported_for_diagnostics` |
| narrow QA artifact explanation | `diagnostic_only` |
| support-limited explanation | `not_supported` |
| capacity-level reconstruction branch | `blocked` |
| architecture, policy, calibration, sequence, neural, and causality | `blocked` |

## Decision

Close the current capacity-level reconstruction repair branch for the present
evidence. Keep only the narrow diagnostic `delta_capacity_Ah` C-rate repair
claim.

Still blocked:

- two-target C-rate repair;
- capacity-level C-rate repair;
- broad robust capacity;
- solved C-rate fade;
- CBAT or multimodal architecture work;
- neural or sequence model claims;
- policy ranking;
- calibrated risk or uncertainty;
- causal or same-cell counterfactual claims.
