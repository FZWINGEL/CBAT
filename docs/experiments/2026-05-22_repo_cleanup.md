# 2026-05-22 Repository Cleanup

## Scope

This cleanup pass was limited to repository hygiene after the Milestone 0.5
capacity-baseline smoke work. It did not run modeling or regenerate data
products.

## Checks Performed

Commands inspected:

```bash
git status --short --ignored
git log -3 --oneline
find . -maxdepth 3 \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.ruff_cache' -o -name '*.tmp' -o -name '*.temp' -o -name '*.bak' -o -name '*.pyc' \) -print
du -sh .pytest_cache .ruff_cache src/mbp/**/__pycache__ tests/__pycache__ .antigravitycli .codegraph .venv data/processed
```

Findings before cleanup:

- Git had no tracked or untracked source changes.
- Only ignored local artifacts were present.
- Disposable cache artifacts were present:
  - `.pytest_cache/`
  - `.ruff_cache/`
  - Python `__pycache__/` directories under `src/` and `tests/`
- `.antigravitycli/` was present as an ignored local tooling directory and had
  no files under the inspected depth.
- Large data products and local environment/index artifacts were ignored as
  expected.

## Cleanup Actions

Removed disposable local artifacts:

```bash
rm -rf .pytest_cache .ruff_cache .antigravitycli \
  src/mbp/__pycache__ \
  src/mbp/audit/__pycache__ \
  src/mbp/baselines/__pycache__ \
  src/mbp/data/__pycache__ \
  src/mbp/data/luh_blank/__pycache__ \
  src/mbp/data/products/__pycache__ \
  tests/__pycache__
```

Intentionally preserved:

- `.venv/`: local Python environment.
- `.codegraph/`: local CodeGraph index/database.
- `data/raw/**`: local raw dataset copies.
- `data/interim/**`: local generated interim data products.
- `data/splits/*.parquet`: local generated split registries.
- `data/processed/capacity_l0_smoke_predictions.parquet`: ignored generated
  prediction data from the L0 smoke run.
- ignored Parquet audit details under `reports/audit/`, including the detailed
  LOG_AGE monotonicity report and raw LOG archive inventory.

## Result

After cleanup:

- No disposable Python, pytest, or Ruff caches were found by the cleanup scan.
- `.antigravitycli/` was removed.
- `git status --short --ignored` showed only intentionally ignored local
  environment, CodeGraph, data-product, and generated-audit artifacts.
- No raw, interim, processed, or split Parquet data products were staged or
  committed.

## Validation

Validation was run in no-cache mode so the cleanup scan stayed clean:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/ruff check . --no-cache
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/uv-cache .venv/bin/pytest -p no:cacheprovider
```

Result:

- Ruff: passed.
- Pytest: `69 passed, 1 warning`.
- Warning: existing `datetime.utcnow()` deprecation warning in
  `src/mbp/data/luh_blank/qa_result_data.py`.
- A follow-up cleanup scan found no `__pycache__`, `.pytest_cache`,
  `.ruff_cache`, `*.pyc`, `*.tmp`, `*.temp`, or `*.bak` artifacts under the
  inspected depth.

## Decision

Keep the repository cleanup policy conservative:

- remove caches and empty local tool byproducts;
- keep ignored data products needed for reproducibility and follow-on analysis;
- keep `.venv/` and `.codegraph/` because they support local development and
  code navigation;
- document cleanup actions under `docs/experiments/` whenever they affect the
  scientific workflow state.
