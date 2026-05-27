from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.support_reliability import (
    condition_support_rows,
    diagnose_support_reliability,
    selective_capacity_performance_rows,
    selective_policy_performance_rows,
    selective_warning_performance_rows,
    support_reliability_claim_readiness_rows,
)


def _interval_rows() -> list[dict[str, object]]:
    specs = [
        (1, 0, 25.0, 1.0, "wide", "constant"),
        (2, 1, 25.0, 1.0, "wide", "constant"),
        (3, 1, 40.0, 2.0, "narrow", "profile"),
    ]
    rows: list[dict[str, object]] = []
    for parameter_set, condition_fold, temperature, c_rate, voltage, profile in specs:
        rows.append(
            {
                "cell_id": f"P{parameter_set:03d}_1",
                "parameter_set": parameter_set,
                "replicate_id": 1,
                "aging_mode": "cyclic",
                "nominal_temperature_C": temperature,
                "voltage_window_family": voltage,
                "nominal_charge_C_rate": c_rate,
                "nominal_discharge_C_rate": 1.0,
                "profile_label": profile,
                "checkup_k": 0,
                "condition_fold": condition_fold,
                "temperature_holdout_fold": 1 if temperature > 30.0 else 0,
                "c_rate_holdout_fold": 1 if c_rate > 1.5 else 0,
                "profile_holdout_fold": 1 if profile == "profile" else 0,
                "voltage_window_holdout_fold": 1 if voltage == "narrow" else 0,
            }
        )
    return rows


def _support_lookup() -> dict[tuple[str, int], dict[str, object]]:
    return {
        ("condition_fold", 1): {
            "support_score": 1.0,
            "nearest_distance": 0.0,
            "exact_nominal_match_count": 1,
            "same_stressor_support_count": 2,
        },
        ("condition_fold", 2): {
            "support_score": 0.1,
            "nearest_distance": 9.0,
            "exact_nominal_match_count": 0,
            "same_stressor_support_count": 0,
        },
    }


def test_condition_support_scores_use_train_only_metadata() -> None:
    rows = condition_support_rows(_interval_rows())
    condition_fold_p1 = next(
        row for row in rows if row["split_name"] == "condition_fold" and row["parameter_set"] == 1
    )

    assert condition_fold_p1["exact_nominal_match_count"] == 1
    assert condition_fold_p1["nearest_parameter_set"] == 2
    assert condition_fold_p1["nearest_distance"] == 0.0
    assert condition_fold_p1["support_score"] == 1.0


def test_selective_capacity_performance_improves_on_high_support_rows() -> None:
    prediction_rows = [
        {
            "split_name": "condition_fold",
            "parameter_set": 1,
            "cell_id": "P001_1",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "model_level": "MH3_hist_gradient_boosting",
            "feature_group": "K2_nominal_condition",
            "y_true": -0.1,
            "y_pred": -0.11,
        },
        {
            "split_name": "condition_fold",
            "parameter_set": 2,
            "cell_id": "P002_1",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "model_level": "MH3_hist_gradient_boosting",
            "feature_group": "K2_nominal_condition",
            "y_true": -0.1,
            "y_pred": -0.5,
        },
    ]

    rows = selective_capacity_performance_rows(prediction_rows, _support_lookup(), retentions=(1.0, 0.5))
    full = next(row for row in rows if row["retention_fraction"] == 1.0)
    selected = next(row for row in rows if row["retention_fraction"] == 0.5)

    assert selected["rows_retained"] == 1
    assert selected["mae"] < full["mae"]


def test_selective_warning_performance_reports_brier_and_ece() -> None:
    prediction_rows = [
        {
            "split_name": "condition_fold",
            "parameter_set": 1,
            "cell_id": "P001_1",
            "target": "event_within_3_checkups",
            "model_level": "B6_hist_gradient_boosting_classifier",
            "feature_group": "W2_nominal",
            "y_true": True,
            "y_prob": 0.9,
        },
        {
            "split_name": "condition_fold",
            "parameter_set": 2,
            "cell_id": "P002_1",
            "target": "event_within_3_checkups",
            "model_level": "B6_hist_gradient_boosting_classifier",
            "feature_group": "W2_nominal",
            "y_true": False,
            "y_prob": 0.9,
        },
    ]

    rows = selective_warning_performance_rows(prediction_rows, _support_lookup(), retentions=(1.0, 0.5))
    full = next(row for row in rows if row["retention_fraction"] == 1.0)
    selected = next(row for row in rows if row["retention_fraction"] == 0.5)

    assert selected["positive_count"] == 1
    assert selected["brier"] < full["brier"]
    assert selected["ece_10_bin"] >= 0.0


