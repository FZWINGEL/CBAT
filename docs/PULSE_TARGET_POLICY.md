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
aggregates duplicate rows for the same `(cell_id, checkup_k, SOC, temperature)`
context by arithmetic mean across represented directions/duplicates. Directional
claims require a later direction-specific policy.

## Alignment Policy

PULSE rows are aligned to check-ups by the parser-reported `checkup_k` and
`alignment_delta_s`. QA must report alignment method counts and alignment delta
min, median, p95, and max. Rows with large alignment deltas are warnings, not
silent exclusions, until the PULSE QA report defines whether they affect the
canonical target.

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
