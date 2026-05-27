"""Non-neural multi-horizon PULSE/EIS diagnostic endpoint baselines."""

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

from mbp.baselines.capacity import SPLIT_COLUMNS, assert_no_parameter_set_leakage, iter_split_instances

SCHEMA_VERSION = "gate82.diagnostic_horizon_baseline.v1"
FORENSICS_SCHEMA_VERSION = "gate821.diagnostic_horizon_forensics.v1"
PREDICTION_SCHEMA_VERSION = "gate82.diagnostic_horizon_predictions.v1"
TARGETS = (
    "pulse_1s_resistance",
    "pulse_10ms_resistance",
    "eis_z_abs_1kHz",
    "eis_phase_1kHz",
    "nyquist_im_peak_abs",
    "nyquist_semicircle_width_proxy",
)
MODEL_LEVELS = (
    "DM0_persistence",
    "DM1_train_mean",
    "DM2_ridge",
    "DM3_hist_gradient_boosting",
)
FEATURE_GROUPS = (
    "DH0_time_nominal",
    "DH1_capacity_state",
    "DH2_prior_same_diagnostic_state",
    "DH3_capacity_plus_prior_same_diagnostic",
)
DEFAULT_TARGETS = TARGETS
DEFAULT_MODELS = MODEL_LEVELS
DEFAULT_FEATURE_GROUPS = FEATURE_GROUPS
DEFAULT_HORIZONS = (1, 2, 3, 5)
PRIMARY_MODEL = "DM3_hist_gradient_boosting"
PRIMARY_FEATURE = "DH3_capacity_plus_prior_same_diagnostic"
REFERENCE_FEATURES = {
    "persistence": ("DM0_persistence", "persistence"),
    "capacity_state": ("DM3_hist_gradient_boosting", "DH1_capacity_state"),
    "prior_same_diagnostic": ("DM3_hist_gradient_boosting", "DH2_prior_same_diagnostic_state"),
}
NUMERIC_FEATURES = {
    "DH0_time_nominal": (
        "horizon_checkups",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "cumulative_q_Ah_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "DH1_capacity_state": (
        "horizon_checkups",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "cumulative_q_Ah_k",
        "capacity_Ah_k",
        "soh_k",
        "prior_delta_capacity_Ah",
        "prior_capacity_slope_per_day",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "DH2_prior_same_diagnostic_state": (
        "horizon_checkups",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "cumulative_q_Ah_k",
        "diagnostic_value_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "DH3_capacity_plus_prior_same_diagnostic": (
        "horizon_checkups",
        "checkup_k",
        "calendar_day_k",
        "cumulative_efc_k",
        "cumulative_q_Ah_k",
        "capacity_Ah_k",
        "soh_k",
        "prior_delta_capacity_Ah",
        "prior_capacity_slope_per_day",
        "diagnostic_value_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
}
CATEGORICAL_FEATURES = {
    "DH0_time_nominal": ("voltage_window_family", "profile_label", "aging_mode"),
    "DH1_capacity_state": ("voltage_window_family", "profile_label", "aging_mode"),
    "DH2_prior_same_diagnostic_state": ("voltage_window_family", "profile_label", "aging_mode"),
    "DH3_capacity_plus_prior_same_diagnostic": ("voltage_window_family", "profile_label", "aging_mode"),
}
FORBIDDEN_FEATURE_FIELDS = {
    "diagnostic_value_kh",
    "delta_diagnostic_value_h",
    "event_observed",
}

DIAGNOSTIC_HORIZON_PREDICTION_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("split_name", pa.string()),
        ("heldout_fold", pa.int32()),
        ("model_level", pa.string()),
        ("feature_group", pa.string()),
        ("diagnostic_family", pa.string()),
        ("target_name", pa.string()),
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
class DiagnosticHorizonFeatureEncoder:
    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    numeric_scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "DiagnosticHorizonFeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown diagnostic horizon feature group: {feature_group}")
        numeric_columns = NUMERIC_FEATURES[feature_group]
        categorical_columns = CATEGORICAL_FEATURES[feature_group]
        leakage = set(numeric_columns) & FORBIDDEN_FEATURE_FIELDS
        if leakage:
            raise ValueError(f"Feature group includes forbidden future target fields: {sorted(leakage)}")
        impute: dict[str, float] = {}
        scale: dict[str, float] = {}
        for column in numeric_columns:
            values = [_as_float(row.get(column)) for row in rows]
            finite = [value for value in values if math.isfinite(value)]
            mean = sum(finite) / len(finite) if finite else 0.0
            variance = sum((value - mean) ** 2 for value in finite) / len(finite) if finite else 0.0
            impute[column] = mean
            scale[column] = math.sqrt(variance) if variance > 0.0 else 1.0
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


def run_diagnostic_horizon_baselines(
    diagnostic_horizon_table_path: Path,
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
    """Run non-neural grouped multi-horizon diagnostic endpoint baselines."""
    selected_targets = _normalize_selection(targets, TARGETS, DEFAULT_TARGETS, "target")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, DEFAULT_MODELS, "model level")
    selected_features = _normalize_selection(feature_groups, FEATURE_GROUPS, DEFAULT_FEATURE_GROUPS, "feature group")
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, SPLIT_COLUMNS, "split view")
    selected_horizons = _normalize_horizons(horizons)
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    if any(model in {"DM2_ridge", "DM3_hist_gradient_boosting"} for model in selected_models):
        _import_sklearn_stack()
    leakage = leakage_audit(selected_features)
    if leakage["status"] != "passed":
        raise ValueError("Diagnostic horizon feature leakage audit failed.")

    rows = [
        row
        for row in pq.read_table(diagnostic_horizon_table_path).to_pylist()
        if int(row["horizon_checkups"]) in set(selected_horizons)
        and str(row["target_name"]) in set(selected_targets)
        and math.isfinite(_target_value(row))
    ]
    if not rows:
        raise ValueError("Diagnostic horizon table has no rows for the selected targets/horizons.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for horizon in selected_horizons:
                for target in selected_targets:
                    train_slice = [
                        row
                        for row in train_rows
                        if int(row["horizon_checkups"]) == horizon and str(row["target_name"]) == target
                    ]
                    test_slice = [
                        row
                        for row in test_rows
                        if int(row["horizon_checkups"]) == horizon and str(row["target_name"]) == target
                    ]
                    if not train_slice or not test_slice:
                        continue
                    for model_level in selected_models:
                        model_features = (
                            ("persistence",)
                            if model_level == "DM0_persistence"
                            else ("train_mean",)
                            if model_level == "DM1_train_mean"
                            else tuple(selected_features)
                        )
                        for feature_group in model_features:
                            y_pred = predict_diagnostic_horizon(
                                model_level,
                                feature_group,
                                train_slice,
                                test_slice,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                            )
                            metrics.append(
                                diagnostic_horizon_metrics(
                                    test_slice,
                                    y_pred,
                                    target=target,
                                    horizon=horizon,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    train_rows=train_slice,
                                )
                            )
                            predictions.extend(
                                prediction_rows(
                                    test_slice,
                                    y_pred,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                )
                            )
    if not metrics:
        raise ValueError("No diagnostic horizon metrics were generated.")

    resolved_out_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=DIAGNOSTIC_HORIZON_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": PREDICTION_SCHEMA_VERSION.encode(),
                b"diagnostic_horizon_table_path": str(diagnostic_horizon_table_path).encode(),
            }
        ),
        predictions_out_path,
    )
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {"diagnostic_horizon_table": str(diagnostic_horizon_table_path)},
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
        "leakage_audit": leakage,
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
    render_diagnostic_horizon_artifacts(report, resolved_out_dir)
    return report


