"""Unit tests verifying Gate 2 Ingestion result-data parsers and QA checks."""

import csv
import io
import json
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.data.luh_blank import ingest_cfg, ingest_eis, ingest_eoc, ingest_pulse, run_qa_checks
from mbp.data.luh_blank.parse_eis import compute_modeling_mask
from mbp.data.luh_blank.parse_pulse import find_closest_checkup_k
from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    CONDITION_TABLE_SCHEMA,
    MODALITY_TABLE_EIS_SCHEMA,
    MODALITY_TABLE_PULSE_SCHEMA,
    validate_table,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Fixture returning a temporary directory path."""
    return tmp_path


def test_find_closest_checkup_k() -> None:
    """Test the closest-timestamp EOC checkup mapping logic."""
    eoc_lookup = {
        "P001_1": [
            (0, 1000.0),
            (1, 2000.0),
            (2, 3000.0),
        ]
    }
    # Exactly on checkup 0
    assert find_closest_checkup_k("P001_1", 1000.0, eoc_lookup) == 0
    # Closer to checkup 0
    assert find_closest_checkup_k("P001_1", 1200.0, eoc_lookup) == 0
    # Closer to checkup 1
    assert find_closest_checkup_k("P001_1", 1800.0, eoc_lookup) == 1
    # Closer to checkup 2
    assert find_closest_checkup_k("P001_1", 2900.0, eoc_lookup) == 2
    # Missing cell defaults to 0
    assert find_closest_checkup_k("P002_1", 1000.0, eoc_lookup) == 0


def test_eis_modeling_mask() -> None:
    """Test standard EIS modeling frequency validation mask rules."""
    # Valid parameters: 1000 Hz, not NaN, valid raw
    assert compute_modeling_mask(1000.0, 0.02, -0.01, 1) is True

    # Invalid raw valid flag
    assert compute_modeling_mask(1000.0, 0.02, -0.01, 0) is False

    # NaNs in impedance
    assert compute_modeling_mask(1000.0, float("nan"), -0.01, 1) is False
    assert compute_modeling_mask(1000.0, 0.02, float("nan"), 1) is False

    # Out of range frequencies
    assert compute_modeling_mask(0.1, 0.02, -0.01, 1) is False  # Too low
    assert compute_modeling_mask(10000.0, 0.02, -0.01, 1) is False  # Too high

    # Excluded specific frequencies
    assert compute_modeling_mask(100.0, 0.02, -0.01, 1) is False
    assert compute_modeling_mask(208.3, 0.02, -0.01, 1) is False
    assert compute_modeling_mask(14700.0, 0.02, -0.01, 1) is False


def test_ingest_cfg_parser(temp_workspace: Path) -> None:
    """Test CFG parser on a synthetic cfg.zip file."""
    zip_path = temp_workspace / "cfg.zip"
    out_path = temp_workspace / "cell_condition_table.parquet"

    # Write synthetic zip
    with zipfile.ZipFile(zip_path, "w") as z:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer, delimiter=";")
        writer.writerow(
            [
                "parameter_id",
                "parameter_nr",
                "age_type",
                "age_temp",
                "V_min_cyc_V",
                "V_max_cyc_V",
                "age_soc",
                "age_chg_rate",
                "age_dischg_rate",
                "age_profile",
            ]
        )
        writer.writerow(["1", "2", "3", "25.0", "2.5", "4.2", "80", "1.0", "1.5", "5"])
        z.writestr("cell_cfg_P001_2_S01_C10.csv", csv_buffer.getvalue())

    # Ingest
    ingest_cfg(zip_path, out_path)
    assert out_path.exists()

    # Read back and validate schema
    table = pq.read_table(out_path)
    assert validate_table(table, CONDITION_TABLE_SCHEMA)
    pydict = table.to_pydict()
    assert pydict["cell_id"] == ["P001_2"]
    assert pydict["parameter_set"] == [1]
    assert pydict["replicate_id"] == [2]
    assert pydict["aging_mode"] == ["cyclic"]
    assert pydict["nominal_temperature_C"] == [25.0]
    assert pydict["voltage_window"] == ["2.50 V - 4.20 V"]
    assert pydict["soc_window_approx"] == ["80%"]
    assert pydict["nominal_charge_C_rate"] == [1.0]
    assert pydict["nominal_discharge_C_rate"] == [1.5]
    assert pydict["profile_label"] == ["5"]


def test_ingest_eoc_parser(temp_workspace: Path) -> None:
    """Test EOC parser on a synthetic cell_eocv2.zip file."""
    zip_path = temp_workspace / "cell_eocv2.zip"
    out_path = temp_workspace / "checkup_event_table.parquet"

    # Write synthetic zip with one charge and one discharge row for checkup_k = 0
    with zipfile.ZipFile(zip_path, "w") as z:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer, delimiter=";")
        writer.writerow(
            [
                "timestamp_s",
                "num_cycles_checkup",
                "cyc_charged",
                "cap_aged_est_Ah",
                "soh_cap",
                "delta_e_chg_Wh",
                "delta_e_dischg_Wh",
            ]
        )
        # Charge row
        writer.writerow(["1000.0", "0", "1", "2.95", "98.0", "11.2", "0.0"])
        # Discharge row
        writer.writerow(["1500.0", "0", "0", "2.94", "97.8", "0.0", "-10.7"])
        z.writestr("cell_eocv2_P001_1_S01_C10.csv", csv_buffer.getvalue())

    # Ingest
    ingest_eoc(zip_path, out_path)
    assert out_path.exists()

    # Read back and validate schema
    table = pq.read_table(out_path)
    assert validate_table(table, CHECKUP_EVENT_TABLE_SCHEMA)
    pydict = table.to_pydict()
    assert pydict["cell_id"] == ["P001_1"]
    assert pydict["parameter_set"] == [1]
    assert pydict["replicate_id"] == [1]
    assert pydict["checkup_k"] == [0]
    assert pydict["timestamp"] == [1500.0]  # Prefers discharge row
    assert pydict["capacity_Ah"] == [2.94]
    assert pydict["capacity_soh"] == [97.8]
    assert pydict["charge_energy_Wh"] == [11.2]
    assert pydict["discharge_energy_Wh"] == [10.7]  # Absolute value
    assert pydict["temperature_context"] == ["RT"]


def test_ingest_pulse_parser(temp_workspace: Path) -> None:
    """Test PULSE parser on a synthetic cell_plsv2.zip file."""
    zip_path = temp_workspace / "cell_plsv2.zip"
    eoc_path = temp_workspace / "checkup_event_table.parquet"
    out_path = temp_workspace / "modality_table_pulse.parquet"

    # Create dummy EOC parquet
    eoc_data = {
        "cell_id": ["P001_1"],
        "parameter_set": [1],
        "replicate_id": [1],
        "checkup_k": [0],
        "timestamp": [1500.0],
        "capacity_Ah": [2.94],
        "capacity_soh": [97.8],
        "charge_energy_Wh": [11.2],
        "discharge_energy_Wh": [10.7],
        "temperature_context": ["RT"],
        "source_file": ["file.csv"],
        "source_archive": ["eoc.zip"],
        "schema_version": ["1.0"],
        "quality_flags": ["OK"],
    }
    pq.write_table(pa.Table.from_pydict(eoc_data, schema=CHECKUP_EVENT_TABLE_SCHEMA), eoc_path)

    # Create synthetic zip
    with zipfile.ZipFile(zip_path, "w") as z:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer, delimiter=";")
        writer.writerow(
            [
                "timestamp_s",
                "soc_nom",
                "is_rt",
                "t_avg_degC",
                "cyc_charged",
                "r_ref_10ms_mOhm",
                "r_ref_1s_mOhm",
                "v_raw_V",
                "i_raw_A",
            ]
        )
        writer.writerow(["1550.0", "50", "1", "25.0", "0", "20.5", "25.2", "3.35", "-1.0"])
        z.writestr("cell_plsv2_P001_1_S01_C10.csv", csv_buffer.getvalue())

    # Ingest
    ingest_pulse(zip_path, eoc_path, out_path)
    assert out_path.exists()

    # Read back and validate schema
    table = pq.read_table(out_path)
    assert validate_table(table, MODALITY_TABLE_PULSE_SCHEMA)
    pydict = table.to_pydict()
    assert pydict["cell_id"] == ["P001_1"]
    assert pydict["checkup_k"] == [0]  # Aligned to checkup 0!
    assert pydict["soc_percent"] == [50.0]
    assert pydict["temperature_context"] == ["RT"]
    assert pydict["temperature_C"] == [25.0]
    assert pydict["pulse_direction"] == ["discharge"]
    assert pydict["pulse_10ms_resistance"] == [0.0205]  # Converted to Ohm
    assert pydict["pulse_1s_resistance"] == [0.0252]  # Converted to Ohm
    assert pydict["voltage"] == [3.35]
    assert pydict["current"] == [-1.0]


def test_ingest_eis_parser(temp_workspace: Path) -> None:
    """Test EIS parser on a synthetic cell_eisv2.zip file."""
    zip_path = temp_workspace / "cell_eisv2.zip"
    eoc_path = temp_workspace / "checkup_event_table.parquet"
    out_path = temp_workspace / "modality_table_eis.parquet"

    # Create dummy EOC parquet
    eoc_data = {
        "cell_id": ["P001_1"],
        "parameter_set": [1],
        "replicate_id": [1],
        "checkup_k": [0],
        "timestamp": [1500.0],
        "capacity_Ah": [2.94],
        "capacity_soh": [97.8],
        "charge_energy_Wh": [11.2],
        "discharge_energy_Wh": [10.7],
        "temperature_context": ["RT"],
        "source_file": ["file.csv"],
        "source_archive": ["eoc.zip"],
        "schema_version": ["1.0"],
        "quality_flags": ["OK"],
    }
    pq.write_table(pa.Table.from_pydict(eoc_data, schema=CHECKUP_EVENT_TABLE_SCHEMA), eoc_path)

    # Create synthetic zip
    with zipfile.ZipFile(zip_path, "w") as z:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer, delimiter=";")
        writer.writerow(
            [
                "timestamp_s",
                "soc_nom",
                "is_rt",
                "t_avg_degC",
                "freq_Hz",
                "valid",
                "z_amp_comp_mOhm",
                "z_ph_comp_deg",
                "z_re_comp_mOhm",
                "z_im_comp_mOhm",
            ]
        )
        writer.writerow(
            ["1550.0", "50", "1", "25.0", "1000.0", "1", "20.0", "-15.0", "19.3", "-5.2"]
        )
        z.writestr("cell_eisv2_P001_1_S01_C10.csv", csv_buffer.getvalue())

    # Ingest
    ingest_eis(zip_path, eoc_path, out_path)
    assert out_path.exists()

    # Read back and validate schema
    table = pq.read_table(out_path)
    assert validate_table(table, MODALITY_TABLE_EIS_SCHEMA)
    pydict = table.to_pydict()
    assert pydict["cell_id"] == ["P001_1"]
    assert pydict["checkup_k"] == [0]  # Aligned to checkup 0!
    assert pydict["soc_percent"] == [50.0]
    assert pydict["temperature_context"] == ["RT"]
    assert pydict["temperature_C"] == [25.0]
    assert pydict["frequency_Hz"] == [1000.0]
    assert pydict["z_real"] == [0.0193]  # Converted to Ohm
    assert pydict["z_imag"] == [-0.0052]  # Converted to Ohm
    assert pydict["z_abs"] == [0.0200]  # Converted to Ohm
    assert pydict["phase"] == [-15.0]
    assert pydict["is_valid_raw"] == [True]
    assert pydict["is_valid_modeling_frequency"] == [True]  # Passes modeling mask criteria


def test_qa_checks_runner(temp_workspace: Path) -> None:
    """Test running the QA checks module on synthetic parquet tables."""
    interim_dir = temp_workspace / "interim"
    interim_dir.mkdir()
    report_json = temp_workspace / "qa_report.json"

    # Save dummy Parquet tables to interim
    cfg_data = {
        "cell_id": ["P001_1"],
        "parameter_set": [1],
        "replicate_id": [1],
        "aging_mode": ["cyclic"],
        "nominal_temperature_C": [25.0],
        "voltage_window": ["2.5 V - 4.2 V"],
        "soc_window_approx": ["80%"],
        "nominal_charge_C_rate": [1.0],
        "nominal_discharge_C_rate": [1.5],
        "profile_label": ["5"],
        "source_file": ["file.csv"],
        "source_archive": ["cfg.zip"],
        "schema_version": ["1.0"],
    }
    pq.write_table(
        pa.Table.from_pydict(cfg_data, schema=CONDITION_TABLE_SCHEMA),
        interim_dir / "cell_condition_table.parquet",
    )

    eoc_data = {
        "cell_id": ["P001_1"],
        "parameter_set": [1],
        "replicate_id": [1],
        "checkup_k": [0],
        "timestamp": [1500.0],
        "capacity_Ah": [2.94],  # Normal range
        "capacity_soh": [97.8],
        "charge_energy_Wh": [11.2],
        "discharge_energy_Wh": [10.7],
        "temperature_context": ["RT"],
        "source_file": ["file.csv"],
        "source_archive": ["eoc.zip"],
        "schema_version": ["1.0"],
        "quality_flags": ["OK"],
    }
    pq.write_table(
        pa.Table.from_pydict(eoc_data, schema=CHECKUP_EVENT_TABLE_SCHEMA),
        interim_dir / "checkup_event_table.parquet",
    )

    pulse_data = {
        "cell_id": ["P001_1"],
        "checkup_k": [0],
        "soc_percent": [50.0],
        "temperature_context": ["RT"],
        "temperature_C": [25.0],
        "pulse_direction": ["discharge"],
        "pulse_10ms_resistance": [0.02],  # Normal range
        "pulse_1s_resistance": [0.025],  # Normal range
        "voltage": [3.35],
        "current": [-1.0],
        "source_file": ["file.csv"],
        "quality_flags": ["OK"],
    }
    pq.write_table(
        pa.Table.from_pydict(pulse_data, schema=MODALITY_TABLE_PULSE_SCHEMA),
        interim_dir / "modality_table_pulse.parquet",
    )

    eis_data = {
        "cell_id": ["P001_1"],
        "checkup_k": [0],
        "soc_percent": [50.0],
        "temperature_context": ["RT"],
        "temperature_C": [25.0],
        "frequency_Hz": [1000.0],
        "z_real": [0.02],
        "z_imag": [-0.005],
        "z_abs": [0.021],
        "phase": [-15.0],
        "is_valid_raw": [True],
        "is_valid_modeling_frequency": [True],
        "source_file": ["file.csv"],
        "source_archive": ["eis.zip"],
        "quality_flags": ["OK"],
    }
    pq.write_table(
        pa.Table.from_pydict(eis_data, schema=MODALITY_TABLE_EIS_SCHEMA),
        interim_dir / "modality_table_eis.parquet",
    )

    # Run QA
    report = run_qa_checks(interim_dir, report_json)
    assert report["status"] == "passed"
    assert report_json.exists()

    with report_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "passed"
    assert data["tables"]["cell_condition_table"]["row_count"] == 1
    assert data["tables"]["checkup_event_table"]["range_violations"] == 0
