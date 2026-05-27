from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.analysis.diagnostic_horizon import (
    build_diagnostic_horizon_table,
    diagnostic_horizon_coverage_rows,
    write_diagnostic_horizon_qa,
)
from mbp.baselines import diagnostic_horizon as baseline
from mbp.baselines.diagnostic_horizon import (
    DIAGNOSTIC_HORIZON_PREDICTION_SCHEMA,
    DiagnosticHorizonFeatureEncoder,
    leakage_audit,
    run_diagnostic_horizon_baselines,
)
from mbp.data.schema_contracts import (
    DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA,
    EIS_TARGET_TABLE_V1_SCHEMA,
    PULSE_TARGET_TABLE_SCHEMA,
    validate_table,
)


def _interval_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parameter_set in range(1, 5):
        for replicate in (1, 2):
            cell_id = f"P{parameter_set:03d}_{replicate}"
            capacity = 3.2 - 0.015 * parameter_set
            for checkup_k in range(6):
                drop = 0.01 + 0.002 * parameter_set + 0.001 * checkup_k
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0 if parameter_set <= 2 else 40.0,
                        "voltage_window_family": "approx_0_100" if parameter_set % 2 else "approx_10_90",
                        "nominal_charge_C_rate": 1.0 if parameter_set <= 2 else 5.0 / 3.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "constant" if parameter_set != 4 else "profile",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "t_result_k_s": float(checkup_k * 86400),
                        "t_result_k1_s": float((checkup_k + 1) * 86400),
                        "calendar_days": 1.0,
                        "capacity_Ah_k": capacity,
                        "capacity_Ah_k1": capacity - drop,
                        "delta_capacity_Ah": -drop,
                        "condition_fold": parameter_set % 2,
                        "temperature_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "c_rate_holdout_fold": 1 if parameter_set >= 3 else 0,
                        "profile_holdout_fold": 1 if parameter_set == 4 else 0,
                        "voltage_window_holdout_fold": 1 if parameter_set % 2 == 0 else 0,
                        "log_age_efc_delta": 8.0 + parameter_set,
                        "log_age_delta_q_Ah": 1.5 + checkup_k,
                        "quality_flags": "none",
                    }
                )
                capacity -= drop
    return rows


def _diagnostic_value(parameter_set: int, checkup_k: int, replicate_id: int) -> float:
    return 0.04 + 0.02 * parameter_set + 0.006 * checkup_k + 0.001 * replicate_id


def _pulse_rows(interval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in interval_rows:
        start = _diagnostic_value(int(row["parameter_set"]), int(row["checkup_k"]), int(row["replicate_id"]))
        stop = _diagnostic_value(int(row["parameter_set"]), int(row["checkup_k_next"]), int(row["replicate_id"]))
        rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "checkup_k_next": row["checkup_k_next"],
                "soc_percent": 50.0,
                "temperature_context": "25C",
                "pulse_1s_resistance_k": start,
                "pulse_1s_resistance_k1": stop,
                "delta_pulse_1s_resistance": stop - start,
                "pulse_10ms_resistance_k": 0.5 * start,
                "pulse_10ms_resistance_k1": 0.5 * stop,
                "delta_pulse_10ms_resistance": 0.5 * (stop - start),
                "alignment_delta_s_k": 0.0,
                "alignment_delta_s_k1": 0.0,
                "quality_flags": "none",
                "schema_version": "test",
            }
        )
    return rows