def predict_diagnostic_horizon(
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    seed: int,
    hgb_max_iter: int,
) -> list[float]:
    if model_level == "DM0_persistence":
        train_mean = _mean([_target_value(row) for row in train_rows])
        return [
            _as_float(row.get("diagnostic_value_k"))
            if math.isfinite(_as_float(row.get("diagnostic_value_k")))
            else train_mean
            for row in test_rows
        ]
    if model_level == "DM1_train_mean":
        return [_mean([_target_value(row) for row in train_rows])] * len(test_rows)

    _, Ridge, HistGradientBoostingRegressor = _import_sklearn_stack()
    encoder = DiagnosticHorizonFeatureEncoder.fit(train_rows, feature_group)
    standardize = model_level == "DM2_ridge"
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=standardize), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=standardize), dtype=float)
    y_train = np.asarray([_target_value(row) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError("Diagnostic horizon target has non-finite train values.")
    if model_level == "DM2_ridge":
        model = Ridge(alpha=1.0)
    elif model_level == "DM3_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown model level: {model_level}")
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict(x_test)]


def diagnostic_horizon_metrics(
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
    y_true = [_target_value(row) for row in test_rows]
    errors = [pred - true for pred, true in zip(predictions, y_true)]
    abs_errors = [abs(error) for error in errors]
    condition_rows = _condition_mae_rows(test_rows, abs_errors)
    return {
        "diagnostic_family": str(test_rows[0]["diagnostic_family"]),
        "target_name": target,
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
    }


def prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[float],
    *,
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
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "diagnostic_family": str(row["diagnostic_family"]),
                "target_name": str(row["target_name"]),
                "cell_id": str(row["cell_id"]),
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "target_checkup_k": int(row["target_checkup_k"]),
                "horizon_checkups": int(row["horizon_checkups"]),
                "y_true": _target_value(row),
                "y_pred": float(prediction),
            }
        )
    return rows


