# GitHub Issue Plan

Milestone: `0.1 - Dataset Audit CLI`

Done means:

```bash
uv run mbp audit inventory --data-root D:/battery_data/luh_blank --out reports/audit/file_inventory.parquet
uv run mbp audit manifest --data-root D:/battery_data/luh_blank --out data/manifests/DATASET_MANIFEST.json \
  --coverage-out reports/audit/modality_coverage.csv \
  --known-issues-out reports/audit/known_issues.csv \
  --evidence-memo-out reports/audit/dataset_evidence_memo.md
uv run pytest
```

Expected outputs:

```text
data/manifests/DATASET_MANIFEST.json
data/manifests/MANIFEST.sha256
reports/audit/file_inventory.parquet
reports/audit/modality_coverage.csv
reports/audit/known_issues.csv
reports/audit/dataset_evidence_memo.md
```

## Initial Issues

| Issue | Title | Acceptance criterion |
|---:|---|---|
| 1 | Repo bootstrap | `uv run pytest` passes; CLI exists. |
| 2 | Add project governance docs | Charter, assumption register, decision log, known issues, evidence memo template exist. |
| 3 | Implement file inventory | Recursively inventories files with size, suffix, path, modified time, and SHA-256. |
| 4 | Implement manifest generator | Writes `DATASET_MANIFEST.json` and `MANIFEST.sha256`. |
| 5 | Dataset family detector | Detects EOC/EIS/PULSE/LOG/LOG_AGE/CFG-like files by path/name/schema. |
| 6 | Modality coverage audit | Summarizes cell IDs, parameter sets, and modality availability. |
| 7 | Known issue checks | Checks EIS coverage, LOG gaps placeholder, PULSE provenance placeholder, version/source metadata. |
| 8 | Evidence memo auto-report | Generates Markdown summary from manifest and audit outputs. |

## `gh` Commands

Run these from an initialized repository after `gh auth status` succeeds:

```bash
gh repo create multimodal-battery-prediction --private --source=. --remote=origin --push
gh api repos/:owner/:repo/milestones -f title='0.1 - Dataset Audit CLI' -f description='Gate 1 dataset audit CLI, manifest, modality coverage, known issue checks, and evidence memo.'

gh issue create --title 'Repo bootstrap' --body 'Acceptance: uv run pytest passes; CLI exists.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Add project governance docs' --body 'Acceptance: Charter, assumption register, decision log, known issues, evidence memo template exist.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Implement file inventory' --body 'Acceptance: Recursively inventories files with size, suffix, path, modified time, and SHA-256.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Implement manifest generator' --body 'Acceptance: Writes DATASET_MANIFEST.json and MANIFEST.sha256.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Dataset family detector' --body 'Acceptance: Detects EOC/EIS/PULSE/LOG/LOG_AGE/CFG-like files by path/name/schema.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Modality coverage audit' --body 'Acceptance: Summarizes cell IDs, parameter sets, and modality availability.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Known issue checks' --body 'Acceptance: Checks EIS coverage, LOG gaps placeholder, PULSE provenance placeholder, version/source metadata.' --milestone '0.1 - Dataset Audit CLI'
gh issue create --title 'Evidence memo auto-report' --body 'Acceptance: Generates Markdown summary from manifest and audit outputs.' --milestone '0.1 - Dataset Audit CLI'
```

