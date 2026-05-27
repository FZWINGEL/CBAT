"""Milestone 5.9 hierarchical replicate-aware capacity baselines."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import (
    BASELINE_PREDICTION_SCHEMA,
    DEFAULT_HGB_MAX_ITER,
    DIRECT_TARGETS,
    FeatureEncoder,
    SPLIT_COLUMNS,
    STRESS_FEATURE_GROUPS,
    assert_no_parameter_set_leakage,
    compute_metrics,
    iter_split_instances,
    load_baseline_rows,
)
from mbp.baselines.capacity import _as_float
from mbp.baselines.capacity import _evaluation_target_value
from mbp.baselines.capacity import _import_sklearn_stack
from mbp.baselines.capacity import _leaderboard_rows
from mbp.baselines.capacity import _mean
from mbp.baselines.capacity import _normalize_selection
from mbp.baselines.capacity import _nullable_float
from mbp.baselines.capacity import _point_prediction
from mbp.baselines.capacity import _prediction_to_evaluation_space
from mbp.baselines.capacity import _training_target_value
from mbp.baselines.capacity import _write_csv

SCHEMA_VERSION = "gate59.hierarchical_replicate_capacity.v1"
DEFAULT_FEATURE_GROUPS = ("F4_state_log_age_scalar",)
HIERARCHICAL_MODEL_LEVELS = (
    "H0_global_train_mean",
    "H1_state_time_ridge",
    "H2_partial_pooling_ridge",
    "H3_hgb_reference",
    "H4_hgb_residual_partial_pooling",
    "H5_replicate_variance_interval",
)
DEFAULT_MODEL_LEVELS = HIERARCHICAL_MODEL_LEVELS
PRIMARY_TARGET = "delta_capacity_Ah"
PRIMARY_SPLIT = "c_rate_holdout_fold"
POOLING_METHOD_COMPARISONS = (
    {
        "comparison_id": "ridge_partial_pooling_vs_ridge",
        "candidate_model_level": "H2_partial_pooling_ridge",
        "reference_model_level": "H1_state_time_ridge",
    },
    {
        "comparison_id": "hgb_partial_pooling_vs_hgb",
        "candidate_model_level": "H4_hgb_residual_partial_pooling",
        "reference_model_level": "H3_hgb_reference",
    },
    {
        "comparison_id": "replicate_interval_vs_hgb",
        "candidate_model_level": "H5_replicate_variance_interval",
        "reference_model_level": "H3_hgb_reference",
    },
)


@dataclass(frozen=True)
class PredictionBundle:
    predictions: list[dict[str, float | None]]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ResidualPool:
    offsets: dict[tuple[str, ...], float]
    counts: dict[tuple[str, ...], int]
    global_offset: float
    residual_count: int
    raw_group_count: int


def run_hierarchical_capacity(
    interval_table_path: Path,
    interval_subsets_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    *,
    stress_features_path: Path | None = None,
    out_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
    shrinkage_strength: float = 5.0,
    min_pool_count: int = 3,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
) -> dict[str, Any]:
    """Run train-only hierarchical/partial-pooling capacity comparators."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    if shrinkage_strength < 0.0:
        raise ValueError("shrinkage_strength must be non-negative.")
    if min_pool_count <= 0:
        raise ValueError("min_pool_count must be positive.")
    selected_models = _normalize_selection(
        model_levels,
        HIERARCHICAL_MODEL_LEVELS,
        "hierarchical model level",
        default=DEFAULT_MODEL_LEVELS,
    )
    selected_feature_groups = _normalize_selection(
        feature_groups,
        ("F4_state_log_age_scalar", "F8_timestamp_weighted_stress"),
        "feature group",
        default=DEFAULT_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, DIRECT_TARGETS, "target", default=DIRECT_TARGETS)
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError("Stress feature groups require --stress-features.")
    if any(model != "H0_global_train_mean" for model in selected_models):
        _import_sklearn_stack()

    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    sensitivity_rows = [
        row for row in subset_rows if not bool(row["sensitivity_flagged_monotonicity"])
    ]
    if not sensitivity_rows:
        raise ValueError("Sensitivity subset is empty after excluding monotonicity-flagged rows.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    for run_scope, rows in (
        ("primary", subset_rows),
        ("sensitivity_excluding_monotonicity", sensitivity_rows),
    ):
        for split_name in selected_splits:
            for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                leakage_rows.append(
                    _leakage_audit_row(
                        run_scope=run_scope,
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                        train_rows=train_rows,
                        test_rows=test_rows,
                    )
                )
                for model_level in selected_models:
                    model_feature_groups = (
                        ("global_mean",)
                        if model_level == "H0_global_train_mean"
                        else tuple(selected_feature_groups)
                    )
                    for feature_group in model_feature_groups:
                        for target in selected_targets:
                            bundle = predict_hierarchical_capacity_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                shrinkage_strength=shrinkage_strength,
                                min_pool_count=min_pool_count,
                            )
                            metric = compute_metrics(
                                test_rows,
                                bundle.predictions,
                                target=target,
                                subset_name=subset,
                                run_scope=run_scope,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                            )
                            metric.update(
                                {
                                    "schema_version": SCHEMA_VERSION,
                                    "shrinkage_strength": shrinkage_strength,
                                    "min_pool_count": min_pool_count,
                                    **bundle.metadata,
                                }
                            )
                            metrics.append(metric)
                            predictions.extend(
                                _hierarchical_prediction_rows(
                                    test_rows,
                                    bundle.predictions,
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
        raise ValueError("No metrics were generated.")

    report_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA).replace_schema_metadata(
            {b"schema_version": SCHEMA_VERSION.encode()}
        ),
        predictions_out_path,
    )
    leaderboard_rows = _leaderboard_rows(metrics)
    comparison_rows = hierarchical_comparison_rows(leaderboard_rows)
    paired_gain_rows = hierarchical_paired_condition_gain_rows(predictions)
    claim_readiness = hierarchical_claim_readiness(metrics, comparison_rows, paired_gain_rows)
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "stress_features": str(stress_features_path) if stress_features_path else None,
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "out_dir": str(report_dir),
        },
        "subset": subset,
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "shrinkage_strength": shrinkage_strength,
        "min_pool_count": min_pool_count,
        "model_levels": selected_models,
        "feature_groups": selected_feature_groups,
        "targets": selected_targets,
        "split_views": selected_splits,
        "row_counts": {
            "full_interval_rows": len(all_rows),
            "selected_subset_rows": len(subset_rows),
            "sensitivity_rows": len(sensitivity_rows),
            "metrics": len(metrics),
            "predictions": len(predictions),
            "leakage_audit_rows": len(leakage_rows),
        },
        "leakage_policy": (
            "Residual offsets, shrinkage factors, and interval radii are computed from outer "
            "training rows only. Parameter-set effects are never fit; held-out parameter sets "
            "fall back to stressor-family or global train residual offsets."
        ),
        "leakage_audit": leakage_rows,
        "paired_condition_gains": paired_gain_rows,
        "claim_readiness": claim_readiness,
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_hierarchical_diagnostics(report, report_dir)
    return report


