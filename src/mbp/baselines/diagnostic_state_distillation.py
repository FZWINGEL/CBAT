"""Non-neural diagnostic-state distillation baselines.

This gate tests whether train-only predictions of current PULSE/EIS diagnostic
state improve downstream capacity-horizon or threshold-warning forecasts. It is
not a multimodal architecture branch: true PULSE/EIS values are auxiliary
supervision targets only, and downstream models receive out-of-fold predicted
diagnostic-state features.
"""

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
from mbp.baselines.threshold_warning import (
    auprc,
    auroc,
    brier_score,
    expected_calibration_error,
    expected_calibration_error_equal_frequency,
    filter_rows_by_label_policy,
    log_loss,
)

SCHEMA_VERSION = "gate81.diagnostic_state_distillation.v1"
PREDICTION_SCHEMA_VERSION = "gate81.diagnostic_state_distillation_predictions.v1"

TASKS = ("capacity_horizon", "threshold_warning")
CAPACITY_TARGETS = ("capacity_Ah_kh", "delta_capacity_Ah_h")
WARNING_TARGETS = ("event_within_3_checkups",)
DEFAULT_HORIZONS = (2, 3)
MODEL_LEVELS = ("DS0_regularized_linear", "DS1_hist_gradient_boosting")
AUXILIARY_MODEL_LEVELS = ("A0_ridge", "A1_hist_gradient_boosting")
FEATURE_GROUPS = (
    "D0_capacity_state_reference",
    "D1_predicted_pulse_state",
    "D2_predicted_eis_state",
    "D3_predicted_pulse_eis_state",
)
DEFAULT_TASKS = TASKS
DEFAULT_MODELS = MODEL_LEVELS
DEFAULT_AUXILIARY_MODEL_LEVEL = "A0_ridge"
DEFAULT_FEATURE_GROUPS = FEATURE_GROUPS
DEFAULT_WARNING_LABEL_POLICY = "verified_only"
WARNING_LABEL_POLICIES = ("all_rows", "verified_only", "censored_as_negative")

PULSE_AUXILIARY_TARGETS = (
    "pulse_1s_resistance_k",
    "pulse_10ms_resistance_k",
)
EIS_AUXILIARY_TARGETS = (
    "eis_z_abs_1kHz_k",
    "eis_phase_1kHz_k",
    "nyquist_im_peak_abs_k",
    "nyquist_semicircle_width_proxy_k",
)
AUXILIARY_TARGETS = PULSE_AUXILIARY_TARGETS + EIS_AUXILIARY_TARGETS

BASE_STATE_NUMERIC_FEATURES = (
    "capacity_Ah_k",
    "soh_k",
    "checkup_k",
    "calendar_day_k",
    "cumulative_efc_k",
    "nominal_temperature_C",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
)
BASE_STATE_CATEGORICAL_FEATURES = ("voltage_window_family", "profile_label", "aging_mode")

CAPACITY_BASE_NUMERIC_FEATURES = (
    "capacity_Ah_k",
    "soh_k",
    "horizon_checkups",
    "checkup_k",
    "calendar_day_k",
    "cumulative_efc_k",
    "cumulative_q_Ah_k",
    "prior_delta_capacity_Ah",
    "prior_capacity_slope_per_day",
    "nominal_temperature_C",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
)
WARNING_BASE_NUMERIC_FEATURES = (
    "capacity_Ah_k",
    "soh_k",
    "checkup_k",
    "calendar_day_k",
    "cumulative_efc_k",
    "nominal_temperature_C",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
)

FORBIDDEN_FEATURE_FIELDS = {
    "capacity_Ah_k1",
    "delta_capacity_Ah",
    "capacity_Ah_kh",
    "delta_capacity_Ah_h",
    "event_checkup_k",
    "time_to_event_checkups",
    "event_within_1_checkup",
    "event_within_2_checkups",
    "event_within_3_checkups",
    "horizon_interval_count",
    "horizon_duration_h",
    "horizon_calendar_days",
    "horizon_log_age_efc_delta",
    "horizon_log_age_delta_q_Ah",
    "horizon_log_age_row_count",
}

FORBIDDEN_AUXILIARY_FIELDS = {
    "pulse_1s_resistance_k1",
    "pulse_10ms_resistance_k1",
    "delta_pulse_1s_resistance",
    "delta_pulse_10ms_resistance",
    "eis_z_real_1kHz_k1",
    "eis_z_imag_1kHz_k1",
    "eis_z_abs_1kHz_k1",
    "eis_phase_1kHz_k1",
    "delta_eis_z_real_1kHz",
    "delta_eis_z_imag_1kHz",
    "delta_eis_z_abs_1kHz",
    "delta_eis_phase_1kHz",
    "nyquist_re_min_k1",
    "nyquist_re_max_k1",
    "nyquist_im_peak_abs_k1",
    "nyquist_semicircle_width_proxy_k1",
}

DIAGNOSTIC_STATE_PREDICTION_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("task", pa.string()),
        ("split_name", pa.string()),
        ("heldout_fold", pa.int32()),
        ("model_level", pa.string()),
        ("feature_group", pa.string()),
        ("target", pa.string()),
        ("cell_id", pa.string()),
        ("parameter_set", pa.int32()),
        ("replicate_id", pa.int32()),
        ("checkup_k", pa.int32()),
        ("target_checkup_k", pa.int32()),
        ("horizon_checkups", pa.int32()),
        ("y_true", pa.float64()),
        ("y_pred", pa.float64()),
    ]
)


@dataclass(frozen=True)
class DiagnosticFeatureEncoder:
    """Small numeric/categorical encoder shared by stage-A and stage-B models."""

    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    numeric_scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(
        cls,
        rows: list[dict[str, Any]],
        *,
        numeric_columns: tuple[str, ...],
        categorical_columns: tuple[str, ...],
    ) -> "DiagnosticFeatureEncoder":
        leakage = (set(numeric_columns) | set(categorical_columns)) & FORBIDDEN_FEATURE_FIELDS
        leakage |= (set(numeric_columns) | set(categorical_columns)) & FORBIDDEN_AUXILIARY_FIELDS
        if leakage:
            raise ValueError(f"Diagnostic-state feature set includes leakage fields: {sorted(leakage)}")
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
        return cls(numeric_columns, categorical_columns, impute, scale, categories)

    def transform(self, rows: list[dict[str, Any]], *, standardize_numeric: bool = False) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                observed = _as_float(row.get(column))
                numeric = observed if math.isfinite(observed) else self.numeric_impute_values[column]
                if standardize_numeric:
                    numeric = (numeric - self.numeric_impute_values[column]) / self.numeric_scale_values[column]
                values.append(numeric)
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(1.0 if observed == category else 0.0 for category in self.categorical_values[column])
            matrix.append(values)
        return matrix


