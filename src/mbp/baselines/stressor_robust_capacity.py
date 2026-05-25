"""Grouped stressor-robust capacity baselines."""

from __future__ import annotations

import copy
from collections import defaultdict
import csv
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
    DIRECT_TARGETS,
    DEFAULT_HGB_MAX_ITER,
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
from mbp.baselines.capacity import _mean
from mbp.baselines.capacity import _normalize_selection
from mbp.baselines.capacity import _point_prediction
from mbp.baselines.capacity import _prediction_to_evaluation_space
from mbp.baselines.capacity import _training_target_value

SCHEMA_VERSION = "gate51.stressor_robust_capacity.v1"
PARETO_SCHEMA_VERSION = "gate54.stressor_robust_pareto.v1"
ADAPTIVE_SCHEMA_VERSION = "gate55.stressor_robust_adaptive.v1"
ADAPTIVE_REPLICATION_SCHEMA_VERSION = "gate56.stressor_robust_adaptive_replication.v1"
ROBUST_MODEL_LEVELS = (
    "R0_reference_hgb50",
    "R1_condition_balanced_hgb",
    "R2_stressor_balanced_hgb",
    "R3_condition_bagged_hgb",
    "R4_worst_fold_selected_hgb",
)
DEFAULT_ROBUST_MODEL_LEVELS = ROBUST_MODEL_LEVELS
SELECTION_MODEL_LEVELS = (
    "R0_reference_hgb50",
    "R1_condition_balanced_hgb",
    "R2_stressor_balanced_hgb",
)
SELECTION_TIE_BREAK_ORDER = {
    "R2_stressor_balanced_hgb": 0,
    "R1_condition_balanced_hgb": 1,
    "R0_reference_hgb50": 2,
}
DEFAULT_ROBUST_FEATURE_GROUPS = ("F4_state_log_age_scalar", "F8_timestamp_weighted_stress")
PRIMARY_TARGET = "delta_capacity_Ah"
PRIMARY_SPLIT = "c_rate_holdout_fold"
DEFAULT_PARETO_WEIGHT_STRENGTHS = (0.25, 0.5, 0.75, 1.0)
DEFAULT_PARETO_BAG_COUNTS = (3, 5, 9)
NON_DEGRADATION_THRESHOLDS = (0.03, 0.05, 0.075, 0.10)
PREDECLARED_PARETO_MODEL_LEVEL = "R2_stressor_balanced_hgb"
PREDECLARED_PARETO_FEATURE_GROUP = "F8_timestamp_weighted_stress"
PREDECLARED_PARETO_WEIGHT_STRENGTH = 1.0
ADAPTIVE_MODEL_LEVEL = "R5_train_only_stressor_selected_hgb"
ADAPTIVE_MODEL_SETTING_ID = ADAPTIVE_MODEL_LEVEL
DEFAULT_ADAPTIVE_SELECTION_SPLITS = (
    "condition_fold",
    "temperature_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
    "c_rate_holdout_fold",
)
ADAPTIVE_NON_DEGRADATION_THRESHOLD = 0.05
DEFAULT_ADAPTIVE_REPLICATION_SEEDS = (42, 101, 202, 303, 404)
DEFAULT_ADAPTIVE_REPLICATION_POLICIES = ("conservative_guarded", "max_gain_guarded")


@dataclass(frozen=True)
class RobustPredictionResult:
    predictions: list[dict[str, float | None]]
    selected_variant: str | None = None
    internal_validation_metric: float | None = None
    internal_validation_condition_mean_mae: float | None = None
    selected_weight_strength: float | None = None
    selection_mean_gain: float | None = None
    selection_max_relative_degradation: float | None = None
    selection_rows: list[dict[str, Any]] | None = None


