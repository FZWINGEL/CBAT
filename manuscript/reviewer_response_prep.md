# Reviewer Response Prep

This file converts `reports/synthesis/reviewer_risk_register.md` into draft
response strategies.

## Grouped Splits Versus Random Splits

Likely criticism: Random split performance is missing or not emphasized.

Response strategy: The experimental unit for generalization is the
parameter-set condition, not an individual row. The 228 cells represent 76
conditions with three replicates. Random row/cell splits can share condition
structure across train and test and are therefore leakage smoke tests rather
than publishable headline evidence.

Artifact to cite: `docs/VALIDATION_PROTOCOL.md`.

Remaining limitation: The paper should clearly state that this makes the
benchmark stricter and may reduce apparent performance.

## Small C-Rate Condition Count

Likely criticism: C-rate claims rely on too few held-out conditions.

Response strategy: Keep C-rate claims narrow. C-rate is identified as the
hardest observed split and as a failure mode, not as a solved regime. Paired
bootstrap summaries are used where available, and fade-rate claims remain
blocked.

Artifact to cite: `docs/experiments/2026-05-23_prior_pulse_vs_best_nonpulse.md`.

Remaining limitation: C-rate condition-level analyses remain limited by the
available dataset design.

## PULSE Alignment Deltas

Likely criticism: PULSE/check-up alignment deltas may undermine the resistance
target.

Response strategy: Present alignment as a sensitivity, not a hidden assumption.
The 24h threshold retains all C-rate rows and all 76 parameter sets, but
alignment remains a reported limitation.

Artifact to cite: `docs/experiments/2026-05-23_pulse_alignment_direction_hardening.md`.

Remaining limitation: Alignment sensitivity does not prove perfect temporal
alignment.

## PULSE Direction Handling

Likely criticism: Mean direction handling could hide charge/discharge effects.

Response strategy: State that current RT/50 `mean` is effectively charge for
adjacent deltas because finite discharge adjacent deltas are unavailable.
Direction-specific claims are blocked.

Artifact to cite: `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`.

Remaining limitation: No discharge RT/50 adjacent-delta result is claimed.

## LOG_AGE Leakage Risk

Likely criticism: LOG_AGE contains inserted diagnostics or target-derived
features.

Response strategy: Explain the leakage policy: inserted diagnostics are masked,
target-derived stress rates are diagnostic only, and future PULSE state/deltas
are forbidden as capacity inputs.

Artifact to cite: `docs/VALIDATION_PROTOCOL.md`.

Remaining limitation: The manuscript must label diagnostic columns and
predictive features separately.

## Prior PULSE Not Beating Strongest Non-PULSE

Likely criticism: Prior PULSE gains over F4 are not enough.

Response strategy: Agree and frame it as the benchmark boundary. Prior PULSE
improves `capacity_Ah_k1` over F4 in selected splits but does not beat the
strongest supplied non-PULSE baselines.

Artifact to cite:
`reports/baselines/capacity_prior_pulse_vs_best_nonpulse/prior_pulse_vs_best_nonpulse_claim_readiness.md`.

Remaining limitation: No broad prior-PULSE predictive claim is made.

## Prior PULSE Fade-Rate Failure

Likely criticism: Prior PULSE does not improve `delta_capacity_Ah`.

Response strategy: Treat this as a core negative result. The paper separates
capacity level from fade-rate prediction and blocks the fade-rate claim.

Artifact to cite: `docs/PAPER_CLAIM_LEDGER.md`.

Remaining limitation: C-rate fade prediction remains unresolved.

## Quantile HGB Calibration

Likely criticism: Quantile intervals are under-covered.

Response strategy: Do not claim validated calibrated intervals. Report q10-q90
coverage as a diagnostic only.

Artifact to cite: `reports/baselines/capacity_hgb50_focused/claim_readiness.md`.

Remaining limitation: A future calibration milestone is needed for uncertainty
claims.

## EIS Not Tested

Likely criticism: EIS appears in the project scope but not the current results.

Response strategy: State that EIS is a gated future modality. The current paper
is a benchmark and PULSE/LOG_AGE evidence paper, not an EIS modeling paper.

Artifact to cite: `docs/REPO_STATUS.md`.

Remaining limitation: Title and abstract must avoid implying EIS performance.

## No Same-Cell Counterfactuals

Likely criticism: Policy or causal conclusions are not supported.

Response strategy: Agree. The paper reports grouped predictive and diagnostic
evidence, not same-cell counterfactual policy response.

Artifact to cite: `docs/PROJECT_CHARTER.md`.

Remaining limitation: Policy ranking remains blocked.
