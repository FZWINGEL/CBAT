"""Failure forensics for target-consistency reconstruction diagnostics.

This report-only gate explains why the Milestone 8.7 capacity-from-delta path
fails the outside-split non-degradation guardrail. It consumes existing
prediction artifacts and interval metadata; it does not train models or add
features.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

from mbp.analysis.target_consistency_reconstruction import (
    ADAPTIVE_FEATURE_GROUP,
    ADAPTIVE_METHOD_ID,
    ADAPTIVE_SETTING_ID,
    CAPACITY_FROM_DELTA_PATH,
    DIRECT_CAPACITY_PATH,
    GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
    PRIMARY_SPLIT,
    REFERENCE_F4,
    REFERENCE_SETTING_ID,
    REFERENCE_STRESS,
    ROUTER_FEATURE_GROUP,
    ROUTER_METHOD_ID,
    ROUTER_REFERENCE_SETTING_ID,
    ROUTER_SETTING_ID,
    _as_float,
    _mean,
    _read_interval_by_key,
    _read_json,
    _read_parquet_rows,
    _reconstructed_prediction_rows,
)

SCHEMA_VERSION = "gate88.reconstruction_failure_forensics.v1"


def diagnose_reconstruction_failure(
    reconstruction_report_path: Path,
    reconstruction_dir: Path,
    interval_table_path: Path,
    out_dir: Path,
    *,
    support_overlap_path: Path | None = None,
) -> dict[str, Any]:
    """Explain the failed capacity-from-delta outside-split guardrail."""
    reconstruction_report = _read_json(reconstruction_report_path, "reconstruction report")
    interval_by_key = _read_interval_by_key(interval_table_path)
    inputs = reconstruction_report.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("Reconstruction report is missing an inputs object.")
    adaptive_predictions_input = inputs.get("adaptive_predictions")
    arm_selector_predictions_input = inputs.get("arm_selector_predictions")
    if not adaptive_predictions_input:
        raise ValueError("Reconstruction report is missing adaptive_predictions input.")
    if not arm_selector_predictions_input:
        raise ValueError("Reconstruction report is missing arm_selector_predictions input.")
    adaptive_predictions_path = Path(str(adaptive_predictions_input))
    arm_selector_predictions_path = Path(str(arm_selector_predictions_input))

    adaptive_predictions = _read_parquet_rows(adaptive_predictions_path, "adaptive predictions")
    arm_selector_predictions = _read_parquet_rows(arm_selector_predictions_path, "arm-selector predictions")
    reconstructed_rows = (
        _reconstructed_prediction_rows(
            adaptive_predictions,
            interval_by_key=interval_by_key,
            method_id=ADAPTIVE_METHOD_ID,
            source_artifact="adaptive_boundary_predictions",
        )
        + _reconstructed_prediction_rows(
            arm_selector_predictions,
            interval_by_key=interval_by_key,
            method_id=ROUTER_METHOD_ID,
            source_artifact="arm_selector_boundary_predictions",
        )
    )
    if not reconstructed_rows:
        raise ValueError("No reconstructed prediction rows were generated.")

    condition_details = _condition_details_by_path(reconstructed_rows, interval_by_key)
    support_by_key = _read_support_overlap(support_overlap_path) if support_overlap_path else {}

    outside_rows = outside_failure_by_split_rows(condition_details)
    hotspot_rows = failing_condition_hotspot_rows(condition_details, outside_rows, support_by_key=support_by_key)
    decomposition_rows = path_error_decomposition_rows(condition_details)
    readiness_rows = reconstruction_failure_claim_readiness_rows(
        outside_rows=outside_rows,
        hotspot_rows=hotspot_rows,
        support_overlap_path=support_overlap_path,
    )
    readiness = {str(row["claim_area"]): str(row["status"]) for row in readiness_rows}
    decision = _decision_scope(readiness, outside_rows, hotspot_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "outside_failure_by_split.csv", outside_rows)
    _write_csv(plots_dir / "failing_condition_hotspots.csv", hotspot_rows)
    _write_csv(plots_dir / "path_error_decomposition.csv", decomposition_rows)
    _write_claim_readiness_md(out_dir / "reconstruction_failure_claim_readiness.md", readiness_rows)
    _write_decision_md(
        out_dir / "reconstruction_failure_decision.md",
        outside_rows=outside_rows,
        hotspot_rows=hotspot_rows,
        decomposition_rows=decomposition_rows,
        readiness_rows=readiness_rows,
        decision_scope=decision,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "reconstruction_report": str(reconstruction_report_path),
            "reconstruction_dir": str(reconstruction_dir),
            "interval_table": str(interval_table_path),
            "adaptive_predictions": str(adaptive_predictions_path),
            "arm_selector_predictions": str(arm_selector_predictions_path),
            "support_overlap": str(support_overlap_path) if support_overlap_path else None,
        },
        "outputs": {
            "report": str(out_dir / "reconstruction_failure_report.json"),
            "decision": str(out_dir / "reconstruction_failure_decision.md"),
            "claim_readiness": str(out_dir / "reconstruction_failure_claim_readiness.md"),
            "outside_failure_by_split": str(plots_dir / "outside_failure_by_split.csv"),
            "failing_condition_hotspots": str(plots_dir / "failing_condition_hotspots.csv"),
            "path_error_decomposition": str(plots_dir / "path_error_decomposition.csv"),
        },
        "source_guardrail_max_outside_degradation": reconstruction_report.get(
            "guardrail_max_outside_degradation",
            GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
        ),
        "guardrail_max_outside_degradation": GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
        "primary_split": PRIMARY_SPLIT,
        "source_claim_scope": reconstruction_report.get("claim_scope"),
        "row_counts": {
            "reconstructed_prediction_rows": len(reconstructed_rows),
            "condition_path_rows": len(condition_details),
            "outside_failure_by_split_rows": len(outside_rows),
            "failing_condition_hotspot_rows": len(hotspot_rows),
            "path_error_decomposition_rows": len(decomposition_rows),
            "claim_readiness_rows": len(readiness_rows),
        },
        "failure_summary": _failure_summary(outside_rows, hotspot_rows),
        "readiness": readiness,
        "decision_scope": decision,
    }
    (out_dir / "reconstruction_failure_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def outside_failure_by_split_rows(condition_details: dict[tuple[Any, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    """Return outside-split direct-reference capacity-from-delta comparisons."""
    rows: list[dict[str, Any]] = []
    for spec in _direct_reference_specs():
        for split_name in _outside_split_names(condition_details):
            paired = _paired_condition_details(
                condition_details,
                split_name=split_name,
                method_id=spec["method_id"],
                candidate_setting=spec["candidate_setting"],
                candidate_feature=spec["candidate_feature"],
                reference_setting=spec["reference_setting"],
                reference_feature=spec["reference_feature"],
            )
            if not paired:
                continue
            candidate_values = [candidate["condition_mae"] for candidate, _reference in paired]
            reference_values = [reference["condition_mae"] for _candidate, reference in paired]
            candidate_mean = _mean(candidate_values)
            reference_mean = _mean(reference_values)
            relative_degradation = _relative_degradation(candidate_mean, reference_mean)
            rows.append(
                {
                    "method_id": spec["method_id"],
                    "eval_target": "capacity_Ah_k1",
                    "candidate_setting": spec["candidate_setting"],
                    "candidate_feature_group": spec["candidate_feature"],
                    "candidate_path": CAPACITY_FROM_DELTA_PATH,
                    "reference_label": spec["reference_label"],
                    "reference_setting": spec["reference_setting"],
                    "reference_feature_group": spec["reference_feature"],
                    "reference_path": DIRECT_CAPACITY_PATH,
                    "split_name": split_name,
                    "condition_rows": len(paired),
                    "candidate_condition_mean_mae": candidate_mean,
                    "reference_condition_mean_mae": reference_mean,
                    "condition_mean_mae_gain": reference_mean - candidate_mean,
                    "relative_degradation": relative_degradation,
                    "passes_guardrail": _passes_guardrail(relative_degradation),
                    "failure_class": (
                        "passes"
                        if _passes_guardrail(relative_degradation)
                        else "fails_outside_split_guardrail"
                    ),
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            str(row["method_id"]),
            str(row["reference_label"]),
            str(row["split_name"]),
        ),
    )


def failing_condition_hotspot_rows(
    condition_details: dict[tuple[Any, ...], dict[str, Any]],
    outside_rows: list[dict[str, Any]],
    *,
    support_by_key: dict[tuple[str, int, int], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return condition-level hotspots for failing outside-split rows."""
    support_by_key = support_by_key or {}
    rows: list[dict[str, Any]] = []
    failing_specs = [row for row in outside_rows if row["passes_guardrail"] is False]
    for split_row in failing_specs:
        paired = _paired_condition_details(
            condition_details,
            split_name=str(split_row["split_name"]),
            method_id=str(split_row["method_id"]),
            candidate_setting=str(split_row["candidate_setting"]),
            candidate_feature=str(split_row["candidate_feature_group"]),
            reference_setting=str(split_row["reference_setting"]),
            reference_feature=str(split_row["reference_feature_group"]),
        )
        for candidate, reference in paired:
            candidate_mae = _as_float(candidate["condition_mae"])
            reference_mae = _as_float(reference["condition_mae"])
            relative_degradation = _relative_degradation(candidate_mae, reference_mae)
            support = support_by_key.get(
                (
                    str(candidate["split_name"]),
                    int(candidate["heldout_fold"]),
                    int(candidate["parameter_set"]),
                ),
                {},
            )
            rows.append(
                {
                    "method_id": split_row["method_id"],
                    "split_name": candidate["split_name"],
                    "heldout_fold": candidate["heldout_fold"],
                    "parameter_set": candidate["parameter_set"],
                    "aging_mode": candidate.get("aging_mode", ""),
                    "nominal_temperature_C": candidate.get("nominal_temperature_C", math.nan),
                    "voltage_window_family": candidate.get("voltage_window_family", ""),
                    "nominal_charge_C_rate": candidate.get("nominal_charge_C_rate", math.nan),
                    "nominal_discharge_C_rate": candidate.get("nominal_discharge_C_rate", math.nan),
                    "profile_label": candidate.get("profile_label", ""),
                    "reference_label": split_row["reference_label"],
                    "candidate_condition_mae": candidate_mae,
                    "reference_condition_mae": reference_mae,
                    "condition_mae_gain": reference_mae - candidate_mae,
                    "relative_degradation": relative_degradation,
                    "row_count": candidate["row_count"],
                    "quality_flagged_rows": candidate["quality_flagged_rows"],
                    "severe_qa_flag_rows": candidate["severe_qa_flag_rows"],
                    "monotonicity_unclean_rows": candidate["monotonicity_unclean_rows"],
                    "support_score": support.get("support_score", ""),
                    "low_support_flag": support.get("low_support_flag", ""),
                    "failure_role": "hotspot" if relative_degradation > 0 else "offsetting_or_neutral",
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            str(row["split_name"]),
            -_as_float(row["relative_degradation"]),
            int(row["parameter_set"]),
        ),
    )


