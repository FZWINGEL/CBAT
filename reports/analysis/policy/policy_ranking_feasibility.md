# Observed Policy-Contrast Feasibility

This report evaluates matched observed condition contrasts only. It does not train a model, rank policies, or estimate causal/counterfactual effects.

## Summary

- Contrast rows: 234
- Triplet-supported contrasts: 234
- Observed stability rows: 3213
- Sign-stable rows: 2943

## Family Summary

| Family | Contrasts | Triplet-supported | Stability rows | Sign-stable fraction |
|---|---:|---:|---:|---:|
| charge_c_rate | 36 | 36 | 228 | 0.903509 |
| profile | 12 | 12 | 186 | 0.897849 |
| temperature | 114 | 114 | 1679 | 0.893985 |
| voltage_window | 72 | 72 | 1120 | 0.954464 |

## Interpretation

- Supported wording is limited to observed support and observed degradation-order diagnostics.
- Policy ranking, policy recommendation, same-cell counterfactual, and causal intervention claims remain blocked.
