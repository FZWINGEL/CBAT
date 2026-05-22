"""Milestone 0.5 capacity baseline runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "gate5.capacity_baseline.v1"

TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
SUBSET_COLUMNS = ("baseline_clean_tolerant", "baseline_clean_strict")
MODEL_LEVELS = (
    "L0_persistence",
    "L1_ridge",
    "L2_hist_gradient_boosting",
    "L3_quantile_hist_gradient_boosting",
)
FEATURE_GROUPS = ("F0_time_only", "F1_time_efc", "F2_nominal_protocol", "F3_log_age_scalar")

DIAGNOSTIC_LEAKAGE_FIELDS = {"cap_aged_est_Ah", "R0_mOhm", "R1_mOhm"}

NUMERIC_FEATURES: dict[str, tuple[str, ...]] = {
    "F0_time_only": ("duration_h", "calendar_days", "checkup_k"),
    "F1_time_efc": (
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
    ),
    "F2_nominal_protocol": (
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "F3_log_age_scalar": (
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_mean_voltage_V",
        "log_age_min_voltage_V",
        "log_age_max_voltage_V",
        "log_age_mean_temperature_C",
        "log_age_min_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_current_A",
        "log_age_mean_abs_current_A",
        "log_age_max_abs_current_A",
        "log_age_mean_soc",
        "log_age_min_soc",
        "log_age_max_soc",
    ),
}

CATEGORICAL_FEATURES: dict[str, tuple[str, ...]] = {
    "F0_time_only": (),
    "F1_time_efc": (),
    "F2_nominal_protocol": ("aging_mode", "voltage_window_family"),
    "F3_log_age_scalar": ("aging_mode", "voltage_window_family"),
}

BASELINE_PREDICTION_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("subset_name", pa.string()),
        ("run_scope", pa.string()),
        ("split_name", pa.string()),
        ("heldout_fold", pa.int32()),
        ("model_level", pa.string()),
        ("feature_group", pa.string()),
        ("target", pa.string()),
        ("cell_id", pa.string()),
        ("parameter_set", pa.int32()),
        ("replicate_id", pa.int32()),
        ("checkup_k", pa.int32()),
        ("checkup_k_next", pa.int32()),
        ("sensitivity_flagged_monotonicity", pa.bool_()),
        ("y_true", pa.float64()),
        ("y_pred", pa.float64()),
        ("y_pred_q10", pa.float64()),
        ("y_pred_q50", pa.float64()),
        ("y_pred_q90", pa.float64()),
    ]
)


@dataclass(frozen=True)
class FeatureEncoder:
    """Train-fold-derived feature encoder with numeric imputation and one-hot categories."""

    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]
    output_columns: tuple[str, ...]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "FeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown feature group: {feature_group}")
        numeric_columns = NUMERIC_FEATURES[feature_group]
        categorical_columns = CATEGORICAL_FEATURES[feature_group]
        leakage = set(numeric_columns) | set(categorical_columns)
        leakage &= DIAGNOSTIC_LEAKAGE_FIELDS
        if leakage:
            raise ValueError(f"Feature group {feature_group} includes leakage fields: {sorted(leakage)}")

        impute_values: dict[str, float] = {}
        for column in numeric_columns:
            values = [_as_float(row.get(column)) for row in rows]
            finite_values = [value for value in values if math.isfinite(value)]
            impute_values[column] = (
                sum(finite_values) / len(finite_values) if finite_values else 0.0
            )

        categorical_values: dict[str, tuple[str, ...]] = {}
        output_columns = list(numeric_columns)
        for column in categorical_columns:
            values = tuple(sorted({_category(row.get(column)) for row in rows}))
            categorical_values[column] = values
            output_columns.extend(f"{column}={value}" for value in values)

        return cls(
            feature_group=feature_group,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            numeric_impute_values=impute_values,
            categorical_values=categorical_values,
            output_columns=tuple(output_columns),
        )

    def transform(self, rows: list[dict[str, Any]]) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                values.append(value if math.isfinite(value) else self.numeric_impute_values[column])
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(
                    1.0 if observed == category else 0.0
                    for category in self.categorical_values[column]
                )
            matrix.append(values)
        return matrix


def run_capacity_baselines(
    interval_table_path: Path,
    interval_subsets_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
) -> dict[str, Any]:
    """Run the L0-L3 capacity baseline ladder and write report/predictions."""
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, "model level")
    selected_feature_groups = _normalize_selection(feature_groups, FEATURE_GROUPS, "feature group")
    _preflight_model_dependencies(selected_models)

    all_rows, subset_rows = load_baseline_rows(interval_table_path, interval_subsets_path, subset)
    sensitivity_rows = [
        row for row in subset_rows if not bool(row["sensitivity_flagged_monotonicity"])
    ]
    if not sensitivity_rows:
        raise ValueError("Sensitivity subset is empty after excluding monotonicity-flagged rows.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for run_scope, rows in (
        ("primary", subset_rows),
        ("sensitivity_excluding_monotonicity", sensitivity_rows),
    ):
        for split_name in SPLIT_COLUMNS:
            for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                for model_level in selected_models:
                    model_feature_groups = (
                        ("persistence",)
                        if model_level == "L0_persistence"
                        else tuple(selected_feature_groups)
                    )
                    for feature_group in model_feature_groups:
                        for target in TARGETS:
                            fold_predictions = predict_capacity_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                seed=seed,
                            )
                            metrics.append(
                                compute_metrics(
                                    test_rows,
                                    fold_predictions,
                                    target=target,
                                    subset_name=subset,
                                    run_scope=run_scope,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    train_rows=train_rows,
                                )
                            )
                            predictions.extend(
                                _prediction_rows(
                                    test_rows,
                                    fold_predictions,
                                    subset_name=subset,
                                    run_scope=run_scope,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    target=target,
                                )
                            )

    if not metrics:
        raise ValueError("No baseline metrics were generated.")

    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"interval_table_path": str(interval_table_path).encode(),
                b"interval_subsets_path": str(interval_subsets_path).encode(),
            }
        ),
        predictions_out_path,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
        },
        "seed": seed,
        "subset": subset,
        "targets": list(TARGETS),
        "model_levels": selected_models,
        "feature_groups": selected_feature_groups,
        "split_views": list(SPLIT_COLUMNS),
        "row_counts": _row_counts(all_rows, subset_rows, sensitivity_rows),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def load_baseline_rows(
    interval_table_path: Path,
    interval_subsets_path: Path,
    subset: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load and join interval rows with baseline subset flags."""
    if subset not in SUBSET_COLUMNS:
        raise ValueError(f"Unknown subset '{subset}'. Expected one of {', '.join(SUBSET_COLUMNS)}.")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    if not interval_subsets_path.exists():
        raise FileNotFoundError(f"Interval subset registry not found: {interval_subsets_path}")

    interval_rows = pq.read_table(interval_table_path).to_pylist()
    subset_rows = pq.read_table(interval_subsets_path).to_pylist()
    if len(interval_rows) != len(subset_rows):
        raise ValueError(
            "Interval table and interval subset registry row counts differ: "
            f"{len(interval_rows)} vs {len(subset_rows)}."
        )

    subset_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in subset_rows:
        key = _interval_key(row)
        if key in subset_by_key:
            raise ValueError(f"Duplicate interval subset key: {key}")
        subset_by_key[key] = row

    merged_rows: list[dict[str, Any]] = []
    for interval_row in interval_rows:
        key = _interval_key(interval_row)
        subset_row = subset_by_key.get(key)
        if subset_row is None:
            raise ValueError(f"Interval subset registry is missing interval key: {key}")
        merged = dict(interval_row)
        for column, value in subset_row.items():
            if column not in {"cell_id", "parameter_set", "replicate_id", "checkup_k", "checkup_k_next"}:
                merged[column] = value
        merged_rows.append(merged)

    selected_rows = [row for row in merged_rows if bool(row[subset])]
    if not selected_rows:
        raise ValueError(f"Requested subset '{subset}' has zero rows.")
    return merged_rows, selected_rows


