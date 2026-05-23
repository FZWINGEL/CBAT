"""Milestone 2.1 scalar EIS diagnostic baseline runner."""

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

from mbp.baselines.capacity import (
    assert_no_parameter_set_leakage,
    iter_split_instances,
    load_baseline_rows,
)

SCHEMA_VERSION = "gate21.eis_baseline.v1"
EIS_TARGETS = (
    "delta_eis_z_abs_1kHz",
    "eis_z_abs_1kHz_k1",
    "delta_nyquist_semicircle_width_proxy",
    "nyquist_semicircle_width_proxy_k1",
)
MODEL_LEVELS = ("L0_persistence", "L1_ridge", "L2_hist_gradient_boosting")
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
FEATURE_GROUPS = (
    "E0_persistence",
    "E1_state_time",
    "E2_state_capacity",
    "E3_state_nominal",
    "E4_log_age_scalar",
    "E5_stress_v1_1",
)
STRESS_GROUPS = {"E5_stress_v1_1"}

EIS_PREDICTION_SCHEMA = pa.schema(
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
        ("y_true", pa.float64()),
        ("y_pred", pa.float64()),
    ]
)

EIS_PRIOR_FEATURES = (
    "eis_z_real_1kHz_k",
    "eis_z_imag_1kHz_k",
    "eis_z_abs_1kHz_k",
    "eis_phase_1kHz_k",
    "nyquist_re_min_k",
    "nyquist_re_max_k",
    "nyquist_im_peak_abs_k",
    "nyquist_semicircle_width_proxy_k",
    "valid_modeling_fraction_k",
)
EIS_FORBIDDEN_FEATURES = (
    "eis_z_real_1kHz_k1",
    "eis_z_imag_1kHz_k1",
    "eis_z_abs_1kHz_k1",
    "eis_phase_1kHz_k1",
    "nyquist_re_min_k1",
    "nyquist_re_max_k1",
    "nyquist_im_peak_abs_k1",
    "nyquist_semicircle_width_proxy_k1",
    "delta_eis_z_real_1kHz",
    "delta_eis_z_abs_1kHz",
    "delta_nyquist_semicircle_width_proxy",
    "R0_mOhm_k",
    "R1_mOhm_k",
)

NUMERIC_FEATURES: dict[str, tuple[str, ...]] = {
    "E0_persistence": ("eis_z_abs_1kHz_k", "nyquist_semicircle_width_proxy_k"),
    "E1_state_time": (
        "eis_z_abs_1kHz_k",
        "nyquist_semicircle_width_proxy_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
    ),
    "E2_state_capacity": (
        "eis_z_abs_1kHz_k",
        "nyquist_semicircle_width_proxy_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "capacity_Ah_k",
    ),
    "E3_state_nominal": (
        "eis_z_abs_1kHz_k",
        "nyquist_semicircle_width_proxy_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "capacity_Ah_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "E4_log_age_scalar": (
        "eis_z_abs_1kHz_k",
        "nyquist_semicircle_width_proxy_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "capacity_Ah_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_efc_delta",
        "log_age_mean_voltage_V",
        "log_age_mean_temperature_C",
        "log_age_mean_abs_current_A",
        "log_age_max_abs_current_A",
        "log_age_mean_soc",
    ),
    "E5_stress_v1_1": (
        "eis_z_abs_1kHz_k",
        "nyquist_semicircle_width_proxy_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "capacity_Ah_k",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_efc_delta",
        "log_age_mean_voltage_V",
        "log_age_mean_temperature_C",
        "log_age_mean_abs_current_A",
        "log_age_max_abs_current_A",
        "log_age_mean_soc",
        "stress_coverage_fraction",
        "max_log_age_gap_s",
        "cold_time_h",
        "high_voltage_time_h",
        "abs_current_ge_1p5C_time_h",
        "abs_current_ge_5over3C_time_h",
    ),
}

CATEGORICAL_FEATURES: dict[str, tuple[str, ...]] = {
    "E0_persistence": (),
    "E1_state_time": (),
    "E2_state_capacity": (),
    "E3_state_nominal": ("aging_mode", "voltage_window_family"),
    "E4_log_age_scalar": ("aging_mode", "voltage_window_family"),
    "E5_stress_v1_1": ("aging_mode", "voltage_window_family"),
}


@dataclass(frozen=True)
class EisFeatureEncoder:
    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    impute_values: dict[str, float]
    scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "EisFeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown EIS feature group: {feature_group}")
        leakage = (set(NUMERIC_FEATURES[feature_group]) | set(CATEGORICAL_FEATURES[feature_group])) & set(EIS_FORBIDDEN_FEATURES)
        if leakage:
            raise ValueError(f"EIS feature group {feature_group} includes forbidden fields: {sorted(leakage)}")
        impute_values: dict[str, float] = {}
        scale_values: dict[str, float] = {}
        for column in NUMERIC_FEATURES[feature_group]:
            values = [_as_float(row.get(column)) for row in rows]
            finite = [value for value in values if math.isfinite(value)]
            mean = sum(finite) / len(finite) if finite else 0.0
            variance = sum((value - mean) ** 2 for value in finite) / len(finite) if finite else 0.0
            impute_values[column] = mean
            scale_values[column] = math.sqrt(variance) if variance > 0 else 1.0
        categorical_values = {
            column: tuple(sorted({_category(row.get(column)) for row in rows}))
            for column in CATEGORICAL_FEATURES[feature_group]
        }
        return cls(
            feature_group,
            NUMERIC_FEATURES[feature_group],
            CATEGORICAL_FEATURES[feature_group],
            impute_values,
            scale_values,
            categorical_values,
        )

    def transform(self, rows: list[dict[str, Any]], *, standardize_numeric: bool = False) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                numeric = value if math.isfinite(value) else self.impute_values[column]
                if standardize_numeric:
                    numeric = (numeric - self.impute_values[column]) / self.scale_values[column]
                values.append(numeric)
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(1.0 if observed == category else 0.0 for category in self.categorical_values[column])
            matrix.append(values)
        return matrix