def test_selective_policy_performance_excludes_oracle_and_improves_sign_accuracy() -> None:
    pairwise_rows = [
        {
            "contrast_id": "c1",
            "contrast_family": "charge_c_rate",
            "split_name": "condition_fold",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "model_level": "MH3_hist_gradient_boosting",
            "feature_group": "K2_nominal_condition",
            "arm_a_parameter_set": 1,
            "arm_b_parameter_set": 1,
            "effect_abs_error": 0.01,
            "sign_evaluable": True,
            "sign_correct": True,
            "claim_scope": "prospective_supported_contrast_diagnostic",
        },
        {
            "contrast_id": "c2",
            "contrast_family": "charge_c_rate",
            "split_name": "condition_fold",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "model_level": "MH3_hist_gradient_boosting",
            "feature_group": "K2_nominal_condition",
            "arm_a_parameter_set": 2,
            "arm_b_parameter_set": 2,
            "effect_abs_error": 0.4,
            "sign_evaluable": True,
            "sign_correct": False,
            "claim_scope": "prospective_supported_contrast_diagnostic",
        },
        {
            "contrast_id": "oracle",
            "contrast_family": "charge_c_rate",
            "split_name": "condition_fold",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "model_level": "MH3_hist_gradient_boosting",
            "feature_group": "K3_oracle_exposure_diagnostic",
            "arm_a_parameter_set": 1,
            "arm_b_parameter_set": 1,
            "effect_abs_error": 0.0,
            "sign_evaluable": True,
            "sign_correct": True,
            "claim_scope": "oracle_diagnostic_only",
        },
    ]

    rows = selective_policy_performance_rows(pairwise_rows, _support_lookup(), retentions=(1.0, 0.5))
    all_rows = [row for row in rows if row["contrast_family"] == "all"]
    full = next(row for row in all_rows if row["retention_fraction"] == 1.0)
    selected = next(row for row in all_rows if row["retention_fraction"] == 0.5)

    assert full["rows_retained"] == 2
    assert selected["sign_accuracy"] > full["sign_accuracy"]


def test_support_reliability_claim_readiness_keeps_blocked_claims_blocked() -> None:
    readiness = support_reliability_claim_readiness_rows(
        capacity_rows=[],
        warning_rows=[],
        policy_rows=[],
    )
    statuses = {row["claim_area"]: row["status"] for row in readiness}

    assert statuses["policy recommendation"] == "blocked"
    assert statuses["causal or same-cell counterfactual claims"] == "blocked"
    assert statuses["calibrated risk or CBAT readiness"] == "blocked"


def test_diagnose_support_reliability_writes_report_bundle(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "horizon.parquet"
    capacity_predictions_path = tmp_path / "capacity_predictions.parquet"
    warning_path = tmp_path / "warning.parquet"
    warning_predictions_path = tmp_path / "warning_predictions.parquet"
    policy_pairwise_path = tmp_path / "policy_pairwise.csv"
    out_dir = tmp_path / "support"
    interval_rows = _interval_rows()
    pq.write_table(pa.Table.from_pylist(interval_rows), interval_path)
    pq.write_table(pa.Table.from_pylist([{"cell_id": "P001_1", "parameter_set": 1}]), horizon_path)
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "split_name": "condition_fold",
                    "parameter_set": 1,
                    "cell_id": "P001_1",
                    "target": "delta_capacity_Ah_h",
                    "horizon_checkups": 2,
                    "model_level": "MH3_hist_gradient_boosting",
                    "feature_group": "K2_nominal_condition",
                    "y_true": -0.1,
                    "y_pred": -0.11,
                }
            ]
        ),
        capacity_predictions_path,
    )
    pq.write_table(pa.Table.from_pylist([{"cell_id": "P001_1", "parameter_set": 1}]), warning_path)
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "split_name": "condition_fold",
                    "parameter_set": 1,
                    "cell_id": "P001_1",
                    "target": "event_within_3_checkups",
                    "model_level": "B6_hist_gradient_boosting_classifier",
                    "feature_group": "W2_nominal",
                    "y_true": True,
                    "y_prob": 0.9,
                }
            ]
        ),
        warning_predictions_path,
    )
    with policy_pairwise_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "contrast_id",
                "contrast_family",
                "split_name",
                "target",
                "horizon_checkups",
                "model_level",
                "feature_group",
                "arm_a_parameter_set",
                "arm_b_parameter_set",
                "effect_abs_error",
                "sign_evaluable",
                "sign_correct",
                "claim_scope",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "contrast_id": "c1",
                "contrast_family": "charge_c_rate",
                "split_name": "condition_fold",
                "target": "delta_capacity_Ah_h",
                "horizon_checkups": 2,
                "model_level": "MH3_hist_gradient_boosting",
                "feature_group": "K2_nominal_condition",
                "arm_a_parameter_set": 1,
                "arm_b_parameter_set": 1,
                "effect_abs_error": 0.01,
                "sign_evaluable": True,
                "sign_correct": True,
                "claim_scope": "prospective_supported_contrast_diagnostic",
            }
        )

    report = diagnose_support_reliability(
        interval_path,
        horizon_path,
        capacity_predictions_path,
        warning_path,
        warning_predictions_path,
        policy_pairwise_path,
        out_dir,
    )

    assert report["status"] == "passed"
    assert (out_dir / "support_reliability_report.json").exists()
    assert (out_dir / "support_reliability_claim_readiness.md").exists()
    assert (out_dir / "plots" / "selective_capacity_performance.csv").exists()
