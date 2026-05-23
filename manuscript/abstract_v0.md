# Abstract v0

Battery degradation models are often evaluated under splits that are easier
than the operating-regime shifts they are intended to support. We build a
reproducible grouped-validation benchmark for battery degradation prediction
from operating histories, capacity check-ups, and pulse resistance using the
Luh-Blank aging dataset. The benchmark links result-data products, LOG_AGE
operating histories, interval tables, stress-feature sidecars, split registries,
and RT/50 PULSE resistance targets across 228 cells organized as 76
parameter-set conditions with three replicates each.

Under condition-level and stressor-axis holdouts, scalar HGB baselines show that
C-rate transfer is the dominant unresolved capacity generalization setting.
Current scalar LOG_AGE summaries and stress features help in some grouped views,
especially for nonlinear models, but they do not solve C-rate
`delta_capacity_Ah` prediction. Canonical RT/50 PULSE is robust enough for
scalar resistance-baseline diagnostics, and PULSE growth is associated with
capacity-model residual magnitude, especially under C-rate holdout. Prior PULSE
state improves `capacity_Ah_k1` over an F4 LOG_AGE scalar baseline in selected
grouped splits, but it does not beat the strongest supplied non-PULSE baselines
and does not improve `delta_capacity_Ah`.

The result is a claim-bounded benchmark and evidence ledger. It supports
grouped validation, scalar diagnostic, and negative-result claims, while keeping
EIS predictive value, neural/sequence models, policy ranking, and CBAT as gated
future work.

Claim IDs: C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12.
