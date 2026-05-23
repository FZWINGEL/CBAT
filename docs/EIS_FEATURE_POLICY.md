# EIS Feature Policy

Milestone 2.0 opens EIS as a gated QA and scalar feature-readiness modality. It does
not authorize EIS predictive modeling, EIS embeddings, DRT features, or claims that
EIS improves capacity, PULSE, calibration, ranking, or degradation prediction.

## Canonical Mask

EIS modeling-frequency rows must satisfy all of the following:

- raw valid flag is true;
- `z_real` and `z_imag` are finite;
- `0.5 Hz <= frequency_Hz <= 5000 Hz`;
- `100 Hz`, `208.3 Hz`, and `14.7 kHz` are excluded.

The mask is audited before any feature table is trusted.

## Feature Tiers

| Tier | Status in Milestone 2.0 | Use |
|---|---|---|
| E0 valid spectra | Required | QA, coverage, alignment, and valid-frequency reports only. |
| E1 selected-frequency features | Required | First simple EIS scalar feature table at selected stable frequencies. |
| E2 R0/R1 | Allowed if provenance and leakage safety are explicit | Low-dimensional diagnostic comparison only. If unavailable or leakage-sensitive, leave null and mark diagnostic. |
| E3 geometric Nyquist features | Required | Fast interpretable scalar EIS features from valid modeling frequencies. |
| E4 DRT | Blocked | Too many regularization and peak-identification choices for the current gate. |
| E5 learned EIS embeddings | Blocked | Too early; no EIS claim or scalar baseline evidence exists yet. |

## Canonical Feature Context

The first feature sidecar uses RT / 50% SOC to match the existing PULSE-first
diagnostic style. If QA shows that RT / 50% SOC is sparse or fragile, a later
policy revision must choose a different canonical context before modeling.

## Selected-Frequency Features

Milestone 2.0 extracts nearest available valid modeling-frequency rows for:

- `0.5 Hz`
- `1 Hz`
- `10 Hz`
- `1 kHz`
- `5 kHz`

For each selected frequency, the sidecar records real impedance, imaginary
impedance, magnitude, phase, and the actual selected frequency.

## R0/R1 Policy

`R0_mOhm_k` and `R1_mOhm_k` remain null in the v1 EIS feature sidecar unless a
source with explicit provenance and leakage safety is available. LOG_AGE-inserted
R0/R1 values are leakage-sensitive and must not be silently merged as predictive
features.

## Claim Gate

No EIS predictive claim is allowed until:

1. EIS QA, coverage, alignment, and valid-frequency reports pass or have explicit
   limitations;
2. an EIS feature table passes schema and feature QA;
3. a later grouped baseline evaluates EIS features against non-EIS baselines; and
4. the result improves a pre-registered non-EIS outcome, calibration metric, or
   ranking claim.

Until then, EIS is a gated data product and diagnostic feature-readiness artifact,
not a validated performance modality.