def iter_split_instances(
    rows: list[dict[str, Any]],
    split_name: str,
) -> list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]]:
    """Return leave-fold-out train/test splits for one split column."""
    if split_name not in SPLIT_COLUMNS:
        raise ValueError(f"Unknown split view: {split_name}")
    folds = sorted({int(row[split_name]) for row in rows})
    if not folds:
        raise ValueError(f"Split {split_name} has no represented folds.")
    heldout_folds = folds if split_name == "condition_fold" else [fold for fold in folds if fold != 0]
    if not heldout_folds:
        raise ValueError(f"Split {split_name} has no non-zero holdout folds.")

    instances: list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]] = []
    for heldout_fold in heldout_folds:
        train_rows = [row for row in rows if int(row[split_name]) != heldout_fold]
        test_rows = [row for row in rows if int(row[split_name]) == heldout_fold]
        if not train_rows or not test_rows:
            raise ValueError(
                f"Split {split_name} fold {heldout_fold} has "
                f"train_rows={len(train_rows)} test_rows={len(test_rows)}."
            )
        instances.append((heldout_fold, train_rows, test_rows))
    return instances


def assert_no_parameter_set_leakage(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    split_name: str,
    heldout_fold: int,
) -> None:
    """Fail if any parameter set appears on both sides of a split instance."""
    train_params = {int(row["parameter_set"]) for row in train_rows}
    test_params = {int(row["parameter_set"]) for row in test_rows}
    overlap = sorted(train_params & test_params)
    if overlap:
        raise ValueError(
            f"Parameter-set leakage in {split_name} fold {heldout_fold}: {overlap}"
        )


