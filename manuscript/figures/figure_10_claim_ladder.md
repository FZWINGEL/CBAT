# Figure 10: Claim Ladder

Claim supported: all claim-ledger statuses.

Source artifacts:

- `reports/synthesis/claim_matrix.csv`
- `docs/PAPER_CLAIM_LEDGER.md`
- `reports/synthesis/negative_results.md`

Intended plot type: claim-status ladder or matrix with status colors.

Key content:

- supported;
- supported for diagnostics;
- supported for explanatory diagnostics;
- partially supported;
- not supported;
- gated;
- blocked.

Risk/limitation:

- Status labels must not imply stronger claims than the ledger allows.

Caption draft:

> Paper claim ladder. The benchmark explicitly separates supported, diagnostic,
> partial, negative, gated, and blocked claims so that operating-history and
> PULSE signals are reported without architecture or multimodal overclaims.
