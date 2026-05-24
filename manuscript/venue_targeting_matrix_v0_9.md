# Venue Targeting Matrix v0.9

This matrix is for choosing a target venue. It does not select a venue by
itself and does not change the manuscript claims.

| Venue family | Fit | Risks | Recommended framing |
|---|---|---|---|
| Battery data descriptor or data-methods venue | strong | May require more formal dataset provenance, licensing, and reuse metadata. | Lead with reproducible benchmark data products, grouped validation, and release package. |
| Battery degradation or electrochemistry methods venue | moderate to strong | May expect deeper mechanistic interpretation than this benchmark supports. | Emphasize empirical gates, diagnostic endpoints, and avoided mechanistic overreach. |
| Machine-learning benchmark venue | moderate | May expect broader cross-dataset comparison or stronger modeling novelty. | Frame as condition-generalization benchmark with negative-result gates and release checks. |
| Scientific software or reproducibility venue | moderate | May expect clearer install/reproduce ergonomics and metadata finalization. | Lead with command DAG, artifact manifest, release checker, and manuscript traceability. |
| Architecture-focused ML venue | weak | Current evidence blocks CBAT, sequence/neural, and broad multimodal claims. | Do not target unless the scope is explicitly benchmark-first and architecture-free. |
| Policy or operational decision venue | weak | Policy ranking and causal claims remain closed. | Do not target for current package. |

## Recommended Default

Prioritize a benchmark/data-methods or battery-methods venue. The strongest
story is a reproducible grouped-validation battery-degradation benchmark with
diagnostic PULSE/EIS endpoints, explicit negative-result gates, and a bounded
threshold-event forecasting diagnostic.

## Venue-Selection Questions For Humans

- Should the manuscript be judged primarily as a benchmark/data product or as a
  battery-aging methods paper?
- Are raw data access and license terms acceptable for the target venue?
- How many figures and tables are allowed in the main text?
- Does the venue require a formal data descriptor, software descriptor, or
  reporting checklist?
- Does the venue permit a prerelease GitHub tag as the code availability anchor,
  or is an archived DOI required?

## Claims To Keep Closed During Venue Targeting

- CBAT architecture readiness;
- neural or sequence model readiness;
- policy ranking;
- detector-knee prediction;
- risk-score calibration readiness;
- causal or same-cell counterfactual conclusions;
- broad multimodal degradation claims.
