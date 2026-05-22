"""Milestone 0.5 capacity baseline runner."""

from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "gate5.capacity_baseline.v1"
DEFAULT_HGB_MAX_ITER = 10

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
FEATURE_GROUPS = (
    "F0_time_only",
    "F1_state_time",
    "F2_state_exposure",
    "F3_state_nominal",
    "F4_state_log_age_scalar",
)

DIAGNOSTIC_LEAKAGE_FIELDS = {"cap_aged_est_Ah", "R0_mOhm", "R1_mOhm"}

NUMERIC_FEATURES: dict[str, tuple[str, ...]] = {
    "F0_time_only": ("duration_h", "calendar_days", "checkup_k"),
    "F1_state_time": ("capacity_Ah_k", "duration_h", "calendar_days", "checkup_k"),
    "F2_state_exposure": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
    ),
    "F3_state_nominal": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "F4_state_log_age_scalar": (
        "capacity_Ah_k",
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
    "F1_state_time": (),
    "F2_state_exposure": (),
    "F3_state_nominal": ("aging_mode", "voltage_window_family"),
    "F4_state_log_age_scalar": ("aging_mode", "voltage_window_family"),
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
    numeric_scale_values: dict[str, float]
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
        scale_values: dict[str, float] = {}
        for column in numeric_columns:
            values = [_as_float(row.get(column)) for row in rows]
            finite_values = [value for value in values if math.isfinite(value)]
            mean = sum(finite_values) / len(finite_values) if finite_values else 0.0
            impute_values[column] = mean
            variance = (
                sum((value - mean) ** 2 for value in finite_values) / len(finite_values)
                if finite_values
                else 0.0
            )
            std = math.sqrt(variance)
            scale_values[column] = std if std > 0 else 1.0

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
            numeric_scale_values=scale_values,
            categorical_values=categorical_values,
            output_columns=tuple(output_columns),
        )

    def transform(
        self,
        rows: list[dict[str, Any]],
        *,
        standardize_numeric: bool = False,
    ) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                numeric = value if math.isfinite(value) else self.numeric_impute_values[column]
                if standardize_numeric:
                    numeric = (
                        numeric - self.numeric_impute_values[column]
                    ) / self.numeric_scale_values[column]
                values.append(numeric)
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
    report_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
) -> dict[str, Any]:
    """Run the L0-L3 capacity baseline ladder and write report/predictions."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, "model level")
    selected_feature_groups = _normalize_selection(feature_groups, FEATURE_GROUPS, "feature group")
    selected_targets = _normalize_selection(targets, TARGETS, "target")
    selected_split_views = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
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
        for split_name in selected_split_views:
            for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                for model_level in selected_models:
                    model_feature_groups = (
                        ("persistence",)
                        if model_level == "L0_persistence"
                        else tuple(selected_feature_groups)
                    )
                    for feature_group in model_feature_groups:
                        for target in selected_targets:
                            fold_predictions = predict_capacity_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
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

    resolved_report_dir = report_dir or _default_report_dir(out_path)
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
            "report_dir": str(resolved_report_dir),
        },
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "numeric_standardization": "train_fold_mean_std",
        "numeric_standardization_applies_to": ["L1_ridge"],
        "subset": subset,
        "targets": selected_targets,
        "model_levels": selected_models,
        "feature_groups": selected_feature_groups,
        "split_views": selected_split_views,
        "row_counts": _row_counts(all_rows, subset_rows, sensitivity_rows),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_capacity_report_artifacts(report, resolved_report_dir)
    return report


def render_capacity_report_artifacts(report: dict[str, Any], report_dir: Path) -> None:
    """Render human-readable baseline summaries from the metrics JSON."""
    report_dir.mkdir(parents=True, exist_ok=True)
    cards_dir = report_dir / "evaluation_cards"
    plots_dir = report_dir / "plots"
    cards_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    metrics = list(report["metrics"])
    leaderboard_rows = _leaderboard_rows(metrics)
    _write_csv(report_dir / "leaderboard.csv", leaderboard_rows)
    _write_csv(plots_dir / "mae_by_model_and_feature.csv", leaderboard_rows)
    _write_csv(plots_dir / "worst_condition_errors.csv", _worst_condition_rows(metrics))
    _write_csv(plots_dir / "strict_vs_tolerant_delta.csv", _sensitivity_delta_rows(metrics))
    _write_evaluation_cards(metrics, cards_dir, report)
    _write_baseline_summary(report, leaderboard_rows, report_dir / "baseline_summary.md")
    render_capacity_diagnostics(report, report_dir)


def diagnose_capacity_report(
    report_path: Path,
    out_dir: Path,
    reference_report_path: Path | None = None,
) -> dict[str, Any]:
    """Render Milestone 0.5b diagnostics from an existing baseline report."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reference_report = (
        json.loads(reference_report_path.read_text(encoding="utf-8"))
        if reference_report_path is not None
        else None
    )
    render_capacity_diagnostics(report, out_dir, reference_report=reference_report)
    return report