def path_error_decomposition_rows(condition_details: dict[tuple[Any, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare direct capacity and capacity-from-delta path errors by split."""
    rows: list[dict[str, Any]] = []
    for spec in _direct_reference_specs():
        for split_name in sorted({str(key[2]) for key in condition_details}):
            paired = _paired_condition_details(
                condition_details,
                split_name=split_name,
                method_id=spec["method_id"],
                candidate_setting=spec["candidate_setting"],
                candidate_feature=spec["candidate_feature"],
                reference_setting=spec["reference_setting"],
                reference_feature=spec["reference_feature"],
            )
            if not paired:
                continue
            candidate_values = [candidate["condition_mae"] for candidate, _reference in paired]
            reference_values = [reference["condition_mae"] for _candidate, reference in paired]
            candidate_biases = [candidate["condition_signed_bias"] for candidate, _reference in paired]
            reference_biases = [reference["condition_signed_bias"] for _candidate, reference in paired]
            candidate_mean = _mean(candidate_values)
            reference_mean = _mean(reference_values)
            rows.append(
                {
                    "method_id": spec["method_id"],
                    "split_name": split_name,
                    "reference_label": spec["reference_label"],
                    "candidate_path": CAPACITY_FROM_DELTA_PATH,
                    "reference_path": DIRECT_CAPACITY_PATH,
                    "condition_rows": len(paired),
                    "candidate_capacity_from_delta_mae": candidate_mean,
                    "reference_direct_capacity_mae": reference_mean,
                    "condition_mean_mae_gain": reference_mean - candidate_mean,
                    "relative_degradation": _relative_degradation(candidate_mean, reference_mean),
                    "candidate_delta_bias_mean": _mean(candidate_biases),
                    "reference_capacity_bias_mean": _mean(reference_biases),
                    "candidate_abs_bias_mean": _mean([abs(value) for value in candidate_biases]),
                    "reference_abs_bias_mean": _mean([abs(value) for value in reference_biases]),
                    "passes_guardrail": _passes_guardrail(_relative_degradation(candidate_mean, reference_mean))
                    if split_name != PRIMARY_SPLIT
                    else "",
                }
            )
    return sorted(rows, key=lambda row: (str(row["method_id"]), str(row["reference_label"]), str(row["split_name"])))


def reconstruction_failure_claim_readiness_rows(
    *,
    outside_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
    support_overlap_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return conservative claim-readiness rows for reconstruction failure forensics."""
    failing_rows = [row for row in outside_rows if row["passes_guardrail"] is False]
    hotspot_degradations = [row for row in hotspot_rows if _as_float(row.get("relative_degradation")) > 0]
    severe_hotspots = [row for row in hotspot_degradations if int(row.get("severe_qa_flag_rows") or 0) > 0]
    support_observed = [row for row in hotspot_degradations if row.get("support_score") not in ("", None)]
    low_support = [row for row in support_observed if str(row.get("low_support_flag")).lower() == "true"]
    broad_failure = len({row["split_name"] for row in failing_rows}) > 1 or len(hotspot_degradations) >= 5
    qa_concentrated = bool(hotspot_degradations) and len(severe_hotspots) / len(hotspot_degradations) >= 0.8
    support_concentrated = bool(support_observed) and len(low_support) / len(support_observed) >= 0.8
    return [
        {
            "claim_area": "outside-split failure attribution",
            "status": "supported_for_diagnostics" if failing_rows else "not_supported",
            "evidence": (
                f"{len(failing_rows)} outside-split direct-reference reconstruction comparisons fail the 5pct guardrail."
                if failing_rows
                else "No outside-split failure was detected in the reconstruction forensics inputs."
            ),
            "allowed_wording": "Use the split and condition forensics to explain why capacity-from-delta transfer remains blocked.",
            "forbidden_wording": "Forensics repair the capacity-level transfer result.",
        },
        {
            "claim_area": "narrow QA artifact explanation",
            "status": "diagnostic_only" if qa_concentrated else "not_supported",
            "evidence": (
                "Most degrading hotspots carry severe trajectory or LOG_AGE monotonicity flags."
                if qa_concentrated
                else "The degrading hotspots are not concentrated enough in severe QA flags to call the failure a narrow data artifact."
            ),
            "allowed_wording": "QA flags may contextualize individual hotspots.",
            "forbidden_wording": "The failed guardrail can be ignored as a QA artifact.",
        },
        {
            "claim_area": "support-limited explanation",
            "status": "diagnostic_only" if support_concentrated else "not_supported",
            "evidence": (
                "Observed support rows indicate most degrading hotspots are low-support."
                if support_concentrated
                else (
                    "Support overlap was not available for enough degrading outside-split hotspots."
                    if support_overlap_path is None or not support_observed
                    else "Low-support rows do not explain most degrading hotspots."
                )
            ),
            "allowed_wording": "Support context can be reported as diagnostic when available.",
            "forbidden_wording": "Support limitation authorizes capacity-level repair or policy ranking.",
        },
        {
            "claim_area": "capacity-level reconstruction branch",
            "status": "blocked" if failing_rows else "not_supported",
            "evidence": (
                "Capacity-from-delta fails outside-split direct-reference non-degradation; the branch should close unless a future data-quality correction gate is explicitly opened."
                if broad_failure
                else "The capacity-level reconstruction branch remains unsupported under the direct-reference guardrail."
            ),
            "allowed_wording": "Close the capacity-level C-rate repair branch for current evidence.",
            "forbidden_wording": "The delta repair can be broadened to capacity_Ah_k1.",
        },
        {
            "claim_area": "architecture, policy, calibration, sequence, neural, and causality",
            "status": "blocked",
            "evidence": "This gate is report-only failure forensics over existing non-neural predictions.",
            "allowed_wording": "CBAT, neural/sequence models, policy ranking, calibrated risk/uncertainty, and causal claims remain blocked.",
            "forbidden_wording": "Failure forensics authorize architecture, policy, calibrated risk, uncertainty, or causal claims.",
        },
    ]


def _condition_details_by_path(
    rows: list[dict[str, Any]],
    interval_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> dict[tuple[Any, ...], dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        y_true = _as_float(row.get("y_true_eval"))
        y_pred = _as_float(row.get("y_pred_eval"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        key = (
            str(row["method_id"]),
            str(row["eval_target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
            str(row["model_setting_id"]),
            str(row["feature_group"]),
            str(row["target_path"]),
        )
        entry = grouped.setdefault(
            key,
            {
                "method_id": str(row["method_id"]),
                "eval_target": str(row["eval_target"]),
                "split_name": str(row["split_name"]),
                "heldout_fold": int(row["heldout_fold"]),
                "parameter_set": int(row["parameter_set"]),
                "model_setting_id": str(row["model_setting_id"]),
                "feature_group": str(row["feature_group"]),
                "target_path": str(row["target_path"]),
                "errors": [],
                "signed_errors": [],
                "row_count": 0,
                "quality_flagged_rows": 0,
                "severe_qa_flag_rows": 0,
                "monotonicity_unclean_rows": 0,
            },
        )
        entry["errors"].append(abs(y_pred - y_true))
        entry["signed_errors"].append(y_pred - y_true)
        entry["row_count"] += 1
        interval = interval_by_key.get((str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])), {})
        _attach_condition_metadata(entry, interval)
        if _has_quality_flag(interval):
            entry["quality_flagged_rows"] += 1
        if _has_severe_quality_flag(interval):
            entry["severe_qa_flag_rows"] += 1
        if str(interval.get("LOG_AGE_monotonicity_clean", "")).lower() == "false":
            entry["monotonicity_unclean_rows"] += 1
    output: dict[tuple[Any, ...], dict[str, Any]] = {}
    for key, entry in grouped.items():
        entry["condition_mae"] = _mean(entry.pop("errors"))
        entry["condition_signed_bias"] = _mean(entry.pop("signed_errors"))
        output[key] = entry
    return output


def _attach_condition_metadata(entry: dict[str, Any], interval: dict[str, Any]) -> None:
    for field in (
        "aging_mode",
        "nominal_temperature_C",
        "voltage_window_family",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "profile_label",
    ):
        if field not in entry and field in interval:
            entry[field] = interval.get(field)


def _direct_reference_specs() -> list[dict[str, str]]:
    return [
        {
            "method_id": ADAPTIVE_METHOD_ID,
            "candidate_setting": ADAPTIVE_SETTING_ID,
            "candidate_feature": ADAPTIVE_FEATURE_GROUP,
            "reference_label": "F4_direct_capacity",
            "reference_setting": REFERENCE_SETTING_ID,
            "reference_feature": REFERENCE_F4,
        },
        {
            "method_id": ADAPTIVE_METHOD_ID,
            "candidate_setting": ADAPTIVE_SETTING_ID,
            "candidate_feature": ADAPTIVE_FEATURE_GROUP,
            "reference_label": "stress_direct_capacity",
            "reference_setting": REFERENCE_SETTING_ID,
            "reference_feature": REFERENCE_STRESS,
        },
        {
            "method_id": ROUTER_METHOD_ID,
            "candidate_setting": ROUTER_SETTING_ID,
            "candidate_feature": ROUTER_FEATURE_GROUP,
            "reference_label": "F4_direct_capacity",
            "reference_setting": ROUTER_REFERENCE_SETTING_ID,
            "reference_feature": REFERENCE_F4,
        },
    ]


def _outside_split_names(condition_details: dict[tuple[Any, ...], dict[str, Any]]) -> list[str]:
    return sorted({str(key[2]) for key in condition_details if str(key[2]) != PRIMARY_SPLIT})


def _paired_condition_details(
    condition_details: dict[tuple[Any, ...], dict[str, Any]],
    *,
    split_name: str,
    method_id: str,
    candidate_setting: str,
    candidate_feature: str,
    reference_setting: str,
    reference_feature: str,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    paired: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for key, candidate in condition_details.items():
        method, eval_target, split, heldout_fold, parameter_set, setting, feature, path = key
        if (
            method != method_id
            or eval_target != "capacity_Ah_k1"
            or split != split_name
            or setting != candidate_setting
            or feature != candidate_feature
            or path != CAPACITY_FROM_DELTA_PATH
        ):
            continue
        reference_key = (
            method_id,
            "capacity_Ah_k1",
            split_name,
            heldout_fold,
            parameter_set,
            reference_setting,
            reference_feature,
            DIRECT_CAPACITY_PATH,
        )
        reference = condition_details.get(reference_key)
        if reference is not None:
            paired.append((candidate, reference))
    return paired


def _read_support_overlap(path: Path | None) -> dict[tuple[str, int, int], dict[str, Any]]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Missing support overlap: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {
        (str(row["split_name"]), int(row["heldout_fold"]), int(row["parameter_set"])): row
        for row in rows
        if row.get("split_name") and row.get("heldout_fold") and row.get("parameter_set")
    }


def _has_quality_flag(interval: dict[str, Any]) -> bool:
    flags = str(interval.get("quality_flags", "") or "").strip()
    return bool(flags)


def _has_severe_quality_flag(interval: dict[str, Any]) -> bool:
    flags = str(interval.get("quality_flags", "") or "").lower()
    if "monotonicity" in flags:
        return True
    return str(interval.get("LOG_AGE_monotonicity_clean", "")).lower() == "false"


def _relative_degradation(candidate_mean: float, reference_mean: float) -> float:
    if math.isfinite(candidate_mean) and math.isfinite(reference_mean) and reference_mean > 0:
        return (candidate_mean - reference_mean) / reference_mean
    return math.nan


def _passes_guardrail(relative_degradation: float) -> bool:
    return math.isfinite(relative_degradation) and relative_degradation <= GUARDRAIL_MAX_OUTSIDE_DEGRADATION


def _failure_summary(outside_rows: list[dict[str, Any]], hotspot_rows: list[dict[str, Any]]) -> dict[str, Any]:
    failing_rows = [row for row in outside_rows if row["passes_guardrail"] is False]
    degrading_hotspots = [row for row in hotspot_rows if _as_float(row.get("relative_degradation")) > 0]
    return {
        "failing_outside_comparisons": len(failing_rows),
        "failing_split_names": sorted({str(row["split_name"]) for row in failing_rows}),
        "degrading_hotspot_rows": len(degrading_hotspots),
        "max_relative_degradation": max(
            (_as_float(row.get("relative_degradation")) for row in outside_rows),
            default=math.nan,
        ),
        "max_hotspot_relative_degradation": max(
            (_as_float(row.get("relative_degradation")) for row in hotspot_rows),
            default=math.nan,
        ),
    }


def _decision_scope(
    readiness: dict[str, str],
    outside_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
) -> str:
    failing_rows = [row for row in outside_rows if row["passes_guardrail"] is False]
    degrading_hotspots = [row for row in hotspot_rows if _as_float(row.get("relative_degradation")) > 0]
    if not failing_rows:
        return "no_outside_split_reconstruction_failure_detected"
    if len({row["split_name"] for row in failing_rows}) > 1 or len(degrading_hotspots) >= 5:
        return "capacity_reconstruction_branch_closed_broad_outside_failure"
    if readiness.get("narrow QA artifact explanation") == "diagnostic_only":
        return "qa_concentrated_failure_requires_data_quality_gate"
    return "capacity_reconstruction_branch_closed_localized_failure"


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


def _write_claim_readiness_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Reconstruction Failure Claim Readiness",
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
    outside_rows: list[dict[str, Any]],
    hotspot_rows: list[dict[str, Any]],
    decomposition_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
    decision_scope: str,
) -> None:
    summary = _failure_summary(outside_rows, hotspot_rows)
    lines = [
        "# Reconstruction Failure Decision",
        "",
        "## Scope",
        "",
        "This report explains the Milestone 8.7 outside-split failure for capacity-from-delta reconstruction. It consumes existing non-neural prediction artifacts and interval metadata only. It does not train a model, tune a repair, add features, calibrate probabilities, recommend policies, or make causal claims.",
        "",
        "## Summary",
        "",
        f"- Decision scope: `{decision_scope}`",
        f"- Failing outside comparisons: `{summary['failing_outside_comparisons']}`",
        f"- Failing split names: `{', '.join(summary['failing_split_names'])}`",
        f"- Degrading hotspot rows: `{summary['degrading_hotspot_rows']}`",
        f"- Max outside relative degradation: `{_fmt(summary['max_relative_degradation'])}`",
        "",
        "## Outside-Split Direct-Reference Comparisons",
        "",
        "| Method | Reference | Split | Candidate MAE | Reference MAE | Relative degradation | Passes |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in outside_rows:
        lines.append(
            "| {method} | `{reference}` | `{split}` | {candidate} | {reference_mae} | {degradation} | `{passes}` |".format(
                method=row["method_id"],
                reference=row["reference_label"],
                split=row["split_name"],
                candidate=_fmt(row["candidate_condition_mean_mae"]),
                reference_mae=_fmt(row["reference_condition_mean_mae"]),
                degradation=_fmt(row["relative_degradation"]),
                passes=bool(row["passes_guardrail"]),
            )
        )
    lines.extend(
        [
            "",
            "## Top Failing Hotspots",
            "",
            "| Split | Fold | Condition | Reference | Relative degradation | Candidate MAE | Reference MAE | Severe QA rows |",
            "|---|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    top_hotspots = [row for row in hotspot_rows if _as_float(row.get("relative_degradation")) > 0][:12]
    for row in top_hotspots:
        lines.append(
            "| {split} | {fold} | {condition} | `{reference}` | {degradation} | {candidate} | {reference_mae} | {qa} |".format(
                split=row["split_name"],
                fold=row["heldout_fold"],
                condition=row["parameter_set"],
                reference=row["reference_label"],
                degradation=_fmt(row["relative_degradation"]),
                candidate=_fmt(row["candidate_condition_mae"]),
                reference_mae=_fmt(row["reference_condition_mae"]),
                qa=row["severe_qa_flag_rows"],
            )
        )
    lines.extend(
        [
            "",
            "## Path Error Decomposition",
            "",
            "| Method | Reference | Split | Candidate MAE | Reference MAE | Candidate bias | Reference bias |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in decomposition_rows:
        if row["split_name"] == PRIMARY_SPLIT or row["passes_guardrail"] is False:
            lines.append(
                "| {method} | `{reference}` | `{split}` | {candidate} | {reference_mae} | {candidate_bias} | {reference_bias} |".format(
                    method=row["method_id"],
                    reference=row["reference_label"],
                    split=row["split_name"],
                    candidate=_fmt(row["candidate_capacity_from_delta_mae"]),
                    reference_mae=_fmt(row["reference_direct_capacity_mae"]),
                    candidate_bias=_fmt(row["candidate_delta_bias_mean"]),
                    reference_bias=_fmt(row["reference_capacity_bias_mean"]),
                )
            )
    lines.extend(
        [
            "",
            "## Claim Readiness",
            "",
            "| Claim area | Status |",
            "|---|---|",
        ]
    )
    for row in readiness_rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The current evidence closes the capacity-level reconstruction repair branch unless a future, explicit data-quality correction gate finds a narrow extraction or labeling artifact. The narrow `delta_capacity_Ah` repair remains diagnostic-only; two-target C-rate repair, broad robust capacity, solved C-rate fade, CBAT, neural/sequence models, policy ranking, calibrated risk/uncertainty, and causal claims remain blocked.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:.6g}"
    return ""
