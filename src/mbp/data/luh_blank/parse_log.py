"""LOG and LOG_AGE parsers for Luh-Blank v2 dataset cell operating logs."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
import py7zr

from mbp.audit.archives import extract_cell_id
from mbp.data.luh_blank.parse_cfg import EXPECTED_EXPERIMENTAL_CELL_IDS
from mbp.data.schema_contracts import (
    MODALITY_TABLE_LOG_AGE_SCHEMA,
    record_exclusions,
)

logger = logging.getLogger(__name__)

LOG_AGE_CSV_COLUMNS = [
    "timestamp_s",
    "v_raw_V",
    "ocv_est_V",
    "i_raw_A",
    "t_cell_degC",
    "soc_est",
    "delta_q_Ah",
    "EFC",
    "cap_aged_est_Ah",
    "R0_mOhm",
    "R1_mOhm",
]

DEFAULT_CSV_BLOCK_SIZE_BYTES = 1 << 20


def _repeated_string(value: str, n_rows: int) -> pa.Array:
    """Build a constant string Arrow array without materializing a Python list."""
    return pa.repeat(pa.scalar(value, type=pa.string()), n_rows)


def _log_age_batch_to_table(
    batch: pa.RecordBatch,
    *,
    cell_id: str,
    source_file: str,
    source_archive: str,
) -> pa.Table:
    """Add provenance columns to a streamed CSV batch and enforce output schema order."""
    n_rows = batch.num_rows
    arrays = [
        _repeated_string(cell_id, n_rows),
        *[batch.column(name) for name in LOG_AGE_CSV_COLUMNS],
        _repeated_string(source_file, n_rows),
        _repeated_string(source_archive, n_rows),
        _repeated_string("", n_rows),
    ]
    return pa.Table.from_arrays(arrays, schema=MODALITY_TABLE_LOG_AGE_SCHEMA)


def ingest_log_age(
    archive_path: Path,
    out_dir: Path,
    exclusions_report_path: Path | None = None,
    skip_extract: bool = False,
    csv_block_size_bytes: int = DEFAULT_CSV_BLOCK_SIZE_BYTES,
    csv_use_threads: bool = False,
    prefer_external_7z: bool = False,
    extract_dir: Path | None = None,
    keep_extracted: bool = False,
    expected_csv_count: int | None = None,
) -> pa.Table:
    """Extract and parse cell-level operating histories from cell_log_age_ultracompr.7z.

    Enforces cohort-level checks, handles missing/NaN formats cleanly inside PyArrow,
    and writes the unified interim modality_table_log_age.parquet table.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"LOG_AGE archive not found at '{archive_path}'")

    if csv_block_size_bytes <= 0:
        raise ValueError("csv_block_size_bytes must be positive")
    if expected_csv_count is not None and expected_csv_count <= 0:
        raise ValueError("expected_csv_count must be positive when provided")

    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_out = out_dir / "modality_table_log_age.parquet"
    if parquet_out.exists():
        parquet_out.unlink()

    # 1. Create or reuse an extraction directory. Supplying extract_dir with
    # keep_extracted=True lets validation extract the 7z archive once and rebuild
    # repeatedly from the CSV cache without repeating decompression.
    temp_extract_dir = extract_dir or out_dir / "tmp_log_age_extracted"

    should_extract = True
    if skip_extract:
        csv_count = _count_csv_files(temp_extract_dir)
        expected_satisfied = expected_csv_count is None or csv_count >= expected_csv_count
        if csv_count and expected_satisfied:
            logger.info(
                "skip_extract is True and %s CSV files found in '%s'. Skipping extraction.",
                csv_count,
                temp_extract_dir,
            )
            should_extract = False
        elif csv_count:
            logger.warning(
                "skip_extract is True but only %s CSV files found in '%s' "
                "(expected at least %s). Re-extracting archive.",
                csv_count,
                temp_extract_dir,
                expected_csv_count,
            )
        else:
            logger.info(
                "skip_extract is True but no CSV files found in '%s'. Proceeding with extraction.",
                temp_extract_dir,
            )

    try:
        if should_extract:
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Extracting cell_log_age_ultracompr.7z to '%s'...", temp_extract_dir)
            if prefer_external_7z and _extract_with_external_7z(archive_path, temp_extract_dir):
                logger.info("Extraction complete using external 7z.")
            else:
                with py7zr.SevenZipFile(archive_path, mode="r") as z:
                    z.extractall(path=temp_extract_dir)
                logger.info("Extraction complete using py7zr.")

            # Ensure all extracted files are readable
            for path in temp_extract_dir.rglob("*.csv"):
                if path.is_file():
                    try:
                        path.chmod(0o644)
                    except Exception:
                        pass

        # 2. Iterate over the uncompressed CSV files
        csv_files = sorted(path for path in temp_extract_dir.rglob("*.csv") if path.is_file())
        logger.info(f"Found {len(csv_files)} log age CSV files to process.")
        if expected_csv_count is not None and len(csv_files) < expected_csv_count:
            raise ValueError(
                f"Only {len(csv_files)} LOG_AGE CSV files found in '{temp_extract_dir}', "
                f"expected at least {expected_csv_count}."
            )

        exclusions = []

        read_options = csv.ReadOptions(
            block_size=csv_block_size_bytes,
            use_threads=csv_use_threads,
        )

        # Custom PyArrow CSV parser options
        # We parse with semicolon delimiter and map literal "nan"/"NAN"/"NaN" to standard PyArrow nulls
        parse_options = csv.ParseOptions(delimiter=";")

        # Explicit column types matching MODALITY_TABLE_LOG_AGE_SCHEMA fields
        column_types = {
            "timestamp_s": pa.float64(),
            "v_raw_V": pa.float64(),
            "ocv_est_V": pa.float64(),
            "i_raw_A": pa.float64(),
            "t_cell_degC": pa.float64(),
            "soc_est": pa.float64(),
            "delta_q_Ah": pa.float64(),
            "EFC": pa.float64(),
            "cap_aged_est_Ah": pa.float64(),
            "R0_mOhm": pa.float64(),
            "R1_mOhm": pa.float64(),
        }
        convert_options = csv.ConvertOptions(
            include_columns=LOG_AGE_CSV_COLUMNS,
            column_types=column_types,
            null_values=["nan", "NAN", "NaN", "null", "NULL", ""],
        )

        writer = None
        written_count = 0
        total_rows_written = 0

        try:
            for csv_file in csv_files:
                cell_id = extract_cell_id(csv_file.name)
                if not cell_id:
                    logger.warning(f"Could not extract cell ID from filename '{csv_file.name}'")
                    continue

                # Cohort validation check
                if cell_id not in EXPECTED_EXPERIMENTAL_CELL_IDS:
                    exclusions.append(
                        {
                            "cell_id": cell_id,
                            "source_archive": archive_path.name,
                            "source_file": csv_file.name,
                            "reason": "Auxiliary cell outside expected 228-cell cohort",
                        }
                    )
                    continue

                try:
                    # Open stream with PyArrow CSV reader to avoid loading entire file into memory at once
                    with csv.open_csv(
                        csv_file,
                        read_options=read_options,
                        parse_options=parse_options,
                        convert_options=convert_options,
                    ) as reader:
                        for batch in reader:
                            table_chunk = _log_age_batch_to_table(
                                batch,
                                cell_id=cell_id,
                                source_file=csv_file.name,
                                source_archive=archive_path.name,
                            )

                            # Write table incrementally to Parquet
                            if writer is None:
                                logger.info(f"Opening ParquetWriter at '{parquet_out}'...")
                                writer = pq.ParquetWriter(parquet_out, MODALITY_TABLE_LOG_AGE_SCHEMA)

                            writer.write_table(table_chunk)
                            total_rows_written += batch.num_rows

                    written_count += 1

                except Exception as e:
                    logger.error(f"Error parsing operating log for cell '{cell_id}' in '{csv_file.name}': {e}")
                    raise

            if written_count == 0:
                raise ValueError("No valid cohort cells were found and parsed from operating logs archive.")

            logger.info(
                "Successfully processed %s cells. Total rows written: %s.",
                written_count,
                total_rows_written,
            )

        finally:
            if writer is not None:
                logger.info("Closing ParquetWriter...")
                writer.close()

        # 5. Record any exclusions
        if exclusions and exclusions_report_path:
            logger.info(f"Recording {len(exclusions)} auxiliary exclusions to '{exclusions_report_path}'...")
            record_exclusions(exclusions, exclusions_report_path)

        # Return a dummy or empty table matching schema for function signature
        return pa.Table.from_batches([], schema=MODALITY_TABLE_LOG_AGE_SCHEMA)

    finally:
        # 6. Always clean up temporary uncompressed files if we extracted them
        if should_extract and temp_extract_dir.exists() and not keep_extracted:
            logger.info("Cleaning up temporary extracted log age files...")
            shutil.rmtree(temp_extract_dir)


def _count_csv_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*.csv") if item.is_file())


def _external_7z_binary() -> str | None:
    """Return an available 7z-compatible binary, if one exists on PATH."""
    for name in ("7zz", "7z", "7za"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _extract_with_external_7z(archive_path: Path, out_dir: Path) -> bool:
    """Extract with a system 7z binary when available.

    py7zr is portable and remains the fallback, but the system 7z binaries can
    use native multithreaded decompression. This is an optimization only; a
    missing binary or non-zero exit code falls back to py7zr so parser semantics
    and test portability stay unchanged.
    """
    binary = _external_7z_binary()
    if not binary:
        return False
    command = [binary, "x", "-y", f"-o{out_dir}", str(archive_path)]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError:
        return False
    if result.returncode != 0:
        logger.warning(
            "External 7z extraction failed with code %s; falling back to py7zr. stderr=%s",
            result.returncode,
            result.stderr.strip()[:500],
        )
        return False
    return True
