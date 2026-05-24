# Repository Metadata Checklist

This checklist records human decisions still needed before a final public
release or venue-specific submission package. Do not guess these values.

| Metadata item | Current status | Required human decision |
|---|---|---|
| License for repository code | open | Choose and add a repository code license. |
| Dataset license wording | source known | Confirm wording for the Luh-Blank dataset citation and terms. |
| Citation metadata | open | Add `CITATION.cff` only after title, author list, and release identity are final. |
| DOI/archive | open | Decide whether to archive the benchmark release on Zenodo or another service. |
| Final author list | open | Confirm author names, order, affiliations, and ORCID IDs. |
| Funding statement | open | Provide funder names and grant numbers. |
| Acknowledgements | open | Provide acknowledgement text. |
| Competing interests | open | Provide declaration text. |
| Data availability | drafted | Review `manuscript/data_code_availability_v0_8.md` against venue policy. |
| Code availability | drafted | Review release URL and tag wording after final release decision. |
| Target venue | open | Select target venue before final formatting. |
| Figure/table limits | open | Apply venue-specific limits after target venue selection. |
| Supplement rules | open | Adapt `manuscript/supplement_v0_7.md` to target venue. |

## Current Defaults

- Public benchmark anchor: `benchmark-v0.1-rc2`.
- Manuscript anchor: `manuscript/manuscript_v0_7.md`.
- Submission bundle anchor: `manuscript/submission_bundle_v0_8.md`.
- No raw data or generated Parquets are redistributed.
- No new scientific claims should be added during metadata cleanup.

## Stop Conditions

Do not add final repository metadata if:

- the license choice is unknown;
- author or affiliation details are incomplete;
- a DOI/archive service has not been selected;
- a target venue has different data/code availability wording requirements;
- adding metadata would imply a claim beyond `docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md`.
