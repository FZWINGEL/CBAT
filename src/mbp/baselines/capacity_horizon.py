"""Non-neural multi-horizon capacity forecasting baselines."""

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

SCHEMA_VERSION = "gate60.capacity_horizon_baseline.v1"
PREDICTION_SCHEMA_VERSION = "gate60.capacity_horizon_predictions.v1"
TARGETS = ("capacity_Ah_kh", "delta_capacity_Ah_h")
MODEL_LEVELS = (
    "MH0_persistence",
    "MH1_prior_slope_linear",
    "MH2_ridge",
    "MH3_hist_gradient_boosting",
)
FEATURE_GROUPS = (
    "K0_prior_capacity",
    "K1_prior_state_time",
    "K2_nominal_condition",
    "K3_oracle_exposure_diagnostic",
)
DEFAULT_TARGETS = TARGETS
DEFAULT_MODELS = MODEL_LEVELS
DEFAULT_FEATURE_GROUPS = ("K0_prior_capacity", "K1_prior_state_time", "K2_nominal_condition")
DEFAULT_HORIZONS = (1, 2, 3, 5)
ORACLE_FEATURE_GROUPS = {"K3_oracle_exposure_diagnostic"}
NUMERIC_FEATURES = {
    "K0_prior_capacity": ("capacity_Ah_k", "horizon_checkups", "checkup_k"),
    "K1_prior_state_time": (
        "capacity_Ah_k",
        "soh_k",
        "horizon_checkups",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "cumulative_q_Ah_k",
        "prior_delta_capacity_Ah",
        "prior_capacity_slope_per_day",
    ),
    "K2_nominal_condition": (
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
    ),
    "K3_oracle_exposure_diagnostic": (
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
        "horizon_interval_count",
        "horizon_duration_h",
        "horizon_calendar_days",
        "horizon_log_age_efc_delta",
        "horizon_log_age_delta_q_Ah",
        "horizon_log_age_row_count",
    ),
}
CATEGORICAL_FEATURES = {
    "K0_prior_capacity": (),
    "K1_prior_state_time": (),
    "K2_nominal_condition": ("voltage_window_family", "profile_label", "aging_mode"),
    "K3_oracle_exposure_diagnostic": ("voltage_window_family", "profile_label", "aging_mode"),
}
FUTURE_EXPOSURE_FIELDS = {
    "horizon_interval_count",
    "horizon_duration_h",
    "horizon_calendar_days",
    "horizon_log_age_efc_delta",
    "horizon_log_age_delta_q_Ah",
    "horizon_log_age_row_count",
}

CAPACITY_HORIZON_PREDICTION_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
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
        ("target_checkup_k", pa.int32()),
        ("horizon_checkups", pa.int32()),
        ("y_true", pa.float64()),
        ("y_pred", pa.float64()),
    ]
)


@dataclass(frozen=True)
class HorizonFeatureEncoder:
    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    numeric_scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "HorizonFeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown capacity horizon feature group: {feature_group}")
        numeric_columns = NUMERIC_FEATURES[feature_group]
        categorical_columns = CATEGORICAL_FEATURES[feature_group]
        if feature_group not in ORACLE_FEATURE_GROUPS:
            leakage = set(numeric_columns) & FUTURE_EXPOSURE_FIELDS
            if leakage:
                raise ValueError(f"Prospective feature group includes future exposure fields: {sorted(leakage)}")

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


def run_capacity_horizon_baselines(
    horizon_table_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    out_dir: Path | None = None,
    *,
    seed: int = 42,
    hgb_max_iter: int = 50,
    targets: list[str] | None = None,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    split_views: list[str] | None = None,
    horizons: list[int] | None = None,
) -> dict[str, Any]:
    """Run non-neural multi-horizon capacity forecasting baselines."""
    selected_targets = _normalize_selection(targets, TARGETS, DEFAULT_TARGETS, "target")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, DEFAULT_MODELS, "model level")
    selected_features = _normalize_selection(feature_groups, FEATURE_GROUPS, DEFAULT_FEATURE_GROUPS, "feature group")
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, SPLIT_COLUMNS, "split view")
    selected_horizons = _normalize_horizons(horizons)
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    if any(model in {"MH2_ridge", "MH3_hist_gradient_boosting"} for model in selected_models):
        _import_sklearn_stack()
    _audit_feature_groups(selected_features)

    rows = [
        row
        for row in pq.read_table(horizon_table_path).to_pylist()
        if int(row["horizon_checkups"]) in set(selected_horizons)
    ]
    if not rows:
        raise ValueError("Capacity horizon table has no rows for the selected horizons.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for horizon in selected_horizons:
                horizon_train = [row for row in train_rows if int(row["horizon_checkups"]) == horizon]
                horizon_test = [row for row in test_rows if int(row["horizon_checkups"]) == horizon]
                if not horizon_train or not horizon_test:
                    continue
                for target in selected_targets:
                    for model_level in selected_models:
                        model_features = (
                            ("persistence",)
                            if model_level == "MH0_persistence"
                            else ("prior_slope",)
                            if model_level == "MH1_prior_slope_linear"
                            else tuple(selected_features)
                        )
                        for feature_group in model_features:
                            y_pred = predict_capacity_horizon(
                                model_level,
                                feature_group,
                                horizon_train,
                                horizon_test,
                                target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                            )
                            metrics.append(
                                capacity_horizon_metrics(
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
                                    target=target,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                )
                            )

    if not metrics:
        raise ValueError("No capacity horizon metrics were generated.")

    resolved_out_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=CAPACITY_HORIZON_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": PREDICTION_SCHEMA_VERSION.encode(),
                b"horizon_table_path": str(horizon_table_path).encode(),
            }
        ),
        predictions_out_path,
    )
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {"horizon_table": str(horizon_table_path)},
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(resolved_out_dir),
        },
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "targets": selected_targets,
        "model_levels": selected_models,
        "feature_groups": selected_features,
        "split_views": selected_splits,
        "horizons": selected_horizons,
        "leakage_audit": leakage_audit(selected_features),
        "row_counts": {
            "rows": len(rows),
            "cells": len({str(row["cell_id"]) for row in rows}),
            "parameter_sets": len({int(row["parameter_set"]) for row in rows}),
            "metrics": len(metrics),
            "predictions": len(predictions),
        },
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_capacity_horizon_artifacts(report, resolved_out_dir)
    return report


