"""Interval subset registry for baseline-readiness policy gates."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import INTERVAL_SUBSET_REGISTRY_SCHEMA, validate_table

SCHEMA_VERSION = "gate4.interval_subset.v1"
POLICY_VERSION = "log_age_monotonicity.v1"
DEFAULT_EFC_JITTER_THRESHOLD = 0.00025


@dataclass(frozen=True)
class MonotonicityPolicyClassification:
    baseline_clean_strict: bool
    baseline_clean_tolerant: bool
    sensitivity_flagged_monotonicity: bool
    small_efc_jitter: bool
    excluded_due_to_large_efc_drop: bool
    excluded_due_to_timestamp_drop: bool
    excluded_due_to_missing_log_age: bool
    excluded_due_to_duration_error: bool


def classify_interval_policy(
    *,
    duration_s: float,
    log_age_available: bool,
    log_age_row_count: int,
    monotonicity_violation_count: int,
    timestamp_decrease_count: int,
    max_timestamp_drop_s: float,
    max_efc_drop: float,
    efc_jitter_threshold: float = DEFAULT_EFC_JITTER_THRESHOLD,
) -> MonotonicityPolicyClassification:
    """Classify one interval under the LOG_AGE monotonicity policy."""
    duration_error = duration_s <= 0
    missing_log_age = (not log_age_available) or log_age_row_count <= 0
    timestamp_drop = timestamp_decrease_count > 0 or max_timestamp_drop_s > 0
    has_monotonicity = monotonicity_violation_count > 0
    small_efc_jitter = (
        has_monotonicity
        and not timestamp_drop
        and max_efc_drop > 0
        and max_efc_drop <= efc_jitter_threshold
    )
    large_efc_drop = max_efc_drop > efc_jitter_threshold
    base_ok = not (duration_error or missing_log_age)

    return MonotonicityPolicyClassification(
        baseline_clean_strict=base_ok and not has_monotonicity,
        baseline_clean_tolerant=base_ok and not timestamp_drop and not large_efc_drop,
        sensitivity_flagged_monotonicity=has_monotonicity,
        small_efc_jitter=small_efc_jitter,
        excluded_due_to_large_efc_drop=large_efc_drop,
        excluded_due_to_timestamp_drop=timestamp_drop,
        excluded_due_to_missing_log_age=missing_log_age,
        excluded_due_to_duration_error=duration_error,
    )


def build_interval_subset_registry(
    interval_table_path: Path,
    out_path: Path,
    report_path: Path,
    efc_jitter_threshold: float = DEFAULT_EFC_JITTER_THRESHOLD,
    policy_version: str = POLICY_VERSION,
) -> pa.Table:
    """Build and write interval subset labels for baseline readiness."""
    if efc_jitter_threshold < 0:
        raise ValueError("efc_jitter_threshold must be non-negative")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")

    interval_table = pq.read_table(interval_table_path)
    rows = []
    counts: Counter[str] = Counter()
    for row in interval_table.to_pylist():
        classification = classify_interval_policy(
            duration_s=float(row["duration_s"]),
            log_age_available=bool(row["LOG_AGE_available"]),
            log_age_row_count=int(row["log_age_row_count"]),
            monotonicity_violation_count=int(row["log_age_monotonicity_violation_count"]),
            timestamp_decrease_count=int(row["log_age_timestamp_decrease_count"]),
            max_timestamp_drop_s=float(row["log_age_max_timestamp_drop_s"]),
            max_efc_drop=float(row["log_age_max_efc_drop"]),
            efc_jitter_threshold=efc_jitter_threshold,
        )
        interval_id = f"{row['cell_id']}:{int(row['checkup_k'])}->{int(row['checkup_k_next'])}"
        out_row = {
            "cell_id": row["cell_id"],
            "parameter_set": int(row["parameter_set"]),
            "replicate_id": int(row["replicate_id"]),
            "checkup_k": int(row["checkup_k"]),
            "checkup_k_next": int(row["checkup_k_next"]),
            "interval_id": interval_id,
            "baseline_clean_strict": classification.baseline_clean_strict,
            "baseline_clean_tolerant": classification.baseline_clean_tolerant,
            "sensitivity_flagged_monotonicity": classification.sensitivity_flagged_monotonicity,
            "small_efc_jitter": classification.small_efc_jitter,
            "excluded_due_to_large_efc_drop": classification.excluded_due_to_large_efc_drop,
            "excluded_due_to_timestamp_drop": classification.excluded_due_to_timestamp_drop,
            "excluded_due_to_missing_log_age": classification.excluded_due_to_missing_log_age,
            "excluded_due_to_duration_error": classification.excluded_due_to_duration_error,
            "monotonicity_policy_version": policy_version,
            "schema_version": SCHEMA_VERSION,
        }
        rows.append(out_row)
        for key, value in out_row.items():
            if isinstance(value, bool) and value:
                counts[key] += 1

    table = pa.Table.from_pylist(rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA)
    if not validate_table(table, INTERVAL_SUBSET_REGISTRY_SCHEMA, strict=True):
        raise TypeError("Generated interval subset registry does not match schema.")

    metadata = {
        b"schema_version": SCHEMA_VERSION.encode(),
        b"monotonicity_policy_version": policy_version.encode(),
        b"efc_jitter_threshold": str(efc_jitter_threshold).encode(),
        b"interval_table_path": str(interval_table_path).encode(),
    }
    table = table.replace_schema_metadata(metadata)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)

    report = {
        "status": "passed",
        "interval_table": str(interval_table_path),
        "interval_subset_registry": str(out_path),
        "row_count": table.num_rows,
        "efc_jitter_threshold": efc_jitter_threshold,
        "monotonicity_policy_version": policy_version,
        "baseline_clean_strict_count": counts["baseline_clean_strict"],
        "baseline_clean_tolerant_count": counts["baseline_clean_tolerant"],
        "sensitivity_flagged_monotonicity_count": counts[
            "sensitivity_flagged_monotonicity"
        ],
        "small_efc_jitter_count": counts["small_efc_jitter"],
        "excluded_due_to_large_efc_drop_count": counts["excluded_due_to_large_efc_drop"],
        "excluded_due_to_timestamp_drop_count": counts["excluded_due_to_timestamp_drop"],
        "excluded_due_to_missing_log_age_count": counts["excluded_due_to_missing_log_age"],
        "excluded_due_to_duration_error_count": counts["excluded_due_to_duration_error"],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return table
