# PULSE Target Policy

Policy version: `pulse_target_policy.v1`

## Scope

This policy authorizes PULSE QA, canonical target extraction, and first scalar
resistance baselines only. It does not authorize EIS modeling, EIS embeddings,
knee prediction, sequence models, neural models, policy ranking, CBAT, or
capacity+PULSE multimodal claims.

## Canonical Targets

Canonical first target:

```text
pulse_1s_resistance at RT / 50% SOC
```

Secondary target:

```text
pulse_10ms_resistance at RT / 50% SOC
```

The first baseline target is:

```text
delta_pulse_1s_resistance
```

Secondary targets may be evaluated only after QA confirms canonical coverage:

```text
pulse_1s_resistance_k1
delta_pulse_10ms_resistance
pulse_10ms_resistance_k1
```

## Naming Convention

Interval target columns use:

```text
pulse_1s_resistance_k
pulse_1s_resistance_k1
delta_pulse_1s_resistance
pulse_10ms_resistance_k
pulse_10ms_resistance_k1
delta_pulse_10ms_resistance
```

## Valid Contexts

Allowed SOC contexts are the SOC values represented in the PULSE summary table.
The canonical context is `50% SOC` with tolerance `+/- 0.25` percentage points.

Allowed temperature contexts are represented summary-table contexts. The
canonical context is `RT`. `OT` remains a coverage/audit context until a later
policy expands targets.

Both charge and discharge pulse directions may be present. The canonical target
uses `direction=mean`, which aggregates duplicate rows for the same
`(cell_id, checkup_k, SOC, temperature)` context by arithmetic mean across
represented directions/duplicates. `direction=charge` and
`direction=discharge` target tables are diagnostic only until a later
direction-specific policy is accepted. Directional claims require that later
policy.

## Alignment Policy

PULSE rows are aligned to check-ups by the parser-reported `checkup_k` and
`alignment_delta_s`. QA must report alignment method counts and alignment delta
min, median, p95, and max. Rows with large alignment deltas are warnings, not
silent exclusions, until the PULSE QA report defines whether they affect the
canonical target.

Milestone 0.7.1 alignment-threshold sensitivity may filter baselines with
`--max-alignment-delta-s`. These filtered runs are diagnostics; they do not
change the canonical target unless a later policy version adopts a threshold.

Milestone 0.7.2 direction robustness found that, for the current RT/50 context,
`direction=mean` and `direction=charge` are equivalent in the generated target
tables because finite adjacent RT/50 discharge interval deltas are unavailable.
This does not authorize direction-specific claims; it documents that the current
canonical RT/50 mean target is effectively RT-charge in the available data.

## Missingness Policy

The target table keeps one row per interval and records missing canonical
endpoints in `quality_flags`:

```text
missing_pulse_k
missing_pulse_k1
```

Baselines may train only on rows with finite target values. Target availability
counts must be reported with every PULSE baseline.

## Claim Gate

No scientific PULSE resistance claim is allowed until:

- `mbp pulse qa` has produced PULSE QA, coverage, and alignment reports;
- canonical RT / 50% SOC target coverage is quantified;
- duplicate aggregation is explicit;
- the interval target table is generated and schema-valid;
- grouped baseline reports include target coverage limitations.

Milestone 0.7.2 satisfies the scalar resistance-baseline diagnostic gate for
canonical RT / 50% mean PULSE. This does not authorize a broad PULSE scientific
claim, capacity+PULSE multimodal modeling, policy ranking, CBAT, or architecture
work. It only authorizes controlled scalar coupling diagnostics in later
milestones.