@dataclass(frozen=True)
class StageAAuxiliaryResult:
    train_rows: list[dict[str, Any]]
    test_rows: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    prediction_modes: dict[str, dict[str, int]]


def run_diagnostic_state_distillation(
    capacity_horizon_table_path: Path,
    threshold_warning_table_path: Path,
    pulse_target_table_path: Path,
    eis_target_table_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    out_dir: Path | None = None,
    *,
    seed: int = 42,
    hgb_max_iter: int = 50,
    tasks: list[str] | None = None,
    capacity_targets: list[str] | None = None,
    warning_targets: list[str] | None = None,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    split_views: list[str] | None = None,
    horizons: list[int] | None = None,
    warning_label_policy: str = DEFAULT_WARNING_LABEL_POLICY,
    inner_folds: int = 5,
    auxiliary_model_level: str = DEFAULT_AUXILIARY_MODEL_LEVEL,
) -> dict[str, Any]:
    """Run the Milestone 8.1 non-neural diagnostic-state distillation gate."""

    selected_tasks = _normalize_selection(tasks, TASKS, DEFAULT_TASKS, "task")
    selected_capacity_targets = _normalize_selection(
        capacity_targets,
        CAPACITY_TARGETS,
        CAPACITY_TARGETS,
        "capacity target",
    )
    selected_warning_targets = _normalize_selection(
        warning_targets,
        WARNING_TARGETS,
        WARNING_TARGETS,
        "warning target",
    )
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, DEFAULT_MODELS, "model level")
    selected_features = _normalize_selection(feature_groups, FEATURE_GROUPS, DEFAULT_FEATURE_GROUPS, "feature group")
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, SPLIT_COLUMNS, "split view")
    selected_horizons = _normalize_horizons(horizons)
    if warning_label_policy not in WARNING_LABEL_POLICIES:
        raise ValueError(f"Unknown warning label policy: {warning_label_policy}")
    if auxiliary_model_level not in AUXILIARY_MODEL_LEVELS:
        raise ValueError(f"Unknown auxiliary model level: {auxiliary_model_level}")
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    if inner_folds <= 1:
        raise ValueError("inner_folds must be greater than one.")
    _import_sklearn_stack()
    audit = leakage_audit(selected_features)
    if audit["status"] != "passed":
        raise ValueError(f"Diagnostic-state leakage audit failed: {audit}")

    pulse_rows = pq.read_table(pulse_target_table_path).to_pylist()
    eis_rows = pq.read_table(eis_target_table_path).to_pylist()
    auxiliary_by_key = _auxiliary_by_base_key(pulse_rows, eis_rows)
    capacity_rows: list[dict[str, Any]] = []
    warning_rows: list[dict[str, Any]] = []
    if "capacity_horizon" in selected_tasks:
        capacity_rows = [
            _with_auxiliary_values(row, auxiliary_by_key)
            for row in pq.read_table(capacity_horizon_table_path).to_pylist()
            if int(row["horizon_checkups"]) in set(selected_horizons)
        ]
        if not capacity_rows:
            raise ValueError("Capacity horizon table has no rows for the selected horizons.")
    if "threshold_warning" in selected_tasks:
        warning_rows = [
            _with_auxiliary_values(row, auxiliary_by_key)
            for row in pq.read_table(threshold_warning_table_path).to_pylist()
        ]
        if not warning_rows:
            raise ValueError("Threshold-warning table is empty.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    stage_a_metrics: list[dict[str, Any]] = []
    stage_a_mode_counts: list[dict[str, Any]] = []

    if capacity_rows:
        for split_name in selected_splits:
            for heldout_fold, train_rows, test_rows in iter_split_instances(capacity_rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                stage_a = stage_a_auxiliary_predictions(
                    train_rows,
                    test_rows,
                    task="capacity_horizon",
                    split_name=split_name,
                    heldout_fold=heldout_fold,
                    seed=seed,
                    hgb_max_iter=hgb_max_iter,
                    inner_folds=inner_folds,
                    auxiliary_model_level=auxiliary_model_level,
                )
                stage_a_metrics.extend(stage_a.metrics)
                stage_a_mode_counts.extend(
                    _stage_a_mode_count_rows(
                        stage_a.prediction_modes,
                        task="capacity_horizon",
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                    )
                )
                for horizon in selected_horizons:
                    horizon_train = [row for row in stage_a.train_rows if int(row["horizon_checkups"]) == horizon]
                    horizon_test = [row for row in stage_a.test_rows if int(row["horizon_checkups"]) == horizon]
                    if not horizon_train or not horizon_test:
                        continue
                    for target in selected_capacity_targets:
                        for model_level in selected_models:
                            for feature_group in selected_features:
                                y_pred = predict_distilled_capacity(
                                    model_level,
                                    feature_group,
                                    horizon_train,
                                    horizon_test,
                                    target,
                                    seed=seed,
                                    hgb_max_iter=hgb_max_iter,
                                )
                                metrics.append(
                                    capacity_metric_row(
                                        horizon_test,
                                        y_pred,
                                        target=target,
                                        horizon=horizon,
                                        split_name=split_name,
                                        heldout_fold=heldout_fold,
                                        model_level=model_level,
                                        feature_group=feature_group,
                                        train_rows=horizon_train,
                                    )
                                )
                                predictions.extend(
                                    prediction_rows(
                                        horizon_test,
                                        y_pred,
                                        task="capacity_horizon",
                                        target=target,
                                        split_name=split_name,
                                        heldout_fold=heldout_fold,
                                        model_level=model_level,
                                        feature_group=feature_group,
                                    )
                                )

    if warning_rows:
        for split_name in selected_splits:
            for heldout_fold, train_rows, test_rows in iter_split_instances(warning_rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                stage_a = stage_a_auxiliary_predictions(
                    train_rows,
                    test_rows,
                    task="threshold_warning",
                    split_name=split_name,
                    heldout_fold=heldout_fold,
                    seed=seed,
                    hgb_max_iter=hgb_max_iter,
                    inner_folds=inner_folds,
                    auxiliary_model_level=auxiliary_model_level,
                )
                stage_a_metrics.extend(stage_a.metrics)
                stage_a_mode_counts.extend(
                    _stage_a_mode_count_rows(
                        stage_a.prediction_modes,
                        task="threshold_warning",
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                    )
                )
                for target in selected_warning_targets:
                    policy_train = filter_rows_by_label_policy(stage_a.train_rows, target, warning_label_policy)
                    policy_test = filter_rows_by_label_policy(stage_a.test_rows, target, warning_label_policy)
                    if not policy_train or not policy_test:
                        continue
                    for model_level in selected_models:
                        for feature_group in selected_features:
                            probs, train_one_class = predict_distilled_warning(
                                model_level,
                                feature_group,
                                policy_train,
                                policy_test,
                                target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                            )
                            metrics.append(
                                warning_metric_row(
                                    policy_test,
                                    probs,
                                    target=target,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    train_rows=policy_train,
                                    train_one_class=train_one_class,
                                )
                            )
                            predictions.extend(
                                prediction_rows(
                                    policy_test,
                                    probs,
                                    task="threshold_warning",
                                    target=target,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                )
                            )

    if not metrics:
        raise ValueError("No diagnostic-state distillation metrics were generated.")
    if not stage_a_metrics:
        raise ValueError("No auxiliary diagnostic-state metrics were generated.")

    resolved_out_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=DIAGNOSTIC_STATE_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": PREDICTION_SCHEMA_VERSION.encode(),
                b"capacity_horizon_table_path": str(capacity_horizon_table_path).encode(),
                b"threshold_warning_table_path": str(threshold_warning_table_path).encode(),
            }
        ),
        predictions_out_path,
    )

    readiness = diagnostic_state_claim_readiness(metrics, stage_a_metrics, audit)
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "capacity_horizon_table": str(capacity_horizon_table_path),
            "threshold_warning_table": str(threshold_warning_table_path),
            "pulse_target_table": str(pulse_target_table_path),
            "eis_target_table": str(eis_target_table_path),
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(resolved_out_dir),
        },
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "inner_folds": inner_folds,
        "auxiliary_model_level": auxiliary_model_level,
        "tasks": selected_tasks,
        "capacity_targets": selected_capacity_targets,
        "warning_targets": selected_warning_targets,
        "model_levels": selected_models,
        "feature_groups": selected_features,
        "split_views": selected_splits,
        "horizons": selected_horizons,
        "warning_label_policy": warning_label_policy,
        "auxiliary_targets": list(AUXILIARY_TARGETS),
        "row_counts": {
            "capacity_rows": len(capacity_rows),
            "warning_rows": len(warning_rows),
            "auxiliary_key_rows": len(auxiliary_by_key),
            "metrics": len(metrics),
            "auxiliary_metrics": len(stage_a_metrics),
            "predictions": len(predictions),
        },
        "leakage_audit": audit,
        "claim_readiness": readiness,
        "auxiliary_metrics": stage_a_metrics,
        "stage_a_prediction_modes": stage_a_mode_counts,
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_diagnostic_state_artifacts(report, resolved_out_dir)
    return report


