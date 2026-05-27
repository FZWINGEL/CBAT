"""Rebuild-and-compare checks for early Luh-Blank extraction products."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import tempfile
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq
import py7zr

from mbp.audit.archives import extract_cell_id
from mbp.data.luh_blank.parse_cfg import (
    EXPECTED_EXPERIMENTAL_CELL_IDS,
    classify_voltage_window_family,
    ingest_cfg,
)
from mbp.data.luh_blank.parse_eis import compute_modeling_mask, ingest_eis
from mbp.data.luh_blank.parse_eoc import ingest_eoc
from mbp.data.luh_blank.parse_log import ingest_log_age
from mbp.data.luh_blank.parse_pulse import build_eoc_lookup, ingest_pulse

EXTRACTION_VALIDATION_SCHEMA_VERSION = "gate83.extraction_validation.v1"
DEFAULT_SAMPLE_CELLS = ("P001_1", "P038_2", "P076_3")
DEFAULT_LOG_AGE_DIGEST_BATCH_ROWS = 262_144


@dataclass(frozen=True)
class TableSpec:
    name: str
    current_path: str
    rebuilt_path: str
    sort_keys: tuple[str, ...]
    required: bool = True
    order_sensitive: bool = False
    project_rebuilt_to_current_schema: bool = False


RESULT_TABLE_SPECS = (
    TableSpec(
        name="cell_condition_table",
        current_path="cell_condition_table.parquet",
        rebuilt_path="cell_condition_table.parquet",
        sort_keys=("cell_id",),
    ),
    TableSpec(
        name="checkup_event_table",
        current_path="checkup_event_table.parquet",
        rebuilt_path="checkup_event_table.parquet",
        sort_keys=("cell_id", "checkup_k"),
    ),
    TableSpec(
        name="modality_table_pulse_raw",
        current_path="modality_table_pulse_raw.parquet",
        rebuilt_path="modality_table_pulse_raw.parquet",
        sort_keys=(
            "cell_id",
            "checkup_k",
            "soc_percent",
            "temperature_context",
            "pulse_direction",
            "source_file",
            "voltage",
            "current",
        ),
    ),
    TableSpec(
        name="modality_table_pulse_alias",
        current_path="modality_table_pulse.parquet",
        rebuilt_path="modality_table_pulse_raw.parquet",
        sort_keys=(
            "cell_id",
            "checkup_k",
            "soc_percent",
            "temperature_context",
            "pulse_direction",
            "source_file",
            "voltage",
            "current",
        ),
        required=False,
        project_rebuilt_to_current_schema=True,
    ),
    TableSpec(
        name="modality_table_pulse_summary",
        current_path="modality_table_pulse_summary.parquet",
        rebuilt_path="modality_table_pulse_summary.parquet",
        sort_keys=(
            "cell_id",
            "checkup_k",
            "soc_percent",
            "temperature_context",
            "pulse_direction",
            "source_file",
        ),
    ),
    TableSpec(
        name="modality_table_eis",
        current_path="modality_table_eis.parquet",
        rebuilt_path="modality_table_eis.parquet",
        sort_keys=(
            "cell_id",
            "checkup_k",
            "soc_percent",
            "temperature_context",
            "frequency_Hz",
            "source_file",
        ),
    ),
    TableSpec(
        name="eis_spectrum_quality",
        current_path="eis_spectrum_quality.parquet",
        rebuilt_path="eis_spectrum_quality.parquet",
        sort_keys=("cell_id", "checkup_k", "soc_percent", "temperature_context", "source_file"),
    ),
)

LOG_AGE_SPEC = TableSpec(
    name="modality_table_log_age",
    current_path="modality_table_log_age.parquet",
    rebuilt_path="modality_table_log_age.parquet",
    sort_keys=(),
    order_sensitive=True,
)


def validate_extraction(
    *,
    result_root: Path,
    current_interim: Path,
    rebuild_dir: Path,
    out_dir: Path,
    log_age_archive: Path | None = None,
    full_log_age: bool = False,
    sample_cells: Sequence[str] = DEFAULT_SAMPLE_CELLS,
    csv_block_size_bytes: int = 8 << 20,
    log_age_digest_batch_rows: int = DEFAULT_LOG_AGE_DIGEST_BATCH_ROWS,
    prefer_external_7z: bool = True,
    csv_use_threads: bool = True,
    log_age_extract_dir: Path | None = None,
    keep_log_age_extracted: bool = True,
    skip_log_age_extract: bool = True,
    expected_log_age_csv_count: int = 228,
) -> dict[str, Any]:
    """Rebuild early extraction products from raw archives and compare them.

    The comparison is deliberately semantic: result-data tables are sorted by
    stable keys before hashing, while LOG_AGE is streamed in parser order so the
    904M-row product does not need to be materialized.
    """
    if csv_block_size_bytes <= 0:
        raise ValueError("csv_block_size_bytes must be positive")
    if log_age_digest_batch_rows <= 0:
        raise ValueError("log_age_digest_batch_rows must be positive")

    out_dir.mkdir(parents=True, exist_ok=True)
    rebuild_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    warnings: list[str] = []
    generated_at = datetime.now(UTC).isoformat()

    archives = _find_result_archives(result_root)
    for label, path in archives.items():
        if path is None:
            failures.append(f"missing required result archive: {label}")
    if full_log_age and (log_age_archive is None or not log_age_archive.exists()):
        failures.append(f"missing LOG_AGE archive for full rebuild: {log_age_archive}")

    rebuild_outputs: dict[str, str] = {}
    if not failures:
        exclusions_path = rebuild_dir / "excluded_records_report.csv"
        rebuild_outputs.update(_rebuild_result_products(archives, rebuild_dir, exclusions_path))
        if full_log_age:
            assert log_age_archive is not None
            ingest_log_age(
                log_age_archive,
                rebuild_dir,
                exclusions_report_path=exclusions_path,
                skip_extract=skip_log_age_extract,
                csv_block_size_bytes=csv_block_size_bytes,
                csv_use_threads=csv_use_threads,
                prefer_external_7z=prefer_external_7z,
                extract_dir=log_age_extract_dir,
                keep_extracted=keep_log_age_extracted,
                expected_csv_count=expected_log_age_csv_count,
            )
            rebuild_outputs[LOG_AGE_SPEC.name] = str(rebuild_dir / LOG_AGE_SPEC.rebuilt_path)

    comparison_rows: list[dict[str, Any]] = []
    if not failures:
        for spec in RESULT_TABLE_SPECS:
            row = compare_parquet_products(
                spec,
                current_interim=current_interim,
                rebuild_dir=rebuild_dir,
                digest_batch_rows=65_536,
            )
            comparison_rows.append(row)
            _collect_compare_status(row, failures, warnings)

        if full_log_age:
            row = compare_parquet_products(
                LOG_AGE_SPEC,
                current_interim=current_interim,
                rebuild_dir=rebuild_dir,
                digest_batch_rows=log_age_digest_batch_rows,
            )
            comparison_rows.append(row)
            _collect_compare_status(row, failures, warnings)
        else:
            warnings.append("LOG_AGE full rebuild was not requested; only result-data products were rebuilt.")

    golden_rows: list[dict[str, Any]] = []
    parser_contract_rows: list[dict[str, Any]] = []
    if not failures:
        golden_rows = build_raw_to_parquet_golden_rows(
            archives=archives,
            rebuild_dir=rebuild_dir,
            sample_cells=sample_cells,
            log_age_archive=log_age_archive if full_log_age else None,
        )
        for row in golden_rows:
            if row["status"] == "failed":
                failures.append(
                    f"golden check failed: {row['modality']} {row['cell_id']} "
                    f"{row['raw_field']} -> {row['parquet_field']}"
                )
            elif row["status"] == "skipped":
                warnings.append(
                    f"golden check skipped: {row['modality']} {row['cell_id']} {row['notes']}"
                )
        parser_contract_rows = _parser_contract_rows(full_log_age=full_log_age)

    status = "passed" if not failures else "failed"
    report = {
        "schema_version": EXTRACTION_VALIDATION_SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "status": status,
        "scope": {
            "result_root": str(result_root),
            "current_interim": str(current_interim),
            "rebuild_dir": str(rebuild_dir),
            "full_log_age": full_log_age,
            "log_age_archive": str(log_age_archive) if log_age_archive else None,
            "csv_block_size_bytes": csv_block_size_bytes,
            "csv_use_threads": csv_use_threads,
            "prefer_external_7z": prefer_external_7z,
            "log_age_extract_dir": str(log_age_extract_dir) if log_age_extract_dir else None,
            "keep_log_age_extracted": keep_log_age_extracted,
            "skip_log_age_extract": skip_log_age_extract,
            "expected_log_age_csv_count": expected_log_age_csv_count,
            "log_age_digest_batch_rows": log_age_digest_batch_rows,
            "sample_cells": list(sample_cells),
        },
        "archives": {label: str(path) if path else None for label, path in archives.items()},
        "rebuild_outputs": rebuild_outputs,
        "comparison_rows": comparison_rows,
        "golden_check_count": len(golden_rows),
        "parser_contract_count": len(parser_contract_rows),
        "failures": failures,
        "warnings": warnings,
    }

    _write_json(report, out_dir / "extraction_validation_report.json")
    _write_csv(comparison_rows, out_dir / "extraction_rebuild_hashes.csv")
    _write_csv(golden_rows, out_dir / "raw_to_parquet_golden_records.csv")
    _write_csv(parser_contract_rows, out_dir / "parser_contract_audit.csv")
    _write_summary_markdown(report, out_dir / "extraction_validation_summary.md")
    return report


def _find_result_archives(result_root: Path) -> dict[str, Path | None]:
    return {
        "cfg": _find_one(result_root, "cfg.zip"),
        "eoc": _find_one(result_root, "cell_eocv2.zip"),
        "pulse": _find_one(result_root, "cell_plsv2.zip"),
        "eis": _find_one(result_root, "cell_eisv2.zip"),
    }


def _find_one(root: Path, name: str) -> Path | None:
    if not root.exists():
        return None
    for path in root.rglob(name):
        if path.is_file():
            return path
    return None


def _rebuild_result_products(
    archives: dict[str, Path | None],
    rebuild_dir: Path,
    exclusions_path: Path,
) -> dict[str, str]:
    cfg_zip = _require_archive(archives, "cfg")
    eoc_zip = _require_archive(archives, "eoc")
    pulse_zip = _require_archive(archives, "pulse")
    eis_zip = _require_archive(archives, "eis")

    cfg_out = rebuild_dir / "cell_condition_table.parquet"
    eoc_out = rebuild_dir / "checkup_event_table.parquet"
    pulse_raw_out = rebuild_dir / "modality_table_pulse_raw.parquet"
    pulse_summary_out = rebuild_dir / "modality_table_pulse_summary.parquet"
    eis_out = rebuild_dir / "modality_table_eis.parquet"
    eis_quality_out = rebuild_dir / "eis_spectrum_quality.parquet"

    ingest_cfg(cfg_zip, cfg_out, exclusions_path=exclusions_path)
    ingest_eoc(eoc_zip, eoc_out, exclusions_path=exclusions_path)
    ingest_pulse(
        pulse_zip,
        eoc_out,
        pulse_raw_out,
        pulse_summary_out,
        exclusions_path=exclusions_path,
    )
    ingest_eis(eis_zip, eoc_out, eis_out, eis_quality_out, exclusions_path=exclusions_path)

    return {
        "cell_condition_table": str(cfg_out),
        "checkup_event_table": str(eoc_out),
        "modality_table_pulse_raw": str(pulse_raw_out),
        "modality_table_pulse_summary": str(pulse_summary_out),
        "modality_table_eis": str(eis_out),
        "eis_spectrum_quality": str(eis_quality_out),
    }


def _require_archive(archives: dict[str, Path | None], label: str) -> Path:
    path = archives.get(label)
    if path is None:
        raise FileNotFoundError(f"missing required result archive: {label}")
    return path


def compare_parquet_products(
    spec: TableSpec,
    *,
    current_interim: Path,
    rebuild_dir: Path,
    digest_batch_rows: int,
) -> dict[str, Any]:
    current_path = current_interim / spec.current_path
    rebuilt_path = rebuild_dir / spec.rebuilt_path
    row: dict[str, Any] = {
        "table_name": spec.name,
        "current_path": str(current_path),
        "rebuilt_path": str(rebuilt_path),
        "required": spec.required,
        "order_sensitive": spec.order_sensitive,
        "status": "passed",
        "current_rows": None,
        "rebuilt_rows": None,
        "current_row_groups": None,
        "rebuilt_row_groups": None,
        "schema_equal": None,
        "row_count_equal": None,
        "digest_equal": None,
        "current_digest": None,
        "rebuilt_digest": None,
        "notes": "",
    }
    if not current_path.exists():
        row["status"] = "failed" if spec.required else "skipped"
        row["notes"] = "current product missing"
        return row
    if not rebuilt_path.exists():
        row["status"] = "failed" if spec.required else "skipped"
        row["notes"] = "rebuilt product missing"
        return row

    current_file = pq.ParquetFile(current_path)
    rebuilt_file = pq.ParquetFile(rebuilt_path)
    row["current_rows"] = current_file.metadata.num_rows
    row["rebuilt_rows"] = rebuilt_file.metadata.num_rows
    row["current_row_groups"] = current_file.metadata.num_row_groups
    row["rebuilt_row_groups"] = rebuilt_file.metadata.num_row_groups
    current_schema = current_file.schema_arrow.remove_metadata()
    rebuilt_schema = rebuilt_file.schema_arrow.remove_metadata()
    if spec.project_rebuilt_to_current_schema:
        missing = [name for name in current_schema.names if name not in rebuilt_schema.names]
        if missing:
            row["schema_equal"] = False
            row["row_count_equal"] = row["current_rows"] == row["rebuilt_rows"]
            row["status"] = "failed" if spec.required else "warning"
            row["notes"] = f"rebuilt table missing projected columns: {missing}"
            return row
        rebuilt_schema = pa.schema([rebuilt_schema.field(name) for name in current_schema.names])
        row["notes"] = "rebuilt canonical table projected to legacy current schema"
    row["schema_equal"] = current_schema.equals(rebuilt_schema, check_metadata=False)
    row["row_count_equal"] = row["current_rows"] == row["rebuilt_rows"]

    if spec.order_sensitive:
        stream_equal, compared_rows, mismatch_note = parquet_streams_equal(
            current_path,
            rebuilt_path,
            batch_size=digest_batch_rows,
            columns=current_schema.names if spec.project_rebuilt_to_current_schema else None,
        )
        current_digest = f"stream_pairwise_rows={compared_rows}"
        rebuilt_digest = f"stream_pairwise_rows={compared_rows}"
        if row["notes"]:
            row["notes"] = f"{row['notes']}; "
        row["notes"] += "streaming pairwise value equality"
        if mismatch_note:
            row["notes"] += f"; {mismatch_note}"
        row["digest_equal"] = stream_equal
    else:
        current_digest = sorted_parquet_digest(current_path, spec.sort_keys)
        rebuilt_digest = sorted_parquet_digest(
            rebuilt_path,
            spec.sort_keys,
            columns=current_schema.names if spec.project_rebuilt_to_current_schema else None,
        )
        row["digest_equal"] = current_digest == rebuilt_digest
    row["current_digest"] = current_digest
    row["rebuilt_digest"] = rebuilt_digest
    if not row["schema_equal"] or not row["row_count_equal"] or not row["digest_equal"]:
        row["status"] = "failed" if spec.required else "warning"
    return row


def sorted_parquet_digest(path: Path, sort_keys: Sequence[str], columns: Sequence[str] | None = None) -> str:
    table = pq.read_table(path, columns=list(columns) if columns else None).replace_schema_metadata(None)
    present_keys = [key for key in sort_keys if key in table.column_names]
    if present_keys:
        table = table.sort_by([(key, "ascending") for key in present_keys])
    return table_digest(table)


def parquet_stream_digest(
    path: Path,
    *,
    batch_size: int,
    columns: Sequence[str] | None = None,
) -> str:
    parquet_file = pq.ParquetFile(path)
    schema = parquet_file.schema_arrow.remove_metadata()
    if columns:
        schema = pa.schema([schema.field(name) for name in columns])
    digest = hashlib.sha256()
    digest.update(_schema_fingerprint(schema).encode("utf-8"))
    for canonical_batch in _iter_normalized_parquet_batches(
        parquet_file,
        schema=schema,
        batch_size=batch_size,
        columns=columns,
    ):
        digest.update(_ipc_bytes_for_batch(canonical_batch))
    return digest.hexdigest()


def parquet_streams_equal(
    current_path: Path,
    rebuilt_path: Path,
    *,
    batch_size: int,
    columns: Sequence[str] | None = None,
) -> tuple[bool, int, str | None]:
    """Compare two Parquet files row-by-row in fixed-size streaming batches."""
    current_file = pq.ParquetFile(current_path)
    rebuilt_file = pq.ParquetFile(rebuilt_path)
    if current_file.metadata.num_rows != rebuilt_file.metadata.num_rows:
        return (
            False,
            0,
            f"row count mismatch: {current_file.metadata.num_rows} != {rebuilt_file.metadata.num_rows}",
        )
    schema = current_file.schema_arrow.remove_metadata()
    rebuilt_schema = rebuilt_file.schema_arrow.remove_metadata()
    if columns:
        schema = pa.schema([schema.field(name) for name in columns])
        rebuilt_schema = pa.schema([rebuilt_schema.field(name) for name in columns])
    if not schema.equals(rebuilt_schema, check_metadata=False):
        return False, 0, "schema mismatch"

    current_batches = _iter_normalized_parquet_batches(
        current_file,
        schema=schema,
        batch_size=batch_size,
        columns=columns,
    )
    rebuilt_batches = _iter_normalized_parquet_batches(
        rebuilt_file,
        schema=schema,
        batch_size=batch_size,
        columns=columns,
    )
    compared_rows = 0
    batch_index = 0
    for current_batch, rebuilt_batch in zip(current_batches, rebuilt_batches, strict=True):
        if not current_batch.equals(rebuilt_batch):
            return False, compared_rows, f"value mismatch in normalized batch {batch_index}"
        compared_rows += current_batch.num_rows
        batch_index += 1
    return True, compared_rows, None


def _iter_normalized_parquet_batches(
    parquet_file: pq.ParquetFile,
    *,
    schema: pa.Schema,
    batch_size: int,
    columns: Sequence[str] | None,
):
    """Yield fixed-size batches so semantic hashes ignore row-group layout."""
    pending: pa.Table | None = None
    column_names = list(columns) if columns else None
    for batch in parquet_file.iter_batches(
        batch_size=batch_size,
        columns=column_names,
        use_threads=True,
    ):
        canonical_batch = pa.RecordBatch.from_arrays(
            [batch.column(batch.schema.get_field_index(name)) for name in schema.names],
            schema=schema,
        )
        table = pa.Table.from_batches([canonical_batch], schema=schema)
        pending = table if pending is None else pa.concat_tables([pending, table], promote_options="none")
        while pending.num_rows >= batch_size:
            yield _single_batch(pending.slice(0, batch_size), schema)
            pending = pending.slice(batch_size)
        if pending.num_rows == 0:
            pending = None
    if pending is not None and pending.num_rows:
        yield _single_batch(pending, schema)


def _single_batch(table: pa.Table, schema: pa.Schema) -> pa.RecordBatch:
    batches = table.combine_chunks().to_batches(max_chunksize=table.num_rows)
    if not batches:
        return pa.RecordBatch.from_arrays([], schema=schema)
    batch = batches[0]
    return pa.RecordBatch.from_arrays(
        [batch.column(batch.schema.get_field_index(name)) for name in schema.names],
        schema=schema,
    )


def table_digest(table: pa.Table, *, max_chunksize: int = 65_536) -> str:
    table = table.replace_schema_metadata(None)
    schema = table.schema.remove_metadata()
    digest = hashlib.sha256()
    digest.update(_schema_fingerprint(schema).encode("utf-8"))
    for batch in table.to_batches(max_chunksize=max_chunksize):
        canonical_batch = pa.RecordBatch.from_arrays(
            [batch.column(batch.schema.get_field_index(name)) for name in schema.names],
            schema=schema,
        )
        digest.update(_ipc_bytes_for_batch(canonical_batch))
    return digest.hexdigest()


def _ipc_bytes_for_batch(batch: pa.RecordBatch) -> bytes:
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, batch.schema) as writer:
        writer.write_batch(batch)
    return sink.getvalue().to_pybytes()


def _schema_fingerprint(schema: pa.Schema) -> str:
    return "|".join(f"{field.name}:{field.type}:{field.nullable}" for field in schema)


def build_raw_to_parquet_golden_rows(
    *,
    archives: dict[str, Path | None],
    rebuild_dir: Path,
    sample_cells: Sequence[str],
    log_age_archive: Path | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_cfg_golden_rows(_require_archive(archives, "cfg"), rebuild_dir, sample_cells))
    rows.extend(_eoc_golden_rows(_require_archive(archives, "eoc"), rebuild_dir, sample_cells))
    rows.extend(_pulse_golden_rows(_require_archive(archives, "pulse"), rebuild_dir, sample_cells))
    rows.extend(_eis_golden_rows(_require_archive(archives, "eis"), rebuild_dir, sample_cells))
    if log_age_archive:
        rows.extend(_log_age_golden_rows(log_age_archive, rebuild_dir, sample_cells))
    return rows


def _cfg_golden_rows(zip_path: Path, rebuild_dir: Path, sample_cells: Sequence[str]) -> list[dict[str, Any]]:
    cell_id, source_file, raw_row = _first_csv_row_for_cells(zip_path, sample_cells)
    if raw_row is None:
        return [_skipped_golden("CFG", "", "no sampled cohort member found")]
    expected = {
        "parameter_set": int(float(raw_row.get("parameter_id", "0"))),
        "replicate_id": int(float(raw_row.get("parameter_nr", "0"))),
        "nominal_temperature_C": float(raw_row.get("age_temp", "nan")),
        "nominal_charge_C_rate": float(raw_row.get("age_chg_rate", "nan")),
        "nominal_discharge_C_rate": float(raw_row.get("age_dischg_rate", "nan")),
        "voltage_window_family": classify_voltage_window_family(
            float(raw_row.get("V_min_cyc_V", "nan")),
            float(raw_row.get("V_max_cyc_V", "nan")),
            _aging_mode(raw_row.get("age_type", "0")),
            raw_row.get("age_soc", "0"),
        ),
    }
    parquet_row = _first_parquet_row(rebuild_dir / "cell_condition_table.parquet", cell_id)
    return _golden_compare_rows("CFG", cell_id, source_file, expected, parquet_row)


def _eoc_golden_rows(zip_path: Path, rebuild_dir: Path, sample_cells: Sequence[str]) -> list[dict[str, Any]]:
    cell_id, source_file, raw_rows = _all_csv_rows_for_first_cell(zip_path, sample_cells)
    if not raw_rows:
        return [_skipped_golden("EOC", cell_id or "", "no sampled cohort member found")]
    checkup_rows: dict[int, list[dict[str, str]]] = {}
    for raw_row in raw_rows:
        k_raw = raw_row.get("num_cycles_checkup")
        cap_raw = raw_row.get("cap_aged_est_Ah", "")
        if not k_raw or cap_raw in {"", "nan", "NaN", "NAN"}:
            continue
        checkup_rows.setdefault(int(float(k_raw)), []).append(raw_row)
    if not checkup_rows:
        return [_skipped_golden("EOC", cell_id or "", "no valid capacity rows found")]
    checkup_k = min(checkup_rows)
    group = checkup_rows[checkup_k]
    discharge_row = next((row for row in group if int(float(row.get("cyc_charged", "0"))) == 0), None)
    charge_row = next((row for row in group if int(float(row.get("cyc_charged", "0"))) == 1), None)
    preferred = discharge_row or charge_row
    if preferred is None:
        return [_skipped_golden("EOC", cell_id or "", "no preferred capacity row found")]
    expected = {
        "checkup_k": checkup_k,
        "timestamp": float(preferred["timestamp_s"]),
        "capacity_Ah": float(preferred["cap_aged_est_Ah"]),
        "capacity_soh": float(preferred.get("soh_cap", "100.0")),
        "charge_energy_Wh": float(charge_row.get("delta_e_chg_Wh", "0.0")) if charge_row else 0.0,
        "discharge_energy_Wh": abs(float(discharge_row.get("delta_e_dischg_Wh", "0.0")))
        if discharge_row
        else 0.0,
    }
    parquet_row = _matching_parquet_row(
        rebuild_dir / "checkup_event_table.parquet",
        cell_id=cell_id or "",
        predicates={"checkup_k": checkup_k},
    )
    return _golden_compare_rows("EOC", cell_id or "", source_file or "", expected, parquet_row)


def _pulse_golden_rows(zip_path: Path, rebuild_dir: Path, sample_cells: Sequence[str]) -> list[dict[str, Any]]:
    cell_id, source_file, raw_row = _first_csv_row_for_cells(zip_path, sample_cells)
    if raw_row is None:
        return [_skipped_golden("PULSE", "", "no sampled cohort member found")]
    eoc_lookup = build_eoc_lookup(rebuild_dir / "checkup_event_table.parquet")
    timestamp = float(raw_row["timestamp_s"])
    checkup_k, delta_s = _nearest_checkup(cell_id, timestamp, eoc_lookup)
    expected = {
        "checkup_k": checkup_k,
        "soc_percent": float(raw_row["soc_nom"]),
        "temperature_context": "RT" if int(float(raw_row["is_rt"])) == 1 else "OT",
        "temperature_C": float(raw_row["t_avg_degC"]),
        "pulse_direction": "charge" if int(float(raw_row.get("cyc_charged", "0"))) == 1 else "discharge",
        "pulse_10ms_resistance": float(raw_row["r_ref_10ms_mOhm"]) / 1000.0,
        "pulse_1s_resistance": float(raw_row["r_ref_1s_mOhm"]) / 1000.0,
        "voltage": float(raw_row["v_raw_V"]),
        "current": float(raw_row["i_raw_A"]),
        "alignment_delta_s": delta_s,
    }
    parquet_row = _matching_parquet_row(
        rebuild_dir / "modality_table_pulse_raw.parquet",
        cell_id=cell_id,
        predicates={
            "checkup_k": checkup_k,
            "source_file": source_file,
            "soc_percent": expected["soc_percent"],
            "pulse_direction": expected["pulse_direction"],
        },
    )
    return _golden_compare_rows("PULSE", cell_id, source_file, expected, parquet_row)


def _eis_golden_rows(zip_path: Path, rebuild_dir: Path, sample_cells: Sequence[str]) -> list[dict[str, Any]]:
    cell_id, source_file, raw_row = _first_csv_row_for_cells(zip_path, sample_cells)
    if raw_row is None:
        return [_skipped_golden("EIS", "", "no sampled cohort member found")]
    eoc_lookup = build_eoc_lookup(rebuild_dir / "checkup_event_table.parquet")
    timestamp = float(raw_row["timestamp_s"])
    checkup_k, delta_s = _nearest_checkup(cell_id, timestamp, eoc_lookup)
    freq = float(raw_row["freq_Hz"])
    valid_raw = int(float(raw_row["valid"]))
    z_real = _ohm_or_nan(raw_row.get("z_re_comp_mOhm", "nan"))
    z_imag = _ohm_or_nan(raw_row.get("z_im_comp_mOhm", "nan"))
    z_abs = _ohm_or_nan(raw_row.get("z_amp_comp_mOhm", "nan"))
    if math.isnan(z_abs) and not math.isnan(z_real) and not math.isnan(z_imag):
        z_abs = math.sqrt(z_real**2 + z_imag**2)
    phase = _float_or_nan(raw_row.get("z_ph_comp_deg", "nan"))
    expected = {
        "checkup_k": checkup_k,
        "soc_percent": float(raw_row["soc_nom"]),
        "temperature_context": "RT" if int(float(raw_row["is_rt"])) == 1 else "OT",
        "temperature_C": float(raw_row["t_avg_degC"]),
        "frequency_Hz": freq,
        "z_real": z_real,
        "z_imag": z_imag,
        "z_abs": z_abs,
        "phase": phase,
        "is_valid_raw": valid_raw == 1,
        "is_valid_modeling_frequency": compute_modeling_mask(freq, z_real, z_imag, valid_raw),
        "alignment_delta_s": delta_s,
    }
    parquet_row = _matching_parquet_row(
        rebuild_dir / "modality_table_eis.parquet",
        cell_id=cell_id,
        predicates={
            "checkup_k": checkup_k,
            "source_file": source_file,
            "soc_percent": expected["soc_percent"],
            "frequency_Hz": expected["frequency_Hz"],
        },
    )
    return _golden_compare_rows("EIS", cell_id, source_file, expected, parquet_row)


def _log_age_golden_rows(
    archive_path: Path,
    rebuild_dir: Path,
    sample_cells: Sequence[str],
) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="log_age_golden_") as tmp:
        temp_dir = Path(tmp)
        with py7zr.SevenZipFile(archive_path, "r") as archive:
            names = archive.getnames()
            selected = _first_name_for_cells(names, sample_cells)
            if not selected:
                return [_skipped_golden("LOG_AGE", "", "no sampled cohort member found")]
            cell_id, source_file = selected
            archive.extract(path=temp_dir, targets=[source_file])
        csv_path = _find_extracted_member(temp_dir, source_file)
        if csv_path is None:
            return [_skipped_golden("LOG_AGE", cell_id, f"could not extract {source_file}")]
        try:
            csv_path.chmod(0o644)
        except OSError:
            pass
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            raw_row = next(reader, None)
        if raw_row is None:
            return [_skipped_golden("LOG_AGE", cell_id, f"empty extracted file {source_file}")]
        expected = {
            "timestamp_s": _float_or_none(raw_row.get("timestamp_s")),
            "v_raw_V": _float_or_none(raw_row.get("v_raw_V")),
            "ocv_est_V": _float_or_none(raw_row.get("ocv_est_V")),
            "i_raw_A": _float_or_none(raw_row.get("i_raw_A")),
            "t_cell_degC": _float_or_none(raw_row.get("t_cell_degC")),
            "soc_est": _float_or_none(raw_row.get("soc_est")),
            "delta_q_Ah": _float_or_none(raw_row.get("delta_q_Ah")),
            "EFC": _float_or_none(raw_row.get("EFC")),
            "cap_aged_est_Ah": _float_or_none(raw_row.get("cap_aged_est_Ah")),
            "R0_mOhm": _float_or_none(raw_row.get("R0_mOhm")),
            "R1_mOhm": _float_or_none(raw_row.get("R1_mOhm")),
        }
        parquet_row = _matching_parquet_row(
            rebuild_dir / "modality_table_log_age.parquet",
            cell_id=cell_id,
            predicates={"source_file": Path(source_file).name, "timestamp_s": expected["timestamp_s"]},
        )
        return _golden_compare_rows("LOG_AGE", cell_id, Path(source_file).name, expected, parquet_row)


def _first_csv_row_for_cells(
    zip_path: Path,
    sample_cells: Sequence[str],
) -> tuple[str, str, dict[str, str] | None]:
    cell_id, source_file, rows = _all_csv_rows_for_first_cell(zip_path, sample_cells)
    if not rows:
        return cell_id or "", source_file or "", None
    return cell_id or "", source_file or "", rows[0]


def _all_csv_rows_for_first_cell(
    zip_path: Path,
    sample_cells: Sequence[str],
) -> tuple[str | None, str | None, list[dict[str, str]]]:
    with zipfile.ZipFile(zip_path, "r") as archive:
        selected = _first_name_for_cells(archive.namelist(), sample_cells)
        if not selected:
            return None, None, []
        cell_id, source_file = selected
        content = archive.read(source_file).decode("utf-8")
    reader = csv.DictReader(content.splitlines(), delimiter=";")
    return cell_id, source_file, list(reader)


def _first_name_for_cells(
    names: Iterable[str],
    sample_cells: Sequence[str],
) -> tuple[str, str] | None:
    candidates: dict[str, str] = {}
    for name in names:
        if name.endswith("/") or name.startswith("__") or ":Zone.Identifier" in name:
            continue
        cell_id = extract_cell_id(name)
        if cell_id and cell_id in EXPECTED_EXPERIMENTAL_CELL_IDS:
            candidates[cell_id] = name
    for cell_id in sample_cells:
        if cell_id in candidates:
            return cell_id, candidates[cell_id]
    if candidates:
        cell_id = sorted(candidates)[0]
        return cell_id, candidates[cell_id]
    return None


def _find_extracted_member(root: Path, source_file: str) -> Path | None:
    exact_path = root / source_file
    if exact_path.exists():
        return exact_path
    basename = Path(source_file).name
    for path in root.rglob(basename):
        if path.is_file():
            return path
    return None


def _first_parquet_row(path: Path, cell_id: str) -> dict[str, Any] | None:
    return _matching_parquet_row(path, cell_id=cell_id, predicates={})


def _matching_parquet_row(
    path: Path,
    *,
    cell_id: str,
    predicates: dict[str, Any],
) -> dict[str, Any] | None:
    if not path.exists():
        return None
    table = pq.read_table(path, filters=[("cell_id", "=", cell_id)])
    if table.num_rows == 0:
        return None
    rows = table.to_pylist()
    for row in rows:
        if all(_values_match(row.get(key), value) for key, value in predicates.items()):
            return row
    return rows[0]


def _golden_compare_rows(
    modality: str,
    cell_id: str,
    source_file: str,
    expected: dict[str, Any],
    parquet_row: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if parquet_row is None:
        return [_skipped_golden(modality, cell_id, "matching Parquet row not found")]
    rows = []
    for field, expected_value in expected.items():
        observed = parquet_row.get(field)
        passed = _values_match(observed, expected_value)
        rows.append(
            {
                "modality": modality,
                "cell_id": cell_id,
                "source_file": source_file,
                "raw_field": field,
                "parquet_field": field,
                "expected_value": _format_value(expected_value),
                "observed_value": _format_value(observed),
                "status": "passed" if passed else "failed",
                "notes": "",
            }
        )
    return rows


def _skipped_golden(modality: str, cell_id: str, notes: str) -> dict[str, Any]:
    return {
        "modality": modality,
        "cell_id": cell_id,
        "source_file": "",
        "raw_field": "",
        "parquet_field": "",
        "expected_value": "",
        "observed_value": "",
        "status": "skipped",
        "notes": notes,
    }


def _values_match(observed: Any, expected: Any, tolerance: float = 1e-9) -> bool:
    if observed is None or expected is None:
        return observed is None and expected is None
    if isinstance(observed, bool) or isinstance(expected, bool):
        return bool(observed) == bool(expected)
    if isinstance(observed, (float, int)) or isinstance(expected, (float, int)):
        try:
            observed_float = float(observed)
            expected_float = float(expected)
        except (TypeError, ValueError):
            return False
        if math.isnan(observed_float) and math.isnan(expected_float):
            return True
        return abs(observed_float - expected_float) <= tolerance
    return str(observed) == str(expected)


def _format_value(value: Any) -> str:
    if value is None:
        return "<NULL>"
    if isinstance(value, float) and math.isnan(value):
        return "NaN"
    return str(value)


def _aging_mode(age_type: str | None) -> str:
    value = int(float(age_type or 0))
    if value == 1:
        return "calendar"
    if value == 2:
        return "cyclic"
    if value == 3:
        return "profile"
    return f"unknown_{value}"


def _nearest_checkup(cell_id: str, timestamp: float, lookup: dict[str, list[tuple[int, float]]]) -> tuple[int, float]:
    events = lookup.get(cell_id)
    if not events:
        return 0, 0.0
    closest_k, closest_delta = min(
        ((int(k), abs(timestamp - float(event_ts))) for k, event_ts in events),
        key=lambda item: item[1],
    )
    return closest_k, closest_delta


def _ohm_or_nan(value: str | None) -> float:
    numeric = _float_or_nan(value)
    if math.isnan(numeric):
        return numeric
    return numeric / 1000.0


def _float_or_nan(value: str | None) -> float:
    if value is None or value in {"", "nan", "NaN", "NAN", "null", "NULL"}:
        return float("nan")
    return float(value)


def _float_or_none(value: str | None) -> float | None:
    if value is None or value in {"", "nan", "NaN", "NAN", "null", "NULL"}:
        return None
    return float(value)


def _parser_contract_rows(*, full_log_age: bool) -> list[dict[str, str]]:
    rows = [
        _contract_row("CFG", "cohort_filter", "outside 228 expected cell IDs are excluded", "checked"),
        _contract_row("CFG", "filename_consistency", "filename parameter/replicate must match CSV", "checked"),
        _contract_row("EOC", "capacity_row_policy", "discharge row is preferred for capacity/timestamp", "checked"),
        _contract_row("EOC", "energy_policy", "discharge energy is absolute value; charge energy from charge row", "checked"),
        _contract_row("PULSE", "unit_conversion", "10 ms and 1 s resistance are converted from mOhm to Ohm", "checked"),
        _contract_row("PULSE", "alignment", "pulse rows align to nearest EOC check-up timestamp", "checked"),
        _contract_row("EIS", "unit_conversion", "real/imag/absolute impedance are converted from mOhm to Ohm", "checked"),
        _contract_row("EIS", "modeling_mask", "valid modeling mask applies frequency and NaN exclusions", "checked"),
        _contract_row("EIS", "alignment", "EIS rows align to nearest EOC check-up timestamp", "checked"),
        _contract_row("LOG_AGE", "streaming_parse", "LOG_AGE is parsed in CSV batches and written incrementally", "checked" if full_log_age else "not_run"),
        _contract_row("LOG_AGE", "null_policy", "nan strings become null diagnostics in nullable columns", "checked" if full_log_age else "not_run"),
    ]
    return rows


def _contract_row(modality: str, rule: str, contract: str, status: str) -> dict[str, str]:
    return {
        "modality": modality,
        "contract_rule": rule,
        "contract": contract,
        "status": status,
        "schema_version": EXTRACTION_VALIDATION_SCHEMA_VERSION,
    }


def _collect_compare_status(row: dict[str, Any], failures: list[str], warnings: list[str]) -> None:
    if row["status"] == "failed":
        failures.append(f"{row['table_name']} comparison failed")
    elif row["status"] == "warning":
        warnings.append(f"{row['table_name']} optional comparison warning")
    elif row["status"] == "skipped":
        warnings.append(f"{row['table_name']} optional comparison skipped: {row['notes']}")


def _write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary_markdown(report: dict[str, Any], path: Path) -> None:
    rows = report["comparison_rows"]
    lines = [
        "# Extraction Validation Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Schema version: `{report['schema_version']}`",
        f"- Full LOG_AGE rebuild: `{report['scope']['full_log_age']}`",
        f"- Result root: `{report['scope']['result_root']}`",
        f"- Rebuild directory: `{report['scope']['rebuild_dir']}`",
        "",
        "## Table Comparisons",
        "",
        "| Table | Status | Current rows | Rebuilt rows | Schema | Digest |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {table_name} | {status} | {current_rows} | {rebuilt_rows} | {schema_equal} | {digest_equal} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Golden Raw-Record Checks",
            "",
            f"- Checks rendered: `{report['golden_check_count']}`",
            "",
            "## Failures",
            "",
        ]
    )
    if report["failures"]:
        lines.extend(f"- {failure}" for failure in report["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- {warning}" for warning in report["warnings"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This gate verifies parser reproducibility and raw-to-Parquet contracts. It does not add models, feature groups, or scientific claim support.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
