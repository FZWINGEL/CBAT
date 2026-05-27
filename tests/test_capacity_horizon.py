from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pyarrow as pa

from mbp.analysis.capacity_horizon import (
    build_capacity_horizon_table,
    build_capacity_horizon_trajectory_features,
    capacity_horizon_coverage_rows,
    capacity_horizon_trajectory_coverage_rows,
    write_capacity_horizon_qa,
    write_capacity_horizon_trajectory_qa,
)
from mbp.baselines.capacity_horizon import (
    CAPACITY_HORIZON_PREDICTION_SCHEMA,
    HorizonFeatureEncoder,
    diagnose_capacity_horizon,
    diagnose_capacity_horizon_trajectory,
    leakage_audit,
    prior_slope_failure_mode_rows,
    prospective_feature_audit_rows,
    predict_capacity_horizon,
    run_capacity_horizon_baselines,
)
from mbp.data.schema_contracts import (
    CAPACITY_HORIZON_TABLE_V1_SCHEMA,
    CAPACITY_HORIZON_TRAJECTORY_FEATURES_V1_SCHEMA,
    validate_table,
)


def _interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set in range(1, 5):
        for replicate in (1, 2):
            cell_id = f"P{parameter_set:03d}_{replicate}"
            capacity = 3.1 - 0.02 * parameter_set
            for checkup_k in range(6):
                drop = 0.02 + 0.006 * parameter_set + 0.002 * checkup_k
                next_capacity = capacity - drop
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0 if parameter_set < 3 else 40.0,
                        "voltage_window_family": "approx_0_100",
                        "nominal_charge_C_rate": 1.0 if parameter_set < 3 else 5.0 / 3.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "constant" if parameter_set != 4 else "profile",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "t_result_k_s": float(checkup_k * 86400),
                        "t_result_k1_s": float((checkup_k + 1) * 86400),
                        "duration_h": 24.0,
                        "calendar_days": 1.0,
                        "capacity_Ah_k": capacity,
                        "capacity_Ah_k1": next_capacity,
                        "delta_capacity_Ah": next_capacity - capacity,
                        "condition_fold": parameter_set % 2,
                        "temperature_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "c_rate_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "profile_holdout_fold": 1 if parameter_set == 4 else 0,
                        "voltage_window_holdout_fold": 1 if parameter_set in {2, 4} else 0,
                        "log_age_row_count": 100,
                        "log_age_efc_delta": 10.0 + parameter_set,
                        "log_age_delta_q_Ah": 2.0 + checkup_k,
                        "quality_flags": "",
                    }
                )
                capacity = next_capacity
    return rows


