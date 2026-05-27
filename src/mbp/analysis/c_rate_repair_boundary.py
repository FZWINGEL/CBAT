"""C-rate repair boundary and transfer diagnostics.

This module checks whether the narrow C-rate repair evidence remains bounded to
`delta_capacity_Ah` or transfers to `capacity_Ah_k1`. It consumes existing
non-neural stressor-robust reports and prediction Parquets; it does not train
models, engineer features, recommend policies, or make causal claims.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
import random
from typing import Any

import pyarrow.parquet as pq

SCHEMA_VERSION = "gate86.c_rate_repair_boundary.v1"
PRIMARY_SPLIT = "c_rate_holdout_fold"
GUARDRAIL_MAX_OUTSIDE_DEGRADATION = 0.05
LOW_SUPPORT_THRESHOLD = 0.5
TARGETS = ("delta_capacity_Ah", "capacity_Ah_k1")

ADAPTIVE_METHOD_ID = "adaptive_R2_F8_conservative"
ADAPTIVE_SETTING_ID = "R5_train_only_stressor_selected_hgb"
ADAPTIVE_FEATURE_GROUP = "F8_timestamp_weighted_stress"
REFERENCE_SETTING_ID = "R0_reference_hgb50"
REFERENCE_F4 = "F4_state_log_age_scalar"
REFERENCE_STRESS = "F8_timestamp_weighted_stress"

ROUTER_METHOD_ID = "targeted_router_D2_F4"
ROUTER_SETTING_ID = "R6_train_only_arm_selector_hgb"
ROUTER_FEATURE_GROUP = "train_only_arm_selector"


def diagnose_c_rate_repair_boundary(
    adaptive_report_path: Path,
    adaptive_predictions_path: Path,
    arm_selector_report_path: Path,
    arm_selector_predictions_path: Path,
    out_dir: Path,
    *,
    support_overlap_path: Path | None = None,
) -> dict[str, Any]:
    """Diagnose target boundaries for the existing non-neural C-rate repair."""
    adaptive_report = _read_json(adaptive_report_path, "adaptive stressor-robust report")
    arm_selector_report = _read_json(arm_selector_report_path, "arm-selector report")
    adaptive_predictions = _read_parquet_rows(adaptive_predictions_path, "adaptive predictions")
    arm_selector_predictions = _read_parquet_rows(arm_selector_predictions_path, "arm-selector predictions")
    support_rows = _read_csv(support_overlap_path) if support_overlap_path else []

    target_rows = c_rate_repair_boundary_target_rows(
        adaptive_report=adaptive_report,
        adaptive_predictions=adaptive_predictions,
        arm_selector_report=arm_selector_report,
        arm_selector_predictions=arm_selector_predictions,
    )
    split_rows = c_rate_repair_boundary_split_rows(
        adaptive_report=adaptive_report,
        arm_selector_report=arm_selector_report,
    )
    support_gain_rows = c_rate_repair_support_stratum_gain_rows(
        support_rows=support_rows,
        adaptive_predictions=adaptive_predictions,
        arm_selector_predictions=arm_selector_predictions,
    )
    readiness_rows = c_rate_repair_boundary_claim_readiness_rows(
        target_rows=target_rows,
        support_gain_rows=support_gain_rows,
    )
    readiness = {str(row["claim_area"]): str(row["status"]) for row in readiness_rows}

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "target_boundary_matrix.csv", target_rows)
    _write_csv(plots_dir / "split_guardrail_matrix.csv", split_rows)
    _write_csv(plots_dir / "support_stratum_gain_matrix.csv", support_gain_rows)
    _write_claim_readiness_md(out_dir / "c_rate_repair_boundary_claim_readiness.md", readiness_rows)
    _write_decision_md(
        out_dir / "c_rate_repair_boundary_decision.md",
        target_rows=target_rows,
        split_rows=split_rows,
        support_gain_rows=support_gain_rows,
        readiness_rows=readiness_rows,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "adaptive_report": str(adaptive_report_path),
            "adaptive_predictions": str(adaptive_predictions_path),
            "arm_selector_report": str(arm_selector_report_path),
            "arm_selector_predictions": str(arm_selector_predictions_path),
            "support_overlap": str(support_overlap_path) if support_overlap_path else None,
        },
        "outputs": {
            "report": str(out_dir / "c_rate_repair_boundary_report.json"),
            "decision": str(out_dir / "c_rate_repair_boundary_decision.md"),
            "claim_readiness": str(out_dir / "c_rate_repair_boundary_claim_readiness.md"),
            "target_boundary_matrix": str(plots_dir / "target_boundary_matrix.csv"),
            "split_guardrail_matrix": str(plots_dir / "split_guardrail_matrix.csv"),
            "support_stratum_gain_matrix": str(plots_dir / "support_stratum_gain_matrix.csv"),
        },
        "guardrail_max_outside_degradation": GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
        "primary_split": PRIMARY_SPLIT,
        "targets": list(TARGETS),
        "row_counts": {
            "target_boundary_rows": len(target_rows),
            "split_guardrail_rows": len(split_rows),
            "support_stratum_gain_rows": len(support_gain_rows),
            "claim_readiness_rows": len(readiness_rows),
        },
        "readiness": readiness,
        "claim_scope": _claim_scope(readiness),
    }
    (out_dir / "c_rate_repair_boundary_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def c_rate_repair_boundary_target_rows(
    *,
    adaptive_report: dict[str, Any],
    adaptive_predictions: list[dict[str, Any]],
    arm_selector_report: dict[str, Any],
    arm_selector_predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return target-level boundary rows for adaptive and router diagnostics."""
    rows: list[dict[str, Any]] = []
    adaptive_leakage = _adaptive_leakage_status(adaptive_report)
    for target in _targets_present(adaptive_report.get("metrics", [])):
        candidate = _mean_metric(
            adaptive_report.get("metrics", []),
            target=target,
            split_name=PRIMARY_SPLIT,
            model_setting_id=ADAPTIVE_SETTING_ID,
            feature_group=ADAPTIVE_FEATURE_GROUP,
        )
        ref_f4 = _mean_metric(
            adaptive_report.get("metrics", []),
            target=target,
            split_name=PRIMARY_SPLIT,
            model_setting_id=REFERENCE_SETTING_ID,
            feature_group=REFERENCE_F4,
        )
        ref_stress = _mean_metric(
            adaptive_report.get("metrics", []),
            target=target,
            split_name=PRIMARY_SPLIT,
            model_setting_id=REFERENCE_SETTING_ID,
            feature_group=REFERENCE_STRESS,
        )
        gain_vs_f4 = _sub(ref_f4, candidate)
        gain_vs_stress = _sub(ref_stress, candidate)
        p05_vs_f4 = _paired_condition_gain_p05(
            adaptive_predictions,
            target=target,
            split_name=PRIMARY_SPLIT,
            candidate_setting=ADAPTIVE_SETTING_ID,
            candidate_feature=ADAPTIVE_FEATURE_GROUP,
            reference_setting=REFERENCE_SETTING_ID,
            reference_feature=REFERENCE_F4,
        )
        p05_vs_stress = _paired_condition_gain_p05(
            adaptive_predictions,
            target=target,
            split_name=PRIMARY_SPLIT,
            candidate_setting=ADAPTIVE_SETTING_ID,
            candidate_feature=ADAPTIVE_FEATURE_GROUP,
            reference_setting=REFERENCE_SETTING_ID,
            reference_feature=REFERENCE_STRESS,
        )
        max_degradation, outside_rows = _adaptive_max_outside_degradation(adaptive_report, target)
        passes = (
            adaptive_leakage == "passed"
            and _positive(gain_vs_f4)
            and _positive(gain_vs_stress)
            and _positive(p05_vs_f4)
            and _positive(p05_vs_stress)
            and _finite_le(max_degradation, GUARDRAIL_MAX_OUTSIDE_DEGRADATION)
        )
        rows.append(
            {
                "method_id": ADAPTIVE_METHOD_ID,
                "target": target,
                "primary_split": PRIMARY_SPLIT,
                "candidate_setting": ADAPTIVE_SETTING_ID,
                "reference_setting": REFERENCE_SETTING_ID,
                "reference_feature_group": REFERENCE_STRESS,
                "candidate_c_rate_condition_mean_mae": candidate,
                "reference_f4_c_rate_condition_mean_mae": ref_f4,
                "reference_stress_c_rate_condition_mean_mae": ref_stress,
                "c_rate_gain_vs_f4": gain_vs_f4,
                "c_rate_gain_vs_stress_reference": gain_vs_stress,
                "paired_p05_vs_f4": p05_vs_f4,
                "paired_p05_vs_stress_reference": p05_vs_stress,
                "max_other_split_relative_degradation": max_degradation,
                "outside_split_rows": outside_rows,
                "leakage_audit": adaptive_leakage,
                "passes_boundary": passes,
                "claim_scope": "train_only_adaptive_non_neural_boundary_diagnostic",
            }
        )

    selector_leakage = str(arm_selector_report.get("leakage_audit", {}).get("status", "not_run"))
    for target in sorted({str(row["target"]) for row in arm_selector_report.get("comparison_rows", [])}):
        primary = _selector_comparison(arm_selector_report, target=target, split_name=PRIMARY_SPLIT)
        outside = _selector_outside(arm_selector_report, target=target)
        gain = _as_float(primary.get("condition_mean_mae_gain")) if primary else math.nan
        p05 = _as_float(primary.get("paired_p05")) if primary else math.nan
        candidate_mae = _as_float(primary.get("candidate_condition_mean_mae")) if primary else math.nan
        reference_mae = _as_float(primary.get("reference_condition_mean_mae")) if primary else math.nan
        max_degradation = (
            _as_float(outside.get("max_other_split_relative_degradation")) if outside else math.nan
        )
        passes = (
            selector_leakage == "passed"
            and _positive(gain)
            and _positive(p05)
            and _finite_le(max_degradation, GUARDRAIL_MAX_OUTSIDE_DEGRADATION)
        )
        rows.append(
            {
                "method_id": ROUTER_METHOD_ID,
                "target": target,
                "primary_split": PRIMARY_SPLIT,
                "candidate_setting": ROUTER_SETTING_ID,
                "reference_setting": "D0_R0_F4_reference",
                "reference_feature_group": REFERENCE_F4,
                "candidate_c_rate_condition_mean_mae": candidate_mae,
                "reference_f4_c_rate_condition_mean_mae": reference_mae,
                "reference_stress_c_rate_condition_mean_mae": math.nan,
                "c_rate_gain_vs_f4": gain,
                "c_rate_gain_vs_stress_reference": math.nan,
                "paired_p05_vs_f4": p05,
                "paired_p05_vs_stress_reference": math.nan,
                "max_other_split_relative_degradation": max_degradation,
                "outside_split_rows": int(outside.get("outside_split_rows", 0)) if outside else 0,
                "leakage_audit": selector_leakage,
                "passes_boundary": passes,
                "claim_scope": "targeted_report_based_router_boundary_diagnostic",
            }
        )
    return sorted(rows, key=lambda row: (str(row["target"]), str(row["method_id"])))


