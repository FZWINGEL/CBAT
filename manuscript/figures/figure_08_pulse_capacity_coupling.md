# Figure 08: Capacity Residual Versus PULSE Growth

Claim supported: C05 PULSE growth as explanatory diagnostic.

Source artifacts:

- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1/plots/*.csv`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah/plots/*.csv`
- `reports/coupling/pulse_capacity_robustness/capacity_Ah_k1_c_rate/plots/*.csv`
- `reports/coupling/pulse_capacity_robustness/delta_capacity_Ah_c_rate/plots/*.csv`

Intended plot type: scatter or binned residual plot, with C-rate subgroup
highlighted.

Key numbers:

- C-rate `capacity_Ah_k1` interval Pearson: `0.857653`.
- C-rate `delta_capacity_Ah` interval Pearson: `0.647125`.

Risk/limitation:

- Correlation is explanatory, not causal; residualization weakens global
  associations.

Caption draft:

> Capacity residuals and PULSE growth. PULSE resistance growth is associated
> with capacity-model residual magnitude, especially under C-rate holdout, but
> the association is diagnostic rather than causal.