def predict_capacity_target(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
) -> list[dict[str, float | None]]:
    """Fit/predict one target for one model and feature group."""
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")
    if model_level == "L0_persistence":
        return [_persistence_prediction(row, target) for row in test_rows]

    np, Ridge, HistGradientBoostingRegressor = _import_sklearn_stack()
    encoder = FeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows), dtype=float)
    y_train = np.asarray([_as_float(row[target]) for row in train_rows], dtype=float)

    if model_level == "L1_ridge":
        model = Ridge(alpha=1.0)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        return [_point_prediction(float(value)) for value in values]

    if model_level == "L2_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=100)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        return [_point_prediction(float(value)) for value in values]

    if model_level == "L3_quantile_hist_gradient_boosting":
        quantile_predictions: dict[float, Any] = {}
        for quantile in (0.1, 0.5, 0.9):
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                random_state=seed,
                max_iter=100,
            )
            model.fit(x_train, y_train)
            quantile_predictions[quantile] = model.predict(x_test)
        return [
            {
                "y_pred": float(quantile_predictions[0.5][idx]),
                "y_pred_q10": float(quantile_predictions[0.1][idx]),
                "y_pred_q50": float(quantile_predictions[0.5][idx]),
                "y_pred_q90": float(quantile_predictions[0.9][idx]),
            }
            for idx in range(len(test_rows))
        ]

    raise ValueError(f"Unknown model level: {model_level}")


