"""Support-aware selective reliability diagnostics.

This module consumes existing prediction artifacts only. It does not train
models, generate features, recommend policies, or estimate causal effects.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

SCHEMA_VERSION = "gate80.support_reliability.v1"
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
NUMERIC_SUPPORT_FIELDS = ("nominal_temperature_C", "nominal_charge_C_rate", "nominal_discharge_C_rate")
CATEGORICAL_SUPPORT_FIELDS = ("voltage_window_family", "profile_label", "aging_mode")
RETENTION_FRACTIONS = (1.0, 0.9, 0.75, 0.5, 0.25)
PRIMARY_CAPACITY_MODEL = ("MH3_hist_gradient_boosting", "K2_nominal_condition")
PRIMARY_WARNING_MODEL = ("B6_hist_gradient_boosting_classifier", "W2_nominal")
PRIMARY_POLICY_MODEL = ("MH3_hist_gradient_boosting", "K2_nominal_condition")


def diagnose_support_reliability(
    interval_table_path: Path,
    horizon_table_path: Path,
    capacity_predictions_path: Path,
    warning_table_path: Path,
    warning_predictions_path: Path,
    policy_pairwise_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Run support-aware reliability diagnostics over existing artifacts."""
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    horizon_rows = pq.read_table(horizon_table_path).to_pylist()
    capacity_prediction_rows = pq.read_table(capacity_predictions_path).to_pylist()
    warning_rows = pq.read_table(warning_table_path).to_pylist()
    warning_prediction_rows = pq.read_table(warning_predictions_path).to_pylist()
    policy_pairwise_rows = _read_csv_rows(policy_pairwise_path)
    if not interval_rows:
        raise ValueError("Interval table is empty.")
    if not horizon_rows:
        raise ValueError("Capacity horizon table is empty.")
    if not capacity_prediction_rows:
        raise ValueError("Capacity horizon predictions are empty.")
    if not warning_rows:
        raise ValueError("Threshold-warning table is empty.")
    if not warning_prediction_rows:
        raise ValueError("Threshold-warning predictions are empty.")
    if not policy_pairwise_rows:
        raise ValueError("Policy pairwise metrics are empty.")

    condition_rows = condition_support_rows(interval_rows)
    support_lookup = {
        (str(row["split_name"]), int(row["parameter_set"])): row
        for row in condition_rows
    }
    capacity_rows = selective_capacity_performance_rows(capacity_prediction_rows, support_lookup)
    warning_rows_out = selective_warning_performance_rows(warning_prediction_rows, support_lookup)
    policy_rows = selective_policy_performance_rows(policy_pairwise_rows, support_lookup)
    readiness_rows = support_reliability_claim_readiness_rows(
        capacity_rows=capacity_rows,
        warning_rows=warning_rows_out,
        policy_rows=policy_rows,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "support_distance_by_split.csv", condition_rows)
    _write_csv(plots_dir / "selective_capacity_performance.csv", capacity_rows)
    _write_csv(plots_dir / "selective_threshold_warning_performance.csv", warning_rows_out)
    _write_csv(plots_dir / "selective_policy_contrast_performance.csv", policy_rows)
    _write_csv(plots_dir / "support_reliability_claim_readiness.csv", readiness_rows)
    _write_support_reliability_markdown(
        out_dir / "support_reliability_diagnostics.md",
        readiness_rows=readiness_rows,
        capacity_rows=capacity_rows,
        warning_rows=warning_rows_out,
        policy_rows=policy_rows,
    )
    _write_claim_readiness_markdown(out_dir / "support_reliability_claim_readiness.md", readiness_rows)

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "horizon_table": str(horizon_table_path),
            "capacity_predictions": str(capacity_predictions_path),
            "warning_table": str(warning_table_path),
            "warning_predictions": str(warning_predictions_path),
            "policy_pairwise": str(policy_pairwise_path),
        },
        "row_counts": {
            "interval_rows": len(interval_rows),
            "horizon_rows": len(horizon_rows),
            "capacity_prediction_rows": len(capacity_prediction_rows),
            "warning_prediction_rows": len(warning_prediction_rows),
            "policy_pairwise_rows": len(policy_pairwise_rows),
            "support_distance_rows": len(condition_rows),
            "selective_capacity_rows": len(capacity_rows),
            "selective_warning_rows": len(warning_rows_out),
            "selective_policy_rows": len(policy_rows),
        },
        "readiness": {str(row["claim_area"]): str(row["status"]) for row in readiness_rows},
        "outputs": {
            "diagnostics": str(out_dir / "support_reliability_diagnostics.md"),
            "claim_readiness": str(out_dir / "support_reliability_claim_readiness.md"),
            "support_distance_by_split": str(plots_dir / "support_distance_by_split.csv"),
            "selective_capacity_performance": str(plots_dir / "selective_capacity_performance.csv"),
            "selective_threshold_warning_performance": str(
                plots_dir / "selective_threshold_warning_performance.csv"
            ),
            "selective_policy_contrast_performance": str(
                plots_dir / "selective_policy_contrast_performance.csv"
            ),
        },
        "claim_scope": "support_aware_reliability_diagnostics_only_no_policy_recommendation",
    }
    (out_dir / "support_reliability_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def condition_support_rows(interval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute train-only support distances for each condition and split."""
    conditions = _condition_metadata(interval_rows)
    output: list[dict[str, Any]] = []
    for split_name in SPLIT_COLUMNS:
        for condition in sorted(conditions, key=lambda row: int(row["parameter_set"])):
            heldout_fold = int(condition[split_name])
            train = [row for row in conditions if int(row[split_name]) != heldout_fold]
            support = _condition_support(condition, train, split_name=split_name)
            output.append(
                {
                    "split_name": split_name,
                    "heldout_fold": heldout_fold,
                    "parameter_set": int(condition["parameter_set"]),
                    "aging_mode": condition["aging_mode"],
                    "nominal_temperature_C": _as_float(condition["nominal_temperature_C"]),
                    "voltage_window_family": condition["voltage_window_family"],
                    "nominal_charge_C_rate": _as_float(condition["nominal_charge_C_rate"]),
                    "nominal_discharge_C_rate": _as_float(condition["nominal_discharge_C_rate"]),
                    "profile_label": condition["profile_label"],
                    "train_conditions": len(train),
                    **support,
                    "claim_scope": "train_only_support_diagnostic",
                }
            )
    return output


def selective_capacity_performance_rows(
    prediction_rows: list[dict[str, Any]],
    support_lookup: dict[tuple[str, int], dict[str, Any]],
    *,
    retentions: tuple[float, ...] = RETENTION_FRACTIONS,
) -> list[dict[str, Any]]:
    """Summarize capacity MAE/RMSE after retaining most-supported rows."""
    supported = [_attach_row_support(row, support_lookup, int(row["parameter_set"])) for row in prediction_rows]
    grouped: dict[tuple[str, str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in supported:
        grouped[
            (
                str(row["split_name"]),
                str(row["target"]),
                int(row["horizon_checkups"]),
                str(row["model_level"]),
                str(row["feature_group"]),
            )
        ].append(row)
    output = []
    for (split_name, target, horizon, model_level, feature_group), rows in sorted(grouped.items()):
        for retention in retentions:
            selected = _select_supported_rows(rows, retention)
            errors = [abs(_as_float(row["y_pred"]) - _as_float(row["y_true"])) for row in selected]
            squared = [value * value for value in errors]
            output.append(
                {
                    "artifact": "capacity_horizon",
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": horizon,
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "retention_fraction": retention,
                    "rows_retained": len(selected),
                    "conditions_retained": len({int(row["parameter_set"]) for row in selected}),
                    "mae": _mean(errors),
                    "rmse": math.sqrt(_mean(squared)) if squared else math.nan,
                    "mean_support_score": _mean([_as_float(row["support_score"]) for row in selected]),
                    "median_nearest_distance": _median([_as_float(row["nearest_distance"]) for row in selected]),
                    "claim_scope": _claim_scope_for_feature_group(feature_group),
                }
            )
    return output


def selective_warning_performance_rows(
    prediction_rows: list[dict[str, Any]],
    support_lookup: dict[tuple[str, int], dict[str, Any]],
    *,
    retentions: tuple[float, ...] = RETENTION_FRACTIONS,
) -> list[dict[str, Any]]:
    """Summarize threshold-warning Brier/ECE after support filtering."""
    supported = [_attach_row_support(row, support_lookup, int(row["parameter_set"])) for row in prediction_rows]
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in supported:
        grouped[
            (
                str(row["split_name"]),
                str(row["target"]),
                str(row["model_level"]),
                str(row["feature_group"]),
            )
        ].append(row)
    output = []
    for (split_name, target, model_level, feature_group), rows in sorted(grouped.items()):
        for retention in retentions:
            selected = _select_supported_rows(rows, retention)
            y_true = [_as_int_bool(row["y_true"]) for row in selected]
            probs = [_clip_probability(_as_float(row["y_prob"])) for row in selected]
            brier_values = [(prob - truth) ** 2 for prob, truth in zip(probs, y_true, strict=False)]
            positives = sum(y_true)
            negatives = len(y_true) - positives
            output.append(
                {
                    "artifact": "threshold_warning",
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": _warning_horizon(target),
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "retention_fraction": retention,
                    "rows_retained": len(selected),
                    "conditions_retained": len({int(row["parameter_set"]) for row in selected}),
                    "positive_count": positives,
                    "negative_count": negatives,
                    "brier": _mean(brier_values),
                    "ece_10_bin": _expected_calibration_error(y_true, probs, bins=10),
                    "mean_support_score": _mean([_as_float(row["support_score"]) for row in selected]),
                    "median_nearest_distance": _median([_as_float(row["nearest_distance"]) for row in selected]),
                    "claim_scope": "prospective_threshold_warning_diagnostic",
                }
            )
    return output


def selective_policy_performance_rows(
    pairwise_rows: list[dict[str, Any]],
    support_lookup: dict[tuple[str, int], dict[str, Any]],
    *,
    retentions: tuple[float, ...] = RETENTION_FRACTIONS,
) -> list[dict[str, Any]]:
    """Summarize policy contrast sign accuracy after support filtering."""
    supported = []
    for row in pairwise_rows:
        if _is_oracle_policy_row(row):
            continue
        supported.append(_attach_policy_support(row, support_lookup))
    grouped: dict[tuple[str, str, int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in supported:
        for family in (str(row["contrast_family"]), "all"):
            grouped[
                (
                    str(row["split_name"]),
                    str(row["target"]),
                    int(row["horizon_checkups"]),
                    str(row["model_level"]),
                    str(row["feature_group"]),
                    family,
                )
            ].append(row)
    output = []
    for (split_name, target, horizon, model_level, feature_group, family), rows in sorted(grouped.items()):
        for retention in retentions:
            selected = _select_supported_rows(rows, retention)
            evaluable = [row for row in selected if _as_bool(row["sign_evaluable"])]
            correct = [row for row in evaluable if _as_bool(row["sign_correct"])]
            output.append(
                {
                    "artifact": "policy_contrast",
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": horizon,
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "contrast_family": family,
                    "retention_fraction": retention,
                    "rows_retained": len(selected),
                    "contrasts_retained": len({str(row["contrast_id"]) for row in selected}),
                    "sign_evaluable_rows": len(evaluable),
                    "sign_correct_rows": len(correct),
                    "sign_accuracy": len(correct) / len(evaluable) if evaluable else math.nan,
                    "mean_effect_abs_error": _mean([_as_float(row["effect_abs_error"]) for row in selected]),
                    "mean_support_score": _mean([_as_float(row["support_score"]) for row in selected]),
                    "median_nearest_distance": _median([_as_float(row["nearest_distance"]) for row in selected]),
                    "claim_scope": "prospective_supported_contrast_diagnostic",
                }
            )
    return output


def support_reliability_claim_readiness_rows(
    *,
    capacity_rows: list[dict[str, Any]],
    warning_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return conservative readiness rows for support-aware reliability."""
    capacity_gain = _selective_metric_gain(
        capacity_rows,
        metric="mae",
        lower_is_better=True,
        filters={
            "target": "delta_capacity_Ah_h",
            "model_level": PRIMARY_CAPACITY_MODEL[0],
            "feature_group": PRIMARY_CAPACITY_MODEL[1],
        },
    )
    c_rate_capacity_gain = _selective_metric_gain(
        capacity_rows,
        metric="mae",
        lower_is_better=True,
        filters={
            "split_name": "c_rate_holdout_fold",
            "target": "delta_capacity_Ah_h",
            "model_level": PRIMARY_CAPACITY_MODEL[0],
            "feature_group": PRIMARY_CAPACITY_MODEL[1],
        },
    )
    warning_gain = _selective_metric_gain(
        warning_rows,
        metric="brier",
        lower_is_better=True,
        filters={
            "target": "event_within_3_checkups",
            "model_level": PRIMARY_WARNING_MODEL[0],
            "feature_group": PRIMARY_WARNING_MODEL[1],
        },
    )
    policy_gain = _selective_metric_gain(
        policy_rows,
        metric="sign_accuracy",
        lower_is_better=False,
        filters={
            "target": "delta_capacity_Ah_h",
            "model_level": PRIMARY_POLICY_MODEL[0],
            "feature_group": PRIMARY_POLICY_MODEL[1],
            "contrast_family": "all",
        },
    )
    selective_passes = sum(gain > 0 for gain in (capacity_gain, warning_gain, policy_gain) if math.isfinite(gain))
    if selective_passes >= 2 and math.isfinite(c_rate_capacity_gain) and c_rate_capacity_gain >= 0:
        reliability_status = "partially_supported"
    elif selective_passes:
        reliability_status = "diagnostic_only"
    else:
        reliability_status = "not_supported"
    return [
        {
            "claim_area": "support-aware reliability diagnostics",
            "status": "supported_for_diagnostics",
            "evidence": "Train-only support-distance diagnostics were generated for capacity, threshold-warning, and policy-contrast artifacts.",
            "allowed_wording": "Support distance can be used to audit where existing predictions are inside or outside observed experimental support.",
            "forbidden_wording": "Support scoring validates deployment, intervention, or counterfactual policy decisions.",
        },
        {
            "claim_area": "selective prediction reliability",
            "status": reliability_status,
            "evidence": (
                f"50% retention gains: capacity MAE {_format_float(capacity_gain)}, "
                f"threshold-warning Brier {_format_float(warning_gain)}, "
                f"policy sign accuracy {_format_float(policy_gain)}."
            ),
            "allowed_wording": "Selective reliability curves may be discussed as diagnostic abstention/support-audit evidence.",
            "forbidden_wording": "A selective model is calibrated, deployable, or globally reliable.",
        },
        {
            "claim_area": "C-rate support reliability",
            "status": "diagnostic_only" if math.isfinite(c_rate_capacity_gain) and c_rate_capacity_gain >= 0 else "not_supported",
            "evidence": f"C-rate primary capacity 50% retention MAE gain is {_format_float(c_rate_capacity_gain)}.",
            "allowed_wording": "C-rate support reliability can be discussed only as split-specific diagnostics.",
            "forbidden_wording": "C-rate transfer is solved or safe for policy decisions.",
        },
        {
            "claim_area": "policy recommendation",
            "status": "blocked",
            "evidence": "Support filtering is an abstention diagnostic over existing predictions, not an optimizer or intervention study.",
            "allowed_wording": "No operating-policy recommendation is made.",
            "forbidden_wording": "Select, prescribe, optimize, or deploy an operating policy.",
        },
        {
            "claim_area": "causal or same-cell counterfactual claims",
            "status": "blocked",
            "evidence": "Support scores compare observed condition metadata and do not create same-cell interventions.",
            "allowed_wording": "Report support-bounded diagnostics only.",
            "forbidden_wording": "Changing a policy would cause the estimated effect in the same cell.",
        },
        {
            "claim_area": "calibrated risk or CBAT readiness",
            "status": "blocked",
            "evidence": "Selective diagnostics do not calibrate probabilities or justify architecture.",
            "allowed_wording": "Scores are diagnostic reliability outputs.",
            "forbidden_wording": "Calibrated risk, CBAT, or architecture readiness is supported.",
        },
    ]


def _condition_metadata(interval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_parameter: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in interval_rows:
        by_parameter[int(row["parameter_set"])].append(row)
    output = []
    for parameter_set, rows in sorted(by_parameter.items()):
        first = sorted(rows, key=lambda row: (str(row["cell_id"]), int(row["checkup_k"])))[0]
        output.append(
            {
                "parameter_set": parameter_set,
                "aging_mode": str(first.get("aging_mode", "missing")),
                "nominal_temperature_C": _as_float(first.get("nominal_temperature_C")),
                "voltage_window_family": str(first.get("voltage_window_family", "missing")),
                "nominal_charge_C_rate": _as_float(first.get("nominal_charge_C_rate")),
                "nominal_discharge_C_rate": _as_float(first.get("nominal_discharge_C_rate")),
                "profile_label": str(first.get("profile_label", "missing")),
                **{split: int(first[split]) for split in SPLIT_COLUMNS},
            }
        )
    return output


def _condition_support(test_condition: dict[str, Any], train_conditions: list[dict[str, Any]], *, split_name: str) -> dict[str, Any]:
    exact_matches = [row for row in train_conditions if _exact_nominal_match(test_condition, row)]
    same_stressor = [row for row in train_conditions if _same_stressor_family(test_condition, row, split_name)]
    distances = [
        (
            _condition_distance(test_condition, row, train_conditions),
            int(row["parameter_set"]),
        )
        for row in train_conditions
    ]
    finite_distances = [(distance, parameter_set) for distance, parameter_set in distances if math.isfinite(distance)]
    if finite_distances:
        nearest_distance, nearest_parameter_set = min(finite_distances, key=lambda item: (item[0], item[1]))
    else:
        nearest_distance = math.inf
        nearest_parameter_set = -1
    support_score = 1.0 / (1.0 + nearest_distance) if math.isfinite(nearest_distance) else 0.0
    return {
        "exact_nominal_match_count": len(exact_matches),
        "same_stressor_support_count": len(same_stressor),
        "nearest_distance": nearest_distance,
        "nearest_parameter_set": nearest_parameter_set,
        "support_score": support_score,
    }


def _exact_nominal_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for field in NUMERIC_SUPPORT_FIELDS:
        if abs(_as_float(left.get(field)) - _as_float(right.get(field))) > 1e-12:
            return False
    return all(str(left.get(field)) == str(right.get(field)) for field in CATEGORICAL_SUPPORT_FIELDS)


def _same_stressor_family(left: dict[str, Any], right: dict[str, Any], split_name: str) -> bool:
    if split_name == "temperature_holdout_fold":
        return abs(_as_float(left["nominal_temperature_C"]) - _as_float(right["nominal_temperature_C"])) <= 1e-12
    if split_name == "c_rate_holdout_fold":
        return (
            abs(_as_float(left["nominal_charge_C_rate"]) - _as_float(right["nominal_charge_C_rate"])) <= 1e-12
            and abs(_as_float(left["nominal_discharge_C_rate"]) - _as_float(right["nominal_discharge_C_rate"])) <= 1e-12
        )
    if split_name == "profile_holdout_fold":
        return str(left["profile_label"]) == str(right["profile_label"])
    if split_name == "voltage_window_holdout_fold":
        return str(left["voltage_window_family"]) == str(right["voltage_window_family"])
    return str(left["aging_mode"]) == str(right["aging_mode"])


def _condition_distance(left: dict[str, Any], right: dict[str, Any], train_conditions: list[dict[str, Any]]) -> float:
    squared = 0.0
    for field in NUMERIC_SUPPORT_FIELDS:
        denominator = _train_range(train_conditions, field)
        delta = (_as_float(left.get(field)) - _as_float(right.get(field))) / denominator
        if math.isfinite(delta):
            squared += delta * delta
    categorical_penalty = sum(str(left.get(field)) != str(right.get(field)) for field in CATEGORICAL_SUPPORT_FIELDS)
    return math.sqrt(squared + categorical_penalty)


def _train_range(rows: list[dict[str, Any]], field: str) -> float:
    values = [_as_float(row.get(field)) for row in rows]
    finite = [value for value in values if math.isfinite(value)]
    if len(finite) < 2:
        return 1.0
    value_range = max(finite) - min(finite)
    return value_range if value_range > 0 else 1.0


def _attach_row_support(
    row: dict[str, Any],
    support_lookup: dict[tuple[str, int], dict[str, Any]],
    parameter_set: int,
) -> dict[str, Any]:
    support = support_lookup.get((str(row["split_name"]), parameter_set), {})
    return row | _support_fields(support)


def _attach_policy_support(
    row: dict[str, Any],
    support_lookup: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    split_name = str(row["split_name"])
    arm_a_support = support_lookup.get((split_name, int(row["arm_a_parameter_set"])), {})
    arm_b_support = support_lookup.get((split_name, int(row["arm_b_parameter_set"])), {})
    score = min(_as_float(arm_a_support.get("support_score")), _as_float(arm_b_support.get("support_score")))
    distance = max(_as_float(arm_a_support.get("nearest_distance")), _as_float(arm_b_support.get("nearest_distance")))
    exact = min(int(arm_a_support.get("exact_nominal_match_count", 0)), int(arm_b_support.get("exact_nominal_match_count", 0)))
    same = min(int(arm_a_support.get("same_stressor_support_count", 0)), int(arm_b_support.get("same_stressor_support_count", 0)))
    return row | {
        "support_score": score if math.isfinite(score) else 0.0,
        "nearest_distance": distance if math.isfinite(distance) else math.inf,
        "exact_nominal_match_count": exact,
        "same_stressor_support_count": same,
    }


def _support_fields(support: dict[str, Any]) -> dict[str, Any]:
    return {
        "support_score": _as_float(support.get("support_score")),
        "nearest_distance": _as_float(support.get("nearest_distance")),
        "exact_nominal_match_count": int(support.get("exact_nominal_match_count", 0)),
        "same_stressor_support_count": int(support.get("same_stressor_support_count", 0)),
    }


def _select_supported_rows(rows: list[dict[str, Any]], retention: float) -> list[dict[str, Any]]:
    if not rows:
        return []
    retention = min(max(retention, 0.0), 1.0)
    count = max(1, math.ceil(len(rows) * retention))
    return sorted(
        rows,
        key=lambda row: (
            -_as_float(row.get("support_score")),
            _as_float(row.get("nearest_distance")),
            int(row.get("parameter_set", row.get("arm_a_parameter_set", 0))),
            str(row.get("cell_id", row.get("contrast_id", ""))),
        ),
    )[:count]


def _selective_metric_gain(
    rows: list[dict[str, Any]],
    *,
    metric: str,
    lower_is_better: bool,
    filters: dict[str, Any],
    selected_retention: float = 0.5,
) -> float:
    full = _mean_filtered_metric(rows, metric=metric, retention=1.0, filters=filters)
    selected = _mean_filtered_metric(rows, metric=metric, retention=selected_retention, filters=filters)
    if not math.isfinite(full) or not math.isfinite(selected):
        return math.nan
    return full - selected if lower_is_better else selected - full


def _mean_filtered_metric(
    rows: list[dict[str, Any]],
    *,
    metric: str,
    retention: float,
    filters: dict[str, Any],
) -> float:
    values = []
    for row in rows:
        if abs(_as_float(row.get("retention_fraction")) - retention) > 1e-12:
            continue
        if any(str(row.get(key)) != str(value) for key, value in filters.items()):
            continue
        value = _as_float(row.get(metric))
        if math.isfinite(value):
            values.append(value)
    return _mean(values)


def _warning_horizon(target: str) -> int:
    for horizon in (1, 2, 3):
        if target == f"event_within_{horizon}_checkups" or target == f"event_within_{horizon}_checkup":
            return horizon
    return -1


def _expected_calibration_error(y_true: list[int], probabilities: list[float], *, bins: int) -> float:
    if not y_true:
        return math.nan
    total = len(y_true)
    ece = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = [
            (truth, probability)
            for truth, probability in zip(y_true, probabilities, strict=False)
            if lower <= probability < upper or (index == bins - 1 and probability == 1.0)
        ]
        if not selected:
            continue
        accuracy = _mean([truth for truth, _ in selected])
        confidence = _mean([probability for _, probability in selected])
        ece += (len(selected) / total) * abs(accuracy - confidence)
    return ece


def _claim_scope_for_feature_group(feature_group: str) -> str:
    if feature_group == "K3_oracle_exposure_diagnostic":
        return "oracle_diagnostic_only"
    return "prospective_support_reliability_diagnostic"


def _is_oracle_policy_row(row: dict[str, Any]) -> bool:
    return (
        str(row.get("claim_scope")) == "oracle_diagnostic_only"
        or str(row.get("feature_group")) == "K3_oracle_exposure_diagnostic"
    )


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_support_reliability_markdown(
    out_path: Path,
    *,
    readiness_rows: list[dict[str, str]],
    capacity_rows: list[dict[str, Any]],
    warning_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
) -> None:
    primary_capacity = _primary_rows(capacity_rows, artifact="capacity_horizon", model=PRIMARY_CAPACITY_MODEL)
    primary_warning = _primary_rows(warning_rows, artifact="threshold_warning", model=PRIMARY_WARNING_MODEL)
    primary_policy = _primary_rows(policy_rows, artifact="policy_contrast", model=PRIMARY_POLICY_MODEL)
    lines = [
        "# Support-Aware Selective Reliability Diagnostics",
        "",
        "This report audits whether train-only condition-support scores identify reliable subsets of existing predictions. It does not train a model, create features, recommend policies, estimate causal effects, or validate calibrated risk.",
        "",
        "## Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in readiness_rows:
        lines.append(
            "| {area} | {status} | {evidence} | {allowed} | {forbidden} |".format(
                area=row["claim_area"],
                status=row["status"],
                evidence=row["evidence"],
                allowed=row["allowed_wording"],
                forbidden=row["forbidden_wording"],
            )
        )
    lines.extend(
        [
            "",
            "## Primary Capacity Rows",
            "",
            "| Split | Target | Horizon | Retention | Rows | MAE | Support |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in primary_capacity[:30]:
        lines.append(
            "| {split} | {target} | {horizon} | {retention} | {rows} | {mae} | {support} |".format(
                split=row["split_name"],
                target=row["target"],
                horizon=row["horizon_checkups"],
                retention=_format_float(row["retention_fraction"]),
                rows=row["rows_retained"],
                mae=_format_float(row["mae"]),
                support=_format_float(row["mean_support_score"]),
            )
        )
    lines.extend(
        [
            "",
            "## Primary Threshold-Warning Rows",
            "",
            "| Split | Target | Retention | Rows | Brier | ECE | Support |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in primary_warning[:30]:
        lines.append(
            "| {split} | {target} | {retention} | {rows} | {brier} | {ece} | {support} |".format(
                split=row["split_name"],
                target=row["target"],
                retention=_format_float(row["retention_fraction"]),
                rows=row["rows_retained"],
                brier=_format_float(row["brier"]),
                ece=_format_float(row["ece_10_bin"]),
                support=_format_float(row["mean_support_score"]),
            )
        )
    lines.extend(
        [
            "",
            "## Primary Policy-Contrast Rows",
            "",
            "| Split | Target | Horizon | Retention | Rows | Sign accuracy | Support |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in primary_policy[:30]:
        lines.append(
            "| {split} | {target} | {horizon} | {retention} | {rows} | {accuracy} | {support} |".format(
                split=row["split_name"],
                target=row["target"],
                horizon=row["horizon_checkups"],
                retention=_format_float(row["retention_fraction"]),
                rows=row["rows_retained"],
                accuracy=_format_float(row["sign_accuracy"]),
                support=_format_float(row["mean_support_score"]),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Support filtering is an abstention/reliability diagnostic over existing artifacts.",
            "- It must not be described as calibrated risk, policy optimization, causal evidence, same-cell counterfactual evidence, CBAT readiness, or deployment support.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _primary_rows(rows: list[dict[str, Any]], *, artifact: str, model: tuple[str, str]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("artifact")) == artifact
        and str(row.get("model_level")) == model[0]
        and str(row.get("feature_group")) == model[1]
        and _as_float(row.get("retention_fraction")) in {1.0, 0.5}
    ]


def _write_claim_readiness_markdown(out_path: Path, readiness_rows: list[dict[str, str]]) -> None:
    lines = [
        "# Support-Reliability Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in readiness_rows:
        lines.append(
            "| {area} | {status} | {evidence} | {allowed} | {forbidden} |".format(
                area=row["claim_area"],
                status=row["status"],
                evidence=row["evidence"],
                allowed=row["allowed_wording"],
                forbidden=row["forbidden_wording"],
            )
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _as_int_bool(value: Any) -> int:
    return 1 if _as_bool(value) else 0


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def _clip_probability(value: float) -> float:
    if not math.isfinite(value):
        return 0.5
    return min(max(value, 1e-6), 1.0 - 1e-6)


def _mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def _median(values: list[float | int]) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return math.nan
    middle = len(finite) // 2
    if len(finite) % 2:
        return finite[middle]
    return (finite[middle - 1] + finite[middle]) / 2.0


def _format_float(value: Any) -> str:
    number = _as_float(value)
    return "nan" if not math.isfinite(number) else f"{number:.6g}"