def render_capacity_diagnostics(
    report: dict[str, Any],
    report_dir: Path,
    reference_report: dict[str, Any] | None = None,
) -> None:
    """Render diagnostic tables and a narrative memo for a capacity report."""
    report_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = report_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_rows = _leaderboard_rows(list(report["metrics"]))
    prediction_rows = _load_prediction_rows(report)
    reference_leaderboard_rows = (
        _leaderboard_rows(list(reference_report["metrics"]))
        if reference_report is not None
        else []
    )
    reference_prediction_rows = (
        _load_prediction_rows(reference_report) if reference_report is not None else []
    )
    metadata = _condition_metadata_by_parameter_set(report)
    best_rows = _best_by_target_split_rows(
        leaderboard_rows,
        prediction_rows,
        reference_leaderboard_rows=reference_leaderboard_rows,
    )
    feature_gain_rows = _feature_gain_rows(leaderboard_rows)
    c_rate_rows = _c_rate_holdout_error_rows(
        leaderboard_rows,
        prediction_rows,
        metadata,
        reference_leaderboard_rows=reference_leaderboard_rows,
        reference_prediction_rows=reference_prediction_rows,
    )
    c_rate_grouped_rows = _c_rate_grouped_summary_rows(c_rate_rows)

    _write_csv(plots_dir / "best_by_target_split.csv", best_rows)
    _write_csv(plots_dir / "feature_gain_by_split.csv", feature_gain_rows)
    _write_csv(plots_dir / "c_rate_holdout_errors.csv", c_rate_rows)
    _write_csv(plots_dir / "c_rate_holdout_by_condition.csv", c_rate_rows)
    _write_csv(plots_dir / "c_rate_grouped_summaries.csv", c_rate_grouped_rows)
    _write_baseline_diagnostics_md(
        report,
        reference_report,
        best_rows,
        feature_gain_rows,
        _sensitivity_delta_rows(list(report["metrics"])),
        c_rate_rows,
        c_rate_grouped_rows,
        report_dir / "baseline_diagnostics.md",
    )
    _write_c_rate_error_analysis_md(
        c_rate_rows,
        c_rate_grouped_rows,
        report_dir / "c_rate_holdout_error_analysis.md",
    )
    _write_claim_readiness_md(
        report,
        best_rows,
        feature_gain_rows,
        _sensitivity_delta_rows(list(report["metrics"])),
        c_rate_rows,
        leaderboard_rows,
        report_dir / "claim_readiness.md",
    )


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
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
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
        x_train = np.asarray(
            encoder.transform(train_rows, standardize_numeric=True),
            dtype=float,
        )
        x_test = np.asarray(
            encoder.transform(test_rows, standardize_numeric=True),
            dtype=float,
        )
        model = Ridge(alpha=1.0)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        return [_point_prediction(float(value)) for value in values]

    if model_level == "L2_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
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
                max_iter=hgb_max_iter,
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
    quantile_metrics = _quantile_metrics(test_rows, predictions, target)

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
        **quantile_metrics,
    }


def _leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        key = (
            str(metric["run_scope"]),
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
        )
        grouped[key].append(metric)

    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        run_scope, model_level, feature_group, target, split_name = key
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "fold_count": len(group),
                "mean_mae": _mean([float(item["mae"]) for item in group]),
                "mean_rmse": _mean([float(item["rmse"]) for item in group]),
                "condition_mean_mae": _mean(
                    [float(item["condition_mean_mae"]) for item in group]
                ),
                "condition_median_mae": _mean(
                    [float(item["condition_median_mae"]) for item in group]
                ),
                "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in group),
                "q10_q90_interval_coverage": _mean_optional(
                    [item.get("q10_q90_interval_coverage") for item in group]
                ),
                "q10_q90_interval_width_mean": _mean_optional(
                    [item.get("q10_q90_interval_width_mean") for item in group]
                ),
                "pinball_loss_q10": _mean_optional(
                    [item.get("pinball_loss_q10") for item in group]
                ),
                "pinball_loss_q50": _mean_optional(
                    [item.get("pinball_loss_q50") for item in group]
                ),
                "pinball_loss_q90": _mean_optional(
                    [item.get("pinball_loss_q90") for item in group]
                ),
                "test_rows": sum(int(item["test_rows"]) for item in group),
                "test_parameter_sets": sum(int(item["test_parameter_sets"]) for item in group),
            }
        )
    return rows


def _worst_condition_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "run_scope": metric["run_scope"],
            "model_level": metric["model_level"],
            "feature_group": metric["feature_group"],
            "target": metric["target"],
            "split_name": metric["split_name"],
            "heldout_fold": metric["heldout_fold"],
            "worst_condition_mae": metric["worst_condition_mae"],
            "condition_mean_mae": metric["condition_mean_mae"],
            "condition_median_mae": metric["condition_median_mae"],
            "test_parameter_sets": metric["test_parameter_sets"],
        }
        for metric in metrics
    ]


