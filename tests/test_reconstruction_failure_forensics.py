from __future__ import annotations

import csv
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.reconstruction_failure_forensics import (
    diagnose_reconstruction_failure,
    failing_condition_hotspot_rows,
    outside_failure_by_split_rows,
    reconstruction_failure_claim_readiness_rows,
)
from mbp.analysis.target_consistency_reconstruction import (
    ADAPTIVE_METHOD_ID,
    ROUTER_METHOD_ID,
    _read_interval_by_key,
    _reconstructed_prediction_rows,
)


def _intervals() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set in (1, 2, 3, 4, 5, 6):
        for checkup_k in (0, 1):
            rows.append(
                {
                    "cell_id": f"cell-{parameter_set}",
                    "parameter_set": parameter_set,
                    "replicate_id": 1,
                    "aging_mode": "cyclic" if parameter_set <= 4 else "calendar",
                    "nominal_temperature_C": 25.0,
                    "voltage_window_family": "approx_0_100",
                    "nominal_charge_C_rate": 1.0,
                    "nominal_discharge_C_rate": 1.0,
                    "profile_label": "0",
                    "checkup_k": checkup_k,
                    "checkup_k_next": checkup_k + 1,
                    "capacity_Ah_k": 1.0 - 0.05 * checkup_k,
                    "capacity_Ah_k1": 0.9 - 0.05 * checkup_k,
                    "delta_capacity_Ah": -0.1,
                    "LOG_AGE_monotonicity_clean": parameter_set != 6,
                    "quality_flags": "LOG_AGE_monotonicity_violation" if parameter_set == 6 else "",
                }
            )
    return rows


def _split_for_parameter(parameter_set: int) -> tuple[str, int]:
    if parameter_set in (1, 2):
        return "c_rate_holdout_fold", 0
    if parameter_set in (3, 4):
        return "condition_fold", 0
    return "profile_holdout_fold", 0


