from __future__ import annotations

import json
from pathlib import Path

from mbp.analysis.c_rate_repair_boundary import (
    ADAPTIVE_METHOD_ID,
    ROUTER_METHOD_ID,
    c_rate_repair_boundary_claim_readiness_rows,
    c_rate_repair_boundary_split_rows,
    c_rate_repair_boundary_target_rows,
    c_rate_repair_support_stratum_gain_rows,
    diagnose_c_rate_repair_boundary,
)


def _metric(
    *,
    target: str,
    split_name: str,
    setting: str,
    feature_group: str,
    condition_mean_mae: float,
) -> dict[str, object]:
    return {
        "run_scope": "primary",
        "target": target,
        "split_name": split_name,
        "model_setting_id": setting,
        "model_level": setting,
        "feature_group": feature_group,
        "condition_mean_mae": condition_mean_mae,
    }


def _prediction(
    *,
    target: str,
    fold: int,
    parameter_set: int,
    setting: str,
    feature_group: str,
    y_true: float,
    y_pred: float,
) -> dict[str, object]:
    return {
        "run_scope": "primary",
        "target": target,
        "split_name": "c_rate_holdout_fold",
        "heldout_fold": fold,
        "parameter_set": parameter_set,
        "model_setting_id": setting,
        "feature_group": feature_group,
        "y_true": y_true,
        "y_pred": y_pred,
    }


def _adaptive_report() -> dict[str, object]:
    metrics = []
    for target in ("delta_capacity_Ah", "capacity_Ah_k1"):
        metrics.extend(
            [
                _metric(
                    target=target,
                    split_name="c_rate_holdout_fold",
                    setting="R0_reference_hgb50",
                    feature_group="F4_state_log_age_scalar",
                    condition_mean_mae=0.20,
                ),
                _metric(
                    target=target,
                    split_name="c_rate_holdout_fold",
                    setting="R0_reference_hgb50",
                    feature_group="F8_timestamp_weighted_stress",
                    condition_mean_mae=0.18,
                ),
                _metric(
                    target=target,
                    split_name="c_rate_holdout_fold",
                    setting="R5_train_only_stressor_selected_hgb",
                    feature_group="F8_timestamp_weighted_stress",
                    condition_mean_mae=0.12 if target == "delta_capacity_Ah" else 0.19,
                ),
                _metric(
                    target=target,
                    split_name="condition_fold",
                    setting="R0_reference_hgb50",
                    feature_group="F8_timestamp_weighted_stress",
                    condition_mean_mae=0.10,
                ),
                _metric(
                    target=target,
                    split_name="condition_fold",
                    setting="R5_train_only_stressor_selected_hgb",
                    feature_group="F8_timestamp_weighted_stress",
                    condition_mean_mae=0.102 if target == "delta_capacity_Ah" else 0.11,
                ),
            ]
        )
    return {
        "leakage_policy": "Held-out outer test rows are never used to choose the weight strength.",
        "metrics": metrics,
    }


def _adaptive_predictions() -> list[dict[str, object]]:
    rows = []
    for target in ("delta_capacity_Ah", "capacity_Ah_k1"):
        candidate_error = 0.02 if target == "delta_capacity_Ah" else 0.11
        for parameter_set in (1, 2, 3):
            rows.extend(
                [
                    _prediction(
                        target=target,
                        fold=0,
                        parameter_set=parameter_set,
                        setting="R0_reference_hgb50",
                        feature_group="F4_state_log_age_scalar",
                        y_true=0.0,
                        y_pred=0.10,
                    ),
                    _prediction(
                        target=target,
                        fold=0,
                        parameter_set=parameter_set,
                        setting="R0_reference_hgb50",
                        feature_group="F8_timestamp_weighted_stress",
                        y_true=0.0,
                        y_pred=0.08,
                    ),
                    _prediction(
                        target=target,
                        fold=0,
                        parameter_set=parameter_set,
                        setting="R5_train_only_stressor_selected_hgb",
                        feature_group="F8_timestamp_weighted_stress",
                        y_true=0.0,
                        y_pred=candidate_error,
                    ),
                ]
            )
    return rows


def _arm_selector_report() -> dict[str, object]:
    comparison_rows = []
    outside_rows = []
    for target in ("delta_capacity_Ah", "capacity_Ah_k1"):
        gain = 0.05 if target == "delta_capacity_Ah" else 0.04
        comparison_rows.extend(
            [
                {
                    "target": target,
                    "split_name": "c_rate_holdout_fold",
                    "candidate_condition_mean_mae": 0.10,
                    "reference_condition_mean_mae": 0.10 + gain,
                    "condition_mean_mae_gain": gain,
                    "paired_p05": 0.02,
                    "relative_degradation": -0.10,
                },
                {
                    "target": target,
                    "split_name": "condition_fold",
                    "candidate_condition_mean_mae": 0.10,
                    "reference_condition_mean_mae": 0.10,
                    "condition_mean_mae_gain": 0.0,
                    "paired_p05": 0.0,
                    "relative_degradation": 0.0,
                },
            ]
        )
        outside_rows.append(
            {
                "target": target,
                "max_other_split_relative_degradation": 0.0,
                "outside_split_rows": 1,
            }
        )
    return {
        "leakage_audit": {"status": "passed"},
        "comparison_rows": comparison_rows,
        "outside_degradation_rows": outside_rows,
    }


