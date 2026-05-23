from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.knee import (
    build_threshold_warning_table,
    threshold_warning_class_balance_rows,
    write_threshold_event_labels,
    write_threshold_warning_qa,
)
from mbp.baselines.threshold_warning import (
    diagnose_threshold_warning,
    distance_feature_matrix,
    leakage_audit,
    label_status,
    lead_time_bin,
    reliability_bin_rows,
    run_threshold_warning_baselines,
)


def _interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set in range(1, 5):
        for replicate in (1, 2, 3):
            cell_id = f"P{parameter_set:03d}_{replicate}"
            capacity = 3.0
            for k in range(8):
                drop = 0.035 if parameter_set < 3 else 0.11
                next_capacity = capacity - drop
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0 if parameter_set < 3 else 40.0,
                        "voltage_window_family": "approx_0_100",
                        "nominal_charge_C_rate": 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "constant",
                        "condition_fold": parameter_set % 2,
                        "temperature_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "c_rate_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "profile_holdout_fold": 0,
                        "voltage_window_holdout_fold": 0,
                        "checkup_k": k,
                        "checkup_k_next": k + 1,
                        "t_result_k_s": float(k * 86400),
                        "t_result_k1_s": float((k + 1) * 86400),
                        "capacity_Ah_k": capacity,
                        "capacity_Ah_k1": next_capacity,
                        "delta_capacity_Ah": next_capacity - capacity,
                        "log_age_efc_delta": 10.0,
                    }
                )
                capacity = next_capacity
    return rows


def test_threshold_warning_table_and_qa(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    label_path = tmp_path / "threshold_labels.parquet"
    warning_path = tmp_path / "warning.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    write_threshold_event_labels(interval_path, tmp_path / "reports", label_path)

    table = build_threshold_warning_table(label_path, interval_path, warning_path)
    row = table.to_pylist()[0]
    assert table.num_rows == len(_interval_rows())
    assert "capacity_Ah_k1" not in row
    assert "delta_capacity_Ah" not in row
    assert row["threshold_name"] == "capacity_below_80pct_initial"

    report = write_threshold_warning_qa(
        warning_path,
        tmp_path / "qa.json",
        tmp_path / "balance.csv",
        tmp_path / "coverage.csv",
    )
    balances = threshold_warning_class_balance_rows(table.to_pylist())
    assert report["row_counts"]["rows"] == table.num_rows
    assert any(row["target"] == "event_within_3_checkups" for row in balances)


def test_threshold_warning_baseline_and_leakage_audit(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    label_path = tmp_path / "threshold_labels.parquet"
    warning_path = tmp_path / "warning.parquet"
    report_path = tmp_path / "warning_report.json"
    prediction_path = tmp_path / "predictions.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    write_threshold_event_labels(interval_path, tmp_path / "reports", label_path)
    build_threshold_warning_table(label_path, interval_path, warning_path)

    report = run_threshold_warning_baselines(
        warning_path,
        report_path,
        prediction_path,
        targets=["event_within_3_checkups"],
        model_levels=["B0_event_rate_prior", "B1_distance_to_threshold_rule", "B4_logistic_regression"],
        feature_groups=["W0_capacity_state", "W2_nominal"],
        split_views=["condition_fold", "temperature_holdout_fold"],
    )
    assert report["row_counts"]["metrics"] > 0
    assert prediction_path.exists()
    assert (tmp_path / "warning" / "threshold_warning_claim_readiness.md").exists()
    assert leakage_audit(["W0_capacity_state", "W2_nominal"])["status"] == "passed"
    diagnostics = diagnose_threshold_warning(report_path, prediction_path, warning_path, tmp_path / "warning")
    assert diagnostics["row_counts"]["lead_time_rows"] > 0
    assert (tmp_path / "warning" / "threshold_warning_reliability.csv").exists()


def test_threshold_warning_hardening_helpers() -> None:
    rows = [
        {
            "capacity_Ah_k": 2.6,
            "soh_k": 0.82,
            "checkup_k": 4,
            "event_checkup_k": 7,
            "time_to_event_checkups": 3,
            "event_observed": True,
            "event_within_3_checkups": True,
        },
        {
            "capacity_Ah_k": 2.9,
            "soh_k": 0.91,
            "checkup_k": 4,
            "event_checkup_k": None,
            "time_to_event_checkups": None,
            "event_observed": False,
            "event_within_3_checkups": False,
        },
    ]

    features = distance_feature_matrix(rows)
    assert abs(features[0][1] - 0.02) < 1e-12
    assert features[0][2] == 4.0
    assert label_status(rows[0], "event_within_3_checkups") == "positive_observed"
    assert label_status(rows[1], "event_within_3_checkups") == "right_censored_unknown"
    assert lead_time_bin(rows[0]) == "event_within_3_checkups"
    assert lead_time_bin(rows[1]) == "no_observed_event_censored"


def test_threshold_warning_reliability_bins() -> None:
    rows = [
        {
            "target": "event_within_3_checkups",
            "model_level": "B6_hist_gradient_boosting_classifier",
            "feature_group": "W2_nominal",
            "y_true": False,
            "y_prob": 0.05,
        },
        {
            "target": "event_within_3_checkups",
            "model_level": "B6_hist_gradient_boosting_classifier",
            "feature_group": "W2_nominal",
            "y_true": True,
            "y_prob": 0.85,
        },
    ]

    bins = reliability_bin_rows(rows, bins=10)
    assert {row["bin"] for row in bins} == {0, 8}
    assert all(row["row_count"] == 1 for row in bins)