def _eis_rows(interval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in interval_rows:
        start = _diagnostic_value(int(row["parameter_set"]), int(row["checkup_k"]), int(row["replicate_id"]))
        stop = _diagnostic_value(int(row["parameter_set"]), int(row["checkup_k_next"]), int(row["replicate_id"]))
        rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "checkup_k_next": row["checkup_k_next"],
                "soc_percent": 50.0,
                "temperature_context": "25C",
                "condition_fold": row["condition_fold"],
                "temperature_holdout_fold": row["temperature_holdout_fold"],
                "c_rate_holdout_fold": row["c_rate_holdout_fold"],
                "profile_holdout_fold": row["profile_holdout_fold"],
                "voltage_window_holdout_fold": row["voltage_window_holdout_fold"],
                "eis_z_real_1kHz_k": start,
                "eis_z_imag_1kHz_k": -0.2 * start,
                "eis_z_abs_1kHz_k": 0.8 * start,
                "eis_phase_1kHz_k": -5.0 - start,
                "eis_z_real_1kHz_k1": stop,
                "eis_z_imag_1kHz_k1": -0.2 * stop,
                "eis_z_abs_1kHz_k1": 0.8 * stop,
                "eis_phase_1kHz_k1": -5.0 - stop,
                "delta_eis_z_real_1kHz": stop - start,
                "delta_eis_z_abs_1kHz": 0.8 * (stop - start),
                "nyquist_re_min_k": start,
                "nyquist_re_max_k": start + 0.1,
                "nyquist_im_peak_abs_k": 0.3 * start,
                "nyquist_semicircle_width_proxy_k": 0.4 * start,
                "nyquist_re_min_k1": stop,
                "nyquist_re_max_k1": stop + 0.1,
                "nyquist_im_peak_abs_k1": 0.3 * stop,
                "nyquist_semicircle_width_proxy_k1": 0.4 * stop,
                "delta_nyquist_semicircle_width_proxy": 0.4 * (stop - start),
                "valid_modeling_fraction_k": 1.0,
                "valid_modeling_fraction_k1": 1.0,
                "alignment_delta_s_k": 0.0,
                "alignment_delta_s_k1": 0.0,
                "quality_flags": "none",
                "schema_version": "test",
                "feature_policy_version": "test",
            }
        )
    return rows


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    interval_rows = _interval_rows()
    interval_path = tmp_path / "interval.parquet"
    pulse_path = tmp_path / "pulse_targets.parquet"
    eis_path = tmp_path / "eis_targets.parquet"
    pq.write_table(pa.Table.from_pylist(interval_rows), interval_path)
    pq.write_table(pa.Table.from_pylist(_pulse_rows(interval_rows), schema=PULSE_TARGET_TABLE_SCHEMA), pulse_path)
    pq.write_table(pa.Table.from_pylist(_eis_rows(interval_rows), schema=EIS_TARGET_TABLE_V1_SCHEMA), eis_path)
    return interval_path, pulse_path, eis_path


def test_diagnostic_horizon_table_and_qa(tmp_path: Path) -> None:
    interval_path, pulse_path, eis_path = _write_inputs(tmp_path)
    out_path = tmp_path / "diagnostic_horizon.parquet"

    table = build_diagnostic_horizon_table(
        interval_path,
        pulse_path,
        eis_path,
        out_path,
        horizons=[1, 2],
        target_families=["pulse", "eis"],
    )
    rows = table.to_pylist()
    assert validate_table(table, DIAGNOSTIC_HORIZON_TABLE_V1_SCHEMA)
    assert table.schema.metadata[b"schema_version"] == b"gate82.diagnostic_horizon_table.v1"
    assert {row["horizon_checkups"] for row in rows} == {1, 2}
    assert {"pulse_1s_resistance", "eis_z_abs_1kHz"} <= {row["target_name"] for row in rows}
    h2 = next(row for row in rows if row["target_name"] == "pulse_1s_resistance" and row["checkup_k"] == 0 and row["horizon_checkups"] == 2)
    assert h2["target_checkup_k"] == 2
    assert h2["diagnostic_value_kh"] > h2["diagnostic_value_k"]
    assert h2["delta_diagnostic_value_h"] == pytest.approx(h2["diagnostic_value_kh"] - h2["diagnostic_value_k"])
    assert "capacity_Ah_k1" not in h2

    report = write_diagnostic_horizon_qa(
        out_path,
        interval_path,
        tmp_path / "diagnostic_horizon_qa.json",
        tmp_path / "diagnostic_horizon_coverage.csv",
    )
    coverage = diagnostic_horizon_coverage_rows(rows, _interval_rows())
    assert report["status"] == "passed"
    assert report["row_counts"]["rows"] == table.num_rows
    assert all(row["horizon_checkups"] in {1, 2} for row in coverage)


