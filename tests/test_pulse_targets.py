from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.data.products.pulse_targets import (
    build_pulse_target_table,
    write_pulse_alignment_sensitivity_report,
    write_pulse_missingness_reports,
    write_pulse_qa_report,
)
from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    INTERVAL_TABLE_SCHEMA,
    MODALITY_TABLE_PULSE_SUMMARY_SCHEMA,
    PULSE_TARGET_TABLE_SCHEMA,
)


def _write_pulse_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    pulse_rows = []
    checkup_rows = []
    interval_rows = []
    for parameter_set in (1, 2):
        for replicate_id in (1, 2, 3):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in (0, 1, 2):
                checkup_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "checkup_k": checkup_k,
                        "timestamp": float(checkup_k * 1000),
                        "capacity_Ah": 3.0 - 0.1 * checkup_k,
                        "capacity_soh": 1.0,
                        "charge_energy_Wh": 1.0,
                        "discharge_energy_Wh": 1.0,
                        "temperature_context": "RT",
                        "source_file": "eoc.csv",
                        "source_archive": "eoc.zip",
                        "schema_version": "test",
                        "quality_flags": "OK",
                    }
                )
                for direction in ("charge", "discharge"):
                    pulse_rows.append(
                        {
                            "cell_id": cell_id,
                            "checkup_k": checkup_k,
                            "soc_percent": 50.0,
                            "temperature_context": "RT",
                            "temperature_C": 25.0,
                            "pulse_direction": direction,
                            "pulse_10ms_resistance": 0.010 + 0.001 * checkup_k,
                            "pulse_1s_resistance": 0.020 + 0.002 * checkup_k,
                            "alignment_method": "nearest_eoc_timestamp",
                            "alignment_delta_s": 10.0 + checkup_k,
                            "source_file": "pulse.csv",
                            "quality_flags": "OK",
                        }
                    )
            for checkup_k in (0, 1):
                interval_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0,
                        "voltage_window": "2.50 V - 4.20 V",
                        "voltage_window_family": "approx_0_100",
                        "soc_window_approx": "50%",
                        "nominal_charge_C_rate": 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "CC",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "t_result_k_s": float(checkup_k * 1000),
                        "t_result_k1_s": float((checkup_k + 1) * 1000),
                        "duration_s": 1000.0,
                        "duration_h": 1000.0 / 3600.0,
                        "calendar_days": 1000.0 / 86400.0,
                        "capacity_Ah_k": 3.0,
                        "capacity_Ah_k1": 2.9,
                        "delta_capacity_Ah": -0.1,
                        "delta_capacity_soh": -0.01,
                        "condition_fold": parameter_set - 1,
                        "temperature_holdout_fold": 1 if parameter_set == 2 else 0,
                        "voltage_window_holdout_fold": parameter_set,
                        "soc_window_holdout_fold": parameter_set,
                        "c_rate_holdout_fold": 1 if parameter_set == 2 else 0,
                        "profile_holdout_fold": 0,
                        "replicate_calibration_fold": 0,
                        "time_horizon_fold": 0,
                        "log_age_row_count": 10,
                        "log_age_elapsed_s": 1000.0,
                        "log_age_efc_delta": 1.0,
                        "log_age_delta_q_Ah": 1.0,
                        "log_age_mean_voltage_V": 3.7,
                        "log_age_min_voltage_V": 3.2,
                        "log_age_max_voltage_V": 4.1,
                        "log_age_mean_temperature_C": 25.0,
                        "log_age_min_temperature_C": 24.0,
                        "log_age_max_temperature_C": 26.0,
                        "log_age_mean_current_A": 0.1,
                        "log_age_mean_abs_current_A": 0.2,
                        "log_age_max_abs_current_A": 1.0,
                        "log_age_mean_soc": 50.0,
                        "log_age_min_soc": 40.0,
                        "log_age_max_soc": 60.0,
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
                        "schema_version": "test",
                    }
                )
    pulse_path = tmp_path / "pulse.parquet"
    checkup_path = tmp_path / "checkups.parquet"
    interval_path = tmp_path / "intervals.parquet"
    pq.write_table(pa.Table.from_pylist(pulse_rows, schema=MODALITY_TABLE_PULSE_SUMMARY_SCHEMA), pulse_path)
    pq.write_table(pa.Table.from_pylist(checkup_rows, schema=CHECKUP_EVENT_TABLE_SCHEMA), checkup_path)
    pq.write_table(pa.Table.from_pylist(interval_rows, schema=INTERVAL_TABLE_SCHEMA), interval_path)
    return pulse_path, checkup_path, interval_path


