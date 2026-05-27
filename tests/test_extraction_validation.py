"""Tests for the Milestone 8.3 extraction reproducibility gate."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import py7zr
from typer.testing import CliRunner

from mbp.audit.extraction_validation import (
    compare_parquet_products,
    parquet_stream_digest,
    parquet_streams_equal,
    sorted_parquet_digest,
    validate_extraction,
)
from mbp.cli import app
from mbp.data.luh_blank.parse_cfg import ingest_cfg
from mbp.data.luh_blank.parse_eis import ingest_eis
from mbp.data.luh_blank.parse_eoc import ingest_eoc
from mbp.data.luh_blank.parse_log import ingest_log_age
from mbp.data.luh_blank.parse_pulse import ingest_pulse
from mbp.data.schema_contracts import CHECKUP_EVENT_TABLE_SCHEMA


def test_validate_extraction_passes_on_rebuilt_synthetic_archives(tmp_path: Path) -> None:
    result_root = _write_result_archives(tmp_path / "raw")
    current_interim = tmp_path / "current"
    _build_current_products(result_root, current_interim)

    report = validate_extraction(
        result_root=result_root,
        current_interim=current_interim,
        rebuild_dir=tmp_path / "rebuild",
        out_dir=tmp_path / "reports",
        sample_cells=["P001_1"],
    )

    assert report["status"] == "passed"
    assert report["golden_check_count"] > 0
    assert (tmp_path / "reports" / "extraction_rebuild_hashes.csv").exists()
    assert (tmp_path / "reports" / "raw_to_parquet_golden_records.csv").exists()


def test_validate_extraction_detects_current_product_mismatch(tmp_path: Path) -> None:
    result_root = _write_result_archives(tmp_path / "raw")
    current_interim = tmp_path / "current"
    _build_current_products(result_root, current_interim)

    table = pq.read_table(current_interim / "checkup_event_table.parquet").to_pydict()
    table["capacity_Ah"][0] = 2.5
    pq.write_table(
        pa.Table.from_pydict(table, schema=CHECKUP_EVENT_TABLE_SCHEMA),
        current_interim / "checkup_event_table.parquet",
    )

    report = validate_extraction(
        result_root=result_root,
        current_interim=current_interim,
        rebuild_dir=tmp_path / "rebuild",
        out_dir=tmp_path / "reports",
        sample_cells=["P001_1"],
    )

    assert report["status"] == "failed"
    assert any("checkup_event_table comparison failed" in failure for failure in report["failures"])


def test_validate_extraction_reports_missing_raw_archive(tmp_path: Path) -> None:
    result_root = _write_result_archives(tmp_path / "raw")
    (result_root / "cell_eisv2.zip").unlink()
    current_interim = tmp_path / "current"
    current_interim.mkdir()

    report = validate_extraction(
        result_root=result_root,
        current_interim=current_interim,
        rebuild_dir=tmp_path / "rebuild",
        out_dir=tmp_path / "reports",
        sample_cells=["P001_1"],
    )

    assert report["status"] == "failed"
    assert "missing required result archive: eis" in report["failures"]


def test_validate_extraction_full_log_age_passes_on_tiny_archive(tmp_path: Path) -> None:
    result_root = _write_result_archives(tmp_path / "raw")
    log_age_archive = _write_log_age_archive(tmp_path / "raw" / "cell_log_age_ultracompr.7z")
    current_interim = tmp_path / "current"
    _build_current_products(result_root, current_interim)
    ingest_log_age(log_age_archive, current_interim, csv_block_size_bytes=128)

    report = validate_extraction(
        result_root=result_root,
        log_age_archive=log_age_archive,
        current_interim=current_interim,
        rebuild_dir=tmp_path / "rebuild",
        out_dir=tmp_path / "reports",
        full_log_age=True,
        sample_cells=["P001_1"],
        csv_block_size_bytes=128,
        prefer_external_7z=False,
        csv_use_threads=False,
        log_age_digest_batch_rows=2,
        expected_log_age_csv_count=1,
    )

    assert report["status"] == "passed"
    log_row = next(row for row in report["comparison_rows"] if row["table_name"] == "modality_table_log_age")
    assert log_row["digest_equal"] is True


def test_log_age_skip_extract_rebuilds_incomplete_csv_cache(tmp_path: Path) -> None:
    log_age_archive = _write_log_age_archive(
        tmp_path / "cell_log_age_ultracompr.7z",
        extra_cell="P001_2",
    )
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    partial_csv = cache_dir / "cell_log_age_2s_P001_1_S01_C01.csv"
    partial_csv.write_text(
        "timestamp_s;v_raw_V;ocv_est_V;i_raw_A;t_cell_degC;soc_est;delta_q_Ah;EFC;cap_aged_est_Ah;R0_mOhm;R1_mOhm\n"
        "999.0;3.4;3.5;-1.0;25.0;50.0;1.2;10.0;2.9;20.0;25.0\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "interim"
    ingest_log_age(
        log_age_archive,
        out_dir,
        skip_extract=True,
        extract_dir=cache_dir,
        keep_extracted=True,
        expected_csv_count=2,
        csv_block_size_bytes=128,
    )

    table = pq.read_table(out_dir / "modality_table_log_age.parquet")
    assert table.column("timestamp_s").to_pylist()[0] == 100.0


def test_sorted_parquet_digest_is_order_insensitive(tmp_path: Path) -> None:
    schema = pa.schema([("cell_id", pa.string()), ("value", pa.int32())])
    path_a = tmp_path / "a.parquet"
    path_b = tmp_path / "b.parquet"
    pq.write_table(pa.Table.from_pydict({"cell_id": ["P002_1", "P001_1"], "value": [2, 1]}, schema=schema), path_a)
    pq.write_table(pa.Table.from_pydict({"cell_id": ["P001_1", "P002_1"], "value": [1, 2]}, schema=schema), path_b)

    assert sorted_parquet_digest(path_a, ("cell_id",)) == sorted_parquet_digest(path_b, ("cell_id",))


def test_parquet_stream_digest_ignores_row_group_layout(tmp_path: Path) -> None:
    schema = pa.schema([("cell_id", pa.string()), ("value", pa.float64())])
    path_a = tmp_path / "a.parquet"
    path_b = tmp_path / "b.parquet"
    table = pa.Table.from_pydict(
        {
            "cell_id": ["P001_1", "P001_1", "P001_1", "P001_1", "P001_1"],
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        },
        schema=schema,
    )
    pq.write_table(table, path_a, row_group_size=1)
    pq.write_table(table, path_b, row_group_size=5)

    assert parquet_stream_digest(path_a, batch_size=2) == parquet_stream_digest(path_b, batch_size=2)


def test_parquet_streams_equal_detects_values_independent_of_row_groups(tmp_path: Path) -> None:
    schema = pa.schema([("cell_id", pa.string()), ("value", pa.float64())])
    path_a = tmp_path / "a.parquet"
    path_b = tmp_path / "b.parquet"
    path_c = tmp_path / "c.parquet"
    table = pa.Table.from_pydict(
        {
            "cell_id": ["P001_1", "P001_1", "P001_1", "P001_1", "P001_1"],
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        },
        schema=schema,
    )
    changed = pa.Table.from_pydict(
        {
            "cell_id": ["P001_1", "P001_1", "P001_1", "P001_1", "P001_1"],
            "value": [1.0, 2.0, 9.0, 4.0, 5.0],
        },
        schema=schema,
    )
    pq.write_table(table, path_a, row_group_size=1)
    pq.write_table(table, path_b, row_group_size=5)
    pq.write_table(changed, path_c, row_group_size=5)

    equal, rows, mismatch = parquet_streams_equal(path_a, path_b, batch_size=2)
    assert equal is True
    assert rows == 5
    assert mismatch is None

    equal, rows, mismatch = parquet_streams_equal(path_a, path_c, batch_size=2)
    assert equal is False
    assert rows == 2
    assert mismatch == "value mismatch in normalized batch 1"


def test_compare_parquet_products_skips_optional_missing_alias(tmp_path: Path) -> None:
    from mbp.audit.extraction_validation import TableSpec

    current = tmp_path / "current"
    rebuild = tmp_path / "rebuild"
    current.mkdir()
    rebuild.mkdir()
    spec = TableSpec("optional", "missing.parquet", "missing.parquet", (), required=False)

    row = compare_parquet_products(spec, current_interim=current, rebuild_dir=rebuild, digest_batch_rows=10)

    assert row["status"] == "skipped"


def test_validate_extraction_cli_smoke(tmp_path: Path) -> None:
    result_root = _write_result_archives(tmp_path / "raw")
    current_interim = tmp_path / "current"
    _build_current_products(result_root, current_interim)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "audit",
            "validate-extraction",
            "--result-root",
            str(result_root),
            "--current-interim",
            str(current_interim),
            "--rebuild-dir",
            str(tmp_path / "rebuild"),
            "--out-dir",
            str(tmp_path / "reports"),
            "--sample-cells",
            "P001_1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Extraction validation passed" in result.output


def _write_result_archives(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _write_cfg_zip(root / "cfg.zip")
    _write_eoc_zip(root / "cell_eocv2.zip")
    _write_pulse_zip(root / "cell_plsv2.zip")
    _write_eis_zip(root / "cell_eisv2.zip")
    return root


def _build_current_products(result_root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = out_dir / "cell_condition_table.parquet"
    eoc = out_dir / "checkup_event_table.parquet"
    pulse_raw = out_dir / "modality_table_pulse_raw.parquet"
    pulse_alias = out_dir / "modality_table_pulse.parquet"
    pulse_summary = out_dir / "modality_table_pulse_summary.parquet"
    eis = out_dir / "modality_table_eis.parquet"
    eis_quality = out_dir / "eis_spectrum_quality.parquet"
    ingest_cfg(result_root / "cfg.zip", cfg)
    ingest_eoc(result_root / "cell_eocv2.zip", eoc)
    ingest_pulse(result_root / "cell_plsv2.zip", eoc, pulse_raw, pulse_summary)
    pq.write_table(pq.read_table(pulse_raw), pulse_alias)
    ingest_eis(result_root / "cell_eisv2.zip", eoc, eis, eis_quality)


def _write_cfg_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "cell_cfg_P001_1_S01_C10.csv",
            _csv_text(
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
                ],
                [["1", "1", "2", "25.0", "2.5", "4.2", "80", "1.0", "1.5", "5"]],
            ),
        )


def _write_eoc_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "cell_eocv2_P001_1_S01_C10.csv",
            _csv_text(
                [
                    "timestamp_s",
                    "num_cycles_checkup",
                    "cyc_charged",
                    "cap_aged_est_Ah",
                    "soh_cap",
                    "delta_e_chg_Wh",
                    "delta_e_dischg_Wh",
                ],
                [
                    ["1000.0", "0", "1", "2.95", "98.0", "11.2", "0.0"],
                    ["1500.0", "0", "0", "2.94", "97.8", "0.0", "-10.7"],
                    ["2000.0", "1", "0", "2.90", "96.5", "0.0", "-10.5"],
                ],
            ),
        )


def _write_pulse_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "cell_plsv2_P001_1_S01_C10.csv",
            _csv_text(
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
                ],
                [["1550.0", "50", "1", "25.0", "0", "20.5", "25.2", "3.35", "-1.0"]],
            ),
        )


def _write_eis_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "cell_eisv2_P001_1_S01_C10.csv",
            _csv_text(
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
                ],
                [["1550.0", "50", "1", "25.0", "1000.0", "1", "20.0", "-15.0", "19.3", "-5.2"]],
            ),
        )


def _write_log_age_archive(path: Path, extra_cell: str | None = None) -> Path:
    header = "timestamp_s;v_raw_V;ocv_est_V;i_raw_A;t_cell_degC;soc_est;delta_q_Ah;EFC;cap_aged_est_Ah;R0_mOhm;R1_mOhm\n"
    body = "100.0;3.4;3.5;-1.0;25.0;50.0;1.2;10.0;2.9;20.0;25.0\n"
    body += "200.0;3.3;3.4;-1.0;25.0;48.0;1.4;10.5;nan;nan;nan\n"
    with py7zr.SevenZipFile(path, "w") as z:
        z.writestr(header + body, "cell_log_age_2s_P001_1_S01_C01.csv")
        if extra_cell:
            z.writestr(header + body, f"cell_log_age_2s_{extra_cell}_S01_C01.csv")
    return path


def _csv_text(header: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()