def _sensitivity_delta_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for metric in metrics:
        key = (
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
            int(metric["heldout_fold"]),
        )
        by_key[key][str(metric["run_scope"])] = metric

    rows: list[dict[str, Any]] = []
    for key, group in sorted(by_key.items()):
        primary = group.get("primary")
        sensitivity = group.get("sensitivity_excluding_monotonicity")
        if not primary or not sensitivity:
            continue
        model_level, feature_group, target, split_name, heldout_fold = key
        rows.append(
            {
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "primary_mae": primary["mae"],
                "sensitivity_mae": sensitivity["mae"],
                "primary_minus_sensitivity_mae": float(primary["mae"])
                - float(sensitivity["mae"]),
                "primary_condition_mean_mae": primary["condition_mean_mae"],
                "sensitivity_condition_mean_mae": sensitivity["condition_mean_mae"],
                "primary_minus_sensitivity_condition_mean_mae": float(
                    primary["condition_mean_mae"]
                )
                - float(sensitivity["condition_mean_mae"]),
            }
        )
    return rows


def _feature_gain_rows(leaderboard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_key = {
        (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["target"]),
            str(row["split_name"]),
            str(row["feature_group"]),
        ): row
        for row in leaderboard_rows
        if str(row["feature_group"]) in FEATURE_GROUPS
    }
    feature_pairs = list(zip(FEATURE_GROUPS[1:], FEATURE_GROUPS[2:], strict=False))
    rows: list[dict[str, Any]] = []
    for run_scope in sorted({str(row["run_scope"]) for row in leaderboard_rows}):
        for model_level in sorted(
            {
                str(row["model_level"])
                for row in leaderboard_rows
                if str(row["model_level"]) != "L0_persistence"
            }
        ):
            for target in sorted({str(row["target"]) for row in leaderboard_rows}):
                for split_name in sorted({str(row["split_name"]) for row in leaderboard_rows}):
                    for from_group, to_group in feature_pairs:
                        from_row = rows_by_key.get(
                            (run_scope, model_level, target, split_name, from_group)
                        )
                        to_row = rows_by_key.get(
                            (run_scope, model_level, target, split_name, to_group)
                        )
                        if not from_row or not to_row:
                            continue
                        rows.append(
                            {
                                "run_scope": run_scope,
                                "model_level": model_level,
                                "target": target,
                                "split_name": split_name,
                                "from_feature_group": from_group,
                                "to_feature_group": to_group,
                                "from_condition_mean_mae": from_row["condition_mean_mae"],
                                "to_condition_mean_mae": to_row["condition_mean_mae"],
                                "condition_mean_mae_gain": float(
                                    from_row["condition_mean_mae"]
                                )
                                - float(to_row["condition_mean_mae"]),
                                "from_worst_condition_mae": from_row["worst_condition_mae"],
                                "to_worst_condition_mae": to_row["worst_condition_mae"],
                                "worst_condition_mae_gain": float(
                                    from_row["worst_condition_mae"]
                                )
                                - float(to_row["worst_condition_mae"]),
                            }
                        )
    return rows