def predict_hierarchical_capacity_target(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int,
    split_name: str,
    heldout_fold: int,
    shrinkage_strength: float,
    min_pool_count: int,
) -> PredictionBundle:
    """Fit/predict one hierarchical comparator for one grouped split."""
    if target not in DIRECT_TARGETS:
        raise ValueError(f"Unknown target: {target}")
    if model_level == "H0_global_train_mean":
        predictions = _global_mean_predictions(train_rows, test_rows, target)
        return PredictionBundle(
            predictions,
            {
                "base_model": "global_train_mean",
                "partial_pooling_enabled": False,
                "interval_enabled": False,
                "train_residual_count": 0,
                "pool_group_count": 0,
                "offset_applied_rows": 0,
                "global_fallback_rows": len(test_rows),
                "interval_radius": None,
            },
        )
    if model_level == "H1_state_time_ridge":
        _, test_predictions = _fit_ridge_train_test(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
        )
        return PredictionBundle(test_predictions, _base_metadata("ridge", len(test_rows)))
    if model_level == "H2_partial_pooling_ridge":
        train_predictions, test_predictions = _fit_ridge_train_test(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
        )
        return _partial_pooling_bundle(
            train_rows=train_rows,
            test_rows=test_rows,
            train_predictions=train_predictions,
            test_predictions=test_predictions,
            target=target,
            base_model="ridge",
            shrinkage_strength=shrinkage_strength,
            min_pool_count=min_pool_count,
            interval_enabled=False,
        )
    if model_level == "H3_hgb_reference":
        _, test_predictions = _fit_hgb_train_test(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
            seed=_variant_seed(seed, model_level, feature_group, target, split_name, heldout_fold),
            hgb_max_iter=hgb_max_iter,
        )
        return PredictionBundle(test_predictions, _base_metadata("hgb", len(test_rows)))
    if model_level == "H4_hgb_residual_partial_pooling":
        train_predictions, test_predictions = _fit_hgb_train_test(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
            seed=_variant_seed(seed, model_level, feature_group, target, split_name, heldout_fold),
            hgb_max_iter=hgb_max_iter,
        )
        return _partial_pooling_bundle(
            train_rows=train_rows,
            test_rows=test_rows,
            train_predictions=train_predictions,
            test_predictions=test_predictions,
            target=target,
            base_model="hgb",
            shrinkage_strength=shrinkage_strength,
            min_pool_count=min_pool_count,
            interval_enabled=False,
        )
    if model_level == "H5_replicate_variance_interval":
        train_predictions, test_predictions = _fit_hgb_train_test(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
            seed=_variant_seed(seed, model_level, feature_group, target, split_name, heldout_fold),
            hgb_max_iter=hgb_max_iter,
        )
        return _partial_pooling_bundle(
            train_rows=train_rows,
            test_rows=test_rows,
            train_predictions=train_predictions,
            test_predictions=test_predictions,
            target=target,
            base_model="hgb",
            shrinkage_strength=shrinkage_strength,
            min_pool_count=min_pool_count,
            interval_enabled=True,
        )
    raise ValueError(f"Unknown hierarchical model level: {model_level}")