def run_eis_baselines(
    interval_table_path: Path,
    interval_subsets_path: Path,
    eis_targets_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    *,
    stress_features_path: Path | None = None,
    report_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    hgb_max_iter: int = 50,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
) -> dict[str, Any]:
    selected_models = _normalize(model_levels, MODEL_LEVELS, "model level")
    selected_features = _normalize(feature_groups, FEATURE_GROUPS, "feature group")
    selected_targets = _normalize(targets, EIS_TARGETS, "target")
    selected_splits = _normalize(split_views, SPLIT_COLUMNS, "split view")
    if STRESS_GROUPS & set(selected_features) and stress_features_path is None:
        raise ValueError("E5_stress_v1_1 requires --stress-features.")
    _preflight(selected_models)
    all_rows, subset_rows = load_eis_rows(
        interval_table_path,
        interval_subsets_path,
        eis_targets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    sensitivity_rows = [row for row in subset_rows if not bool(row["sensitivity_flagged_monotonicity"])]
    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for run_scope, rows in (("primary", subset_rows), ("sensitivity_excluding_monotonicity", sensitivity_rows)):
        for target in selected_targets:
            target_rows = [row for row in rows if math.isfinite(_target_value(row, target))]
            if not target_rows:
                continue
            for split_name in selected_splits:
                for heldout_fold, train_rows, test_rows in iter_split_instances(target_rows, split_name):
                    assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                    for model_level in selected_models:
                        groups = ("E0_persistence",) if model_level == "L0_persistence" else tuple(selected_features)
                        for feature_group in groups:
                            fold_predictions = predict_eis_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                            )
                            metrics.append(_metrics(test_rows, fold_predictions, target, subset, run_scope, split_name, heldout_fold, model_level, feature_group, train_rows))
                            predictions.extend(_prediction_rows(test_rows, fold_predictions, subset, run_scope, split_name, heldout_fold, model_level, feature_group, target))
    resolved_report_dir = report_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(predictions, schema=EIS_PREDICTION_SCHEMA), predictions_out_path)
    report = {
        "status": "passed" if metrics else "warning",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "eis_targets": str(eis_targets_path),
            "stress_features": str(stress_features_path) if stress_features_path else None,
        },
        "outputs": {"report": str(out_path), "predictions": str(predictions_out_path), "report_dir": str(resolved_report_dir)},
        "subset": subset,
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "targets": selected_targets,
        "model_levels": selected_models,
        "feature_groups": selected_features,
        "split_views": selected_splits,
        "row_counts": _row_counts(all_rows, subset_rows, sensitivity_rows),
        "leakage_audit": eis_leakage_audit(selected_features),
        "metrics": metrics,
        "warnings": [] if metrics else ["no_finite_target_rows_for_selected_configuration"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_eis_artifacts(report, resolved_report_dir)
    return report


def load_eis_rows(
    interval_table_path: Path,
    interval_subsets_path: Path,
    eis_targets_path: Path,
    subset: str,
    *,
    stress_features_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows, selected_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    target_rows = pq.read_table(eis_targets_path).to_pylist()
    target_by_key = {_interval_key(row): row for row in target_rows}
    merged: list[dict[str, Any]] = []
    for row in all_rows:
        target = target_by_key.get(_interval_key(row))
        if target is None:
            continue
        combined = dict(row)
        for column, value in target.items():
            if column not in {"cell_id", "parameter_set", "replicate_id", "checkup_k", "checkup_k_next", "schema_version"}:
                combined[column] = value
        merged.append(combined)
    selected_keys = {_interval_key(row) for row in selected_rows}
    selected = [row for row in merged if _interval_key(row) in selected_keys]
    if not selected:
        raise ValueError("No EIS target rows joined to the selected interval subset.")
    return merged, selected


def predict_eis_target(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int,
) -> list[float]:
    if model_level == "L0_persistence":
        return [_persistence(row, target) for row in test_rows]
    np, Ridge, HistGradientBoostingRegressor = _import_sklearn()
    encoder = EisFeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=model_level == "L1_ridge"), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=model_level == "L1_ridge"), dtype=float)
    y_train = np.asarray([_target_value(row, target) for row in train_rows], dtype=float)
    if model_level == "L1_ridge":
        model = Ridge(alpha=1.0)
    elif model_level == "L2_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    else:
        raise ValueError(f"Unknown EIS model level: {model_level}")
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict(x_test)]


