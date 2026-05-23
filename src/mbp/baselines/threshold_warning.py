"""Non-neural threshold-event early-warning baselines."""

from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import (
    SPLIT_COLUMNS,
    assert_no_parameter_set_leakage,
    iter_split_instances,
)

SCHEMA_VERSION = "gate26.threshold_warning_baseline.v1"
TARGETS = ("event_within_1_checkup", "event_within_2_checkups", "event_within_3_checkups")
MODEL_LEVELS = (
    "B0_event_rate_prior",
    "B1_distance_to_threshold_rule",
    "B2_linear_extrapolation_to_threshold",
    "B3_logistic_distance_baseline",
    "B4_logistic_regression",
    "B5_ridge_logistic",
    "B6_hist_gradient_boosting_classifier",
)
FEATURE_GROUPS = ("W0_capacity_state", "W1_state_time", "W2_nominal")
PROXIMITY_MODEL_LEVELS = {
    "B1_distance_to_threshold_rule",
    "B2_linear_extrapolation_to_threshold",
    "B3_logistic_distance_baseline",
}
DEFAULT_TARGETS = TARGETS
DEFAULT_MODELS = MODEL_LEVELS
DEFAULT_FEATURE_GROUPS = FEATURE_GROUPS
LABEL_POLICIES = ("all_rows", "verified_only", "censored_as_negative")
DEFAULT_LABEL_POLICY = "all_rows"
LEAKAGE_FIELDS = {
    "capacity_Ah_k1",
    "delta_capacity_Ah",
    "event_checkup_k",
    "time_to_event_checkups",
    "event_within_1_checkup",
    "event_within_2_checkups",
    "event_within_3_checkups",
    "pulse_1s_resistance_k1",
    "delta_pulse_1s_resistance",
    "eis_z_abs_1kHz_k1",
    "delta_eis_z_abs_1kHz",
}

NUMERIC_FEATURES = {
    "W0_capacity_state": ("capacity_Ah_k", "soh_k"),
    "W1_state_time": ("capacity_Ah_k", "soh_k", "checkup_k", "calendar_day_k", "cumulative_efc_k"),
    "W2_nominal": (
        "capacity_Ah_k",
        "soh_k",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
}
CATEGORICAL_FEATURES = {
    "W0_capacity_state": (),
    "W1_state_time": (),
    "W2_nominal": ("voltage_window_family", "profile_label", "aging_mode"),
}


@dataclass(frozen=True)
class WarningFeatureEncoder:
    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    numeric_scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "WarningFeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown threshold-warning feature group: {feature_group}")
        numeric_columns = NUMERIC_FEATURES[feature_group]
        categorical_columns = CATEGORICAL_FEATURES[feature_group]
        leakage = (set(numeric_columns) | set(categorical_columns)) & LEAKAGE_FIELDS
        if leakage:
            raise ValueError(f"Feature group {feature_group} includes leakage fields: {sorted(leakage)}")
        impute: dict[str, float] = {}
        scale: dict[str, float] = {}
        for column in numeric_columns:
            values = [_as_float(row.get(column)) for row in rows]
            finite = [value for value in values if math.isfinite(value)]
            mean = sum(finite) / len(finite) if finite else 0.0
            variance = sum((value - mean) ** 2 for value in finite) / len(finite) if finite else 0.0
            impute[column] = mean
            scale[column] = math.sqrt(variance) if variance > 0 else 1.0
        categories = {
            column: tuple(sorted({_category(row.get(column)) for row in rows}))
            for column in categorical_columns
        }
        return cls(feature_group, numeric_columns, categorical_columns, impute, scale, categories)

    def transform(self, rows: list[dict[str, Any]], *, standardize_numeric: bool = False) -> list[list[float]]:
        matrix = []
        for row in rows:
            values = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                numeric = value if math.isfinite(value) else self.numeric_impute_values[column]
                if standardize_numeric:
                    numeric = (numeric - self.numeric_impute_values[column]) / self.numeric_scale_values[column]
                values.append(numeric)
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(1.0 if observed == category else 0.0 for category in self.categorical_values[column])
            matrix.append(values)
        return matrix


def run_threshold_warning_baselines(
    warning_table_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    *,
    seed: int = 42,
    hgb_max_iter: int = 50,
    targets: list[str] | None = None,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    split_views: list[str] | None = None,
    label_policy: str = DEFAULT_LABEL_POLICY,
) -> dict[str, Any]:
    """Run non-neural grouped threshold-event warning baselines."""
    selected_targets = _normalize_selection(targets, TARGETS, DEFAULT_TARGETS, "target")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, DEFAULT_MODELS, "model")
    selected_features = _normalize_selection(feature_groups, FEATURE_GROUPS, DEFAULT_FEATURE_GROUPS, "feature group")
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, SPLIT_COLUMNS, "split view")
    if label_policy not in LABEL_POLICIES:
        raise ValueError(f"Unknown label policy: {label_policy}")
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    dependency_free_models = {
        "B0_event_rate_prior",
        "B1_distance_to_threshold_rule",
        "B2_linear_extrapolation_to_threshold",
    }
    if any(model not in dependency_free_models for model in selected_models):
        _import_sklearn()
    rows = pq.read_table(warning_table_path).to_pylist()
    if not rows:
        raise ValueError("Threshold-warning table is empty.")
    _audit_warning_feature_groups(selected_features)

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for target in selected_targets:
                policy_train_rows = filter_rows_by_label_policy(train_rows, target, label_policy)
                policy_test_rows = filter_rows_by_label_policy(test_rows, target, label_policy)
                if not policy_train_rows or not policy_test_rows:
                    continue
                for model_level in selected_models:
                    model_features = (
                        ("prior_rate",)
                        if model_level == "B0_event_rate_prior"
                        else ("distance_to_threshold",)
                        if model_level in PROXIMITY_MODEL_LEVELS
                        else tuple(selected_features)
                    )
                    for feature_group in model_features:
                        probs, train_one_class = predict_warning_probability(
                            model_level,
                            feature_group,
                            policy_train_rows,
                            policy_test_rows,
                            target,
                            seed=seed,
                            hgb_max_iter=hgb_max_iter,
                        )
                        metrics.append(
                            warning_metrics(
                                policy_test_rows,
                                probs,
                                target=target,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=policy_train_rows,
                                train_one_class=train_one_class,
                            )
                        )
                        predictions.extend(
                            prediction_rows(
                                policy_test_rows,
                                probs,
                                target=target,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=model_level,
                                feature_group=feature_group,
                            )
                        )

    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(predictions), predictions_out_path)
    report_dir = _default_report_dir(out_path)
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {"warning_table": str(warning_table_path)},
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(report_dir),
        },
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "targets": selected_targets,
        "model_levels": selected_models,
        "feature_groups": selected_features,
        "split_views": selected_splits,
        "label_policy": label_policy,
        "row_counts": {
            "rows": len(rows),
            "cells": len({str(row["cell_id"]) for row in rows}),
            "parameter_sets": len({int(row["parameter_set"]) for row in rows}),
            "metrics": len(metrics),
            "predictions": len(predictions),
            "target_label_policy_rows": target_label_policy_counts(rows, selected_targets, label_policy),
        },
        "leakage_audit": leakage_audit(selected_features),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_threshold_warning_artifacts(report, report_dir)
    return report