def test_capacity_horizon_table_and_qa(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "capacity_horizon.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)

    table = build_capacity_horizon_table(interval_path, horizon_path, horizons=[1, 2, 3])
    rows = table.to_pylist()
    assert validate_table(table, CAPACITY_HORIZON_TABLE_V1_SCHEMA)
    assert table.schema.metadata[b"schema_version"] == b"gate60.capacity_horizon_table.v1"
    assert {row["horizon_checkups"] for row in rows} == {1, 2, 3}
    h3 = next(row for row in rows if row["checkup_k"] == 0 and row["horizon_checkups"] == 3)
    assert h3["target_checkup_k"] == 3
    assert h3["delta_capacity_Ah_h"] == h3["capacity_Ah_kh"] - h3["capacity_Ah_k"]
    assert h3["horizon_interval_count"] == 3
    assert "capacity_Ah_k1" not in h3

    report = write_capacity_horizon_qa(
        horizon_path,
        interval_path,
        tmp_path / "qa.json",
        tmp_path / "coverage.csv",
    )
    coverage = capacity_horizon_coverage_rows(rows, _interval_rows())
    assert report["row_counts"]["rows"] == table.num_rows
    assert any(row["horizon_checkups"] == 3 for row in coverage)


def test_capacity_horizon_feature_policy_and_prior_slope() -> None:
    rows = build_capacity_horizon_rows_for_test(_interval_rows())
    assert leakage_audit(["K0_prior_capacity", "K2_nominal_condition"])["status"] == "passed"
    oracle = leakage_audit(["K3_oracle_exposure_diagnostic"])
    assert oracle["rows"][0]["claim_scope"] == "oracle_diagnostic_only"
    encoder = HorizonFeatureEncoder.fit(rows, "K2_nominal_condition")
    assert not (set(encoder.numeric_columns) & {"horizon_log_age_efc_delta"})
    prediction = predict_capacity_horizon(
        "MH1_prior_slope_linear",
        "prior_slope",
        rows,
        [rows[0]],
        "delta_capacity_Ah_h",
        seed=42,
        hgb_max_iter=5,
    )[0]
    assert prediction == 0.0 or prediction < 0.0


def test_capacity_horizon_trajectory_features_and_qa(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "capacity_horizon.parquet"
    trajectory_path = tmp_path / "capacity_horizon_trajectory.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    build_capacity_horizon_table(interval_path, horizon_path, horizons=[1, 2])

    table = build_capacity_horizon_trajectory_features(horizon_path, interval_path, trajectory_path)
    rows = table.to_pylist()
    assert validate_table(table, CAPACITY_HORIZON_TRAJECTORY_FEATURES_V1_SCHEMA)
    assert table.schema.metadata[b"schema_version"] == b"gate62.capacity_horizon_trajectory_features.v1"
    row_k3 = next(row for row in rows if row["checkup_k"] == 3 and row["horizon_checkups"] == 1)
    assert row_k3["prior_history_length"] == 3
    assert row_k3["prior_capacity_delta_lag1"] < 0
    assert row_k3["prior_delta_std_3"] >= 0
    assert "capacity_Ah_kh" not in row_k3

    report = write_capacity_horizon_trajectory_qa(
        trajectory_path,
        horizon_path,
        tmp_path / "trajectory_qa.json",
        tmp_path / "trajectory_coverage.csv",
    )
    coverage = capacity_horizon_trajectory_coverage_rows(rows, pq.read_table(horizon_path).to_pylist())
    assert report["status"] == "passed"
    assert report["row_counts"]["rows"] == table.num_rows
    assert any(row["zero_prior_history_rows"] > 0 for row in coverage)


def test_capacity_horizon_trajectory_feature_groups_are_prospective() -> None:
    rows = build_capacity_horizon_rows_for_test(_interval_rows())
    trajectory_rows = []
    for row in rows:
        trajectory_rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "target_checkup_k": row["target_checkup_k"],
                "horizon_checkups": row["horizon_checkups"],
                "prior_history_length": 2,
                "prior_capacity_delta_lag1": -0.01,
                "prior_capacity_delta_lag2": -0.02,
                "prior_capacity_delta_lag3": None,
                "prior_delta_mean_3": -0.015,
                "prior_delta_std_3": 0.005,
                "prior_delta_min_3": -0.02,
                "prior_delta_max_3": -0.01,
                "prior_delta_mean_all": -0.015,
                "prior_delta_std_all": 0.005,
                "prior_slope_per_day_mean_3": -0.015,
                "prior_slope_per_day_std_3": 0.005,
                "prior_capacity_curvature_lag1": 0.01,
                "prior_capacity_acceleration_mean_3": 0.01,
                "prior_capacity_volatility_3": 0.005,
                "prior_capacity_increase_count": 0,
                "prior_capacity_increase_fraction": 0.0,
                "prior_capacity_range_Ah_all": 0.03,
                "prior_delta_abs_max_all": 0.02,
                "trajectory_quality_flags": "none",
                "schema_version": "test",
            }
        )
    merged = [dict(row) | {key: value for key, value in trajectory_rows[index].items()} for index, row in enumerate(rows)]
    audit = leakage_audit(["K4_prior_trajectory_shape", "K5_nominal_plus_trajectory_shape"])
    assert audit["status"] == "passed"
    encoder = HorizonFeatureEncoder.fit(merged, "K5_nominal_plus_trajectory_shape")
    assert "prior_delta_mean_3" in encoder.numeric_columns
    assert "horizon_log_age_efc_delta" not in encoder.numeric_columns


