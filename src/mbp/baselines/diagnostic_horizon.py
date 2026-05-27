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