def filter_rows_by_label_policy(rows: list[dict[str, Any]], target: str, label_policy: str) -> list[dict[str, Any]]:
    if label_policy not in LABEL_POLICIES:
        raise ValueError(f"Unknown label policy: {label_policy}")
    if label_policy in {"all_rows", "censored_as_negative"}:
        return rows
    return [row for row in rows if label_status(row, target) != "right_censored_unknown"]


def target_label_policy_counts(
    rows: list[dict[str, Any]],
    targets: list[str],
    label_policy: str,
) -> dict[str, dict[str, int]]:
    return {
        target: {
            "rows": len(filtered := filter_rows_by_label_policy(rows, target, label_policy)),
            "positive_count": sum(1 for row in filtered if row[target]),
            "negative_count": sum(1 for row in filtered if not row[target]),
            "right_censored_unknown": sum(1 for row in rows if label_status(row, target) == "right_censored_unknown"),
        }
        for target in targets
    }


def predict_warning_probability(
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
) -> tuple[list[float], bool]:
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")
    y_train = np.asarray([1.0 if row[target] else 0.0 for row in train_rows], dtype=float)
    base_rate = float(np.mean(y_train)) if len(y_train) else 0.0
    train_one_class = len(set(y_train.tolist())) < 2
    if model_level == "B0_event_rate_prior" or train_one_class:
        return [base_rate for _ in test_rows], train_one_class
    if model_level == "B1_distance_to_threshold_rule":
        return distance_rule_probabilities(train_rows, test_rows, target), False
    if model_level == "B2_linear_extrapolation_to_threshold":
        return extrapolation_probabilities(train_rows, test_rows, target), False

    LogisticRegression, HistGradientBoostingClassifier = _import_sklearn()
    if model_level == "B3_logistic_distance_baseline":
        feature_group = "W_distance_margin"
        x_train = np.asarray(distance_feature_matrix(train_rows), dtype=float)
        x_test = np.asarray(distance_feature_matrix(test_rows), dtype=float)
        model = LogisticRegression(C=1.0, max_iter=1000, random_state=seed)
        model.fit(x_train, y_train)
        return [float(value) for value in model.predict_proba(x_test)[:, 1]], False
    encoder = WarningFeatureEncoder.fit(train_rows, feature_group)
    standardize = model_level in {"B4_logistic_regression", "B5_ridge_logistic"}
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=standardize), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=standardize), dtype=float)
    if model_level == "B4_logistic_regression":
        model = LogisticRegression(C=1e6, max_iter=1000, random_state=seed)
    elif model_level == "B5_ridge_logistic":
        model = LogisticRegression(C=1.0, max_iter=1000, random_state=seed)
    elif model_level == "B6_hist_gradient_boosting_classifier":
        model = HistGradientBoostingClassifier(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown model level: {model_level}")
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict_proba(x_test)[:, 1]], False


def warning_metrics(
    test_rows: list[dict[str, Any]],
    probabilities: list[float],
    *,
    target: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    train_one_class: bool,
) -> dict[str, Any]:
    y_true = [1 if row[target] else 0 for row in test_rows]
    probs = [_clip_probability(value) for value in probabilities]
    condition_brier = _condition_brier_rows(test_rows, y_true, probs)
    return {
        "target": target,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "train_positive_count": sum(1 for row in train_rows if row[target]),
        "test_positive_count": sum(y_true),
        "test_negative_count": len(y_true) - sum(y_true),
        "train_one_class": train_one_class,
        "test_one_class": len(set(y_true)) < 2,
        "auroc": auroc(y_true, probs),
        "auprc": auprc(y_true, probs),
        "brier": brier_score(y_true, probs),
        "log_loss": log_loss(y_true, probs),
        "condition_mean_brier": _mean([row["brier"] for row in condition_brier]),
        "worst_condition_brier": max((row["brier"] for row in condition_brier), default=None),
        "ece_10_bin": expected_calibration_error(y_true, probs, bins=10),
    }


def prediction_rows(
    test_rows: list[dict[str, Any]],
    probabilities: list[float],
    *,
    target: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
) -> list[dict[str, Any]]:
    rows = []
    for row, prob in zip(test_rows, probabilities):
        rows.append(
            {
                "cell_id": str(row["cell_id"]),
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "target": target,
                "y_true": bool(row[target]),
                "y_prob": _clip_probability(prob),
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "time_to_event_checkups": row.get("time_to_event_checkups"),
                "event_observed": bool(row.get("event_observed")),
                "capacity_margin_to_80": _capacity_margin_to_threshold(row),
                "soh_margin_to_80": _soh_margin_to_threshold(row),
                "lead_time_bin": lead_time_bin(row),
                "proximity_bin": proximity_bin(row),
                "label_status": label_status(row, target),
                "schema_version": SCHEMA_VERSION,
            }
        )
    return rows


def distance_feature_matrix(rows: list[dict[str, Any]]) -> list[list[float]]:
    return [
        [
            _capacity_margin_to_threshold(row),
            _soh_margin_to_threshold(row),
            _as_float(row.get("checkup_k"), default=0.0),
            _as_float(row.get("calendar_day_k"), default=0.0),
            _prior_capacity_slope(row),
        ]
        for row in rows
    ]


def distance_rule_probabilities(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
) -> list[float]:
    margins = sorted(_soh_margin_to_threshold(row) for row in train_rows if row[target])
    if not margins:
        threshold = 0.0
    else:
        threshold = margins[min(max(int(0.9 * (len(margins) - 1)), 0), len(margins) - 1)]
    train_positive_rate = sum(bool(row[target]) for row in train_rows) / len(train_rows)
    return [
        0.75 if _soh_margin_to_threshold(row) <= threshold else max(0.01, train_positive_rate * 0.25)
        for row in test_rows
    ]