def compute_metrics(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    target: str,
    subset_name: str,
    run_scope: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute row and condition-level regression metrics."""
    if len(test_rows) != len(predictions):
        raise ValueError("Prediction count does not match test row count.")
    errors = [
        _as_float(prediction["y_pred"]) - _as_float(row[target])
        for row, prediction in zip(test_rows, predictions)
    ]
    abs_errors = [abs(error) for error in errors]
    condition_abs_errors: dict[int, list[float]] = {}
    for row, abs_error in zip(test_rows, abs_errors):
        condition_abs_errors.setdefault(int(row["parameter_set"]), []).append(abs_error)
    condition_mae = [_mean(values) for values in condition_abs_errors.values()]

    return {
        "subset_name": subset_name,
        "run_scope": run_scope,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "target": target,
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "train_parameter_sets": len({int(row["parameter_set"]) for row in train_rows}),
        "test_parameter_sets": len({int(row["parameter_set"]) for row in test_rows}),
        "test_cells": len({str(row["cell_id"]) for row in test_rows}),
        "mae": _mean(abs_errors),
        "rmse": math.sqrt(_mean([error * error for error in errors])),
        "condition_mean_mae": _mean(condition_mae),
        "condition_median_mae": _median(condition_mae),
        "worst_condition_mae": max(condition_mae),
    }


def _prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    subset_name: str,
    run_scope: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    target: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row, prediction in zip(test_rows, predictions):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "subset_name": subset_name,
                "run_scope": run_scope,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "cell_id": row["cell_id"],
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "checkup_k_next": int(row["checkup_k_next"]),
                "sensitivity_flagged_monotonicity": bool(
                    row["sensitivity_flagged_monotonicity"]
                ),
                "y_true": _as_float(row[target]),
                "y_pred": _as_float(prediction["y_pred"]),
                "y_pred_q10": _nullable_float(prediction.get("y_pred_q10")),
                "y_pred_q50": _nullable_float(prediction.get("y_pred_q50")),
                "y_pred_q90": _nullable_float(prediction.get("y_pred_q90")),
            }
        )
    return rows


def _row_counts(
    all_rows: list[dict[str, Any]],
    subset_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "full_interval_rows": len(all_rows),
        "selected_subset_rows": len(subset_rows),
        "sensitivity_excluding_monotonicity_rows": len(sensitivity_rows),
        "baseline_clean_strict_rows": sum(bool(row["baseline_clean_strict"]) for row in all_rows),
        "baseline_clean_tolerant_rows": sum(
            bool(row["baseline_clean_tolerant"]) for row in all_rows
        ),
        "sensitivity_flagged_monotonicity_rows": sum(
            bool(row["sensitivity_flagged_monotonicity"]) for row in all_rows
        ),
        "selected_cells": len({str(row["cell_id"]) for row in subset_rows}),
        "selected_parameter_sets": len({int(row["parameter_set"]) for row in subset_rows}),
    }


def _normalize_selection(
    selected: list[str] | None,
    allowed: tuple[str, ...],
    label: str,
) -> list[str]:
    if selected is None:
        return list(allowed)
    normalized = [item.strip() for item in selected if item.strip()]
    unknown = sorted(set(normalized) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}(s): {unknown}. Allowed: {list(allowed)}")
    if not normalized:
        raise ValueError(f"At least one {label} must be selected.")
    return normalized


def _preflight_model_dependencies(model_levels: list[str]) -> None:
    if model_levels == ["L0_persistence"]:
        return
    if any(model != "L0_persistence" for model in model_levels):
        _import_sklearn_stack()


def _import_sklearn_stack() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Capacity baselines L1-L3 require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry, or select "
            "`--model-levels L0_persistence` for the dependency-free persistence baseline."
        ) from exc
    return np, Ridge, HistGradientBoostingRegressor


def _persistence_prediction(row: dict[str, Any], target: str) -> dict[str, float | None]:
    if target == "capacity_Ah_k1":
        return _point_prediction(_as_float(row["capacity_Ah_k"]))
    if target == "delta_capacity_Ah":
        return _point_prediction(0.0)
    raise ValueError(f"Unknown target: {target}")


def _point_prediction(value: float) -> dict[str, float | None]:
    return {"y_pred": value, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None}


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    numeric = _as_float(value)
    return numeric if math.isfinite(numeric) else None


def _category(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute mean of empty values.")
    return sum(values) / len(values)


def _median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute median of empty values.")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