def c_rate_repair_boundary_split_rows(
    *,
    adaptive_report: dict[str, Any],
    arm_selector_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return split-level guardrail rows for each target and method."""
    rows: list[dict[str, Any]] = []
    for target in _targets_present(adaptive_report.get("metrics", [])):
        for split_name in _splits_present(adaptive_report.get("metrics", [])):
            candidate = _mean_metric(
                adaptive_report.get("metrics", []),
                target=target,
                split_name=split_name,
                model_setting_id=ADAPTIVE_SETTING_ID,
                feature_group=ADAPTIVE_FEATURE_GROUP,
            )
            reference = _mean_metric(
                adaptive_report.get("metrics", []),
                target=target,
                split_name=split_name,
                model_setting_id=REFERENCE_SETTING_ID,
                feature_group=ADAPTIVE_FEATURE_GROUP,
            )
            rows.append(
                _split_guardrail_row(
                    method_id=ADAPTIVE_METHOD_ID,
                    target=target,
                    split_name=split_name,
                    candidate_setting=ADAPTIVE_SETTING_ID,
                    reference_setting=REFERENCE_SETTING_ID,
                    candidate_condition_mean_mae=candidate,
                    reference_condition_mean_mae=reference,
                )
            )
    for row in arm_selector_report.get("comparison_rows", []):
        rows.append(
            {
                "method_id": ROUTER_METHOD_ID,
                "target": row.get("target"),
                "split_name": row.get("split_name"),
                "candidate_setting": ROUTER_SETTING_ID,
                "reference_setting": "D0_R0_F4_reference",
                "candidate_condition_mean_mae": _as_float(row.get("candidate_condition_mean_mae")),
                "reference_condition_mean_mae": _as_float(row.get("reference_condition_mean_mae")),
                "condition_mean_mae_gain": _as_float(row.get("condition_mean_mae_gain")),
                "relative_degradation": _as_float(row.get("relative_degradation")),
                "passes_non_degradation_guardrail": (
                    row.get("split_name") == PRIMARY_SPLIT
                    or _finite_le(row.get("relative_degradation"), GUARDRAIL_MAX_OUTSIDE_DEGRADATION)
                ),
                "claim_scope": "split_guardrail_diagnostic",
            }
        )
    return sorted(rows, key=lambda row: (str(row["target"]), str(row["method_id"]), str(row["split_name"])))


def c_rate_repair_support_stratum_gain_rows(
    *,
    support_rows: list[dict[str, Any]],
    adaptive_predictions: list[dict[str, Any]],
    arm_selector_predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize C-rate condition gains by train-only support stratum."""
    if not support_rows:
        return []
    support_by_key = {
        (int(float(row["heldout_fold"])), int(float(row["parameter_set"]))): row
        for row in support_rows
        if row.get("heldout_fold") not in (None, "") and row.get("parameter_set") not in (None, "")
    }
    output: list[dict[str, Any]] = []
    specs = [
        (
            ADAPTIVE_METHOD_ID,
            adaptive_predictions,
            ADAPTIVE_SETTING_ID,
            ADAPTIVE_FEATURE_GROUP,
            REFERENCE_SETTING_ID,
            REFERENCE_F4,
            "vs_f4",
        ),
        (
            ADAPTIVE_METHOD_ID,
            adaptive_predictions,
            ADAPTIVE_SETTING_ID,
            ADAPTIVE_FEATURE_GROUP,
            REFERENCE_SETTING_ID,
            REFERENCE_STRESS,
            "vs_stress_reference",
        ),
        (
            ROUTER_METHOD_ID,
            arm_selector_predictions,
            ROUTER_SETTING_ID,
            ROUTER_FEATURE_GROUP,
            "D0_R0_F4_reference",
            REFERENCE_F4,
            "vs_f4",
        ),
    ]
    for method_id, predictions, candidate_setting, candidate_feature, ref_setting, ref_feature, comparison in specs:
        for target in TARGETS:
            gains = _condition_gain_rows(
                predictions,
                target=target,
                split_name=PRIMARY_SPLIT,
                candidate_setting=candidate_setting,
                candidate_feature=candidate_feature,
                reference_setting=ref_setting,
                reference_feature=ref_feature,
            )
            grouped: dict[str, list[dict[str, float]]] = {}
            for gain_row in gains:
                support = support_by_key.get((int(gain_row["heldout_fold"]), int(gain_row["parameter_set"])))
                if support is None:
                    continue
                score = _as_float(support.get("support_score"))
                stratum = "low_support" if math.isfinite(score) and score < LOW_SUPPORT_THRESHOLD else "higher_support"
                grouped.setdefault(stratum, []).append(
                    {
                        "gain": float(gain_row["condition_mae_gain"]),
                        "support_score": score,
                    }
                )
            for stratum, items in sorted(grouped.items()):
                gains_only = [item["gain"] for item in items]
                scores = [item["support_score"] for item in items]
                output.append(
                    {
                        "method_id": method_id,
                        "target": target,
                        "comparison": comparison,
                        "support_stratum": stratum,
                        "condition_rows": len(items),
                        "mean_condition_mae_gain": _mean(gains_only),
                        "median_condition_mae_gain": _median(gains_only),
                        "median_support_score": _median(scores),
                        "low_support_threshold": LOW_SUPPORT_THRESHOLD,
                        "claim_scope": "support_stratified_diagnostic_context",
                    }
                )
    return output


def c_rate_repair_boundary_claim_readiness_rows(
    *,
    target_rows: list[dict[str, Any]],
    support_gain_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return conservative claim-readiness rows for the boundary gate."""
    by_method_target = {
        (str(row["method_id"]), str(row["target"])): bool(row["passes_boundary"])
        for row in target_rows
    }
    delta_passes = by_method_target.get((ADAPTIVE_METHOD_ID, "delta_capacity_Ah"), False) and by_method_target.get(
        (ROUTER_METHOD_ID, "delta_capacity_Ah"), False
    )
    capacity_passes = by_method_target.get((ADAPTIVE_METHOD_ID, "capacity_Ah_k1"), False) and by_method_target.get(
        (ROUTER_METHOD_ID, "capacity_Ah_k1"), False
    )
    any_capacity_pass = by_method_target.get((ADAPTIVE_METHOD_ID, "capacity_Ah_k1"), False) or by_method_target.get(
        (ROUTER_METHOD_ID, "capacity_Ah_k1"), False
    )
    return [
        {
            "claim_area": "C-rate delta repair boundary",
            "status": "supported_for_diagnostics" if delta_passes else "not_supported",
            "evidence": (
                "Adaptive R2/F8 and the targeted router both pass the C-rate delta boundary checks."
                if delta_passes
                else "At least one delta-capacity repair method fails a target-boundary guardrail."
            ),
            "allowed_wording": "The narrow C-rate `delta_capacity_Ah` repair diagnostic remains supported.",
            "forbidden_wording": "C-rate fade is solved globally.",
        },
        {
            "claim_area": "capacity-level transfer boundary",
            "status": "supported_for_diagnostics" if capacity_passes else ("diagnostic_only" if any_capacity_pass else "not_supported"),
            "evidence": (
                "Both repair methods pass the same C-rate/outside-split checks for `capacity_Ah_k1`."
                if capacity_passes
                else "Capacity-level transfer is incomplete or missing for at least one repair method."
            ),
            "allowed_wording": "Capacity-level transfer may be discussed only at the status shown by this boundary audit.",
            "forbidden_wording": "The delta-capacity repair automatically transfers to capacity level.",
        },
        {
            "claim_area": "two-target C-rate repair wording",
            "status": "supported_for_diagnostics" if delta_passes and capacity_passes else "not_supported",
            "evidence": (
                "Both targets pass both non-neural repair boundaries."
                if delta_passes and capacity_passes
                else "The target boundary does not justify two-target or broad robust-capacity wording."
            ),
            "allowed_wording": "Two-target C-rate repair is allowed only if both target rows pass.",
            "forbidden_wording": "A single delta-capacity gain supports broad robust capacity.",
        },
        {
            "claim_area": "support-stratified repair context",
            "status": "diagnostic_only" if support_gain_rows else "not_supported",
            "evidence": (
                "Support-stratified condition gains are available for interpretation."
                if support_gain_rows
                else "No support-overlap rows were supplied."
            ),
            "allowed_wording": "Support strata contextualize where repair gains occur.",
            "forbidden_wording": "Support strata prove deployment reliability or causal stressor effects.",
        },
        {
            "claim_area": "architecture, policy, calibration, and causality",
            "status": "blocked",
            "evidence": "The boundary gate uses existing non-neural artifacts only and adds no calibration, policy, neural, sequence, CBAT, or causal evidence.",
            "allowed_wording": "Architecture, policy, calibrated-risk/uncertainty, neural/sequence, CBAT, and causal claims remain blocked.",
            "forbidden_wording": "This boundary audit authorizes CBAT, policy ranking, calibrated risk, or causal claims.",
        },
    ]


def _adaptive_leakage_status(report: dict[str, Any]) -> str:
    if report.get("leakage_audit"):
        return str(report.get("leakage_audit", {}).get("status", "not_run"))
    return "passed" if "outer test rows are never used" in str(report.get("leakage_policy", "")) else "not_run"


def _adaptive_max_outside_degradation(report: dict[str, Any], target: str) -> tuple[float, int]:
    values: list[float] = []
    row_count = 0
    for split_name in _splits_present(report.get("metrics", [])):
        if split_name == PRIMARY_SPLIT:
            continue
        candidate = _mean_metric(
            report.get("metrics", []),
            target=target,
            split_name=split_name,
            model_setting_id=ADAPTIVE_SETTING_ID,
            feature_group=ADAPTIVE_FEATURE_GROUP,
        )
        reference = _mean_metric(
            report.get("metrics", []),
            target=target,
            split_name=split_name,
            model_setting_id=REFERENCE_SETTING_ID,
            feature_group=ADAPTIVE_FEATURE_GROUP,
        )
        if math.isfinite(candidate) and math.isfinite(reference) and reference > 0:
            row_count += 1
            values.append((candidate - reference) / reference)
    return (max(values) if values else math.nan), row_count


def _split_guardrail_row(
    *,
    method_id: str,
    target: str,
    split_name: str,
    candidate_setting: str,
    reference_setting: str,
    candidate_condition_mean_mae: float,
    reference_condition_mean_mae: float,
) -> dict[str, Any]:
    gain = _sub(reference_condition_mean_mae, candidate_condition_mean_mae)
    relative_degradation = (
        (candidate_condition_mean_mae - reference_condition_mean_mae) / reference_condition_mean_mae
        if math.isfinite(candidate_condition_mean_mae)
        and math.isfinite(reference_condition_mean_mae)
        and reference_condition_mean_mae > 0
        else math.nan
    )
    return {
        "method_id": method_id,
        "target": target,
        "split_name": split_name,
        "candidate_setting": candidate_setting,
        "reference_setting": reference_setting,
        "candidate_condition_mean_mae": candidate_condition_mean_mae,
        "reference_condition_mean_mae": reference_condition_mean_mae,
        "condition_mean_mae_gain": gain,
        "relative_degradation": relative_degradation,
        "passes_non_degradation_guardrail": (
            split_name == PRIMARY_SPLIT or _finite_le(relative_degradation, GUARDRAIL_MAX_OUTSIDE_DEGRADATION)
        ),
        "claim_scope": "split_guardrail_diagnostic",
    }


def _mean_metric(
    metrics: list[dict[str, Any]],
    *,
    target: str,
    split_name: str,
    model_setting_id: str,
    feature_group: str,
) -> float:
    values = [
        _as_float(row.get("condition_mean_mae"))
        for row in metrics
        if row.get("run_scope") == "primary"
        and row.get("target") == target
        and row.get("split_name") == split_name
        and row.get("model_setting_id") == model_setting_id
        and row.get("feature_group") == feature_group
    ]
    return _mean(values)


def _condition_gain_rows(
    predictions: list[dict[str, Any]],
    *,
    target: str,
    split_name: str,
    candidate_setting: str,
    candidate_feature: str,
    reference_setting: str,
    reference_feature: str,
) -> list[dict[str, Any]]:
    condition_errors = _condition_mae_by_setting(predictions)
    candidate_items = [
        (key, value)
        for key, value in condition_errors.items()
        if key[0] == target and key[1] == split_name and key[4] == candidate_setting and key[5] == candidate_feature
    ]
    rows = []
    for key, candidate_mae in candidate_items:
        _, _, heldout_fold, parameter_set, _, _ = key
        reference_key = (target, split_name, heldout_fold, parameter_set, reference_setting, reference_feature)
        reference_mae = condition_errors.get(reference_key)
        if reference_mae is None:
            continue
        rows.append(
            {
                "heldout_fold": heldout_fold,
                "parameter_set": parameter_set,
                "reference_condition_mae": reference_mae,
                "candidate_condition_mae": candidate_mae,
                "condition_mae_gain": reference_mae - candidate_mae,
            }
        )
    return rows


def _paired_condition_gain_p05(
    predictions: list[dict[str, Any]],
    *,
    target: str,
    split_name: str,
    candidate_setting: str,
    candidate_feature: str,
    reference_setting: str,
    reference_feature: str,
) -> float:
    gains = [
        float(row["condition_mae_gain"])
        for row in _condition_gain_rows(
            predictions,
            target=target,
            split_name=split_name,
            candidate_setting=candidate_setting,
            candidate_feature=candidate_feature,
            reference_setting=reference_setting,
            reference_feature=reference_feature,
        )
    ]
    return _bootstrap_mean_p05(gains)


def _condition_mae_by_setting(
    predictions: list[dict[str, Any]],
) -> dict[tuple[str, str, int, int, str, str], float]:
    grouped: dict[tuple[str, str, int, int, str, str], list[float]] = {}
    for row in predictions:
        if row.get("run_scope") != "primary":
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        key = (
            str(row.get("target")),
            str(row.get("split_name")),
            int(row.get("heldout_fold")),
            int(row.get("parameter_set")),
            str(row.get("model_setting_id")),
            str(row.get("feature_group")),
        )
        grouped.setdefault(key, []).append(abs(y_true - y_pred))
    return {key: _mean(values) for key, values in grouped.items()}


def _selector_comparison(report: dict[str, Any], *, target: str, split_name: str) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in report.get("comparison_rows", [])
            if row.get("target") == target and row.get("split_name") == split_name
        ),
        None,
    )


def _selector_outside(report: dict[str, Any], *, target: str) -> dict[str, Any] | None:
    return next((row for row in report.get("outside_degradation_rows", []) if row.get("target") == target), None)


def _targets_present(metrics: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row.get("target")) for row in metrics if row.get("target") in TARGETS})


def _splits_present(metrics: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row.get("split_name")) for row in metrics if row.get("split_name")})


def _bootstrap_mean_p05(values: list[float], *, resamples: int = 1000, seed: int = 42) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        sample = [finite[rng.randrange(len(finite))] for _ in finite]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[max(0, min(len(means) - 1, int(0.05 * (len(means) - 1))))]


def _claim_scope(readiness: dict[str, str]) -> str:
    if readiness.get("two-target C-rate repair wording") == "supported_for_diagnostics":
        return "two_target_non_neural_c_rate_repair_diagnostic_only"
    if readiness.get("C-rate delta repair boundary") == "supported_for_diagnostics":
        return "narrow_delta_only_non_neural_c_rate_repair_diagnostic_only"
    return "c_rate_repair_boundary_not_supported"


def _write_claim_readiness_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# C-Rate Repair Boundary Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} | "
            f"{row['allowed_wording']} | {row['forbidden_wording']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_decision_md(
    path: Path,
    *,
    target_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    support_gain_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> None:
    statuses = {row["claim_area"]: row["status"] for row in readiness_rows}
    lines = [
        "# C-Rate Repair Boundary Decision",
        "",
        "## Scope",
        "",
        "This gate tests whether the existing non-neural C-rate repair diagnostics transfer from `delta_capacity_Ah` to `capacity_Ah_k1`. It consumes existing grouped reports and prediction artifacts. It does not train a new model, add features, recommend policies, calibrate risk, or make causal claims.",
        "",
        "## Target Boundary Matrix",
        "",
        "| Method | Target | Gain vs F4 | Gain vs stress | p05 vs F4 | p05 vs stress | Outside degradation | Leakage | Passes |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in target_rows:
        lines.append(
            "| {method} | `{target}` | {gain_f4} | {gain_stress} | {p05_f4} | {p05_stress} | {degradation} | `{leakage}` | `{passes}` |".format(
                method=row["method_id"],
                target=row["target"],
                gain_f4=_fmt(row.get("c_rate_gain_vs_f4")),
                gain_stress=_fmt(row.get("c_rate_gain_vs_stress_reference")),
                p05_f4=_fmt(row.get("paired_p05_vs_f4")),
                p05_stress=_fmt(row.get("paired_p05_vs_stress_reference")),
                degradation=_fmt(row.get("max_other_split_relative_degradation")),
                leakage=row.get("leakage_audit"),
                passes=bool(row.get("passes_boundary")),
            )
        )
    lines.extend(
        [
            "",
            "## Split Guardrail",
            "",
            f"- Split guardrail rows: `{len(split_rows)}`",
            f"- Support-stratified gain rows: `{len(support_gain_rows)}`",
            "",
            "## Decision",
            "",
            f"- C-rate delta repair boundary: `{statuses.get('C-rate delta repair boundary')}`",
            f"- Capacity-level transfer boundary: `{statuses.get('capacity-level transfer boundary')}`",
            f"- Two-target C-rate repair wording: `{statuses.get('two-target C-rate repair wording')}`",
            f"- Support-stratified repair context: `{statuses.get('support-stratified repair context')}`",
            f"- Architecture/policy/calibration/causality: `{statuses.get('architecture, policy, calibration, and causality')}`",
            "",
            "The decision remains claim-gated. Passing `delta_capacity_Ah` does not by itself authorize capacity-level, broad robust-capacity, policy, architecture, calibrated-risk, calibrated-uncertainty, neural/sequence, CBAT, or causal wording.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return content


def _read_parquet_rows(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    rows = pq.read_table(path).to_pylist()
    if not rows:
        raise ValueError(f"{label} must contain at least one row: {path}")
    return rows


def _read_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"Missing support-overlap CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def _positive(value: Any) -> bool:
    numeric = _as_float(value)
    return math.isfinite(numeric) and numeric > 0


def _finite_le(value: Any, threshold: float) -> bool:
    numeric = _as_float(value)
    return math.isfinite(numeric) and numeric <= threshold


def _sub(left: Any, right: Any) -> float:
    left_float = _as_float(left)
    right_float = _as_float(right)
    if math.isfinite(left_float) and math.isfinite(right_float):
        return left_float - right_float
    return math.nan


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _mean(values: list[float]) -> float:
    finite = _finite(values)
    return sum(finite) / len(finite) if finite else math.nan


def _median(values: list[float]) -> float:
    finite = sorted(_finite(values))
    if not finite:
        return math.nan
    midpoint = len(finite) // 2
    if len(finite) % 2:
        return finite[midpoint]
    return (finite[midpoint - 1] + finite[midpoint]) / 2.0


def _fmt(value: Any) -> str:
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:.6g}"
    return ""
