from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pyarrow as pa

from mbp.analysis.capacity_horizon import (
    build_capacity_horizon_table,
    capacity_horizon_coverage_rows,
    write_capacity_horizon_qa,
)
from mbp.baselines.capacity_horizon import (
    CAPACITY_HORIZON_PREDICTION_SCHEMA,
    HorizonFeatureEncoder,
    leakage_audit,
    predict_capacity_horizon,
    run_capacity_horizon_baselines,
)
from mbp.data.schema_contracts import CAPACITY_HORIZON_TABLE_V1_SCHEMA, validate_table


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


def build_capacity_horizon_rows_for_test(interval_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_cell = {}
    for row in interval_rows:
        by_cell.setdefault(str(row["cell_id"]), []).append(row)
    first_cell = next(iter(by_cell.values()))
    from mbp.analysis.capacity_horizon import _cell_horizon_rows

    return _cell_horizon_rows(first_cell, (1, 2))
