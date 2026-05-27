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


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