def test_pulse_qa_reports_canonical_coverage_and_duplicates(tmp_path: Path) -> None:
    pulse_path, checkup_path, _ = _write_pulse_fixture(tmp_path)

    report = write_pulse_qa_report(
        pulse_path,
        checkup_path,
        tmp_path / "qa.json",
        tmp_path / "coverage.csv",
        tmp_path / "alignment.json",
    )

    assert report["row_count"] == 36
    assert report["canonical_target"]["duplicate_cell_checkups"] == 18
    assert report["alignment"]["alignment_delta_s"]["median"] == 11.0
    assert "pulse_direction" in (tmp_path / "coverage.csv").read_text()
    assert json.loads((tmp_path / "alignment.json").read_text())["alignment_delta_s"]["max"] == 12.0


def test_pulse_target_table_builds_adjacent_deltas(tmp_path: Path) -> None:
    pulse_path, _, interval_path = _write_pulse_fixture(tmp_path)

    table = build_pulse_target_table(
        pulse_path,
        interval_path,
        tmp_path / "pulse_target_table.parquet",
    )

    assert table.schema == PULSE_TARGET_TABLE_SCHEMA
    rows = table.to_pylist()
    assert len(rows) == 12
    assert rows[0]["pulse_1s_resistance_k"] == 0.020
    assert rows[0]["pulse_1s_resistance_k1"] == 0.022
    assert rows[0]["delta_pulse_1s_resistance"] == pytest.approx(0.002)
    assert rows[0]["quality_flags"] == "OK"


def test_direction_specific_target_extraction(tmp_path: Path) -> None:
    pulse_path, _, interval_path = _write_pulse_fixture(tmp_path)
    charge_table = build_pulse_target_table(
        pulse_path,
        interval_path,
        tmp_path / "pulse_charge.parquet",
        direction="charge",
    )
    mean_table = build_pulse_target_table(
        pulse_path,
        interval_path,
        tmp_path / "pulse_mean.parquet",
        direction="mean",
    )

    assert charge_table.num_rows == mean_table.num_rows
    assert charge_table.to_pylist()[0]["delta_pulse_1s_resistance"] == pytest.approx(0.002)


def test_alignment_sensitivity_and_missingness_reports(tmp_path: Path) -> None:
    pulse_path, _, interval_path = _write_pulse_fixture(tmp_path)
    targets_path = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_path, interval_path, targets_path)

    sensitivity = write_pulse_alignment_sensitivity_report(
        pulse_path,
        targets_path,
        interval_path,
        tmp_path / "alignment_sensitivity.json",
        tmp_path / "alignment_sensitivity.csv",
        thresholds_s=(11.0, 12.0),
    )
    missing = write_pulse_missingness_reports(
        targets_path,
        interval_path,
        tmp_path / "missing.csv",
        tmp_path / "missing_by_condition.csv",
        tmp_path / "missing_by_split.csv",
    )

    assert sensitivity["thresholds"][0]["retained_intervals"] == 6
    assert sensitivity["thresholds"][1]["retained_intervals"] == 12
    assert "threshold_s" in (tmp_path / "alignment_sensitivity.csv").read_text()
    assert missing["missing_rows"] == 0
