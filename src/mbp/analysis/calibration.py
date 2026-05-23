"""Grouped calibration diagnostics for capacity prediction intervals."""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from mbp.baselines.capacity import _as_float, _format_diagnostic_value, _mean, _median, _write_csv

SCHEMA_VERSION = "gate23.calibration_capacity.v1"
TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")
SPLIT_VIEWS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
POINT_MODEL = "L2_hist_gradient_boosting"
QUANTILE_MODEL = "L3_quantile_hist_gradient_boosting"
FEATURE_GROUP = "F4_state_log_age_scalar"
METHODS = (
    "Q0_hgb_quantile_raw",
    "Q1_split_conformal_abs_residual",
    "Q2_stressor_family_conformal",
    "Q3_replicate_tolerance_hybrid",
)


def write_capacity_calibration_report(
    capacity_report_path: Path,
    capacity_predictions_path: Path,
    interval_table_path: Path,
    replicate_spread_path: Path,
    out_dir: Path,
    nominal_coverage: float = 0.9,
    min_calibration_conditions: int = 5,
) -> dict[str, Any]:
    """Evaluate grouped capacity prediction interval calibration from existing predictions."""
    out_dir.mkdir(parents=True, exist_ok=True)
    capacity_report = json.loads(capacity_report_path.read_text(encoding="utf-8"))
    prediction_rows = [
        row
        for row in pq.read_table(capacity_predictions_path).to_pylist()
        if str(row.get("run_scope")) == "primary" and str(row.get("target")) in TARGETS
    ]
    spread_rows = _read_csv_rows(replicate_spread_path)
    spread_lookup = _spread_lookup(spread_rows)

    coverage_rows, condition_rows = calibration_rows(
        prediction_rows,
        spread_lookup,
        nominal_coverage=nominal_coverage,
        min_calibration_conditions=min_calibration_conditions,
    )
    width_rows = interval_width_summary_rows(coverage_rows)
    c_rate_rows = [row for row in coverage_rows if row["split_name"] == "c_rate_holdout_fold"]
    claim_rows = claim_readiness_rows(coverage_rows)

    _write_csv(out_dir / "coverage_by_split.csv", coverage_rows)
    _write_csv(out_dir / "coverage_by_condition.csv", condition_rows)
    _write_csv(out_dir / "interval_width_summary.csv", width_rows)
    _write_c_rate_summary(c_rate_rows, out_dir / "c_rate_calibration_summary.md")
    _write_claim_readiness(claim_rows, out_dir / "calibration_claim_readiness.md")

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "nominal_coverage": nominal_coverage,
        "min_calibration_conditions": min_calibration_conditions,
        "inputs": {
            "capacity_report": str(capacity_report_path),
            "capacity_predictions": str(capacity_predictions_path),
            "interval_table": str(interval_table_path),
            "replicate_spread": str(replicate_spread_path),
        },
        "source_capacity_report_schema": capacity_report.get("schema_version"),
        "row_counts": {
            "prediction_rows": len(prediction_rows),
            "coverage_rows": len(coverage_rows),
            "condition_rows": len(condition_rows),
        },
        "outputs": {
            "coverage_by_split": str(out_dir / "coverage_by_split.csv"),
            "coverage_by_condition": str(out_dir / "coverage_by_condition.csv"),
            "interval_width_summary": str(out_dir / "interval_width_summary.csv"),
            "c_rate_calibration_summary": str(out_dir / "c_rate_calibration_summary.md"),
            "calibration_claim_readiness": str(out_dir / "calibration_claim_readiness.md"),
        },
    }
    (out_dir / "calibration_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def calibration_rows(
    prediction_rows: list[dict[str, Any]],
    replicate_spread_lookup: dict[tuple[int, int, str], float],
    nominal_coverage: float = 0.9,
    min_calibration_conditions: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return split-level and condition-level calibration summaries."""
    split_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    point_rows = [
        row
        for row in prediction_rows
        if str(row.get("model_level")) == POINT_MODEL and str(row.get("feature_group")) == FEATURE_GROUP
    ]
    quantile_rows = [
        row
        for row in prediction_rows
        if str(row.get("model_level")) == QUANTILE_MODEL and str(row.get("feature_group")) == FEATURE_GROUP
    ]
    for target in TARGETS:
        for split_name in SPLIT_VIEWS:
            fold_values = sorted(
                {
                    int(row["heldout_fold"])
                    for row in point_rows + quantile_rows
                    if str(row.get("target")) == target and str(row.get("split_name")) == split_name
                }
            )
            for heldout_fold in fold_values:
                q_test = _selection_rows(quantile_rows, target, split_name, heldout_fold)
                if q_test:
                    method_condition, method_split = _evaluate_quantile_rows(
                        q_test, target, split_name, heldout_fold
                    )
                    condition_rows.extend(method_condition)
                    split_rows.append(method_split)

                test_rows = _selection_rows(point_rows, target, split_name, heldout_fold)
                if not test_rows:
                    continue
                split_calibration = _calibration_pool(
                    point_rows, target, split_name, heldout_fold, test_rows, same_split_only=True
                )
                split_result = _evaluate_conformal_method(
                    "Q1_split_conformal_abs_residual",
                    test_rows,
                    split_calibration,
                    replicate_spread_lookup,
                    nominal_coverage,
                    min_calibration_conditions,
                )
                condition_rows.extend(split_result[0])
                split_rows.append(split_result[1])

                stressor_calibration = _calibration_pool(
                    point_rows, target, split_name, heldout_fold, test_rows, same_split_only=False
                )
                stressor_result = _evaluate_conformal_method(
                    "Q2_stressor_family_conformal",
                    test_rows,
                    stressor_calibration,
                    replicate_spread_lookup,
                    nominal_coverage,
                    min_calibration_conditions,
                )
                condition_rows.extend(stressor_result[0])
                split_rows.append(stressor_result[1])

                hybrid_result = _evaluate_conformal_method(
                    "Q3_replicate_tolerance_hybrid",
                    test_rows,
                    stressor_calibration,
                    replicate_spread_lookup,
                    nominal_coverage,
                    min_calibration_conditions,
                    use_replicate_hybrid=True,
                )
                condition_rows.extend(hybrid_result[0])
                split_rows.append(hybrid_result[1])
    return split_rows, condition_rows


def interval_width_summary_rows(coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "method": row["method"],
            "target": row["target"],
            "split_name": row["split_name"],
            "heldout_fold": row["heldout_fold"],
            "nominal_coverage": row["nominal_coverage"],
            "empirical_coverage": row["empirical_coverage"],
            "mean_interval_width": row["mean_interval_width"],
            "median_interval_width": row["median_interval_width"],
            "interval_score": row["interval_score"],
            "n_test_rows": row["n_test_rows"],
            "n_test_conditions": row["n_test_conditions"],
            "n_calibration_conditions": row["n_calibration_conditions"],
        }
        for row in coverage_rows
    ]


def claim_readiness_rows(coverage_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    def rows_for(method: str, target: str | None = None, split: str | None = None) -> list[dict[str, Any]]:
        return [
            row
            for row in coverage_rows
            if row["method"] == method
            and (target is None or row["target"] == target)
            and (split is None or row["split_name"] == split)
            and row["status"] == "evaluated"
        ]

    return [
        _claim_row(
            "Raw HGB quantiles calibrated",
            "Q0_hgb_quantile_raw",
            rows_for("Q0_hgb_quantile_raw"),
        ),
        _claim_row(
            "Grouped conformal intervals calibrated",
            "Q1_split_conformal_abs_residual",
            rows_for("Q1_split_conformal_abs_residual"),
        ),
        _claim_row(
            "Stressor-family conformal intervals calibrated",
            "Q2_stressor_family_conformal",
            rows_for("Q2_stressor_family_conformal"),
        ),
        _claim_row(
            "Replicate-aware hybrid intervals useful",
            "Q3_replicate_tolerance_hybrid",
            rows_for("Q3_replicate_tolerance_hybrid"),
            width_sensitive=True,
        ),
        _claim_row(
            "C-rate coverage acceptable",
            "all_methods",
            rows_for("Q2_stressor_family_conformal", split="c_rate_holdout_fold")
            + rows_for("Q3_replicate_tolerance_hybrid", split="c_rate_holdout_fold"),
        ),
        _claim_row(
            "delta_capacity_Ah coverage acceptable",
            "all_methods",
            rows_for("Q2_stressor_family_conformal", target="delta_capacity_Ah")
            + rows_for("Q3_replicate_tolerance_hybrid", target="delta_capacity_Ah"),
        ),
        {
            "claim_area": "Uncertainty claim readiness",
            "status": "blocked",
            "evidence": "No calibrated uncertainty claim is authorized unless coverage is close to nominal without test-residual leakage and C-rate coverage remains acceptable.",
        },
    ]


def _evaluate_quantile_rows(
    rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    intervals = []
    for row in rows:
        y_true = _as_float(row.get("y_true"))
        lower = _as_float(row.get("y_pred_q10"))
        upper = _as_float(row.get("y_pred_q90"))
        if math.isfinite(y_true) and math.isfinite(lower) and math.isfinite(upper) and upper >= lower:
            intervals.append(_interval_record(row, lower, upper, y_true))
    return _summarize_intervals(
        intervals,
        method="Q0_hgb_quantile_raw",
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        nominal_coverage=0.8,
        n_calibration_rows=0,
        n_calibration_conditions=0,
        calibration_source="model_quantile_outputs",
    )


def _evaluate_conformal_method(
    method: str,
    test_rows: list[dict[str, Any]],
    calibration_rows_: list[dict[str, Any]],
    replicate_spread_lookup: dict[tuple[int, int, str], float],
    nominal_coverage: float,
    min_calibration_conditions: int,
    use_replicate_hybrid: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = str(test_rows[0]["target"])
    split_name = str(test_rows[0]["split_name"])
    heldout_fold = int(test_rows[0]["heldout_fold"])
    calibration_parameter_sets = {int(row["parameter_set"]) for row in calibration_rows_}
    if len(calibration_parameter_sets) < min_calibration_conditions:
        return [], _insufficient_row(
            method,
            target,
            split_name,
            heldout_fold,
            len(calibration_rows_),
            len(calibration_parameter_sets),
            "not_enough_disjoint_calibration_conditions",
        )

    residuals = [
        abs(_as_float(row.get("y_true")) - _as_float(row.get("y_pred")))
        for row in calibration_rows_
    ]
    residuals = [value for value in residuals if math.isfinite(value)]
    if not residuals:
        return [], _insufficient_row(
            method,
            target,
            split_name,
            heldout_fold,
            len(calibration_rows_),
            len(calibration_parameter_sets),
            "no_finite_calibration_residuals",
        )

    radius = _conformal_radius(residuals, nominal_coverage)
    replicate_radius = 0.0
    if use_replicate_hybrid:
        replicate_values = [
            replicate_spread_lookup.get((int(row["parameter_set"]), int(row["checkup_k_next"]), target))
            for row in calibration_rows_
        ]
        replicate_values = [
            _as_float(value) for value in replicate_values if value is not None and math.isfinite(_as_float(value))
        ]
        replicate_radius = _median(replicate_values) if replicate_values else 0.0
        radius = max(radius, replicate_radius)

    intervals = []
    for row in test_rows:
        y_true = _as_float(row.get("y_true"))
        pred = _as_float(row.get("y_pred"))
        if math.isfinite(y_true) and math.isfinite(pred):
            test_spread = replicate_spread_lookup.get(
                (int(row["parameter_set"]), int(row["checkup_k_next"]), target)
            )
            intervals.append(
                _interval_record(
                    row,
                    pred - radius,
                    pred + radius,
                    y_true,
                    test_replicate_spread=test_spread,
                )
            )
    condition_rows, split_row = _summarize_intervals(
        intervals,
        method=method,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        nominal_coverage=nominal_coverage,
        n_calibration_rows=len(calibration_rows_),
        n_calibration_conditions=len(calibration_parameter_sets),
        calibration_source="same_split_excluding_test_conditions"
        if method == "Q1_split_conformal_abs_residual"
        else "cross_split_excluding_test_conditions",
        conformal_radius=radius,
        replicate_radius=replicate_radius if use_replicate_hybrid else None,
    )
    return condition_rows, split_row


def _summarize_intervals(
    intervals: list[dict[str, Any]],
    method: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    nominal_coverage: float,
    n_calibration_rows: int,
    n_calibration_conditions: int,
    calibration_source: str,
    conformal_radius: float | None = None,
    replicate_radius: float | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not intervals:
        return [], _insufficient_row(
            method,
            target,
            split_name,
            heldout_fold,
            n_calibration_rows,
            n_calibration_conditions,
            "no_finite_test_intervals",
        )

    condition_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in intervals:
        condition_groups[int(row["parameter_set"])].append(row)
    condition_rows = [
        _aggregate_interval_rows(
            rows,
            method,
            target,
            split_name,
            heldout_fold,
            nominal_coverage,
            n_calibration_rows,
            n_calibration_conditions,
            calibration_source,
            conformal_radius,
            replicate_radius,
            parameter_set=parameter_set,
        )
        for parameter_set, rows in sorted(condition_groups.items())
    ]
    split_row = _aggregate_interval_rows(
        intervals,
        method,
        target,
        split_name,
        heldout_fold,
        nominal_coverage,
        n_calibration_rows,
        n_calibration_conditions,
        calibration_source,
        conformal_radius,
        replicate_radius,
        parameter_set=None,
    )
    split_row["condition_level_coverage"] = _mean(
        [_as_float(row["empirical_coverage"]) for row in condition_rows]
    )
    split_row["worst_condition_coverage"] = min(
        _as_float(row["empirical_coverage"]) for row in condition_rows
    )
    return condition_rows, split_row


def _aggregate_interval_rows(
    rows: list[dict[str, Any]],
    method: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    nominal_coverage: float,
    n_calibration_rows: int,
    n_calibration_conditions: int,
    calibration_source: str,
    conformal_radius: float | None,
    replicate_radius: float | None,
    parameter_set: int | None,
) -> dict[str, Any]:
    covered = [bool(row["covered"]) for row in rows]
    widths = [_as_float(row["width"]) for row in rows]
    scores = [_as_float(row["interval_score"]) for row in rows]
    replicate_spreads = [
        _as_float(row.get("test_replicate_spread"))
        for row in rows
        if math.isfinite(_as_float(row.get("test_replicate_spread")))
    ]
    coverage = sum(covered) / len(covered)
    base = {
        "status": "evaluated",
        "method": method,
        "target": target,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "parameter_set": parameter_set,
        "nominal_coverage": nominal_coverage,
        "empirical_coverage": coverage,
        "coverage_delta_from_nominal": coverage - nominal_coverage,
        "n_test_rows": len(rows),
        "n_test_conditions": len({int(row["parameter_set"]) for row in rows}),
        "n_calibration_rows": n_calibration_rows,
        "n_calibration_conditions": n_calibration_conditions,
        "mean_interval_width": _mean(widths),
        "median_interval_width": _median(widths),
        "interval_score": _mean(scores),
        "calibration_source": calibration_source,
        "conformal_radius": conformal_radius,
        "replicate_radius": replicate_radius,
        "mean_test_replicate_spread": _mean(replicate_spreads) if replicate_spreads else None,
        "intervals_narrower_than_replicate_spread_fraction": _fraction(
            [
                _as_float(row["width"]) < _as_float(row.get("test_replicate_spread"))
                for row in rows
                if math.isfinite(_as_float(row.get("test_replicate_spread")))
            ]
        ),
        "intervals_wider_than_replicate_spread_fraction": _fraction(
            [
                _as_float(row["width"]) >= _as_float(row.get("test_replicate_spread"))
                for row in rows
                if math.isfinite(_as_float(row.get("test_replicate_spread")))
            ]
        ),
    }
    if parameter_set is None:
        base["condition_level_coverage"] = None
        base["worst_condition_coverage"] = None
    return base


def _interval_record(
    row: dict[str, Any],
    lower: float,
    upper: float,
    y_true: float,
    test_replicate_spread: float | None = None,
) -> dict[str, Any]:
    alpha = 0.1
    if upper < lower:
        lower, upper = upper, lower
    below = max(0.0, lower - y_true)
    above = max(0.0, y_true - upper)
    width = upper - lower
    return {
        "target": row["target"],
        "split_name": row["split_name"],
        "heldout_fold": row["heldout_fold"],
        "parameter_set": row["parameter_set"],
        "checkup_k_next": row["checkup_k_next"],
        "covered": lower <= y_true <= upper,
        "width": width,
        "interval_score": width + (2.0 / alpha) * (below + above),
        "test_replicate_spread": test_replicate_spread,
    }


def _calibration_pool(
    rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    test_rows: list[dict[str, Any]],
    same_split_only: bool,
) -> list[dict[str, Any]]:
    test_parameter_sets = {int(row["parameter_set"]) for row in test_rows}
    pool: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("target")) != target:
            continue
        if int(row["parameter_set"]) in test_parameter_sets:
            continue
        if same_split_only and str(row.get("split_name")) != split_name:
            continue
        if same_split_only and int(row.get("heldout_fold")) == heldout_fold:
            continue
        if _finite_residual(row):
            pool.append(row)
    return pool


def _selection_rows(
    rows: list[dict[str, Any]], target: str, split_name: str, heldout_fold: int
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("target")) == target
        and str(row.get("split_name")) == split_name
        and int(row.get("heldout_fold")) == heldout_fold
    ]


def _finite_residual(row: dict[str, Any]) -> bool:
    return math.isfinite(_as_float(row.get("y_true"))) and math.isfinite(_as_float(row.get("y_pred")))


def _conformal_radius(residuals: list[float], nominal_coverage: float) -> float:
    if not residuals:
        raise ValueError("Cannot compute conformal radius from no residuals.")
    ordered = sorted(residuals)
    index = min(len(ordered) - 1, max(0, math.ceil((len(ordered) + 1) * nominal_coverage) - 1))
    return ordered[index]


def _spread_lookup(rows: list[dict[str, Any]]) -> dict[tuple[int, int, str], float]:
    lookup: dict[tuple[int, int, str], float] = {}
    for row in rows:
        value = _as_float(row.get("replicate_spread"))
        if math.isfinite(value):
            lookup[(int(row["parameter_set"]), int(row["checkup_k_next"]), str(row["target"]))] = value
    return lookup


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fraction(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _insufficient_row(
    method: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    n_calibration_rows: int,
    n_calibration_conditions: int,
    reason: str,
) -> dict[str, Any]:
    return {
        "status": "insufficient",
        "method": method,
        "target": target,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "parameter_set": None,
        "nominal_coverage": 0.8 if method == "Q0_hgb_quantile_raw" else 0.9,
        "empirical_coverage": None,
        "condition_level_coverage": None,
        "worst_condition_coverage": None,
        "coverage_delta_from_nominal": None,
        "n_test_rows": 0,
        "n_test_conditions": 0,
        "n_calibration_rows": n_calibration_rows,
        "n_calibration_conditions": n_calibration_conditions,
        "mean_interval_width": None,
        "median_interval_width": None,
        "interval_score": None,
        "calibration_source": reason,
        "conformal_radius": None,
        "replicate_radius": None,
        "mean_test_replicate_spread": None,
        "intervals_narrower_than_replicate_spread_fraction": None,
        "intervals_wider_than_replicate_spread_fraction": None,
    }


def _claim_row(
    claim_area: str,
    method: str,
    rows: list[dict[str, Any]],
    width_sensitive: bool = False,
) -> dict[str, str]:
    if not rows:
        return {
            "claim_area": claim_area,
            "status": "blocked",
            "evidence": "No evaluated rows are available for this claim area.",
        }
    coverages = [_as_float(row["empirical_coverage"]) for row in rows]
    c_rate_rows = [row for row in rows if row["split_name"] == "c_rate_holdout_fold"]
    c_rate_ok = bool(c_rate_rows) and min(_as_float(row["empirical_coverage"]) for row in c_rate_rows) >= 0.85
    close_to_nominal = min(coverages) >= 0.85
    mean_coverage = _mean(coverages)
    mean_width = _mean([_as_float(row["mean_interval_width"]) for row in rows])
    if close_to_nominal and c_rate_ok:
        status = "partially_supported" if width_sensitive and mean_width > 0.5 else "supported"
    elif mean_coverage >= 0.85:
        status = "partially_supported"
    else:
        status = "not_supported"
    return {
        "claim_area": claim_area,
        "status": status,
        "evidence": (
            f"{method}: evaluated {len(rows)} rows; min coverage "
            f"{_format_diagnostic_value(min(coverages))}; mean coverage "
            f"{_format_diagnostic_value(mean_coverage)}; C-rate acceptable={c_rate_ok}."
        ),
    }


def _write_c_rate_summary(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# C-Rate Calibration Summary",
        "",
        "Intervals are calibrated without using C-rate test residuals.",
        "",
        "| Method | Target | Coverage | Width | Conditions | Calibration conditions | Status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['method']}` | `{row['target']}` | "
            f"{_format_diagnostic_value(row.get('empirical_coverage'))} | "
            f"{_format_diagnostic_value(row.get('mean_interval_width'))} | "
            f"{row.get('n_test_conditions')} | {row.get('n_calibration_conditions')} | "
            f"`{row.get('status')}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness(rows: list[dict[str, str]], path: Path) -> None:
    lines = [
        "# Calibration Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