def _best_by_target_split_rows(
    leaderboard_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    reference_leaderboard_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    primary_rows = [row for row in leaderboard_rows if row["run_scope"] == "primary"]
    l0_reference_rows = _l0_reference_rows(reference_leaderboard_rows or [])
    rows: list[dict[str, Any]] = []
    for target in sorted({str(row["target"]) for row in primary_rows}):
        for split_name in sorted({str(row["split_name"]) for row in primary_rows}):
            group = [
                row
                for row in primary_rows
                if row["target"] == target and row["split_name"] == split_name
            ]
            if not group:
                continue
            best = min(
                group,
                key=lambda row: (
                    float(row["condition_mean_mae"]),
                    float(row["worst_condition_mae"]),
                ),
            )
            l0 = next(
                (
                    row
                    for row in group
                    if row["model_level"] == "L0_persistence"
                    and row["feature_group"] == "persistence"
                ),
                None,
            )
            l0_reference_status = "current_report" if l0 is not None else "reference_missing"
            if l0 is None:
                l0 = l0_reference_rows.get((target, split_name))
                if l0 is not None:
                    l0_reference_status = "reference_report"
            worst_parameter_set, worst_mae = _worst_condition_for_selection(
                prediction_rows,
                run_scope="primary",
                model_level=str(best["model_level"]),
                feature_group=str(best["feature_group"]),
                target=target,
                split_name=split_name,
            )
            l0_condition_mean = _optional_float(
                l0["condition_mean_mae"] if l0 is not None else None
            )
            best_condition_mean = float(best["condition_mean_mae"])
            improvement = (
                l0_condition_mean - best_condition_mean
                if l0_condition_mean is not None
                else "reference_missing"
            )
            rows.append(
                {
                    "target": target,
                    "split_name": split_name,
                    "best_model_level": best["model_level"],
                    "best_feature_group": best["feature_group"],
                    "best_condition_mean_mae": best_condition_mean,
                    "best_worst_condition_mae": best["worst_condition_mae"],
                    "worst_parameter_set": worst_parameter_set,
                    "worst_parameter_set_mae": worst_mae,
                    "l0_condition_mean_mae": (
                        l0_condition_mean
                        if l0_condition_mean is not None
                        else "reference_missing"
                    ),
                    "l0_reference_status": l0_reference_status,
                    "condition_mean_mae_improvement_vs_l0": improvement,
                }
            )
    return rows


def _c_rate_holdout_error_rows(
    leaderboard_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    metadata: dict[int, dict[str, Any]],
    reference_leaderboard_rows: list[dict[str, Any]] | None = None,
    reference_prediction_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    best_rows = [
        row
        for row in _best_by_target_split_rows(
            leaderboard_rows,
            prediction_rows,
            reference_leaderboard_rows=reference_leaderboard_rows,
        )
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    output_rows: list[dict[str, Any]] = []
    for best in best_rows:
        target = str(best["target"])
        best_errors = _condition_mae_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level=str(best["best_model_level"]),
            feature_group=str(best["best_feature_group"]),
            target=target,
            split_name="c_rate_holdout_fold",
        )
        l0_errors = _condition_mae_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level="L0_persistence",
            feature_group="persistence",
            target=target,
            split_name="c_rate_holdout_fold",
        )
        persistence_reference_status = "current_report"
        if not l0_errors and reference_prediction_rows:
            l0_errors = _condition_mae_for_selection(
                reference_prediction_rows,
                run_scope="primary",
                model_level="L0_persistence",
                feature_group="persistence",
                target=target,
                split_name="c_rate_holdout_fold",
            )
            persistence_reference_status = (
                "reference_report" if l0_errors else "reference_missing"
            )
        elif not l0_errors:
            persistence_reference_status = "reference_missing"
        for parameter_set, best_error in sorted(best_errors.items()):
            meta = metadata.get(parameter_set, {})
            persistence_error = l0_errors.get(parameter_set)
            improvement = (
                persistence_error - best_error
                if persistence_error is not None
                else "reference_missing"
            )
            output_rows.append(
                {
                    "target": target,
                    "parameter_set": parameter_set,
                    "replicate_count": meta.get("replicate_count"),
                    "aging_mode": meta.get("aging_mode"),
                    "nominal_temperature_C": meta.get("nominal_temperature_C"),
                    "voltage_window_family": meta.get("voltage_window_family"),
                    "nominal_charge_C_rate": meta.get("nominal_charge_C_rate"),
                    "nominal_discharge_C_rate": meta.get("nominal_discharge_C_rate"),
                    "n_intervals": meta.get("n_intervals"),
                    "capacity_Ah_k_min": meta.get("capacity_Ah_k_min"),
                    "capacity_Ah_k_max": meta.get("capacity_Ah_k_max"),
                    "delta_capacity_Ah_min": meta.get("delta_capacity_Ah_min"),
                    "delta_capacity_Ah_max": meta.get("delta_capacity_Ah_max"),
                    "best_model_level": best["best_model_level"],
                    "best_feature_group": best["best_feature_group"],
                    "best_model_error": best_error,
                    "persistence_error": (
                        persistence_error
                        if persistence_error is not None
                        else "reference_missing"
                    ),
                    "persistence_reference_status": persistence_reference_status,
                    "error_improvement_vs_persistence": improvement,
                }
            )
    return output_rows


def _l0_reference_rows(
    leaderboard_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for row in leaderboard_rows:
        if (
            str(row.get("run_scope")) != "primary"
            or str(row.get("model_level")) != "L0_persistence"
            or str(row.get("feature_group")) != "persistence"
        ):
            continue
        rows[(str(row["target"]), str(row["split_name"]))] = row
    return rows


def _c_rate_grouped_summary_rows(c_rate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouping_specs = (
        ("temperature", lambda row: _group_value(row.get("nominal_temperature_C"))),
        ("voltage_window_family", lambda row: _group_value(row.get("voltage_window_family"))),
        ("target", lambda row: _group_value(row.get("target"))),
        ("parameter_set", lambda row: _group_value(row.get("parameter_set"))),
        ("interval_count_bucket", lambda row: _interval_count_bucket(row.get("n_intervals"))),
        ("capacity_Ah_k_range", lambda row: _value_range_bucket(
            row.get("capacity_Ah_k_min"),
            row.get("capacity_Ah_k_max"),
            thresholds=(2.4, 2.6, 2.8),
            labels=("<2.4", "2.4-2.6", "2.6-2.8", ">=2.8"),
        )),
        ("delta_capacity_Ah_range", lambda row: _value_range_bucket(
            row.get("delta_capacity_Ah_min"),
            row.get("delta_capacity_Ah_max"),
            thresholds=(-0.6, -0.4, -0.2),
            labels=("<-0.6", "-0.6--0.4", "-0.4--0.2", ">=-0.2"),
        )),
    )
    output_rows: list[dict[str, Any]] = []
    for group_name, key_fn in grouping_specs:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in c_rate_rows:
            grouped[key_fn(row)].append(row)
        for group_value, rows in sorted(grouped.items()):
            best_errors = [_nullable_float(row.get("best_model_error")) for row in rows]
            persistence_errors = [
                _nullable_float(row.get("persistence_error")) for row in rows
            ]
            improvements = [
                _nullable_float(row.get("error_improvement_vs_persistence"))
                for row in rows
            ]
            output_rows.append(
                {
                    "grouping": group_name,
                    "group_value": group_value,
                    "row_count": len(rows),
                    "parameter_set_count": len({int(row["parameter_set"]) for row in rows}),
                    "total_intervals": sum(
                        int(row["n_intervals"]) for row in rows if row.get("n_intervals") is not None
                    ),
                    "mean_best_model_error": _mean_optional(best_errors),
                    "mean_persistence_error": _mean_optional(persistence_errors),
                    "mean_error_improvement_vs_persistence": _mean_optional(improvements),
                    "max_best_model_error": _max_optional(best_errors),
                }
            )
    return output_rows


def _write_baseline_diagnostics_md(
    report: dict[str, Any],
    reference_report: dict[str, Any] | None,
    best_rows: list[dict[str, Any]],
    feature_gain_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    c_rate_grouped_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    primary_best = sorted(
        best_rows,
        key=lambda row: float(row["best_condition_mean_mae"]),
    )[:10]
    c_rate_best = sorted(
        [row for row in best_rows if row["split_name"] == "c_rate_holdout_fold"],
        key=lambda row: float(row["best_condition_mean_mae"]),
    )
    gains = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
    ]
    sensitivity_deltas = [
        float(row["primary_minus_sensitivity_condition_mean_mae"])
        for row in sensitivity_rows
    ]
    lines = [
        "# Capacity Baseline Diagnostics",
        "",
        f"Source report: `{report['outputs']['report']}`",
        f"Generated at UTC: `{datetime.now(UTC).isoformat()}`",
        f"Schema version: `{report['schema_version']}`",
        f"HGB max iterations: `{report.get('hgb_max_iter')}`",
        f"Numeric standardization: `{report.get('numeric_standardization', 'none')}`",
        f"L0 reference report: `{_reference_report_label(reference_report)}`",
        "",
        "## Best Rows By Target And Split",
        "",
        "| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |",
        "|---|---|---|---|---:|---|---:|---:|",
    ]
    for row in primary_best:
        improvement = row["condition_mean_mae_improvement_vs_l0"]
        lines.append(
            "| "
            f"`{row['target']}` | `{row['split_name']}` | `{row['best_model_level']}` | "
            f"`{row['best_feature_group']}` | {float(row['best_condition_mean_mae']):.6g} | "
            f"`{row['l0_reference_status']}` | "
            f"{_format_diagnostic_value(improvement)} | {row['worst_parameter_set']} |"
        )

    lines.extend(
        [
            "",
            "## C-Rate Holdout",
            "",
            "The C-rate holdout remains the hardest split in the bounded capacity runs.",
            "",
            "| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |",
            "|---|---|---|---:|---|---:|",
        ]
    )
    for row in c_rate_best:
        lines.append(
            "| "
            f"`{row['target']}` | `{row['best_model_level']}` | `{row['best_feature_group']}` | "
            f"{float(row['best_condition_mean_mae']):.6g} | "
            f"`{row['l0_reference_status']}` | "
            f"{_format_diagnostic_value(row['condition_mean_mae_improvement_vs_l0'])} |"
        )

    lines.extend(
        [
            "",
            "## Feature Gains",
            "",
            f"Primary feature-gain rows: `{len(gains)}`",
            f"Mean primary adjacent-feature gain: `{_format_optional_float(_mean(gains) if gains else None)}`",
            "",
            "Positive gain means the later feature group reduced condition-mean MAE.",
            "",
            "## Strict Vs Tolerant Sensitivity",
            "",
            f"Sensitivity rows: `{len(sensitivity_rows)}`",
            f"Mean primary-minus-sensitivity condition-mean MAE: `{_format_optional_float(_mean(sensitivity_deltas) if sensitivity_deltas else None)}`",
            f"Median primary-minus-sensitivity condition-mean MAE: `{_format_optional_float(_median(sensitivity_deltas) if sensitivity_deltas else None)}`",
            "",
            "## Diagnostic Tables",
            "",
            "- `plots/best_by_target_split.csv`",
            "- `plots/feature_gain_by_split.csv`",
            "- `plots/c_rate_holdout_errors.csv`",
            "- `plots/c_rate_holdout_by_condition.csv`",
            "- `plots/c_rate_grouped_summaries.csv`",
            "- `plots/strict_vs_tolerant_delta.csv`",
            "- `plots/worst_condition_errors.csv`",
            "- `c_rate_holdout_error_analysis.md`",
            "- `claim_readiness.md`",
            "",
            f"C-rate diagnostic rows: `{len(c_rate_rows)}`",
            f"C-rate grouped summary rows: `{len(c_rate_grouped_rows)}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_c_rate_error_analysis_md(
    c_rate_rows: list[dict[str, Any]],
    c_rate_grouped_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    worst_rows = sorted(
        c_rate_rows,
        key=lambda row: float(row["best_model_error"]),
        reverse=True,
    )[:10]
    lines = [
        "# C-Rate Holdout Error Analysis",
        "",
        "This diagnostic focuses on the high-C-rate holdout conditions because the",
        "bounded L0-L3 baseline report identified C-rate transfer as the hardest",
        "split.",
        "",
        f"Diagnostic rows: `{len(c_rate_rows)}`",
        "",
        "## Worst Held-Out Conditions",
        "",
        "| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |",
        "|---|---:|---:|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in worst_rows:
        lines.append(
            "| "
            f"`{row['target']}` | {row['parameter_set']} | "
            f"{_format_optional_float(row['nominal_temperature_C'])} | "
            f"`{row['voltage_window_family']}` | "
            f"{_format_optional_float(row['nominal_charge_C_rate'])} | "
            f"{row['n_intervals']} | "
            f"`{row['best_model_level']}:{row['best_feature_group']}` | "
            f"{_format_diagnostic_value(row['best_model_error'])} | "
            f"{_format_diagnostic_value(row['persistence_error'])} | "
            f"{_format_diagnostic_value(row['error_improvement_vs_persistence'])} |"
        )

    lines.extend(["", "## Grouped Summaries", ""])
    for grouping in (
        "temperature",
        "voltage_window_family",
        "target",
        "parameter_set",
        "interval_count_bucket",
        "capacity_Ah_k_range",
        "delta_capacity_Ah_range",
    ):
        rows = [row for row in c_rate_grouped_rows if row["grouping"] == grouping]
        if not rows:
            continue
        lines.extend(
            [
                f"### {grouping}",
                "",
                "| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            lines.append(
                "| "
                f"`{row['group_value']}` | {row['row_count']} | "
                f"{row['parameter_set_count']} | {row['total_intervals']} | "
                f"{_format_diagnostic_value(row['mean_best_model_error'])} | "
                f"{_format_diagnostic_value(row['mean_persistence_error'])} | "
                f"{_format_diagnostic_value(row['mean_error_improvement_vs_persistence'])} | "
                f"{_format_diagnostic_value(row['max_best_model_error'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "",
            "## Table",
            "",
            "Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.",
            "Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_claim_readiness_md(
    report: dict[str, Any],
    best_rows: list[dict[str, Any]],
    feature_gain_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    leaderboard_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    f2_to_f3 = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
        and row["from_feature_group"] == "F2_state_exposure"
        and row["to_feature_group"] == "F3_state_nominal"
    ]
    f3_to_f4 = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
        and row["from_feature_group"] == "F3_state_nominal"
        and row["to_feature_group"] == "F4_state_log_age_scalar"
    ]
    sensitivity_deltas = [
        abs(float(row["primary_minus_sensitivity_condition_mean_mae"]))
        for row in sensitivity_rows
    ]
    quantile_coverages = [
        _nullable_float(metric.get("q10_q90_interval_coverage"))
        for metric in report["metrics"]
        if str(metric.get("run_scope")) == "primary"
        and str(metric.get("model_level")) == "L3_quantile_hist_gradient_boosting"
    ]
    c_rate_best_errors = [
        _nullable_float(row.get("best_condition_mean_mae"))
        for row in best_rows
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    other_best_errors = [
        _nullable_float(row.get("best_condition_mean_mae"))
        for row in best_rows
        if row["split_name"] != "c_rate_holdout_fold"
    ]
    lines = [
        "# Capacity Baseline Claim Readiness",
        "",
        "This table is a Milestone 0.5c synthesis aid. It does not authorize",
        "EIS/PULSE modeling, knee prediction, sequence models, neural models,",
        "policy ranking, or CBAT.",
        "",
        "| Claim | Status | Evidence | Decision |",
        "|---|---|---|---|",
        "| State-aware baselines beat weak time-only baselines | Supported | "
        "`F1_state_time` and later groups include prior capacity state and dominate "
        "the weak `F0_time_only` sanity baseline in the capacity ladder. | Keep "
        "state-aware groups as the first forecast baseline. |",
        "| Nominal protocol features help | Supported | "
        f"`F2_state_exposure -> F3_state_nominal` mean gain "
        f"{_format_diagnostic_value(_mean(f2_to_f3) if f2_to_f3 else None)} "
        f"across {len(f2_to_f3)} primary rows. | Keep nominal protocol features. |",
        "| LOG_AGE scalar features help | Partially supported | "
        f"`F3_state_nominal -> F4_state_log_age_scalar` mean gain "
        f"{_format_diagnostic_value(_mean(f3_to_f4) if f3_to_f4 else None)}; "
        "the benefit is model-dependent and strongest in focused HGB. | Build "
        "stronger log-derived stress features before adding modalities. |",
        "| C-rate holdout is hardest | Supported | "
        f"Best C-rate condition-mean MAE max "
        f"{_format_diagnostic_value(_max_optional(c_rate_best_errors))}, "
        f"other split best max {_format_diagnostic_value(_max_optional(other_best_errors))}. | "
        "Focus next engineering on C-rate/stress exposure. |",
        "| Monotonicity policy changes conclusions | Not supported | "
        f"Mean absolute strict-vs-tolerant delta "
        f"{_format_diagnostic_value(_mean(sensitivity_deltas) if sensitivity_deltas else None)}. | "
        "Keep tolerant subset as primary with strict sensitivity. |",
        "| Quantile HGB is calibrated | Not supported | "
        f"Mean q10-q90 coverage "
        f"{_format_diagnostic_value(_mean_optional(quantile_coverages))}; nominal "
        "central coverage is 0.8. | Treat quantile metrics as diagnostics only. |",
        "",
        "C-rate condition rows used for stress analysis: "
        f"`{len(c_rate_rows)}`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_evaluation_cards(
    metrics: list[dict[str, Any]],
    cards_dir: Path,
    report: dict[str, Any],
) -> None:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        key = (
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
        )
        grouped[key].append(metric)

    for key, group in sorted(grouped.items()):
        model_level, feature_group, target, split_name = key
        primary = [item for item in group if item["run_scope"] == "primary"]
        sensitivity = [
            item for item in group if item["run_scope"] == "sensitivity_excluding_monotonicity"
        ]
        card = {
            "schema_version": SCHEMA_VERSION,
            "model_level": model_level,
            "feature_group": feature_group,
            "target": target,
            "split_name": split_name,
            "row_counts": report["row_counts"],
            "primary_summary": _metric_summary(primary),
            "sensitivity_excluding_monotonicity_summary": _metric_summary(sensitivity),
            "fold_metrics": group,
        }
        filename = "__".join(_slug(part) for part in key) + ".json"
        (cards_dir / filename).write_text(
            json.dumps(card, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _metric_summary(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not metrics:
        return {}
    return {
        "fold_count": len(metrics),
        "mean_mae": _mean([float(item["mae"]) for item in metrics]),
        "mean_rmse": _mean([float(item["rmse"]) for item in metrics]),
        "condition_mean_mae": _mean([float(item["condition_mean_mae"]) for item in metrics]),
        "condition_median_mae": _mean(
            [float(item["condition_median_mae"]) for item in metrics]
        ),
        "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in metrics),
    }


def _write_baseline_summary(
    report: dict[str, Any],
    leaderboard_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    row_counts = report["row_counts"]
    primary_rows = [row for row in leaderboard_rows if row["run_scope"] == "primary"]
    best_rows = sorted(primary_rows, key=lambda row: float(row["condition_mean_mae"]))[:10]
    lines = [
        "# Capacity Baseline Summary",
        "",
        f"Schema version: `{report['schema_version']}`",
        f"Generated at UTC: `{report['generated_at_utc']}`",
        f"Primary subset: `{report['subset']}`",
        "",
        "## Row Counts",
        "",
        "| Count | Value |",
        "|---|---:|",
    ]
    for key, value in row_counts.items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Best Primary Rows",
            "",
            "| Model | Feature group | Target | Split | Condition mean MAE | Worst condition MAE |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for row in best_rows:
        lines.append(
            "| "
            f"`{row['model_level']}` | `{row['feature_group']}` | `{row['target']}` | "
            f"`{row['split_name']}` | {float(row['condition_mean_mae']):.6g} | "
            f"{float(row['worst_condition_mae']):.6g} |"
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `leaderboard.csv`",
            "- `evaluation_cards/*.json`",
            "- `plots/mae_by_model_and_feature.csv`",
            "- `plots/worst_condition_errors.csv`",
            "- `plots/strict_vs_tolerant_delta.csv`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def _load_prediction_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    predictions_path = Path(report["outputs"]["predictions"])
    if not predictions_path.exists():
        return []
    return pq.read_table(predictions_path).to_pylist()


def _condition_metadata_by_parameter_set(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    interval_path = Path(report["inputs"]["interval_table"])
    if not interval_path.exists():
        return {}
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in pq.read_table(interval_path).to_pylist():
        groups[int(row["parameter_set"])].append(row)

    metadata: dict[int, dict[str, Any]] = {}
    for parameter_set, rows in groups.items():
        capacity_values = [_as_float(row.get("capacity_Ah_k")) for row in rows]
        delta_values = [_as_float(row.get("delta_capacity_Ah")) for row in rows]
        finite_capacity = [value for value in capacity_values if math.isfinite(value)]
        finite_delta = [value for value in delta_values if math.isfinite(value)]
        metadata[parameter_set] = {
            "replicate_count": len({str(row["cell_id"]) for row in rows}),
            "aging_mode": _first_non_empty(row.get("aging_mode") for row in rows),
            "nominal_temperature_C": _first_finite(
                _as_float(row.get("nominal_temperature_C")) for row in rows
            ),
            "voltage_window_family": _first_non_empty(
                row.get("voltage_window_family") for row in rows
            ),
            "nominal_charge_C_rate": _first_finite(
                _as_float(row.get("nominal_charge_C_rate")) for row in rows
            ),
            "nominal_discharge_C_rate": _first_finite(
                _as_float(row.get("nominal_discharge_C_rate")) for row in rows
            ),
            "n_intervals": len(rows),
            "capacity_Ah_k_min": min(finite_capacity) if finite_capacity else None,
            "capacity_Ah_k_max": max(finite_capacity) if finite_capacity else None,
            "delta_capacity_Ah_min": min(finite_delta) if finite_delta else None,
            "delta_capacity_Ah_max": max(finite_delta) if finite_delta else None,
        }
    return metadata


def _condition_mae_for_selection(
    prediction_rows: list[dict[str, Any]],
    *,
    run_scope: str,
    model_level: str,
    feature_group: str,
    target: str,
    split_name: str,
) -> dict[int, float]:
    grouped_errors: dict[int, list[float]] = defaultdict(list)
    for row in prediction_rows:
        if (
            str(row["run_scope"]) != run_scope
            or str(row["model_level"]) != model_level
            or str(row["feature_group"]) != feature_group
            or str(row["target"]) != target
            or str(row["split_name"]) != split_name
        ):
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        grouped_errors[int(row["parameter_set"])].append(abs(y_pred - y_true))
    return {
        parameter_set: _mean(errors)
        for parameter_set, errors in grouped_errors.items()
        if errors
    }


def _worst_condition_for_selection(
    prediction_rows: list[dict[str, Any]],
    *,
    run_scope: str,
    model_level: str,
    feature_group: str,
    target: str,
    split_name: str,
) -> tuple[int | None, float | None]:
    errors = _condition_mae_for_selection(
        prediction_rows,
        run_scope=run_scope,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
        split_name=split_name,
    )
    if not errors:
        return None, None
    return max(errors.items(), key=lambda item: item[1])


def _quantile_metrics(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    target: str,
) -> dict[str, float | None]:
    quantile_rows: list[tuple[float, float, float, float]] = []
    for row, prediction in zip(test_rows, predictions):
        y_true = _as_float(row[target])
        q10 = _nullable_float(prediction.get("y_pred_q10"))
        q50 = _nullable_float(prediction.get("y_pred_q50"))
        q90 = _nullable_float(prediction.get("y_pred_q90"))
        if (
            not math.isfinite(y_true)
            or q10 is None
            or q50 is None
            or q90 is None
        ):
            return _empty_quantile_metrics()
        quantile_rows.append((y_true, q10, q50, q90))

    if not quantile_rows:
        return _empty_quantile_metrics()
    return {
        "q10_q90_interval_coverage": _mean(
            [1.0 if q10 <= y_true <= q90 else 0.0 for y_true, q10, _, q90 in quantile_rows]
        ),
        "q10_q90_interval_width_mean": _mean(
            [q90 - q10 for _, q10, _, q90 in quantile_rows]
        ),
        "pinball_loss_q10": _mean(
            [_pinball_loss(y_true, q10, 0.1) for y_true, q10, _, _ in quantile_rows]
        ),
        "pinball_loss_q50": _mean(
            [_pinball_loss(y_true, q50, 0.5) for y_true, _, q50, _ in quantile_rows]
        ),
        "pinball_loss_q90": _mean(
            [_pinball_loss(y_true, q90, 0.9) for y_true, _, _, q90 in quantile_rows]
        ),
    }


def _empty_quantile_metrics() -> dict[str, None]:
    return {
        "q10_q90_interval_coverage": None,
        "q10_q90_interval_width_mean": None,
        "pinball_loss_q10": None,
        "pinball_loss_q50": None,
        "pinball_loss_q90": None,
    }


def _pinball_loss(y_true: float, prediction: float, quantile: float) -> float:
    error = y_true - prediction
    return max(quantile * error, (quantile - 1.0) * error)


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


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _slug(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace("=", "-")
        .replace(".", "p")
    )


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


def _optional_float(value: Any) -> float | None:
    numeric = _nullable_float(value)
    return numeric


def _format_optional_float(value: Any) -> str:
    numeric = _optional_float(value)
    return "NA" if numeric is None else f"{numeric:.6g}"


def _format_diagnostic_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _format_optional_float(value)


def _mean_optional(values: list[Any]) -> float | None:
    numeric_values = [_nullable_float(value) for value in values]
    finite_values = [value for value in numeric_values if value is not None]
    return _mean(finite_values) if finite_values else None


def _max_optional(values: list[Any]) -> float | None:
    numeric_values = [_nullable_float(value) for value in values]
    finite_values = [value for value in numeric_values if value is not None]
    return max(finite_values) if finite_values else None


def _reference_report_label(reference_report: dict[str, Any] | None) -> str:
    if reference_report is None:
        return "none"
    return str(reference_report.get("outputs", {}).get("report", "provided"))


def _group_value(value: Any) -> str:
    if value is None:
        return "unknown"
    numeric = _nullable_float(value)
    if numeric is not None:
        return f"{numeric:g}"
    text = str(value).strip()
    return text if text else "unknown"


def _interval_count_bucket(value: Any) -> str:
    numeric = _nullable_float(value)
    if numeric is None:
        return "unknown"
    count = int(numeric)
    if count <= 5:
        return "<=5"
    if count <= 10:
        return "6-10"
    if count <= 20:
        return "11-20"
    return ">20"


def _value_range_bucket(
    minimum: Any,
    maximum: Any,
    *,
    thresholds: tuple[float, float, float],
    labels: tuple[str, str, str, str],
) -> str:
    values = [_nullable_float(minimum), _nullable_float(maximum)]
    finite_values = [value for value in values if value is not None]
    if not finite_values:
        return "unknown"
    midpoint = sum(finite_values) / len(finite_values)
    if midpoint < thresholds[0]:
        return labels[0]
    if midpoint < thresholds[1]:
        return labels[1]
    if midpoint < thresholds[2]:
        return labels[2]
    return labels[3]


def _first_non_empty(values: Any) -> str | None:
    for value in values:
        text = _category(value)
        if text:
            return text
    return None


def _first_finite(values: Any) -> float | None:
    for value in values:
        if math.isfinite(value):
            return value
    return None


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
