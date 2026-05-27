"""C-rate generalization root-cause diagnostics.

This module consumes existing prediction artifacts only. It does not train
models, add feature engineering, recommend policies, or make causal claims.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from mbp.analysis.support_reliability import condition_support_rows

SCHEMA_VERSION = "gate84.c_rate_generalization.v1"
PRIMARY_SPLIT = "c_rate_holdout_fold"
PRIMARY_TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")
PRIMARY_MODEL = "L2_hist_gradient_boosting"
PRIMARY_FEATURE_FALLBACKS = (
    "F8_timestamp_weighted_stress",
    "F4_state_log_age_scalar",
    "F10_c_rate_v1_1",
    "F7_c_rate_focused",
)
IDENTITY_KEYS = ("cell_id", "parameter_set", "replicate_id", "checkup_k", "checkup_k_next")
CONDITION_FIELDS = (
    "aging_mode",
    "nominal_temperature_C",
    "voltage_window_family",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
    "profile_label",
)
LEAKAGE_STRESS_FIELDS = {
    "delta_capacity_per_day",
    "delta_capacity_per_efc",
    "delta_capacity_per_Ah_throughput",
}
STRESS_FIELDS_OF_INTEREST = (
    "cold_time_h",
    "hot_time_h",
    "high_voltage_time_h",
    "high_soc_time_h",
    "abs_current_ge_1C_time_h",
    "abs_current_ge_1p5C_time_h",
    "charge_current_ge_1C_time_h",
    "cold_high_charge_time_h",
    "cold_high_abs_current_time_h",
    "high_voltage_high_abs_current_time_h",
    "high_soc_high_abs_current_time_h",
    "max_abs_current_ge_1C_event_h",
    "max_cold_high_abs_current_event_h",
    "stress_coverage_fraction",
    "max_log_age_gap_s",
)


def diagnose_c_rate_generalization(
    capacity_report_path: Path,
    predictions_path: Path,
    interval_table_path: Path,
    out_dir: Path,
    *,
    stress_features_path: Path | None = None,
) -> dict[str, Any]:
    """Diagnose C-rate generalization failure modes from existing artifacts."""
    if not capacity_report_path.exists():
        raise FileNotFoundError(f"Missing capacity report: {capacity_report_path}")
    if not predictions_path.exists():
        raise FileNotFoundError(f"Missing capacity predictions: {predictions_path}")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Missing interval table: {interval_table_path}")
    if stress_features_path is not None and not stress_features_path.exists():
        raise FileNotFoundError(f"Missing stress features: {stress_features_path}")

    report = json.loads(capacity_report_path.read_text(encoding="utf-8"))
    metrics = list(report.get("metrics", []))
    predictions = pq.read_table(predictions_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    stress_rows = pq.read_table(stress_features_path).to_pylist() if stress_features_path else []
    if not metrics:
        raise ValueError("Capacity report has no metrics.")
    if not predictions:
        raise ValueError("Capacity prediction table is empty.")
    if not interval_rows:
        raise ValueError("Interval table is empty.")

    condition_lookup = _condition_lookup(interval_rows)
    support_rows = [row for row in condition_support_rows(interval_rows) if row["split_name"] == PRIMARY_SPLIT]
    support_lookup = {int(row["parameter_set"]): row for row in support_rows}
    primary_feature_group = _select_primary_feature_group(metrics)

    metric_summary_rows = c_rate_metric_summary_rows(metrics)
    hotspot_rows = c_rate_condition_hotspot_rows(predictions, condition_lookup, support_lookup)
    support_overlap_rows = c_rate_support_overlap_rows(support_rows)
    stress_error_rows = c_rate_stress_error_rows(
        predictions,
        stress_rows,
        condition_lookup,
        primary_feature_group=primary_feature_group,
    )
    readiness_rows = c_rate_claim_readiness_rows(
        metric_summary_rows=metric_summary_rows,
        hotspot_rows=hotspot_rows,
        support_overlap_rows=support_overlap_rows,
        stress_error_rows=stress_error_rows,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "c_rate_metric_summary.csv", metric_summary_rows)
    _write_csv(out_dir / "c_rate_condition_hotspots.csv", hotspot_rows)
    _write_csv(out_dir / "c_rate_support_overlap.csv", support_overlap_rows)
    _write_csv(plots_dir / "c_rate_stress_error_bins.csv", stress_error_rows)
    _write_csv(plots_dir / "c_rate_claim_readiness.csv", readiness_rows)
    _write_summary_markdown(
        out_dir / "c_rate_failure_summary.md",
        report=report,
        primary_feature_group=primary_feature_group,
        metric_summary_rows=metric_summary_rows,
        hotspot_rows=hotspot_rows,
        support_overlap_rows=support_overlap_rows,
        stress_error_rows=stress_error_rows,
        readiness_rows=readiness_rows,
    )
    _write_claim_readiness_markdown(out_dir / "c_rate_claim_readiness.md", readiness_rows)

    result = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "capacity_report": str(capacity_report_path),
            "predictions": str(predictions_path),
            "interval_table": str(interval_table_path),
            "stress_features": str(stress_features_path) if stress_features_path else None,
        },
        "primary_split": PRIMARY_SPLIT,
        "primary_feature_group": primary_feature_group,
        "row_counts": {
            "metrics": len(metrics),
            "predictions": len(predictions),
            "interval_rows": len(interval_rows),
            "stress_feature_rows": len(stress_rows),
            "metric_summary_rows": len(metric_summary_rows),
            "condition_hotspot_rows": len(hotspot_rows),
            "support_overlap_rows": len(support_overlap_rows),
            "stress_error_rows": len(stress_error_rows),
            "readiness_rows": len(readiness_rows),
        },
        "readiness": {str(row["claim_area"]): str(row["status"]) for row in readiness_rows},
        "outputs": {
            "report": str(out_dir / "c_rate_failure_report.json"),
            "summary": str(out_dir / "c_rate_failure_summary.md"),
            "condition_hotspots": str(out_dir / "c_rate_condition_hotspots.csv"),
            "support_overlap": str(out_dir / "c_rate_support_overlap.csv"),
            "stress_error_bins": str(plots_dir / "c_rate_stress_error_bins.csv"),
            "claim_readiness": str(out_dir / "c_rate_claim_readiness.md"),
        },
        "claim_scope": "c_rate_root_cause_diagnostics_only_no_new_model_no_architecture_no_policy_no_causal_claim",
    }
    (out_dir / "c_rate_failure_report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def c_rate_metric_summary_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize C-rate metric rows by target/model/feature group."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metrics:
        if str(row.get("split_name")) != PRIMARY_SPLIT:
            continue
        if str(row.get("target")) not in PRIMARY_TARGETS:
            continue
        grouped[(str(row["target"]), str(row["model_level"]), str(row["feature_group"]))].append(row)

    output = []
    for (target, model_level, feature_group), rows in sorted(grouped.items()):
        output.append(
            {
                "target": target,
                "model_level": model_level,
                "feature_group": feature_group,
                "fold_rows": len(rows),
                "test_rows": sum(_as_int(row.get("test_rows")) for row in rows),
                "test_parameter_sets": sum(_as_int(row.get("test_parameter_sets")) for row in rows),
                "mean_mae": _mean([_as_float(row.get("mae")) for row in rows]),
                "mean_condition_mean_mae": _mean(
                    [_as_float(row.get("condition_mean_mae")) for row in rows]
                ),
                "max_worst_condition_mae": _max(
                    [_as_float(row.get("worst_condition_mae")) for row in rows]
                ),
                "claim_scope": "c_rate_metric_diagnostic",
            }
        )
    return output


def c_rate_condition_hotspot_rows(
    prediction_rows: list[dict[str, Any]],
    condition_lookup: dict[int, dict[str, Any]],
    support_lookup: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate C-rate prediction errors by condition and candidate model row."""
    grouped: dict[tuple[str, str, str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in prediction_rows:
        if str(row.get("split_name")) != PRIMARY_SPLIT:
            continue
        if str(row.get("target")) not in PRIMARY_TARGETS:
            continue
        if str(row.get("run_scope", "primary")) != "primary":
            continue
        key = (
            str(row["target"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            _as_int(row.get("heldout_fold")),
            _as_int(row.get("parameter_set")),
        )
        grouped[key].append(row)

    output = []
    for (target, model_level, feature_group, heldout_fold, parameter_set), rows in sorted(grouped.items()):
        errors = [_as_float(row.get("y_pred")) - _as_float(row.get("y_true")) for row in rows]
        abs_errors = [abs(value) for value in errors]
        condition = condition_lookup.get(parameter_set, {})
        support = support_lookup.get(parameter_set, {})
        output.append(
            {
                "target": target,
                "model_level": model_level,
                "feature_group": feature_group,
                "heldout_fold": heldout_fold,
                "parameter_set": parameter_set,
                **_condition_fields(condition),
                "rows": len(rows),
                "cells": len({str(row["cell_id"]) for row in rows}),
                "mae": _mean(abs_errors),
                "rmse": math.sqrt(_mean([value * value for value in errors])),
                "mean_signed_error": _mean(errors),
                "median_abs_error": _median(abs_errors),
                "mean_y_true": _mean([_as_float(row.get("y_true")) for row in rows]),
                "mean_y_pred": _mean([_as_float(row.get("y_pred")) for row in rows]),
                "support_score": _as_float(support.get("support_score")),
                "nearest_distance": _as_float(support.get("nearest_distance")),
                "nearest_parameter_set": support.get("nearest_parameter_set"),
                "same_stressor_support_count": _as_int(support.get("same_stressor_support_count")),
                "exact_nominal_match_count": _as_int(support.get("exact_nominal_match_count")),
                "claim_scope": "condition_error_hotspot_diagnostic",
            }
        )
    return sorted(output, key=lambda row: (-_as_float(row["mae"]), row["target"], row["model_level"]))


def c_rate_support_overlap_rows(support_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format train-only C-rate support overlap diagnostics."""
    output = []
    for row in sorted(support_rows, key=lambda item: (int(item["heldout_fold"]), int(item["parameter_set"]))):
        output.append(
            {
                "split_name": PRIMARY_SPLIT,
                "heldout_fold": _as_int(row.get("heldout_fold")),
                "parameter_set": _as_int(row.get("parameter_set")),
                **_condition_fields(row),
                "train_conditions": _as_int(row.get("train_conditions")),
                "nearest_parameter_set": row.get("nearest_parameter_set"),
                "nearest_distance": _as_float(row.get("nearest_distance")),
                "support_score": _as_float(row.get("support_score")),
                "same_stressor_support_count": _as_int(row.get("same_stressor_support_count")),
                "exact_nominal_match_count": _as_int(row.get("exact_nominal_match_count")),
                "low_support_flag": _as_float(row.get("support_score")) < 0.5,
                "claim_scope": "train_only_c_rate_support_overlap_diagnostic",
            }
        )
    return output


def c_rate_stress_error_rows(
    prediction_rows: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
    condition_lookup: dict[int, dict[str, Any]],
    *,
    primary_feature_group: str,
) -> list[dict[str, Any]]:
    """Compare stress-feature exposure levels in high-error versus lower-error C-rate rows."""
    if not stress_rows:
        return []
    stress_lookup = {_row_key(row): row for row in stress_rows}
    joined = []
    for row in prediction_rows:
        if str(row.get("split_name")) != PRIMARY_SPLIT:
            continue
        if str(row.get("model_level")) != PRIMARY_MODEL:
            continue
        if str(row.get("feature_group")) != primary_feature_group:
            continue
        if str(row.get("target")) not in PRIMARY_TARGETS:
            continue
        stress = stress_lookup.get(_row_key(row))
        if not stress:
            continue
        error = abs(_as_float(row.get("y_pred")) - _as_float(row.get("y_true")))
        joined.append((row, stress, error))
    if not joined:
        return []

    output = []
    available_fields = [
        field for field in STRESS_FIELDS_OF_INTEREST if field in joined[0][1] and field not in LEAKAGE_STRESS_FIELDS
    ]
    for target in PRIMARY_TARGETS:
        target_rows = [(row, stress, error) for row, stress, error in joined if str(row.get("target")) == target]
        if len(target_rows) < 4:
            continue
        threshold = _quantile([error for _, _, error in target_rows], 0.75)
        high_error = [(row, stress, error) for row, stress, error in target_rows if error >= threshold]
        lower_error = [(row, stress, error) for row, stress, error in target_rows if error < threshold]
        for field in available_fields:
            high_values = [_as_float(stress.get(field)) for _, stress, _ in high_error]
            lower_values = [_as_float(stress.get(field)) for _, stress, _ in lower_error]
            output.append(
                {
                    "target": target,
                    "model_level": PRIMARY_MODEL,
                    "feature_group": primary_feature_group,
                    "stress_feature": field,
                    "high_error_threshold_mae": threshold,
                    "high_error_rows": len(high_error),
                    "lower_error_rows": len(lower_error),
                    "high_error_mean_feature": _mean(high_values),
                    "lower_error_mean_feature": _mean(lower_values),
                    "mean_feature_difference": _mean(high_values) - _mean(lower_values),
                    "high_error_mean_mae": _mean([error for _, _, error in high_error]),
                    "lower_error_mean_mae": _mean([error for _, _, error in lower_error]),
                    "high_error_conditions": len({int(row["parameter_set"]) for row, _, _ in high_error}),
                    "lower_error_conditions": len({int(row["parameter_set"]) for row, _, _ in lower_error}),
                    "dominant_high_error_conditions": _dominant_conditions(high_error, condition_lookup),
                    "claim_scope": "stress_error_association_diagnostic_not_causal",
                }
            )
    return sorted(output, key=lambda row: abs(_as_float(row["mean_feature_difference"])), reverse=True)


def c_rate_claim_readiness_rows(
    *,
    metric_summary_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
    support_overlap_rows: list[dict[str, Any]],
    stress_error_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Render conservative claim-readiness statuses for the diagnostic gate."""
    low_support = [row for row in support_overlap_rows if row.get("low_support_flag")]
    return [
        {
            "claim_area": "C-rate root-cause diagnostics",
            "status": "supported_for_diagnostics" if hotspot_rows and metric_summary_rows else "not_supported",
            "evidence": f"{len(hotspot_rows)} condition-hotspot rows and {len(metric_summary_rows)} C-rate metric summary rows.",
            "forbidden_wording": "C-rate generalization is solved.",
        },
        {
            "claim_area": "train-only C-rate support overlap",
            "status": "supported_for_diagnostics" if support_overlap_rows else "not_supported",
            "evidence": f"{len(low_support)} of {len(support_overlap_rows)} C-rate condition rows have support_score < 0.5.",
            "forbidden_wording": "Support diagnostics prove out-of-distribution robustness.",
        },
        {
            "claim_area": "stress-feature error association",
            "status": "supported_for_diagnostics" if stress_error_rows else "not_supported",
            "evidence": f"{len(stress_error_rows)} stress-feature high-error association rows.",
            "forbidden_wording": "Stress associations are causal mechanisms.",
        },
        {
            "claim_area": "new C-rate repair model readiness",
            "status": "blocked",
            "evidence": "This gate is report-only and trains no repair model.",
            "forbidden_wording": "A new repair model is authorized or validated by this report alone.",
        },
        {
            "claim_area": "architecture or policy readiness",
            "status": "blocked",
            "evidence": "The report contains no neural, sequence, CBAT, policy-ranking, or causal evidence.",
            "forbidden_wording": "CBAT, policy ranking, causal claims, or broad architecture work is justified.",
        },
    ]


def _select_primary_feature_group(metrics: list[dict[str, Any]]) -> str:
    available = {str(row.get("feature_group")) for row in metrics}
    for feature_group in PRIMARY_FEATURE_FALLBACKS:
        if feature_group in available:
            return feature_group
    return sorted(available)[0] if available else ""


def _condition_lookup(interval_rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    lookup = {}
    for row in interval_rows:
        parameter_set = _as_int(row.get("parameter_set"))
        if parameter_set not in lookup:
            lookup[parameter_set] = row
    return lookup


def _condition_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in CONDITION_FIELDS}


def _row_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(key) for key in IDENTITY_KEYS)


def _dominant_conditions(
    rows: list[tuple[dict[str, Any], dict[str, Any], float]],
    condition_lookup: dict[int, dict[str, Any]],
    *,
    limit: int = 5,
) -> str:
    counts: dict[int, int] = defaultdict(int)
    for prediction, _, _ in rows:
        counts[int(prediction["parameter_set"])] += 1
    labels = []
    for parameter_set, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        condition = condition_lookup.get(parameter_set, {})
        labels.append(
            f"P{parameter_set}:n={count},T={condition.get('nominal_temperature_C')},"
            f"C={condition.get('nominal_charge_C_rate')}/{condition.get('nominal_discharge_C_rate')},"
            f"V={condition.get('voltage_window_family')}"
        )
    return "; ".join(labels)


def _write_summary_markdown(
    path: Path,
    *,
    report: dict[str, Any],
    primary_feature_group: str,
    metric_summary_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
    support_overlap_rows: list[dict[str, Any]],
    stress_error_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> None:
    primary_hotspots = [row for row in hotspot_rows if row.get("model_level") == PRIMARY_MODEL]
    top_hotspots = (primary_hotspots or hotspot_rows)[:10]
    low_support = [row for row in support_overlap_rows if row.get("low_support_flag")]
    lines = [
        "# C-Rate Generalization Root-Cause Diagnostics",
        "",
        "## Scope",
        "",
        "This is a report-only diagnostic over existing capacity prediction artifacts. It does not train models, add feature engineering, recommend policies, or make causal claims.",
        "",
        "## Inputs",
        "",
        f"- Report schema: `{report.get('schema_version', 'unknown')}`",
        f"- Primary split: `{PRIMARY_SPLIT}`",
        f"- Primary model for stress-error associations: `{PRIMARY_MODEL}`",
        f"- Primary feature group for stress-error associations: `{primary_feature_group}`",
        "",
        "## Summary",
        "",
        f"- C-rate metric summary rows: `{len(metric_summary_rows)}`",
        f"- Condition hotspot rows: `{len(hotspot_rows)}`",
        f"- Support-overlap rows: `{len(support_overlap_rows)}`",
        f"- Low-support condition rows: `{len(low_support)}`",
        f"- Stress-error association rows: `{len(stress_error_rows)}`",
        "",
        "## Top Condition Hotspots",
        "",
        "| Target | Model | Feature group | Parameter set | MAE | Support score | Temperature | C-rate | Voltage/profile |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in top_hotspots:
        lines.append(
            "| {target} | {model_level} | {feature_group} | {parameter_set} | {mae:.6g} | {support_score:.6g} | {temp} | {charge}/{discharge} | {voltage}/{profile} |".format(
                target=row["target"],
                model_level=row["model_level"],
                feature_group=row["feature_group"],
                parameter_set=row["parameter_set"],
                mae=_as_float(row["mae"]),
                support_score=_as_float(row["support_score"]),
                temp=row.get("nominal_temperature_C"),
                charge=row.get("nominal_charge_C_rate"),
                discharge=row.get("nominal_discharge_C_rate"),
                voltage=row.get("voltage_window_family"),
                profile=row.get("profile_label"),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Readiness",
            "",
            "| Claim area | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for row in readiness_rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The output identifies where C-rate transfer fails and whether failures align with train-only support gaps or stress-exposure regimes. It is not a repair model and does not relax any existing guardrail.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# C-Rate Generalization Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Forbidden wording |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} | {row['forbidden_wording']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _as_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _mean(values: list[float]) -> float:
    finite = _finite(values)
    return sum(finite) / len(finite) if finite else math.nan


def _median(values: list[float]) -> float:
    finite = sorted(_finite(values))
    if not finite:
        return math.nan
    mid = len(finite) // 2
    if len(finite) % 2:
        return finite[mid]
    return (finite[mid - 1] + finite[mid]) / 2.0


def _max(values: list[float]) -> float:
    finite = _finite(values)
    return max(finite) if finite else math.nan


def _quantile(values: list[float], q: float) -> float:
    finite = sorted(_finite(values))
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    pos = (len(finite) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return finite[lower]
    frac = pos - lower
    return finite[lower] * (1.0 - frac) + finite[upper] * frac
