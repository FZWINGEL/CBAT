# Results: PULSE QA And Resistance Baseline v0

PULSE was opened as a QA-first scalar resistance endpoint after the LOG_AGE-only
C-rate delta path failed to beat the F4 threshold. The canonical target policy
uses RT/50 `delta_pulse_1s_resistance` as the first transition target and
RT/50 `delta_pulse_10ms_resistance` as a secondary diagnostic target.

PULSE target robustness checks support the canonical RT/50 endpoint for scalar
diagnostics. Alignment sensitivity, direction handling, and missingness remain
part of the reporting package. The current RT/50 `mean` extraction is
effectively charge-direction for adjacent interval deltas because finite
discharge adjacent deltas are unavailable.

Target robustness results:

| Target | C-rate best MAE | Condition-fold best MAE | Interpretation |
|---|---:|---:|---|
| `delta_pulse_1s_resistance` | `0.00185842` | `0.000960407` | canonical transition target |
| `delta_pulse_10ms_resistance` | `0.00180642` | `0.000910676` | viable secondary diagnostic |
| `pulse_1s_resistance_k1` | `0.00189616` | `0.00104973` | state-tracking target |
| `pulse_10ms_resistance_k1` | `0.00179792` | `0.00105917` | state-tracking target |

Allowed claims:

- C04: canonical RT/50 PULSE is robust enough for scalar resistance-baseline
  diagnostics.
- PULSE resistance is predictable enough for scalar baseline diagnostics.

Blocked claims:

- PULSE target robustness proves broad capacity+PULSE multimodal modeling.
- Direction-specific claims from discharge RT/50 adjacent deltas.

Source artifacts:

- `docs/PULSE_TARGET_POLICY.md`
- `docs/experiments/2026-05-23_pulse_target_robustness_decision.md`
- `reports/baselines/pulse_resistance_target_robustness/plots/pulse_target_comparison.csv`
- `reports/baselines/pulse_resistance_l0_l3/pulse_claim_readiness.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`

Figure/table references:

- Figure 6: PULSE QA and coverage.
- Figure 7: PULSE resistance baseline.

Limitations:

- Alignment deltas and missing canonical endpoints must remain disclosed.
- RT/50 `mean` is effectively charge in the current adjacent-delta extraction.