def _arm_selector_predictions() -> list[dict[str, object]]:
    rows = []
    for target in ("delta_capacity_Ah", "capacity_Ah_k1"):
        for parameter_set in (1, 2, 3):
            rows.extend(
                [
                    _prediction(
                        target=target,
                        fold=0,
                        parameter_set=parameter_set,
                        setting="D0_R0_F4_reference",
                        feature_group="F4_state_log_age_scalar",
                        y_true=0.0,
                        y_pred=0.10,
                    ),
                    _prediction(
                        target=target,
                        fold=0,
                        parameter_set=parameter_set,
                        setting="R6_train_only_arm_selector_hgb",
                        feature_group="train_only_arm_selector",
                        y_true=0.0,
                        y_pred=0.05,
                    ),
                ]
            )
    return rows


def test_boundary_target_rows_keep_capacity_transfer_separate() -> None:
    rows = c_rate_repair_boundary_target_rows(
        adaptive_report=_adaptive_report(),
        adaptive_predictions=_adaptive_predictions(),
        arm_selector_report=_arm_selector_report(),
        arm_selector_predictions=_arm_selector_predictions(),
    )
    by_method_target = {(row["method_id"], row["target"]): row for row in rows}

    assert by_method_target[(ADAPTIVE_METHOD_ID, "delta_capacity_Ah")]["passes_boundary"] is True
    assert by_method_target[(ROUTER_METHOD_ID, "delta_capacity_Ah")]["passes_boundary"] is True
    assert by_method_target[(ADAPTIVE_METHOD_ID, "capacity_Ah_k1")]["passes_boundary"] is False
    assert by_method_target[(ROUTER_METHOD_ID, "capacity_Ah_k1")]["passes_boundary"] is True


def test_boundary_claim_readiness_blocks_two_target_wording() -> None:
    target_rows = c_rate_repair_boundary_target_rows(
        adaptive_report=_adaptive_report(),
        adaptive_predictions=_adaptive_predictions(),
        arm_selector_report=_arm_selector_report(),
        arm_selector_predictions=_arm_selector_predictions(),
    )
    support_rows = c_rate_repair_support_stratum_gain_rows(
        support_rows=[
            {"heldout_fold": "0", "parameter_set": "1", "support_score": "0.2"},
            {"heldout_fold": "0", "parameter_set": "2", "support_score": "0.8"},
        ],
        adaptive_predictions=_adaptive_predictions(),
        arm_selector_predictions=_arm_selector_predictions(),
    )
    rows = c_rate_repair_boundary_claim_readiness_rows(
        target_rows=target_rows,
        support_gain_rows=support_rows,
    )
    statuses = {row["claim_area"]: row["status"] for row in rows}

    assert statuses["C-rate delta repair boundary"] == "supported_for_diagnostics"
    assert statuses["capacity-level transfer boundary"] == "diagnostic_only"
    assert statuses["two-target C-rate repair wording"] == "not_supported"
    assert statuses["architecture, policy, calibration, and causality"] == "blocked"


def test_support_stratum_gain_rows_join_support_by_condition() -> None:
    rows = c_rate_repair_support_stratum_gain_rows(
        support_rows=[
            {"heldout_fold": "0", "parameter_set": "1", "support_score": "0.2"},
            {"heldout_fold": "0", "parameter_set": "2", "support_score": "0.8"},
        ],
        adaptive_predictions=_adaptive_predictions(),
        arm_selector_predictions=_arm_selector_predictions(),
    )
    strata = {(row["method_id"], row["comparison"], row["support_stratum"]) for row in rows}

    assert (ADAPTIVE_METHOD_ID, "vs_f4", "low_support") in strata
    assert (ADAPTIVE_METHOD_ID, "vs_stress_reference", "higher_support") in strata
    assert (ROUTER_METHOD_ID, "vs_f4", "low_support") in strata


def test_split_guardrail_rows_include_capacity_failure() -> None:
    rows = c_rate_repair_boundary_split_rows(
        adaptive_report=_adaptive_report(),
        arm_selector_report=_arm_selector_report(),
    )
    adaptive_capacity_condition = [
        row
        for row in rows
        if row["method_id"] == ADAPTIVE_METHOD_ID
        and row["target"] == "capacity_Ah_k1"
        and row["split_name"] == "condition_fold"
    ][0]

    assert adaptive_capacity_condition["passes_non_degradation_guardrail"] is False


def test_diagnose_c_rate_repair_boundary_writes_bundle(tmp_path: Path) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    adaptive_report = tmp_path / "adaptive.json"
    adaptive_predictions = tmp_path / "adaptive.parquet"
    selector_report = tmp_path / "selector.json"
    selector_predictions = tmp_path / "selector.parquet"
    out_dir = tmp_path / "out"
    adaptive_report.write_text(json.dumps(_adaptive_report()), encoding="utf-8")
    selector_report.write_text(json.dumps(_arm_selector_report()), encoding="utf-8")
    pq.write_table(pa.Table.from_pylist(_adaptive_predictions()), adaptive_predictions)
    pq.write_table(pa.Table.from_pylist(_arm_selector_predictions()), selector_predictions)

    report = diagnose_c_rate_repair_boundary(
        adaptive_report,
        adaptive_predictions,
        selector_report,
        selector_predictions,
        out_dir,
    )

    assert report["status"] == "passed"
    assert report["readiness"]["two-target C-rate repair wording"] == "not_supported"
    assert (out_dir / "c_rate_repair_boundary_report.json").exists()
    assert (out_dir / "plots" / "target_boundary_matrix.csv").exists()
