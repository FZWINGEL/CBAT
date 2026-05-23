# Tagging the Benchmark Release Candidate

Suggested tag name: `benchmark-v0.1-rc1`

Suggested tag message:

```text
Benchmark v0.1 release candidate: grouped-validation battery degradation benchmark
```

## Pre-Tag Checklist

Run:

```bash
ruff check . --no-cache
pytest -p no:cacheprovider
mbp report check-release-candidate
git diff --check
git status --short
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

The staged data-artifact command should return no generated data products. If
there are no staged changes, the command may return exit code 1 because `rg`
found no matches; that is acceptable.

## Tag Command

```bash
git tag -a benchmark-v0.1-rc1 -m "Benchmark v0.1 release candidate: grouped-validation battery degradation benchmark"
git push origin benchmark-v0.1-rc1
```

## Rollback Guidance

If a generated data artifact is accidentally staged, do not commit or tag.
Unstage the file and re-run the release checks:

```bash
git restore --staged <path>
mbp report check-release-candidate
git diff --check
```

If a tag is created before the mistake is noticed, stop and inspect the commit
contents before deleting or moving the tag. Do not rewrite shared release tags
without explicit approval.