def _global_mean_predictions(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
) -> list[dict[str, float | None]]:
    values = [_training_target_value(row, target) for row in train_rows]
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        raise ValueError(f"Target {target} has no finite train values.")
    mean_value = _mean(finite)
    return [_point_prediction(_prediction_to_evaluation_space(row, target, mean_value)) for row in test_rows]


def _fit_ridge_train_test(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
) -> tuple[list[dict[str, float | None]], list[dict[str, float | None]]]:
    np, Ridge, _ = _import_sklearn_stack()
    encoder = FeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows, standardize_numeric=True), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows, standardize_numeric=True), dtype=float)
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")
    model = Ridge(alpha=1.0)
    model.fit(x_train, y_train)
    return (
        _predictions_from_values(train_rows, target, model.predict(x_train)),
        _predictions_from_values(test_rows, target, model.predict(x_test)),
    )


def _fit_hgb_train_test(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int,
) -> tuple[list[dict[str, float | None]], list[dict[str, float | None]]]:
    np, _, HistGradientBoostingRegressor = _import_sklearn_stack()
    encoder = FeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows), dtype=float)
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")
    model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    model.fit(x_train, y_train)
    return (
        _predictions_from_values(train_rows, target, model.predict(x_train)),
        _predictions_from_values(test_rows, target, model.predict(x_test)),
    )


def _predictions_from_values(
    rows: list[dict[str, Any]],
    target: str,
    values: Any,
) -> list[dict[str, float | None]]:
    return [
        _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
        for row, value in zip(rows, values)
    ]


