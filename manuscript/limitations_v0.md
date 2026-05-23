# Limitations v0

The benchmark is deliberately conservative. Its limitations should appear in
the abstract, discussion, and figure captions where relevant.

## C-Rate Condition Count

C-rate holdout is central to the story, but several C-rate analyses use only 12
held-out parameter-set conditions and 143 PULSE-covered C-rate intervals. Claims
therefore need condition-level aggregation, bootstrap intervals where available,
and cautious wording.

## PULSE Alignment And Direction Policy

PULSE alignment sensitivity is quantified, but alignment remains a reporting
sensitivity rather than a perfect temporal guarantee. The current RT/50 `mean`
target is effectively charge-direction for adjacent interval deltas because
finite discharge adjacent deltas are unavailable.

## LOG_AGE And PULSE Leakage Risk

The repo explicitly masks inserted LOG_AGE diagnostics, excludes target-derived
stress rates from predictive feature groups, and forbids future PULSE state or
PULSE deltas as capacity inputs. The manuscript must keep diagnostic variables
separate from predictive features.

## Fade-Rate Prediction

The benchmark has stronger evidence for capacity level than for
`delta_capacity_Ah`. LOG_AGE stress features, normalized rate targets, residual
correction, and prior PULSE do not solve C-rate fade prediction.

## Quantile Calibration

HGB quantile outputs are not calibrated. The paper can report quantile
diagnostics only if it labels them as uncalibrated.

## EIS And CBAT

EIS is not tested as a predictive modality in the current evidence set. CBAT,
neural/sequence models, and policy ranking remain blocked.

## Counterfactual And Causal Limits

The benchmark is based on grouped observational experimental conditions, not
same-cell counterfactual interventions. PULSE growth correlations are
explanatory diagnostics, not causal proof.

Source artifacts:

- `reports/synthesis/reviewer_risk_register.md`
- `docs/PAPER_CLAIM_LEDGER.md`
- `docs/VALIDATION_PROTOCOL.md`

Forbidden wording:

- "validated calibrated intervals";
- "EIS has demonstrated predictive benefit";
- "PULSE supports fade-rate prediction";
- "CBAT has been validated";
- "same-cell counterfactual".
