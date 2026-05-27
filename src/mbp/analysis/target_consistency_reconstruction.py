"""Target-consistency reconstruction diagnostics for C-rate repair.

This report-only gate checks whether successful `delta_capacity_Ah` C-rate
repair can be translated into a capacity-level prediction by adding the
predicted interval change to the observed check-up-k capacity. It consumes
existing prediction artifacts and does not train models or engineer features.
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

SCHEMA_VERSION = "gate87.target_consistency_reconstruction.v1"
PRIMARY_SPLIT = "c_rate_holdout_fold"
GUARDRAIL_MAX_OUTSIDE_DEGRADATION = 0.05

ADAPTIVE_METHOD_ID = "adaptive_R2_F8_conservative"
ADAPTIVE_SETTING_ID = "R5_train_only_stressor_selected_hgb"
ADAPTIVE_FEATURE_GROUP = "F8_timestamp_weighted_stress"
REFERENCE_SETTING_ID = "R0_reference_hgb50"
REFERENCE_F4 = "F4_state_log_age_scalar"
REFERENCE_STRESS = "F8_timestamp_weighted_stress"

ROUTER_METHOD_ID = "targeted_router_D2_F4"
ROUTER_SETTING_ID = "R6_train_only_arm_selector_hgb"
ROUTER_FEATURE_GROUP = "train_only_arm_selector"
ROUTER_REFERENCE_SETTING_ID = "D0_R0_F4_reference"

DIRECT_CAPACITY_PATH = "direct_capacity"
CAPACITY_FROM_DELTA_PATH = "capacity_from_delta"
DIRECT_DELTA_PATH = "direct_delta"
DELTA_FROM_CAPACITY_PATH = "delta_from_capacity"


def diagnose_target_consistency_reconstruction(
    interval_table_path: Path,
    adaptive_predictions_path: Path,
    arm_selector_predictions_path: Path,
    out_dir: Path,
    *,
    boundary_report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the report-only direct-vs-derived target consistency diagnostic."""
    interval_by_key = _read_interval_by_key(interval_table_path)
    adaptive_predictions = _read_parquet_rows(adaptive_predictions_path, "adaptive predictions")
    arm_selector_predictions = _read_parquet_rows(arm_selector_predictions_path, "arm-selector predictions")
    boundary_report = _read_json(boundary_report_path, "boundary report") if boundary_report_path else {}

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

    summary_rows = target_path_summary_rows(reconstructed_rows)
    gain_rows = target_path_gain_rows(reconstructed_rows)
    guardrail_rows = target_path_guardrail_rows(reconstructed_rows)
    readiness_rows = target_consistency_claim_readiness_rows(gain_rows=gain_rows, guardrail_rows=guardrail_rows)
    readiness = {str(row["claim_area"]): str(row["status"]) for row in readiness_rows}

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "direct_vs_derived_target_paths.csv", summary_rows)
    _write_csv(plots_dir / "c_rate_reconstruction_gain.csv", gain_rows)
    _write_csv(plots_dir / "outside_split_reconstruction_guardrail.csv", guardrail_rows)
    _write_claim_readiness_md(out_dir / "target_consistency_claim_readiness.md", readiness_rows)
    _write_decision_md(
        out_dir / "target_consistency_reconstruction_decision.md",
        gain_rows=gain_rows,
        guardrail_rows=guardrail_rows,
        readiness_rows=readiness_rows,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "adaptive_predictions": str(adaptive_predictions_path),
            "arm_selector_predictions": str(arm_selector_predictions_path),
            "boundary_report": str(boundary_report_path) if boundary_report_path else None,
        },
        "outputs": {
            "report": str(out_dir / "target_consistency_reconstruction_report.json"),
            "decision": str(out_dir / "target_consistency_reconstruction_decision.md"),
            "claim_readiness": str(out_dir / "target_consistency_claim_readiness.md"),
            "direct_vs_derived_target_paths": str(plots_dir / "direct_vs_derived_target_paths.csv"),
            "c_rate_reconstruction_gain": str(plots_dir / "c_rate_reconstruction_gain.csv"),
            "outside_split_reconstruction_guardrail": str(
                plots_dir / "outside_split_reconstruction_guardrail.csv"
            ),
        },
        "boundary_claim_scope": boundary_report.get("claim_scope"),
        "guardrail_max_outside_degradation": GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
        "primary_split": PRIMARY_SPLIT,
        "row_counts": {
            "interval_rows": len(interval_by_key),
            "reconstructed_prediction_rows": len(reconstructed_rows),
            "target_path_summary_rows": len(summary_rows),
            "c_rate_gain_rows": len(gain_rows),
            "outside_guardrail_rows": len(guardrail_rows),
            "claim_readiness_rows": len(readiness_rows),
        },
        "readiness": readiness,
        "claim_scope": _claim_scope(readiness),
    }
    (out_dir / "target_consistency_reconstruction_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def target_path_summary_rows(reconstructed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate direct and derived prediction paths by condition-level MAE."""
    grouped: dict[tuple[str, str, str, str, int, str, str, str], list[dict[str, float]]] = {}
    for row in reconstructed_rows:
        key = (
            str(row["method_id"]),
            str(row["eval_target"]),
            str(row["target_path"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            str(row["model_setting_id"]),
            str(row["feature_group"]),
            str(row["source_artifact"]),
        )
        grouped.setdefault(key, []).append(
            {
                "parameter_set": float(row["parameter_set"]),
                "error": abs(float(row["y_true_eval"]) - float(row["y_pred_eval"])),
            }
        )
    rows: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items()):
        method_id, eval_target, target_path, split_name, heldout_fold, setting, feature, source = key
        by_condition: dict[int, list[float]] = {}
        for value in values:
            by_condition.setdefault(int(value["parameter_set"]), []).append(value["error"])
        condition_maes = [_mean(errors) for errors in by_condition.values()]
        rows.append(
            {
                "method_id": method_id,
                "eval_target": eval_target,
                "target_path": target_path,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_setting_id": setting,
                "feature_group": feature,
                "source_artifact": source,
                "row_count": len(values),
                "condition_count": len(by_condition),
                "condition_mean_mae": _mean(condition_maes),
            }
        )
    return rows


def target_path_gain_rows(reconstructed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return primary C-rate gains for direct and derived target paths."""
    condition_errors = _condition_mae_by_path(reconstructed_rows)
    rows: list[dict[str, Any]] = []
    specs = [
        {
            "method_id": ADAPTIVE_METHOD_ID,
            "candidate_setting": ADAPTIVE_SETTING_ID,
            "candidate_feature": ADAPTIVE_FEATURE_GROUP,
            "references": [
                ("F4_direct_capacity", REFERENCE_SETTING_ID, REFERENCE_F4, DIRECT_CAPACITY_PATH),
                ("F4_capacity_from_delta", REFERENCE_SETTING_ID, REFERENCE_F4, CAPACITY_FROM_DELTA_PATH),
                ("stress_direct_capacity", REFERENCE_SETTING_ID, REFERENCE_STRESS, DIRECT_CAPACITY_PATH),
                ("stress_capacity_from_delta", REFERENCE_SETTING_ID, REFERENCE_STRESS, CAPACITY_FROM_DELTA_PATH),
            ],
        },
        {
            "method_id": ROUTER_METHOD_ID,
            "candidate_setting": ROUTER_SETTING_ID,
            "candidate_feature": ROUTER_FEATURE_GROUP,
            "references": [
                ("F4_direct_capacity", ROUTER_REFERENCE_SETTING_ID, REFERENCE_F4, DIRECT_CAPACITY_PATH),
                ("F4_capacity_from_delta", ROUTER_REFERENCE_SETTING_ID, REFERENCE_F4, CAPACITY_FROM_DELTA_PATH),
            ],
        },
    ]
    for spec in specs:
        for candidate_path in (DIRECT_CAPACITY_PATH, CAPACITY_FROM_DELTA_PATH):
            for reference_label, reference_setting, reference_feature, reference_path in spec["references"]:
                rows.extend(
                    _comparison_rows(
                        condition_errors,
                        method_id=str(spec["method_id"]),
                        eval_target="capacity_Ah_k1",
                        split_name=PRIMARY_SPLIT,
                        candidate_setting=str(spec["candidate_setting"]),
                        candidate_feature=str(spec["candidate_feature"]),
                        candidate_path=candidate_path,
                        reference_setting=reference_setting,
                        reference_feature=reference_feature,
                        reference_path=reference_path,
                        reference_label=reference_label,
                    )
                )
        for candidate_path in (DIRECT_DELTA_PATH, DELTA_FROM_CAPACITY_PATH):
            rows.extend(
                _comparison_rows(
                    condition_errors,
                    method_id=str(spec["method_id"]),
                    eval_target="delta_capacity_Ah",
                    split_name=PRIMARY_SPLIT,
                    candidate_setting=str(spec["candidate_setting"]),
                    candidate_feature=str(spec["candidate_feature"]),
                    candidate_path=candidate_path,
                    reference_setting=(
                        REFERENCE_SETTING_ID
                        if spec["method_id"] == ADAPTIVE_METHOD_ID
                        else ROUTER_REFERENCE_SETTING_ID
                    ),
                    reference_feature=REFERENCE_F4,
                    reference_path=DIRECT_DELTA_PATH,
                    reference_label="F4_direct_delta",
                )
            )
    return sorted(rows, key=lambda row: (row["eval_target"], row["method_id"], row["candidate_path"], row["reference_label"]))


def target_path_guardrail_rows(reconstructed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return outside-C-rate non-degradation checks for reconstruction paths."""
    condition_errors = _condition_mae_by_path(reconstructed_rows)
    rows: list[dict[str, Any]] = []
    specs = [
        (
            ADAPTIVE_METHOD_ID,
            ADAPTIVE_SETTING_ID,
            ADAPTIVE_FEATURE_GROUP,
            REFERENCE_SETTING_ID,
            REFERENCE_STRESS,
        ),
        (
            ROUTER_METHOD_ID,
            ROUTER_SETTING_ID,
            ROUTER_FEATURE_GROUP,
            ROUTER_REFERENCE_SETTING_ID,
            REFERENCE_F4,
        ),
    ]
    for method_id, candidate_setting, candidate_feature, reference_setting, reference_feature in specs:
        for eval_target, candidate_paths in (
            ("capacity_Ah_k1", (DIRECT_CAPACITY_PATH, CAPACITY_FROM_DELTA_PATH)),
            ("delta_capacity_Ah", (DIRECT_DELTA_PATH, DELTA_FROM_CAPACITY_PATH)),
        ):
            for candidate_path in candidate_paths:
                reference_paths = [("outside_direct_reference", _direct_path_for_target(eval_target))]
                if candidate_path in {CAPACITY_FROM_DELTA_PATH, DELTA_FROM_CAPACITY_PATH}:
                    reference_paths.append(("outside_derived_reference", candidate_path))
                for reference_label, reference_path in reference_paths:
                    values: list[float] = []
                    split_count = 0
                    for split_name in sorted({key[2] for key in condition_errors if key[2] != PRIMARY_SPLIT}):
                        comparisons = _comparison_rows(
                            condition_errors,
                            method_id=method_id,
                            eval_target=eval_target,
                            split_name=split_name,
                            candidate_setting=candidate_setting,
                            candidate_feature=candidate_feature,
                            candidate_path=candidate_path,
                            reference_setting=reference_setting,
                            reference_feature=reference_feature,
                            reference_path=reference_path,
                            reference_label=reference_label,
                        )
                        if not comparisons:
                            continue
                        split_count += 1
                        degradation = _as_float(comparisons[0]["relative_degradation"])
                        if math.isfinite(degradation):
                            values.append(degradation)
                    max_degradation = max(values) if values else math.nan
                    rows.append(
                        {
                            "method_id": method_id,
                            "eval_target": eval_target,
                            "candidate_path": candidate_path,
                            "reference_label": reference_label,
                            "reference_path": reference_path,
                            "reference_feature_group": reference_feature,
                            "outside_split_rows": split_count,
                            "max_other_split_relative_degradation": max_degradation,
                            "passes_guardrail": _finite_le(max_degradation, GUARDRAIL_MAX_OUTSIDE_DEGRADATION),
                        }
                    )
    return sorted(rows, key=lambda row: (row["eval_target"], row["method_id"], row["candidate_path"]))


def target_consistency_claim_readiness_rows(
    *,
    gain_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return conservative claim-readiness rows for reconstruction diagnostics."""
    delta_passes = _passes_required_delta_rows(gain_rows, guardrail_rows)
    capacity_direct_reference_passes = _passes_capacity_from_delta_vs_direct_references(gain_rows, guardrail_rows)
    capacity_derived_reference_passes = _passes_capacity_from_delta_vs_derived_references(gain_rows, guardrail_rows)
    return [
        {
            "claim_area": "delta target-path consistency",
            "status": "supported_for_diagnostics" if delta_passes else "not_supported",
            "evidence": (
                "Direct delta repair remains positive against F4 under the reconstructed path audit."
                if delta_passes
                else "Direct or derived delta paths fail a gain or outside-split guardrail."
            ),
            "allowed_wording": "C-rate `delta_capacity_Ah` repair remains a diagnostic target-specific result.",
            "forbidden_wording": "Delta repair proves broad capacity repair.",
        },
        {
            "claim_area": "capacity-from-delta transfer versus direct references",
            "status": "supported_for_diagnostics" if capacity_direct_reference_passes else "not_supported",
            "evidence": (
                "`capacity_Ah_k + predicted_delta` beats direct capacity references and passes outside-split guardrails."
                if capacity_direct_reference_passes
                else "`capacity_Ah_k + predicted_delta` does not pass the direct capacity-reference transfer gate."
            ),
            "allowed_wording": "Capacity-from-delta transfer may be claimed only if direct reference checks pass.",
            "forbidden_wording": "A derived-capacity diagnostic can replace the direct capacity benchmark without passing direct references.",
        },
        {
            "claim_area": "capacity-from-delta transfer versus derived references",
            "status": "diagnostic_only" if capacity_derived_reference_passes else "not_supported",
            "evidence": (
                "Derived capacity beats derived reference paths, but this is weaker than direct capacity-reference transfer."
                if capacity_derived_reference_passes
                else "Derived capacity does not pass the full derived-reference transfer check."
            ),
            "allowed_wording": "Derived-vs-derived comparisons may be used as target-path diagnostics.",
            "forbidden_wording": "Derived-reference gains alone authorize capacity-level repair.",
        },
        {
            "claim_area": "two-target C-rate repair wording",
            "status": "supported_for_diagnostics" if delta_passes and capacity_direct_reference_passes else "not_supported",
            "evidence": (
                "Delta repair and capacity-from-delta direct-reference transfer both pass."
                if delta_passes and capacity_direct_reference_passes
                else "The reconstruction gate does not justify two-target C-rate repair wording."
            ),
            "allowed_wording": "Two-target repair wording requires both delta and capacity-level direct-reference checks.",
            "forbidden_wording": "The successful delta target alone supports two-target repair.",
        },
        {
            "claim_area": "architecture, policy, calibration, and causality",
            "status": "blocked",
            "evidence": "This gate consumes existing non-neural predictions and adds no calibration, policy, neural, sequence, CBAT, or causal evidence.",
            "allowed_wording": "Architecture, policy, calibrated-risk/uncertainty, neural/sequence, CBAT, and causal claims remain blocked.",
            "forbidden_wording": "Target reconstruction authorizes CBAT, policy ranking, calibrated risk, or causal claims.",
        },
    ]


def _reconstructed_prediction_rows(
    prediction_rows: list[dict[str, Any]],
    *,
    interval_by_key: dict[tuple[str, int, int], dict[str, Any]],
    method_id: str,
    source_artifact: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in prediction_rows:
        if row.get("run_scope") != "primary":
            continue
        key = (str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"]))
        interval = interval_by_key.get(key)
        if interval is None:
            continue
        capacity_k = _as_float(interval.get("capacity_Ah_k"))
        capacity_k1 = _as_float(interval.get("capacity_Ah_k1"))
        delta = _as_float(interval.get("delta_capacity_Ah"))
        y_pred = _as_float(row.get("y_pred"))
        if not all(math.isfinite(value) for value in (capacity_k, capacity_k1, delta, y_pred)):
            continue
        base = {
            "method_id": method_id,
            "source_artifact": source_artifact,
            "source_target": str(row["target"]),
            "split_name": str(row["split_name"]),
            "heldout_fold": int(row["heldout_fold"]),
            "model_setting_id": str(row["model_setting_id"]),
            "feature_group": str(row["feature_group"]),
            "cell_id": str(row["cell_id"]),
            "parameter_set": int(row["parameter_set"]),
            "replicate_id": int(row["replicate_id"]),
            "checkup_k": int(row["checkup_k"]),
            "checkup_k_next": int(row["checkup_k_next"]),
        }
        if row["target"] == "capacity_Ah_k1":
            output.append(
                {
                    **base,
                    "eval_target": "capacity_Ah_k1",
                    "target_path": DIRECT_CAPACITY_PATH,
                    "y_true_eval": capacity_k1,
                    "y_pred_eval": y_pred,
                }
            )
            output.append(
                {
                    **base,
                    "eval_target": "delta_capacity_Ah",
                    "target_path": DELTA_FROM_CAPACITY_PATH,
                    "y_true_eval": delta,
                    "y_pred_eval": y_pred - capacity_k,
                }
            )
        elif row["target"] == "delta_capacity_Ah":
            output.append(
                {
                    **base,
                    "eval_target": "delta_capacity_Ah",
                    "target_path": DIRECT_DELTA_PATH,
                    "y_true_eval": delta,
                    "y_pred_eval": y_pred,
                }
            )
            output.append(
                {
                    **base,
                    "eval_target": "capacity_Ah_k1",
                    "target_path": CAPACITY_FROM_DELTA_PATH,
                    "y_true_eval": capacity_k1,
                    "y_pred_eval": capacity_k + y_pred,
                }
            )
    return output


def _comparison_rows(
    condition_errors: dict[tuple[str, str, str, int, int, str, str, str], float],
    *,
    method_id: str,
    eval_target: str,
    split_name: str,
    candidate_setting: str,
    candidate_feature: str,
    candidate_path: str,
    reference_setting: str,
    reference_feature: str,
    reference_path: str,
    reference_label: str,
) -> list[dict[str, Any]]:
    gains: list[float] = []
    candidate_values: list[float] = []
    reference_values: list[float] = []
    for key, candidate_mae in condition_errors.items():
        method, target, split, fold, parameter_set, setting, feature, path = key
        if (
            method != method_id
            or target != eval_target
            or split != split_name
            or setting != candidate_setting
            or feature != candidate_feature
            or path != candidate_path
        ):
            continue
        reference_key = (
            method_id,
            eval_target,
            split_name,
            fold,
            parameter_set,
            reference_setting,
            reference_feature,
            reference_path,
        )
        reference_mae = condition_errors.get(reference_key)
        if reference_mae is None:
            continue
        candidate_values.append(candidate_mae)
        reference_values.append(reference_mae)
        gains.append(reference_mae - candidate_mae)
    if not gains:
        return []
    candidate_mean = _mean(candidate_values)
    reference_mean = _mean(reference_values)
    return [
        {
            "method_id": method_id,
            "eval_target": eval_target,
            "split_name": split_name,
            "candidate_setting": candidate_setting,
            "candidate_feature_group": candidate_feature,
            "candidate_path": candidate_path,
            "reference_label": reference_label,
            "reference_setting": reference_setting,
            "reference_feature_group": reference_feature,
            "reference_path": reference_path,
            "condition_rows": len(gains),
            "candidate_condition_mean_mae": candidate_mean,
            "reference_condition_mean_mae": reference_mean,
            "condition_mean_mae_gain": reference_mean - candidate_mean,
            "paired_p05": _bootstrap_mean_p05(gains),
            "relative_degradation": (
                (candidate_mean - reference_mean) / reference_mean
                if math.isfinite(candidate_mean) and math.isfinite(reference_mean) and reference_mean > 0
                else math.nan
            ),
            "passes_gain_guardrail": _positive(reference_mean - candidate_mean) and _positive(_bootstrap_mean_p05(gains)),
        }
    ]


def _condition_mae_by_path(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str, str, int, int, str, str, str], float]:
    grouped: dict[tuple[str, str, str, int, int, str, str, str], list[float]] = {}
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
        grouped.setdefault(key, []).append(abs(y_true - y_pred))
    return {key: _mean(values) for key, values in grouped.items()}


def _passes_required_delta_rows(gain_rows: list[dict[str, Any]], guardrail_rows: list[dict[str, Any]]) -> bool:
    for method_id in (ADAPTIVE_METHOD_ID, ROUTER_METHOD_ID):
        required_gain = _gain_row(
            gain_rows,
            method_id=method_id,
            eval_target="delta_capacity_Ah",
            candidate_path=DIRECT_DELTA_PATH,
            reference_label="F4_direct_delta",
        )
        required_guardrail = _guardrail_row(
            guardrail_rows,
            method_id=method_id,
            eval_target="delta_capacity_Ah",
            candidate_path=DIRECT_DELTA_PATH,
            reference_path=DIRECT_DELTA_PATH,
        )
        if not (required_gain and required_gain["passes_gain_guardrail"] and required_guardrail and required_guardrail["passes_guardrail"]):
            return False
    return True


def _passes_capacity_from_delta_vs_direct_references(
    gain_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> bool:
    required = [
        (ADAPTIVE_METHOD_ID, "F4_direct_capacity"),
        (ADAPTIVE_METHOD_ID, "stress_direct_capacity"),
        (ROUTER_METHOD_ID, "F4_direct_capacity"),
    ]
    for method_id, reference_label in required:
        row = _gain_row(
            gain_rows,
            method_id=method_id,
            eval_target="capacity_Ah_k1",
            candidate_path=CAPACITY_FROM_DELTA_PATH,
            reference_label=reference_label,
        )
        guardrail = _guardrail_row(
            guardrail_rows,
            method_id=method_id,
            eval_target="capacity_Ah_k1",
            candidate_path=CAPACITY_FROM_DELTA_PATH,
            reference_path=DIRECT_CAPACITY_PATH,
        )
        if not (row and row["passes_gain_guardrail"] and guardrail and guardrail["passes_guardrail"]):
            return False
    return True


def _passes_capacity_from_delta_vs_derived_references(
    gain_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
) -> bool:
    required = [
        (ADAPTIVE_METHOD_ID, "F4_capacity_from_delta"),
        (ADAPTIVE_METHOD_ID, "stress_capacity_from_delta"),
        (ROUTER_METHOD_ID, "F4_capacity_from_delta"),
    ]
    for method_id, reference_label in required:
        row = _gain_row(
            gain_rows,
            method_id=method_id,
            eval_target="capacity_Ah_k1",
            candidate_path=CAPACITY_FROM_DELTA_PATH,
            reference_label=reference_label,
        )
        guardrail = _guardrail_row(
            guardrail_rows,
            method_id=method_id,
            eval_target="capacity_Ah_k1",
            candidate_path=CAPACITY_FROM_DELTA_PATH,
            reference_path=CAPACITY_FROM_DELTA_PATH,
        )
        if not (row and row["passes_gain_guardrail"] and guardrail and guardrail["passes_guardrail"]):
            return False
    return True


def _gain_row(
    rows: list[dict[str, Any]],
    *,
    method_id: str,
    eval_target: str,
    candidate_path: str,
    reference_label: str,
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in rows
            if row["method_id"] == method_id
            and row["eval_target"] == eval_target
            and row["candidate_path"] == candidate_path
            and row["reference_label"] == reference_label
        ),
        None,
    )


def _guardrail_row(
    rows: list[dict[str, Any]],
    *,
    method_id: str,
    eval_target: str,
    candidate_path: str,
    reference_path: str,
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in rows
            if row["method_id"] == method_id
            and row["eval_target"] == eval_target
            and row["candidate_path"] == candidate_path
            and row["reference_path"] == reference_path
        ),
        None,
    )


def _direct_path_for_target(eval_target: str) -> str:
    if eval_target == "capacity_Ah_k1":
        return DIRECT_CAPACITY_PATH
    if eval_target == "delta_capacity_Ah":
        return DIRECT_DELTA_PATH
    raise ValueError(f"Unknown target: {eval_target}")


def _read_interval_by_key(path: Path) -> dict[tuple[str, int, int], dict[str, Any]]:
    rows = _read_parquet_rows(path, "interval table")
    output: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        output[(str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"]))] = row
    if not output:
        raise ValueError(f"Interval table contains no usable rows: {path}")
    return output


def _read_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None:
        return {}
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
        "# Target-Consistency Reconstruction Claim Readiness",
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
    gain_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> None:
    statuses = {row["claim_area"]: row["status"] for row in readiness_rows}
    lines = [
        "# Target-Consistency Reconstruction Decision",
        "",
        "## Scope",
        "",
        "This gate tests whether existing C-rate `delta_capacity_Ah` repair predictions can be translated into `capacity_Ah_k1` by adding the predicted delta to observed check-up-k capacity. It consumes existing prediction artifacts and does not train a new model, add features, recommend policies, calibrate risk, or make causal claims.",
        "",
        "## C-Rate Reconstruction Gain Rows",
        "",
        "| Method | Eval target | Candidate path | Reference | Gain | p05 | Passes |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in gain_rows:
        if row["eval_target"] == "capacity_Ah_k1" or row["candidate_path"] in {DIRECT_DELTA_PATH, DELTA_FROM_CAPACITY_PATH}:
            lines.append(
                "| {method} | `{target}` | `{path}` | `{reference}` | {gain} | {p05} | `{passes}` |".format(
                    method=row["method_id"],
                    target=row["eval_target"],
                    path=row["candidate_path"],
                    reference=row["reference_label"],
                    gain=_fmt(row["condition_mean_mae_gain"]),
                    p05=_fmt(row["paired_p05"]),
                    passes=bool(row["passes_gain_guardrail"]),
                )
            )
    lines.extend(
        [
            "",
            "## Outside-Split Guardrail",
            "",
            "| Method | Eval target | Candidate path | Reference | Max degradation | Passes |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for row in guardrail_rows:
        lines.append(
            "| {method} | `{target}` | `{path}` | `{reference}` | {degradation} | `{passes}` |".format(
                method=row["method_id"],
                target=row["eval_target"],
                path=row["candidate_path"],
                reference=row["reference_label"],
                degradation=_fmt(row["max_other_split_relative_degradation"]),
                passes=bool(row["passes_guardrail"]),
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Delta target-path consistency: `{statuses.get('delta target-path consistency')}`",
            f"- Capacity-from-delta transfer versus direct references: `{statuses.get('capacity-from-delta transfer versus direct references')}`",
            f"- Capacity-from-delta transfer versus derived references: `{statuses.get('capacity-from-delta transfer versus derived references')}`",
            f"- Two-target C-rate repair wording: `{statuses.get('two-target C-rate repair wording')}`",
            f"- Architecture/policy/calibration/causality: `{statuses.get('architecture, policy, calibration, and causality')}`",
            "",
            "The decision remains claim-gated. Derived capacity paths are useful diagnostics, but they do not authorize capacity-level or two-target repair unless they beat the existing direct capacity references under the same grouped guardrails.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _claim_scope(readiness: dict[str, str]) -> str:
    if readiness.get("two-target C-rate repair wording") == "supported_for_diagnostics":
        return "two_target_reconstruction_supported_for_diagnostics"
    if readiness.get("capacity-from-delta transfer versus direct references") == "supported_for_diagnostics":
        return "capacity_from_delta_transfer_supported_for_diagnostics"
    if readiness.get("delta target-path consistency") == "supported_for_diagnostics":
        return "delta_only_reconstruction_diagnostic"
    return "target_consistency_reconstruction_not_supported"


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


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _mean(values: list[float]) -> float:
    finite = _finite(values)
    return sum(finite) / len(finite) if finite else math.nan


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


def _fmt(value: Any) -> str:
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:.6g}"
    return ""
