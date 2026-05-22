"""Tests for Milestone 0.6 LOG_AGE stress-feature sidecar."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.baselines.capacity import DIAGNOSTIC_LEAKAGE_FIELDS
from mbp.baselines.capacity import FeatureEncoder
from mbp.baselines.capacity import NUMERIC_FEATURES
from mbp.baselines.capacity import load_baseline_rows
from mbp.baselines.capacity import run_capacity_baselines
from mbp.data.products.current_sign_audit import audit_current_sign
from mbp.data.products.stress_features import build_interval_stress_features
from mbp.data.products.stress_features import run_stress_feature_qa
from mbp.data.schema_contracts import INTERVAL_STRESS_FEATURES_SCHEMA
from mbp.data.schema_contracts import INTERVAL_SUBSET_REGISTRY_SCHEMA
from mbp.data.schema_contracts import INTERVAL_TABLE_SCHEMA
from mbp.data.schema_contracts import MODALITY_TABLE_LOG_AGE_SCHEMA
from mbp.data.schema_contracts import validate_table


def _write_interval_table(tmp_path: Path) -> Path:
    rows = []
    for checkup_k, start, end, cap_k, cap_k1 in (
        (0, 100.0, 200.0, 3.0, 2.9),
        (1, 200.0, 320.0, 2.9, 2.75),
    ):
        rows.append(
            {
                "cell_id": "P001_1",
                "parameter_set": 1,
                "replicate_id": 1,
                "aging_mode": "cyclic",
                "nominal_temperature_C": 10.0,
                "voltage_window": "2.50 V - 4.20 V",
                "voltage_window_family": "approx_0_100",
                "soc_window_approx": "0-100",
                "nominal_charge_C_rate": 5.0 / 3.0,
                "nominal_discharge_C_rate": 1.0,
                "profile_label": "CC",
                "checkup_k": checkup_k,
                "checkup_k_next": checkup_k + 1,
                "t_result_k_s": start,
                "t_result_k1_s": end,
                "duration_s": end - start,
                "duration_h": (end - start) / 3600.0,
                "calendar_days": (end - start) / 86400.0,
                "capacity_Ah_k": cap_k,
                "capacity_Ah_k1": cap_k1,
                "delta_capacity_Ah": cap_k1 - cap_k,
                "delta_capacity_soh": -0.03,
                "condition_fold": 0,
                "temperature_holdout_fold": 1,
                "voltage_window_holdout_fold": 1,
                "soc_window_holdout_fold": 1,
                "c_rate_holdout_fold": 1,
                "profile_holdout_fold": 0,
                "replicate_calibration_fold": 0,
                "time_horizon_fold": 0,
                "log_age_row_count": 4,
                "log_age_elapsed_s": end - start,
                "log_age_efc_delta": 1.0,
                "log_age_delta_q_Ah": 2.0,
                "log_age_mean_voltage_V": 3.8,
                "log_age_min_voltage_V": 3.2,
                "log_age_max_voltage_V": 4.2,
                "log_age_mean_temperature_C": 15.0,
                "log_age_min_temperature_C": 0.0,
                "log_age_max_temperature_C": 42.0,
                "log_age_mean_current_A": 0.0,
                "log_age_mean_abs_current_A": 3.0,
                "log_age_max_abs_current_A": 5.5,
                "log_age_mean_soc": 55.0,
                "log_age_min_soc": 10.0,
                "log_age_max_soc": 90.0,
                "log_age_capacity_diag_rows_masked": 0,
                "log_age_r0_diag_rows_masked": 0,
                "log_age_r1_diag_rows_masked": 0,
                "LOG_AGE_available": True,
                "log_age_monotonicity_violation_count": 0,
                "log_age_timestamp_decrease_count": 0,
                "log_age_efc_decrease_count": 0,
                "log_age_max_timestamp_drop_s": 0.0,
                "log_age_max_efc_drop": 0.0,
                "LOG_AGE_monotonicity_clean": True,
                "quality_flags": "",
                "schema_version": "gate2.interval.v1",
            }
        )
    path = tmp_path / "interval_table.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=INTERVAL_TABLE_SCHEMA), path)
    return path


def _write_log_age(tmp_path: Path) -> Path:
    rows = {
        "cell_id": ["P001_1"] * 8,
        "timestamp_s": [10.0, 20.0, 50.0, 100.0, 130.0, 160.0, 190.0, 220.0],
        "v_raw_V": [3.2, 3.4, 3.75, 4.15, 3.25, 3.55, 3.95, 4.2],
        "ocv_est_V": [3.2, 3.4, 3.75, 4.15, 3.25, 3.55, 3.95, 4.2],
        "i_raw_A": [0.0, 3.2, 4.7, 5.2, -3.2, -4.7, 5.2, 0.0],
        "t_cell_degC": [0.0, 10.0, 25.0, 42.0, 2.0, 12.0, 35.0, 45.0],
        "soc_est": [10.0, 35.0, 65.0, 85.0, 15.0, 45.0, 75.0, 90.0],
        "delta_q_Ah": list(range(8)),
        "EFC": [0.1 * idx for idx in range(8)],
        "cap_aged_est_Ah": [None] * 8,
        "R0_mOhm": [None] * 8,
        "R1_mOhm": [None] * 8,
        "source_file": ["log.csv"] * 8,
        "source_archive": ["log.7z"] * 8,
        "quality_flags": [""] * 8,
    }
    path = tmp_path / "modality_table_log_age.parquet"
    pq.write_table(pa.Table.from_pydict(rows, schema=MODALITY_TABLE_LOG_AGE_SCHEMA), path)
    return path


def _write_interval_subsets(tmp_path: Path) -> Path:
    rows = []
    for checkup_k in (0, 1):
        rows.append(
            {
                "cell_id": "P001_1",
                "parameter_set": 1,
                "replicate_id": 1,
                "checkup_k": checkup_k,
                "checkup_k_next": checkup_k + 1,
                "interval_id": f"P001_1:{checkup_k}->{checkup_k + 1}",
                "baseline_clean_strict": True,
                "baseline_clean_tolerant": True,
                "sensitivity_flagged_monotonicity": False,
                "small_efc_jitter": False,
                "excluded_due_to_large_efc_drop": False,
                "excluded_due_to_timestamp_drop": False,
                "excluded_due_to_missing_log_age": False,
                "excluded_due_to_duration_error": False,
                "monotonicity_policy_version": "log_age_monotonicity.v1",
                "schema_version": "gate4.interval_subset.v1",
            }
        )
    path = tmp_path / "interval_subset_registry_v1.parquet"
    pq.write_table(
        pa.Table.from_pylist(rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA),
        path,
    )
    return path


def test_stress_feature_schema_and_dwell_consistency(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    _write_log_age(tmp_path)
    out_path = tmp_path / "interval_stress_features_v1.parquet"

    table = build_interval_stress_features(tmp_path, interval_path, out_path)

    assert validate_table(table, INTERVAL_STRESS_FEATURES_SCHEMA)
    assert table.num_rows == 2
    rows = table.to_pylist()
    for row in rows:
        duration = row["stress_observed_duration_h"]
        voltage_sum = sum(
            row[column]
            for column in (
                "time_voltage_lt_3p3_h",
                "time_voltage_3p3_3p6_h",
                "time_voltage_3p6_3p9_h",
                "time_voltage_3p9_4p1_h",
                "time_voltage_ge_4p1_h",
            )
        )
        temperature_sum = sum(
            row[column]
            for column in (
                "time_temp_lt_5C_h",
                "time_temp_5_15C_h",
                "time_temp_15_30C_h",
                "time_temp_30_40C_h",
                "time_temp_ge_40C_h",
            )
        )
        soc_sum = sum(
            row[column]
            for column in (
                "time_soc_lt_20_h",
                "time_soc_20_50_h",
                "time_soc_50_80_h",
                "time_soc_ge_80_h",
            )
        )
        current_sum = sum(
            row[column] for column in ("charge_time_h", "discharge_time_h", "rest_time_h")
        )
        assert voltage_sum == pytest.approx(duration)
        assert temperature_sum == pytest.approx(duration)
        assert soc_sum == pytest.approx(duration)
        assert current_sum == pytest.approx(duration)
        assert row["cold_high_abs_current_time_h"] >= 0.0
        assert row["cold_high_abs_current_time_h"] <= duration
        assert row["stress_coverage_fraction"] <= 1.0
        assert row["median_log_age_dt_s"] is not None
        assert row["max_log_age_gap_s"] >= row["median_log_age_dt_s"]
        assert row["n_charge_events"] >= 0
        assert row["max_abs_current_ge_1C_event_h"] <= duration
        assert row["sign_dependent_features_provisional"] is True
        assert row["current_sign_convention_confirmed"] is False


def test_stress_feature_qa_passes_synthetic_fixture(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    _write_log_age(tmp_path)
    stress_path = tmp_path / "interval_stress_features_v1.parquet"
    build_interval_stress_features(tmp_path, interval_path, stress_path)

    report = run_stress_feature_qa(
        stress_path,
        tmp_path / "stress_feature_qa_report.json",
        interval_table_path=interval_path,
    )

    assert report["status"] == "passed"
    assert report["row_count"] == 2
    assert report["intervals_missing_stress_features"] == 0
    assert report["sign_dependent_features_provisional_counts"] == {"True": 2}
    assert report["duration_consistency"]["reference"] == "stress_observed_duration_h"


def test_baseline_loader_joins_stress_features_by_interval_key(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    subset_path = _write_interval_subsets(tmp_path)
    _write_log_age(tmp_path)
    stress_path = tmp_path / "interval_stress_features_v1.parquet"
    build_interval_stress_features(tmp_path, interval_path, stress_path)

    _, rows = load_baseline_rows(
        interval_path,
        subset_path,
        "baseline_clean_tolerant",
        stress_features_path=stress_path,
    )
    encoder = FeatureEncoder.fit(rows, "F5_log_age_histograms")

    assert "time_voltage_ge_4p1_h" in encoder.output_columns
    assert rows[0]["stress_log_age_row_count"] > 0


def test_stress_feature_groups_require_stress_sidecar(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    subset_path = _write_interval_subsets(tmp_path)

    with pytest.raises(ValueError, match="require --stress-features"):
        run_capacity_baselines(
            interval_path,
            subset_path,
            tmp_path / "report.json",
            tmp_path / "predictions.parquet",
            model_levels=["L1_ridge"],
            feature_groups=["F5_log_age_histograms"],
        )


def test_stress_feature_groups_exclude_inserted_diagnostics() -> None:
    target_derived_fields = {
        "delta_capacity_per_day",
        "delta_capacity_per_efc",
        "delta_capacity_per_Ah_throughput",
    }
    for feature_group in (
        "F5_log_age_histograms",
        "F6_coupled_stress",
        "F7_c_rate_focused",
        "F8_timestamp_weighted_stress",
        "F9_event_segmented_stress",
        "F10_c_rate_v1_1",
    ):
        assert not (set(NUMERIC_FEATURES[feature_group]) & DIAGNOSTIC_LEAKAGE_FIELDS)
        assert not (set(NUMERIC_FEATURES[feature_group]) & target_derived_fields)


def test_timestamp_weighted_dwell_differs_from_count_weighted_when_gaps_exist(
    tmp_path: Path,
) -> None:
    interval_path = _write_interval_table(tmp_path)
    _write_log_age(tmp_path)
    stress_path = tmp_path / "interval_stress_features_v1_1.parquet"

    table = build_interval_stress_features(tmp_path, interval_path, stress_path)
    first = table.to_pylist()[0]

    assert first["stress_duration_h"] == pytest.approx(100.0 / 3600.0)
    assert first["stress_observed_duration_h"] == pytest.approx(100.0 / 3600.0)
    assert first["stress_coverage_fraction"] == pytest.approx(1.0)
    count_weighted_ge_4p1 = first["stress_duration_h"] * 1 / 4
    assert first["time_voltage_ge_4p1_h"] != pytest.approx(count_weighted_ge_4p1)


def test_event_segmented_features_on_synthetic_trace(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    _write_log_age(tmp_path)
    stress_path = tmp_path / "interval_stress_features_v1_1.parquet"

    table = build_interval_stress_features(tmp_path, interval_path, stress_path)
    first = table.to_pylist()[0]

    assert first["n_charge_events"] == 1
    assert first["max_charge_event_h"] == pytest.approx(90.0 / 3600.0)
    assert first["max_abs_current_ge_1p5C_event_h"] == pytest.approx(80.0 / 3600.0)


def test_current_sign_audit_synthetic_trace(tmp_path: Path) -> None:
    interval_path = _write_interval_table(tmp_path)
    rows = {
        "cell_id": ["P001_1"] * 8,
        "timestamp_s": [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0],
        "v_raw_V": [3.50, 3.55, 3.60, 3.65, 3.60, 3.55, 3.50, 3.45],
        "ocv_est_V": [3.50, 3.55, 3.60, 3.65, 3.60, 3.55, 3.50, 3.45],
        "i_raw_A": [0.0, 3.0, 3.0, 3.0, -3.0, -3.0, -3.0, -3.0],
        "t_cell_degC": [25.0] * 8,
        "soc_est": [50.0, 52.0, 54.0, 56.0, 54.0, 52.0, 50.0, 48.0],
        "delta_q_Ah": list(range(8)),
        "EFC": [0.1 * idx for idx in range(8)],
        "cap_aged_est_Ah": [None] * 8,
        "R0_mOhm": [None] * 8,
        "R1_mOhm": [None] * 8,
        "source_file": ["log.csv"] * 8,
        "source_archive": ["log.7z"] * 8,
        "quality_flags": [""] * 8,
    }
    log_age_path = tmp_path / "modality_table_log_age.parquet"
    pq.write_table(pa.Table.from_pydict(rows, schema=MODALITY_TABLE_LOG_AGE_SCHEMA), log_age_path)

    report = audit_current_sign(
        log_age_path,
        interval_path,
        tmp_path / "current_sign_audit_report.json",
    )

    assert report["current_sign_convention"] == "positive_current_charge"
    assert report["confidence"] == "high"