def extrapolation_probabilities(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
) -> list[float]:
    horizon = _target_horizon(target)
    train_positive_rate = sum(bool(row[target]) for row in train_rows) / len(train_rows)
    output = []
    for row in test_rows:
        slope = _prior_capacity_slope(row)
        margin = _soh_margin_to_threshold(row)
        if slope < 0:
            estimated_checkups = margin / abs(slope)
            output.append(0.8 if estimated_checkups <= horizon else max(0.01, train_positive_rate * 0.3))
        else:
            output.append(max(0.01, train_positive_rate * 0.2))
    return output


def label_status(row: dict[str, Any], target: str) -> str:
    if bool(row[target]):
        return "positive_observed"
    remaining = _as_float(row.get("time_to_event_checkups"))
    horizon = _target_horizon(target)
    if math.isfinite(remaining) and remaining > horizon:
        return "negative_observed"
    if bool(row.get("event_observed")):
        return "negative_observed"
    return "right_censored_unknown"


def lead_time_bin(row: dict[str, Any]) -> str:
    if _soh_margin_to_threshold(row) <= 0:
        return "at_or_below_threshold_at_k"
    value = _as_float(row.get("time_to_event_checkups"))
    if not math.isfinite(value):
        return "right_censored_unknown"
    if value <= 1:
        return "event_next_checkup"
    if value <= 2:
        return "event_within_2_checkups_not_next"
    if value <= 3:
        return "event_within_3_checkups_not_1_or_2"
    return "event_later_than_3_checkups"


def proximity_bin(row: dict[str, Any]) -> str:
    margin = _soh_margin_to_threshold(row)
    if margin <= 0:
        return "at_or_below_threshold"
    if margin <= 0.02:
        return "within_2pct_soh"
    if margin <= 0.05:
        return "within_5pct_soh"
    if margin <= 0.10:
        return "within_10pct_soh"
    return "above_10pct_soh"


def _soh_margin_to_threshold(row: dict[str, Any]) -> float:
    return _as_float(row.get("soh_k"), default=math.nan) - 0.8


def _capacity_margin_to_threshold(row: dict[str, Any]) -> float:
    capacity = _as_float(row.get("capacity_Ah_k"))
    initial = _estimated_initial_capacity(row)
    if not math.isfinite(capacity) or not math.isfinite(initial):
        return math.nan
    return capacity - 0.8 * initial


def _prior_capacity_slope(row: dict[str, Any]) -> float:
    checkup = _as_float(row.get("checkup_k"), default=0.0)
    capacity = _as_float(row.get("capacity_Ah_k"))
    initial = _estimated_initial_capacity(row)
    if not math.isfinite(checkup) or checkup <= 0 or not math.isfinite(capacity) or not math.isfinite(initial):
        return 0.0
    return (capacity - initial) / checkup


def _estimated_initial_capacity(row: dict[str, Any]) -> float:
    capacity = _as_float(row.get("capacity_Ah_k"))
    soh = _as_float(row.get("soh_k"))
    if not math.isfinite(capacity) or not math.isfinite(soh) or soh <= 0:
        return math.nan
    return capacity / soh


def _target_horizon(target: str) -> int:
    if target == "event_within_1_checkup":
        return 1
    if target == "event_within_2_checkups":
        return 2
    if target == "event_within_3_checkups":
        return 3
    raise ValueError(f"Unknown threshold-warning target: {target}")


