# Sequence Value Claim Readiness

| Claim area | Status | Evidence |
|---|---|---|
| Aggregate event features help | `diagnostic_only` | mean gain=-0.000575091; positive rows=13/24. |
| Order-aware features beat aggregate-only | `not_supported` | mean gain=-0.000575091; positive rows=13/24. |
| Order-aware features beat shuffled-order | `not_supported` | mean gain=-0.000564409; positive rows=12/24. |
| Order-aware features improve over stress baseline | `not_supported` | mean gain=-0.000470028; positive rows=8/24. |
| Order-aware features improve C-rate | `not_supported` | mean gain=-0.00131991; positive rows=1/4. |
| Sequence model readiness | `blocked` | Sequence models remain blocked unless order-aware features beat aggregate and shuffled controls under grouped validation. |
