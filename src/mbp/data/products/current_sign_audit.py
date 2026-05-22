"""Current-sign convention audit for LOG_AGE stress features."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

AUDIT_COLUMNS = ["cell_id", "timestamp_s", "v_raw_V", "i_raw_A", "soc_est"]
REST_CURRENT_A = 0.05
SAMPLE_LIMIT_PER_SIGN = 100_000


@dataclass
class RateSamples:
    """Bounded samples and streaming sums for one current-sign bucket."""

    count: int = 0
    dv_dt_sum: float = 0.0
    dsoc_dt_sum: float = 0.0
    dv_dt_samples: list[float] = field(default_factory=list)
    dsoc_dt_samples: list[float] = field(default_factory=list)

    def add(self, dv_dt: float, dsoc_dt: float) -> None:
        if not math.isfinite(dv_dt) or not math.isfinite(dsoc_dt):
            return
        self.count += 1
        self.dv_dt_sum += dv_dt
        self.dsoc_dt_sum += dsoc_dt
        if len(self.dv_dt_samples) < SAMPLE_LIMIT_PER_SIGN:
            self.dv_dt_samples.append(dv_dt)
            self.dsoc_dt_samples.append(dsoc_dt)

    @property
    def median_dv_dt(self) -> float | None:
        return _median(self.dv_dt_samples)

    @property
    def median_dsoc_dt(self) -> float | None:
        return _median(self.dsoc_dt_samples)

    @property
    def mean_dv_dt(self) -> float | None:
        return _safe_ratio(self.dv_dt_sum, self.count)

    @property
    def mean_dsoc_dt(self) -> float | None:
        return _safe_ratio(self.dsoc_dt_sum, self.count)


def audit_current_sign(
    log_age_path: Path,
    interval_table_path: Path,
    out_path: Path,
    max_row_groups: int | None = None,
) -> dict[str, Any]:
    """Audit whether positive LOG_AGE current corresponds to charge or discharge.

    The audit streams row groups and compares voltage/SOC derivatives following
    positive-current and negative-current samples. It is intentionally evidence
    producing, not a hard-coded sign decision.
    """
    if not log_age_path.exists():
        raise FileNotFoundError(f"LOG_AGE table not found: {log_age_path}")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")

    cohort_cells = set(
        pq.read_table(interval_table_path, columns=["cell_id"]).column("cell_id").to_pylist()
    )
    parquet_file = pq.ParquetFile(log_age_path)
    positive = RateSamples()
    negative = RateSamples()
    previous_by_cell: dict[str, tuple[float, float, float]] = {}
    row_groups_scanned = 0

    row_group_indices = list(range(parquet_file.metadata.num_row_groups))
    if max_row_groups is not None and max_row_groups < len(row_group_indices):
        step = len(row_group_indices) / max_row_groups
        row_group_indices = sorted({int(idx * step) for idx in range(max_row_groups)})
    for row_group_idx in row_group_indices:
        table = parquet_file.read_row_group(row_group_idx, columns=AUDIT_COLUMNS)
        rows = sorted(
            table.to_pylist(),
            key=lambda row: (str(row["cell_id"]), float(row["timestamp_s"])),
        )
        row_groups_scanned += 1
        for row in rows:
            cell_id = str(row["cell_id"])
            if cell_id not in cohort_cells:
                continue
            timestamp_s = _as_float(row.get("timestamp_s"))
            voltage = _as_float(row.get("v_raw_V"))
            current = _as_float(row.get("i_raw_A"))
            soc = _as_float(row.get("soc_est"))
            previous = previous_by_cell.get(cell_id)
            if previous is not None:
                previous_t, previous_v, previous_soc = previous
                dt_s = timestamp_s - previous_t
                if dt_s > 0.0 and abs(current) > REST_CURRENT_A:
                    dv_dt = (voltage - previous_v) / dt_s
                    dsoc_dt = (soc - previous_soc) / dt_s
                    if current > REST_CURRENT_A:
                        positive.add(dv_dt, dsoc_dt)
                    elif current < -REST_CURRENT_A:
                        negative.add(dv_dt, dsoc_dt)
            previous_by_cell[cell_id] = (timestamp_s, voltage, soc)

    convention, confidence, recommendation = _classify_sign_convention(positive, negative)
    report = {
        "schema_version": "gate6.current_sign_audit.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "log_age_path": str(log_age_path),
        "interval_table_path": str(interval_table_path),
        "row_groups_scanned": row_groups_scanned,
        "current_sign_convention": convention,
        "confidence": confidence,
        "evidence_rows": {
            "positive_current": positive.count,
            "negative_current": negative.count,
        },
        "median_dv_dt_positive_current": positive.median_dv_dt,
        "median_dv_dt_negative_current": negative.median_dv_dt,
        "median_dsoc_dt_positive_current": positive.median_dsoc_dt,
        "median_dsoc_dt_negative_current": negative.median_dsoc_dt,
        "mean_dv_dt_positive_current": positive.mean_dv_dt,
        "mean_dv_dt_negative_current": negative.mean_dv_dt,
        "mean_dsoc_dt_positive_current": positive.mean_dsoc_dt,
        "mean_dsoc_dt_negative_current": negative.mean_dsoc_dt,
        "recommendation": recommendation,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _classify_sign_convention(
    positive: RateSamples,
    negative: RateSamples,
) -> tuple[str, str, str]:
    pos_soc = positive.median_dsoc_dt
    neg_soc = negative.median_dsoc_dt
    pos_v = positive.median_dv_dt
    neg_v = negative.median_dv_dt
    min_rows = 1_000
    if positive.count < min_rows or negative.count < min_rows:
        min_rows = 3
    if (
        pos_soc is None
        or neg_soc is None
        or pos_v is None
        or neg_v is None
        or positive.count < min_rows
        or negative.count < min_rows
    ):
        return (
            "unknown",
            "low",
            "Insufficient derivative evidence; keep sign-dependent stress features provisional.",
        )

    positive_charge_votes = int(pos_soc > 0 and neg_soc < 0) + int(pos_v > 0 and neg_v < 0)
    positive_discharge_votes = int(pos_soc < 0 and neg_soc > 0) + int(pos_v < 0 and neg_v > 0)
    if positive_charge_votes == 2:
        return (
            "positive_current_charge",
            "high",
            "Positive current aligns with increasing voltage/SOC; sign-dependent charge features may be promoted after documentation review.",
        )
    if positive_discharge_votes == 2:
        return (
            "positive_current_discharge",
            "high",
            "Positive current aligns with decreasing voltage/SOC; invert charge/discharge labels before using sign-dependent features.",
        )
    if positive_charge_votes == 1 and positive_discharge_votes == 0:
        return (
            "positive_current_charge",
            "medium",
            "Evidence weakly supports positive-current charge; keep sign-dependent features provisional.",
        )
    if positive_discharge_votes == 1 and positive_charge_votes == 0:
        return (
            "positive_current_discharge",
            "medium",
            "Evidence weakly supports positive-current discharge; keep sign-dependent features provisional.",
        )
    return (
        "ambiguous",
        "low",
        "Voltage/SOC derivative evidence conflicts; use abs-current stress features as primary.",
    )


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _median(values: list[float]) -> float | None:
    finite_values = sorted(value for value in values if math.isfinite(value))
    if not finite_values:
        return None
    middle = len(finite_values) // 2
    if len(finite_values) % 2:
        return finite_values[middle]
    return (finite_values[middle - 1] + finite_values[middle]) / 2.0