def _prediction_rows(
    *,
    model_setting_id: str,
    feature_group: str,
    target: str,
    y_pred_by_parameter: dict[int, float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for interval in _intervals():
        split_name, heldout_fold = _split_for_parameter(int(interval["parameter_set"]))
        parameter_set = int(interval["parameter_set"])
        rows.append(
            {
                "run_scope": "primary",
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_setting_id": model_setting_id,
                "feature_group": feature_group,
                "target": target,
                "cell_id": interval["cell_id"],
                "parameter_set": parameter_set,
                "replicate_id": interval["replicate_id"],
                "checkup_k": interval["checkup_k"],
                "checkup_k_next": interval["checkup_k_next"],
                "y_true": interval["capacity_Ah_k1"] if target == "capacity_Ah_k1" else interval["delta_capacity_Ah"],
                "y_pred": y_pred_by_parameter[parameter_set],
            }
        )
    return rows


def _adaptive_predictions() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(
        _prediction_rows(
            model_setting_id="R0_reference_hgb50",
            feature_group="F4_state_log_age_scalar",
            target="capacity_Ah_k1",
            y_pred_by_parameter={idx: 0.91 for idx in range(1, 7)},
        )
    )
    rows.extend(
        _prediction_rows(
            model_setting_id="R0_reference_hgb50",
            feature_group="F8_timestamp_weighted_stress",
            target="capacity_Ah_k1",
            y_pred_by_parameter={idx: 0.91 for idx in range(1, 7)},
        )
    )
    rows.extend(
        _prediction_rows(
            model_setting_id="R5_train_only_stressor_selected_hgb",
            feature_group="F8_timestamp_weighted_stress",
            target="delta_capacity_Ah",
            y_pred_by_parameter={idx: -0.1 for idx in range(1, 7)},
        )
    )
    return rows


def _router_predictions() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(
        _prediction_rows(
            model_setting_id="D0_R0_F4_reference",
            feature_group="F4_state_log_age_scalar",
            target="capacity_Ah_k1",
            y_pred_by_parameter={idx: 0.91 for idx in range(1, 7)},
        )
    )
    rows.extend(
        _prediction_rows(
            model_setting_id="R6_train_only_arm_selector_hgb",
            feature_group="train_only_arm_selector",
            target="delta_capacity_Ah",
            y_pred_by_parameter={
                1: -0.1,
                2: -0.1,
                3: -0.01,
                4: -0.01,
                5: -0.01,
                6: -0.01,
            },
        )
    )
    return rows


def _reconstructed_rows(tmp_path: Path) -> list[dict[str, object]]:
    interval_path = tmp_path / "interval.parquet"
    pq.write_table(pa.Table.from_pylist(_intervals()), interval_path)
    interval_by_key = _read_interval_by_key(interval_path)
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


def _condition_details(tmp_path: Path) -> dict[tuple[object, ...], dict[str, object]]:
    from mbp.analysis.reconstruction_failure_forensics import _condition_details_by_path

    interval_path = tmp_path / "interval.parquet"
    pq.write_table(pa.Table.from_pylist(_intervals()), interval_path)
    return _condition_details_by_path(_reconstructed_rows(tmp_path), _read_interval_by_key(interval_path))


def test_outside_failure_rows_detect_failed_router_guardrail(tmp_path: Path) -> None:
    rows = outside_failure_by_split_rows(_condition_details(tmp_path))
    failed = [row for row in rows if row["method_id"] == ROUTER_METHOD_ID and row["passes_guardrail"] is False]

    assert {row["split_name"] for row in failed} == {"condition_fold", "profile_holdout_fold"}
    assert all(row["relative_degradation"] > 0.05 for row in failed)


def test_hotspots_keep_qa_context_without_calling_failure_a_qa_artifact(tmp_path: Path) -> None:
    condition_details = _condition_details(tmp_path)
    outside_rows = outside_failure_by_split_rows(condition_details)
    hotspot_rows = failing_condition_hotspot_rows(condition_details, outside_rows)
    readiness = reconstruction_failure_claim_readiness_rows(outside_rows=outside_rows, hotspot_rows=hotspot_rows)
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert any(row["severe_qa_flag_rows"] > 0 for row in hotspot_rows)
    assert statuses["outside-split failure attribution"] == "supported_for_diagnostics"
    assert statuses["narrow QA artifact explanation"] == "not_supported"
    assert statuses["capacity-level reconstruction branch"] == "blocked"


def test_diagnose_reconstruction_failure_writes_bundle(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    adaptive_path = tmp_path / "adaptive.parquet"
    router_path = tmp_path / "router.parquet"
    reconstruction_dir = tmp_path / "reconstruction"
    out_dir = tmp_path / "out"
    support_path = tmp_path / "support.csv"
    reconstruction_report_path = reconstruction_dir / "target_consistency_reconstruction_report.json"
    pq.write_table(pa.Table.from_pylist(_intervals()), interval_path)
    pq.write_table(pa.Table.from_pylist(_adaptive_predictions()), adaptive_path)
    pq.write_table(pa.Table.from_pylist(_router_predictions()), router_path)
    reconstruction_dir.mkdir()
    reconstruction_report_path.write_text(
        json.dumps(
            {
                "status": "passed",
                "claim_scope": "delta_only_reconstruction_diagnostic",
                "guardrail_max_outside_degradation": 0.05,
                "inputs": {
                    "adaptive_predictions": str(adaptive_path),
                    "arm_selector_predictions": str(router_path),
                    "interval_table": str(interval_path),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with support_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["split_name", "heldout_fold", "parameter_set", "support_score", "low_support_flag"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "split_name": "condition_fold",
                "heldout_fold": 0,
                "parameter_set": 3,
                "support_score": 0.1,
                "low_support_flag": "True",
            }
        )

    report = diagnose_reconstruction_failure(
        reconstruction_report_path,
        reconstruction_dir,
        interval_path,
        out_dir,
        support_overlap_path=support_path,
    )

    assert report["status"] == "passed"
    assert report["decision_scope"] == "capacity_reconstruction_branch_closed_broad_outside_failure"
    assert report["readiness"]["architecture, policy, calibration, sequence, neural, and causality"] == "blocked"
    assert (out_dir / "reconstruction_failure_report.json").exists()
    assert (out_dir / "plots" / "outside_failure_by_split.csv").exists()
    assert (out_dir / "plots" / "failing_condition_hotspots.csv").exists()