def _partial_pooling_bundle(
    *,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    train_predictions: list[dict[str, float | None]],
    test_predictions: list[dict[str, float | None]],
    target: str,
    base_model: str,
    shrinkage_strength: float,
    min_pool_count: int,
    interval_enabled: bool,
) -> PredictionBundle:
    pool = fit_train_residual_pool(
        train_rows,
        train_predictions,
        target=target,
        shrinkage_strength=shrinkage_strength,
        min_pool_count=min_pool_count,
    )
    residuals = train_residuals(train_rows, train_predictions, target)
    radius = (
        replicate_interval_radius(train_rows, residuals, target)
        if interval_enabled
        else None
    )
    adjusted: list[dict[str, float | None]] = []
    offset_applied_rows = 0
    fallback_rows = 0
    abs_offsets: list[float] = []
    for row, prediction in zip(test_rows, test_predictions):
        offset, used_specific_offset = pool_offset_for_row(row, pool)
        if used_specific_offset:
            offset_applied_rows += 1
        else:
            fallback_rows += 1
        abs_offsets.append(abs(offset))
        y_pred = _as_float(prediction["y_pred"]) + offset
        if interval_enabled:
            q_radius = float(radius or 0.0)
            adjusted.append(
                {
                    "y_pred": y_pred,
                    "y_pred_q10": y_pred - q_radius,
                    "y_pred_q50": y_pred,
                    "y_pred_q90": y_pred + q_radius,
                }
            )
        else:
            adjusted.append(_point_prediction(y_pred))
    return PredictionBundle(
        adjusted,
        {
            "base_model": base_model,
            "partial_pooling_enabled": True,
            "interval_enabled": interval_enabled,
            "train_residual_count": pool.residual_count,
            "pool_group_count": len(pool.offsets),
            "raw_pool_group_count": pool.raw_group_count,
            "offset_applied_rows": offset_applied_rows,
            "global_fallback_rows": fallback_rows,
            "mean_abs_offset": _mean(abs_offsets) if abs_offsets else 0.0,
            "global_residual_offset": pool.global_offset,
            "interval_radius": radius,
        },
    )


def train_residuals(
    train_rows: list[dict[str, Any]],
    train_predictions: list[dict[str, float | None]],
    target: str,
) -> list[float]:
    residuals: list[float] = []
    for row, prediction in zip(train_rows, train_predictions):
        residual = _evaluation_target_value(row, target) - _as_float(prediction["y_pred"])
        if math.isfinite(residual):
            residuals.append(residual)
    return residuals


def fit_train_residual_pool(
    train_rows: list[dict[str, Any]],
    train_predictions: list[dict[str, float | None]],
    *,
    target: str,
    shrinkage_strength: float,
    min_pool_count: int,
) -> ResidualPool:
    grouped: dict[tuple[str, ...], list[float]] = defaultdict(list)
    residuals: list[float] = []
    for row, prediction in zip(train_rows, train_predictions):
        residual = _evaluation_target_value(row, target) - _as_float(prediction["y_pred"])
        if not math.isfinite(residual):
            continue
        residuals.append(residual)
        for key in pooling_keys(row):
            grouped[key].append(residual)
    global_offset = _mean(residuals) if residuals else 0.0
    offsets: dict[tuple[str, ...], float] = {}
    counts: dict[tuple[str, ...], int] = {}
    for key, values in grouped.items():
        if len(values) < min_pool_count:
            continue
        shrinkage = len(values) / (len(values) + shrinkage_strength)
        offsets[key] = shrinkage * _mean(values)
        counts[key] = len(values)
    return ResidualPool(
        offsets=offsets,
        counts=counts,
        global_offset=global_offset,
        residual_count=len(residuals),
        raw_group_count=len(grouped),
    )


