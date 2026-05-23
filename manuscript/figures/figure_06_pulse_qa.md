# Figure 06: PULSE QA And Coverage

Claim supported: C04 PULSE RT/50 scalar endpoint.

Source artifacts:

- `reports/audit/pulse_qa_report.json`
- `reports/baselines/pulse_resistance_alignment_robustness.md`
- `reports/baselines/pulse_resistance_l0_l3/pulse_direction_policy_summary.md`

Intended plot type: coverage table plus alignment-threshold retention plot.

Key content:

- canonical RT/50 availability;
- missing canonical endpoint count;
- alignment threshold retention;
- mean equals charge for current RT/50 adjacent deltas;
- discharge adjacent deltas unavailable.

Risk/limitation:

- Alignment and missingness are reporting sensitivities.

Caption draft:

> PULSE target QA. The canonical RT/50 resistance endpoint has sufficient
> coverage for scalar diagnostics, while alignment, missingness, and direction
> policy remain explicit limitations.