def test_diagnostic_horizon_baseline_smoke(tmp_path: Path) -> None:
    interval_path, pulse_path, eis_path = _write_inputs(tmp_path)
    horizon_path = tmp_path / "diagnostic_horizon.parquet"
    build_diagnostic_horizon_table(
        interval_path,
        pulse_path,
        eis_path,
        horizon_path,
        horizons=[1, 2],
        target_families=["pulse"],
    )

    report = run_diagnostic_horizon_baselines(
        horizon_path,
        tmp_path / "diagnostic_horizon_report.json",
        tmp_path / "diagnostic_horizon_predictions.parquet",
        tmp_path / "diagnostic_horizon_reports",
        targets=["pulse_1s_resistance"],
        model_levels=["DM0_persistence", "DM1_train_mean", "DM2_ridge"],
        feature_groups=["DH0_time_nominal", "DH3_capacity_plus_prior_same_diagnostic"],
        split_views=["condition_fold"],
        horizons=[1, 2],
        hgb_max_iter=3,
    )
    prediction_table = pq.read_table(tmp_path / "diagnostic_horizon_predictions.parquet")
    assert report["row_counts"]["metrics"] > 0
    assert prediction_table.schema == DIAGNOSTIC_HORIZON_PREDICTION_SCHEMA
    assert prediction_table.schema.metadata[b"schema_version"] == b"gate82.diagnostic_horizon_predictions.v1"
    assert any(row["split_name"] == "all" for row in baseline.leaderboard_rows(report["metrics"]))
    assert (tmp_path / "diagnostic_horizon_reports" / "diagnostic_horizon_claim_readiness.md").exists()
    assert (tmp_path / "diagnostic_horizon_reports" / "plots" / "diagnostic_horizon_reference_gains.csv").exists()


def test_diagnostic_horizon_feature_groups_are_prospective(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        {
            "horizon_checkups": 1,
            "checkup_k": 0,
            "calendar_day_k": 0.0,
            "cumulative_efc_k": 0.0,
            "cumulative_q_Ah_k": 0.0,
            "capacity_Ah_k": 3.0,
            "soh_k": 1.0,
            "prior_delta_capacity_Ah": None,
            "prior_capacity_slope_per_day": None,
            "diagnostic_value_k": 0.1,
            "nominal_temperature_C": 25.0,
            "nominal_charge_C_rate": 1.0,
            "nominal_discharge_C_rate": 1.0,
            "voltage_window_family": "approx_0_100",
            "profile_label": "constant",
            "aging_mode": "cyclic",
        }
    ]
    assert leakage_audit(["DH0_time_nominal", "DH3_capacity_plus_prior_same_diagnostic"])["status"] == "passed"
    encoder = DiagnosticHorizonFeatureEncoder.fit(rows, "DH3_capacity_plus_prior_same_diagnostic")
    assert "diagnostic_value_k" in encoder.numeric_columns
    assert "diagnostic_value_kh" not in encoder.numeric_columns

    monkeypatch.setitem(
        baseline.NUMERIC_FEATURES,
        "DH3_capacity_plus_prior_same_diagnostic",
        baseline.NUMERIC_FEATURES["DH3_capacity_plus_prior_same_diagnostic"] + ("diagnostic_value_kh",),
    )
    assert leakage_audit(["DH3_capacity_plus_prior_same_diagnostic"])["status"] == "failed"
    with pytest.raises(ValueError, match="forbidden future target"):
        DiagnosticHorizonFeatureEncoder.fit(rows, "DH3_capacity_plus_prior_same_diagnostic")