def pooling_keys(row: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    """Return stressor-family keys only; never include parameter_set or cell_id."""
    return (
        ("aging_mode", _group_value(row.get("aging_mode"))),
        ("temperature", _group_value(row.get("nominal_temperature_C"))),
        (
            "c_rate",
            _c_rate_bucket(row.get("nominal_charge_C_rate")),
            _c_rate_bucket(row.get("nominal_discharge_C_rate")),
        ),
        ("profile", _group_value(row.get("profile_label"))),
        ("voltage_window", _group_value(row.get("voltage_window_family"))),
    )


def pool_offset_for_row(row: dict[str, Any], pool: ResidualPool) -> tuple[float, bool]:
    offsets = [pool.offsets[key] for key in pooling_keys(row) if key in pool.offsets]
    if not offsets:
        return pool.global_offset, False
    return _mean(offsets), True


def replicate_interval_radius(
    train_rows: list[dict[str, Any]],
    residuals: list[float],
    target: str,
) -> float:
    abs_residual_radius = _quantile([abs(value) for value in residuals], 0.9)
    spread_values = replicate_spread_values(train_rows, target)
    replicate_radius = _quantile(spread_values, 0.9) / 2.0 if spread_values else 0.0
    return max(abs_residual_radius, replicate_radius)


def replicate_spread_values(train_rows: list[dict[str, Any]], target: str) -> list[float]:
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
    for row in train_rows:
        value = _evaluation_target_value(row, target)
        if math.isfinite(value):
            grouped[(int(row["parameter_set"]), int(row["checkup_k_next"]))].append(value)
    spreads: list[float] = []
    for values in grouped.values():
        if len(values) > 1:
            spreads.append(max(values) - min(values))
    return spreads


def hierarchical_comparison_rows(leaderboard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["target"]),
            str(row["split_name"]),
        ): row
        for row in leaderboard_rows
    }
    rows: list[dict[str, Any]] = []
    groups = sorted(
        {
            (str(row["run_scope"]), str(row["feature_group"]), str(row["target"]), str(row["split_name"]))
            for row in leaderboard_rows
        }
    )
    for run_scope, feature_group, target, split_name in groups:
        for comparison in POOLING_METHOD_COMPARISONS:
            candidate = by_key.get(
                (
                    run_scope,
                    comparison["candidate_model_level"],
                    feature_group,
                    target,
                    split_name,
                )
            )
            reference = by_key.get(
                (
                    run_scope,
                    comparison["reference_model_level"],
                    feature_group,
                    target,
                    split_name,
                )
            )
            if not candidate or not reference:
                continue
            reference_mae = float(reference["condition_mean_mae"])
            candidate_mae = float(candidate["condition_mean_mae"])
            rows.append(
                {
                    "comparison_id": comparison["comparison_id"],
                    "run_scope": run_scope,
                    "candidate_model_level": comparison["candidate_model_level"],
                    "reference_model_level": comparison["reference_model_level"],
                    "feature_group": feature_group,
                    "target": target,
                    "split_name": split_name,
                    "reference_condition_mean_mae": reference_mae,
                    "candidate_condition_mean_mae": candidate_mae,
                    "condition_mean_mae_gain": reference_mae - candidate_mae,
                    "relative_degradation": (
                        max(candidate_mae - reference_mae, 0.0) / reference_mae
                        if reference_mae > 0.0
                        else None
                    ),
                    "candidate_q10_q90_coverage": candidate.get("q10_q90_interval_coverage"),
                    "candidate_q10_q90_width": candidate.get("q10_q90_interval_width_mean"),
                }
            )
    return rows


def hierarchical_paired_condition_gain_rows(prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
        ): row
        for row in _condition_error_rows(prediction_rows)
    }
    rows: list[dict[str, Any]] = []
    base_keys = sorted(
        {
            (
                str(row["run_scope"]),
                str(row["feature_group"]),
                str(row["target"]),
                str(row["split_name"]),
                int(row["heldout_fold"]),
                int(row["parameter_set"]),
            )
            for row in _condition_error_rows(prediction_rows)
        }
    )
    for run_scope, feature_group, target, split_name, heldout_fold, parameter_set in base_keys:
        for comparison in POOLING_METHOD_COMPARISONS:
            candidate = by_key.get(
                (
                    run_scope,
                    comparison["candidate_model_level"],
                    feature_group,
                    target,
                    split_name,
                    heldout_fold,
                    parameter_set,
                )
            )
            reference = by_key.get(
                (
                    run_scope,
                    comparison["reference_model_level"],
                    feature_group,
                    target,
                    split_name,
                    heldout_fold,
                    parameter_set,
                )
            )
            if not candidate or not reference:
                continue
            rows.append(
                {
                    "comparison_id": comparison["comparison_id"],
                    "run_scope": run_scope,
                    "candidate_model_level": comparison["candidate_model_level"],
                    "reference_model_level": comparison["reference_model_level"],
                    "feature_group": feature_group,
                    "target": target,
                    "split_name": split_name,
                    "heldout_fold": heldout_fold,
                    "parameter_set": parameter_set,
                    "candidate_condition_mae": candidate["condition_mae"],
                    "reference_condition_mae": reference["condition_mae"],
                    "condition_mae_gain": float(reference["condition_mae"])
                    - float(candidate["condition_mae"]),
                    "row_count": candidate["row_count"],
                }
            )
    return rows