def predict_capacity_horizon(
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    *,
    seed: int,
    hgb_max_iter: int,
) -> list[float]:
    if target not in TARGETS:
        raise ValueError(f"Unknown capacity horizon target: {target}")
    if model_level == "MH0_persistence":
        return [_persistence_prediction(row, target) for row in test_rows]
    if model_level == "MH1_prior_slope_linear":
        return [_prior_slope_prediction(row, target) for row in test_rows]

    _, Ridge, HistGradientBoostingRegressor = _import_sklearn_stack()
    encoder = HorizonFeatureEncoder.fit(train_rows, feature_group)
    standardize = model_level == "MH2_ridge"
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=standardize), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=standardize), dtype=float)
    y_train = np.asarray([_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")
    if model_level == "MH2_ridge":
        model = Ridge(alpha=1.0)
    elif model_level == "MH3_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown model level: {model_level}")
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict(x_test)]


def capacity_horizon_metrics(
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
    y_true = [_target_value(row, target) for row in test_rows]
    errors = [pred - true for pred, true in zip(predictions, y_true)]
    abs_errors = [abs(error) for error in errors]
    condition_rows = _condition_mae_rows(test_rows, abs_errors)
    return {
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
        "condition_median_mae": _median([row["mae"] for row in condition_rows]),
        "worst_condition_mae": max(row["mae"] for row in condition_rows),
        "oracle_exposure_feature_group": feature_group in ORACLE_FEATURE_GROUPS,
    }


def prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[float],
    *,
    target: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
) -> list[dict[str, Any]]:
    rows = []
    for row, prediction in zip(test_rows, predictions):
        rows.append(
            {
                "schema_version": PREDICTION_SCHEMA_VERSION,
                "run_scope": "primary",
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "cell_id": str(row["cell_id"]),
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "target_checkup_k": int(row["target_checkup_k"]),
                "horizon_checkups": int(row["horizon_checkups"]),
                "y_true": _target_value(row, target),
                "y_pred": float(prediction),
            }
        )
    return rows


