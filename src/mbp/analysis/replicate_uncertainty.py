"""Replicate-aware uncertainty diagnostics for condition triplets."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from mbp.baselines.capacity import (
    _as_float,
    _format_diagnostic_value,
    _mean,
    _median,
    _write_csv,
)

SCHEMA_VERSION = "gate22.replicate_uncertainty.v1"
TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")


def write_replicate_uncertainty_report(
    interval_table_path: Path,
    capacity_report_path: Path,
    capacity_predictions_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Write condition-triplet spread and model-error diagnostics."""
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    capacity_report = json.loads(capacity_report_path.read_text(encoding="utf-8"))
    prediction_rows = pq.read_table(capacity_predictions_path).to_pylist()
    out_dir.mkdir(parents=True, exist_ok=True)

    spread_rows = replicate_spread_rows(interval_rows)
    tolerance_rows = condition_tolerance_rows(spread_rows)
    error_rows = model_error_vs_replicate_spread_rows(prediction_rows, spread_rows)
    summary_rows = uncertainty_summary_rows(error_rows)
    _write_csv(out_dir / "replicate_spread_by_condition.csv", spread_rows)
    _write_csv(out_dir / "condition_tolerance_intervals.csv", tolerance_rows)
    _write_csv(out_dir / "model_error_vs_replicate_spread.csv", error_rows)
    _write_summary_md(summary_rows, out_dir / "replicate_uncertainty_summary.md")
    _write_c_rate_md(error_rows, out_dir / "c_rate_replicate_uncertainty.md")
    _write_uncertainty_claim_readiness(summary_rows, out_dir / "uncertainty_claim_readiness.md")
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "capacity_report": str(capacity_report_path),
            "capacity_predictions": str(capacity_predictions_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "replicate_spread_by_condition": str(out_dir / "replicate_spread_by_condition.csv"),
            "model_error_vs_replicate_spread": str(out_dir / "model_error_vs_replicate_spread.csv"),
            "condition_tolerance_intervals": str(out_dir / "condition_tolerance_intervals.csv"),
            "summary": str(out_dir / "replicate_uncertainty_summary.md"),
            "claim_readiness": str(out_dir / "uncertainty_claim_readiness.md"),
        },
        "source_capacity_report_schema": capacity_report.get("schema_version"),
        "row_counts": {
            "interval_rows": len(interval_rows),
            "spread_rows": len(spread_rows),
            "model_error_rows": len(error_rows),
        },
    }
    (out_dir / "replicate_uncertainty_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def replicate_spread_rows(interval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in interval_rows:
        for target in TARGETS:
            value = _as_float(row.get(target))
            if math.isfinite(value):
                grouped[(int(row["parameter_set"]), int(row["checkup_k_next"]), target)].append(row)
    output: list[dict[str, Any]] = []
    for (parameter_set, checkup_k_next, target), rows in sorted(grouped.items()):
        values = [_as_float(row.get(target)) for row in rows]
        finite = [value for value in values if math.isfinite(value)]
        if not finite:
            continue
        std = _std(finite)
        output.append(
            {
                "parameter_set": parameter_set,
                "checkup_k_next": checkup_k_next,
                "target": target,
                "n_replicates": len({str(row["cell_id"]) for row in rows}),
                "n_intervals": len(rows),
                "condition_mean": _mean(finite),
                "condition_median": _median(finite),
                "condition_std": std,
                "replicate_spread": max(finite) - min(finite) if len(finite) > 1 else 0.0,
                "tolerance_low": min(finite),
                "tolerance_high": max(finite),
                "aging_mode": _first(rows, "aging_mode"),
                "nominal_temperature_C": _first(rows, "nominal_temperature_C"),
                "voltage_window_family": _first(rows, "voltage_window_family"),
                "nominal_charge_C_rate": _first(rows, "nominal_charge_C_rate"),
                "c_rate_holdout_fold": _first(rows, "c_rate_holdout_fold"),
                "profile_holdout_fold": _first(rows, "profile_holdout_fold"),
            }
        )
    return output


def condition_tolerance_rows(spread_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "parameter_set": row["parameter_set"],
            "checkup_k_next": row["checkup_k_next"],
            "target": row["target"],
            "tolerance_low": row["tolerance_low"],
            "tolerance_high": row["tolerance_high"],
            "replicate_spread": row["replicate_spread"],
            "n_replicates": row["n_replicates"],
        }
        for row in spread_rows
    ]


