# Reproducibility Smoke Test Plan

This plan defines a future tiny fixture path for infrastructure validation
without requiring the full Luh-Blank raw dataset. It is a plan only; it does
not implement a fixture and does not create claim-bearing outputs.

## Purpose

Validate CLI wiring, schema contracts, release checks, benchmark task-registry
checks, and no-data-artifact policy on a tiny synthetic fixture.

## Non-Goals

- No scientific metrics.
- No model-training claim.
- No capacity, PULSE, EIS, policy, calibration, or architecture claim.
- No raw-data redistribution.
- No generated Parquet staged into git.

## Future Fixture Shape

The fixture should be small enough to run in seconds:

- two synthetic parameter-set conditions;
- two replicate cells per condition;
- two or three check-ups per cell;
- a tiny interval table with required split columns and schema version;
- tiny PULSE target table with scalar RT/50-style fields;
- tiny EIS target table with selected scalar endpoints;
- tiny run-event table with a few LOG_AGE-style events per interval;
- minimal artifact manifest rows that point to fixture-local generated data.

## Expected Command Coverage

The fixture path should eventually exercise:

- audit/inventory commands on fixture directories;
- schema validation for interval, PULSE, EIS, and run-event products;
- one no-op or tiny baseline command that proves CLI wiring only;
- `mbp report check-release-candidate`;
- `mbp report check-benchmark-tasks` against a fixture task registry;
- no-data-artifact staging guard.

## Expected Success Criteria

- Commands exit successfully on the fixture package.
- Required schema fields and schema versions are present.
- Generated local data stay under ignored `data/` paths.
- Release/task checks can run without the full dataset.
- Reports state that fixture outputs are infrastructure smoke tests only.

## Expected Failure Paths

The fixture should also include documented negative checks:

- missing schema version fails validation;
- missing required split column fails validation;
- a staged `data/` or Parquet path fails the data-policy guard;
- a fixture task with a supported blocked claim fails the task checker.

## Future Branch Boundary

Implement this plan only on a separate infrastructure branch. Do not mix it
with release tagging, manuscript edits, model training, or claim changes.
