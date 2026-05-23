# Figure 02: Grouped Validation Design

Claim supported: C12 grouped validation discipline.

Source artifacts:

- `docs/VALIDATION_PROTOCOL.md`
- `reports/audit/split_registry_report.json`

Intended plot type: split schematic and condition grouping diagram.

Key content:

- 228 cells as 76 parameter-set condition triplets;
- condition fold;
- temperature holdout;
- C-rate holdout;
- profile holdout;
- voltage-window holdout;
- random row/cell splits excluded from headline evidence.

Risk/limitation:

- C-rate and profile held-out views have fewer parameter-set conditions than the
  full condition fold.

Caption draft:

> Grouped validation protocol. Replicate cells from the same parameter-set
> condition remain grouped for headline claims, and stressor-axis holdouts test
> operating-regime transfer rather than random row interpolation.
