from __future__ import annotations

import math
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.target_consistency_reconstruction import (
    ADAPTIVE_METHOD_ID,
    CAPACITY_FROM_DELTA_PATH,
    DIRECT_CAPACITY_PATH,
    DIRECT_DELTA_PATH,
    ROUTER_METHOD_ID,
    diagnose_target_consistency_reconstruction,
    target_consistency_claim_readiness_rows,
    target_path_gain_rows,
    target_path_guardrail_rows,
    target_path_summary_rows,
)


def _intervals() -> list[dict[str, object]]:
    return [
        {
            "cell_id": f"cell-{idx}",
            "parameter_set": idx,
            "replicate_id": 1,
            "checkup_k": 0,
            "checkup_k_next": 1,
            "capacity_Ah_k": 1.0,
            "capacity_Ah_k1": 0.9,
            "delta_capacity_Ah": -0.1,
        }
        for idx in (1, 2, 3)
    ]


def _prediction(
    *,
    method_setting: str,
    feature_group: str,
    target: str,
    y_pred: float,
    split_name: str = "c_rate_holdout_fold",
) -> list[dict[str, object]]:
    y_true = 0.9 if target == "capacity_Ah_k1" else -0.1
    return [
        {
            "run_scope": "primary",
            "split_name": split_name,
            "heldout_fold": 0,
            "model_setting_id": method_setting,
            "feature_group": feature_group,
            "target": target,
            "cell_id": interval["cell_id"],
            "parameter_set": interval["parameter_set"],
            "replicate_id": interval["replicate_id"],
            "checkup_k": interval["checkup_k"],
            "checkup_k_next": interval["checkup_k_next"],
            "y_true": y_true,
            "y_pred": y_pred,
        }
        for interval in _intervals()
    ]


def _adaptive_predictions() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for split in ("c_rate_holdout_fold", "condition_fold"):
        rows.extend(_prediction(method_setting="R0_reference_hgb50", feature_group="F4_state_log_age_scalar", target="delta_capacity_Ah", y_pred=0.0, split_name=split))
        rows.extend(_prediction(method_setting="R0_reference_hgb50", feature_group="F8_timestamp_weighted_stress", target="delta_capacity_Ah", y_pred=-0.02, split_name=split))
        rows.extend(_prediction(method_setting="R5_train_only_stressor_selected_hgb", feature_group="F8_timestamp_weighted_stress", target="delta_capacity_Ah", y_pred=-0.1, split_name=split))
        rows.extend(_prediction(method_setting="R0_reference_hgb50", feature_group="F4_state_log_age_scalar", target="capacity_Ah_k1", y_pred=0.92, split_name=split))
        rows.extend(_prediction(method_setting="R0_reference_hgb50", feature_group="F8_timestamp_weighted_stress", target="capacity_Ah_k1", y_pred=0.91, split_name=split))
        rows.extend(_prediction(method_setting="R5_train_only_stressor_selected_hgb", feature_group="F8_timestamp_weighted_stress", target="capacity_Ah_k1", y_pred=1.0, split_name=split))
    return rows


def _router_predictions() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for split in ("c_rate_holdout_fold", "condition_fold"):
        rows.extend(_prediction(method_setting="D0_R0_F4_reference", feature_group="F4_state_log_age_scalar", target="delta_capacity_Ah", y_pred=0.0, split_name=split))
        rows.extend(_prediction(method_setting="R6_train_only_arm_selector_hgb", feature_group="train_only_arm_selector", target="delta_capacity_Ah", y_pred=-0.1, split_name=split))
        rows.extend(_prediction(method_setting="D0_R0_F4_reference", feature_group="F4_state_log_age_scalar", target="capacity_Ah_k1", y_pred=0.92, split_name=split))
        rows.extend(_prediction(method_setting="R6_train_only_arm_selector_hgb", feature_group="train_only_arm_selector", target="capacity_Ah_k1", y_pred=1.0, split_name=split))
    return rows


def _reconstructed_rows() -> list[dict[str, object]]:
    from mbp.analysis.target_consistency_reconstruction import _reconstructed_prediction_rows

    interval_by_key = {
        (str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])): row
        for row in _intervals()
    }
    return _reconstructed_prediction_rows(
        _adaptive_predictions(),
        interval_by_key=interval_by_key,
        method_id=ADAPTIVE_METHOD_ID,
        source_artifact="adaptive",
    ) + _reconstructed_prediction_rows(
        _router_predictions(),
        interval_by_key=interval_by_key,
        method_id=ROUTER_METHOD_ID,
        source_artifact="router",
    )


def test_target_path_summary_builds_direct_and_derived_paths() -> None:
    rows = target_path_summary_rows(_reconstructed_rows())
    paths = {(row["eval_target"], row["target_path"]) for row in rows}

    assert ("capacity_Ah_k1", DIRECT_CAPACITY_PATH) in paths
    assert ("capacity_Ah_k1", CAPACITY_FROM_DELTA_PATH) in paths
    assert ("delta_capacity_Ah", DIRECT_DELTA_PATH) in paths


def test_capacity_from_delta_beats_direct_capacity_references() -> None:
    gain_rows = target_path_gain_rows(_reconstructed_rows())
    row = next(
        row
        for row in gain_rows
        if row["method_id"] == ADAPTIVE_METHOD_ID
        and row["eval_target"] == "capacity_Ah_k1"
        and row["candidate_path"] == CAPACITY_FROM_DELTA_PATH
        and row["reference_label"] == "stress_direct_capacity"
    )

    assert row["condition_mean_mae_gain"] > 0
    assert row["paired_p05"] > 0
    assert row["passes_gain_guardrail"] is True