def stage_a_auxiliary_predictions(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    task: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    inner_folds: int = 5,
    auxiliary_model_level: str = DEFAULT_AUXILIARY_MODEL_LEVEL,
) -> StageAAuxiliaryResult:
    """Attach train-only predicted diagnostic-state features to rows."""

    train_unique = _unique_base_rows(train_rows)
    test_unique = _unique_base_rows(test_rows)
    train_by_key = {_base_key(row): row for row in train_unique}
    test_by_key = {_base_key(row): row for row in test_unique}
    train_predictions: dict[str, dict[tuple[Any, ...], float]] = {}
    test_predictions: dict[str, dict[tuple[Any, ...], float]] = {}
    metrics: list[dict[str, Any]] = []
    modes: dict[str, dict[str, int]] = {}
    for target in AUXILIARY_TARGETS:
        train_pred, test_pred, mode_counts = _predict_auxiliary_target(
            train_unique,
            test_unique,
            target,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            inner_folds=inner_folds,
            auxiliary_model_level=auxiliary_model_level,
        )
        train_predictions[target] = train_pred
        test_predictions[target] = test_pred
        modes[target] = mode_counts
        metrics.append(
            auxiliary_metric_row(
                list(test_by_key.values()),
                test_pred,
                train_rows=list(train_by_key.values()),
                target=target,
                task=task,
                split_name=split_name,
                heldout_fold=heldout_fold,
            )
        )
    return StageAAuxiliaryResult(
        train_rows=_attach_prediction_features(train_rows, train_predictions),
        test_rows=_attach_prediction_features(test_rows, test_predictions),
        metrics=metrics,
        prediction_modes=modes,
    )


def predict_distilled_capacity(
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
) -> list[float]:
    if target not in CAPACITY_TARGETS:
        raise ValueError(f"Unknown capacity distillation target: {target}")
    _, Ridge, HistGradientBoostingRegressor, _, _ = _import_sklearn_stack()
    numeric, categorical = feature_columns("capacity_horizon", feature_group)
    encoder = DiagnosticFeatureEncoder.fit(train_rows, numeric_columns=numeric, categorical_columns=categorical)
    standardize = model_level == "DS0_regularized_linear"
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=standardize), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=standardize), dtype=float)
    y_train = np.asarray([_as_float(row.get(target)) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Capacity target {target} has non-finite train values.")
    if model_level == "DS0_regularized_linear":
        model = Ridge(alpha=1.0)
    elif model_level == "DS1_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown diagnostic-state model level: {model_level}")
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict(x_test)]