def test_capacity_horizon_baseline_smoke(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "capacity_horizon.parquet"
    report_path = tmp_path / "capacity_horizon_report.json"
    predictions_path = tmp_path / "capacity_horizon_predictions.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    build_capacity_horizon_table(interval_path, horizon_path, horizons=[1, 2])

    report = run_capacity_horizon_baselines(
        horizon_path,
        report_path,
        predictions_path,
        tmp_path / "capacity_horizon",
        targets=["capacity_Ah_kh", "delta_capacity_Ah_h"],
        model_levels=["MH0_persistence", "MH1_prior_slope_linear", "MH2_ridge"],
        feature_groups=["K0_prior_capacity", "K2_nominal_condition"],
        split_views=["condition_fold", "c_rate_holdout_fold"],
        horizons=[1, 2],
        hgb_max_iter=5,
    )
    prediction_table = pq.read_table(predictions_path)
    assert report["row_counts"]["metrics"] > 0
    assert prediction_table.schema == CAPACITY_HORIZON_PREDICTION_SCHEMA
    assert prediction_table.schema.metadata[b"schema_version"] == b"gate60.capacity_horizon_predictions.v1"
    assert (tmp_path / "capacity_horizon" / "capacity_horizon_claim_readiness.md").exists()
    assert (tmp_path / "capacity_horizon" / "plots" / "horizon_performance.csv").exists()


def test_capacity_horizon_baseline_with_trajectory_sidecar(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "capacity_horizon.parquet"
    trajectory_path = tmp_path / "capacity_horizon_trajectory.parquet"
    report_path = tmp_path / "capacity_horizon_trajectory_report.json"
    predictions_path = tmp_path / "capacity_horizon_trajectory_predictions.parquet"
    out_dir = tmp_path / "capacity_horizon_trajectory"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    build_capacity_horizon_table(interval_path, horizon_path, horizons=[1, 2])
    build_capacity_horizon_trajectory_features(horizon_path, interval_path, trajectory_path)

    report = run_capacity_horizon_baselines(
        horizon_path,
        report_path,
        predictions_path,
        out_dir,
        trajectory_path,
        targets=["capacity_Ah_kh"],
        model_levels=["MH0_persistence", "MH1_prior_slope_linear", "MH3_hist_gradient_boosting"],
        feature_groups=["K2_nominal_condition", "K5_nominal_plus_trajectory_shape"],
        split_views=["condition_fold"],
        horizons=[1, 2],
        hgb_max_iter=5,
    )
    diagnostic = diagnose_capacity_horizon_trajectory(report_path, predictions_path, horizon_path, out_dir)

    assert report["row_counts"]["metrics"] > 0
    assert report["optional_inputs"]["trajectory_features"] == str(trajectory_path)
    assert diagnostic["row_counts"]["trajectory_gain_rows"] > 0
    assert (out_dir / "trajectory_shape_claim_readiness.md").exists()


def test_capacity_horizon_diagnostics_render_forensics(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    horizon_path = tmp_path / "capacity_horizon.parquet"
    report_path = tmp_path / "capacity_horizon_report.json"
    predictions_path = tmp_path / "capacity_horizon_predictions.parquet"
    out_dir = tmp_path / "capacity_horizon"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    build_capacity_horizon_table(interval_path, horizon_path, horizons=[2])
    run_capacity_horizon_baselines(
        horizon_path,
        report_path,
        predictions_path,
        out_dir,
        targets=["capacity_Ah_kh", "delta_capacity_Ah_h"],
        model_levels=["MH0_persistence", "MH1_prior_slope_linear", "MH3_hist_gradient_boosting"],
        feature_groups=["K2_nominal_condition", "K3_oracle_exposure_diagnostic"],
        split_views=["c_rate_holdout_fold"],
        horizons=[2],
        hgb_max_iter=5,
    )

    report = diagnose_capacity_horizon(report_path, predictions_path, horizon_path, out_dir)

    assert report["row_counts"]["gain_rows"] > 0
    assert (out_dir / "multi_horizon_error_forensics.md").exists()
    assert (out_dir / "multi_horizon_next_branch_readiness.md").exists()
    assert (out_dir / "plots" / "c_rate_condition_horizon_errors.csv").exists()
    assert report["readiness"]["sequence_or_neural_models"] == "blocked"


def test_prior_slope_failure_modes_bin_hgb_vs_reference() -> None:
    horizon_rows = build_capacity_horizon_rows_for_test(_interval_rows())
    row = horizon_rows[0]
    base = {
        "schema_version": "test",
        "run_scope": "primary",
        "split_name": "condition_fold",
        "heldout_fold": 0,
        "target": "capacity_Ah_kh",
        "cell_id": row["cell_id"],
        "parameter_set": row["parameter_set"],
        "replicate_id": row["replicate_id"],
        "checkup_k": row["checkup_k"],
        "target_checkup_k": row["target_checkup_k"],
        "horizon_checkups": row["horizon_checkups"],
        "y_true": 3.0,
    }
    predictions = [
        base | {"model_level": "MH3_hist_gradient_boosting", "feature_group": "K2_nominal_condition", "y_pred": 2.8},
        base | {"model_level": "MH1_prior_slope_linear", "feature_group": "prior_slope", "y_pred": 2.95},
    ]

    rows = prior_slope_failure_mode_rows(predictions, horizon_rows)

    assert rows
    assert rows[0]["hgb_minus_prior_slope_mae"] > 0
    assert rows[0]["hgb_wins_fraction"] == 0.0


def test_prospective_feature_audit_blocks_future_exposure_candidates() -> None:
    rows = prospective_feature_audit_rows()
    existing_oracle = next(row for row in rows if row["feature_family"] == "K3_oracle_exposure_diagnostic")
    future_candidate = next(row for row in rows if row["feature_family"] == "candidate_actual_horizon_exposure")
    prior_candidate = next(row for row in rows if row["feature_family"] == "candidate_prior_trajectory_shape")

    assert existing_oracle["allowed_for_future_prospective_branch"] is False
    assert future_candidate["claim_scope"] == "oracle_diagnostic_only"
    assert prior_candidate["allowed_for_future_prospective_branch"] is True


def build_capacity_horizon_rows_for_test(interval_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_cell = {}
    for row in interval_rows:
        by_cell.setdefault(str(row["cell_id"]), []).append(row)
    first_cell = next(iter(by_cell.values()))
    from mbp.analysis.capacity_horizon import _cell_horizon_rows

    return _cell_horizon_rows(first_cell, (1, 2))