def render_diagnostic_horizon_artifacts(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    leaderboard = leaderboard_rows(metrics)
    gain_rows = diagnostic_horizon_gain_rows(metrics)
    _write_csv(out_dir / "leaderboard.csv", leaderboard)
    _write_csv(plots_dir / "diagnostic_horizon_performance.csv", metrics)
    _write_csv(
        plots_dir / "c_rate_diagnostic_horizon_performance.csv",
        [row for row in metrics if row["split_name"] == "c_rate_holdout_fold"],
    )
    _write_csv(plots_dir / "diagnostic_horizon_reference_gains.csv", gain_rows)
    _write_claim_readiness_md(
        diagnostic_horizon_claim_readiness(report),
        out_dir / "diagnostic_horizon_claim_readiness.md",
    )
    _write_summary_md(report, leaderboard, out_dir / "diagnostic_horizon_summary.md")


def diagnose_diagnostic_horizon(
    report_path: Path,
    predictions_path: Path,
    diagnostic_horizon_table_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Render report-only failure forensics for diagnostic endpoint horizon forecasting."""
    if not report_path.exists():
        raise FileNotFoundError(f"Missing diagnostic horizon report: {report_path}")
    if not predictions_path.exists():
        raise FileNotFoundError(f"Missing diagnostic horizon predictions: {predictions_path}")
    if not diagnostic_horizon_table_path.exists():
        raise FileNotFoundError(f"Missing diagnostic horizon table: {diagnostic_horizon_table_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = list(report.get("metrics", []))
    if not metrics:
        raise ValueError("Diagnostic horizon report has no metrics.")
    predictions = pq.read_table(predictions_path).to_pylist()
    horizon_rows = pq.read_table(diagnostic_horizon_table_path).to_pylist()
    if not predictions:
        raise ValueError("Diagnostic horizon prediction table is empty.")
    if not horizon_rows:
        raise ValueError("Diagnostic horizon table is empty.")

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    gains = diagnostic_horizon_gain_rows(metrics)
    endpoint_failure_rows = endpoint_reference_failure_rows(gains)
    target_horizon_rows = target_horizon_gain_rows(gains)
    c_rate_failure_rows = [row for row in endpoint_failure_rows if row["split_name"] == "c_rate_holdout_fold"]
    persistence_rows = persistence_ceiling_rows(horizon_rows, metrics)
    hotspot_rows = condition_error_hotspot_rows(predictions)
    endpoint_readiness = diagnostic_horizon_endpoint_readiness_rows(gains)

    _write_csv(plots_dir / "endpoint_reference_failure_matrix.csv", endpoint_failure_rows)
    _write_csv(plots_dir / "target_horizon_gain_matrix.csv", target_horizon_rows)
    _write_csv(plots_dir / "c_rate_endpoint_failure_matrix.csv", c_rate_failure_rows)
    _write_csv(plots_dir / "persistence_ceiling_diagnostics.csv", persistence_rows)
    _write_csv(plots_dir / "condition_error_hotspots.csv", hotspot_rows)
    _write_csv(plots_dir / "diagnostic_horizon_endpoint_claim_readiness.csv", endpoint_readiness)
    _write_diagnostic_horizon_forensics_md(
        report,
        endpoint_failure_rows,
        target_horizon_rows,
        c_rate_failure_rows,
        persistence_rows,
        hotspot_rows,
        out_dir / "diagnostic_horizon_forensics.md",
    )
    _write_endpoint_claim_readiness_md(
        endpoint_readiness,
        out_dir / "diagnostic_horizon_endpoint_claim_readiness.md",
    )

    result = {
        "status": "passed",
        "schema_version": FORENSICS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "report": str(report_path),
            "predictions": str(predictions_path),
            "diagnostic_horizon_table": str(diagnostic_horizon_table_path),
        },
        "outputs": {
            "report": str(out_dir / "diagnostic_horizon_forensics_report.json"),
            "forensics_markdown": str(out_dir / "diagnostic_horizon_forensics.md"),
            "endpoint_claim_readiness": str(out_dir / "diagnostic_horizon_endpoint_claim_readiness.md"),
            "plots_dir": str(plots_dir),
        },
        "row_counts": {
            "metrics": len(metrics),
            "predictions": len(predictions),
            "diagnostic_horizon_rows": len(horizon_rows),
            "endpoint_failure_rows": len(endpoint_failure_rows),
            "target_horizon_rows": len(target_horizon_rows),
            "c_rate_failure_rows": len(c_rate_failure_rows),
            "persistence_ceiling_rows": len(persistence_rows),
            "condition_hotspot_rows": len(hotspot_rows),
            "endpoint_readiness_rows": len(endpoint_readiness),
        },
        "claim_scope": "failure_forensics_only_no_architecture_no_calibrated_risk_no_policy_no_causal_claim",
    }
    (out_dir / "diagnostic_horizon_forensics_report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        grouped[
            (
                str(row["target_name"]),
                int(row["horizon_checkups"]),
                str(row["split_name"]),
                str(row["model_level"]),
                str(row["feature_group"]),
            )
        ].append(row)
    output = []
    for (target, horizon, split_name, model_level, feature_group), rows in grouped.items():
        output.append(_aggregate_leaderboard_rows(rows, target, horizon, split_name, model_level, feature_group))
    overall_grouped: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        overall_grouped[
            (
                str(row["target_name"]),
                int(row["horizon_checkups"]),
                str(row["model_level"]),
                str(row["feature_group"]),
            )
        ].append(row)
    for (target, horizon, model_level, feature_group), rows in overall_grouped.items():
        output.append(_aggregate_leaderboard_rows(rows, target, horizon, "all", model_level, feature_group))
    return sorted(output, key=lambda row: (row["split_name"], row["target_name"], row["horizon_checkups"], row["model_level"], row["feature_group"]))


def _aggregate_leaderboard_rows(
    rows: list[dict[str, Any]],
    target: str,
    horizon: int,
    split_name: str,
    model_level: str,
    feature_group: str,
) -> dict[str, Any]:
    return {
        "target_name": target,
        "diagnostic_family": str(rows[0]["diagnostic_family"]),
        "horizon_checkups": horizon,
        "split_name": split_name,
        "model_level": model_level,
        "feature_group": feature_group,
        "mean_mae": _mean([float(row["mae"]) for row in rows]),
        "mean_rmse": _mean([float(row["rmse"]) for row in rows]),
        "mean_condition_mae": _mean([float(row["condition_mean_mae"]) for row in rows]),
        "worst_condition_mae": max(float(row["worst_condition_mae"]) for row in rows),
        "rows": len(rows),
        "total_test_rows": sum(int(row["n_test"]) for row in rows),
    }


def diagnostic_horizon_gain_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = leaderboard_rows(metrics)
    output = []
    for candidate in rows:
        if candidate["model_level"] != PRIMARY_MODEL or candidate["feature_group"] != PRIMARY_FEATURE:
            continue
        for reference_name, (reference_model, reference_feature) in REFERENCE_FEATURES.items():
            reference = _find_row(
                rows,
                target=str(candidate["target_name"]),
                horizon=int(candidate["horizon_checkups"]),
                split_name=str(candidate["split_name"]),
                model_level=reference_model,
                feature_group=reference_feature,
            )
            if reference is None:
                continue
            candidate_mae = float(candidate["mean_mae"])
            reference_mae = float(reference["mean_mae"])
            output.append(
                {
                    "target_name": candidate["target_name"],
                    "diagnostic_family": candidate["diagnostic_family"],
                    "horizon_checkups": candidate["horizon_checkups"],
                    "split_name": candidate["split_name"],
                    "candidate_model_level": PRIMARY_MODEL,
                    "candidate_feature_group": PRIMARY_FEATURE,
                    "reference_name": reference_name,
                    "reference_model_level": reference_model,
                    "reference_feature_group": reference_feature,
                    "candidate_mean_mae": candidate_mae,
                    "reference_mean_mae": reference_mae,
                    "gain": reference_mae - candidate_mae,
                    "relative_gain": _safe_ratio(reference_mae - candidate_mae, reference_mae),
                    "beats_reference": candidate_mae < reference_mae,
                }
            )
    return sorted(output, key=lambda row: (row["split_name"], row["target_name"], row["horizon_checkups"], row["reference_name"]))


def endpoint_reference_failure_rows(gains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate reference-gain rows with the Milestone 8.2 gate checks."""
    output = []
    for row in gains:
        horizon = int(row["horizon_checkups"])
        split_name = str(row["split_name"])
        reference = str(row["reference_name"])
        relative_gain = _as_float(row.get("relative_gain"))
        gain = _as_float(row.get("gain"))
        is_primary = split_name == "all" and horizon in {2, 3} and reference in {"persistence", "capacity_state"}
        is_c_rate_gate = (
            split_name == "c_rate_holdout_fold"
            and horizon in {2, 3}
            and reference in {"persistence", "capacity_state"}
        )
        passes_10pct_gain = math.isfinite(relative_gain) and relative_gain >= 0.10
        passes_noncollapse = math.isfinite(gain) and gain >= 0.0
        failure_reasons = []
        if is_primary and not passes_10pct_gain:
            failure_reasons.append("primary_gain_below_10pct")
        if is_c_rate_gate and not passes_noncollapse:
            failure_reasons.append("c_rate_negative_gain")
        if not failure_reasons and (is_primary or is_c_rate_gate):
            failure_reasons.append("passes_gate_row")
        output.append(
            {
                **row,
                "is_primary_gate_row": is_primary,
                "is_c_rate_gate_row": is_c_rate_gate,
                "passes_10pct_gain": passes_10pct_gain,
                "passes_noncollapse": passes_noncollapse,
                "failure_reason": ";".join(failure_reasons) if failure_reasons else "not_gate_row",
            }
        )
    return output


def target_horizon_gain_rows(gains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize gain behavior by endpoint, horizon, split, and reference."""
    grouped: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in gains:
        grouped[
            (
                str(row["target_name"]),
                int(row["horizon_checkups"]),
                str(row["split_name"]),
                str(row["reference_name"]),
            )
        ].append(row)
    output = []
    for (target, horizon, split_name, reference), rows in sorted(grouped.items()):
        gains_values = [_as_float(row.get("gain")) for row in rows]
        rel_values = [_as_float(row.get("relative_gain")) for row in rows]
        output.append(
            {
                "target_name": target,
                "diagnostic_family": str(rows[0]["diagnostic_family"]),
                "horizon_checkups": horizon,
                "split_name": split_name,
                "reference_name": reference,
                "rows": len(rows),
                "positive_gain_rows": sum(math.isfinite(value) and value > 0.0 for value in gains_values),
                "nonnegative_gain_rows": sum(math.isfinite(value) and value >= 0.0 for value in gains_values),
                "gain_10pct_rows": sum(math.isfinite(value) and value >= 0.10 for value in rel_values),
                "mean_gain": _mean(gains_values),
                "mean_relative_gain": _mean(rel_values),
                "min_gain": min((value for value in gains_values if math.isfinite(value)), default=math.nan),
                "min_relative_gain": min((value for value in rel_values if math.isfinite(value)), default=math.nan),
                "max_relative_gain": max((value for value in rel_values if math.isfinite(value)), default=math.nan),
            }
        )
    return output


def persistence_ceiling_rows(
    horizon_rows: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Report endpoint scale and persistence-baseline ceilings by target/horizon."""
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in horizon_rows:
        grouped[(str(row["target_name"]), int(row["horizon_checkups"]))].append(row)
    persistence_metrics = [
        row
        for row in leaderboard_rows(metrics)
        if str(row["model_level"]) == "DM0_persistence" and str(row["feature_group"]) == "persistence"
    ]
    metric_lookup = {
        (str(row["target_name"]), int(row["horizon_checkups"]), str(row["split_name"])): row
        for row in persistence_metrics
    }
    output = []
    for (target, horizon), rows in sorted(grouped.items()):
        values = [_as_float(row.get("diagnostic_value_kh")) for row in rows]
        current_values = [_as_float(row.get("diagnostic_value_k")) for row in rows]
        deltas = [
            _as_float(row.get("diagnostic_value_kh")) - _as_float(row.get("diagnostic_value_k"))
            for row in rows
            if math.isfinite(_as_float(row.get("diagnostic_value_kh")))
            and math.isfinite(_as_float(row.get("diagnostic_value_k")))
        ]
        finite_values = [value for value in values if math.isfinite(value)]
        finite_current = [value for value in current_values if math.isfinite(value)]
        all_metric = metric_lookup.get((target, horizon, "all"))
        c_rate_metric = metric_lookup.get((target, horizon, "c_rate_holdout_fold"))
        output.append(
            {
                "target_name": target,
                "diagnostic_family": str(rows[0]["diagnostic_family"]),
                "horizon_checkups": horizon,
                "rows": len(rows),
                "finite_target_rows": len(finite_values),
                "finite_current_rows": len(finite_current),
                "target_mean": _mean(finite_values),
                "target_std": _std(finite_values),
                "target_range": (max(finite_values) - min(finite_values)) if finite_values else math.nan,
                "mean_abs_delta_from_current": _mean([abs(value) for value in deltas]),
                "median_abs_delta_from_current": _median([abs(value) for value in deltas]),
                "all_split_persistence_mae": _as_float(all_metric.get("mean_mae")) if all_metric else math.nan,
                "c_rate_persistence_mae": _as_float(c_rate_metric.get("mean_mae")) if c_rate_metric else math.nan,
            }
        )
    return output


def condition_error_hotspot_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate condition-level absolute errors for DH3 and key references."""
    allowed = {
        (PRIMARY_MODEL, PRIMARY_FEATURE),
        ("DM0_persistence", "persistence"),
        ("DM3_hist_gradient_boosting", "DH1_capacity_state"),
        ("DM3_hist_gradient_boosting", "DH2_prior_same_diagnostic_state"),
    }
    grouped: dict[tuple[str, str, int, str, str, int], list[float]] = defaultdict(list)
    for row in predictions:
        model_key = (str(row["model_level"]), str(row["feature_group"]))
        if model_key not in allowed:
            continue
        error = abs(_as_float(row.get("y_pred")) - _as_float(row.get("y_true")))
        if not math.isfinite(error):
            continue
        grouped[
            (
                str(row["split_name"]),
                str(row["target_name"]),
                int(row["horizon_checkups"]),
                str(row["model_level"]),
                str(row["feature_group"]),
                int(row["parameter_set"]),
            )
        ].append(error)
    output = []
    for (split_name, target, horizon, model_level, feature_group, parameter_set), values in grouped.items():
        output.append(
            {
                "split_name": split_name,
                "target_name": target,
                "horizon_checkups": horizon,
                "model_level": model_level,
                "feature_group": feature_group,
                "parameter_set": parameter_set,
                "rows": len(values),
                "mean_abs_error": _mean(values),
                "median_abs_error": _median(values),
                "max_abs_error": max(values),
            }
        )
    return sorted(output, key=lambda row: (-float(row["mean_abs_error"]), row["split_name"], row["target_name"]))[:500]


def diagnostic_horizon_endpoint_readiness_rows(gains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return endpoint-specific readiness rows for the Milestone 8.2 forensics gate."""
    targets = sorted({str(row["target_name"]) for row in gains})
    output = []
    for target in targets:
        target_rows = [row for row in gains if str(row["target_name"]) == target]
        primary = [
            row
            for row in target_rows
            if row["split_name"] == "all"
            and int(row["horizon_checkups"]) in {2, 3}
            and row["reference_name"] in {"persistence", "capacity_state"}
        ]
        c_rate = [
            row
            for row in target_rows
            if row["split_name"] == "c_rate_holdout_fold"
            and int(row["horizon_checkups"]) in {2, 3}
            and row["reference_name"] in {"persistence", "capacity_state"}
        ]
        primary_pass_count = sum(_as_float(row.get("relative_gain")) >= 0.10 for row in primary)
        c_rate_pass_count = sum(_as_float(row.get("gain")) >= 0.0 for row in c_rate)
        any_gain = any(_as_float(row.get("gain")) > 0.0 for row in target_rows)
        if primary and c_rate and primary_pass_count == len(primary) and c_rate_pass_count == len(c_rate):
            status = "supported_for_diagnostics"
        elif primary and (primary_pass_count >= len(primary) / 2 or c_rate_pass_count >= len(c_rate) / 2):
            status = "partially_supported"
        elif any_gain:
            status = "diagnostic_only"
        else:
            status = "not_supported"
        output.append(
            {
                "target_name": target,
                "diagnostic_family": str(target_rows[0]["diagnostic_family"]) if target_rows else "",
                "status": status,
                "primary_rows": len(primary),
                "primary_rows_passing_10pct_gain": primary_pass_count,
                "c_rate_rows": len(c_rate),
                "c_rate_rows_noncollapsed": c_rate_pass_count,
                "best_primary_relative_gain": max((_as_float(row.get("relative_gain")) for row in primary), default=math.nan),
                "min_primary_relative_gain": min((_as_float(row.get("relative_gain")) for row in primary), default=math.nan),
                "best_c_rate_relative_gain": max((_as_float(row.get("relative_gain")) for row in c_rate), default=math.nan),
                "min_c_rate_gain": min((_as_float(row.get("gain")) for row in c_rate), default=math.nan),
                "allowed_wording": _endpoint_allowed_wording(status, target),
                "forbidden_wording": "broad endpoint forecasting, architecture, CBAT, calibrated risk/uncertainty, policy ranking, causal claims, or same-cell counterfactuals are authorized",
            }
        )
    output.extend(
        [
            {
                "target_name": "capacity_plus_pulse_eis_architecture",
                "diagnostic_family": "blocked_branch",
                "status": "blocked",
                "primary_rows": 0,
                "primary_rows_passing_10pct_gain": 0,
                "c_rate_rows": 0,
                "c_rate_rows_noncollapsed": 0,
                "best_primary_relative_gain": math.nan,
                "min_primary_relative_gain": math.nan,
                "best_c_rate_relative_gain": math.nan,
                "min_c_rate_gain": math.nan,
                "allowed_wording": "architecture remains blocked",
                "forbidden_wording": "CBAT or broad multimodal architecture is authorized",
            },
            {
                "target_name": "calibrated_risk_or_uncertainty",
                "diagnostic_family": "blocked_branch",
                "status": "blocked",
                "primary_rows": 0,
                "primary_rows_passing_10pct_gain": 0,
                "c_rate_rows": 0,
                "c_rate_rows_noncollapsed": 0,
                "best_primary_relative_gain": math.nan,
                "min_primary_relative_gain": math.nan,
                "best_c_rate_relative_gain": math.nan,
                "min_c_rate_gain": math.nan,
                "allowed_wording": "calibration was not tested in this gate",
                "forbidden_wording": "endpoint forecasts are calibrated risk or uncertainty",
            },
        ]
    )
    return output


def diagnostic_horizon_claim_readiness(report: dict[str, Any]) -> dict[str, Any]:
    gains = diagnostic_horizon_gain_rows(list(report["metrics"]))
    primary = [
        row
        for row in gains
        if row["split_name"] == "all"
        and int(row["horizon_checkups"]) in {2, 3}
        and row["reference_name"] in {"persistence", "capacity_state"}
    ]
    c_rate = [
        row
        for row in gains
        if row["split_name"] == "c_rate_holdout_fold"
        and int(row["horizon_checkups"]) in {2, 3}
        and row["reference_name"] in {"persistence", "capacity_state"}
    ]
    primary_pass = bool(primary) and all(float(row["relative_gain"] or 0.0) >= 0.10 for row in primary)
    c_rate_noncollapse = bool(c_rate) and all(float(row["gain"]) >= 0.0 for row in c_rate)
    any_gain = any(float(row["gain"]) > 0.0 for row in gains)
    primary_pass_count = sum(float(row["relative_gain"] or 0.0) >= 0.10 for row in primary)
    c_rate_noncollapse_count = sum(float(row["gain"]) >= 0.0 for row in c_rate)
    if primary_pass and c_rate_noncollapse and report["leakage_audit"]["status"] == "passed":
        status = "supported_for_diagnostics"
    elif any_gain and report["leakage_audit"]["status"] == "passed":
        status = "partially_supported"
    else:
        status = "not_supported"
    return {
        "diagnostic_horizon_forecasting": status,
        "beats_persistence_and_capacity_state": "supported_for_diagnostics" if primary_pass else "not_supported",
        "c_rate_noncollapse": "supported_for_diagnostics" if c_rate_noncollapse else "not_supported",
        "leakage_audit": report["leakage_audit"]["status"],
        "cbat_architecture": "blocked",
        "policy_ranking": "blocked",
        "calibrated_risk_or_uncertainty": "blocked",
        "primary_rows": len(primary),
        "primary_rows_passing_10pct_gain": primary_pass_count,
        "best_primary_relative_gain": max((float(row["relative_gain"] or 0.0) for row in primary), default=None),
        "min_primary_relative_gain": min((float(row["relative_gain"] or 0.0) for row in primary), default=None),
        "c_rate_rows": len(c_rate),
        "c_rate_rows_noncollapsed": c_rate_noncollapse_count,
        "best_c_rate_relative_gain": max((float(row["relative_gain"] or 0.0) for row in c_rate), default=None),
        "min_c_rate_gain": min((float(row["gain"]) for row in c_rate), default=None),
    }


def leakage_audit(feature_groups: list[str] | tuple[str, ...]) -> dict[str, Any]:
    rows = []
    status = "passed"
    for group in feature_groups:
        numeric = set(NUMERIC_FEATURES[group])
        leakage = sorted(numeric & FORBIDDEN_FEATURE_FIELDS)
        if leakage:
            status = "failed"
        rows.append(
            {
                "feature_group": group,
                "forbidden_fields": leakage,
                "status": "failed" if leakage else "passed",
                "claim_scope": "prospective_checkup_k_diagnostic_endpoint_forecasting",
            }
        )
    return {"status": status, "rows": rows}


def _write_claim_readiness_md(readiness: dict[str, Any], out: Path) -> None:
    lines = [
        "# Diagnostic-Horizon Claim Readiness",
        "",
        "This gate forecasts future PULSE/EIS scalar diagnostic endpoints. It does not use future diagnostic values as features.",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        (
            "| Diagnostic endpoint forecasting | "
            f"`{readiness['diagnostic_horizon_forecasting']}` | "
            "DH3 must beat persistence and capacity-state references on primary horizon-2/3 rows by at least 10% and avoid C-rate collapse. |"
        ),
        (
            "| Primary reference gains | "
            f"`{readiness['beats_persistence_and_capacity_state']}` | "
            f"`{readiness['primary_rows_passing_10pct_gain']}/{readiness['primary_rows']}` primary rows pass the 10% gain rule; "
            f"best relative gain `{readiness['best_primary_relative_gain']}`, minimum `{readiness['min_primary_relative_gain']}`. |"
        ),
        (
            "| C-rate non-collapse | "
            f"`{readiness['c_rate_noncollapse']}` | "
            f"`{readiness['c_rate_rows_noncollapsed']}/{readiness['c_rate_rows']}` C-rate rows have non-negative gain; "
            f"best relative gain `{readiness['best_c_rate_relative_gain']}`, minimum gain `{readiness['min_c_rate_gain']}`. |"
        ),
        f"| Leakage audit | `{readiness['leakage_audit']}` | Feature groups exclude future diagnostic values and diagnostic deltas. |",
        f"| CBAT architecture | `{readiness['cbat_architecture']}` | Not tested. |",
        f"| Policy ranking | `{readiness['policy_ranking']}` | Not tested. |",
        f"| Calibrated risk or uncertainty | `{readiness['calibrated_risk_or_uncertainty']}` | Not tested. |",
        "",
        "Allowed wording must stay limited to non-neural diagnostic endpoint forecasting under grouped validation.",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary_md(report: dict[str, Any], leaderboard: list[dict[str, Any]], out: Path) -> None:
    best = min(leaderboard, key=lambda row: float(row["mean_mae"])) if leaderboard else None
    lines = [
        "# Diagnostic-Horizon Baseline Summary",
        "",
        f"Schema version: `{report['schema_version']}`",
        "",
        "This run forecasts future PULSE/EIS scalar diagnostic endpoints from check-up-k state and nominal metadata.",
        "",
        f"Metric rows: `{report['row_counts']['metrics']}`",
        f"Prediction rows: `{report['row_counts']['predictions']}`",
    ]
    if best:
        lines.append(
            "Best leaderboard row: "
            f"`{best['target_name']}` horizon `{best['horizon_checkups']}` split `{best['split_name']}` "
            f"model `{best['model_level']}` feature `{best['feature_group']}` mean MAE `{best['mean_mae']}`."
        )
    lines.extend(["", "This is endpoint forecasting, not architecture validation."])
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_diagnostic_horizon_forensics_md(
    report: dict[str, Any],
    endpoint_failure_rows: list[dict[str, Any]],
    target_horizon_rows: list[dict[str, Any]],
    c_rate_failure_rows: list[dict[str, Any]],
    persistence_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
    out: Path,
) -> None:
    primary = [row for row in endpoint_failure_rows if row["is_primary_gate_row"]]
    primary_pass = [row for row in primary if row["passes_10pct_gain"]]
    c_rate = [row for row in endpoint_failure_rows if row["is_c_rate_gate_row"]]
    c_rate_pass = [row for row in c_rate if row["passes_noncollapse"]]
    weakest_primary = sorted(primary, key=lambda row: _as_float(row.get("relative_gain")))[:5]
    weakest_c_rate = sorted(c_rate, key=lambda row: _as_float(row.get("gain")))[:5]
    strongest_targets = sorted(
        [row for row in target_horizon_rows if row["split_name"] == "all" and row["reference_name"] == "capacity_state"],
        key=lambda row: _as_float(row.get("mean_relative_gain")),
        reverse=True,
    )[:5]
    low_delta_targets = sorted(
        persistence_rows,
        key=lambda row: _as_float(row.get("median_abs_delta_from_current")),
    )[:5]
    lines = [
        "# Diagnostic-Horizon Failure Forensics",
        "",
        "This report explains the Milestone 8.2 partial result using existing diagnostic-horizon artifacts only.",
        "",
        "## Inputs",
        "",
        f"- Metric rows: `{report['row_counts']['metrics']}`",
        f"- Prediction rows: `{report['row_counts']['predictions']}`",
        "",
        "## Gate Summary",
        "",
        f"- Primary 10% gain rows passed: `{len(primary_pass)}/{len(primary)}`",
        f"- C-rate non-collapse rows passed: `{len(c_rate_pass)}/{len(c_rate)}`",
        "- Architecture, calibrated risk, policy, causal, same-cell counterfactual, and CBAT claims remain blocked.",
        "",
        "## Weakest Primary Rows",
        "",
        "| Target | Horizon | Reference | Relative gain | Gain | Reason |",
        "|---|---:|---|---:|---:|---|",
    ]
    for row in weakest_primary:
        lines.append(
            f"| `{row['target_name']}` | `{row['horizon_checkups']}` | `{row['reference_name']}` | "
            f"`{row['relative_gain']}` | `{row['gain']}` | `{row['failure_reason']}` |"
        )
    lines.extend(
        [
            "",
            "## Weakest C-Rate Rows",
            "",
            "| Target | Horizon | Reference | Relative gain | Gain | Reason |",
            "|---|---:|---|---:|---:|---|",
        ]
    )
    for row in weakest_c_rate:
        lines.append(
            f"| `{row['target_name']}` | `{row['horizon_checkups']}` | `{row['reference_name']}` | "
            f"`{row['relative_gain']}` | `{row['gain']}` | `{row['failure_reason']}` |"
        )
    lines.extend(
        [
            "",
            "## Strongest Capacity-State Gains",
            "",
            "| Target | Horizon | Mean relative gain | Positive rows |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in strongest_targets:
        lines.append(
            f"| `{row['target_name']}` | `{row['horizon_checkups']}` | "
            f"`{row['mean_relative_gain']}` | `{row['positive_gain_rows']}/{row['rows']}` |"
        )
    lines.extend(
        [
            "",
            "## Low-Movement Endpoint Diagnostics",
            "",
            "| Target | Horizon | Median abs delta from current | Persistence MAE |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in low_delta_targets:
        lines.append(
            f"| `{row['target_name']}` | `{row['horizon_checkups']}` | "
            f"`{row['median_abs_delta_from_current']}` | `{row['all_split_persistence_mae']}` |"
        )
    lines.extend(
        [
            "",
            "## Condition Hotspots",
            "",
            "| Split | Target | Horizon | Model | Feature | Parameter set | Mean abs error |",
            "|---|---|---:|---|---|---:|---:|",
        ]
    )
    for row in hotspot_rows[:10]:
        lines.append(
            f"| `{row['split_name']}` | `{row['target_name']}` | `{row['horizon_checkups']}` | "
            f"`{row['model_level']}` | `{row['feature_group']}` | `{row['parameter_set']}` | "
            f"`{row['mean_abs_error']}` |"
        )
    lines.extend(
        [
            "",
            "Decision: the Milestone 8.2 result remains partial diagnostic endpoint evidence. Do not broaden to architecture or calibrated-risk wording.",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_endpoint_claim_readiness_md(readiness_rows: list[dict[str, Any]], out: Path) -> None:
    lines = [
        "# Diagnostic-Horizon Endpoint Claim Readiness",
        "",
        "Endpoint-specific statuses are conservative and do not override the overall Milestone 8.2 partial result.",
        "",
        "| Target | Status | Primary rows | C-rate rows | Allowed wording |",
        "|---|---|---:|---:|---|",
    ]
    for row in readiness_rows:
        lines.append(
            f"| `{row['target_name']}` | `{row['status']}` | "
            f"`{row['primary_rows_passing_10pct_gain']}/{row['primary_rows']}` | "
            f"`{row['c_rate_rows_noncollapsed']}/{row['c_rate_rows']}` | "
            f"{row['allowed_wording']} |"
        )
    lines.extend(
        [
            "",
            "Forbidden wording remains: broad endpoint forecasting, capacity+PULSE+EIS architecture, CBAT, calibrated risk or uncertainty, policy ranking, causal effects, and same-cell counterfactuals.",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _endpoint_allowed_wording(status: str, target: str) -> str:
    if status == "supported_for_diagnostics":
        return f"`{target}` supports endpoint-specific diagnostic forecasting under the Milestone 8.2 grouped checks"
    if status == "partially_supported":
        return f"`{target}` has partial endpoint-forecasting signal but misses at least one strict guardrail"
    if status == "diagnostic_only":
        return f"`{target}` has isolated diagnostic gains only"
    if status == "not_supported":
        return f"`{target}` endpoint forecasting is not supported by this gate"
    return "blocked branch"


def _condition_mae_rows(rows: list[dict[str, Any]], abs_errors: list[float]) -> list[dict[str, Any]]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for row, error in zip(rows, abs_errors):
        grouped[int(row["parameter_set"])].append(error)
    return [{"parameter_set": key, "mae": _mean(values), "n": len(values)} for key, values in grouped.items()]


def _target_value(row: dict[str, Any]) -> float:
    return _as_float(row.get("diagnostic_value_kh"))


def _find_row(
    rows: list[dict[str, Any]],
    *,
    target: str,
    horizon: int,
    split_name: str,
    model_level: str,
    feature_group: str,
) -> dict[str, Any] | None:
    for row in rows:
        if (
            str(row["target_name"]) == target
            and int(row["horizon_checkups"]) == horizon
            and str(row["split_name"]) == split_name
            and str(row["model_level"]) == model_level
            and str(row["feature_group"]) == feature_group
        ):
            return row
    return None


def _normalize_selection(
    values: list[str] | None,
    allowed: tuple[str, ...],
    default: tuple[str, ...],
    label: str,
) -> list[str]:
    selected = list(default if values is None else values)
    output = []
    seen = set()
    for value in selected:
        item = str(value).strip()
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            output.append(item)
    unknown = sorted(set(output) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}(s): {unknown}. Allowed: {list(allowed)}")
    if not output:
        raise ValueError(f"At least one {label} must be selected.")
    return output


def _normalize_horizons(horizons: list[int] | None) -> list[int]:
    selected = list(DEFAULT_HORIZONS if horizons is None else horizons)
    output = []
    seen = set()
    for value in selected:
        horizon = int(value)
        if horizon <= 0:
            raise ValueError("Horizons must be positive check-up counts.")
        if horizon not in seen:
            seen.add(horizon)
            output.append(horizon)
    if not output:
        raise ValueError("At least one horizon must be selected.")
    return output


def _default_report_dir(path: Path) -> Path:
    return path.with_suffix("")


def _import_sklearn_stack() -> tuple[Any, Any, Any]:
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scikit-learn is required for diagnostic horizon baselines.") from exc
    return np, Ridge, HistGradientBoostingRegressor


def _category(value: Any) -> str:
    if value is None:
        return "missing"
    text = str(value)
    return text if text else "missing"


def _as_float(value: Any, default: float = math.nan) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return math.nan
    return sum(finite) / len(finite)


def _median(values: list[float]) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return math.nan
    midpoint = len(finite) // 2
    if len(finite) % 2:
        return finite[midpoint]
    return (finite[midpoint - 1] + finite[midpoint]) / 2.0


def _std(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return math.nan
    mean = sum(finite) / len(finite)
    return math.sqrt(sum((value - mean) ** 2 for value in finite) / len(finite))


def _safe_ratio(numerator: Any, denominator: Any) -> float | None:
    num = _as_float(numerator)
    den = _as_float(denominator)
    if not math.isfinite(num) or not math.isfinite(den) or abs(den) <= 1e-12:
        return None
    return num / den


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