def predict_distilled_warning(
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
) -> tuple[list[float], bool]:
    if target not in WARNING_TARGETS:
        raise ValueError(f"Unknown warning distillation target: {target}")
    _, _, _, LogisticRegression, HistGradientBoostingClassifier = _import_sklearn_stack()
    y_train = np.asarray([1.0 if row[target] else 0.0 for row in train_rows], dtype=float)
    base_rate = float(np.mean(y_train)) if len(y_train) else 0.0
    train_one_class = len(set(y_train.tolist())) < 2
    if train_one_class:
        return [_clip_probability(base_rate) for _ in test_rows], True
    numeric, categorical = feature_columns("threshold_warning", feature_group)
    encoder = DiagnosticFeatureEncoder.fit(train_rows, numeric_columns=numeric, categorical_columns=categorical)
    standardize = model_level == "DS0_regularized_linear"
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=standardize), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=standardize), dtype=float)
    if model_level == "DS0_regularized_linear":
        model = LogisticRegression(C=1.0, max_iter=1000, random_state=seed)
    elif model_level == "DS1_hist_gradient_boosting":
        model = HistGradientBoostingClassifier(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown diagnostic-state model level: {model_level}")
    model.fit(x_train, y_train)
    return [_clip_probability(float(value)) for value in model.predict_proba(x_test)[:, 1]], False


def feature_columns(task: str, feature_group: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if feature_group not in FEATURE_GROUPS:
        raise ValueError(f"Unknown diagnostic-state feature group: {feature_group}")
    if task == "capacity_horizon":
        base_numeric = CAPACITY_BASE_NUMERIC_FEATURES
    elif task == "threshold_warning":
        base_numeric = WARNING_BASE_NUMERIC_FEATURES
    else:
        raise ValueError(f"Unknown diagnostic-state task: {task}")
    aux_columns = tuple(_predicted_feature_name(target) for target in _auxiliary_targets_for_group(feature_group))
    return base_numeric + aux_columns, BASE_STATE_CATEGORICAL_FEATURES


def capacity_metric_row(
    test_rows: list[dict[str, Any]],
    predictions: list[float],
    *,
    target: str,
    horizon: int,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    y_true = [_as_float(row.get(target)) for row in test_rows]
    errors = [prediction - true for prediction, true in zip(predictions, y_true)]
    abs_errors = [abs(error) for error in errors]
    condition_rows = _condition_metric_rows(test_rows, abs_errors, metric_name="mae")
    return {
        "task": "capacity_horizon",
        "target": target,
        "horizon_checkups": horizon,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "train_conditions": len({int(row["parameter_set"]) for row in train_rows}),
        "test_conditions": len({int(row["parameter_set"]) for row in test_rows}),
        "mae": _mean(abs_errors),
        "rmse": math.sqrt(_mean([error * error for error in errors])),
        "bias": _mean(errors),
        "condition_mean_mae": _mean([row["mae"] for row in condition_rows]),
        "worst_condition_mae": max(row["mae"] for row in condition_rows),
    }


def warning_metric_row(
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
    condition_rows = _condition_brier_rows(test_rows, y_true, probs)
    return {
        "task": "threshold_warning",
        "target": target,
        "horizon_checkups": None,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "train_conditions": len({int(row["parameter_set"]) for row in train_rows}),
        "test_conditions": len({int(row["parameter_set"]) for row in test_rows}),
        "train_positive_count": sum(1 for row in train_rows if row[target]),
        "test_positive_count": sum(y_true),
        "test_negative_count": len(y_true) - sum(y_true),
        "train_one_class": train_one_class,
        "test_one_class": len(set(y_true)) < 2,
        "auroc": auroc(y_true, probs),
        "auprc": auprc(y_true, probs),
        "brier": brier_score(y_true, probs),
        "log_loss": log_loss(y_true, probs),
        "condition_mean_brier": _mean([row["brier"] for row in condition_rows]),
        "worst_condition_brier": max((row["brier"] for row in condition_rows), default=None),
        "ece_10_bin": expected_calibration_error(y_true, probs, bins=10),
        "ece_10_bin_equal_freq": expected_calibration_error_equal_frequency(y_true, probs, bins=10),
    }


def auxiliary_metric_row(
    test_rows: list[dict[str, Any]],
    predictions_by_key: dict[tuple[Any, ...], float],
    *,
    train_rows: list[dict[str, Any]],
    target: str,
    task: str,
    split_name: str,
    heldout_fold: int,
) -> dict[str, Any]:
    train_values = [_as_float(row.get(target)) for row in train_rows]
    train_finite = [value for value in train_values if math.isfinite(value)]
    baseline = _mean(train_finite) if train_finite else 0.0
    scored = []
    for row in test_rows:
        truth = _as_float(row.get(target))
        prediction = predictions_by_key.get(_base_key(row), baseline)
        if math.isfinite(truth) and math.isfinite(prediction):
            scored.append((row, truth, prediction))
    if not scored:
        return {
            "task": task,
            "auxiliary_target": target,
            "auxiliary_family": _auxiliary_family(target),
            "split_name": split_name,
            "heldout_fold": heldout_fold,
            "n_train_finite": len(train_finite),
            "n_test_finite": 0,
            "mae": None,
            "baseline_mae": None,
            "mae_gain_vs_train_mean": None,
            "relative_mae_gain_vs_train_mean": None,
            "status": "not_evaluated",
        }
    abs_errors = [abs(prediction - truth) for _, truth, prediction in scored]
    baseline_errors = [abs(baseline - truth) for _, truth, _ in scored]
    mae = _mean(abs_errors)
    baseline_mae = _mean(baseline_errors)
    return {
        "task": task,
        "auxiliary_target": target,
        "auxiliary_family": _auxiliary_family(target),
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "n_train_finite": len(train_finite),
        "n_test_finite": len(scored),
        "mae": mae,
        "baseline_mae": baseline_mae,
        "mae_gain_vs_train_mean": baseline_mae - mae,
        "relative_mae_gain_vs_train_mean": _safe_relative_gain(baseline_mae - mae, baseline_mae),
        "status": "evaluated",
    }


def prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[float],
    *,
    task: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
) -> list[dict[str, Any]]:
    output = []
    for row, prediction in zip(test_rows, predictions):
        output.append(
            {
                "schema_version": PREDICTION_SCHEMA_VERSION,
                "task": task,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "cell_id": str(row["cell_id"]),
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "target_checkup_k": int(row.get("target_checkup_k") or row.get("checkup_k")),
                "horizon_checkups": int(row.get("horizon_checkups") or 0),
                "y_true": _task_target_value(row, task, target),
                "y_pred": float(prediction),
            }
        )
    return output


def leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[
            (
                row["task"],
                row["target"],
                row.get("horizon_checkups"),
                row["model_level"],
                row["feature_group"],
            )
        ].append(row)
    return [
        _aggregate_downstream_rows(rows, split_name="all")
        for _, rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


def split_leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[
            (
                row["task"],
                row["target"],
                row.get("horizon_checkups"),
                row["split_name"],
                row["model_level"],
                row["feature_group"],
            )
        ].append(row)
    return [
        _aggregate_downstream_rows(rows, split_name=str(key[3]))
        for key, rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


def auxiliary_leaderboard_rows(auxiliary_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in auxiliary_metrics:
        if row["status"] != "evaluated":
            continue
        grouped[(row["task"], row["auxiliary_family"], row["auxiliary_target"])].append(row)
    output = []
    for (task, family, target), rows in sorted(grouped.items()):
        mean_mae = _mean([row["mae"] for row in rows])
        mean_baseline = _mean([row["baseline_mae"] for row in rows])
        output.append(
            {
                "task": task,
                "auxiliary_family": family,
                "auxiliary_target": target,
                "split_name": "all",
                "evaluated_rows": len(rows),
                "mean_mae": mean_mae,
                "mean_train_mean_baseline_mae": mean_baseline,
                "mean_mae_gain_vs_train_mean": mean_baseline - mean_mae,
                "relative_mae_gain_vs_train_mean": _safe_relative_gain(mean_baseline - mean_mae, mean_baseline),
            }
        )
    return output


def diagnostic_state_gain_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = leaderboard_rows(metrics) + split_leaderboard_rows(metrics)
    output = []
    for candidate in rows:
        if candidate["model_level"] != "DS1_hist_gradient_boosting":
            continue
        if candidate["feature_group"] == "D0_capacity_state_reference":
            continue
        reference = _find_downstream_row(
            rows,
            task=candidate["task"],
            target=candidate["target"],
            horizon=candidate.get("horizon_checkups"),
            split_name=candidate["split_name"],
            model_level="DS1_hist_gradient_boosting",
            feature_group="D0_capacity_state_reference",
        )
        if reference is None:
            continue
        if candidate["task"] == "capacity_horizon":
            reference_value = reference["mean_mae"]
            candidate_value = candidate["mean_mae"]
            metric = "mae"
        else:
            reference_value = reference["mean_brier"]
            candidate_value = candidate["mean_brier"]
            metric = "brier"
        gain = reference_value - candidate_value
        output.append(
            {
                "task": candidate["task"],
                "target": candidate["target"],
                "horizon_checkups": candidate.get("horizon_checkups"),
                "split_name": candidate["split_name"],
                "model_level": candidate["model_level"],
                "candidate_feature_group": candidate["feature_group"],
                "reference_feature_group": "D0_capacity_state_reference",
                "metric": metric,
                "reference_value": reference_value,
                "candidate_value": candidate_value,
                "gain": gain,
                "relative_gain": _safe_relative_gain(gain, reference_value),
                "beats_reference": candidate_value < reference_value,
            }
        )
    return sorted(
        output,
        key=lambda row: (
            row["task"],
            row["split_name"],
            row["target"],
            row.get("horizon_checkups") or 0,
            row["candidate_feature_group"],
        ),
    )


def leakage_audit(feature_groups: list[str]) -> dict[str, Any]:
    rows = []
    status = "passed"
    for group in feature_groups:
        if group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown diagnostic-state feature group: {group}")
        capacity_numeric, capacity_categorical = feature_columns("capacity_horizon", group)
        warning_numeric, warning_categorical = feature_columns("threshold_warning", group)
        fields = set(capacity_numeric + capacity_categorical + warning_numeric + warning_categorical)
        future_fields = sorted(fields & FORBIDDEN_FEATURE_FIELDS)
        forbidden_auxiliary_fields = sorted(fields & FORBIDDEN_AUXILIARY_FIELDS)
        true_auxiliary_fields = sorted(fields & set(AUXILIARY_TARGETS))
        if future_fields or forbidden_auxiliary_fields or true_auxiliary_fields:
            status = "failed"
        rows.append(
            {
                "feature_group": group,
                "uses_predicted_pulse_state": any(
                    target in _auxiliary_targets_for_group(group) for target in PULSE_AUXILIARY_TARGETS
                ),
                "uses_predicted_eis_state": any(
                    target in _auxiliary_targets_for_group(group) for target in EIS_AUXILIARY_TARGETS
                ),
                "future_or_target_fields": future_fields,
                "future_auxiliary_fields": forbidden_auxiliary_fields,
                "true_auxiliary_fields_as_features": true_auxiliary_fields,
                "claim_scope": "predicted_diagnostic_state_only",
            }
        )
    return {
        "status": status,
        "allowed_features": "check-up-k capacity/state/time/nominal fields plus out-of-fold predicted diagnostic state",
        "forbidden_features": sorted(FORBIDDEN_FEATURE_FIELDS | FORBIDDEN_AUXILIARY_FIELDS | set(AUXILIARY_TARGETS)),
        "rows": rows,
    }


def diagnostic_state_claim_readiness(
    metrics: list[dict[str, Any]],
    auxiliary_metrics: list[dict[str, Any]],
    audit: dict[str, Any],
) -> dict[str, Any]:
    gains = diagnostic_state_gain_rows(metrics)
    aux_rows = auxiliary_leaderboard_rows(auxiliary_metrics)
    primary_capacity = [
        row
        for row in gains
        if row["task"] == "capacity_horizon"
        and row["candidate_feature_group"] == "D3_predicted_pulse_eis_state"
        and row["split_name"] == "all"
        and row["target"] in CAPACITY_TARGETS
        and int(row["horizon_checkups"] or 0) in {2, 3}
    ]
    primary_warning = [
        row
        for row in gains
        if row["task"] == "threshold_warning"
        and row["candidate_feature_group"] == "D3_predicted_pulse_eis_state"
        and row["split_name"] == "all"
        and row["target"] == "event_within_3_checkups"
    ]
    c_rate = [
        row
        for row in gains
        if row["candidate_feature_group"] == "D3_predicted_pulse_eis_state"
        and row["split_name"] == "c_rate_holdout_fold"
    ]
    aux_positive = [row for row in aux_rows if row["mean_mae_gain_vs_train_mean"] > 0]
    auxiliary_status = (
        "supported_for_diagnostics"
        if len(aux_positive) == len(aux_rows) and aux_rows
        else "partially_supported"
        if aux_positive
        else "not_supported"
    )
    capacity_best_relative = _max_nullable([row["relative_gain"] for row in primary_capacity])
    warning_best_relative = _max_nullable([row["relative_gain"] for row in primary_warning])
    c_rate_noncollapse = bool(c_rate) and all(row["gain"] >= 0 for row in c_rate)
    capacity_passes = capacity_best_relative is not None and capacity_best_relative >= 0.10
    warning_passes = warning_best_relative is not None and warning_best_relative >= 0.10
    any_positive = any(row["gain"] > 0 for row in primary_capacity + primary_warning)
    if audit["status"] != "passed":
        multimodal_status = "blocked"
    elif (capacity_passes or warning_passes) and c_rate_noncollapse and auxiliary_status in {
        "supported_for_diagnostics",
        "partially_supported",
    }:
        multimodal_status = "supported_for_diagnostics"
    elif any_positive and auxiliary_status != "not_supported":
        multimodal_status = "partially_supported"
    else:
        multimodal_status = "not_supported"
    return {
        "diagnostic_state_distillation": multimodal_status,
        "auxiliary_surrogate_prediction": auxiliary_status,
        "capacity_horizon_gain": "supported_for_diagnostics" if capacity_passes else "not_supported",
        "threshold_warning_gain": "supported_for_diagnostics" if warning_passes else "not_supported",
        "c_rate_noncollapse": "supported_for_diagnostics" if c_rate_noncollapse else "not_supported",
        "leakage_audit": audit["status"],
        "cbat_architecture": "blocked",
        "neural_or_sequence_models": "blocked",
        "policy_ranking": "blocked",
        "calibrated_risk_or_uncertainty": "blocked",
        "causal_or_same_cell_counterfactual": "blocked",
        "claim_rule": "D3 must improve a primary capacity or threshold-warning metric by at least 10%, avoid C-rate collapse, and use only out-of-fold predicted diagnostic-state features.",
        "capacity_best_relative_gain": capacity_best_relative,
        "threshold_best_relative_gain": warning_best_relative,
        "auxiliary_positive_rows": len(aux_positive),
        "auxiliary_evaluated_rows": len(aux_rows),
    }


def render_diagnostic_state_artifacts(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    auxiliary_metrics = list(report["auxiliary_metrics"])
    leaderboard = leaderboard_rows(metrics)
    split_leaderboard = split_leaderboard_rows(metrics)
    gains = diagnostic_state_gain_rows(metrics)
    aux_leaderboard = auxiliary_leaderboard_rows(auxiliary_metrics)
    _write_csv(out_dir / "leaderboard.csv", leaderboard)
    _write_csv(plots_dir / "downstream_split_leaderboard.csv", split_leaderboard)
    _write_csv(plots_dir / "diagnostic_state_downstream_gains.csv", gains)
    _write_csv(plots_dir / "auxiliary_target_accuracy.csv", aux_leaderboard)
    _write_csv(plots_dir / "c_rate_diagnostic_state_gains.csv", [row for row in gains if row["split_name"] == "c_rate_holdout_fold"])
    _write_csv(plots_dir / "stage_a_prediction_modes.csv", list(report.get("stage_a_prediction_modes", [])))
    _write_claim_readiness_md(report["claim_readiness"], out_dir / "diagnostic_state_distillation_claim_readiness.md")
    _write_summary_md(report, aux_leaderboard, gains, out_dir / "diagnostic_state_distillation_summary.md")


def _predict_auxiliary_target(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
    inner_folds: int,
    auxiliary_model_level: str,
) -> tuple[dict[tuple[Any, ...], float], dict[tuple[Any, ...], float], dict[str, int]]:
    train_finite = [row for row in train_rows if math.isfinite(_as_float(row.get(target)))]
    train_mean = _mean([_as_float(row.get(target)) for row in train_finite]) if train_finite else 0.0
    train_predictions = {_base_key(row): train_mean for row in train_rows}
    test_predictions = {_base_key(row): train_mean for row in test_rows}
    mode_counts = defaultdict(int)
    if len({int(row["parameter_set"]) for row in train_finite}) < 2 or len(train_finite) < 2:
        mode_counts["train_mean_fallback"] = len(train_predictions) + len(test_predictions)
        return train_predictions, test_predictions, dict(mode_counts)

    condition_folds = _inner_condition_folds(train_finite, inner_folds=inner_folds, seed=seed, target=target)
    for fold_conditions in condition_folds:
        inner_fit = [row for row in train_finite if int(row["parameter_set"]) not in fold_conditions]
        inner_holdout = [row for row in train_finite if int(row["parameter_set"]) in fold_conditions]
        if len(inner_fit) < 2 or not inner_holdout:
            for row in inner_holdout:
                train_predictions[_base_key(row)] = train_mean
                mode_counts["inner_train_mean_fallback"] += 1
            continue
        fold_predictions = _fit_predict_auxiliary(
            inner_fit,
            inner_holdout,
            target,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            auxiliary_model_level=auxiliary_model_level,
        )
        for row, prediction in zip(inner_holdout, fold_predictions):
            train_predictions[_base_key(row)] = prediction
            mode_counts["inner_out_of_fold"] += 1

    missing_target_train = [row for row in train_rows if not math.isfinite(_as_float(row.get(target)))]
    if missing_target_train:
        missing_predictions = _fit_predict_auxiliary(
            train_finite,
            missing_target_train,
            target,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            auxiliary_model_level=auxiliary_model_level,
        )
        for row, prediction in zip(missing_target_train, missing_predictions):
            train_predictions[_base_key(row)] = prediction
            mode_counts["missing_target_full_train_prediction"] += 1

    test_full_predictions = _fit_predict_auxiliary(
        train_finite,
        test_rows,
        target,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        auxiliary_model_level=auxiliary_model_level,
    )
    for row, prediction in zip(test_rows, test_full_predictions):
        test_predictions[_base_key(row)] = prediction
        mode_counts["outer_test_full_train_prediction"] += 1
    return train_predictions, test_predictions, dict(mode_counts)


def _fit_predict_auxiliary(
    fit_rows: list[dict[str, Any]],
    predict_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
    auxiliary_model_level: str = DEFAULT_AUXILIARY_MODEL_LEVEL,
) -> list[float]:
    if not predict_rows:
        return []
    y_fit = np.asarray([_as_float(row.get(target)) for row in fit_rows], dtype=float)
    finite_mask = np.isfinite(y_fit)
    filtered_fit = [row for row, finite in zip(fit_rows, finite_mask.tolist()) if finite]
    filtered_y = y_fit[finite_mask]
    if len(filtered_fit) < 2:
        fallback = float(np.mean(filtered_y)) if len(filtered_y) else 0.0
        return [fallback for _ in predict_rows]
    if auxiliary_model_level not in AUXILIARY_MODEL_LEVELS:
        raise ValueError(f"Unknown auxiliary model level: {auxiliary_model_level}")
    _, Ridge, HistGradientBoostingRegressor, _, _ = _import_sklearn_stack()
    encoder = DiagnosticFeatureEncoder.fit(
        filtered_fit,
        numeric_columns=BASE_STATE_NUMERIC_FEATURES,
        categorical_columns=BASE_STATE_CATEGORICAL_FEATURES,
    )
    standardize = auxiliary_model_level == "A0_ridge"
    x_fit = np.asarray(encoder.transform(filtered_fit, standardize_numeric=standardize), dtype=float)
    x_predict = np.asarray(encoder.transform(predict_rows, standardize_numeric=standardize), dtype=float)
    if auxiliary_model_level == "A0_ridge":
        model = Ridge(alpha=1.0)
    else:
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    model.fit(x_fit, filtered_y)
    return [float(value) for value in model.predict(x_predict)]


def _inner_condition_folds(
    rows: list[dict[str, Any]],
    *,
    inner_folds: int,
    seed: int,
    target: str,
) -> list[set[int]]:
    conditions = sorted({int(row["parameter_set"]) for row in rows})
    fold_count = min(inner_folds, len(conditions))
    ordered = sorted(conditions, key=lambda condition: (_stable_hash(f"{seed}:{target}:{condition}"), condition))
    folds: list[set[int]] = [set() for _ in range(fold_count)]
    for index, condition in enumerate(ordered):
        folds[index % fold_count].add(condition)
    return [fold for fold in folds if fold]


def _attach_prediction_features(
    rows: list[dict[str, Any]],
    predictions: dict[str, dict[tuple[Any, ...], float]],
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        new_row = dict(row)
        key = _base_key(row)
        for target, target_predictions in predictions.items():
            new_row[_predicted_feature_name(target)] = float(target_predictions.get(key, 0.0))
        output.append(new_row)
    return output


def _auxiliary_by_base_key(
    pulse_rows: list[dict[str, Any]],
    eis_rows: list[dict[str, Any]],
) -> dict[tuple[Any, ...], dict[str, Any]]:
    joined: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(dict)
    for row in pulse_rows:
        key = _base_key(row)
        for target in PULSE_AUXILIARY_TARGETS:
            joined[key][target] = row.get(target)
    for row in eis_rows:
        key = _base_key(row)
        for target in EIS_AUXILIARY_TARGETS:
            joined[key][target] = row.get(target)
    return dict(joined)


def _with_auxiliary_values(
    row: dict[str, Any],
    auxiliary_by_key: dict[tuple[Any, ...], dict[str, Any]],
) -> dict[str, Any]:
    output = dict(row)
    output.update(auxiliary_by_key.get(_base_key(row), {}))
    return output


def _unique_base_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        by_key.setdefault(_base_key(row), row)
    return list(by_key.values())


def _stage_a_mode_count_rows(
    modes: dict[str, dict[str, int]],
    *,
    task: str,
    split_name: str,
    heldout_fold: int,
) -> list[dict[str, Any]]:
    rows = []
    for target, mode_counts in sorted(modes.items()):
        for mode, count in sorted(mode_counts.items()):
            rows.append(
                {
                    "task": task,
                    "split_name": split_name,
                    "heldout_fold": heldout_fold,
                    "auxiliary_target": target,
                    "auxiliary_family": _auxiliary_family(target),
                    "prediction_mode": mode,
                    "row_count": count,
                }
            )
    return rows


def _aggregate_downstream_rows(rows: list[dict[str, Any]], *, split_name: str) -> dict[str, Any]:
    first = rows[0]
    if first["task"] == "capacity_horizon":
        return {
            "task": first["task"],
            "target": first["target"],
            "horizon_checkups": first.get("horizon_checkups"),
            "split_name": split_name,
            "model_level": first["model_level"],
            "feature_group": first["feature_group"],
            "folds": len(rows),
            "n_test": sum(int(row["n_test"]) for row in rows),
            "mean_mae": _mean([row["mae"] for row in rows]),
            "mean_rmse": _mean([row["rmse"] for row in rows]),
            "mean_condition_mean_mae": _mean([row["condition_mean_mae"] for row in rows]),
            "max_worst_condition_mae": max(row["worst_condition_mae"] for row in rows),
        }
    return {
        "task": first["task"],
        "target": first["target"],
        "horizon_checkups": first.get("horizon_checkups"),
        "split_name": split_name,
        "model_level": first["model_level"],
        "feature_group": first["feature_group"],
        "folds": len(rows),
        "n_test": sum(int(row["n_test"]) for row in rows),
        "mean_brier": _mean([row["brier"] for row in rows]),
        "mean_auroc": _mean_nullable([row["auroc"] for row in rows]),
        "mean_auprc": _mean_nullable([row["auprc"] for row in rows]),
        "mean_log_loss": _mean([row["log_loss"] for row in rows]),
        "mean_condition_mean_brier": _mean([row["condition_mean_brier"] for row in rows]),
        "max_worst_condition_brier": _max_nullable([row["worst_condition_brier"] for row in rows]),
        "mean_ece_10_bin": _mean([row["ece_10_bin"] for row in rows]),
        "mean_ece_10_bin_equal_freq": _mean([row["ece_10_bin_equal_freq"] for row in rows]),
    }


def _find_downstream_row(
    rows: list[dict[str, Any]],
    *,
    task: str,
    target: str,
    horizon: Any,
    split_name: str,
    model_level: str,
    feature_group: str,
) -> dict[str, Any] | None:
    for row in rows:
        if (
            row["task"] == task
            and row["target"] == target
            and row.get("horizon_checkups") == horizon
            and row["split_name"] == split_name
            and row["model_level"] == model_level
            and row["feature_group"] == feature_group
        ):
            return row
    return None


def _condition_metric_rows(
    rows: list[dict[str, Any]],
    values: list[float],
    *,
    metric_name: str,
) -> list[dict[str, Any]]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for row, value in zip(rows, values):
        grouped[int(row["parameter_set"])].append(float(value))
    return [{"parameter_set": key, metric_name: _mean(group_values)} for key, group_values in grouped.items()]


def _condition_brier_rows(
    rows: list[dict[str, Any]],
    y_true: list[int],
    probabilities: list[float],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for row, truth, probability in zip(rows, y_true, probabilities):
        grouped[int(row["parameter_set"])].append((probability - truth) ** 2)
    return [{"parameter_set": key, "brier": _mean(values)} for key, values in grouped.items()]


def _write_claim_readiness_md(readiness: dict[str, Any], path: Path) -> None:
    lines = [
        "# Diagnostic-State Distillation Claim Readiness",
        "",
        "This gate tests train-only predicted PULSE/EIS diagnostic-state features. It does not use true diagnostic values as downstream features.",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Diagnostic-state distillation | `{readiness['diagnostic_state_distillation']}` | {readiness['claim_rule']} |",
        f"| Auxiliary surrogate prediction | `{readiness['auxiliary_surrogate_prediction']}` | `{readiness['auxiliary_positive_rows']}` of `{readiness['auxiliary_evaluated_rows']}` auxiliary leaderboard rows beat train-mean baselines. |",
        f"| Capacity-horizon gain | `{readiness['capacity_horizon_gain']}` | Best relative D3 gain: `{_fmt(readiness['capacity_best_relative_gain'])}`. |",
        f"| Threshold-warning gain | `{readiness['threshold_warning_gain']}` | Best relative D3 gain: `{_fmt(readiness['threshold_best_relative_gain'])}`. |",
        f"| C-rate non-collapse | `{readiness['c_rate_noncollapse']}` | D3 must not be worse than D0 on C-rate downstream rows. |",
        f"| Leakage audit | `{readiness['leakage_audit']}` | Downstream features are check-up-k state/time/nominal fields plus out-of-fold predicted diagnostic state. |",
        f"| CBAT architecture | `{readiness['cbat_architecture']}` | Not tested. |",
        f"| Neural or sequence models | `{readiness['neural_or_sequence_models']}` | Not tested. |",
        f"| Policy ranking | `{readiness['policy_ranking']}` | Not tested. |",
        f"| Calibrated risk or uncertainty | `{readiness['calibrated_risk_or_uncertainty']}` | Not tested. |",
        "",
        "Allowed wording must stay limited to non-neural diagnostic-state distillation under grouped validation.",
        "Forbidden wording: true multimodal architecture, CBAT validation, calibrated risk, policy recommendation, causal effects, or same-cell counterfactual claims.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_md(
    report: dict[str, Any],
    auxiliary_rows: list[dict[str, Any]],
    gain_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    readiness = report["claim_readiness"]
    best_capacity = max(
        [row for row in gain_rows if row["task"] == "capacity_horizon"],
        key=lambda row: row["relative_gain"] if row["relative_gain"] is not None else -math.inf,
        default=None,
    )
    best_warning = max(
        [row for row in gain_rows if row["task"] == "threshold_warning"],
        key=lambda row: row["relative_gain"] if row["relative_gain"] is not None else -math.inf,
        default=None,
    )
    lines = [
        "# Diagnostic-State Distillation Summary",
        "",
        f"Schema version: `{report['schema_version']}`",
        "",
        "The run predicts current PULSE/EIS diagnostic-state scalars from check-up-k capacity/state/nominal features, then feeds only those predicted diagnostic-state values into downstream non-neural baselines.",
        "",
        f"Claim readiness: `{readiness['diagnostic_state_distillation']}`.",
        "",
    ]
    if best_capacity:
        lines.append(
            f"Best capacity downstream row: `{best_capacity['target']}` horizon `{best_capacity['horizon_checkups']}` split `{best_capacity['split_name']}` feature `{best_capacity['candidate_feature_group']}` relative gain `{_fmt(best_capacity['relative_gain'])}`."
        )
    if best_warning:
        lines.append(
            f"Best threshold-warning downstream row: `{best_warning['target']}` split `{best_warning['split_name']}` feature `{best_warning['candidate_feature_group']}` relative Brier gain `{_fmt(best_warning['relative_gain'])}`."
        )
    if auxiliary_rows:
        positive = sum(1 for row in auxiliary_rows if row["mean_mae_gain_vs_train_mean"] > 0)
        lines.append(
            f"Auxiliary surrogate targets beating train-mean baselines: `{positive}` / `{len(auxiliary_rows)}`."
        )
    lines.extend(
        [
            "",
            "This is a falsification gate for charter Q2/H3, not an architecture milestone.",
        ]
    )
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


def _task_target_value(row: dict[str, Any], task: str, target: str) -> float:
    if task == "threshold_warning":
        return 1.0 if row[target] else 0.0
    return _as_float(row.get(target))


def _auxiliary_targets_for_group(feature_group: str) -> tuple[str, ...]:
    if feature_group == "D0_capacity_state_reference":
        return ()
    if feature_group == "D1_predicted_pulse_state":
        return PULSE_AUXILIARY_TARGETS
    if feature_group == "D2_predicted_eis_state":
        return EIS_AUXILIARY_TARGETS
    if feature_group == "D3_predicted_pulse_eis_state":
        return AUXILIARY_TARGETS
    raise ValueError(f"Unknown diagnostic-state feature group: {feature_group}")


def _predicted_feature_name(target: str) -> str:
    return f"predicted_{target}"


def _auxiliary_family(target: str) -> str:
    if target in PULSE_AUXILIARY_TARGETS:
        return "pulse"
    if target in EIS_AUXILIARY_TARGETS:
        return "eis"
    return "unknown"


def _base_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["cell_id"]),
        int(row["parameter_set"]),
        int(row["replicate_id"]),
        int(row["checkup_k"]),
    )


def _normalize_selection(
    values: list[str] | None,
    allowed: tuple[str, ...],
    default: tuple[str, ...],
    label: str,
) -> list[str]:
    raw = default if values is None else values
    selected = []
    seen = set()
    for item in raw:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        selected.append(normalized)
        seen.add(normalized)
    unknown = sorted(set(selected) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}: {unknown}. Allowed: {list(allowed)}")
    if not selected:
        raise ValueError(f"At least one {label} must be selected.")
    return selected


def _normalize_horizons(values: list[int] | None) -> list[int]:
    selected = list(DEFAULT_HORIZONS if values is None else values)
    output = []
    seen = set()
    for item in selected:
        horizon = int(item)
        if horizon <= 0:
            raise ValueError("Horizons must be positive.")
        if horizon not in seen:
            output.append(horizon)
            seen.add(horizon)
    if not output:
        raise ValueError("At least one horizon must be selected.")
    return output


def _import_sklearn_stack() -> tuple[Any, Any, Any, Any, Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
        from sklearn.linear_model import LogisticRegression, Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Diagnostic-state distillation requires the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry."
        ) from exc
    return np, Ridge, HistGradientBoostingRegressor, LogisticRegression, HistGradientBoostingClassifier


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _as_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _category(value: Any) -> str:
    return "" if value is None else str(value)


def _mean(values: list[float | None]) -> float:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not finite:
        raise ValueError("Cannot compute mean of empty finite values.")
    return sum(finite) / len(finite)


def _mean_nullable(values: list[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    if not finite:
        return None
    return sum(finite) / len(finite)


def _max_nullable(values: list[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return max(finite) if finite else None


def _safe_relative_gain(gain: float | None, reference: float | None) -> float | None:
    if gain is None or reference is None or not math.isfinite(float(reference)) or abs(float(reference)) < 1e-12:
        return None
    return float(gain) / float(reference)


def _clip_probability(value: float) -> float:
    return min(max(float(value), 1e-6), 1.0 - 1e-6)


def _stable_hash(value: str) -> int:
    # Avoid Python's randomized process hash for reproducible inner folds.
    import hashlib

    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return "NA"
    return f"{number:.6g}"