def eis_leakage_audit(feature_groups: list[str] | tuple[str, ...]) -> dict[str, Any]:
    forbidden_hits: dict[str, list[str]] = {}
    for group in feature_groups:
        fields = set(NUMERIC_FEATURES.get(group, ())) | set(CATEGORICAL_FEATURES.get(group, ()))
        hits = sorted(fields & set(EIS_FORBIDDEN_FEATURES))
        if hits:
            forbidden_hits[group] = hits
    if forbidden_hits:
        raise ValueError(f"Forbidden EIS fields in feature groups: {forbidden_hits}")
    return {
        "status": "passed",
        "allowed": list(EIS_PRIOR_FEATURES),
        "forbidden": list(EIS_FORBIDDEN_FEATURES),
        "drt_fields_absent": True,
        "embedding_fields_absent": True,
    }


def render_eis_artifacts(report: dict[str, Any], report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    leaderboard = _leaderboard_rows(list(report["metrics"]))
    _write_csv(report_dir / "leaderboard.csv", leaderboard)
    _write_summary(report, leaderboard, report_dir / "baseline_summary.md")
    _write_diagnostics(report, leaderboard, report_dir / "eis_diagnostics.md")


def _metrics(rows: list[dict[str, Any]], predictions: list[float], target: str, subset_name: str, run_scope: str, split_name: str, heldout_fold: int, model_level: str, feature_group: str, train_rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [pred - _target_value(row, target) for row, pred in zip(rows, predictions)]
    abs_errors = [abs(error) for error in errors]
    by_condition: dict[int, list[float]] = defaultdict(list)
    for row, error in zip(rows, abs_errors):
        by_condition[int(row["parameter_set"])].append(error)
    condition_mae = [_mean(values) for values in by_condition.values()]
    return {
        "subset_name": subset_name,
        "run_scope": run_scope,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "target": target,
        "train_rows": len(train_rows),
        "test_rows": len(rows),
        "train_parameter_sets": len({int(row["parameter_set"]) for row in train_rows}),
        "test_parameter_sets": len({int(row["parameter_set"]) for row in rows}),
        "mae": _mean(abs_errors),
        "rmse": math.sqrt(_mean([error * error for error in errors])),
        "condition_mean_mae": _mean(condition_mae),
        "condition_median_mae": _median(condition_mae),
        "worst_condition_mae": max(condition_mae),
    }


def _leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        grouped[(metric["run_scope"], metric["model_level"], metric["feature_group"], metric["target"], metric["split_name"])].append(metric)
    rows: list[dict[str, Any]] = []
    for (run_scope, model, feature, target, split), group in sorted(grouped.items()):
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model,
                "feature_group": feature,
                "target": target,
                "split_name": split,
                "fold_count": len(group),
                "condition_mean_mae": _mean([float(row["condition_mean_mae"]) for row in group]),
                "condition_median_mae": _mean([float(row["condition_median_mae"]) for row in group]),
                "worst_condition_mae": max(float(row["worst_condition_mae"]) for row in group),
                "mean_mae": _mean([float(row["mae"]) for row in group]),
                "mean_rmse": _mean([float(row["rmse"]) for row in group]),
                "test_rows": sum(int(row["test_rows"]) for row in group),
            }
        )
    return rows


