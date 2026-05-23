# PULSE Missingness Interpretation

Canonical RT/50 target missingness remains a reporting limitation, not a hard blocker for scalar diagnostics.

Missing endpoint rows: `76`
Parameter-set condition groups with missingness: `34`

## Split Overlap

| Grouping | Value | Missing rows | Missing cells | Missing parameter sets |
|---|---:|---:|---:|---:|
| `c_rate_holdout_fold` | `0` | 62 | 61 | 28 |
| `c_rate_holdout_fold` | `1` | 14 | 14 | 6 |
| `profile_holdout_fold` | `0` | 57 | 57 | 26 |
| `profile_holdout_fold` | `1` | 19 | 18 | 8 |

## Check-Up Missingness

| checkup_k | Missing rows |
|---:|---:|
| 1 | 1 |
| 3 | 3 |
| 4 | 9 |
| 5 | 5 |
| 6 | 6 |
| 7 | 2 |
| 8 | 1 |
| 9 | 1 |
| 10 | 5 |
| 11 | 7 |
| 12 | 1 |
| 13 | 5 |
| 14 | 3 |
| 15 | 8 |
| 16 | 1 |
| 17 | 1 |
| 18 | 2 |
| 19 | 2 |
| 20 | 1 |
| 21 | 2 |
| 22 | 2 |
| 23 | 2 |
| 24 | 2 |
| 25 | 1 |
| 26 | 2 |
| 27 | 1 |

Decision: missingness overlaps C-rate and profile holdouts but does not remove those views. It must be reported with PULSE claim-readiness artifacts.
