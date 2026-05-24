"""Grouped stressor-robust capacity baselines."""

from __future__ import annotations

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


@dataclass(frozen=True)
class RobustPredictionResult:
    predictions: list[dict[str, float | None]]
    selected_variant: str | None = None
    internal_validation_metric: float | None = None
    internal_validation_condition_mean_mae: float | None = None


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
    )
    return RobustPredictionResult(predictions=predictions)


def condition_balanced_weights(rows: list[dict[str, Any]]) -> list[float]:
    counts = defaultdict(int)
    for row in rows:
        counts[int(row["parameter_set"])] += 1
    raw = [1.0 / counts[int(row["parameter_set"])] for row in rows]
    return _normalize_weights(raw)


def stressor_balanced_weights(rows: list[dict[str, Any]], split_name: str) -> list[float]:
    counts = defaultdict(int)
    for row in rows:
        counts[_stressor_key(row, split_name)] += 1
    raw = [1.0 / counts[_stressor_key(row, split_name)] for row in rows]
    return _normalize_weights(raw)


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
        sample_weight = condition_balanced_weights(train_rows)
    elif model_level == "R2_stressor_balanced_hgb":
        sample_weight = stressor_balanced_weights(train_rows, split_name)
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