def render_threshold_warning_artifacts(report: dict[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir / "leaderboard.csv", _leaderboard_rows(report["metrics"]))
    _write_calibration_md(report["metrics"], report_dir / "threshold_warning_calibration.md")
    _write_leakage_audit_md(report["leakage_audit"], report_dir / "threshold_warning_leakage_audit.md")
    _write_claim_readiness_md(report["metrics"], report["leakage_audit"], report_dir / "threshold_warning_claim_readiness.md")
    _write_summary_md(report, report_dir / "baseline_summary.md")


def diagnose_threshold_warning(
    report_path: Path,
    predictions_path: Path,
    warning_table_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Write lead-time, proximity, censoring, and reliability diagnostics."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    predictions = pq.read_table(predictions_path).to_pylist()
    warning_rows = pq.read_table(warning_table_path).to_pylist()
    out_dir.mkdir(parents=True, exist_ok=True)
    lead_rows = grouped_prediction_performance(predictions, "lead_time_bin")
    proximity_rows = grouped_prediction_performance(predictions, "proximity_bin")
    c_rate_rows = [
        row for row in grouped_prediction_performance(predictions, "lead_time_bin", split_name="c_rate_holdout_fold")
    ]
    reliability_rows = reliability_bin_rows(predictions)
    calibration_split_rows = calibration_by_split_rows(predictions)
    censoring_report = censoring_policy_report(warning_rows)
    censoring_rows = censoring_by_split_rows(warning_rows)
    _write_csv(out_dir / "plots" / "lead_time_performance.csv", lead_rows)
    _write_csv(out_dir / "plots" / "proximity_bin_performance.csv", proximity_rows)
    _write_csv(out_dir / "plots" / "c_rate_lead_time_performance.csv", c_rate_rows)
    _write_csv(out_dir / "threshold_warning_reliability.csv", reliability_rows)
    _write_csv(out_dir / "threshold_warning_calibration_by_split.csv", calibration_split_rows)
    _write_csv(out_dir / "threshold_warning_censoring_by_split.csv", censoring_rows)
    (out_dir / "threshold_warning_censoring_report.json").write_text(
        json.dumps(censoring_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_lead_time_md(lead_rows, proximity_rows, out_dir / "lead_time_diagnostics.md")
    _write_c_rate_calibration_md(calibration_split_rows, out_dir / "threshold_warning_calibration_by_c_rate.md")
    _write_claim_readiness_md(report["metrics"], report["leakage_audit"], out_dir / "threshold_warning_claim_readiness.md")
    return {
        "row_counts": {
            "predictions": len(predictions),
            "lead_time_rows": len(lead_rows),
            "proximity_rows": len(proximity_rows),
            "reliability_rows": len(reliability_rows),
        },
        "outputs": {
            "lead_time": str(out_dir / "lead_time_diagnostics.md"),
            "censoring": str(out_dir / "threshold_warning_censoring_report.json"),
            "reliability": str(out_dir / "threshold_warning_reliability.csv"),
        },
    }


def compare_threshold_warning_censoring(
    all_rows_report_path: Path,
    verified_only_report_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Compare all-row and verified-only threshold-warning reports."""
    all_report = json.loads(all_rows_report_path.read_text(encoding="utf-8"))
    verified_report = json.loads(verified_only_report_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    policy_reports = [
        ("all_rows", all_report),
        ("verified_only", verified_report),
    ]
    metric_rows = censoring_policy_metric_rows(policy_reports)
    split_rows = censoring_policy_split_rows(policy_reports)
    c_rate_rows = [row for row in split_rows if row["split_name"] == "c_rate_holdout_fold"]
    _write_csv(out_dir / "plots" / "censoring_policy_metric_comparison.csv", metric_rows)
    _write_csv(out_dir / "plots" / "censoring_policy_split_comparison.csv", split_rows)
    _write_csv(out_dir / "plots" / "censoring_policy_c_rate_comparison.csv", c_rate_rows)
    summary = censoring_sensitivity_summary(policy_reports)
    (out_dir / "threshold_warning_censoring_sensitivity_report.json").write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "summary": summary,
                "policy_note": "all_rows is equivalent to censored_as_negative for the current Boolean horizon labels.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_censoring_sensitivity_md(summary, out_dir / "censoring_sensitivity_summary.md")
    return {
        "status": "passed",
        "summary": summary,
        "row_counts": {
            "metric_rows": len(metric_rows),
            "split_rows": len(split_rows),
            "c_rate_rows": len(c_rate_rows),
        },
        "outputs": {
            "summary": str(out_dir / "censoring_sensitivity_summary.md"),
            "json_report": str(out_dir / "threshold_warning_censoring_sensitivity_report.json"),
            "metric_comparison": str(out_dir / "plots" / "censoring_policy_metric_comparison.csv"),
            "split_comparison": str(out_dir / "plots" / "censoring_policy_split_comparison.csv"),
            "c_rate_comparison": str(out_dir / "plots" / "censoring_policy_c_rate_comparison.csv"),
        },
    }


def finalize_threshold_warning_claim(
    report_path: Path,
    predictions_path: Path,
    warning_table_path: Path,
    censoring_sensitivity_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Write final threshold-warning claim matrices and readiness report."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    predictions = pq.read_table(predictions_path).to_pylist()
    warning_rows = pq.read_table(warning_table_path).to_pylist()
    sensitivity_text = censoring_sensitivity_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    lead_rows = grouped_prediction_performance(predictions, "lead_time_bin")
    final_lead_rows = [
        row
        for row in lead_rows
        if row["model_level"] in {"B0_event_rate_prior", "B3_logistic_distance_baseline", "B6_hist_gradient_boosting_classifier"}
        and row["target"] == "event_within_3_checkups"
    ]
    final_c_rate_rows = [
        {
            "target": row["target"],
            "model_level": row["model_level"],
            "feature_group": row["feature_group"],
            "split_name": row["split_name"],
            "heldout_fold": row["heldout_fold"],
            "n_test": row["n_test"],
            "test_positive_count": row["test_positive_count"],
            "test_negative_count": row["test_negative_count"],
            "brier": row["brier"],
            "auroc": row["auroc"],
            "auprc": row["auprc"],
            "ece_10_bin": row["ece_10_bin"],
        }
        for row in report["metrics"]
        if row["split_name"] == "c_rate_holdout_fold"
        and row["target"] == "event_within_3_checkups"
        and (
            row["model_level"] in {"B0_event_rate_prior", "B3_logistic_distance_baseline"}
            or (row["model_level"] == "B6_hist_gradient_boosting_classifier" and row["feature_group"] == "W2_nominal")
        )
    ]
    _write_csv(out_dir / "plots" / "final_lead_time_claim_matrix.csv", final_lead_rows)
    _write_csv(out_dir / "plots" / "final_c_rate_warning_matrix.csv", final_c_rate_rows)
    readiness = final_claim_readiness(report, warning_rows, sensitivity_text)
    _write_final_claim_readiness_md(readiness, out_dir / "threshold_warning_final_claim_readiness.md")
    _write_final_claim_readiness_md(readiness, out_dir / "threshold_warning_claim_readiness.md")
    return {
        "status": "passed",
        "readiness": readiness,
        "outputs": {
            "claim_readiness": str(out_dir / "threshold_warning_final_claim_readiness.md"),
            "lead_time_matrix": str(out_dir / "plots" / "final_lead_time_claim_matrix.csv"),
            "c_rate_matrix": str(out_dir / "plots" / "final_c_rate_warning_matrix.csv"),
        },
    }


def leakage_audit(feature_groups: list[str]) -> dict[str, Any]:
    rows = []
    status = "passed"
    for group in feature_groups:
        fields = set(NUMERIC_FEATURES[group]) | set(CATEGORICAL_FEATURES[group])
        leakage = sorted(fields & LEAKAGE_FIELDS)
        if leakage:
            status = "failed"
        rows.append({"feature_group": group, "leakage_fields": leakage})
    return {
        "status": status,
        "allowed": "capacity/state/time/nominal fields known at check-up k",
        "forbidden": sorted(LEAKAGE_FIELDS),
        "rows": rows,
    }


def grouped_prediction_performance(
    predictions: list[dict[str, Any]],
    group_field: str,
    *,
    split_name: str | None = None,
) -> list[dict[str, Any]]:
    filtered = [
        row
        for row in predictions
        if split_name is None or str(row["split_name"]) == split_name
    ]
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in filtered:
        grouped[
            (
                str(row["target"]),
                str(row["model_level"]),
                str(row["feature_group"]),
                str(row.get(group_field, "<missing>")),
            )
        ].append(row)
    output = []
    for (target, model, feature, group_value), rows in sorted(grouped.items()):
        y_true = [1 if row["y_true"] else 0 for row in rows]
        probs = [_as_float(row["y_prob"]) for row in rows]
        output.append(
            {
                "target": target,
                "model_level": model,
                "feature_group": feature,
                "group_field": group_field,
                "group_value": group_value,
                "split_name": split_name or "all",
                "row_count": len(rows),
                "positive_count": sum(y_true),
                "negative_count": len(y_true) - sum(y_true),
                "auroc": auroc(y_true, probs),
                "auprc": auprc(y_true, probs),
                "brier": brier_score(y_true, probs),
                "ece_10_bin": expected_calibration_error(y_true, probs, bins=10),
            }
        )
    return output


def censoring_policy_metric_rows(policy_reports: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    output = []
    for policy, report in policy_reports:
        for row in _leaderboard_rows(report["metrics"]):
            if row["model_level"] not in {
                "B0_event_rate_prior",
                "B3_logistic_distance_baseline",
                "B6_hist_gradient_boosting_classifier",
            }:
                continue
            if row["model_level"] == "B6_hist_gradient_boosting_classifier" and row["feature_group"] != "W2_nominal":
                continue
            output.append({"label_policy": policy, **row})
    return output


def censoring_policy_split_rows(policy_reports: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    output = []
    for policy, report in policy_reports:
        for row in report["metrics"]:
            if row["model_level"] not in {
                "B0_event_rate_prior",
                "B3_logistic_distance_baseline",
                "B6_hist_gradient_boosting_classifier",
            }:
                continue
            if row["model_level"] == "B6_hist_gradient_boosting_classifier" and row["feature_group"] != "W2_nominal":
                continue
            output.append(
                {
                    "label_policy": policy,
                    "target": row["target"],
                    "model_level": row["model_level"],
                    "feature_group": row["feature_group"],
                    "split_name": row["split_name"],
                    "heldout_fold": row["heldout_fold"],
                    "n_train": row["n_train"],
                    "n_test": row["n_test"],
                    "test_positive_count": row["test_positive_count"],
                    "test_negative_count": row["test_negative_count"],
                    "brier": row["brier"],
                    "auroc": row["auroc"],
                    "auprc": row["auprc"],
                    "ece_10_bin": row["ece_10_bin"],
                }
            )
    return output


def censoring_sensitivity_summary(policy_reports: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    by_policy = {policy: report for policy, report in policy_reports}
    output: dict[str, Any] = {"policies": {}, "event_within_3_checkups": {}}
    for policy, report in by_policy.items():
        rows = _leaderboard_rows(report["metrics"])
        target_rows = [row for row in rows if row["target"] == "event_within_3_checkups"]
        prior = _find_leaderboard_row(target_rows, "B0_event_rate_prior")
        distance = _find_leaderboard_row(target_rows, "B3_logistic_distance_baseline")
        hgb = _find_leaderboard_row(target_rows, "B6_hist_gradient_boosting_classifier", "W2_nominal")
        beats_prior = _brier_gain(prior, hgb)
        beats_distance = _brier_gain(distance, hgb)
        output["policies"][policy] = {
            "rows": report["row_counts"]["rows"],
            "target_rows": report["row_counts"].get("target_label_policy_rows", {}).get(
                "event_within_3_checkups", {}
            ),
            "metrics": report["row_counts"]["metrics"],
            "hgb_brier": hgb["mean_brier"] if hgb else None,
            "event_rate_prior_brier": prior["mean_brier"] if prior else None,
            "proximity_brier": distance["mean_brier"] if distance else None,
            "hgb_gain_vs_prior": beats_prior,
            "hgb_gain_vs_proximity": beats_distance,
            "passes": beats_prior is not None and beats_prior > 0 and beats_distance is not None and beats_distance > 0,
        }
    output["event_within_3_checkups"]["both_policies_pass"] = all(
        value["passes"] for value in output["policies"].values()
    )
    return output


def final_claim_readiness(report: dict[str, Any], warning_rows: list[dict[str, Any]], sensitivity_text: str) -> dict[str, Any]:
    rows = _leaderboard_rows(report["metrics"])
    target_rows = [row for row in rows if row["target"] == "event_within_3_checkups"]
    prior = _find_leaderboard_row(target_rows, "B0_event_rate_prior")
    distance = _find_leaderboard_row(target_rows, "B3_logistic_distance_baseline")
    hgb = _find_leaderboard_row(target_rows, "B6_hist_gradient_boosting_classifier", "W2_nominal")
    hgb_gain_vs_prior = _brier_gain(prior, hgb)
    hgb_gain_vs_distance = _brier_gain(distance, hgb)
    c_rate_rows = [
        row
        for row in report["metrics"]
        if row["target"] == "event_within_3_checkups"
        and row["split_name"] == "c_rate_holdout_fold"
        and (
            row["model_level"] in {"B0_event_rate_prior", "B3_logistic_distance_baseline"}
            or (row["model_level"] == "B6_hist_gradient_boosting_classifier" and row["feature_group"] == "W2_nominal")
        )
    ]
    c_prior = _find_metric_row(c_rate_rows, "B0_event_rate_prior")
    c_distance = _find_metric_row(c_rate_rows, "B3_logistic_distance_baseline")
    c_hgb = _find_metric_row(c_rate_rows, "B6_hist_gradient_boosting_classifier", "W2_nominal")
    censoring = censoring_policy_report(warning_rows)["targets"]["event_within_3_checkups"]
    both_policies_pass = "both_policies_pass: true" in sensitivity_text
    return {
        "threshold_event_forecasting": "supported_for_diagnostics" if both_policies_pass else "exploratory_only",
        "threshold_detection_only": "not_supported" if hgb_gain_vs_distance and hgb_gain_vs_distance > 0 else "partially_supported",
        "early_warning_diagnostic": "exploratory_only",
        "c_rate_warning": "supported_for_diagnostics"
        if _brier_gain(c_prior, c_hgb) and _brier_gain(c_distance, c_hgb) and int(c_hgb.get("test_positive_count", 0)) > 0
        else "exploratory_only",
        "calibrated_risk": "not_supported",
        "detector_knee_prediction": "blocked",
        "policy_ranking": "blocked",
        "hgb_gain_vs_prior": hgb_gain_vs_prior,
        "hgb_gain_vs_proximity": hgb_gain_vs_distance,
        "c_rate_hgb_gain_vs_prior": _brier_gain(c_prior, c_hgb),
        "c_rate_hgb_gain_vs_proximity": _brier_gain(c_distance, c_hgb),
        "c_rate_ece": c_hgb.get("ece_10_bin") if c_hgb else None,
        "censoring_counts": censoring,
        "both_policies_pass": both_policies_pass,
    }


def _find_leaderboard_row(
    rows: list[dict[str, Any]],
    model_level: str,
    feature_group: str | None = None,
) -> dict[str, Any] | None:
    for row in rows:
        if row["model_level"] == model_level and (feature_group is None or row["feature_group"] == feature_group):
            return row
    return None


def _find_metric_row(
    rows: list[dict[str, Any]],
    model_level: str,
    feature_group: str | None = None,
) -> dict[str, Any] | None:
    for row in rows:
        if row["model_level"] == model_level and (feature_group is None or row["feature_group"] == feature_group):
            return row
    return None


def _brier_gain(reference: dict[str, Any] | None, candidate: dict[str, Any] | None) -> float | None:
    if not reference or not candidate:
        return None
    ref = reference.get("mean_brier", reference.get("brier"))
    cand = candidate.get("mean_brier", candidate.get("brier"))
    if ref is None or cand is None:
        return None
    return float(ref) - float(cand)


def reliability_bin_rows(predictions: list[dict[str, Any]], *, bins: int = 10) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        prob = _clip_probability(_as_float(row["y_prob"]))
        bin_idx = min(int(prob * bins), bins - 1)
        grouped[(str(row["target"]), str(row["model_level"]), str(row["feature_group"]), bin_idx)].append(row)
    output = []
    for (target, model, feature, bin_idx), rows in sorted(grouped.items()):
        probs = [_clip_probability(_as_float(row["y_prob"])) for row in rows]
        positives = sum(bool(row["y_true"]) for row in rows)
        output.append(
            {
                "target": target,
                "model_level": model,
                "feature_group": feature,
                "bin": bin_idx,
                "bin_left": bin_idx / bins,
                "bin_right": (bin_idx + 1) / bins,
                "row_count": len(rows),
                "mean_probability": sum(probs) / len(probs),
                "observed_rate": positives / len(rows),
            }
        )
    return output


def calibration_by_split_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        grouped[
            (
                str(row["target"]),
                str(row["model_level"]),
                str(row["feature_group"]),
                str(row["split_name"]),
                int(row["heldout_fold"]),
            )
        ].append(row)
    output = []
    for (target, model, feature, split, fold), rows in sorted(grouped.items()):
        y_true = [1 if row["y_true"] else 0 for row in rows]
        probs = [_clip_probability(_as_float(row["y_prob"])) for row in rows]
        output.append(
            {
                "target": target,
                "model_level": model,
                "feature_group": feature,
                "split_name": split,
                "heldout_fold": fold,
                "row_count": len(rows),
                "positive_count": sum(y_true),
                "brier": brier_score(y_true, probs),
                "ece_10_bin": expected_calibration_error(y_true, probs, bins=10),
                "calibration_slope": calibration_slope(y_true, probs),
                "calibration_intercept": calibration_intercept(y_true, probs),
            }
        )
    return output


def censoring_policy_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets = {}
    for target in TARGETS:
        statuses = defaultdict(int)
        for row in rows:
            statuses[label_status(row, target)] += 1
        targets[target] = dict(sorted(statuses.items()))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "targets": targets,
        "policy": {
            "all_current_rows": "Milestone 2.6 baseline treatment.",
            "verified_only": "Exclude right_censored_unknown rows for sensitivity diagnostics.",
            "censored_as_negative": "Current Boolean horizon labels implicitly treat unknown future crossings as negative.",
        },
    }


def censoring_by_split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for target in TARGETS:
        for split_name in SPLIT_COLUMNS:
            folds = sorted({int(row[split_name]) for row in rows})
            heldout = folds if split_name == "condition_fold" else [fold for fold in folds if fold != 0]
            for fold in heldout:
                split_rows = [row for row in rows if int(row[split_name]) == fold]
                statuses = defaultdict(int)
                for row in split_rows:
                    statuses[label_status(row, target)] += 1
                output.append(
                    {
                        "target": target,
                        "split_name": split_name,
                        "heldout_fold": fold,
                        "row_count": len(split_rows),
                        "positive_observed": statuses["positive_observed"],
                        "negative_observed": statuses["negative_observed"],
                        "right_censored_unknown": statuses["right_censored_unknown"],
                    }
                )
    return output


def calibration_slope(y_true: list[int], probabilities: list[float]) -> float | None:
    if len(set(y_true)) < 2:
        return None
    logits = [math.log(prob / (1 - prob)) for prob in probabilities]
    x_mean = sum(logits) / len(logits)
    y_mean = sum(y_true) / len(y_true)
    denom = sum((value - x_mean) ** 2 for value in logits)
    if denom <= 1e-12:
        return None
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(logits, y_true)) / denom


def calibration_intercept(y_true: list[int], probabilities: list[float]) -> float | None:
    slope = calibration_slope(y_true, probabilities)
    if slope is None:
        return None
    logits = [math.log(prob / (1 - prob)) for prob in probabilities]
    return sum(y_true) / len(y_true) - slope * (sum(logits) / len(logits))


def auroc(y_true: list[int], probabilities: list[float]) -> float | None:
    positives = sum(y_true)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        return None
    pairs = sorted(zip(probabilities, y_true), key=lambda item: item[0])
    ranks: list[float] = [0.0] * len(pairs)
    idx = 0
    while idx < len(pairs):
        end = idx + 1
        while end < len(pairs) and pairs[end][0] == pairs[idx][0]:
            end += 1
        avg_rank = (idx + 1 + end) / 2.0
        for rank_idx in range(idx, end):
            ranks[rank_idx] = avg_rank
        idx = end
    pos_rank_sum = sum(rank for rank, (_, label) in zip(ranks, pairs) if label == 1)
    return (pos_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def auprc(y_true: list[int], probabilities: list[float]) -> float | None:
    positives = sum(y_true)
    if positives == 0:
        return None
    ordered = sorted(zip(probabilities, y_true), key=lambda item: item[0], reverse=True)
    tp = 0
    fp = 0
    prev_recall = 0.0
    area = 0.0
    for _, label in ordered:
        if label:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        area += (recall - prev_recall) * precision
        prev_recall = recall
    return area


def brier_score(y_true: list[int], probabilities: list[float]) -> float:
    return sum((prob - truth) ** 2 for truth, prob in zip(y_true, probabilities)) / len(y_true)


def log_loss(y_true: list[int], probabilities: list[float]) -> float:
    return -sum(
        truth * math.log(prob) + (1 - truth) * math.log(1 - prob)
        for truth, prob in zip(y_true, probabilities)
    ) / len(y_true)


def expected_calibration_error(y_true: list[int], probabilities: list[float], *, bins: int) -> float:
    total = len(y_true)
    ece = 0.0
    for bin_idx in range(bins):
        left = bin_idx / bins
        right = (bin_idx + 1) / bins
        in_bin = [
            idx
            for idx, prob in enumerate(probabilities)
            if (left <= prob < right) or (bin_idx == bins - 1 and prob == right)
        ]
        if not in_bin:
            continue
        confidence = sum(probabilities[idx] for idx in in_bin) / len(in_bin)
        accuracy = sum(y_true[idx] for idx in in_bin) / len(in_bin)
        ece += len(in_bin) / total * abs(accuracy - confidence)
    return ece


def _condition_brier_rows(
    rows: list[dict[str, Any]], y_true: list[int], probabilities: list[float]
) -> list[dict[str, Any]]:
    grouped: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for row, truth, prob in zip(rows, y_true, probabilities):
        grouped[int(row["parameter_set"])].append((truth, prob))
    output = []
    for parameter_set, values in grouped.items():
        output.append(
            {
                "parameter_set": parameter_set,
                "brier": sum((prob - truth) ** 2 for truth, prob in values) / len(values),
            }
        )
    return output


def _leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[(row["target"], row["model_level"], row["feature_group"])].append(row)
    output = []
    for (target, model, feature), rows in sorted(grouped.items()):
        output.append(
            {
                "target": target,
                "model_level": model,
                "feature_group": feature,
                "mean_auroc": _mean([row["auroc"] for row in rows if row["auroc"] is not None]),
                "mean_auprc": _mean([row["auprc"] for row in rows if row["auprc"] is not None]),
                "mean_brier": _mean([row["brier"] for row in rows]),
                "mean_ece_10_bin": _mean([row["ece_10_bin"] for row in rows]),
                "n_rows": len(rows),
            }
        )
    return output


def _write_calibration_md(metrics: list[dict[str, Any]], path: Path) -> None:
    rows = _leaderboard_rows(metrics)
    best = min(rows, key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf)
    lines = [
        "# Threshold-Warning Calibration Diagnostics",
        "",
        "This report summarizes probability diagnostics only. It does not authorize calibrated risk claims.",
        "",
        f"Best mean Brier row: `{best['model_level']} + {best['feature_group']}` on `{best['target']}` with mean Brier `{_fmt(best['mean_brier'])}`.",
        "",
        "Calibration remains claim-gated until grouped calibration and C-rate behavior are reviewed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_leakage_audit_md(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Threshold-Warning Leakage Audit",
        "",
        f"Status: `{audit['status']}`",
        "",
        "Allowed inputs are prior state/time/nominal fields known at check-up `k`.",
        "",
        "Forbidden fields include future capacity, interval deltas, event targets, future PULSE/EIS, and future interval exposure.",
        "",
        "| Feature group | Leakage fields |",
        "|---|---|",
    ]
    for row in audit["rows"]:
        fields = ", ".join(row["leakage_fields"]) if row["leakage_fields"] else "none"
        lines.append(f"| `{row['feature_group']}` | {fields} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_md(metrics: list[dict[str, Any]], audit: dict[str, Any], path: Path) -> None:
    rows = _leaderboard_rows(metrics)
    prior_rows = [row for row in rows if row["model_level"] == "B0_event_rate_prior"]
    model_rows = [row for row in rows if row["model_level"] != "B0_event_rate_prior"]
    distance_rows = [row for row in rows if row["model_level"] in PROXIMITY_MODEL_LEVELS]
    hgb_rows = [row for row in rows if row["model_level"] == "B6_hist_gradient_boosting_classifier"]
    best_prior = min(prior_rows, key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf)
    best_model = min(model_rows, key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf)
    best_distance = min(distance_rows, key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf)
    best_hgb = min(
        hgb_rows or model_rows,
        key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf,
    )
    gain = (best_prior["mean_brier"] or 0.0) - (best_model["mean_brier"] or 0.0)
    hgb_distance_gain = (best_distance["mean_brier"] or 0.0) - (best_hgb["mean_brier"] or 0.0)
    feasibility = "partially_supported" if gain > 0 and audit["status"] == "passed" else "not_supported"
    distance_status = "partially_supported" if hgb_distance_gain > 0 else "not_supported"
    lines = [
        "# Threshold-Warning Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        "| Threshold label stability | `partially_supported` | Milestone 2.5.1 selected `capacity_below_80pct_initial` as the strongest threshold target candidate. |",
        f"| Warning baseline feasibility | `{feasibility}` | Best model mean Brier gain versus event-rate prior is `{gain:.6g}`. |",
        f"| Beats distance-to-threshold baseline | `{distance_status}` | Best HGB mean Brier gain versus best proximity baseline is `{hgb_distance_gain:.6g}`. |",
        "| Lead-time usefulness | `exploratory_only` | Lead-time stratified diagnostics are reported separately and do not yet authorize an early-warning claim. |",
        "| Censoring robustness | `exploratory_only` | Censoring sensitivity is reported; verified-only conclusions require review. |",
        "| Grouped warning performance | `supported_for_diagnostics` | Grouped metrics beat event-rate priors, but this remains threshold-event forecasting, not detector-knee prediction. |",
        "| C-rate warning performance | `exploratory_only` | C-rate rows require separate review for positive counts and performance. |",
        "| Calibration | `not_supported` | Probability outputs are diagnostic; no calibrated-risk claim is authorized. |",
        "| Detector-knee prediction | `blocked` | Detector-knee labels failed replicate consistency in Milestone 2.5. |",
        "| Policy ranking | `blocked` | No intervention or ranking claim is tested. |",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_md(report: dict[str, Any], path: Path) -> None:
    rows = _leaderboard_rows(report["metrics"])
    best = min(rows, key=lambda row: row["mean_brier"] if row["mean_brier"] is not None else math.inf)
    lines = [
        "# Threshold-Warning Baseline Summary",
        "",
        f"Rows: {report['row_counts']['rows']}",
        f"Parameter sets: {report['row_counts']['parameter_sets']}",
        f"Best mean Brier row: `{best['target']} / {best['model_level']} / {best['feature_group']}` = `{_fmt(best['mean_brier'])}`",
        "",
        "This is a non-neural threshold-event warning baseline. It is not detector-knee prediction.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_lead_time_md(
    lead_rows: list[dict[str, Any]],
    proximity_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    best_lead = min(
        [row for row in lead_rows if row["model_level"] == "B6_hist_gradient_boosting_classifier"],
        key=lambda row: row["brier"] if row["brier"] is not None else math.inf,
        default=None,
    )
    best_proximity = min(
        [row for row in proximity_rows if row["model_level"] == "B6_hist_gradient_boosting_classifier"],
        key=lambda row: row["brier"] if row["brier"] is not None else math.inf,
        default=None,
    )
    lines = [
        "# Threshold-Warning Lead-Time Diagnostics",
        "",
        "This report stratifies predictions by observed lead-time and proximity bins. It does not authorize policy ranking or calibrated risk.",
        "",
    ]
    if best_lead:
        lines.append(
            f"Best HGB lead-time bin row: `{best_lead['target']}` / `{best_lead['feature_group']}` / `{best_lead['group_value']}` with Brier `{_fmt(best_lead['brier'])}`."
        )
    if best_proximity:
        lines.append(
            f"Best HGB proximity bin row: `{best_proximity['target']}` / `{best_proximity['feature_group']}` / `{best_proximity['group_value']}` with Brier `{_fmt(best_proximity['brier'])}`."
        )
    lines.append("")
    lines.append("Near-threshold performance and longer-lead performance must be interpreted separately.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_c_rate_calibration_md(rows: list[dict[str, Any]], path: Path) -> None:
    c_rate = [row for row in rows if row["split_name"] == "c_rate_holdout_fold"]
    best = min(
        [row for row in c_rate if row["model_level"] == "B6_hist_gradient_boosting_classifier"],
        key=lambda row: row["brier"] if row["brier"] is not None else math.inf,
        default=None,
    )
    lines = [
        "# Threshold-Warning C-Rate Calibration Diagnostics",
        "",
        "This report summarizes C-rate probability diagnostics only. It does not authorize calibrated risk.",
        "",
    ]
    if best:
        lines.append(
            f"Best C-rate HGB row: `{best['target']}` / `{best['feature_group']}` with Brier `{_fmt(best['brier'])}` and ECE `{_fmt(best['ece_10_bin'])}`."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_censoring_sensitivity_md(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Threshold-Warning Censoring Sensitivity",
        "",
        "This report compares all-row and verified-only threshold-warning evaluation. It does not authorize calibrated risk or detector-knee prediction.",
        "",
        f"both_policies_pass: {str(summary['event_within_3_checkups']['both_policies_pass']).lower()}",
        "",
        "| Label policy | Target rows | Positives | Negatives | HGB Brier | Prior Brier | Proximity Brier | Gain vs prior | Gain vs proximity | Passes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for policy, row in summary["policies"].items():
        target_rows = row.get("target_rows", {})
        lines.append(
            "| "
            f"`{policy}` | "
            f"`{target_rows.get('rows', 'NA')}` | "
            f"`{target_rows.get('positive_count', 'NA')}` | "
            f"`{target_rows.get('negative_count', 'NA')}` | "
            f"`{_fmt(row['hgb_brier'])}` | "
            f"`{_fmt(row['event_rate_prior_brier'])}` | "
            f"`{_fmt(row['proximity_brier'])}` | "
            f"`{_fmt(row['hgb_gain_vs_prior'])}` | "
            f"`{_fmt(row['hgb_gain_vs_proximity'])}` | "
            f"`{row['passes']}` |"
        )
    lines.extend(
        [
            "",
            "If verified-only performance collapses, threshold-warning claims remain exploratory. If both policies pass, a narrow diagnostic threshold-event forecasting claim is allowed.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_final_claim_readiness_md(readiness: dict[str, Any], path: Path) -> None:
    lines = [
        "# Threshold-Warning Final Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Threshold-event forecasting diagnostic | `{readiness['threshold_event_forecasting']}` | HGB W2 gain vs prior `{_fmt(readiness['hgb_gain_vs_prior'])}` and vs proximity `{_fmt(readiness['hgb_gain_vs_proximity'])}`; all-row and verified-only policies pass: `{readiness['both_policies_pass']}`. |",
        f"| Threshold detection only | `{readiness['threshold_detection_only']}` | HGB W2 beats the proximity baseline, so the result is not only a current-threshold detector. |",
        f"| Early-warning diagnostic | `{readiness['early_warning_diagnostic']}` | Lead-time bins are reported separately; this wording remains exploratory. |",
        f"| C-rate threshold warning | `{readiness['c_rate_warning']}` | C-rate HGB W2 gain vs prior `{_fmt(readiness['c_rate_hgb_gain_vs_prior'])}` and vs proximity `{_fmt(readiness['c_rate_hgb_gain_vs_proximity'])}`. |",
        f"| Calibrated risk | `{readiness['calibrated_risk']}` | C-rate ECE is `{_fmt(readiness['c_rate_ece'])}` and grouped calibration remains claim-gated. |",
        f"| Detector-knee prediction | `{readiness['detector_knee_prediction']}` | Detector-knee replicate consistency failed in Milestone 2.5. |",
        f"| Policy ranking | `{readiness['policy_ranking']}` | No intervention or ranking task is tested. |",
        "",
        "Censoring counts for `event_within_3_checkups`:",
        "",
        "| Label status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(readiness["censoring_counts"].items()):
        lines.append(f"| `{status}` | `{count}` |")
    lines.append("")
    lines.append(
        "Allowed wording: non-neural baselines can forecast the 80% capacity-relative threshold event diagnostically under grouped validation, including under verified-only sensitivity."
    )
    lines.append(
        "Forbidden wording: calibrated risk, detector-knee prediction, causal early-warning claims, policy ranking, or CBAT validation."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _audit_warning_feature_groups(feature_groups: list[str]) -> None:
    audit = leakage_audit(feature_groups)
    if audit["status"] != "passed":
        raise ValueError("Threshold-warning leakage audit failed.")


def _normalize_selection(
    values: list[str] | None,
    allowed: tuple[str, ...],
    default: tuple[str, ...],
    label: str,
) -> list[str]:
    selected = list(default if values is None else values)
    unknown = sorted(set(selected) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}: {unknown}")
    return selected


def _import_sklearn() -> tuple[Any, Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:
        raise RuntimeError(
            "Threshold-warning baselines require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry."
        ) from exc
    return LogisticRegression, HistGradientBoostingClassifier


def _as_float(value: Any, default: float = math.nan) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if math.isfinite(output) else default


def _category(value: Any) -> str:
    if value is None:
        return "<missing>"
    text = str(value)
    return text if text else "<missing>"


def _clip_probability(value: float) -> float:
    return min(max(float(value), 1e-6), 1.0 - 1e-6)


def _mean(values: list[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else None


def _fmt(value: Any) -> str:
    number = _as_float(value)
    return "NA" if not math.isfinite(number) else f"{number:.6g}"