def _prediction_rows(rows: list[dict[str, Any]], predictions: list[float], subset_name: str, run_scope: str, split_name: str, heldout_fold: int, model_level: str, feature_group: str, target: str) -> list[dict[str, Any]]:
    return [
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
            "y_true": _target_value(row, target),
            "y_pred": float(pred),
        }
        for row, pred in zip(rows, predictions)
    ]


def _write_summary(report: dict[str, Any], leaderboard: list[dict[str, Any]], path: Path) -> None:
    best = sorted([row for row in leaderboard if row["run_scope"] == "primary"], key=lambda row: float(row["condition_mean_mae"]))[:10]
    lines = [
        "# EIS Scalar Baseline Summary",
        "",
        "This is a scalar EIS diagnostic baseline, not an EIS improvement claim.",
        "",
        "| Target | Split | Model | Feature group | Condition mean MAE |",
        "|---|---|---|---|---:|",
    ]
    for row in best:
        lines.append(f"| `{row['target']}` | `{row['split_name']}` | `{row['model_level']}` | `{row['feature_group']}` | {float(row['condition_mean_mae']):.6g} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_diagnostics(report: dict[str, Any], leaderboard: list[dict[str, Any]], path: Path) -> None:
    best_by_target = []
    for target in sorted({row["target"] for row in leaderboard}):
        rows = [row for row in leaderboard if row["run_scope"] == "primary" and row["target"] == target]
        if rows:
            best_by_target.append(min(rows, key=lambda row: float(row["condition_mean_mae"])))
    lines = [
        "# EIS Diagnostics",
        "",
        "Prior EIS `k` features are allowed for scalar EIS endpoints. Future EIS `k1`, EIS deltas, DRT, embeddings, and R0/R1 without leakage-safe provenance are blocked as non-EIS inputs.",
        "",
        "| Target | Split | Model | Feature group | Condition mean MAE | Worst condition MAE |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in best_by_target:
        lines.append(f"| `{row['target']}` | `{row['split_name']}` | `{row['model_level']}` | `{row['feature_group']}` | {float(row['condition_mean_mae']):.6g} | {float(row['worst_condition_mae']):.6g} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _row_counts(all_rows: list[dict[str, Any]], subset_rows: list[dict[str, Any]], sensitivity_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "joined_interval_rows": len(all_rows),
        "selected_subset_rows": len(subset_rows),
        "sensitivity_excluding_monotonicity_rows": len(sensitivity_rows),
        "selected_cells": len({str(row["cell_id"]) for row in subset_rows}),
        "selected_parameter_sets": len({int(row["parameter_set"]) for row in subset_rows}),
    }


def _target_value(row: dict[str, Any], target: str) -> float:
    return _as_float(row.get(target))


def _persistence(row: dict[str, Any], target: str) -> float:
    if target.startswith("delta_"):
        return 0.0
    if target == "eis_z_abs_1kHz_k1":
        return _as_float(row.get("eis_z_abs_1kHz_k"))
    if target == "nyquist_semicircle_width_proxy_k1":
        return _as_float(row.get("nyquist_semicircle_width_proxy_k"))
    raise ValueError(f"Unknown EIS target: {target}")


def _normalize(selected: list[str] | None, allowed: tuple[str, ...], label: str) -> list[str]:
    values = list(allowed) if selected is None else [item.strip() for item in selected if item.strip()]
    unknown = sorted(set(values) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}(s): {unknown}. Allowed: {list(allowed)}")
    if not values:
        raise ValueError(f"At least one {label} must be selected.")
    return values


def _preflight(model_levels: list[str]) -> None:
    if any(model != "L0_persistence" for model in model_levels):
        _import_sklearn()


def _import_sklearn() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError("EIS baselines require `uv sync --extra baseline`.") from exc
    return np, Ridge, HistGradientBoostingRegressor


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _category(value: Any) -> str:
    return "unknown" if value is None or str(value).strip() == "" else str(value)


def _mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return sum(finite) / len(finite) if finite else math.nan


def _median(values: list[float]) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return math.nan
    mid = len(finite) // 2
    if len(finite) % 2:
        return finite[mid]
    return (finite[mid - 1] + finite[mid]) / 2.0