def _condition_error_rows(prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, int, int], list[float]] = defaultdict(list)
    for row in prediction_rows:
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        key = (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
        )
        grouped[key].append(abs(y_pred - y_true))
    rows: list[dict[str, Any]] = []
    for key, errors in sorted(grouped.items()):
        run_scope, model_level, feature_group, target, split_name, heldout_fold, parameter_set = key
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "parameter_set": parameter_set,
                "condition_mae": _mean(errors),
                "row_count": len(errors),
            }
        )
    return rows


def _paired_gain_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gains = [_as_float(row.get("condition_mae_gain")) for row in rows]
    gains = [gain for gain in gains if math.isfinite(gain)]
    if not gains:
        return {"condition_count": 0, "gain_mean": None, "gain_p05": None}
    return {
        "condition_count": len(gains),
        "gain_mean": _mean(gains),
        "gain_p05": _bootstrap_mean_p05(gains, resamples=1000, seed=59),
    }


def _bootstrap_mean_p05(values: list[float], *, resamples: int, seed: int) -> float:
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(resamples):
        sample = [rng.choice(values) for _ in values]
        means.append(_mean(sample))
    return _quantile(means, 0.05)


def hierarchical_claim_readiness(
    metrics: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    paired_gain_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    primary = [
        row
        for row in comparison_rows
        if row["run_scope"] == "primary"
        and row["comparison_id"] == "hgb_partial_pooling_vs_hgb"
        and row["feature_group"] == "F4_state_log_age_scalar"
        and row["target"] == PRIMARY_TARGET
    ]
    c_rate_row = next((row for row in primary if row["split_name"] == PRIMARY_SPLIT), None)
    outside = [row for row in primary if row["split_name"] != PRIMARY_SPLIT]
    max_outside_degradation = _max_optional(
        [
            _nullable_float(row.get("relative_degradation"))
            for row in outside
        ]
    )
    c_rate_gain = _nullable_float(c_rate_row.get("condition_mean_mae_gain")) if c_rate_row else None
    paired_summary = _paired_gain_summary(
        [
            row
            for row in paired_gain_rows
            if row["comparison_id"] == "hgb_partial_pooling_vs_hgb"
            and row["run_scope"] == "primary"
            and row["feature_group"] == "F4_state_log_age_scalar"
            and row["target"] == PRIMARY_TARGET
            and row["split_name"] == PRIMARY_SPLIT
        ]
    )
    paired_gain_p05 = paired_summary.get("gain_p05")
    c_rate_passes = c_rate_gain is not None and c_rate_gain > 0.0
    paired_passes = paired_gain_p05 is not None and paired_gain_p05 > 0.0
    outside_passes = max_outside_degradation is not None and max_outside_degradation <= 0.05
    partial_pooling_status = (
        "supported_for_diagnostics"
        if c_rate_passes and paired_passes and outside_passes
        else "diagnostic_only"
        if c_rate_passes and outside_passes
        else "not_supported"
    )

    interval_metrics = [
        metric
        for metric in metrics
        if metric["run_scope"] == "primary"
        and metric["model_level"] == "H5_replicate_variance_interval"
        and metric["feature_group"] == "F4_state_log_age_scalar"
        and metric["target"] == PRIMARY_TARGET
    ]
    interval_coverages = [
        _nullable_float(metric.get("q10_q90_interval_coverage")) for metric in interval_metrics
    ]
    interval_coverages = [value for value in interval_coverages if value is not None]
    min_interval_coverage = min(interval_coverages) if interval_coverages else None
    c_rate_interval = next(
        (
            _nullable_float(metric.get("q10_q90_interval_coverage"))
            for metric in interval_metrics
            if metric["split_name"] == PRIMARY_SPLIT
        ),
        None,
    )
    interval_status = (
        "supported_for_diagnostics"
        if min_interval_coverage is not None
        and min_interval_coverage >= 0.8
        and c_rate_interval is not None
        and c_rate_interval >= 0.8
        else "diagnostic_only"
        if interval_coverages
        else "blocked"
    )
    return {
        "l5_hierarchical_comparator": "supported_for_diagnostics",
        "hgb_partial_pooling_c_rate_delta": partial_pooling_status,
        "c_rate_delta_gain_vs_hgb_reference": c_rate_gain,
        "c_rate_delta_paired_gain_mean": paired_summary.get("gain_mean"),
        "c_rate_delta_paired_gain_p05": paired_gain_p05,
        "c_rate_delta_paired_conditions": paired_summary.get("condition_count"),
        "max_outside_c_rate_relative_degradation": max_outside_degradation,
        "outside_c_rate_non_degradation_passes_5pct": outside_passes,
        "replicate_variance_interval": interval_status,
        "min_primary_interval_coverage": min_interval_coverage,
        "c_rate_interval_coverage": c_rate_interval,
        "calibrated_uncertainty": "blocked",
        "hierarchical_c_rate_delta_diagnostic": partial_pooling_status,
        "global_robust_capacity_claim": "not_supported",
        "architecture_readiness": "blocked",
        "policy_ranking": "blocked",
        "claim_rule": (
            "A narrow hierarchical diagnostic claim requires H4/F4 to improve C-rate "
            "delta_capacity_Ah versus H3/F4, have paired condition bootstrap p05 above zero, "
            "and keep max outside-C-rate relative degradation at or below 5%. Intervals remain "
            "diagnostic unless grouped and C-rate coverage pass."
        ),
    }


def render_hierarchical_diagnostics(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    leaderboard_rows = _leaderboard_rows(metrics)
    comparison_rows = hierarchical_comparison_rows(leaderboard_rows)
    paired_gain_rows = list(report.get("paired_condition_gains", []))
    c_rate_rows = [
        row for row in comparison_rows if row["split_name"] == PRIMARY_SPLIT and row["run_scope"] == "primary"
    ]
    outside_rows = [
        row for row in comparison_rows if row["split_name"] != PRIMARY_SPLIT and row["run_scope"] == "primary"
    ]
    _write_csv(out_dir / "leaderboard.csv", leaderboard_rows)
    _write_csv(out_dir / "hierarchical_comparisons.csv", comparison_rows)
    _write_csv(out_dir / "paired_condition_gains.csv", paired_gain_rows)
    _write_csv(plots_dir / "c_rate_hierarchical_gain.csv", c_rate_rows)
    _write_csv(plots_dir / "outside_split_degradation.csv", outside_rows)
    _write_csv(
        plots_dir / "c_rate_paired_condition_gains.csv",
        [
            row for row in paired_gain_rows
            if row["split_name"] == PRIMARY_SPLIT and row["run_scope"] == "primary"
        ],
    )
    _write_claim_readiness_md(report, out_dir / "hierarchical_claim_readiness.md")


def _write_claim_readiness_md(report: dict[str, Any], path: Path) -> None:
    readiness = report["claim_readiness"]
    lines = [
        "# Hierarchical Replicate Capacity Claim Readiness",
        "",
        "| Claim area | Status / value |",
        "|---|---|",
        f"| L5 hierarchical comparator | {readiness['l5_hierarchical_comparator']} |",
        f"| HGB partial pooling C-rate delta | {readiness['hgb_partial_pooling_c_rate_delta']} |",
        f"| C-rate delta gain vs HGB reference | {_format_optional(readiness['c_rate_delta_gain_vs_hgb_reference'])} |",
        f"| C-rate paired gain mean | {_format_optional(readiness['c_rate_delta_paired_gain_mean'])} |",
        f"| C-rate paired gain p05 | {_format_optional(readiness['c_rate_delta_paired_gain_p05'])} |",
        f"| C-rate paired conditions | {readiness['c_rate_delta_paired_conditions']} |",
        f"| Max outside-C-rate relative degradation | {_format_optional(readiness['max_outside_c_rate_relative_degradation'])} |",
        f"| Replicate-variance interval | {readiness['replicate_variance_interval']} |",
        f"| Minimum primary interval coverage | {_format_optional(readiness['min_primary_interval_coverage'])} |",
        f"| C-rate interval coverage | {_format_optional(readiness['c_rate_interval_coverage'])} |",
        f"| Calibrated uncertainty | {readiness['calibrated_uncertainty']} |",
        f"| Hierarchical C-rate delta diagnostic | {readiness['hierarchical_c_rate_delta_diagnostic']} |",
        f"| Global robust capacity claim | {readiness['global_robust_capacity_claim']} |",
        f"| Architecture readiness | {readiness['architecture_readiness']} |",
        f"| Policy ranking | {readiness['policy_ranking']} |",
        "",
        "## Claim Rule",
        "",
        readiness["claim_rule"],
        "",
        "## Leakage Policy",
        "",
        report["leakage_policy"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _hierarchical_prediction_rows(
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
                "sensitivity_flagged_monotonicity": bool(row["sensitivity_flagged_monotonicity"]),
                "y_true": _evaluation_target_value(row, target),
                "y_pred": _as_float(prediction["y_pred"]),
                "y_pred_q10": _nullable_float(prediction.get("y_pred_q10")),
                "y_pred_q50": _nullable_float(prediction.get("y_pred_q50")),
                "y_pred_q90": _nullable_float(prediction.get("y_pred_q90")),
            }
        )
    return rows


def _leakage_audit_row(
    *,
    run_scope: str,
    split_name: str,
    heldout_fold: int,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    train_params = {int(row["parameter_set"]) for row in train_rows}
    test_params = {int(row["parameter_set"]) for row in test_rows}
    return {
        "run_scope": run_scope,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "train_parameter_sets": len(train_params),
        "test_parameter_sets": len(test_params),
        "parameter_set_overlap_count": len(train_params & test_params),
        "uses_parameter_set_random_effects": False,
        "uses_test_residuals": False,
        "status": "passed" if not (train_params & test_params) else "failed",
    }


def _base_metadata(base_model: str, row_count: int) -> dict[str, Any]:
    return {
        "base_model": base_model,
        "partial_pooling_enabled": False,
        "interval_enabled": False,
        "train_residual_count": 0,
        "pool_group_count": 0,
        "offset_applied_rows": 0,
        "global_fallback_rows": row_count,
        "interval_radius": None,
    }


def _quantile(values: list[float], quantile: float) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return 0.0
    if len(finite) == 1:
        return finite[0]
    position = (len(finite) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return finite[int(position)]
    lower_value = finite[lower]
    upper_value = finite[upper]
    return lower_value + (upper_value - lower_value) * (position - lower)


def _variant_seed(seed: int, *parts: object) -> int:
    payload = "|".join(str(part) for part in (seed, *parts))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1)


def _group_value(value: Any) -> str:
    if value is None:
        return "NA"
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:.6g}"
    text = str(value).strip()
    return text if text else "NA"


def _c_rate_bucket(value: Any) -> str:
    numeric = _as_float(value)
    if not math.isfinite(numeric):
        return "NA"
    if numeric < 0.75:
        return "lt_0p75C"
    if numeric < 1.25:
        return "approx_1C"
    if numeric < 1.55:
        return "approx_1p5C"
    return "ge_1p55C"


def _max_optional(values: list[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return max(finite) if finite else None


def _format_optional(value: Any) -> str:
    numeric = _nullable_float(value)
    return "NA" if numeric is None else f"{numeric:.6g}"


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)
