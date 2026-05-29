# 2026-05-29 Repository Cleanup

## Scope

A conservative repository-hygiene pass after the Milestone 9 neural-sequence
architecture gate. It removed disposable cruft, archived a small set of
superseded planning and release-candidate-1 documents, and added navigation
indexes. It did **not** run modeling, regenerate data products, or touch the
scientific record (experiment logs, claim ledgers, the manuscript and its
drafts, or any `reports/` evidence).

This follows the conservative policy established in
[2026-05-22_repo_cleanup.md](2026-05-22_repo_cleanup.md): remove caches and
empty local byproducts, keep reproducibility and record artifacts, and document
any cleanup that affects workflow state here under `docs/experiments/`.

## Removed (disposable cruft)

- Empty placeholder packages, unused and unimported since the Gate-1 bootstrap:
  `src/mbp/config/`, `src/mbp/features/`, `src/mbp/utils/`, `src/mbp/validation/`
  (each contained only a one-line docstring `__init__.py`).
- Empty notebook stub `notebooks/00_dataset_audit_preview.ipynb` (zero cells),
  and the then-empty `notebooks/` directory.
- Empty local tooling directories `.agents/` and `.codex/` (untracked).
- Local caches `.pytest_cache/`, `.ruff_cache/`, and `__pycache__/`
  (git-ignored; local only).

These remain recoverable from git history.

## Archived to `docs/archive/` (superseded, non-load-bearing)

Moved with `git mv` (fully reversible) and de-referenced from the canonical docs:

- `GITHUB_ISSUE_PLAN.md` — completed Milestone 0.1 issue bootstrap checklist; no
  remaining references.
- `PAPER_SKELETON.md`, `MANUSCRIPT_PACKAGE_PLAN.md` — Milestone 1.0/1.0.1
  pre-manuscript planning artifacts, superseded by the v0.7 manuscript and the
  v0.8 submission bundle.
- `BENCHMARK_V0_1_RC1_SUMMARY.md`, `GITHUB_RELEASE_DRAFT_v0.1-rc1.md` — RC1
  release-candidate handoff artifacts, superseded by the RC2 equivalents.

Path references to these five files were updated in `docs/PROJECT_CHARTER.md`,
`docs/REPO_STATUS.md`, and `docs/VALIDATION_PROTOCOL.md` to point at
`docs/archive/`. References inside historical experiment logs were intentionally
left unchanged (they are part of the record).

## Intentionally kept (looked stale, but load-bearing)

- `docs/PAPER_CLAIM_LEDGER.md` and `docs/PAPER_FIGURE_PLAN.md` — referenced in
  code (`src/mbp/reporting/manuscript_tables.py`, `manuscript_figures.py`) as
  the manuscript claim-ledger default and figure/table source artifacts.
- `docs/RELEASE_NOTES_v0.1-rc1.md` and `docs/CODEX_NEXT_WORK.md` — required by
  the release-candidate validator (`src/mbp/reporting/release_checks.py`).
- All `docs/experiments/` gate logs, all claim ledgers, the full `manuscript/`
  version trail and traceability sidecars, and all `reports/` evidence.

## Added (navigation; additive, no record changes)

- `docs/README.md` — top-level map of the documentation set.
- `docs/experiments/README.md` — chronological index of the milestone-gate
  provenance trail.
- `docs/archive/README.md` — note on what is archived and why.

## Validation

Run in no-cache mode so the hygiene scan stays clean:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/ruff check . --no-cache
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -p no:cacheprovider -q
.venv/bin/mbp report check-release-candidate
```

Result:

- Ruff: passed.
- Pytest: `284 passed`.
- Release-candidate check: passed.

## Decision

Keep the repository-cleanup policy conservative: remove caches and empty local
byproducts, archive (do not delete) superseded planning/release drafts, never
touch the scientific record, and document the cleanup here.