def model_error_vs_replicate_spread_rows(
    prediction_rows: list[dict[str, Any]],
    spread_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    spread_lookup = {
        (int(row["parameter_set"]), int(row["checkup_k_next"]), str(row["target"])): row
        for row in spread_rows
    }
    grouped: dict[tuple[str, str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in prediction_rows:
        if str(row.get("run_scope")) != "primary":
            continue
        if str(row.get("target")) not in TARGETS:
            continue
        key = (
            str(row["target"]),
            str(row["split_name"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            int(row["parameter_set"]),
        )
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for (target, split_name, model_level, feature_group, parameter_set), rows in sorted(grouped.items()):
        abs_errors = [abs(_as_float(row.get("y_pred")) - _as_float(row.get("y_true"))) for row in rows]
        abs_errors = [value for value in abs_errors if math.isfinite(value)]
        spreads = [
            _as_float(spread_lookup.get((parameter_set, int(row["checkup_k_next"]), target), {}).get("replicate_spread"))
            for row in rows
        ]
        spreads = [value for value in spreads if math.isfinite(value)]
        if not abs_errors:
            continue
        mean_spread = _mean(spreads) if spreads else None
        output.append(
            {
                "target": target,
                "split_name": split_name,
                "model_level": model_level,
                "feature_group": feature_group,
                "parameter_set": parameter_set,
                "n_predictions": len(abs_errors),
                "model_mae": _mean(abs_errors),
                "model_median_abs_error": _median(abs_errors),
                "mean_replicate_spread": mean_spread,
                "model_mae_minus_replicate_spread": _mean(abs_errors) - mean_spread if mean_spread is not None else None,
                "model_error_exceeds_spread": bool(mean_spread is not None and _mean(abs_errors) > mean_spread),
            }
        )
    return output


def uncertainty_summary_rows(error_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in error_rows:
        grouped[(str(row["target"]), str(row["split_name"]), str(row["model_level"]), str(row["feature_group"]))].append(row)
    output = []
    for (target, split_name, model_level, feature_group), rows in sorted(grouped.items()):
        diffs = [_as_float(row.get("model_mae_minus_replicate_spread")) for row in rows]
        diffs = [value for value in diffs if math.isfinite(value)]
        output.append(
            {
                "target": target,
                "split_name": split_name,
                "model_level": model_level,
                "feature_group": feature_group,
                "n_conditions": len(rows),
                "mean_model_mae": _mean([float(row["model_mae"]) for row in rows]),
                "mean_replicate_spread": _mean([_as_float(row["mean_replicate_spread"]) for row in rows if math.isfinite(_as_float(row["mean_replicate_spread"]))]),
                "mean_mae_minus_spread": _mean(diffs) if diffs else None,
                "fraction_conditions_error_exceeds_spread": sum(bool(row["model_error_exceeds_spread"]) for row in rows) / len(rows),
            }
        )
    return output


def _write_summary_md(rows: list[dict[str, Any]], path: Path) -> None:
    best = sorted(rows, key=lambda row: float(row["mean_model_mae"]))[:12]
    lines = [
        "# Replicate Uncertainty Summary",
        "",
        "This is a condition-triplet diagnostic. It does not validate calibrated uncertainty.",
        "",
        "| Target | Split | Model | Feature group | Mean model MAE | Mean replicate spread | Error > spread fraction |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in best:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"{_format_diagnostic_value(row['mean_model_mae'])} | {_format_diagnostic_value(row['mean_replicate_spread'])} | "
            f"{_format_diagnostic_value(row['fraction_conditions_error_exceeds_spread'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_c_rate_md(rows: list[dict[str, Any]], path: Path) -> None:
    c_rate = [row for row in rows if row["split_name"] == "c_rate_holdout_fold"]
    lines = [
        "# C-Rate Replicate Uncertainty",
        "",
        "| Target | Model | Feature group | Conditions | Mean MAE | Mean spread | Error > spread fraction |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in uncertainty_summary_rows(c_rate):
        lines.append(
            f"| `{row['target']}` | `{row['model_level']}` | `{row['feature_group']}` | {row['n_conditions']} | "
            f"{_format_diagnostic_value(row['mean_model_mae'])} | {_format_diagnostic_value(row['mean_replicate_spread'])} | "
            f"{_format_diagnostic_value(row['fraction_conditions_error_exceeds_spread'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_uncertainty_claim_readiness(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Uncertainty Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        "| Replicate spread is quantified | `supported_for_diagnostics` | Condition-triplet spread and tolerance rows are generated. |",
        "| HGB calibrated uncertainty | `not_supported` | This diagnostic compares errors with empirical triplet spread; it does not calibrate HGB intervals. |",
        "| Replicate-aware intervals | `diagnostic_only` | Empirical min/max triplet tolerance intervals are reported, not validated predictive intervals. |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _first(rows: list[dict[str, Any]], key: str) -> Any:
    return next((row.get(key) for row in rows if row.get(key) is not None), None)
