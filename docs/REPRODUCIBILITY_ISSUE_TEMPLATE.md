# Reproducibility Issue Template

Use this template for issues encountered while validating the benchmark package
or manuscript handoff.

## Issue Type

Choose one or more:

- command failure
- dependency/environment setup
- missing artifact
- schema mismatch
- release-check failure
- task-registry-check failure
- manuscript-check failure
- data policy
- documentation ambiguity

## Environment

```text
OS:
Python:
uv:
Command:
Branch or commit:
```

## Observed Behavior

```text

```

## Expected Behavior

```text

```

## Relevant Output

Paste the shortest useful excerpt. Do not include raw data or generated
Parquet contents.

```text

```

## Data Policy Check

Confirm whether any generated data or Parquet path is staged:

```bash
git diff --cached --name-only | rg '(^data/|\.parquet$)'
```

Expected result: no output.
