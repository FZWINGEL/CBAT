"""LOG and LOG_AGE parsers for Luh-Blank v2 dataset cell operating logs."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
import py7zr

from mbp.audit.archives import extract_cell_id
from mbp.data.luh_blank.parse_cfg import EXPECTED_EXPERIMENTAL_CELL_IDS
from mbp.data.schema_contracts import (
    MODALITY_TABLE_LOG_AGE_SCHEMA,
    validate_table,
    record_exclusions,
)

logger = logging.getLogger(__name__)


def ingest_log_age(
    archive_path: Path,
    out_dir: Path,
    exclusions_report_path: Path | None = None,
) -> pa.Table:
    """Extract and parse cell-level operating histories from cell_log_age_ultracompr.7z.

    Enforces cohort-level checks, handles missing/NaN formats cleanly inside PyArrow,
    and writes the unified interim modality_table_log_age.parquet table.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"LOG_AGE archive not found at '{archive_path}'")

    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_out = out_dir / "modality_table_log_age.parquet"

    # 1. Create a workspace temporary extraction directory
    temp_extract_dir = out_dir / "tmp_log_age_extracted"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Extracting cell_log_age_ultracompr.7z to '{temp_extract_dir}'...")
        with py7zr.SevenZipFile(archive_path, mode="r") as z:
            z.extractall(path=temp_extract_dir)
        logger.info("Extraction complete!")

        # 2. Iterate over the uncompressed CSV files
        csv_files = sorted(temp_extract_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} log age CSV files to process.")

        tables: list[pa.Table] = []
        exclusions = []

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
            column_types=column_types,
            null_values=["nan", "NAN", "NaN", "null", "NULL", ""],
        )

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
                # Load fast with PyArrow CSV reader
                table = csv.read_csv(
                    csv_file,
                    parse_options=parse_options,
                    convert_options=convert_options,
                )

                # Add additional provenance fields to match schema contract
                n_rows = len(table)
                cell_id_col = pa.array([cell_id] * n_rows, type=pa.string())
                source_file_col = pa.array([csv_file.name] * n_rows, type=pa.string())
                source_archive_col = pa.array([archive_path.name] * n_rows, type=pa.string())
                quality_flags_col = pa.array([""] * n_rows, type=pa.string())

                table = table.append_column("cell_id", cell_id_col)
                table = table.append_column("source_file", source_file_col)
                table = table.append_column("source_archive", source_archive_col)
                table = table.append_column("quality_flags", quality_flags_col)

                # Ensure exact column order matching schema contract
                ordered_cols = [MODALITY_TABLE_LOG_AGE_SCHEMA.field(i).name for i in range(len(MODALITY_TABLE_LOG_AGE_SCHEMA))]
                table = table.select(ordered_cols)

                tables.append(table)
            except Exception as e:
                logger.error(f"Error parsing operating log for cell '{cell_id}' in '{csv_file.name}': {e}")
                raise

        # 3. Concatenate and validate
        if not tables:
            raise ValueError("No valid cohort cells were found and parsed from operating logs archive.")

        logger.info("Concatenating cell operating log tables...")
        merged_table = pa.concat_tables(tables)

        logger.info("Validating schema contracts for merged operating logs table...")
        if not validate_table(merged_table, MODALITY_TABLE_LOG_AGE_SCHEMA, strict=True):
            raise TypeError("Merged operating log table does not match required MODALITY_TABLE_LOG_AGE_SCHEMA contract.")

        # 4. Save to Parquet
        logger.info(f"Saving merged operating logs table ({len(merged_table)} rows) to '{parquet_out}'...")
        pq.write_table(merged_table, parquet_out)

        # 5. Record any exclusions
        if exclusions and exclusions_report_path:
            logger.info(f"Recording {len(exclusions)} auxiliary exclusions to '{exclusions_report_path}'...")
            record_exclusions(exclusions, exclusions_report_path)

        return merged_table

    finally:
        # 6. Always clean up temporary uncompressed files
        if temp_extract_dir.exists():
            logger.info("Cleaning up temporary extracted log age files...")
            shutil.rmtree(temp_extract_dir)