def test_reconstruction_claim_readiness_requires_direct_reference_transfer() -> None:
    rows = _reconstructed_rows()
    gain_rows = target_path_gain_rows(rows)
    guardrail_rows = target_path_guardrail_rows(rows)
    readiness = target_consistency_claim_readiness_rows(gain_rows=gain_rows, guardrail_rows=guardrail_rows)
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert statuses["delta target-path consistency"] == "supported_for_diagnostics"
    assert statuses["capacity-from-delta transfer versus direct references"] == "supported_for_diagnostics"
    assert statuses["two-target C-rate repair wording"] == "supported_for_diagnostics"
    assert statuses["architecture, policy, calibration, and causality"] == "blocked"


def test_reconstruction_claim_readiness_blocks_when_direct_reference_transfer_fails() -> None:
    rows = [
        row
        for row in _reconstructed_rows()
        if not (
            row["method_id"] == ROUTER_METHOD_ID
            and row["target_path"] == CAPACITY_FROM_DELTA_PATH
            and row["model_setting_id"] == "R6_train_only_arm_selector_hgb"
        )
    ]
    for row in rows:
        if row["method_id"] == ROUTER_METHOD_ID and row["target_path"] == CAPACITY_FROM_DELTA_PATH:
            row["y_pred_eval"] = 1.2
    gain_rows = target_path_gain_rows(rows)
    guardrail_rows = target_path_guardrail_rows(rows)
    readiness = target_consistency_claim_readiness_rows(gain_rows=gain_rows, guardrail_rows=guardrail_rows)
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert statuses["capacity-from-delta transfer versus direct references"] == "not_supported"
    assert statuses["two-target C-rate repair wording"] == "not_supported"


def test_readiness_separates_direct_and_derived_reference_guardrails() -> None:
    gain_rows = [
        {
            "method_id": method_id,
            "eval_target": "delta_capacity_Ah",
            "candidate_path": DIRECT_DELTA_PATH,
            "reference_label": "F4_direct_delta",
            "passes_gain_guardrail": True,
        }
        for method_id in (ADAPTIVE_METHOD_ID, ROUTER_METHOD_ID)
    ]
    for method_id, reference_label in (
        (ADAPTIVE_METHOD_ID, "F4_direct_capacity"),
        (ADAPTIVE_METHOD_ID, "stress_direct_capacity"),
        (ROUTER_METHOD_ID, "F4_direct_capacity"),
        (ADAPTIVE_METHOD_ID, "F4_capacity_from_delta"),
        (ADAPTIVE_METHOD_ID, "stress_capacity_from_delta"),
        (ROUTER_METHOD_ID, "F4_capacity_from_delta"),
    ):
        gain_rows.append(
            {
                "method_id": method_id,
                "eval_target": "capacity_Ah_k1",
                "candidate_path": CAPACITY_FROM_DELTA_PATH,
                "reference_label": reference_label,
                "passes_gain_guardrail": True,
            }
        )
    guardrail_rows = [
        {
            "method_id": method_id,
            "eval_target": "delta_capacity_Ah",
            "candidate_path": DIRECT_DELTA_PATH,
            "reference_path": DIRECT_DELTA_PATH,
            "passes_guardrail": True,
        }
        for method_id in (ADAPTIVE_METHOD_ID, ROUTER_METHOD_ID)
    ]
    guardrail_rows.extend(
        [
            {
                "method_id": ADAPTIVE_METHOD_ID,
                "eval_target": "capacity_Ah_k1",
                "candidate_path": CAPACITY_FROM_DELTA_PATH,
                "reference_path": DIRECT_CAPACITY_PATH,
                "passes_guardrail": True,
            },
            {
                "method_id": ROUTER_METHOD_ID,
                "eval_target": "capacity_Ah_k1",
                "candidate_path": CAPACITY_FROM_DELTA_PATH,
                "reference_path": DIRECT_CAPACITY_PATH,
                "passes_guardrail": False,
            },
            {
                "method_id": ADAPTIVE_METHOD_ID,
                "eval_target": "capacity_Ah_k1",
                "candidate_path": CAPACITY_FROM_DELTA_PATH,
                "reference_path": CAPACITY_FROM_DELTA_PATH,
                "passes_guardrail": True,
            },
            {
                "method_id": ROUTER_METHOD_ID,
                "eval_target": "capacity_Ah_k1",
                "candidate_path": CAPACITY_FROM_DELTA_PATH,
                "reference_path": CAPACITY_FROM_DELTA_PATH,
                "passes_guardrail": True,
            },
        ]
    )

    readiness = target_consistency_claim_readiness_rows(gain_rows=gain_rows, guardrail_rows=guardrail_rows)
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert statuses["capacity-from-delta transfer versus direct references"] == "not_supported"
    assert statuses["capacity-from-delta transfer versus derived references"] == "diagnostic_only"
    assert statuses["two-target C-rate repair wording"] == "not_supported"


def test_diagnose_target_consistency_reconstruction_writes_bundle(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    adaptive_path = tmp_path / "adaptive.parquet"
    router_path = tmp_path / "router.parquet"
    out_dir = tmp_path / "out"
    pq.write_table(pa.Table.from_pylist(_intervals()), interval_path)
    pq.write_table(pa.Table.from_pylist(_adaptive_predictions()), adaptive_path)
    pq.write_table(pa.Table.from_pylist(_router_predictions()), router_path)

    report = diagnose_target_consistency_reconstruction(interval_path, adaptive_path, router_path, out_dir)

    assert report["status"] == "passed"
    assert report["readiness"]["architecture, policy, calibration, and causality"] == "blocked"
    assert math.isfinite(report["row_counts"]["reconstructed_prediction_rows"])
    assert (out_dir / "target_consistency_reconstruction_report.json").exists()
    assert (out_dir / "plots" / "c_rate_reconstruction_gain.csv").exists()