def run_stressor_robust_capacity(
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
    bag_count: int = 5,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
) -> dict[str, Any]:
    """Run non-neural robust HGB capacity baselines under grouped validation."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    if bag_count <= 0:
        raise ValueError("bag_count must be positive.")
    selected_models = _normalize_selection(
        model_levels,
        ROBUST_MODEL_LEVELS,
        "robust model level",
        default=DEFAULT_ROBUST_MODEL_LEVELS,
    )
    selected_feature_groups = _normalize_selection(
        feature_groups,
        DEFAULT_ROBUST_FEATURE_GROUPS,
        "feature group",
        default=DEFAULT_ROBUST_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, DIRECT_TARGETS, "target", default=DIRECT_TARGETS)
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError("Stress feature groups require --stress-features.")
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
    for run_scope, rows in (
        ("primary", subset_rows),
        ("sensitivity_excluding_monotonicity", sensitivity_rows),
    ):
        for split_name in selected_splits:
            for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                for model_level in selected_models:
                    for feature_group in selected_feature_groups:
                        for target in selected_targets:
                            result = predict_stressor_robust_capacity_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                                bag_count=bag_count,
                            )
                            metric = compute_metrics(
                                test_rows,
                                result.predictions,
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
                                    "selected_variant": result.selected_variant,
                                    "internal_validation_metric": result.internal_validation_metric,
                                    "internal_validation_condition_mean_mae": (
                                        result.internal_validation_condition_mean_mae
                                    ),
                                    "bag_count": bag_count,
                                }
                            )
                            metrics.append(metric)
                            predictions.extend(
                                _robust_prediction_rows(
                                    test_rows,
                                    result.predictions,
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
        "bag_count": bag_count,
        "selection_model_levels": list(SELECTION_MODEL_LEVELS),
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
        },
        "leakage_policy": "All weights, bagging samples, and model selection are computed from train rows only.",
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    diagnose_stressor_robustness(out_path, predictions_out_path, report_dir)
    return report


def run_stressor_robust_pareto(
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
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
    weight_strengths: list[float] | None = None,
    bag_counts: list[int] | None = None,
) -> dict[str, Any]:
    """Run a bounded stressor-robust Pareto diagnostic grid."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    selected_models = _normalize_selection(
        model_levels,
        ROBUST_MODEL_LEVELS,
        "robust model level",
        default=DEFAULT_ROBUST_MODEL_LEVELS,
    )
    selected_feature_groups = _normalize_selection(
        feature_groups,
        DEFAULT_ROBUST_FEATURE_GROUPS,
        "feature group",
        default=DEFAULT_ROBUST_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, DIRECT_TARGETS, "target", default=DIRECT_TARGETS)
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    selected_weight_strengths = _normalize_float_grid(
        weight_strengths,
        DEFAULT_PARETO_WEIGHT_STRENGTHS,
        "weight strength",
    )
    selected_bag_counts = _normalize_int_grid(bag_counts, DEFAULT_PARETO_BAG_COUNTS, "bag count")
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError("Stress feature groups require --stress-features.")
    _import_sklearn_stack()

    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    if not subset_rows:
        raise ValueError("Selected interval subset is empty.")
    settings = pareto_model_settings(
        selected_models,
        weight_strengths=selected_weight_strengths,
        bag_counts=selected_bag_counts,
    )

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(subset_rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for setting in settings:
                for feature_group in selected_feature_groups:
                    for target in selected_targets:
                        result = predict_stressor_robust_capacity_target(
                            model_level=str(setting["model_level"]),
                            feature_group=feature_group,
                            train_rows=train_rows,
                            test_rows=test_rows,
                            target=target,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            seed=seed,
                            hgb_max_iter=hgb_max_iter,
                            bag_count=int(setting["bag_count"]),
                            weight_strength=float(setting["weight_strength"]),
                        )
                        metric = compute_metrics(
                            test_rows,
                            result.predictions,
                            target=target,
                            subset_name=subset,
                            run_scope="primary",
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level=str(setting["model_level"]),
                            feature_group=feature_group,
                            train_rows=train_rows,
                        )
                        metric.update(
                            {
                                "schema_version": PARETO_SCHEMA_VERSION,
                                "model_setting_id": setting["model_setting_id"],
                                "weight_strength": setting["weight_strength"],
                                "bag_count": setting["bag_count"],
                                "selected_variant": result.selected_variant,
                                "internal_validation_metric": result.internal_validation_metric,
                                "internal_validation_condition_mean_mae": (
                                    result.internal_validation_condition_mean_mae
                                ),
                            }
                        )
                        metrics.append(metric)
                        predictions.extend(
                            _pareto_prediction_rows(
                                test_rows,
                                result.predictions,
                                subset_name=subset,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=str(setting["model_level"]),
                                feature_group=feature_group,
                                target=target,
                                model_setting_id=str(setting["model_setting_id"]),
                                weight_strength=float(setting["weight_strength"]),
                                bag_count=int(setting["bag_count"]),
                            )
                        )

    if not metrics:
        raise ValueError("No metrics were generated.")
    report_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(predictions).replace_schema_metadata(
            {b"schema_version": PARETO_SCHEMA_VERSION.encode()}
        ),
        predictions_out_path,
    )
    leaderboard = pareto_leaderboard_rows(metrics)
    paired = pareto_paired_condition_gain_rows(predictions)
    frontier = pareto_frontier_rows(leaderboard, paired)
    threshold_sensitivity = non_degradation_threshold_sensitivity_rows(frontier)
    claim = stressor_robust_pareto_claim_readiness(frontier)
    report = {
        "status": "passed",
        "schema_version": PARETO_SCHEMA_VERSION,
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
        "model_levels": selected_models,
        "feature_groups": selected_feature_groups,
        "targets": selected_targets,
        "split_views": selected_splits,
        "weight_strengths": selected_weight_strengths,
        "bag_counts": selected_bag_counts,
        "row_counts": {
            "full_interval_rows": len(all_rows),
            "selected_subset_rows": len(subset_rows),
            "settings": len(settings),
            "metrics": len(metrics),
            "predictions": len(predictions),
        },
        "claim_readiness": claim,
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_stressor_robust_pareto_artifacts(
        report,
        leaderboard,
        paired,
        frontier,
        threshold_sensitivity,
        claim,
        report_dir,
    )
    return report


def run_stressor_robust_adaptive(
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
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
    weight_strengths: list[float] | None = None,
    selection_split_views: list[str] | None = None,
    selection_policy: str = "max_gain_guarded",
) -> dict[str, Any]:
    """Run a train-only adaptive robust HGB selector under grouped validation."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    selected_feature_groups = _normalize_selection(
        feature_groups,
        DEFAULT_ROBUST_FEATURE_GROUPS,
        "feature group",
        default=DEFAULT_ROBUST_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, DIRECT_TARGETS, "target", default=[PRIMARY_TARGET])
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    selected_weight_strengths = _normalize_float_grid(
        weight_strengths,
        DEFAULT_PARETO_WEIGHT_STRENGTHS,
        "weight strength",
    )
    selected_selection_splits = _normalize_selection(
        selection_split_views,
        SPLIT_COLUMNS,
        "selection split view",
        default=DEFAULT_ADAPTIVE_SELECTION_SPLITS,
    )
    if selection_policy not in {"max_gain_guarded", "conservative_guarded"}:
        raise ValueError("selection_policy must be 'max_gain_guarded' or 'conservative_guarded'.")
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError("Stress feature groups require --stress-features.")
    _import_sklearn_stack()

    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    if not subset_rows:
        raise ValueError("Selected interval subset is empty.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(subset_rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            outer_train_sets = {int(row["parameter_set"]) for row in train_rows}
            outer_test_sets = {int(row["parameter_set"]) for row in test_rows}
            outer_overlap_count = len(outer_train_sets & outer_test_sets)
            for feature_group in selected_feature_groups:
                for target in selected_targets:
                    reference_predictions = predict_stressor_robust_capacity_target(
                        model_level="R0_reference_hgb50",
                        feature_group=feature_group,
                        train_rows=train_rows,
                        test_rows=test_rows,
                        target=target,
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                        seed=seed,
                        hgb_max_iter=hgb_max_iter,
                        bag_count=1,
                    )
                    reference_metric = compute_metrics(
                        test_rows,
                        reference_predictions.predictions,
                        target=target,
                        subset_name=subset,
                        run_scope="primary",
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                        model_level="R0_reference_hgb50",
                        feature_group=feature_group,
                        train_rows=train_rows,
                    )
                    reference_metric.update(
                        {
                            "schema_version": ADAPTIVE_SCHEMA_VERSION,
                            "model_setting_id": "R0_reference_hgb50",
                            "weight_strength": 0.0,
                            "selected_variant": None,
                            "selected_weight_strength": None,
                            "selection_mean_gain": None,
                            "selection_max_relative_degradation": None,
                            "internal_validation_metric": None,
                            "internal_validation_condition_mean_mae": None,
                        }
                    )
                    metrics.append(reference_metric)
                    predictions.extend(
                        _adaptive_prediction_rows(
                            test_rows,
                            reference_predictions.predictions,
                            subset_name=subset,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level="R0_reference_hgb50",
                            feature_group=feature_group,
                            target=target,
                            model_setting_id="R0_reference_hgb50",
                            selected_weight_strength=None,
                            selection_mean_gain=None,
                            selection_max_relative_degradation=None,
                        )
                    )

                    adaptive_result = predict_adaptive_stressor_robust_capacity_target(
                        feature_group=feature_group,
                        train_rows=train_rows,
                        test_rows=test_rows,
                        target=target,
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                        seed=seed,
                        hgb_max_iter=hgb_max_iter,
                        weight_strengths=selected_weight_strengths,
                        selection_split_views=selected_selection_splits,
                        selection_policy=selection_policy,
                    )
                    adaptive_metric = compute_metrics(
                        test_rows,
                        adaptive_result.predictions,
                        target=target,
                        subset_name=subset,
                        run_scope="primary",
                        split_name=split_name,
                        heldout_fold=heldout_fold,
                        model_level=ADAPTIVE_MODEL_LEVEL,
                        feature_group=feature_group,
                        train_rows=train_rows,
                    )
                    adaptive_metric.update(
                        {
                            "schema_version": ADAPTIVE_SCHEMA_VERSION,
                            "model_setting_id": ADAPTIVE_MODEL_SETTING_ID,
                            "weight_strength": adaptive_result.selected_weight_strength,
                            "selected_variant": adaptive_result.selected_variant,
                            "selected_weight_strength": adaptive_result.selected_weight_strength,
                            "selection_mean_gain": adaptive_result.selection_mean_gain,
                            "selection_max_relative_degradation": adaptive_result.selection_max_relative_degradation,
                            "internal_validation_metric": adaptive_result.internal_validation_metric,
                            "internal_validation_condition_mean_mae": (
                                adaptive_result.internal_validation_condition_mean_mae
                            ),
                        }
                    )
                    metrics.append(adaptive_metric)
                    predictions.extend(
                        _adaptive_prediction_rows(
                            test_rows,
                            adaptive_result.predictions,
                            subset_name=subset,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level=ADAPTIVE_MODEL_LEVEL,
                            feature_group=feature_group,
                            target=target,
                            model_setting_id=ADAPTIVE_MODEL_SETTING_ID,
                            selected_weight_strength=adaptive_result.selected_weight_strength,
                            selection_mean_gain=adaptive_result.selection_mean_gain,
                            selection_max_relative_degradation=(
                                adaptive_result.selection_max_relative_degradation
                            ),
                        )
                    )
                    for row in adaptive_result.selection_rows or []:
                        selection_rows.append(
                            {
                                **row,
                                "outer_split_name": split_name,
                                "outer_heldout_fold": heldout_fold,
                                "outer_train_condition_count": len(outer_train_sets),
                                "outer_test_condition_count": len(outer_test_sets),
                                "outer_train_test_overlap_count": outer_overlap_count,
                                "target": target,
                                "feature_group": feature_group,
                            }
                        )

    if not metrics:
        raise ValueError("No metrics were generated.")
    report_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(predictions).replace_schema_metadata(
            {b"schema_version": ADAPTIVE_SCHEMA_VERSION.encode()}
        ),
        predictions_out_path,
    )
    leaderboard = pareto_leaderboard_rows(metrics)
    paired = pareto_paired_condition_gain_rows(predictions)
    frontier = pareto_frontier_rows(leaderboard, paired)
    claim = stressor_robust_adaptive_claim_readiness(frontier)
    report = {
        "status": "passed",
        "schema_version": ADAPTIVE_SCHEMA_VERSION,
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
        "feature_groups": selected_feature_groups,
        "targets": selected_targets,
        "split_views": selected_splits,
        "weight_strengths": selected_weight_strengths,
        "selection_split_views": selected_selection_splits,
        "selection_policy": selection_policy,
        "row_counts": {
            "full_interval_rows": len(all_rows),
            "selected_subset_rows": len(subset_rows),
            "metrics": len(metrics),
            "predictions": len(predictions),
            "selection_rows": len(selection_rows),
        },
        "leakage_policy": (
            "Adaptive weights are selected only from inner grouped validation splits "
            "inside each outer training fold. Held-out outer test rows are never used "
            "to choose the weight strength."
        ),
        "claim_readiness": claim,
        "metrics": metrics,
        "selection_rows": selection_rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_stressor_robust_adaptive_artifacts(
        report,
        leaderboard,
        paired,
        frontier,
        selection_rows,
        claim,
        report_dir,
    )
    return report


def replicate_stressor_robust_adaptive(
    interval_table_path: Path,
    interval_subsets_path: Path,
    out_dir: Path,
    *,
    stress_features_path: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seeds: list[int] | None = None,
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
    weight_strengths: list[float] | None = None,
    selection_split_views: list[str] | None = None,
    selection_policies: list[str] | None = None,
    recompute_seeds: bool = False,
) -> dict[str, Any]:
    """Replicate adaptive stressor-robust selection across deterministic seeds."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    selected_seeds = list(DEFAULT_ADAPTIVE_REPLICATION_SEEDS if seeds is None else seeds)
    if not selected_seeds:
        raise ValueError("At least one replication seed is required.")
    selected_policies = _normalize_selection(
        selection_policies,
        list(DEFAULT_ADAPTIVE_REPLICATION_POLICIES),
        "selection policy",
        default=list(DEFAULT_ADAPTIVE_REPLICATION_POLICIES),
    )
    for policy in selected_policies:
        if policy not in DEFAULT_ADAPTIVE_REPLICATION_POLICIES:
            raise ValueError(f"Unknown selection policy: {policy}")
    selected_feature_groups = _normalize_selection(
        feature_groups,
        DEFAULT_ROBUST_FEATURE_GROUPS,
        "feature group",
        default=DEFAULT_ROBUST_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, DIRECT_TARGETS, "target", default=[PRIMARY_TARGET])
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    selected_weight_strengths = _normalize_float_grid(
        weight_strengths,
        DEFAULT_PARETO_WEIGHT_STRENGTHS,
        "weight strength",
    )
    selected_selection_splits = _normalize_selection(
        selection_split_views,
        SPLIT_COLUMNS,
        "selection split view",
        default=DEFAULT_ADAPTIVE_SELECTION_SPLITS,
    )
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError("Stress feature groups require --stress-features.")
    _import_sklearn_stack()
    effective_fit_seeds = selected_seeds if recompute_seeds else [selected_seeds[0]]
    seed_reuse_mode = "recomputed_each_seed" if recompute_seeds else "deterministic_hgb_no_bagging_reuse"

    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    if not subset_rows:
        raise ValueError("Selected interval subset is empty.")

    policy_metrics: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    policy_predictions: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    policy_selection_rows: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    out_dir.mkdir(parents=True, exist_ok=True)

    for seed in effective_fit_seeds:
        for split_name in selected_splits:
            for heldout_fold, train_rows, test_rows in iter_split_instances(subset_rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                outer_train_sets = {int(row["parameter_set"]) for row in train_rows}
                outer_test_sets = {int(row["parameter_set"]) for row in test_rows}
                outer_overlap_count = len(outer_train_sets & outer_test_sets)
                for feature_group in selected_feature_groups:
                    for target in selected_targets:
                        reference_result = predict_stressor_robust_capacity_target(
                            model_level="R0_reference_hgb50",
                            feature_group=feature_group,
                            train_rows=train_rows,
                            test_rows=test_rows,
                            target=target,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            seed=int(seed),
                            hgb_max_iter=hgb_max_iter,
                            bag_count=1,
                        )
                        reference_metric = compute_metrics(
                            test_rows,
                            reference_result.predictions,
                            target=target,
                            subset_name=subset,
                            run_scope="primary",
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level="R0_reference_hgb50",
                            feature_group=feature_group,
                            train_rows=train_rows,
                        )
                        reference_metric.update(
                            {
                                "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
                                "model_setting_id": "R0_reference_hgb50",
                                "weight_strength": 0.0,
                                "selected_variant": None,
                                "selected_weight_strength": None,
                                "selection_mean_gain": None,
                                "selection_max_relative_degradation": None,
                                "internal_validation_metric": None,
                                "internal_validation_condition_mean_mae": None,
                            }
                        )
                        reference_rows = _adaptive_prediction_rows(
                            test_rows,
                            reference_result.predictions,
                            subset_name=subset,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level="R0_reference_hgb50",
                            feature_group=feature_group,
                            target=target,
                            model_setting_id="R0_reference_hgb50",
                            selected_weight_strength=None,
                            selection_mean_gain=None,
                            selection_max_relative_degradation=None,
                        )
                        raw_selection_rows = raw_adaptive_weight_selection_rows(
                            train_rows=train_rows,
                            feature_group=feature_group,
                            target=target,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            seed=int(seed),
                            hgb_max_iter=hgb_max_iter,
                            weight_strengths=selected_weight_strengths,
                            selection_split_views=selected_selection_splits,
                        )
                        for policy in selected_policies:
                            key = (int(seed), policy)
                            policy_metrics[key].append(dict(reference_metric))
                            policy_predictions[key].extend(reference_rows)
                            selection_rows = aggregate_adaptive_weight_selection_rows(
                                raw_selection_rows,
                                selection_policy=policy,
                            )
                            selected = select_adaptive_weight_strength(selection_rows, policy=policy)
                            selected_strength = float(selected["weight_strength"])
                            adaptive_predictions = _fit_predict_hgb_variant(
                                "R2_stressor_balanced_hgb",
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                seed=int(seed),
                                hgb_max_iter=hgb_max_iter,
                                bag_count=1,
                                weight_strength=selected_strength,
                            )
                            adaptive_metric = compute_metrics(
                                test_rows,
                                adaptive_predictions,
                                target=target,
                                subset_name=subset,
                                run_scope="primary",
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=ADAPTIVE_MODEL_LEVEL,
                                feature_group=feature_group,
                                train_rows=train_rows,
                            )
                            adaptive_metric.update(
                                {
                                    "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
                                    "model_setting_id": ADAPTIVE_MODEL_SETTING_ID,
                                    "weight_strength": selected_strength,
                                    "selected_variant": f"R2_stressor_balanced_hgb__w{_slug_float(selected_strength)}",
                                    "selected_weight_strength": selected_strength,
                                    "selection_mean_gain": _as_float(selected["mean_gain_vs_r0"]),
                                    "selection_max_relative_degradation": _as_float(
                                        selected["max_relative_degradation"]
                                    ),
                                    "internal_validation_metric": _as_float(selected["selection_score"]),
                                    "internal_validation_condition_mean_mae": _as_float(
                                        selected["mean_candidate_condition_mae"]
                                    ),
                                }
                            )
                            policy_metrics[key].append(adaptive_metric)
                            policy_predictions[key].extend(
                                _adaptive_prediction_rows(
                                    test_rows,
                                    adaptive_predictions,
                                    subset_name=subset,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=ADAPTIVE_MODEL_LEVEL,
                                    feature_group=feature_group,
                                    target=target,
                                    model_setting_id=ADAPTIVE_MODEL_SETTING_ID,
                                    selected_weight_strength=selected_strength,
                                    selection_mean_gain=_as_float(selected["mean_gain_vs_r0"]),
                                    selection_max_relative_degradation=_as_float(
                                        selected["max_relative_degradation"]
                                    ),
                                )
                            )
                            for row in selection_rows:
                                policy_selection_rows[key].append(
                                    {
                                        **row,
                                        "seed": int(seed),
                                        "outer_split_name": split_name,
                                        "outer_heldout_fold": heldout_fold,
                                        "outer_train_condition_count": len(outer_train_sets),
                                        "outer_test_condition_count": len(outer_test_sets),
                                        "outer_train_test_overlap_count": outer_overlap_count,
                                        "target": target,
                                        "feature_group": feature_group,
                                    }
                                )

    computed_run_reports = []
    for (seed, policy), metrics in sorted(policy_metrics.items()):
        predictions = policy_predictions[(seed, policy)]
        selection_rows = policy_selection_rows[(seed, policy)]
        leaderboard = pareto_leaderboard_rows(metrics)
        paired = pareto_paired_condition_gain_rows(predictions)
        frontier = pareto_frontier_rows(leaderboard, paired)
        claim = stressor_robust_adaptive_claim_readiness(frontier)
        run_report = {
            "status": "passed",
            "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
            "seed": seed,
            "computed_seed": seed,
            "seed_reuse_mode": "recomputed_each_seed",
            "selection_policy": policy,
            "row_counts": {
                "full_interval_rows": len(all_rows),
                "selected_subset_rows": len(subset_rows),
                "metrics": len(metrics),
                "predictions": len(predictions),
                "selection_rows": len(selection_rows),
            },
            "claim_readiness": claim,
            "selection_rows": selection_rows,
        }
        computed_run_reports.append(run_report)

    run_reports = _expand_adaptive_replication_seed_reports(
        computed_run_reports,
        requested_seeds=selected_seeds,
        selection_policies=selected_policies,
        seed_reuse_mode=seed_reuse_mode,
    )
    replication_rows = [_adaptive_replication_row(report) for report in run_reports]

    leakage_audit = adaptive_replication_leakage_audit(run_reports)
    policy_rows = adaptive_replication_policy_rows(replication_rows)
    degradation_rows = adaptive_replication_degradation_rows(replication_rows)
    claim = adaptive_replication_claim_readiness(
        replication_rows,
        expected_seeds=selected_seeds,
        primary_policy="conservative_guarded",
        leakage_audit=leakage_audit,
    )
    report = {
        "status": "passed",
        "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "stress_features": str(stress_features_path) if stress_features_path else None,
        },
        "outputs": {
            "out_dir": str(out_dir),
            "summary": str(out_dir / "replication_summary.json"),
        },
        "subset": subset,
        "seeds": selected_seeds,
        "effective_fit_seeds": effective_fit_seeds,
        "seed_reuse_mode": seed_reuse_mode,
        "recompute_seeds": recompute_seeds,
        "selection_policies": selected_policies,
        "hgb_max_iter": hgb_max_iter,
        "feature_groups": selected_feature_groups,
        "targets": selected_targets,
        "split_views": selected_splits,
        "weight_strengths": selected_weight_strengths,
        "selection_split_views": selected_selection_splits,
        "row_counts": {
            "replication_rows": len(replication_rows),
            "policy_rows": len(policy_rows),
            "degradation_rows": len(degradation_rows),
            "run_reports": len(run_reports),
        },
        "leakage_audit": leakage_audit,
        "claim_readiness": claim,
        "replication_rows": replication_rows,
        "policy_rows": policy_rows,
        "degradation_rows": degradation_rows,
    }
    render_stressor_robust_adaptive_replication_artifacts(
        report,
        replication_rows,
        policy_rows,
        degradation_rows,
        claim,
        out_dir,
    )
    return report


def predict_stressor_robust_capacity_target(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    bag_count: int,
    weight_strength: float = 1.0,
) -> RobustPredictionResult:
    if model_level not in ROBUST_MODEL_LEVELS:
        raise ValueError(f"Unknown robust model level: {model_level}")
    if model_level == "R4_worst_fold_selected_hgb":
        return _worst_fold_selected_predictions(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
            split_name=split_name,
            heldout_fold=heldout_fold,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            bag_count=bag_count,
            weight_strength=weight_strength,
        )
    predictions = _fit_predict_hgb_variant(
        model_level,
        feature_group=feature_group,
        train_rows=train_rows,
        test_rows=test_rows,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        bag_count=bag_count,
        weight_strength=weight_strength,
    )
    return RobustPredictionResult(predictions=predictions)


def predict_adaptive_stressor_robust_capacity_target(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    weight_strengths: list[float],
    selection_split_views: list[str],
    selection_policy: str = "max_gain_guarded",
) -> RobustPredictionResult:
    """Select R2 weight strength using train-only inner grouped validation."""
    selection_rows = adaptive_weight_selection_rows(
        train_rows=train_rows,
        feature_group=feature_group,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        weight_strengths=weight_strengths,
        selection_split_views=selection_split_views,
        selection_policy=selection_policy,
    )
    selected = select_adaptive_weight_strength(selection_rows, policy=selection_policy)
    selected_strength = float(selected["weight_strength"])
    predictions = _fit_predict_hgb_variant(
        "R2_stressor_balanced_hgb",
        feature_group=feature_group,
        train_rows=train_rows,
        test_rows=test_rows,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        bag_count=1,
        weight_strength=selected_strength,
    )
    return RobustPredictionResult(
        predictions=predictions,
        selected_variant=f"R2_stressor_balanced_hgb__w{_slug_float(selected_strength)}",
        selected_weight_strength=selected_strength,
        selection_mean_gain=_as_float(selected["mean_gain_vs_r0"]),
        selection_max_relative_degradation=_as_float(selected["max_relative_degradation"]),
        internal_validation_metric=_as_float(selected["selection_score"]),
        internal_validation_condition_mean_mae=_as_float(selected["mean_candidate_condition_mae"]),
        selection_rows=selection_rows,
    )


def adaptive_weight_selection_rows(
    *,
    train_rows: list[dict[str, Any]],
    feature_group: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    weight_strengths: list[float],
    selection_split_views: list[str],
    selection_policy: str = "max_gain_guarded",
) -> list[dict[str, Any]]:
    """Score weight strengths on inner grouped splits from outer train rows only."""
    raw_rows = raw_adaptive_weight_selection_rows(
        train_rows=train_rows,
        feature_group=feature_group,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        weight_strengths=weight_strengths,
        selection_split_views=selection_split_views,
    )
    return aggregate_adaptive_weight_selection_rows(raw_rows, selection_policy=selection_policy)


def raw_adaptive_weight_selection_rows(
    *,
    train_rows: list[dict[str, Any]],
    feature_group: str,
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    weight_strengths: list[float],
    selection_split_views: list[str],
) -> list[dict[str, Any]]:
    """Return unaggregated inner grouped validation rows for adaptive weight selection."""
    raw_rows: list[dict[str, Any]] = []
    for selection_split in selection_split_views:
        try:
            inner_instances = iter_split_instances(train_rows, selection_split)
        except ValueError:
            continue
        for inner_heldout_fold, inner_train, inner_validation in inner_instances:
            if not inner_train or not inner_validation:
                continue
            assert_no_parameter_set_leakage(
                inner_train,
                inner_validation,
                f"adaptive_{selection_split}",
                inner_heldout_fold,
            )
            inner_train_sets = {int(row["parameter_set"]) for row in inner_train}
            inner_validation_sets = {int(row["parameter_set"]) for row in inner_validation}
            reference_predictions = _fit_predict_hgb_variant(
                "R0_reference_hgb50",
                feature_group=feature_group,
                train_rows=inner_train,
                test_rows=inner_validation,
                target=target,
                split_name=selection_split,
                heldout_fold=inner_heldout_fold,
                seed=seed,
                hgb_max_iter=hgb_max_iter,
                bag_count=1,
                weight_strength=0.0,
            )
            reference_metric = compute_metrics(
                inner_validation,
                reference_predictions,
                target=target,
                subset_name="adaptive_inner_validation",
                run_scope="adaptive_inner_validation",
                split_name=selection_split,
                heldout_fold=inner_heldout_fold,
                model_level="R0_reference_hgb50",
                feature_group=feature_group,
                train_rows=inner_train,
            )
            reference_mae = float(reference_metric["condition_mean_mae"])
            for strength in weight_strengths:
                candidate_predictions = _fit_predict_hgb_variant(
                    "R2_stressor_balanced_hgb",
                    feature_group=feature_group,
                    train_rows=inner_train,
                    test_rows=inner_validation,
                    target=target,
                    split_name=selection_split,
                    heldout_fold=inner_heldout_fold,
                    seed=seed,
                    hgb_max_iter=hgb_max_iter,
                    bag_count=1,
                    weight_strength=float(strength),
                )
                candidate_metric = compute_metrics(
                    inner_validation,
                    candidate_predictions,
                    target=target,
                    subset_name="adaptive_inner_validation",
                    run_scope="adaptive_inner_validation",
                    split_name=selection_split,
                    heldout_fold=inner_heldout_fold,
                    model_level="R2_stressor_balanced_hgb",
                    feature_group=feature_group,
                    train_rows=inner_train,
                )
                candidate_mae = float(candidate_metric["condition_mean_mae"])
                raw_rows.append(
                    {
                        "schema_version": ADAPTIVE_SCHEMA_VERSION,
                        "outer_split_name_for_seed": split_name,
                        "outer_heldout_fold_for_seed": heldout_fold,
                        "selection_split_name": selection_split,
                        "selection_heldout_fold": inner_heldout_fold,
                        "inner_train_condition_count": len(inner_train_sets),
                        "inner_validation_condition_count": len(inner_validation_sets),
                        "inner_train_validation_overlap_count": len(
                            inner_train_sets & inner_validation_sets
                        ),
                        "weight_strength": float(strength),
                        "reference_condition_mean_mae": reference_mae,
                        "candidate_condition_mean_mae": candidate_mae,
                        "condition_mean_mae_gain": reference_mae - candidate_mae,
                        "relative_degradation": (
                            (candidate_mae - reference_mae) / reference_mae if reference_mae > 0 else None
                        ),
                    }
                )
    return raw_rows


def aggregate_adaptive_weight_selection_rows(
    rows: list[dict[str, Any]],
    *,
    selection_policy: str = "max_gain_guarded",
) -> list[dict[str, Any]]:
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[float(row["weight_strength"])].append(row)
    output = []
    for strength, group in sorted(grouped.items()):
        relative_values = [
            _as_float(row["relative_degradation"])
            for row in group
            if row.get("relative_degradation") is not None
            and math.isfinite(_as_float(row["relative_degradation"]))
        ]
        mean_gain = _mean([float(row["condition_mean_mae_gain"]) for row in group])
        mean_candidate = _mean([float(row["candidate_condition_mean_mae"]) for row in group])
        max_degradation = max(relative_values) if relative_values else None
        max_inner_overlap = max(
            int(row.get("inner_train_validation_overlap_count", 0)) for row in group
        )
        passes_guardrail = (
            max_degradation is not None
            and max_degradation <= ADAPTIVE_NON_DEGRADATION_THRESHOLD
            and mean_gain > 0
        )
        output.append(
            {
                "schema_version": ADAPTIVE_SCHEMA_VERSION,
                "model_level": "R2_stressor_balanced_hgb",
                "model_setting_id": f"R2_stressor_balanced_hgb__w{_slug_float(strength)}",
                "weight_strength": strength,
                "inner_validation_rows": len(group),
                "mean_gain_vs_r0": mean_gain,
                "mean_candidate_condition_mae": mean_candidate,
                "max_relative_degradation": max_degradation,
                "max_inner_train_validation_overlap_count": max_inner_overlap,
                "passes_inner_guardrail": passes_guardrail,
                "selection_policy": selection_policy,
                "selection_score": _adaptive_selection_score(mean_gain, max_degradation),
                "selected_by_train_only_rule": False,
            }
        )
    if not output:
        raise ValueError("Adaptive selection produced no inner-validation rows.")
    selected = select_adaptive_weight_strength(output, policy=selection_policy)
    for row in output:
        row["selected_by_train_only_rule"] = row["weight_strength"] == selected["weight_strength"]
    return output


def select_adaptive_weight_strength(rows: list[dict[str, Any]], *, policy: str = "max_gain_guarded") -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot select an adaptive weight from no rows.")
    if policy not in {"max_gain_guarded", "conservative_guarded"}:
        raise ValueError("policy must be 'max_gain_guarded' or 'conservative_guarded'.")
    guarded = [row for row in rows if bool(row.get("passes_inner_guardrail"))]
    if policy == "conservative_guarded":
        if guarded:
            return min(
                guarded,
                key=lambda row: (
                    _as_float(row["weight_strength"]),
                    _finite_or(row.get("max_relative_degradation"), math.inf),
                    -_finite_or(row.get("mean_gain_vs_r0"), -math.inf),
                ),
            )
        return min(
            rows,
            key=lambda row: (
                _as_float(row["weight_strength"]),
                _finite_or(row.get("max_relative_degradation"), math.inf),
                -_finite_or(row.get("mean_gain_vs_r0"), -math.inf),
            ),
        )
    if guarded:
        return max(
            guarded,
            key=lambda row: (
                _finite_or(row.get("mean_gain_vs_r0"), -math.inf),
                -_finite_or(row.get("max_relative_degradation"), math.inf),
                -_as_float(row["weight_strength"]),
            ),
        )
    return min(
        rows,
        key=lambda row: (
            _finite_or(row.get("max_relative_degradation"), math.inf),
            -_finite_or(row.get("mean_gain_vs_r0"), -math.inf),
            _as_float(row["weight_strength"]),
        ),
    )


def _adaptive_selection_score(mean_gain: float, max_degradation: float | None) -> float:
    degradation = _finite_or(max_degradation, math.inf)
    excess = max(0.0, degradation - ADAPTIVE_NON_DEGRADATION_THRESHOLD)
    return mean_gain - excess


def condition_balanced_weights(rows: list[dict[str, Any]], *, strength: float = 1.0) -> list[float]:
    counts = defaultdict(int)
    for row in rows:
        counts[int(row["parameter_set"])] += 1
    raw = [1.0 / counts[int(row["parameter_set"])] for row in rows]
    return _blend_weights(_normalize_weights(raw), strength=strength)


def stressor_balanced_weights(rows: list[dict[str, Any]], split_name: str, *, strength: float = 1.0) -> list[float]:
    counts = defaultdict(int)
    for row in rows:
        counts[_stressor_key(row, split_name)] += 1
    raw = [1.0 / counts[_stressor_key(row, split_name)] for row in rows]
    return _blend_weights(_normalize_weights(raw), strength=strength)


def _fit_predict_hgb_variant(
    model_level: str,
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    bag_count: int,
    weight_strength: float = 1.0,
) -> list[dict[str, float | None]]:
    if model_level == "R3_condition_bagged_hgb":
        return _condition_bagged_predictions(
            feature_group=feature_group,
            train_rows=train_rows,
            test_rows=test_rows,
            target=target,
            split_name=split_name,
            heldout_fold=heldout_fold,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            bag_count=bag_count,
        )
    sample_weight = None
    if model_level == "R1_condition_balanced_hgb":
        sample_weight = condition_balanced_weights(train_rows, strength=weight_strength)
    elif model_level == "R2_stressor_balanced_hgb":
        sample_weight = stressor_balanced_weights(train_rows, split_name, strength=weight_strength)
    elif model_level != "R0_reference_hgb50":
        raise ValueError(f"Unsupported direct robust HGB variant: {model_level}")
    return _fit_hgb_predictions(
        feature_group=feature_group,
        train_rows=train_rows,
        test_rows=test_rows,
        target=target,
        seed=_variant_seed(seed, model_level, feature_group, target, split_name, heldout_fold),
        hgb_max_iter=hgb_max_iter,
        sample_weight=sample_weight,
    )


def _fit_hgb_predictions(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int,
    sample_weight: list[float] | None = None,
    encoder: FeatureEncoder | None = None,
) -> list[dict[str, float | None]]:
    np, _, HistGradientBoostingRegressor = _import_sklearn_stack()
    fitted_encoder = encoder or FeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(fitted_encoder.transform(train_rows), dtype=float)
    x_test = np.asarray(fitted_encoder.transform(test_rows), dtype=float)
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")
    model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
    if sample_weight is None:
        model.fit(x_train, y_train)
    else:
        model.fit(x_train, y_train, sample_weight=np.asarray(sample_weight, dtype=float))
    values = model.predict(x_test)
    return [
        _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
        for row, value in zip(test_rows, values)
    ]


def _condition_bagged_predictions(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    bag_count: int,
) -> list[dict[str, float | None]]:
    condition_rows = _rows_by_parameter_set(train_rows)
    parameter_sets = sorted(condition_rows)
    if not parameter_sets:
        raise ValueError("Cannot bag over zero parameter-set conditions.")
    encoder = FeatureEncoder.fit(train_rows, feature_group)
    rows_per_condition_draw = max(1, math.ceil(len(train_rows) / len(parameter_sets)))
    bag_values: list[list[float]] = []
    for bag_idx in range(bag_count):
        rng = random.Random(
            _variant_seed(seed, "R3_condition_bagged_hgb", feature_group, target, split_name, heldout_fold, bag_idx)
        )
        sampled_rows: list[dict[str, Any]] = []
        for _ in parameter_sets:
            sampled_rows.extend(
                _sample_condition_rows(
                    condition_rows[rng.choice(parameter_sets)],
                    rows_per_condition_draw,
                    rng,
                )
            )
        predictions = _fit_hgb_predictions(
            feature_group=feature_group,
            train_rows=sampled_rows,
            test_rows=test_rows,
            target=target,
            seed=_variant_seed(seed, "bag_model", feature_group, target, split_name, heldout_fold, bag_idx),
            hgb_max_iter=hgb_max_iter,
            encoder=encoder,
        )
        bag_values.append([_as_float(prediction["y_pred"]) for prediction in predictions])
    averaged = [
        _point_prediction(_mean([bag[idx] for bag in bag_values]))
        for idx in range(len(test_rows))
    ]
    return averaged


def _sample_condition_rows(
    rows: list[dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("Cannot sample an empty condition.")
    return [rows[rng.randrange(len(rows))] for _ in range(count)]


def _worst_fold_selected_predictions(
    *,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    split_name: str,
    heldout_fold: int,
    seed: int,
    hgb_max_iter: int,
    bag_count: int,
    weight_strength: float = 1.0,
) -> RobustPredictionResult:
    fit_rows, validation_rows = _internal_condition_validation_split(
        train_rows,
        seed=_variant_seed(seed, "internal_validation", feature_group, target, split_name, heldout_fold),
    )
    scored: list[tuple[float, float, str]] = []
    for candidate in SELECTION_MODEL_LEVELS:
        predictions = _fit_predict_hgb_variant(
            candidate,
            feature_group=feature_group,
            train_rows=fit_rows,
            test_rows=validation_rows,
            target=target,
            split_name=split_name,
            heldout_fold=heldout_fold,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            bag_count=bag_count,
            weight_strength=weight_strength,
        )
        metric = compute_metrics(
            validation_rows,
            predictions,
            target=target,
            subset_name="internal_validation",
            run_scope="internal_validation",
            split_name=split_name,
            heldout_fold=heldout_fold,
            model_level=candidate,
            feature_group=feature_group,
            train_rows=fit_rows,
        )
        scored.append((float(metric["worst_condition_mae"]), float(metric["condition_mean_mae"]), candidate))
    best_worst, best_mean, selected = min(
        scored,
        key=lambda item: (item[0], item[1], SELECTION_TIE_BREAK_ORDER[item[2]]),
    )
    predictions = _fit_predict_hgb_variant(
        selected,
        feature_group=feature_group,
        train_rows=train_rows,
        test_rows=test_rows,
        target=target,
        split_name=split_name,
        heldout_fold=heldout_fold,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        bag_count=bag_count,
        weight_strength=weight_strength,
    )
    return RobustPredictionResult(
        predictions=predictions,
        selected_variant=selected,
        internal_validation_metric=best_worst,
        internal_validation_condition_mean_mae=best_mean,
    )


def diagnose_stressor_robustness(
    report_path: Path,
    predictions_path: Path,
    out_dir: Path,
    *,
    bootstrap_resamples: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Render robust-capacity comparison diagnostics."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    predictions = pq.read_table(predictions_path).to_pylist()
    out_dir.mkdir(parents=True, exist_ok=True)
    leaderboard = robust_leaderboard_rows(report["metrics"])
    paired = paired_condition_gain_rows(predictions)
    claim = stressor_robust_claim_readiness(
        leaderboard,
        paired,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    _write_csv(out_dir / "robustness_leaderboard.csv", leaderboard)
    _write_csv(out_dir / "paired_condition_gains.csv", paired)
    _write_c_rate_summary_md(leaderboard, paired, claim, out_dir / "c_rate_robustness_summary.md")
    _write_claim_readiness_md(claim, out_dir / "stressor_robustness_claim_readiness.md")
    return {
        "status": "passed",
        "row_counts": {
            "leaderboard_rows": len(leaderboard),
            "paired_condition_gain_rows": len(paired),
        },
        "claim_readiness": claim,
        "outputs": {
            "leaderboard": str(out_dir / "robustness_leaderboard.csv"),
            "paired_condition_gains": str(out_dir / "paired_condition_gains.csv"),
            "c_rate_summary": str(out_dir / "c_rate_robustness_summary.md"),
            "claim_readiness": str(out_dir / "stressor_robustness_claim_readiness.md"),
        },
    }


def robust_leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        grouped[
            (
                str(metric["run_scope"]),
                str(metric["model_level"]),
                str(metric["feature_group"]),
                str(metric["target"]),
                str(metric["split_name"]),
            )
        ].append(metric)
    rows = []
    for (run_scope, model, feature, target, split), group in sorted(grouped.items()):
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model,
                "feature_group": feature,
                "target": target,
                "split_name": split,
                "fold_count": len(group),
                "mean_mae": _mean([float(item["mae"]) for item in group]),
                "mean_rmse": _mean([float(item["rmse"]) for item in group]),
                "condition_mean_mae": _mean([float(item["condition_mean_mae"]) for item in group]),
                "condition_median_mae": _mean([float(item["condition_median_mae"]) for item in group]),
                "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in group),
                "selected_variants": ",".join(
                    sorted({str(item.get("selected_variant")) for item in group if item.get("selected_variant")})
                ),
            }
        )
    return rows


def paired_condition_gain_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    condition_errors = _condition_mae_by_prediction_group(predictions)
    reference_items = [(key, value) for key, value in condition_errors.items() if key[3] == "R0_reference_hgb50"]
    rows = []
    for key, candidate_mae in sorted(condition_errors.items()):
        run_scope, split_name, target, model, feature, fold, parameter_set = key
        if model == "R0_reference_hgb50":
            continue
        for reference_key, reference in reference_items:
            (
                ref_run_scope,
                ref_split_name,
                ref_target,
                _ref_model,
                ref_feature,
                ref_fold,
                ref_parameter_set,
            ) = reference_key
            if (
                ref_run_scope != run_scope
                or ref_split_name != split_name
                or ref_target != target
                or ref_fold != fold
                or ref_parameter_set != parameter_set
            ):
                continue
            rows.append(
                {
                    "run_scope": run_scope,
                    "split_name": split_name,
                    "heldout_fold": fold,
                    "target": target,
                    "feature_group": feature,
                    "candidate_feature_group": feature,
                    "reference_feature_group": ref_feature,
                    "candidate_model_level": model,
                    "reference_model_level": "R0_reference_hgb50",
                    "parameter_set": parameter_set,
                    "reference_condition_mae": reference,
                    "candidate_condition_mae": candidate_mae,
                    "condition_mae_gain": reference - candidate_mae,
                }
            )
    return rows


def stressor_robust_claim_readiness(
    leaderboard: list[dict[str, Any]],
    paired_gains: list[dict[str, Any]],
    *,
    bootstrap_resamples: int,
    seed: int,
) -> dict[str, Any]:
    primary_rows = [
        row
        for row in leaderboard
        if row["run_scope"] == "primary"
        and row["target"] == PRIMARY_TARGET
        and row["split_name"] == PRIMARY_SPLIT
    ]
    r0_f4 = _find_leaderboard(primary_rows, "R0_reference_hgb50", "F4_state_log_age_scalar")
    r0_stress_rows = [
        row
        for row in primary_rows
        if row["model_level"] == "R0_reference_hgb50" and row["feature_group"] != "F4_state_log_age_scalar"
    ]
    r0_stress = min(r0_stress_rows, key=lambda row: float(row["condition_mean_mae"]), default=None)
    candidates = [row for row in primary_rows if row["model_level"] != "R0_reference_hgb50"]
    best = min(candidates, key=lambda row: float(row["condition_mean_mae"]), default=None)
    gain_vs_f4 = _leaderboard_gain(r0_f4, best)
    gain_vs_stress = _leaderboard_gain(r0_stress, best)
    paired_for_best_vs_f4 = [
        row
        for row in paired_gains
        if best
        and row["run_scope"] == "primary"
        and row["target"] == PRIMARY_TARGET
        and row["split_name"] == PRIMARY_SPLIT
        and row["candidate_model_level"] == best["model_level"]
        and row["candidate_feature_group"] == best["feature_group"]
        and row["reference_feature_group"] == "F4_state_log_age_scalar"
    ]
    paired_for_best_vs_stress = [
        row
        for row in paired_gains
        if best
        and r0_stress
        and row["run_scope"] == "primary"
        and row["target"] == PRIMARY_TARGET
        and row["split_name"] == PRIMARY_SPLIT
        and row["candidate_model_level"] == best["model_level"]
        and row["candidate_feature_group"] == best["feature_group"]
        and row["reference_feature_group"] == r0_stress["feature_group"]
    ]
    paired_mean_vs_f4 = _optional_mean([float(row["condition_mae_gain"]) for row in paired_for_best_vs_f4])
    paired_p05_vs_f4 = _bootstrap_mean_p05(
        [float(row["condition_mae_gain"]) for row in paired_for_best_vs_f4],
        resamples=bootstrap_resamples,
        seed=seed,
    )
    paired_mean_vs_stress = _optional_mean([float(row["condition_mae_gain"]) for row in paired_for_best_vs_stress])
    paired_p05_vs_stress = _bootstrap_mean_p05(
        [float(row["condition_mae_gain"]) for row in paired_for_best_vs_stress],
        resamples=bootstrap_resamples,
        seed=seed,
    )
    paired_p05 = _min_optional(paired_p05_vs_f4, paired_p05_vs_stress)
    max_degradation = _max_other_split_relative_degradation(leaderboard, best)
    supported = (
        gain_vs_f4 is not None
        and gain_vs_stress is not None
        and gain_vs_f4 > 0
        and gain_vs_stress > 0
        and paired_p05_vs_f4 is not None
        and paired_p05_vs_f4 > 0
        and paired_p05_vs_stress is not None
        and paired_p05_vs_stress > 0
        and max_degradation is not None
        and max_degradation <= 0.05
    )
    return {
        "robust_capacity_claim": "supported_for_diagnostics" if supported else "not_supported",
        "c_rate_delta_improves_vs_f4": gain_vs_f4,
        "c_rate_delta_improves_vs_stress_reference": gain_vs_stress,
        "paired_condition_gain_mean": _min_optional(paired_mean_vs_f4, paired_mean_vs_stress),
        "paired_condition_gain_p05": paired_p05,
        "paired_condition_gain_mean_vs_f4": paired_mean_vs_f4,
        "paired_condition_gain_p05_vs_f4": paired_p05_vs_f4,
        "paired_condition_gain_mean_vs_stress_reference": paired_mean_vs_stress,
        "paired_condition_gain_p05_vs_stress_reference": paired_p05_vs_stress,
        "max_other_split_relative_degradation": max_degradation,
        "best_candidate_model_level": best["model_level"] if best else None,
        "best_candidate_feature_group": best["feature_group"] if best else None,
        "best_candidate_condition_mean_mae": best["condition_mean_mae"] if best else None,
        "f4_reference_condition_mean_mae": r0_f4["condition_mean_mae"] if r0_f4 else None,
        "stress_reference_feature_group": r0_stress["feature_group"] if r0_stress else None,
        "stress_reference_condition_mean_mae": r0_stress["condition_mean_mae"] if r0_stress else None,
        "architecture_readiness": "blocked",
        "policy_ranking": "blocked",
        "selection_policy": (
            "R4 selects from R0/R1/R2 on internal training-only condition splits. "
            "Exact validation-metric ties prefer R2, then R1, then R0. "
            "R3 bagging is evaluated directly but excluded from nested selection to avoid redundant bagged refits."
        ),
        "claim_rule": (
            "Support requires C-rate delta gains over F4 and strongest stress R0, "
            "paired bootstrap p05 above zero against both references, and <=5% degradation outside C-rate."
        ),
    }


def pareto_model_settings(
    selected_models: list[str],
    *,
    weight_strengths: list[float],
    bag_counts: list[int],
) -> list[dict[str, Any]]:
    settings: list[dict[str, Any]] = []
    for model_level in selected_models:
        if model_level == "R0_reference_hgb50":
            settings.append(
                {
                    "model_setting_id": "R0_reference_hgb50",
                    "model_level": model_level,
                    "weight_strength": 0.0,
                    "bag_count": 1,
                }
            )
        elif model_level in {"R1_condition_balanced_hgb", "R2_stressor_balanced_hgb", "R4_worst_fold_selected_hgb"}:
            for strength in weight_strengths:
                settings.append(
                    {
                        "model_setting_id": f"{model_level}__w{_slug_float(strength)}",
                        "model_level": model_level,
                        "weight_strength": strength,
                        "bag_count": 1,
                    }
                )
        elif model_level == "R3_condition_bagged_hgb":
            for bag_count in bag_counts:
                settings.append(
                    {
                        "model_setting_id": f"{model_level}__bags{bag_count}",
                        "model_level": model_level,
                        "weight_strength": 0.0,
                        "bag_count": bag_count,
                    }
                )
        else:
            raise ValueError(f"Unknown robust model level: {model_level}")
    if not settings:
        raise ValueError("At least one Pareto model setting must be selected.")
    return settings


def diagnose_stressor_robust_forensics(
    report_path: Path,
    predictions_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Render failure-source forensics for an existing stressor-robust run."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    predictions = pq.read_table(predictions_path).to_pylist()
    out_dir.mkdir(parents=True, exist_ok=True)
    leaderboard = robust_leaderboard_rows(report["metrics"])
    split_degradation = degradation_by_split_target_feature_rows(leaderboard)
    condition_degradation = degradation_by_condition_rows(predictions)
    worst_conditions = sorted(
        [row for row in condition_degradation if _as_float(row["condition_mae_delta"]) > 0],
        key=lambda row: _as_float(row["condition_mae_delta"]),
        reverse=True,
    )[:50]
    claim = stressor_robust_claim_readiness(
        leaderboard,
        paired_condition_gain_rows(predictions),
        bootstrap_resamples=1000,
        seed=42,
    )
    _write_csv(out_dir / "plots" / "degradation_by_split_target_feature.csv", split_degradation)
    _write_csv(out_dir / "plots" / "degradation_by_condition.csv", condition_degradation)
    _write_csv(out_dir / "plots" / "worst_regression_conditions.csv", worst_conditions)
    _write_stressor_forensics_md(
        split_degradation,
        worst_conditions,
        claim,
        out_dir / "stressor_failure_forensics.md",
    )
    return {
        "status": "passed",
        "row_counts": {
            "split_degradation_rows": len(split_degradation),
            "condition_degradation_rows": len(condition_degradation),
            "worst_condition_rows": len(worst_conditions),
        },
        "outputs": {
            "forensics": str(out_dir / "stressor_failure_forensics.md"),
            "split_degradation": str(out_dir / "plots" / "degradation_by_split_target_feature.csv"),
            "condition_degradation": str(out_dir / "plots" / "degradation_by_condition.csv"),
            "worst_conditions": str(out_dir / "plots" / "worst_regression_conditions.csv"),
        },
    }


def degradation_by_split_target_feature_rows(leaderboard: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in leaderboard:
        if row["run_scope"] != "primary" or row["model_level"] == "R0_reference_hgb50":
            continue
        reference = _find_leaderboard(
            [
                ref
                for ref in leaderboard
                if ref["run_scope"] == row["run_scope"]
                and ref["target"] == row["target"]
                and ref["split_name"] == row["split_name"]
            ],
            "R0_reference_hgb50",
            str(row["feature_group"]),
        )
        if not reference:
            continue
        ref_value = _as_float(reference["condition_mean_mae"])
        candidate_value = _as_float(row["condition_mean_mae"])
        output.append(
            {
                "run_scope": row["run_scope"],
                "split_name": row["split_name"],
                "target": row["target"],
                "model_level": row["model_level"],
                "feature_group": row["feature_group"],
                "reference_model_level": "R0_reference_hgb50",
                "reference_feature_group": row["feature_group"],
                "candidate_condition_mean_mae": candidate_value,
                "reference_condition_mean_mae": ref_value,
                "condition_mean_mae_delta": candidate_value - ref_value,
                "relative_degradation": ((candidate_value - ref_value) / ref_value) if ref_value > 0 else None,
                "exceeds_5pct_guardrail": (
                    ((candidate_value - ref_value) / ref_value) > 0.05 if ref_value > 0 else False
                ),
            }
        )
    return output


def degradation_by_condition_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    condition_errors = _condition_mae_by_prediction_group(predictions)
    output = []
    for key, candidate_mae in sorted(condition_errors.items()):
        run_scope, split_name, target, model, feature, fold, parameter_set = key
        if model == "R0_reference_hgb50" or run_scope != "primary":
            continue
        reference = condition_errors.get(
            (run_scope, split_name, target, "R0_reference_hgb50", feature, fold, parameter_set)
        )
        if reference is None:
            continue
        output.append(
            {
                "run_scope": run_scope,
                "split_name": split_name,
                "target": target,
                "model_level": model,
                "feature_group": feature,
                "heldout_fold": fold,
                "parameter_set": parameter_set,
                "candidate_condition_mae": candidate_mae,
                "reference_condition_mae": reference,
                "condition_mae_delta": candidate_mae - reference,
                "relative_degradation": ((candidate_mae - reference) / reference) if reference > 0 else None,
            }
        )
    return output


def pareto_leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        grouped[
            (
                str(metric["run_scope"]),
                str(metric["model_setting_id"]),
                str(metric["model_level"]),
                str(metric["feature_group"]),
                str(metric["target"]),
                str(metric["split_name"]),
            )
        ].append(metric)
    rows = []
    for (run_scope, setting_id, model, feature, target, split), group in sorted(grouped.items()):
        rows.append(
            {
                "run_scope": run_scope,
                "model_setting_id": setting_id,
                "model_level": model,
                "feature_group": feature,
                "target": target,
                "split_name": split,
                "fold_count": len(group),
                "weight_strength": group[0].get("weight_strength"),
                "bag_count": group[0].get("bag_count"),
                "mean_mae": _mean([float(item["mae"]) for item in group]),
                "mean_rmse": _mean([float(item["rmse"]) for item in group]),
                "condition_mean_mae": _mean([float(item["condition_mean_mae"]) for item in group]),
                "condition_median_mae": _mean([float(item["condition_median_mae"]) for item in group]),
                "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in group),
                "selected_variants": ",".join(
                    sorted({str(item.get("selected_variant")) for item in group if item.get("selected_variant")})
                ),
            }
        )
    return rows


def pareto_paired_condition_gain_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    condition_errors = _condition_mae_by_prediction_setting_group(predictions)
    reference_items = [(key, value) for key, value in condition_errors.items() if key[3] == "R0_reference_hgb50"]
    rows = []
    for key, candidate_mae in sorted(condition_errors.items()):
        run_scope, split_name, target, model, feature, setting_id, fold, parameter_set = key
        if model == "R0_reference_hgb50":
            continue
        for reference_key, reference in reference_items:
            (
                ref_run_scope,
                ref_split_name,
                ref_target,
                _ref_model,
                ref_feature,
                _ref_setting,
                ref_fold,
                ref_parameter_set,
            ) = reference_key
            if (
                ref_run_scope != run_scope
                or ref_split_name != split_name
                or ref_target != target
                or ref_fold != fold
                or ref_parameter_set != parameter_set
            ):
                continue
            rows.append(
                {
                    "run_scope": run_scope,
                    "split_name": split_name,
                    "heldout_fold": fold,
                    "target": target,
                    "model_setting_id": setting_id,
                    "feature_group": feature,
                    "candidate_feature_group": feature,
                    "reference_feature_group": ref_feature,
                    "candidate_model_level": model,
                    "reference_model_level": "R0_reference_hgb50",
                    "parameter_set": parameter_set,
                    "reference_condition_mae": reference,
                    "candidate_condition_mae": candidate_mae,
                    "condition_mae_gain": reference - candidate_mae,
                }
            )
    return rows


def pareto_frontier_rows(
    leaderboard: list[dict[str, Any]],
    paired_gains: list[dict[str, Any]],
    *,
    bootstrap_resamples: int = 1000,
    seed: int = 42,
) -> list[dict[str, Any]]:
    primary_rows = [
        row
        for row in leaderboard
        if row["run_scope"] == "primary" and row["target"] == PRIMARY_TARGET and row["split_name"] == PRIMARY_SPLIT
    ]
    r0_f4 = _find_pareto_leaderboard(primary_rows, "R0_reference_hgb50", "F4_state_log_age_scalar")
    r0_stress_rows = [
        row
        for row in primary_rows
        if row["model_level"] == "R0_reference_hgb50" and row["feature_group"] != "F4_state_log_age_scalar"
    ]
    r0_stress = min(r0_stress_rows, key=lambda row: float(row["condition_mean_mae"]), default=None)
    output = []
    for row in primary_rows:
        if row["model_level"] == "R0_reference_hgb50":
            continue
        gain_vs_f4 = _leaderboard_gain(r0_f4, row)
        gain_vs_stress = _leaderboard_gain(r0_stress, row)
        paired_vs_f4 = _pareto_gains_for_candidate(paired_gains, row, "F4_state_log_age_scalar")
        paired_vs_stress = _pareto_gains_for_candidate(
            paired_gains,
            row,
            str(r0_stress["feature_group"]) if r0_stress else "",
        )
        max_degradation = _max_other_split_relative_degradation_for_setting(leaderboard, row)
        output.append(
            {
                "model_setting_id": row["model_setting_id"],
                "model_level": row["model_level"],
                "feature_group": row["feature_group"],
                "weight_strength": row.get("weight_strength"),
                "bag_count": row.get("bag_count"),
                "c_rate_condition_mean_mae": row["condition_mean_mae"],
                "c_rate_worst_condition_mae": row["worst_condition_mae"],
                "gain_vs_f4": gain_vs_f4,
                "gain_vs_stress_reference": gain_vs_stress,
                "paired_p05_vs_f4": _bootstrap_mean_p05(paired_vs_f4, resamples=bootstrap_resamples, seed=seed),
                "paired_p05_vs_stress_reference": _bootstrap_mean_p05(
                    paired_vs_stress,
                    resamples=bootstrap_resamples,
                    seed=seed,
                ),
                "max_other_split_relative_degradation": max_degradation,
                "is_predeclared_primary_setting": _is_predeclared_pareto_setting(row),
            }
        )
    _mark_nondominated(output)
    return sorted(
        output,
        key=lambda item: (
            not bool(item["is_predeclared_primary_setting"]),
            _finite_or(item["max_other_split_relative_degradation"], math.inf),
            -_finite_or(item["gain_vs_stress_reference"], -math.inf),
        ),
    )


def non_degradation_threshold_sensitivity_rows(frontier: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in frontier:
        for threshold in NON_DEGRADATION_THRESHOLDS:
            max_degradation = row["max_other_split_relative_degradation"]
            passes = _pareto_candidate_passes(row, max_degradation_threshold=threshold)
            output.append(
                {
                    "model_setting_id": row["model_setting_id"],
                    "model_level": row["model_level"],
                    "feature_group": row["feature_group"],
                    "weight_strength": row["weight_strength"],
                    "bag_count": row["bag_count"],
                    "threshold": threshold,
                    "gain_vs_f4": row["gain_vs_f4"],
                    "gain_vs_stress_reference": row["gain_vs_stress_reference"],
                    "paired_p05_vs_f4": row["paired_p05_vs_f4"],
                    "paired_p05_vs_stress_reference": row["paired_p05_vs_stress_reference"],
                    "max_other_split_relative_degradation": max_degradation,
                    "passes_threshold": passes,
                    "is_predeclared_primary_setting": row["is_predeclared_primary_setting"],
                }
            )
    return output


def stressor_robust_pareto_claim_readiness(frontier: list[dict[str, Any]]) -> dict[str, Any]:
    predeclared = next((row for row in frontier if row["is_predeclared_primary_setting"]), None)
    predeclared_passes = bool(predeclared and _pareto_candidate_passes(predeclared, max_degradation_threshold=0.05))
    passing_frontier = [
        row for row in frontier if _pareto_candidate_passes(row, max_degradation_threshold=0.05)
    ]
    status = "supported_for_diagnostics" if predeclared_passes else "not_supported"
    if not predeclared_passes and passing_frontier:
        status = "diagnostic_only"
    best = predeclared or (frontier[0] if frontier else None)
    return {
        "stressor_robust_pareto_claim": status,
        "predeclared_setting_id": best["model_setting_id"] if best else None,
        "predeclared_passes_5pct": predeclared_passes,
        "passing_frontier_settings_5pct": len(passing_frontier),
        "best_c_rate_gain_vs_f4": best["gain_vs_f4"] if best else None,
        "best_c_rate_gain_vs_stress_reference": best["gain_vs_stress_reference"] if best else None,
        "best_max_other_split_relative_degradation": (
            best["max_other_split_relative_degradation"] if best else None
        ),
        "architecture_readiness": "blocked",
        "policy_ranking": "blocked",
        "claim_rule": (
            "Support requires the predeclared R2/F8/weight=1.0 setting to retain positive C-rate delta gains "
            "versus F4 and stress references, paired p05 above zero for both references, and <=5% outside-C-rate "
            "degradation. Other passing frontier points are diagnostic only."
        ),
    }


def stressor_robust_adaptive_claim_readiness(frontier: list[dict[str, Any]]) -> dict[str, Any]:
    adaptive = next(
        (
            row
            for row in frontier
            if row["model_setting_id"] == ADAPTIVE_MODEL_SETTING_ID
            and row["feature_group"] == PREDECLARED_PARETO_FEATURE_GROUP
        ),
        None,
    )
    adaptive_passes = bool(adaptive and _pareto_candidate_passes(adaptive, max_degradation_threshold=0.05))
    return {
        "stressor_robust_adaptive_claim": "supported_for_diagnostics" if adaptive_passes else "not_supported",
        "adaptive_setting_id": adaptive["model_setting_id"] if adaptive else None,
        "adaptive_passes_5pct": adaptive_passes,
        "c_rate_gain_vs_f4": adaptive["gain_vs_f4"] if adaptive else None,
        "c_rate_gain_vs_stress_reference": adaptive["gain_vs_stress_reference"] if adaptive else None,
        "paired_p05_vs_f4": adaptive["paired_p05_vs_f4"] if adaptive else None,
        "paired_p05_vs_stress_reference": adaptive["paired_p05_vs_stress_reference"] if adaptive else None,
        "max_other_split_relative_degradation": (
            adaptive["max_other_split_relative_degradation"] if adaptive else None
        ),
        "architecture_readiness": "blocked",
        "policy_ranking": "blocked",
        "claim_rule": (
            "Support requires the train-only adaptive selector on F8 to retain positive C-rate delta gains "
            "versus F4 and stress references, paired p05 above zero for both references, and <=5% "
            "outside-C-rate degradation. Outer held-out rows must not be used for weight selection."
        ),
    }


def _expand_adaptive_replication_seed_reports(
    computed_run_reports: list[dict[str, Any]],
    *,
    requested_seeds: list[int],
    selection_policies: list[str],
    seed_reuse_mode: str,
) -> list[dict[str, Any]]:
    if seed_reuse_mode == "recomputed_each_seed":
        return computed_run_reports
    if not computed_run_reports:
        return []
    output: list[dict[str, Any]] = []
    by_policy = {str(report["selection_policy"]): report for report in computed_run_reports}
    missing_policies = sorted(set(selection_policies) - set(by_policy))
    if missing_policies:
        raise ValueError(f"Missing computed replication reports for policies: {missing_policies}")
    for policy in selection_policies:
        base = by_policy[policy]
        computed_seed = int(base["computed_seed"])
        for seed in requested_seeds:
            cloned = copy.deepcopy(base)
            cloned["seed"] = int(seed)
            cloned["computed_seed"] = computed_seed
            cloned["seed_reuse_mode"] = seed_reuse_mode
            for row in cloned.get("selection_rows", []):
                row["seed"] = int(seed)
                row["computed_seed"] = computed_seed
                row["seed_reuse_mode"] = seed_reuse_mode
            output.append(cloned)
    return output


def adaptive_replication_leakage_audit(run_reports: list[dict[str, Any]]) -> dict[str, Any]:
    outer_overlaps: list[int] = []
    inner_overlaps: list[int] = []
    for report in run_reports:
        for row in report.get("selection_rows", []):
            outer_overlaps.append(int(row.get("outer_train_test_overlap_count", 0)))
            inner_overlaps.append(int(row.get("max_inner_train_validation_overlap_count", 0)))
    max_outer = max(outer_overlaps, default=0)
    max_inner = max(inner_overlaps, default=0)
    status = "passed" if max_outer == 0 and max_inner == 0 and run_reports else "failed"
    return {
        "status": status,
        "run_reports_checked": len(run_reports),
        "selection_rows_checked": len(outer_overlaps),
        "max_outer_train_test_overlap_count": max_outer,
        "max_inner_train_validation_overlap_count": max_inner,
        "rule": (
            "Adaptive weight selection must use only outer-training rows. "
            "Inner fit/validation conditions and outer train/test conditions must not overlap."
        ),
    }


def adaptive_replication_claim_readiness(
    rows: list[dict[str, Any]],
    *,
    expected_seeds: list[int],
    primary_policy: str = "conservative_guarded",
    leakage_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    primary_rows = [row for row in rows if row["selection_policy"] == primary_policy]
    observed_seeds = sorted({int(row["seed"]) for row in primary_rows})
    expected_seed_set = {int(seed) for seed in expected_seeds}
    missing_seeds = sorted(expected_seed_set - set(observed_seeds))
    failing_rows = [
        row
        for row in primary_rows
        if int(row["seed"]) in expected_seed_set and not bool(row["adaptive_passes_5pct"])
    ]
    leakage_passes = (leakage_audit or {}).get("status") == "passed"
    all_pass = (
        bool(expected_seed_set)
        and not missing_seeds
        and len(primary_rows) >= len(expected_seed_set)
        and not failing_rows
        and leakage_passes
    )
    any_pass = any(bool(row["adaptive_passes_5pct"]) for row in primary_rows)
    status = "supported_for_diagnostics" if all_pass else ("partially_supported" if any_pass else "not_supported")
    required_rows = [row for row in primary_rows if int(row["seed"]) in expected_seed_set]
    return {
        "adaptive_replication_claim": status,
        "primary_policy": primary_policy,
        "required_seed_count": len(expected_seed_set),
        "observed_seed_count": len(observed_seeds),
        "missing_seeds": ",".join(str(seed) for seed in missing_seeds),
        "failing_seeds": ",".join(str(row["seed"]) for row in failing_rows),
        "all_required_seeds_pass": all_pass,
        "passing_seed_count": sum(1 for row in required_rows if bool(row["adaptive_passes_5pct"])),
        "min_c_rate_gain_vs_f4": min(
            (_as_float(row["c_rate_gain_vs_f4"]) for row in required_rows),
            default=None,
        ),
        "min_c_rate_gain_vs_stress_reference": min(
            (_as_float(row["c_rate_gain_vs_stress_reference"]) for row in required_rows),
            default=None,
        ),
        "min_paired_p05_vs_f4": min(
            (_as_float(row["paired_p05_vs_f4"]) for row in required_rows),
            default=None,
        ),
        "min_paired_p05_vs_stress_reference": min(
            (_as_float(row["paired_p05_vs_stress_reference"]) for row in required_rows),
            default=None,
        ),
        "max_other_split_relative_degradation": max(
            (_as_float(row["max_other_split_relative_degradation"]) for row in required_rows),
            default=None,
        ),
        "leakage_audit": (leakage_audit or {}).get("status", "not_run"),
        "architecture_readiness": "blocked",
        "policy_ranking": "blocked",
        "claim_rule": (
            "Support requires every required conservative_guarded seed to pass C-rate gains versus F4 "
            "and stress references, paired p05 above zero, <=5% outside-C-rate degradation, and a "
            "passed leakage audit. Any seed failure blocks replicated support."
        ),
    }


def adaptive_replication_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["selection_policy"])].append(row)
    output = []
    for policy, group in sorted(grouped.items()):
        output.append(
            {
                "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
                "selection_policy": policy,
                "seed_count": len(group),
                "passing_seed_count": sum(1 for row in group if bool(row["adaptive_passes_5pct"])),
                "min_c_rate_gain_vs_f4": min(_as_float(row["c_rate_gain_vs_f4"]) for row in group),
                "min_c_rate_gain_vs_stress_reference": min(
                    _as_float(row["c_rate_gain_vs_stress_reference"]) for row in group
                ),
                "min_paired_p05_vs_f4": min(_as_float(row["paired_p05_vs_f4"]) for row in group),
                "min_paired_p05_vs_stress_reference": min(
                    _as_float(row["paired_p05_vs_stress_reference"]) for row in group
                ),
                "max_other_split_relative_degradation": max(
                    _as_float(row["max_other_split_relative_degradation"]) for row in group
                ),
            }
        )
    return output


def adaptive_replication_degradation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
            "seed": row["seed"],
            "selection_policy": row["selection_policy"],
            "max_other_split_relative_degradation": row["max_other_split_relative_degradation"],
            "adaptive_passes_5pct": row["adaptive_passes_5pct"],
        }
        for row in rows
    ]


def _adaptive_replication_row(report: dict[str, Any]) -> dict[str, Any]:
    claim = report["claim_readiness"]
    selected_counts = _selected_weight_count_string(report.get("selection_rows", []))
    return {
        "schema_version": ADAPTIVE_REPLICATION_SCHEMA_VERSION,
        "seed": int(report["seed"]),
        "computed_seed": int(report.get("computed_seed", report["seed"])),
        "seed_reuse_mode": str(report.get("seed_reuse_mode", "recomputed_each_seed")),
        "selection_policy": str(report["selection_policy"]),
        "adaptive_claim": claim["stressor_robust_adaptive_claim"],
        "adaptive_passes_5pct": bool(claim["adaptive_passes_5pct"]),
        "c_rate_gain_vs_f4": claim["c_rate_gain_vs_f4"],
        "c_rate_gain_vs_stress_reference": claim["c_rate_gain_vs_stress_reference"],
        "paired_p05_vs_f4": claim["paired_p05_vs_f4"],
        "paired_p05_vs_stress_reference": claim["paired_p05_vs_stress_reference"],
        "max_other_split_relative_degradation": claim["max_other_split_relative_degradation"],
        "metric_rows": report["row_counts"]["metrics"],
        "prediction_rows": report["row_counts"]["predictions"],
        "selection_rows": report["row_counts"]["selection_rows"],
        "selected_weight_counts": selected_counts,
    }


def _selected_weight_count_string(selection_rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for row in selection_rows:
        if bool(row.get("selected_by_train_only_rule")):
            counts[str(row["weight_strength"])] += 1
    return ";".join(f"{weight}:{counts[weight]}" for weight in sorted(counts))


def _robust_prediction_rows(
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
    rows = []
    for row, prediction in zip(test_rows, predictions):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "subset_name": subset_name,
                "run_scope": run_scope,
                "split_name": split_name,
                "heldout_fold": int(heldout_fold),
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "cell_id": str(row["cell_id"]),
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "checkup_k_next": int(row["checkup_k_next"]),
                "sensitivity_flagged_monotonicity": bool(row["sensitivity_flagged_monotonicity"]),
                "y_true": _evaluation_target_value(row, target),
                "y_pred": _as_float(prediction["y_pred"]),
                "y_pred_q10": None,
                "y_pred_q50": None,
                "y_pred_q90": None,
            }
        )
    return rows


def _pareto_prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    subset_name: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    target: str,
    model_setting_id: str,
    weight_strength: float,
    bag_count: int,
) -> list[dict[str, Any]]:
    rows = _robust_prediction_rows(
        test_rows,
        predictions,
        subset_name=subset_name,
        run_scope="primary",
        split_name=split_name,
        heldout_fold=heldout_fold,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
    )
    for row in rows:
        row.update(
            {
                "schema_version": PARETO_SCHEMA_VERSION,
                "model_setting_id": model_setting_id,
                "weight_strength": weight_strength,
                "bag_count": bag_count,
            }
        )
    return rows


def _adaptive_prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    subset_name: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    target: str,
    model_setting_id: str,
    selected_weight_strength: float | None,
    selection_mean_gain: float | None,
    selection_max_relative_degradation: float | None,
) -> list[dict[str, Any]]:
    rows = _pareto_prediction_rows(
        test_rows,
        predictions,
        subset_name=subset_name,
        split_name=split_name,
        heldout_fold=heldout_fold,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
        model_setting_id=model_setting_id,
        weight_strength=selected_weight_strength if selected_weight_strength is not None else 0.0,
        bag_count=1,
    )
    for row in rows:
        row.update(
            {
                "schema_version": ADAPTIVE_SCHEMA_VERSION,
                "selected_weight_strength": selected_weight_strength,
                "selection_mean_gain": selection_mean_gain,
                "selection_max_relative_degradation": selection_max_relative_degradation,
            }
        )
    return rows


def _condition_mae_by_prediction_group(predictions: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, str, int, int], float]:
    grouped: dict[tuple[str, str, str, str, str, int, int], list[float]] = defaultdict(list)
    for row in predictions:
        key = (
            str(row["run_scope"]),
            str(row["split_name"]),
            str(row["target"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
        )
        grouped[key].append(abs(_as_float(row["y_pred"]) - _as_float(row["y_true"])))
    return {key: _mean(values) for key, values in grouped.items()}


def _condition_mae_by_prediction_setting_group(
    predictions: list[dict[str, Any]],
) -> dict[tuple[str, str, str, str, str, str, int, int], float]:
    grouped: dict[tuple[str, str, str, str, str, str, int, int], list[float]] = defaultdict(list)
    for row in predictions:
        key = (
            str(row["run_scope"]),
            str(row["split_name"]),
            str(row["target"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row.get("model_setting_id", row["model_level"])),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
        )
        grouped[key].append(abs(_as_float(row["y_pred"]) - _as_float(row["y_true"])))
    return {key: _mean(values) for key, values in grouped.items()}


def _internal_condition_validation_split(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    validation_fraction: float = 0.2,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    condition_rows = _rows_by_parameter_set(rows)
    parameter_sets = sorted(condition_rows)
    if len(parameter_sets) < 2:
        raise ValueError("Internal model selection requires at least two training conditions.")
    rng = random.Random(seed)
    shuffled = list(parameter_sets)
    rng.shuffle(shuffled)
    validation_count = min(max(1, math.ceil(len(parameter_sets) * validation_fraction)), len(parameter_sets) - 1)
    validation_sets = set(shuffled[:validation_count])
    validation_rows = [row for row in rows if int(row["parameter_set"]) in validation_sets]
    fit_rows = [row for row in rows if int(row["parameter_set"]) not in validation_sets]
    assert_no_parameter_set_leakage(fit_rows, validation_rows, "internal_validation", 0)
    return fit_rows, validation_rows


def _rows_by_parameter_set(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["parameter_set"])].append(row)
    return grouped


def _normalize_weights(raw_weights: list[float]) -> list[float]:
    mean = sum(raw_weights) / len(raw_weights)
    return [value / mean for value in raw_weights]


def _normalize_float_grid(values: list[float] | None, default: tuple[float, ...], label: str) -> list[float]:
    raw = list(default if values is None else values)
    selected: list[float] = []
    seen = set()
    for value in raw:
        number = float(value)
        if number < 0:
            raise ValueError(f"{label} values must be non-negative.")
        if number in seen:
            continue
        selected.append(number)
        seen.add(number)
    if not selected:
        raise ValueError(f"At least one {label} must be selected.")
    return selected


def _normalize_int_grid(values: list[int] | None, default: tuple[int, ...], label: str) -> list[int]:
    raw = list(default if values is None else values)
    selected: list[int] = []
    seen = set()
    for value in raw:
        number = int(value)
        if number <= 0:
            raise ValueError(f"{label} values must be positive.")
        if number in seen:
            continue
        selected.append(number)
        seen.add(number)
    if not selected:
        raise ValueError(f"At least one {label} must be selected.")
    return selected


def _blend_weights(weights: list[float], *, strength: float) -> list[float]:
    if strength < 0:
        raise ValueError("weight strength must be non-negative.")
    return [1.0 + strength * (value - 1.0) for value in weights]


def _slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "p").replace("-", "m")


def _stressor_key(row: dict[str, Any], split_name: str) -> tuple[str, ...]:
    if split_name == "temperature_holdout_fold":
        return (_group_value(row.get("nominal_temperature_C")),)
    if split_name == "c_rate_holdout_fold":
        return (_c_rate_bucket(row.get("nominal_charge_C_rate")), _c_rate_bucket(row.get("nominal_discharge_C_rate")))
    if split_name == "profile_holdout_fold":
        return (_group_value(row.get("profile_label")),)
    if split_name == "voltage_window_holdout_fold":
        return (_group_value(row.get("voltage_window_family")),)
    return (
        _group_value(row.get("aging_mode")),
        _group_value(row.get("nominal_temperature_C")),
        _c_rate_bucket(row.get("nominal_charge_C_rate")),
        _group_value(row.get("voltage_window_family")),
        _group_value(row.get("profile_label")),
    )


def _variant_seed(seed: int, *parts: object) -> int:
    text = "|".join([str(seed), *(str(part) for part in parts)])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _group_value(value: Any) -> str:
    if value is None:
        return "<missing>"
    return str(value)


def _c_rate_bucket(value: Any) -> str:
    rate = _as_float(value)
    if not math.isfinite(rate):
        return "<missing>"
    if rate < 0.75:
        return "lt_0p75C"
    if rate < 1.25:
        return "0p75_1p25C"
    if rate < 1.75:
        return "1p25_1p75C"
    return "ge_1p75C"


def _find_leaderboard(
    rows: list[dict[str, Any]],
    model_level: str,
    feature_group: str,
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in rows
            if row["model_level"] == model_level and row["feature_group"] == feature_group
        ),
        None,
    )


def _leaderboard_gain(reference: dict[str, Any] | None, candidate: dict[str, Any] | None) -> float | None:
    if not reference or not candidate:
        return None
    return float(reference["condition_mean_mae"]) - float(candidate["condition_mean_mae"])


def _bootstrap_mean_p05(values: list[float], *, resamples: int, seed: int) -> float | None:
    if not values:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        sample = [rng.choice(values) for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[min(max(int(0.05 * (len(means) - 1)), 0), len(means) - 1)]


def _optional_mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _min_optional(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _max_other_split_relative_degradation(
    leaderboard: list[dict[str, Any]],
    best: dict[str, Any] | None,
) -> float | None:
    if not best:
        return None
    values = []
    for row in leaderboard:
        if (
            row["run_scope"] != "primary"
            or row["target"] != PRIMARY_TARGET
            or row["model_level"] != best["model_level"]
            or row["feature_group"] != best["feature_group"]
            or row["split_name"] == PRIMARY_SPLIT
        ):
            continue
        reference = _find_leaderboard(
            [
                ref
                for ref in leaderboard
                if ref["run_scope"] == "primary"
                and ref["target"] == PRIMARY_TARGET
                and ref["split_name"] == row["split_name"]
            ],
            "R0_reference_hgb50",
            best["feature_group"],
        )
        if not reference:
            continue
        ref_value = float(reference["condition_mean_mae"])
        if ref_value <= 0:
            continue
        values.append((float(row["condition_mean_mae"]) - ref_value) / ref_value)
    return max(values) if values else None


def _max_other_split_relative_degradation_for_setting(
    leaderboard: list[dict[str, Any]],
    candidate: dict[str, Any] | None,
) -> float | None:
    if not candidate:
        return None
    values = []
    for row in leaderboard:
        if (
            row["run_scope"] != "primary"
            or row["target"] != PRIMARY_TARGET
            or row["model_setting_id"] != candidate["model_setting_id"]
            or row["model_level"] != candidate["model_level"]
            or row["feature_group"] != candidate["feature_group"]
            or row["split_name"] == PRIMARY_SPLIT
        ):
            continue
        reference = _find_pareto_leaderboard(
            [
                ref
                for ref in leaderboard
                if ref["run_scope"] == "primary"
                and ref["target"] == PRIMARY_TARGET
                and ref["split_name"] == row["split_name"]
            ],
            "R0_reference_hgb50",
            str(candidate["feature_group"]),
        )
        if not reference:
            continue
        ref_value = float(reference["condition_mean_mae"])
        if ref_value <= 0:
            continue
        values.append((float(row["condition_mean_mae"]) - ref_value) / ref_value)
    return max(values) if values else None


def _find_pareto_leaderboard(
    rows: list[dict[str, Any]],
    model_level: str,
    feature_group: str,
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in rows
            if row["model_level"] == model_level and row["feature_group"] == feature_group
        ),
        None,
    )


def _pareto_gains_for_candidate(
    paired_gains: list[dict[str, Any]],
    candidate: dict[str, Any],
    reference_feature_group: str,
) -> list[float]:
    if not reference_feature_group:
        return []
    return [
        float(row["condition_mae_gain"])
        for row in paired_gains
        if row["run_scope"] == "primary"
        and row["target"] == PRIMARY_TARGET
        and row["split_name"] == PRIMARY_SPLIT
        and row["candidate_model_level"] == candidate["model_level"]
        and row["candidate_feature_group"] == candidate["feature_group"]
        and row["model_setting_id"] == candidate["model_setting_id"]
        and row["reference_feature_group"] == reference_feature_group
    ]


def _is_predeclared_pareto_setting(row: dict[str, Any]) -> bool:
    return (
        row["model_level"] == PREDECLARED_PARETO_MODEL_LEVEL
        and row["feature_group"] == PREDECLARED_PARETO_FEATURE_GROUP
        and abs(_as_float(row.get("weight_strength")) - PREDECLARED_PARETO_WEIGHT_STRENGTH) < 1e-12
    )


def _pareto_candidate_passes(row: dict[str, Any], *, max_degradation_threshold: float) -> bool:
    return (
        (gain_f4 := row.get("gain_vs_f4")) is not None
        and (gain_stress := row.get("gain_vs_stress_reference")) is not None
        and (p05_f4 := row.get("paired_p05_vs_f4")) is not None
        and (p05_stress := row.get("paired_p05_vs_stress_reference")) is not None
        and (degradation := row.get("max_other_split_relative_degradation")) is not None
        and _as_float(gain_f4) > 0
        and _as_float(gain_stress) > 0
        and _as_float(p05_f4) > 0
        and _as_float(p05_stress) > 0
        and _as_float(degradation) <= max_degradation_threshold
    )


def _mark_nondominated(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row_gain = _finite_or(row.get("gain_vs_stress_reference"), -math.inf)
        row_degradation = _finite_or(row.get("max_other_split_relative_degradation"), math.inf)
        dominated = False
        for other in rows:
            if other is row:
                continue
            other_gain = _finite_or(other.get("gain_vs_stress_reference"), -math.inf)
            other_degradation = _finite_or(other.get("max_other_split_relative_degradation"), math.inf)
            if (
                other_gain >= row_gain
                and other_degradation <= row_degradation
                and (other_gain > row_gain or other_degradation < row_degradation)
            ):
                dominated = True
                break
        row["is_nondominated"] = not dominated


def _finite_or(value: Any, default: float) -> float:
    number = _as_float(value)
    return number if math.isfinite(number) else default


def render_stressor_robust_pareto_artifacts(
    report: dict[str, Any],
    leaderboard: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    frontier: list[dict[str, Any]],
    threshold_sensitivity: list[dict[str, Any]],
    claim: dict[str, Any],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "robustness_leaderboard.csv", leaderboard)
    _write_csv(out_dir / "paired_condition_gains.csv", paired)
    _write_csv(out_dir / "plots" / "pareto_frontier.csv", frontier)
    _write_csv(out_dir / "plots" / "non_degradation_threshold_sensitivity.csv", threshold_sensitivity)
    _write_pareto_claim_readiness_md(report, claim, frontier, out_dir / "stressor_robust_pareto_claim_readiness.md")


def render_stressor_robust_adaptive_artifacts(
    report: dict[str, Any],
    leaderboard: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    frontier: list[dict[str, Any]],
    selection_rows: list[dict[str, Any]],
    claim: dict[str, Any],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "robustness_leaderboard.csv", leaderboard)
    _write_csv(out_dir / "paired_condition_gains.csv", paired)
    _write_csv(out_dir / "adaptive_selection_summary.csv", selection_rows)
    _write_csv(out_dir / "plots" / "adaptive_frontier.csv", frontier)
    _write_adaptive_claim_readiness_md(
        report,
        claim,
        frontier,
        selection_rows,
        out_dir / "stressor_robust_adaptive_claim_readiness.md",
    )


def render_stressor_robust_adaptive_replication_artifacts(
    report: dict[str, Any],
    replication_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    degradation_rows: list[dict[str, Any]],
    claim: dict[str, Any],
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "replication_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(out_dir / "plots" / "seed_sensitivity.csv", replication_rows)
    _write_csv(out_dir / "plots" / "policy_sensitivity.csv", policy_rows)
    _write_csv(out_dir / "plots" / "outside_split_degradation.csv", degradation_rows)
    _write_adaptive_replication_claim_readiness_md(
        report,
        claim,
        policy_rows,
        out_dir / "adaptive_replication_claim_readiness.md",
    )


def _write_stressor_forensics_md(
    split_degradation: list[dict[str, Any]],
    worst_conditions: list[dict[str, Any]],
    claim: dict[str, Any],
    path: Path,
) -> None:
    worst_splits = sorted(
        [row for row in split_degradation if row["target"] == PRIMARY_TARGET],
        key=lambda row: _finite_or(row["relative_degradation"], -math.inf),
        reverse=True,
    )[:10]
    lines = [
        "# Stressor-Robust Failure Forensics",
        "",
        "This report diagnoses where the existing robust-capacity near miss fails. It does not change the 5% non-degradation guardrail.",
        "",
        f"Current robust-capacity claim: `{claim['robust_capacity_claim']}`.",
        f"Best candidate: `{claim['best_candidate_model_level']}` / `{claim['best_candidate_feature_group']}`.",
        f"Max outside-C-rate relative degradation: `{_fmt(claim['max_other_split_relative_degradation'])}`.",
        "",
        "## Largest Split-Level Regressions",
        "",
        "| Split | Target | Model | Feature | Relative degradation | MAE delta |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in worst_splits:
        lines.append(
            "| "
            f"`{row['split_name']}` | `{row['target']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"`{_fmt(row['relative_degradation'])}` | `{_fmt(row['condition_mean_mae_delta'])}` |"
        )
    lines.extend(
        [
            "",
            "## Largest Condition-Level Regressions",
            "",
            "| Split | Target | Model | Feature | Parameter set | MAE delta | Relative degradation |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in worst_conditions[:10]:
        lines.append(
            "| "
            f"`{row['split_name']}` | `{row['target']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"`{row['parameter_set']}` | `{_fmt(row['condition_mae_delta'])}` | "
            f"`{_fmt(row['relative_degradation'])}` |"
        )
    lines.extend(
        [
            "",
            "Decision: use this for forensics only. Do not relax the 5% gate based on this report.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_adaptive_replication_claim_readiness_md(
    report: dict[str, Any],
    claim: dict[str, Any],
    policy_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# Adaptive Stressor-Robust Replication Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Replicated adaptive robust-selection diagnostic | `{claim['adaptive_replication_claim']}` | All required seeds pass: `{claim['all_required_seeds_pass']}`. |",
        f"| Required seed coverage | `diagnostic` | Observed `{claim['observed_seed_count']}` of `{claim['required_seed_count']}` required seeds; missing `{claim['missing_seeds'] or 'none'}`. |",
        f"| C-rate gain floor | `diagnostic` | Min gain vs F4 `{_fmt(claim['min_c_rate_gain_vs_f4'])}`; min gain vs stress `{_fmt(claim['min_c_rate_gain_vs_stress_reference'])}`. |",
        f"| Paired support floor | `diagnostic` | Min p05 vs F4 `{_fmt(claim['min_paired_p05_vs_f4'])}`; min p05 vs stress `{_fmt(claim['min_paired_p05_vs_stress_reference'])}`. |",
        f"| Other split non-degradation | `{'supported_for_diagnostics' if claim['all_required_seeds_pass'] else 'not_supported'}` | Max outside-C-rate degradation across required seeds `{_fmt(claim['max_other_split_relative_degradation'])}`. |",
        f"| Leakage audit | `{claim['leakage_audit']}` | Outer held-out rows must not enter inner selection. |",
        f"| Architecture readiness | `{claim['architecture_readiness']}` | This remains a non-neural diagnostic. |",
        f"| Policy ranking | `{claim['policy_ranking']}` | No calibrated risk or intervention task is tested. |",
        "",
        claim["claim_rule"],
        "",
        f"Seed reuse mode: `{report.get('seed_reuse_mode', 'recomputed_each_seed')}`; "
        f"effective fit seeds: `{','.join(str(seed) for seed in report.get('effective_fit_seeds', []))}`.",
        "",
        "## Policy Sensitivity",
        "",
        "| Policy | Seeds | Passing seeds | Min gain vs F4 | Min gain vs stress | Max outside-C-rate degradation |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in policy_rows:
        lines.append(
            "| "
            f"`{row['selection_policy']}` | `{row['seed_count']}` | `{row['passing_seed_count']}` | "
            f"`{_fmt(row['min_c_rate_gain_vs_f4'])}` | "
            f"`{_fmt(row['min_c_rate_gain_vs_stress_reference'])}` | "
            f"`{_fmt(row['max_other_split_relative_degradation'])}` |"
        )
    lines.extend(
        [
            "",
            f"Replication rows evaluated: `{report['row_counts']['replication_rows']}`.",
            "Decision: replicated support is narrow and diagnostic only. Do not claim C-rate fade is solved globally.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_adaptive_claim_readiness_md(
    report: dict[str, Any],
    claim: dict[str, Any],
    frontier: list[dict[str, Any]],
    selection_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    selected_counts = defaultdict(int)
    for row in selection_rows:
        if bool(row.get("selected_by_train_only_rule")):
            selected_counts[str(row["weight_strength"])] += 1
    selected_summary = ", ".join(
        f"w={strength}: {count}" for strength, count in sorted(selected_counts.items())
    ) or "none"
    lines = [
        "# Stressor-Robust Adaptive Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Adaptive robust-selection diagnostic | `{claim['stressor_robust_adaptive_claim']}` | Train-only adaptive setting passes 5% gate: `{claim['adaptive_passes_5pct']}`. |",
        f"| C-rate gain | `diagnostic` | Gain vs F4 `{_fmt(claim['c_rate_gain_vs_f4'])}`; gain vs stress reference `{_fmt(claim['c_rate_gain_vs_stress_reference'])}`. |",
        f"| Paired support | `diagnostic` | p05 vs F4 `{_fmt(claim['paired_p05_vs_f4'])}`; p05 vs stress `{_fmt(claim['paired_p05_vs_stress_reference'])}`. |",
        f"| Other split non-degradation | `{'supported_for_diagnostics' if claim['adaptive_passes_5pct'] else 'not_supported'}` | Max outside-C-rate degradation `{_fmt(claim['max_other_split_relative_degradation'])}`. |",
        f"| Architecture readiness | `{claim['architecture_readiness']}` | This is a non-neural train-only selector. |",
        f"| Policy ranking | `{claim['policy_ranking']}` | No calibrated risk or intervention task is tested. |",
        "",
        claim["claim_rule"],
        "",
        f"Selected weight counts from inner validation: {selected_summary}.",
        "",
        "## Frontier Rows",
        "",
        "| Setting | Model | Feature | Gain vs F4 | Gain vs stress | Max outside-C-rate degradation |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in frontier[:20]:
        lines.append(
            "| "
            f"`{row['model_setting_id']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"`{_fmt(row['gain_vs_f4'])}` | `{_fmt(row['gain_vs_stress_reference'])}` | "
            f"`{_fmt(row['max_other_split_relative_degradation'])}` |"
        )
    lines.extend(
        [
            "",
            f"Metric rows evaluated: `{report['row_counts']['metrics']}`.",
            "Decision: this supports only an adaptive robust-selection diagnostic if the strict outer guardrail passes.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_pareto_claim_readiness_md(
    report: dict[str, Any],
    claim: dict[str, Any],
    frontier: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# Stressor-Robust Pareto Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Pareto robust-capacity claim | `{claim['stressor_robust_pareto_claim']}` | Predeclared setting passes 5% gate: `{claim['predeclared_passes_5pct']}`. |",
        f"| C-rate gain | `diagnostic` | Gain vs F4 `{_fmt(claim['best_c_rate_gain_vs_f4'])}`; gain vs stress reference `{_fmt(claim['best_c_rate_gain_vs_stress_reference'])}`. |",
        f"| Other split non-degradation | `{'supported_for_diagnostics' if claim['predeclared_passes_5pct'] else 'not_supported'}` | Max degradation for predeclared setting `{_fmt(claim['best_max_other_split_relative_degradation'])}`. |",
        f"| Architecture readiness | `{claim['architecture_readiness']}` | This is a non-neural Pareto diagnostic only. |",
        f"| Policy ranking | `{claim['policy_ranking']}` | No calibrated risk or intervention task is tested. |",
        "",
        claim["claim_rule"],
        "",
        "## Nondominated Frontier Rows",
        "",
        "| Setting | Model | Feature | Gain vs F4 | Gain vs stress | Max outside-C-rate degradation | Predeclared |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in [item for item in frontier if item.get("is_nondominated")][:20]:
        lines.append(
            "| "
            f"`{row['model_setting_id']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"`{_fmt(row['gain_vs_f4'])}` | `{_fmt(row['gain_vs_stress_reference'])}` | "
            f"`{_fmt(row['max_other_split_relative_degradation'])}` | "
            f"`{row['is_predeclared_primary_setting']}` |"
        )
    lines.extend(
        [
            "",
            f"Metric rows evaluated: `{report['row_counts']['metrics']}`.",
            "Decision: passing non-predeclared frontier rows are diagnostic only.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_c_rate_summary_md(
    leaderboard: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    claim: dict[str, Any],
    path: Path,
) -> None:
    c_rate_rows = [
        row
        for row in leaderboard
        if row["run_scope"] == "primary"
        and row["split_name"] == PRIMARY_SPLIT
        and row["target"] in {"capacity_Ah_k1", "delta_capacity_Ah"}
    ]
    lines = [
        "# Stressor-Robust Capacity C-Rate Summary",
        "",
        "This report evaluates non-neural robust HGB variants under grouped validation. It does not authorize architecture, policy, or causal claims.",
        "",
        "| Target | Model | Feature group | Condition mean MAE | Worst condition MAE |",
        "|---|---|---|---:|---:|",
    ]
    for row in sorted(c_rate_rows, key=lambda item: (item["target"], float(item["condition_mean_mae"]))):
        lines.append(
            "| "
            f"`{row['target']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"`{_fmt(row['condition_mean_mae'])}` | `{_fmt(row['worst_condition_mae'])}` |"
        )
    lines.extend(
        [
            "",
            f"Best C-rate delta candidate: `{claim['best_candidate_model_level']}` / `{claim['best_candidate_feature_group']}`.",
            f"Gain vs F4 reference: `{_fmt(claim['c_rate_delta_improves_vs_f4'])}`.",
            f"Gain vs stress reference: `{_fmt(claim['c_rate_delta_improves_vs_stress_reference'])}`.",
            f"Paired condition gain p05 vs F4: `{_fmt(claim['paired_condition_gain_p05_vs_f4'])}`.",
            f"Paired condition gain p05 vs stress reference: `{_fmt(claim['paired_condition_gain_p05_vs_stress_reference'])}`.",
            "",
            f"Paired condition gain rows: `{len(paired)}`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_md(claim: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stressor-Robust Capacity Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        f"| Robust C-rate fade improvement | `{claim['robust_capacity_claim']}` | Gain vs F4 `{_fmt(claim['c_rate_delta_improves_vs_f4'])}`; gain vs stress reference `{_fmt(claim['c_rate_delta_improves_vs_stress_reference'])}`; paired p05 vs F4 `{_fmt(claim['paired_condition_gain_p05_vs_f4'])}`; paired p05 vs stress `{_fmt(claim['paired_condition_gain_p05_vs_stress_reference'])}`. |",
        f"| Other split non-degradation | `{'supported_for_diagnostics' if claim['max_other_split_relative_degradation'] is not None and claim['max_other_split_relative_degradation'] <= 0.05 else 'not_supported'}` | Max relative degradation outside C-rate is `{_fmt(claim['max_other_split_relative_degradation'])}`. |",
        f"| Architecture readiness | `{claim['architecture_readiness']}` | This is a non-neural baseline gate only. |",
        f"| Policy ranking | `{claim['policy_ranking']}` | No calibrated risk or intervention task is tested. |",
        "",
        claim["selection_policy"],
        "",
        claim["claim_rule"],
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


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _fmt(value: Any) -> str:
    number = _as_float(value)
    return "NA" if not math.isfinite(number) else f"{number:.6g}"