def render_capacity_horizon_artifacts(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    leaderboard = leaderboard_rows(metrics)
    _write_csv(out_dir / "leaderboard.csv", leaderboard)
    _write_csv(plots_dir / "horizon_performance.csv", metrics)
    _write_csv(
        plots_dir / "c_rate_horizon_performance.csv",
        [row for row in metrics if row["split_name"] == "c_rate_holdout_fold"],
    )
    _write_csv(plots_dir / "oracle_exposure_gain.csv", oracle_exposure_gain_rows(leaderboard))
    _write_capacity_horizon_claim_readiness_md(
        capacity_horizon_claim_readiness(report),
        out_dir / "capacity_horizon_claim_readiness.md",
    )
    _write_summary_md(report, leaderboard, out_dir / "baseline_summary.md")


def diagnose_capacity_horizon(
    report_path: Path,
    predictions_path: Path,
    horizon_table_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Render Milestone 6.1 multi-horizon error forensics from existing artifacts."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = list(report.get("metrics", []))
    predictions = pq.read_table(predictions_path).to_pylist()
    horizon_rows = pq.read_table(horizon_table_path).to_pylist()
    if not metrics:
        raise ValueError("Capacity horizon report has no metrics.")
    if not predictions:
        raise ValueError("Capacity horizon prediction table has no rows.")
    if not horizon_rows:
        raise ValueError("Capacity horizon table has no rows.")

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    gain_rows = horizon_reference_gain_by_split_rows(metrics)
    c_rate_rows = c_rate_condition_horizon_error_rows(predictions, horizon_rows)
    prior_failure_rows = prior_slope_failure_mode_rows(predictions, horizon_rows)
    oracle_rows = oracle_exposure_gain_by_split_rows(metrics)
    audit_rows = prospective_feature_audit_rows()
    readiness = multi_horizon_next_branch_readiness(gain_rows, c_rate_rows, prior_failure_rows, oracle_rows)

    _write_csv(plots_dir / "horizon_reference_gain_by_split.csv", gain_rows)
    _write_csv(plots_dir / "c_rate_condition_horizon_errors.csv", c_rate_rows)
    _write_csv(plots_dir / "prior_slope_failure_modes.csv", prior_failure_rows)
    _write_csv(plots_dir / "oracle_exposure_gain_by_split.csv", oracle_rows)
    _write_csv(plots_dir / "prospective_feature_audit.csv", audit_rows)
    _write_multi_horizon_forensics_md(
        report,
        gain_rows,
        c_rate_rows,
        prior_failure_rows,
        oracle_rows,
        readiness,
        out_dir / "multi_horizon_error_forensics.md",
    )
    _write_next_branch_readiness_md(readiness, out_dir / "multi_horizon_next_branch_readiness.md")

    diagnostic_report = {
        "status": "passed",
        "schema_version": "gate61.capacity_horizon_forensics.v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "report": str(report_path),
            "predictions": str(predictions_path),
            "horizon_table": str(horizon_table_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "horizon_reference_gain_by_split": str(plots_dir / "horizon_reference_gain_by_split.csv"),
            "c_rate_condition_horizon_errors": str(plots_dir / "c_rate_condition_horizon_errors.csv"),
            "prior_slope_failure_modes": str(plots_dir / "prior_slope_failure_modes.csv"),
            "oracle_exposure_gain_by_split": str(plots_dir / "oracle_exposure_gain_by_split.csv"),
            "prospective_feature_audit": str(plots_dir / "prospective_feature_audit.csv"),
            "error_forensics": str(out_dir / "multi_horizon_error_forensics.md"),
            "next_branch_readiness": str(out_dir / "multi_horizon_next_branch_readiness.md"),
        },
        "row_counts": {
            "metrics": len(metrics),
            "predictions": len(predictions),
            "horizon_rows": len(horizon_rows),
            "gain_rows": len(gain_rows),
            "c_rate_condition_rows": len(c_rate_rows),
            "prior_slope_failure_rows": len(prior_failure_rows),
            "oracle_gain_rows": len(oracle_rows),
        },
        "readiness": readiness,
    }
    (out_dir / "capacity_horizon_forensics_report.json").write_text(
        json.dumps(diagnostic_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return diagnostic_report


def horizon_reference_gain_by_split_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare prospective HGB K2 against persistence and prior-slope references."""
    rows = leaderboard_rows(metrics) + _split_leaderboard_rows(metrics)
    output = []
    for candidate in rows:
        if (
            candidate["model_level"] != "MH3_hist_gradient_boosting"
            or candidate["feature_group"] != "K2_nominal_condition"
        ):
            continue
        target = str(candidate["target"])
        horizon = int(candidate["horizon_checkups"])
        split_name = str(candidate["split_name"])
        persistence = _find_row(
            rows,
            target=target,
            horizon=horizon,
            model_level="MH0_persistence",
            feature_group="persistence",
            split_name=split_name,
        )
        prior_slope = _find_row(
            rows,
            target=target,
            horizon=horizon,
            model_level="MH1_prior_slope_linear",
            feature_group="prior_slope",
            split_name=split_name,
        )
        if persistence is None or prior_slope is None:
            continue
        hgb_mae = float(candidate["mean_mae"])
        persistence_mae = float(persistence["mean_mae"])
        prior_slope_mae = float(prior_slope["mean_mae"])
        output.append(
            {
                "target": target,
                "horizon_checkups": horizon,
                "split_name": split_name,
                "hgb_k2_mean_mae": hgb_mae,
                "persistence_mean_mae": persistence_mae,
                "prior_slope_mean_mae": prior_slope_mae,
                "gain_vs_persistence": persistence_mae - hgb_mae,
                "gain_vs_prior_slope": prior_slope_mae - hgb_mae,
                "beats_persistence": hgb_mae < persistence_mae,
                "beats_prior_slope": hgb_mae < prior_slope_mae,
                "beats_both_references": hgb_mae < persistence_mae and hgb_mae < prior_slope_mae,
                "claim_scope": "prospective_diagnostic",
            }
        )
    return sorted(output, key=lambda row: (row["split_name"], row["target"], row["horizon_checkups"]))


def oracle_exposure_gain_by_split_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare oracle K3 against prospective K2 by split without authorizing K3."""
    rows = leaderboard_rows(metrics) + _split_leaderboard_rows(metrics)
    output = []
    for oracle in rows:
        if (
            oracle["model_level"] != "MH3_hist_gradient_boosting"
            or oracle["feature_group"] != "K3_oracle_exposure_diagnostic"
        ):
            continue
        target = str(oracle["target"])
        horizon = int(oracle["horizon_checkups"])
        split_name = str(oracle["split_name"])
        reference = _find_row(
            rows,
            target=target,
            horizon=horizon,
            model_level="MH3_hist_gradient_boosting",
            feature_group="K2_nominal_condition",
            split_name=split_name,
        )
        if reference is None:
            continue
        reference_mae = float(reference["mean_mae"])
        oracle_mae = float(oracle["mean_mae"])
        output.append(
            {
                "target": target,
                "horizon_checkups": horizon,
                "split_name": split_name,
                "prospective_feature_group": "K2_nominal_condition",
                "oracle_feature_group": "K3_oracle_exposure_diagnostic",
                "prospective_mean_mae": reference_mae,
                "oracle_mean_mae": oracle_mae,
                "oracle_gain": reference_mae - oracle_mae,
                "claim_scope": "oracle_diagnostic_only_not_prospective",
            }
        )
    return sorted(output, key=lambda row: (row["split_name"], row["target"], row["horizon_checkups"]))


def c_rate_condition_horizon_error_rows(
    predictions: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize C-rate holdout condition-level errors for each model arm."""
    horizon_by_key = _horizon_row_index(horizon_rows)
    grouped: dict[tuple[Any, ...], list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for row in predictions:
        if row["split_name"] != "c_rate_holdout_fold":
            continue
        horizon_row = horizon_by_key.get(_prediction_horizon_key(row))
        if horizon_row is None:
            continue
        error = abs(_as_float(row["y_pred"]) - _as_float(row["y_true"]))
        grouped[
            (
                row["target"],
                int(row["horizon_checkups"]),
                int(row["parameter_set"]),
                row["model_level"],
                row["feature_group"],
            )
        ].append((horizon_row, error))

    output = []
    for (target, horizon, parameter_set, model_level, feature_group), values in sorted(grouped.items()):
        horizon_context = values[0][0]
        errors = [error for _, error in values]
        output.append(
            {
                "target": target,
                "horizon_checkups": horizon,
                "parameter_set": parameter_set,
                "model_level": model_level,
                "feature_group": feature_group,
                "n_rows": len(values),
                "mae": _mean(errors),
                "mean_checkup_k": _mean([_as_float(row.get("checkup_k")) for row, _ in values]),
                "mean_soh_k": _mean([_as_float(row.get("soh_k")) for row, _ in values]),
                "aging_mode": horizon_context.get("aging_mode", ""),
                "nominal_temperature_C": horizon_context.get("nominal_temperature_C"),
                "nominal_charge_C_rate": horizon_context.get("nominal_charge_C_rate"),
                "nominal_discharge_C_rate": horizon_context.get("nominal_discharge_C_rate"),
                "voltage_window_family": horizon_context.get("voltage_window_family", ""),
                "profile_label": horizon_context.get("profile_label", ""),
            }
        )
    return output


def prior_slope_failure_mode_rows(
    predictions: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Bin row-level HGB K2 versus prior-slope differences by known-at-k state."""
    horizon_by_key = _horizon_row_index(horizon_rows)
    by_prediction_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in predictions:
        key = (
            row["split_name"],
            int(row["heldout_fold"]),
            row["target"],
            row["cell_id"],
            int(row["checkup_k"]),
            int(row["target_checkup_k"]),
            int(row["horizon_checkups"]),
            row["model_level"],
            row["feature_group"],
        )
        by_prediction_key[key] = row

    grouped: dict[tuple[Any, ...], list[dict[str, float]]] = defaultdict(list)
    for k2_row in predictions:
        if (
            k2_row["model_level"] != "MH3_hist_gradient_boosting"
            or k2_row["feature_group"] != "K2_nominal_condition"
        ):
            continue
        prior_key = (
            k2_row["split_name"],
            int(k2_row["heldout_fold"]),
            k2_row["target"],
            k2_row["cell_id"],
            int(k2_row["checkup_k"]),
            int(k2_row["target_checkup_k"]),
            int(k2_row["horizon_checkups"]),
            "MH1_prior_slope_linear",
            "prior_slope",
        )
        prior_row = by_prediction_key.get(prior_key)
        horizon_row = horizon_by_key.get(_prediction_horizon_key(k2_row))
        if prior_row is None or horizon_row is None:
            continue
        k2_abs = abs(_as_float(k2_row["y_pred"]) - _as_float(k2_row["y_true"]))
        prior_abs = abs(_as_float(prior_row["y_pred"]) - _as_float(prior_row["y_true"]))
        grouped[
            (
                k2_row["split_name"],
                k2_row["target"],
                int(k2_row["horizon_checkups"]),
                _checkup_bin(_as_float(horizon_row.get("checkup_k"))),
                _soh_bin(_as_float(horizon_row.get("soh_k"))),
                _prior_delta_bin(abs(_as_float(horizon_row.get("prior_delta_capacity_Ah"), default=0.0))),
            )
        ].append({"k2_abs": k2_abs, "prior_abs": prior_abs, "parameter_set": float(k2_row["parameter_set"])})

    output = []
    for (split_name, target, horizon, checkup_bin, soh_bin, prior_delta_bin), values in sorted(grouped.items()):
        k2_errors = [row["k2_abs"] for row in values]
        prior_errors = [row["prior_abs"] for row in values]
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "checkup_bin": checkup_bin,
                "soh_bin": soh_bin,
                "prior_delta_abs_bin": prior_delta_bin,
                "n_rows": len(values),
                "condition_count": len({int(row["parameter_set"]) for row in values}),
                "hgb_k2_mae": _mean(k2_errors),
                "prior_slope_mae": _mean(prior_errors),
                "hgb_minus_prior_slope_mae": _mean(k2_errors) - _mean(prior_errors),
                "hgb_wins_fraction": sum(k2 < prior for k2, prior in zip(k2_errors, prior_errors)) / len(values),
            }
        )
    return output


def prospective_feature_audit_rows() -> list[dict[str, Any]]:
    """Classify existing and candidate feature families for future work."""
    rows = []
    for group in FEATURE_GROUPS:
        fields = sorted(set(NUMERIC_FEATURES[group]) | set(CATEGORICAL_FEATURES[group]))
        future_fields = sorted(set(fields) & FUTURE_EXPOSURE_FIELDS)
        rows.append(
            {
                "feature_family": group,
                "artifact_status": "implemented",
                "claim_scope": "oracle_diagnostic_only" if group in ORACLE_FEATURE_GROUPS else "prospective",
                "allowed_for_future_prospective_branch": group not in ORACLE_FEATURE_GROUPS,
                "future_or_target_leakage_fields": ",".join(future_fields),
                "policy": "existing feature group",
            }
        )
    rows.extend(
        [
            {
                "feature_family": "candidate_prior_trajectory_shape",
                "artifact_status": "not_implemented",
                "claim_scope": "prospective_candidate",
                "allowed_for_future_prospective_branch": True,
                "future_or_target_leakage_fields": "",
                "policy": "may use capacity trajectory and slopes observed at or before check-up k only",
            },
            {
                "feature_family": "candidate_planned_protocol_metadata",
                "artifact_status": "not_implemented",
                "claim_scope": "prospective_candidate_if_known_at_k",
                "allowed_for_future_prospective_branch": True,
                "future_or_target_leakage_fields": "",
                "policy": "may use scheduled protocol metadata only if known before the forecast horizon",
            },
            {
                "feature_family": "candidate_actual_horizon_exposure",
                "artifact_status": "forbidden_for_prospective",
                "claim_scope": "oracle_diagnostic_only",
                "allowed_for_future_prospective_branch": False,
                "future_or_target_leakage_fields": ",".join(sorted(FUTURE_EXPOSURE_FIELDS)),
                "policy": "actual k-to-k+h exposure cannot be used as an early forecasting input",
            },
            {
                "feature_family": "candidate_future_diagnostics",
                "artifact_status": "forbidden_for_prospective",
                "claim_scope": "leakage",
                "allowed_for_future_prospective_branch": False,
                "future_or_target_leakage_fields": "capacity_Ah_kh,delta_capacity_Ah_h,future_PULSE,future_EIS",
                "policy": "future diagnostics and target values remain forbidden",
            },
        ]
    )
    return rows


def multi_horizon_next_branch_readiness(
    gain_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    prior_failure_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Make the post-forensics branch decision explicit and claim-bounded."""
    primary_gain_rows = [
        row
        for row in gain_rows
        if row["split_name"] == "all"
        and row["target"] in TARGETS
        and int(row["horizon_checkups"]) in {2, 3}
    ]
    c_rate_gain_rows = [
        row
        for row in gain_rows
        if row["split_name"] == "c_rate_holdout_fold" and int(row["horizon_checkups"]) in {2, 3}
    ]
    c_rate_k2_rows = [
        row
        for row in c_rate_rows
        if row["model_level"] == "MH3_hist_gradient_boosting" and row["feature_group"] == "K2_nominal_condition"
    ]
    c_rate_conditions = len({int(row["parameter_set"]) for row in c_rate_k2_rows})
    losing_prior_bins = [
        row
        for row in prior_failure_rows
        if int(row["horizon_checkups"]) in {2, 3} and float(row["hgb_minus_prior_slope_mae"]) > 0
    ]
    oracle_positive = any(float(row["oracle_gain"]) > 0 for row in oracle_rows)
    all_primary_pass = bool(primary_gain_rows) and all(row["beats_both_references"] for row in primary_gain_rows)
    c_rate_pass = bool(c_rate_gain_rows) and all(row["beats_both_references"] for row in c_rate_gain_rows)
    if losing_prior_bins:
        recommended_next_branch = "prior_trajectory_shape_audit"
    elif oracle_positive:
        recommended_next_branch = "planned_protocol_feature_audit"
    else:
        recommended_next_branch = "stop_modeling_and_synthesize"
    return {
        "multi_horizon_global_status": "supported_for_diagnostics" if all_primary_pass else "partially_supported",
        "c_rate_multi_horizon_status": "supported_for_diagnostics" if c_rate_pass else "partially_supported",
        "c_rate_condition_count": c_rate_conditions,
        "prior_slope_failure_bins": len(losing_prior_bins),
        "oracle_exposure_status": "oracle_diagnostic_only" if oracle_positive else "not_supported",
        "prior_trajectory_shape_branch": "possible_next_gate" if losing_prior_bins else "not_indicated",
        "planned_protocol_feature_branch": "diagnostic_only" if oracle_positive else "not_indicated",
        "sequence_or_neural_models": "blocked",
        "policy_ranking": "blocked",
        "cbat_architecture": "blocked",
        "recommended_next_branch": recommended_next_branch,
        "claim_scope": "no new scientific claim; forensics only",
    }


def leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[
            (
                row["target"],
                row["horizon_checkups"],
                row["model_level"],
                row["feature_group"],
            )
        ].append(row)
    output = []
    for (target, horizon, model, feature), rows in sorted(grouped.items()):
        output.append(_aggregate_metric_rows(rows, target, horizon, model, feature, split_name="all"))
    return output


def oracle_exposure_gain_rows(leaderboard: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in leaderboard:
        if row["model_level"] != "MH3_hist_gradient_boosting" or row["feature_group"] != "K3_oracle_exposure_diagnostic":
            continue
        reference = _find_row(
            leaderboard,
            target=row["target"],
            horizon=int(row["horizon_checkups"]),
            model_level="MH3_hist_gradient_boosting",
            feature_group="K2_nominal_condition",
        )
        if reference is None:
            continue
        output.append(
            {
                "target": row["target"],
                "horizon_checkups": row["horizon_checkups"],
                "reference_feature_group": "K2_nominal_condition",
                "oracle_feature_group": "K3_oracle_exposure_diagnostic",
                "reference_mean_mae": reference["mean_mae"],
                "oracle_mean_mae": row["mean_mae"],
                "mae_gain": reference["mean_mae"] - row["mean_mae"],
                "claim_scope": "oracle_diagnostic_only_not_prospective",
            }
        )
    return output


def capacity_horizon_claim_readiness(report: dict[str, Any]) -> dict[str, Any]:
    leaderboard = leaderboard_rows(list(report["metrics"]))
    c_rate_rows = [
        row for row in report["metrics"] if row["split_name"] == "c_rate_holdout_fold"
    ]
    c_rate_leaderboard = _split_leaderboard_rows(c_rate_rows)
    primary_pairs = [(target, horizon) for target in TARGETS for horizon in (2, 3)]
    prospective_passes = [
        _beats_references(leaderboard, target, horizon, split_name="all")
        for target, horizon in primary_pairs
    ]
    c_rate_passes = [
        _beats_references(c_rate_leaderboard, target, horizon, split_name="c_rate_holdout_fold")
        for target, horizon in primary_pairs
    ]
    oracle_rows = oracle_exposure_gain_rows(leaderboard)
    return {
        "multi_horizon_forecasting": _readiness_from_passes(prospective_passes),
        "c_rate_multi_horizon": _readiness_from_passes(c_rate_passes),
        "delta_capacity_multi_horizon": _readiness_from_passes(
            [
                _beats_references(leaderboard, "delta_capacity_Ah_h", horizon, split_name="all")
                for horizon in (2, 3)
            ]
        ),
        "oracle_exposure_diagnostic": "diagnostic_only"
        if any(row["mae_gain"] > 0 for row in oracle_rows)
        else "not_supported",
        "sequence_or_neural_readiness": "blocked",
        "policy_ranking": "blocked",
        "calibrated_uncertainty_or_risk": "blocked",
        "primary_pairs": primary_pairs,
        "prospective_passes": prospective_passes,
        "c_rate_passes": c_rate_passes,
    }


def leakage_audit(feature_groups: list[str]) -> dict[str, Any]:
    rows = []
    status = "passed"
    for group in feature_groups:
        fields = set(NUMERIC_FEATURES[group]) | set(CATEGORICAL_FEATURES[group])
        future_fields = sorted(fields & FUTURE_EXPOSURE_FIELDS)
        claim_scope = "oracle_diagnostic_only" if group in ORACLE_FEATURE_GROUPS else "prospective"
        if future_fields and group not in ORACLE_FEATURE_GROUPS:
            status = "failed"
        rows.append(
            {
                "feature_group": group,
                "claim_scope": claim_scope,
                "future_exposure_fields": future_fields,
            }
        )
    return {
        "status": status,
        "allowed_prospective": "check-up-k state/time/nominal/history fields only",
        "oracle_diagnostic_fields": sorted(FUTURE_EXPOSURE_FIELDS),
        "rows": rows,
    }


def _aggregate_metric_rows(
    rows: list[dict[str, Any]],
    target: str,
    horizon: int,
    model: str,
    feature: str,
    *,
    split_name: str,
) -> dict[str, Any]:
    return {
        "target": target,
        "horizon_checkups": horizon,
        "split_name": split_name,
        "model_level": model,
        "feature_group": feature,
        "metric_rows": len(rows),
        "total_test_rows": sum(int(row["n_test"]) for row in rows),
        "mean_mae": _mean([float(row["mae"]) for row in rows]),
        "mean_rmse": _mean([float(row["rmse"]) for row in rows]),
        "mean_condition_mean_mae": _mean([float(row["condition_mean_mae"]) for row in rows]),
        "mean_worst_condition_mae": _mean([float(row["worst_condition_mae"]) for row in rows]),
    }


def _split_leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[
            (
                row["target"],
                row["horizon_checkups"],
                row["model_level"],
                row["feature_group"],
                row["split_name"],
            )
        ].append(row)
    return [
        _aggregate_metric_rows(rows, target, horizon, model, feature, split_name=split_name)
        for (target, horizon, model, feature, split_name), rows in sorted(grouped.items())
    ]


def _beats_references(
    rows: list[dict[str, Any]],
    target: str,
    horizon: int,
    *,
    split_name: str,
) -> bool:
    candidate = _find_row(
        rows,
        target=target,
        horizon=horizon,
        model_level="MH3_hist_gradient_boosting",
        feature_group="K2_nominal_condition",
        split_name=split_name,
    )
    persistence = _find_row(
        rows,
        target=target,
        horizon=horizon,
        model_level="MH0_persistence",
        feature_group="persistence",
        split_name=split_name,
    )
    prior_slope = _find_row(
        rows,
        target=target,
        horizon=horizon,
        model_level="MH1_prior_slope_linear",
        feature_group="prior_slope",
        split_name=split_name,
    )
    if candidate is None or persistence is None or prior_slope is None:
        return False
    return (
        float(candidate["mean_mae"]) < float(persistence["mean_mae"])
        and float(candidate["mean_mae"]) < float(prior_slope["mean_mae"])
    )


def _find_row(
    rows: list[dict[str, Any]],
    *,
    target: str,
    horizon: int,
    model_level: str,
    feature_group: str,
    split_name: str | None = None,
) -> dict[str, Any] | None:
    for row in rows:
        if (
            row["target"] == target
            and int(row["horizon_checkups"]) == horizon
            and row["model_level"] == model_level
            and row["feature_group"] == feature_group
            and (split_name is None or row.get("split_name") == split_name)
        ):
            return row
    return None


def _readiness_from_passes(passes: list[bool]) -> str:
    if passes and all(passes):
        return "supported_for_diagnostics"
    if any(passes):
        return "partially_supported"
    return "not_supported"


def _write_capacity_horizon_claim_readiness_md(readiness: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Capacity Horizon Claim Readiness",
        "",
        "| Claim area | Status |",
        "| --- | --- |",
        f"| Multi-horizon capacity forecasting | {readiness['multi_horizon_forecasting']} |",
        f"| C-rate multi-horizon forecasting | {readiness['c_rate_multi_horizon']} |",
        f"| Delta-capacity multi-horizon forecasting | {readiness['delta_capacity_multi_horizon']} |",
        f"| Oracle exposure diagnostic | {readiness['oracle_exposure_diagnostic']} |",
        f"| Sequence or neural readiness | {readiness['sequence_or_neural_readiness']} |",
        f"| Policy ranking | {readiness['policy_ranking']} |",
        f"| Calibrated uncertainty or risk | {readiness['calibrated_uncertainty_or_risk']} |",
        "",
        "Prospective feature groups exclude k-to-k+h exposure. "
        "K3_oracle_exposure_diagnostic is not a valid early-forecasting input.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_summary_md(report: dict[str, Any], leaderboard: list[dict[str, Any]], out_path: Path) -> None:
    best_rows = sorted(leaderboard, key=lambda row: (row["target"], row["horizon_checkups"], row["mean_mae"]))
    lines = [
        "# Capacity Horizon Baseline Summary",
        "",
        f"Rows: {report['row_counts']['rows']}",
        f"Metric rows: {report['row_counts']['metrics']}",
        "",
        "This gate evaluates non-neural multi-check-up capacity forecasting. "
        "Prospective claims may use K0-K2 only; K3 is oracle diagnostic.",
        "",
        "| Target | Horizon | Model | Feature group | Mean MAE |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for row in best_rows[:20]:
        lines.append(
            f"| {row['target']} | {row['horizon_checkups']} | {row['model_level']} | "
            f"{row['feature_group']} | {row['mean_mae']:.6g} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _condition_mae_rows(test_rows: list[dict[str, Any]], abs_errors: list[float]) -> list[dict[str, Any]]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for row, error in zip(test_rows, abs_errors):
        grouped[int(row["parameter_set"])].append(error)
    return [{"parameter_set": key, "mae": _mean(values)} for key, values in grouped.items()]


def _persistence_prediction(row: dict[str, Any], target: str) -> float:
    if target == "capacity_Ah_kh":
        return _as_float(row.get("capacity_Ah_k"))
    if target == "delta_capacity_Ah_h":
        return 0.0
    raise ValueError(f"Unknown capacity horizon target: {target}")


def _prior_slope_prediction(row: dict[str, Any], target: str) -> float:
    prior_delta = _as_float(row.get("prior_delta_capacity_Ah"), default=0.0)
    if not math.isfinite(prior_delta):
        prior_delta = 0.0
    predicted_delta = prior_delta * int(row["horizon_checkups"])
    if target == "capacity_Ah_kh":
        return _as_float(row.get("capacity_Ah_k")) + predicted_delta
    if target == "delta_capacity_Ah_h":
        return predicted_delta
    raise ValueError(f"Unknown capacity horizon target: {target}")


def _target_value(row: dict[str, Any], target: str) -> float:
    if target not in TARGETS:
        raise ValueError(f"Unknown capacity horizon target: {target}")
    return _as_float(row.get(target))


def _audit_feature_groups(feature_groups: list[str]) -> None:
    audit = leakage_audit(feature_groups)
    if audit["status"] != "passed":
        raise ValueError(f"Capacity horizon feature leakage audit failed: {audit}")


def _normalize_selection(
    values: list[str] | None,
    allowed: tuple[str, ...],
    default: tuple[str, ...],
    label: str,
) -> list[str]:
    selected = list(default if values is None else values)
    output = []
    seen = set()
    for item in selected:
        normalized = str(item).strip()
        if not normalized:
            continue
        if normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    unknown = sorted(set(output) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}(s): {unknown}. Allowed: {list(allowed)}")
    if not output:
        raise ValueError(f"At least one {label} must be selected.")
    return output


def _normalize_horizons(values: list[int] | None) -> list[int]:
    selected = list(DEFAULT_HORIZONS if values is None else values)
    output = []
    seen = set()
    for item in selected:
        horizon = int(item)
        if horizon <= 0:
            raise ValueError("Horizons must be positive.")
        if horizon not in seen:
            seen.add(horizon)
            output.append(horizon)
    if not output:
        raise ValueError("At least one horizon must be selected.")
    return output


def _import_sklearn_stack() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Capacity horizon baselines require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry, or select MH0/MH1 only."
        ) from exc
    return np, Ridge, HistGradientBoostingRegressor


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


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        raise ValueError("Cannot compute mean of empty finite values.")
    return sum(finite) / len(finite)


def _median(values: list[float]) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        raise ValueError("Cannot compute median of empty finite values.")
    midpoint = len(finite) // 2
    if len(finite) % 2:
        return finite[midpoint]
    return (finite[midpoint - 1] + finite[midpoint]) / 2.0


def _horizon_row_index(rows: list[dict[str, Any]]) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {_horizon_key(row): row for row in rows}


def _horizon_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["cell_id"]),
        int(row["parameter_set"]),
        int(row["replicate_id"]),
        int(row["checkup_k"]),
        int(row["target_checkup_k"]),
        int(row["horizon_checkups"]),
    )


def _prediction_horizon_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["cell_id"]),
        int(row["parameter_set"]),
        int(row["replicate_id"]),
        int(row["checkup_k"]),
        int(row["target_checkup_k"]),
        int(row["horizon_checkups"]),
    )


def _checkup_bin(value: float) -> str:
    if not math.isfinite(value):
        return "unknown"
    if value <= 3:
        return "checkup_0_3"
    if value <= 7:
        return "checkup_4_7"
    if value <= 12:
        return "checkup_8_12"
    return "checkup_13_plus"


def _soh_bin(value: float) -> str:
    if not math.isfinite(value):
        return "unknown"
    if value >= 0.9:
        return "soh_ge_0_90"
    if value >= 0.8:
        return "soh_0_80_0_90"
    if value >= 0.7:
        return "soh_0_70_0_80"
    return "soh_lt_0_70"


def _prior_delta_bin(value: float) -> str:
    if not math.isfinite(value):
        return "unknown"
    if value < 0.005:
        return "prior_abs_lt_0_005"
    if value < 0.02:
        return "prior_abs_0_005_0_02"
    if value < 0.05:
        return "prior_abs_0_02_0_05"
    return "prior_abs_ge_0_05"


def _write_multi_horizon_forensics_md(
    report: dict[str, Any],
    gain_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    prior_failure_rows: list[dict[str, Any]],
    oracle_rows: list[dict[str, Any]],
    readiness: dict[str, Any],
    out_path: Path,
) -> None:
    primary = [
        row
        for row in gain_rows
        if row["split_name"] == "all" and int(row["horizon_checkups"]) in {2, 3}
    ]
    c_rate = [
        row
        for row in gain_rows
        if row["split_name"] == "c_rate_holdout_fold" and int(row["horizon_checkups"]) in {2, 3}
    ]
    worst_prior_bins = sorted(
        prior_failure_rows,
        key=lambda row: float(row["hgb_minus_prior_slope_mae"]),
        reverse=True,
    )[:10]
    top_c_rate = sorted(
        [
            row
            for row in c_rate_rows
            if row["model_level"] == "MH3_hist_gradient_boosting"
            and row["feature_group"] == "K2_nominal_condition"
        ],
        key=lambda row: float(row["mae"]),
        reverse=True,
    )[:10]
    positive_oracle = [row for row in oracle_rows if float(row["oracle_gain"]) > 0]
    lines = [
        "# Multi-Horizon Error Forensics",
        "",
        "Milestone 6.1 diagnoses the Milestone 6.0 multi-horizon result using existing "
        "reports and prediction artifacts only. It does not train a new model and does "
        "not add a new scientific claim.",
        "",
        f"Baseline rows: {report['row_counts']['metrics']} metric rows.",
        f"Recommended next branch: `{readiness['recommended_next_branch']}`.",
        "",
        "## Primary Horizon 2/3 Reference Gains",
        "",
        "| Split | Target | Horizon | HGB K2 MAE | Prior-slope MAE | Gain vs prior | Beats both |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in primary + c_rate:
        lines.append(
            f"| {row['split_name']} | {row['target']} | {row['horizon_checkups']} | "
            f"{float(row['hgb_k2_mean_mae']):.6g} | {float(row['prior_slope_mean_mae']):.6g} | "
            f"{float(row['gain_vs_prior_slope']):.6g} | {row['beats_both_references']} |"
        )
    lines.extend(
        [
            "",
            "## C-Rate Condition Hotspots",
            "",
            "| Target | Horizon | Parameter set | MAE | Mean SOH | Charge C-rate | Profile |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in top_c_rate:
        lines.append(
            f"| {row['target']} | {row['horizon_checkups']} | {row['parameter_set']} | "
            f"{float(row['mae']):.6g} | {float(row['mean_soh_k']):.6g} | "
            f"{float(row['nominal_charge_C_rate']):.6g} | {row['profile_label']} |"
        )
    lines.extend(
        [
            "",
            "## Prior-Slope Failure Modes",
            "",
            "| Split | Target | Horizon | Check-up bin | SOH bin | Prior-delta bin | Rows | HGB - prior MAE |",
            "| --- | --- | ---: | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in worst_prior_bins:
        lines.append(
            f"| {row['split_name']} | {row['target']} | {row['horizon_checkups']} | "
            f"{row['checkup_bin']} | {row['soh_bin']} | {row['prior_delta_abs_bin']} | "
            f"{row['n_rows']} | {float(row['hgb_minus_prior_slope_mae']):.6g} |"
        )
    lines.extend(
        [
            "",
            "## Oracle Exposure Diagnostic",
            "",
            f"Rows where K3 oracle exposure improves over K2: {len(positive_oracle)}.",
            "K3 aggregates actual k-to-k+h exposure and remains oracle-diagnostic only.",
            "",
            "## Claim Posture",
            "",
            "- Multi-horizon forecasting remains scoped by the existing Milestone 6.0 claim readiness.",
            "- C-rate and delta-capacity diagnostics remain the supported diagnostic subset when their rows pass.",
            "- Sequence/neural models, CBAT, policy ranking, causal claims, and calibrated risk/uncertainty remain blocked.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_next_branch_readiness_md(readiness: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Multi-Horizon Next-Branch Readiness",
        "",
        "| Area | Status |",
        "| --- | --- |",
        f"| Global multi-horizon diagnostic | {readiness['multi_horizon_global_status']} |",
        f"| C-rate multi-horizon diagnostic | {readiness['c_rate_multi_horizon_status']} |",
        f"| Oracle exposure | {readiness['oracle_exposure_status']} |",
        f"| Prior-trajectory shape branch | {readiness['prior_trajectory_shape_branch']} |",
        f"| Planned-protocol feature branch | {readiness['planned_protocol_feature_branch']} |",
        f"| Sequence or neural models | {readiness['sequence_or_neural_models']} |",
        f"| Policy ranking | {readiness['policy_ranking']} |",
        f"| CBAT architecture | {readiness['cbat_architecture']} |",
        "",
        f"Recommended next branch: `{readiness['recommended_next_branch']}`.",
        "",
        "The recommendation is a diagnostic planning result, not authorization for "
        "architecture, policy, causal, or calibrated-risk claims.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
