"""Milestone 2.2 semi-empirical capacity baselines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import (
    BASELINE_PREDICTION_SCHEMA,
    SPLIT_COLUMNS,
    assert_no_parameter_set_leakage,
    compute_metrics,
    iter_split_instances,
    load_baseline_rows,
    _all_primary_prediction_keys,
    _as_float,
    _best_selection_by_target_split,
    _condition_metadata_by_parameter_set,
    _evaluation_target_value,
    _format_diagnostic_value,
    _leaderboard_rows,
    _load_prediction_rows,
    _paired_best_nonpulse_gain_rows,
    _prediction_rows,
    _row_counts,
    _selection_condition_mae_rows,
    _write_csv,
)

SCHEMA_VERSION = "gate22.semi_empirical_capacity.v1"
MODEL_LEVEL = "L4_semi_empirical_ridge"
TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")
FEATURE_GROUPS = (
    "SE0_time_efc",
    "SE1_calendar_cycling",
    "SE2_temperature_voltage",
    "SE3_c_rate_interactions",
    "SE4_coupled_stress",
)
TARGET_DERIVED_FORBIDDEN = {
    "delta_capacity_per_day",
    "delta_capacity_per_efc",
    "delta_capacity_per_Ah_throughput",
    "delta_capacity_per_day_target",
    "delta_capacity_per_efc_target",
}

NUMERIC_FEATURES: dict[str, tuple[str, ...]] = {
    "SE0_time_efc": (
        "capacity_Ah_k",
        "calendar_days",
        "log_age_efc_delta",
    ),
    "SE1_calendar_cycling": (
        "capacity_Ah_k",
        "calendar_days",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
    ),
    "SE2_temperature_voltage": (
        "capacity_Ah_k",
        "calendar_days",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "log_age_mean_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_voltage_V",
        "log_age_max_voltage_V",
        "high_voltage_time_h",
        "cold_time_h",
        "hot_time_h",
    ),
    "SE3_c_rate_interactions": (
        "capacity_Ah_k",
        "calendar_days",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_mean_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_voltage_V",
        "log_age_max_voltage_V",
        "high_voltage_time_h",
        "cold_time_h",
        "hot_time_h",
        "abs_current_ge_1p5C_time_h",
        "cold_high_abs_current_time_h",
    ),
    "SE4_coupled_stress": (
        "capacity_Ah_k",
        "calendar_days",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_mean_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_voltage_V",
        "log_age_max_voltage_V",
        "high_voltage_time_h",
        "cold_time_h",
        "hot_time_h",
        "abs_current_ge_1p5C_time_h",
        "cold_high_abs_current_time_h",
        "high_voltage_hot_time_h",
        "high_soc_hot_time_h",
    ),
}

CATEGORICAL_FEATURES: dict[str, tuple[str, ...]] = {
    "SE0_time_efc": (),
    "SE1_calendar_cycling": (),
    "SE2_temperature_voltage": ("voltage_window_family",),
    "SE3_c_rate_interactions": ("voltage_window_family", "aging_mode"),
    "SE4_coupled_stress": ("voltage_window_family", "aging_mode"),
}


@dataclass(frozen=True)
class SemiEmpiricalEncoder:
    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    impute_values: dict[str, float]
    scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "SemiEmpiricalEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown semi-empirical feature group: {feature_group}")
        leakage = (set(NUMERIC_FEATURES[feature_group]) | set(CATEGORICAL_FEATURES[feature_group])) & TARGET_DERIVED_FORBIDDEN
        if leakage:
            raise ValueError(f"Target-derived features are forbidden: {sorted(leakage)}")
        impute_values: dict[str, float] = {}
        scale_values: dict[str, float] = {}
        for column in NUMERIC_FEATURES[feature_group]:
            finite = [_as_float(row.get(column)) for row in rows]
            finite = [value for value in finite if math.isfinite(value)]
            mean = sum(finite) / len(finite) if finite else 0.0
            variance = sum((value - mean) ** 2 for value in finite) / len(finite) if finite else 0.0
            impute_values[column] = mean
            scale_values[column] = math.sqrt(variance) if variance > 0.0 else 1.0
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

    def transform(self, rows: list[dict[str, Any]]) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                numeric = value if math.isfinite(value) else self.impute_values[column]
                values.append((numeric - self.impute_values[column]) / self.scale_values[column])
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(1.0 if observed == category else 0.0 for category in self.categorical_values[column])
            matrix.append(values)
        return matrix


def run_semi_empirical_baselines(
    interval_table_path: Path,
    interval_subsets_path: Path,
    stress_features_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    *,
    report_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
) -> dict[str, Any]:
    selected_features = _normalize(feature_groups, FEATURE_GROUPS, "feature group")
    selected_targets = _normalize(targets, TARGETS, "target")
    selected_splits = _normalize(split_views, SPLIT_COLUMNS, "split view")
    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
    )
    sensitivity_rows = [row for row in subset_rows if not bool(row["sensitivity_flagged_monotonicity"])]
    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for run_scope, rows in (("primary", subset_rows), ("sensitivity_excluding_monotonicity", sensitivity_rows)):
        for target in selected_targets:
            target_rows = [row for row in rows if math.isfinite(_evaluation_target_value(row, target))]
            for split_name in selected_splits:
                for heldout_fold, train_rows, test_rows in iter_split_instances(target_rows, split_name):
                    assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                    for feature_group in selected_features:
                        fold_predictions = _predict_ridge(train_rows, test_rows, target, feature_group)
                        metrics.append(
                            compute_metrics(
                                test_rows,
                                fold_predictions,
                                target=target,
                                subset_name=subset,
                                run_scope=run_scope,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=MODEL_LEVEL,
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
                                model_level=MODEL_LEVEL,
                                feature_group=feature_group,
                                target=target,
                            )
                        )
    if not metrics:
        raise ValueError("No semi-empirical metrics were generated.")
    resolved_report_dir = report_dir or out_path.with_suffix("").parent / out_path.with_suffix("").name
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA), predictions_out_path)
    leaderboard = _leaderboard_rows(metrics)
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "stress_features": str(stress_features_path),
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(resolved_report_dir),
        },
        "subset": subset,
        "seed": seed,
        "model_level": MODEL_LEVEL,
        "targets": selected_targets,
        "feature_groups": selected_features,
        "split_views": selected_splits,
        "row_counts": _row_counts(all_rows, subset_rows, sensitivity_rows),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_semi_empirical_artifacts(report, leaderboard, resolved_report_dir)
    return report


def render_semi_empirical_artifacts(
    report: dict[str, Any],
    leaderboard: list[dict[str, Any]],
    report_dir: Path,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir / "leaderboard.csv", leaderboard)
    _write_summary(leaderboard, report_dir / "baseline_summary.md")
    _write_claim_readiness(leaderboard, report_dir / "semi_empirical_claim_readiness.md")


def compare_semi_empirical_reports(
    semi_report_path: Path,
    hgb_f4_report_path: Path,
    stress_report_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Compare best semi-empirical groups against HGB F4 and stress reports."""
    semi_report = json.loads(semi_report_path.read_text(encoding="utf-8"))
    hgb_report = json.loads(hgb_f4_report_path.read_text(encoding="utf-8"))
    stress_report = json.loads(stress_report_path.read_text(encoding="utf-8"))
    semi_predictions = _load_prediction_rows(semi_report)
    covered_keys = _all_primary_prediction_keys(semi_predictions)
    metadata = _condition_metadata_by_parameter_set(semi_report)
    semi_rows = _semi_selection_condition_mae_rows(
        semi_predictions,
        allowed_feature_groups=set(FEATURE_GROUPS),
        covered_keys=covered_keys,
        source_report=Path(semi_report["outputs"]["report"]).name,
    )
    f4_rows = _selection_condition_mae_rows(
        _load_prediction_rows(hgb_report),
        allowed_feature_groups={"F4_state_log_age_scalar"},
        covered_keys=covered_keys,
        source_report=Path(hgb_report["outputs"]["report"]).name,
    )
    stress_rows = _selection_condition_mae_rows(
        _load_prediction_rows(stress_report),
        allowed_feature_groups=None,
        covered_keys=covered_keys,
        source_report=Path(stress_report["outputs"]["report"]).name,
        exclude_feature_groups={"F0_time_only", "F1_state_time", "F2_state_exposure", "F3_state_nominal", "F4_state_log_age_scalar"},
    )
    best_semi = _best_selection_by_target_split(semi_rows)
    best_f4 = _best_selection_by_target_split(f4_rows)
    best_stress = _best_selection_by_target_split(stress_rows)
    vs_f4 = _rename_comparison_rows(
        _paired_best_nonpulse_gain_rows(semi_rows, f4_rows, best_semi, best_f4, metadata),
        "hgb_f4",
    )
    vs_stress = _rename_comparison_rows(
        _paired_best_nonpulse_gain_rows(semi_rows, stress_rows, best_semi, best_stress, metadata),
        "best_stress",
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "paired_gain_vs_hgb_f4.csv", vs_f4)
    _write_csv(out_dir / "paired_gain_vs_best_stress.csv", vs_stress)
    summary = _comparison_summary(vs_f4, "hgb_f4") + _comparison_summary(vs_stress, "best_stress")
    _write_csv(out_dir / "semi_empirical_comparison_summary.csv", summary)
    _write_comparison_md(summary, out_dir / "semi_empirical_comparison.md")
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "semi_empirical_report": str(semi_report_path),
            "hgb_f4_report": str(hgb_f4_report_path),
            "stress_report": str(stress_report_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "paired_gain_vs_hgb_f4": str(out_dir / "paired_gain_vs_hgb_f4.csv"),
            "paired_gain_vs_best_stress": str(out_dir / "paired_gain_vs_best_stress.csv"),
            "summary": str(out_dir / "semi_empirical_comparison_summary.csv"),
        },
        "row_counts": {
            "semi_condition_rows": len(semi_rows),
            "paired_vs_hgb_f4": len(vs_f4),
            "paired_vs_best_stress": len(vs_stress),
        },
    }
    (out_dir / "semi_empirical_comparison_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _predict_ridge(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    feature_group: str,
) -> list[dict[str, float | None]]:
    np, Ridge, _ = _import_sklearn_stack()
    encoder = SemiEmpiricalEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows), dtype=float)
    y_train = np.asarray([_evaluation_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")
    model = Ridge(alpha=1.0)
    model.fit(x_train, y_train)
    return [{"y_pred": float(value), "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None} for value in model.predict(x_test)]


def _write_summary(leaderboard: list[dict[str, Any]], path: Path) -> None:
    rows = sorted(
        [row for row in leaderboard if row["run_scope"] == "primary"],
        key=lambda row: float(row["condition_mean_mae"]),
    )[:12]
    lines = [
        "# Semi-Empirical Capacity Baseline Summary",
        "",
        "These are interpretable ridge-style domain comparators, not neural or architecture baselines.",
        "",
        "| Target | Split | Feature group | Condition mean MAE | Worst condition MAE |",
        "|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | `{row['feature_group']}` | "
            f"{_format_diagnostic_value(row['condition_mean_mae'])} | {_format_diagnostic_value(row['worst_condition_mae'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness(leaderboard: list[dict[str, Any]], path: Path) -> None:
    primary = [row for row in leaderboard if row["run_scope"] == "primary"]
    by_target_split = {(row["target"], row["split_name"]): row for row in _best_rows(primary)}
    c_rate_delta = by_target_split.get(("delta_capacity_Ah", "c_rate_holdout_fold"), {})
    c_rate_level = by_target_split.get(("capacity_Ah_k1", "c_rate_holdout_fold"), {})
    lines = [
        "# Semi-Empirical Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
        "| Semi-empirical capacity comparator exists | `supported` | Ridge-style SE0-SE4 baselines ran under grouped validation. |",
        f"| C-rate capacity level | `diagnostic_only` | Best condition-mean MAE {_format_diagnostic_value(c_rate_level.get('condition_mean_mae'))}. |",
        f"| C-rate fade target | `diagnostic_only` | Best condition-mean MAE {_format_diagnostic_value(c_rate_delta.get('condition_mean_mae'))}. |",
        "| Architecture readiness | `blocked` | Semi-empirical and replicate-aware gates are comparators, not architecture authorization. |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _best_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["target"]), str(row["split_name"])), []).append(row)
    return [min(group, key=lambda row: (float(row["condition_mean_mae"]), float(row["worst_condition_mae"]))) for group in grouped.values()]


def _rename_comparison_rows(rows: list[dict[str, Any]], reference: str) -> list[dict[str, Any]]:
    renamed = []
    for row in rows:
        output = dict(row)
        output["semi_empirical_feature_group"] = output.pop("prior_pulse_feature_group")
        output["semi_empirical_source_report"] = output.pop("prior_pulse_source_report")
        output["reference_feature_group"] = output.pop("best_nonpulse_feature_group")
        output["reference_source_report"] = output.pop("best_nonpulse_source_report")
        output["reference_condition_mae"] = output.pop("best_nonpulse_condition_mae")
        output["semi_empirical_condition_mae"] = output.pop("prior_pulse_condition_mae")
        output["reference"] = reference
        renamed.append(output)
    return renamed


def _semi_selection_condition_mae_rows(
    prediction_rows: list[dict[str, Any]],
    *,
    allowed_feature_groups: set[str],
    covered_keys: set[tuple[str, str, int, str, int, int]],
    source_report: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, int, str, str, str], list[float]] = {}
    for row in prediction_rows:
        if str(row.get("run_scope")) != "primary":
            continue
        feature_group = str(row["feature_group"])
        if feature_group not in allowed_feature_groups:
            continue
        key = (
            str(row["target"]),
            str(row["split_name"]),
            int(row["parameter_set"]),
            str(row["cell_id"]),
            int(row["checkup_k"]),
            int(row["checkup_k_next"]),
        )
        if key not in covered_keys:
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        group_key = (
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
            str(row["model_level"]),
            feature_group,
            source_report,
        )
        grouped.setdefault(group_key, []).append(abs(y_pred - y_true))
    rows = []
    for (
        target,
        split_name,
        heldout_fold,
        parameter_set,
        model_level,
        feature_group,
        source_report,
    ), errors in sorted(grouped.items()):
        rows.append(
            {
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "parameter_set": parameter_set,
                "model_level": model_level,
                "feature_group": feature_group,
                "source_report": source_report,
                "condition_mae": sum(errors) / len(errors),
                "n_intervals": len(errors),
            }
        )
    return rows


def _comparison_summary(rows: list[dict[str, Any]], reference: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["target"]), str(row["split_name"])), []).append(row)
    summary = []
    for (target, split_name), group in sorted(grouped.items()):
        gains = [float(row["gain"]) for row in group]
        summary.append(
            {
                "reference": reference,
                "target": target,
                "split_name": split_name,
                "semi_empirical_feature_group": group[0]["semi_empirical_feature_group"],
                "reference_feature_group": group[0]["reference_feature_group"],
                "n_conditions": len(group),
                "mean_gain_reference_minus_semi": sum(gains) / len(gains),
                "median_gain_reference_minus_semi": sorted(gains)[len(gains) // 2],
                "win_rate_semi_beats_reference": sum(1 for gain in gains if gain > 0) / len(gains),
                "worst_condition_gain": min(gains),
            }
        )
    return summary


def _write_comparison_md(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Semi-Empirical Baseline Comparison",
        "",
        "Positive gain means the semi-empirical ridge comparator has lower condition MAE than the reference.",
        "",
        "| Reference | Target | Split | Semi group | Reference group | Conditions | Mean gain | Win rate |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['reference']}` | `{row['target']}` | `{row['split_name']}` | "
            f"`{row['semi_empirical_feature_group']}` | `{row['reference_feature_group']}` | {row['n_conditions']} | "
            f"{_format_diagnostic_value(row['mean_gain_reference_minus_semi'])} | "
            f"{_format_diagnostic_value(row['win_rate_semi_beats_reference'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _normalize(values: list[str] | None, allowed: tuple[str, ...], label: str) -> list[str]:
    selected = list(allowed if values is None else values)
    unknown = [value for value in selected if value not in allowed]
    if unknown:
        raise ValueError(f"Unknown {label}: {unknown}. Expected one of {allowed}.")
    return selected


def _category(value: Any) -> str:
    return "missing" if value is None or value == "" else str(value)


def _import_sklearn_stack() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Semi-empirical baselines require numpy and scikit-learn. "
            "Install the baseline optional dependencies."
        ) from exc
    return np, Ridge, HistGradientBoostingRegressor
