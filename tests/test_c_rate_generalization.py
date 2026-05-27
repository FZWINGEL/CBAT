from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.c_rate_generalization import (
    c_rate_claim_readiness_rows,
    c_rate_condition_hotspot_rows,
    c_rate_metric_summary_rows,
    c_rate_stress_error_rows,
    diagnose_c_rate_generalization,
)
from mbp.analysis.support_reliability import condition_support_rows


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def _interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    specs = [
        (1, 0, 0, 0, 25.0, 0.5, 0.5, "wide", "constant"),
        (2, 1, 0, 1, 25.0, 1.0, 1.0, "wide", "constant"),
        (3, 2, 1, 2, 10.0, 2.0, 1.0, "narrow", "constant"),
    ]
    for parameter_set, condition_fold, c_rate_fold, heldout_fold, temp, charge, discharge, voltage, profile in specs:
        for replicate_id in (1, 2):
            for checkup_k in (0, 1):
                rows.append(
                    {
                        "cell_id": f"P{parameter_set:03d}_{replicate_id}",
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": temp,
                        "voltage_window_family": voltage,
                        "nominal_charge_C_rate": charge,
                        "nominal_discharge_C_rate": discharge,
                        "profile_label": profile,
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "condition_fold": condition_fold,
                        "temperature_holdout_fold": 0 if temp == 25.0 else 1,
                        "c_rate_holdout_fold": c_rate_fold,
                        "profile_holdout_fold": 0 if profile == "constant" else 1,
                        "voltage_window_holdout_fold": 0 if voltage == "wide" else 1,
                    }
                )
    return rows


def _prediction_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for target in ("capacity_Ah_k1", "delta_capacity_Ah"):
        for parameter_set, error in ((1, 0.01), (2, 0.02), (3, 0.3)):
            for replicate_id in (1, 2):
                for checkup_k in (0, 1):
                    y_true = 1.0 if target == "capacity_Ah_k1" else -0.1
                    rows.append(
                        {
                            "split_name": "c_rate_holdout_fold",
                            "heldout_fold": 0 if parameter_set in (1, 2) else 1,
                            "run_scope": "primary",
                            "model_level": "L2_hist_gradient_boosting",
                            "feature_group": "F8_timestamp_weighted_stress",
                            "target": target,
                            "cell_id": f"P{parameter_set:03d}_{replicate_id}",
                            "parameter_set": parameter_set,
                            "replicate_id": replicate_id,
                            "checkup_k": checkup_k,
                            "checkup_k_next": checkup_k + 1,
                            "y_true": y_true,
                            "y_pred": y_true + error,
                        }
                    )
    return rows


def _stress_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for interval in _interval_rows():
        parameter_set = int(interval["parameter_set"])
        rows.append(
            {
                "cell_id": interval["cell_id"],
                "parameter_set": parameter_set,
                "replicate_id": interval["replicate_id"],
                "checkup_k": interval["checkup_k"],
                "checkup_k_next": interval["checkup_k_next"],
                "cold_time_h": 10.0 if parameter_set == 3 else 0.5,
                "high_voltage_time_h": 4.0 if parameter_set == 3 else 0.0,
                "abs_current_ge_1C_time_h": 6.0 if parameter_set == 3 else 0.0,
                "stress_coverage_fraction": 0.99,
                "delta_capacity_per_day": -999.0,
            }
        )
    return rows


def _report_rows() -> list[dict[str, object]]:
    return [
        {
            "split_name": "c_rate_holdout_fold",
            "target": "delta_capacity_Ah",
            "model_level": "L2_hist_gradient_boosting",
            "feature_group": "F8_timestamp_weighted_stress",
            "heldout_fold": 1,
            "mae": 0.1,
            "condition_mean_mae": 0.12,
            "worst_condition_mae": 0.3,
            "test_rows": 8,
            "test_parameter_sets": 3,
        },
        {
            "split_name": "condition_fold",
            "target": "delta_capacity_Ah",
            "model_level": "L2_hist_gradient_boosting",
            "feature_group": "F8_timestamp_weighted_stress",
            "heldout_fold": 0,
            "mae": 0.01,
            "condition_mean_mae": 0.01,
            "worst_condition_mae": 0.02,
            "test_rows": 4,
            "test_parameter_sets": 1,
        },
    ]


def test_c_rate_hotspots_attach_support_and_sort_by_error() -> None:
    support = {
        int(row["parameter_set"]): row
        for row in condition_support_rows(_interval_rows())
        if row["split_name"] == "c_rate_holdout_fold"
    }
    conditions = {int(row["parameter_set"]): row for row in _interval_rows()}

    rows = c_rate_condition_hotspot_rows(_prediction_rows(), conditions, support)

    assert rows[0]["parameter_set"] == 3
    assert rows[0]["mae"] > rows[-1]["mae"]
    assert "support_score" in rows[0]
    assert rows[0]["claim_scope"] == "condition_error_hotspot_diagnostic"


def test_stress_error_rows_exclude_target_derived_stress_fields() -> None:
    conditions = {int(row["parameter_set"]): row for row in _interval_rows()}

    rows = c_rate_stress_error_rows(
        _prediction_rows(),
        _stress_rows(),
        conditions,
        primary_feature_group="F8_timestamp_weighted_stress",
    )

    fields = {row["stress_feature"] for row in rows}
    assert "cold_time_h" in fields
    assert "delta_capacity_per_day" not in fields
    cold = next(row for row in rows if row["stress_feature"] == "cold_time_h")
    assert cold["high_error_mean_feature"] > cold["lower_error_mean_feature"]


def test_claim_readiness_blocks_repair_and_architecture() -> None:
    readiness = c_rate_claim_readiness_rows(
        metric_summary_rows=c_rate_metric_summary_rows(_report_rows()),
        hotspot_rows=[{"x": 1}],
        support_overlap_rows=[{"low_support_flag": True}],
        stress_error_rows=[{"x": 1}],
    )
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert statuses["C-rate root-cause diagnostics"] == "supported_for_diagnostics"
    assert statuses["new C-rate repair model readiness"] == "blocked"
    assert statuses["architecture or policy readiness"] == "blocked"


def test_diagnose_c_rate_generalization_writes_report_bundle(tmp_path: Path) -> None:
    report_path = tmp_path / "capacity_report.json"
    predictions_path = tmp_path / "predictions.parquet"
    interval_path = tmp_path / "interval.parquet"
    stress_path = tmp_path / "stress.parquet"
    out_dir = tmp_path / "out"

    report_path.write_text(json.dumps({"schema_version": "test", "metrics": _report_rows()}), encoding="utf-8")
    _write_parquet(predictions_path, _prediction_rows())
    _write_parquet(interval_path, _interval_rows())
    _write_parquet(stress_path, _stress_rows())

    report = diagnose_c_rate_generalization(
        report_path,
        predictions_path,
        interval_path,
        out_dir,
        stress_features_path=stress_path,
    )

    assert report["status"] == "passed"
    assert report["row_counts"]["condition_hotspot_rows"] > 0
    assert report["readiness"]["new C-rate repair model readiness"] == "blocked"
    assert (out_dir / "c_rate_failure_report.json").exists()
    assert (out_dir / "c_rate_condition_hotspots.csv").exists()
    assert (out_dir / "c_rate_support_overlap.csv").exists()
