from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.data.products.eis_features import (
    build_eis_target_table,
    build_eis_feature_table,
    write_eis_alignment_sensitivity_report,
    write_eis_claim_readiness_report,
    write_eis_feature_qa_report,
    write_eis_qa_report,
    write_eis_target_qa_report,
)
from mbp.baselines import capacity as capacity_baselines
from mbp.baselines import pulse as pulse_baselines
from mbp.baselines.eis import (
    EIS_FORBIDDEN_FEATURES,
    EIS_PREDICTION_SCHEMA,
    load_eis_rows,
    run_eis_baselines,
)
from mbp.data.schema_contracts import (
    EIS_FEATURE_TABLE_V1_SCHEMA,
    EIS_TARGET_TABLE_V1_SCHEMA,
    EIS_SPECTRUM_QUALITY_SCHEMA,
    INTERVAL_SUBSET_REGISTRY_SCHEMA,
    INTERVAL_TABLE_SCHEMA,
    MODALITY_TABLE_EIS_SCHEMA,
)


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    eis_rows = []
    quality_rows = []
    interval_rows = []
    frequencies = [0.5, 1.0, 10.0, 100.0, 208.3, 1000.0, 5000.0, 14700.0]
    for parameter_set in (1, 2):
        for replicate_id in (1, 2, 3):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in (0, 1, 2):
                for soc in (50.0, 70.0):
                    alignment_delta_s = 1000.0 + checkup_k * 100.0 + parameter_set
                    valid_modeling = 0
                    for freq in frequencies:
                        z_real = 0.01 + 0.001 * checkup_k + freq * 1e-7
                        z_imag = -0.005 - freq * 1e-8
                        is_valid = freq != 14700.0
                        is_modeling = is_valid and freq not in {100.0, 208.3, 14700.0}
                        valid_modeling += int(is_modeling)
                        eis_rows.append(
                            {
                                "cell_id": cell_id,
                                "checkup_k": checkup_k,
                                "soc_percent": soc,
                                "temperature_context": "RT",
                                "temperature_C": 25.0,
                                "frequency_Hz": freq,
                                "z_real": z_real,
                                "z_imag": z_imag,
                                "z_abs": (z_real**2 + z_imag**2) ** 0.5,
                                "phase": -10.0,
                                "is_valid_raw": is_valid,
                                "is_valid_modeling_frequency": is_modeling,
                                "alignment_method": "nearest_eoc_timestamp",
                                "alignment_delta_s": alignment_delta_s,
                                "source_file": "eis.csv",
                                "source_archive": "eis.zip",
                                "quality_flags": "OK",
                            }
                        )
                    quality_rows.append(
                        {
                            "cell_id": cell_id,
                            "checkup_k": checkup_k,
                            "soc_percent": soc,
                            "temperature_context": "RT",
                            "temperature_C_mean": 25.0,
                            "total_frequencies": len(frequencies),
                            "valid_raw_frequencies": len(frequencies) - 1,
                            "valid_modeling_frequencies": valid_modeling,
                            "valid_modeling_fraction": valid_modeling / len(frequencies),
                            "alignment_method": "nearest_eoc_timestamp",
                            "alignment_delta_s": alignment_delta_s,
                            "quality_flags": "OK",
                            "source_file": "eis.csv",
                            "source_archive": "eis.zip",
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
                        "profile_holdout_fold": 1 if parameter_set == 1 else 0,
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
    eis_path = tmp_path / "eis.parquet"
    quality_path = tmp_path / "quality.parquet"
    interval_path = tmp_path / "interval.parquet"
    pq.write_table(pa.Table.from_pylist(eis_rows, schema=MODALITY_TABLE_EIS_SCHEMA), eis_path)
    pq.write_table(pa.Table.from_pylist(quality_rows, schema=EIS_SPECTRUM_QUALITY_SCHEMA), quality_path)
    pq.write_table(pa.Table.from_pylist(interval_rows, schema=INTERVAL_TABLE_SCHEMA), interval_path)
    return eis_path, quality_path, interval_path


def _write_subset_from_interval(interval_path: Path, subset_path: Path) -> Path:
    interval_rows = pq.read_table(interval_path).to_pylist()
    subset_rows = [
        {
            "cell_id": row["cell_id"],
            "parameter_set": row["parameter_set"],
            "replicate_id": row["replicate_id"],
            "checkup_k": row["checkup_k"],
            "checkup_k_next": row["checkup_k_next"],
            "interval_id": f"{row['cell_id']}:{row['checkup_k']}:{row['checkup_k_next']}",
            "baseline_clean_strict": True,
            "baseline_clean_tolerant": True,
            "sensitivity_flagged_monotonicity": False,
            "small_efc_jitter": False,
            "excluded_due_to_large_efc_drop": False,
            "excluded_due_to_timestamp_drop": False,
            "excluded_due_to_missing_log_age": False,
            "excluded_due_to_duration_error": False,
            "monotonicity_policy_version": "test",
            "schema_version": "test",
        }
        for row in interval_rows
    ]
    pq.write_table(pa.Table.from_pylist(subset_rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA), subset_path)
    return subset_path


def test_eis_qa_and_valid_frequency_audit(tmp_path: Path) -> None:
    eis_path, quality_path, interval_path = _write_fixture(tmp_path)

    report = write_eis_qa_report(
        eis_path,
        quality_path,
        interval_path,
        tmp_path / "qa.json",
        tmp_path / "coverage.csv",
        tmp_path / "alignment.json",
        tmp_path / "frequency.csv",
    )

    assert report["row_count"] == 288
    assert report["unique_parameter_sets"] == 2
    frequency_text = (tmp_path / "frequency.csv").read_text()
    assert "excluded_100Hz" in frequency_text
    assert "excluded_208p3Hz" in frequency_text
    assert "excluded_14p7kHz" in frequency_text
    assert "modeling_band_other" in frequency_text
    assert json.loads((tmp_path / "alignment.json").read_text())["alignment_delta_s"]["max"] > 0


def test_eis_alignment_sensitivity(tmp_path: Path) -> None:
    _, quality_path, interval_path = _write_fixture(tmp_path)

    report = write_eis_alignment_sensitivity_report(
        quality_path,
        interval_path,
        tmp_path / "alignment_sensitivity.json",
        tmp_path / "alignment_sensitivity.csv",
        thresholds_s=(1050.0, 1300.0),
    )

    assert report["thresholds"][0]["retained_spectra"] == 12
    assert report["thresholds"][1]["retained_spectra"] == 36
    assert "c_rate_holdout_rows" in (tmp_path / "alignment_sensitivity.csv").read_text()


def test_eis_feature_table_selected_frequency_and_nyquist_features(tmp_path: Path) -> None:
    eis_path, quality_path, interval_path = _write_fixture(tmp_path)

    table = build_eis_feature_table(
        eis_path,
        quality_path,
        interval_path,
        tmp_path / "eis_features.parquet",
    )

    assert table.schema == EIS_FEATURE_TABLE_V1_SCHEMA
    rows = table.to_pylist()
    assert len(rows) == 18
    assert rows[0]["freq_selected_1Hz"] == pytest.approx(1.0)
    assert rows[0]["freq_selected_10Hz"] == pytest.approx(10.0)
    assert rows[0]["freq_selected_1kHz"] == pytest.approx(1000.0)
    assert rows[0]["nyquist_semicircle_width_proxy"] is not None
    assert rows[0]["r0_r1_source"] == "unavailable"


def test_eis_target_table_and_qa_build_adjacent_deltas(tmp_path: Path) -> None:
    eis_path, quality_path, interval_path = _write_fixture(tmp_path)
    feature_path = tmp_path / "eis_features.parquet"
    target_path = tmp_path / "eis_targets.parquet"
    build_eis_feature_table(eis_path, quality_path, interval_path, feature_path)

    table = build_eis_target_table(feature_path, interval_path, target_path)
    report = write_eis_target_qa_report(
        target_path,
        interval_path,
        tmp_path / "target_qa.json",
        tmp_path / "target_coverage.csv",
    )

    assert table.schema == EIS_TARGET_TABLE_V1_SCHEMA
    rows = table.to_pylist()
    assert len(rows) == 12
    assert rows[0]["eis_z_abs_1kHz_k1"] is not None
    assert rows[0]["delta_eis_z_abs_1kHz"] == pytest.approx(
        rows[0]["eis_z_abs_1kHz_k1"] - rows[0]["eis_z_abs_1kHz_k"]
    )
    assert report["finite_delta_target_counts"]["delta_eis_z_abs_1kHz"] == 12
    assert "c_rate_holdout_fold" in (tmp_path / "target_coverage.csv").read_text()


def test_eis_feature_qa_and_claim_readiness(tmp_path: Path) -> None:
    eis_path, quality_path, interval_path = _write_fixture(tmp_path)
    feature_path = tmp_path / "eis_features.parquet"
    build_eis_feature_table(eis_path, quality_path, interval_path, feature_path)
    qa_path = tmp_path / "qa.json"
    feature_qa_path = tmp_path / "feature_qa.json"
    write_eis_qa_report(
        eis_path,
        quality_path,
        interval_path,
        qa_path,
        tmp_path / "coverage.csv",
        tmp_path / "alignment.json",
        tmp_path / "frequency.csv",
    )
    feature_qa = write_eis_feature_qa_report(
        feature_path,
        interval_path,
        feature_qa_path,
        minimum_canonical_rows=1,
    )
    text = write_eis_claim_readiness_report(
        qa_path,
        feature_qa_path,
        tmp_path / "claim_readiness.md",
    )

    assert feature_qa["row_count"] == 18
    assert "DRT remains blocked" in text
    assert "No EIS predictive claim is authorized" in text


def test_eis_baseline_loader_persistence_and_leakage_guard(tmp_path: Path) -> None:
    eis_path, quality_path, interval_path = _write_fixture(tmp_path)
    feature_path = tmp_path / "eis_features.parquet"
    target_path = tmp_path / "eis_targets.parquet"
    subset_path = _write_subset_from_interval(interval_path, tmp_path / "subsets.parquet")
    build_eis_feature_table(eis_path, quality_path, interval_path, feature_path)
    build_eis_target_table(feature_path, interval_path, target_path)

    _, selected = load_eis_rows(interval_path, subset_path, target_path, "baseline_clean_tolerant")
    report = run_eis_baselines(
        interval_path,
        subset_path,
        target_path,
        tmp_path / "eis_report.json",
        tmp_path / "eis_predictions.parquet",
        model_levels=["L0_persistence"],
        feature_groups=["E0_persistence"],
        targets=["delta_eis_z_abs_1kHz"],
        split_views=["condition_fold"],
    )

    assert len(selected) == 12
    assert report["metrics"]
    assert pq.read_table(tmp_path / "eis_predictions.parquet").schema == EIS_PREDICTION_SCHEMA
    assert "delta_eis_z_abs_1kHz" in EIS_FORBIDDEN_FEATURES


def test_prior_eis_feature_groups_use_only_k_features() -> None:
    forbidden = set(EIS_FORBIDDEN_FEATURES)
    for group in capacity_baselines.EIS_FEATURE_GROUPS:
        fields = set(capacity_baselines.NUMERIC_FEATURES[group]) | set(capacity_baselines.CATEGORICAL_FEATURES[group])
        assert not fields & forbidden
        assert "eis_z_abs_1kHz_k" in fields
    for group in pulse_baselines.EIS_FEATURE_GROUPS:
        fields = set(pulse_baselines.NUMERIC_FEATURES[group]) | set(pulse_baselines.CATEGORICAL_FEATURES[group])
        assert not fields & forbidden
        assert "eis_z_abs_1kHz_k" in fields
