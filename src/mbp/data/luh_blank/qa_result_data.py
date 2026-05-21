import json
import math
from pathlib import Path
import re
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow as pa

from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    CONDITION_TABLE_SCHEMA,
    MODALITY_TABLE_LOG_AGE_SCHEMA,
    MODALITY_TABLE_EIS_SCHEMA,
    MODALITY_TABLE_PULSE_SUMMARY_SCHEMA,
    EIS_SPECTRUM_QUALITY_SCHEMA,
    validate_table,
)


def _is_cohort_cell_id(cell_id: str) -> bool:
    m = re.match(r"^P(\d{3})_([1-3])$", cell_id)
    return bool(m and 1 <= int(m.group(1)) <= 76)


def _metadata_unique_values(parquet_file: pq.ParquetFile, column_name: str) -> set[str] | None:
    schema = parquet_file.schema_arrow
    try:
        column_index = schema.get_field_index(column_name)
    except KeyError:
        return None
    if column_index < 0:
        return None

    values: set[str] = set()
    for rg_idx in range(parquet_file.metadata.num_row_groups):
        col = parquet_file.metadata.row_group(rg_idx).column(column_index)
        stats = col.statistics
        if stats is None or stats.min is None or stats.max is None or stats.min != stats.max:
            return None
        values.add(str(stats.min))
    return values


def _null_count(array) -> int:
    return int(pc.sum(pc.cast(pc.is_null(array), "int64")).as_py() or 0)


def _nonnull_count(array) -> int:
    return len(array) - _null_count(array)


def _monotonic_violations_vector(timestamp_array, efc_array) -> int:
    if len(timestamp_array) < 2:
        return 0
    timestamp_diff = pc.pairwise_diff(timestamp_array.combine_chunks())
    efc_diff = pc.pairwise_diff(efc_array.combine_chunks())
    violations = pc.or_(pc.less(timestamp_diff, 0), pc.less(efc_diff, 0))
    return int(pc.sum(pc.cast(violations, "int64")).as_py() or 0)


def _first_last_valid_pair(
    timestamp_array, efc_array
) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    if len(timestamp_array) == 0:
        return None, None
    timestamps = timestamp_array.combine_chunks()
    efc = efc_array.combine_chunks()
    return (
        (float(timestamps[0].as_py()), float(efc[0].as_py())),
        (float(timestamps[-1].as_py()), float(efc[-1].as_py())),
    )


def _qa_log_age(log_age_path: Path, report: dict) -> None:
    if not log_age_path.exists():
        report["tables"]["modality_table_log_age"] = {"exists": False}
        report["failures"].append("modality_table_log_age: Missing Parquet file!")
        report["status"] = "failed"
        return

    try:
        parquet_file = pq.ParquetFile(log_age_path)
        schema_valid = validate_table(
            pa.Table.from_batches([], schema=parquet_file.schema_arrow),
            MODALITY_TABLE_LOG_AGE_SCHEMA,
        )
        row_count = parquet_file.metadata.num_rows
        file_size = log_age_path.stat().st_size

        cell_ids = _metadata_unique_values(parquet_file, "cell_id")
        if cell_ids is None:
            cell_table = pq.read_table(log_age_path, columns=["cell_id"])
            cell_ids = set(cell_table.column("cell_id").to_pylist())

        null_counts = {"cap_aged_est_Ah": 0, "R0_mOhm": 0, "R1_mOhm": 0}
        nonnull_counts = {"cap_aged_est_Ah": 0, "R0_mOhm": 0, "R1_mOhm": 0}
        last_by_cell: dict[str, tuple[float, float]] = {}
        monotonic_violations = 0
        non_cohort_cells = sorted(cid for cid in cell_ids if not _is_cohort_cell_id(cid))

        scan_columns = [
            "cell_id",
            "timestamp_s",
            "EFC",
            "cap_aged_est_Ah",
            "R0_mOhm",
            "R1_mOhm",
        ]
        for rg_idx in range(parquet_file.metadata.num_row_groups):
            batch_table = parquet_file.read_row_group(rg_idx, columns=scan_columns)
            for col in null_counts:
                array = batch_table.column(col)
                null_counts[col] += _null_count(array)
                nonnull_counts[col] += _nonnull_count(array)

            rg_meta = parquet_file.metadata.row_group(rg_idx)
            cell_stats = rg_meta.column(parquet_file.schema_arrow.get_field_index("cell_id")).statistics
            if (
                cell_stats is not None
                and cell_stats.min is not None
                and cell_stats.max is not None
                and cell_stats.min == cell_stats.max
            ):
                cid = str(cell_stats.min)
                timestamps = batch_table.column("timestamp_s")
                efc = batch_table.column("EFC")
                monotonic_violations += _monotonic_violations_vector(timestamps, efc)
                first, last = _first_last_valid_pair(timestamps, efc)
                previous = last_by_cell.get(cid)
                if first and previous and (first[0] < previous[0] or first[1] < previous[1]):
                    monotonic_violations += 1
                if last:
                    last_by_cell[cid] = last
            else:
                data = batch_table.to_pydict()
                for cid, timestamp, efc in zip(data["cell_id"], data["timestamp_s"], data["EFC"]):
                    if timestamp is None or efc is None:
                        continue
                    current = (float(timestamp), float(efc))
                    previous = last_by_cell.get(cid)
                    if previous and (current[0] < previous[0] or current[1] < previous[1]):
                        monotonic_violations += 1
                    last_by_cell[cid] = current

        null_rates = {
            name: (count / row_count if row_count else 0.0) for name, count in null_counts.items()
        }

        report["tables"]["modality_table_log_age"] = {
            "exists": True,
            "row_count": row_count,
            "file_size_bytes": file_size,
            "row_groups": parquet_file.metadata.num_row_groups,
            "unique_cells": len(cell_ids),
            "schema_valid": schema_valid,
            "diagnostic_null_counts": null_counts,
            "diagnostic_nonnull_counts": nonnull_counts,
            "diagnostic_null_rates": null_rates,
            "monotonic_timestamp_efc_violations": monotonic_violations,
            "non_cohort_cell_count": len(non_cohort_cells),
        }

        if not schema_valid:
            report["failures"].append("modality_table_log_age: Schema mismatch!")
            report["status"] = "failed"
        if len(cell_ids) != 228:
            report["failures"].append(
                f"modality_table_log_age: Expected 228 cohort cells, found {len(cell_ids)}!"
            )
            report["status"] = "failed"
        if non_cohort_cells:
            report["failures"].append(
                "modality_table_log_age: Non-cohort cells present in modeling table: "
                + ", ".join(non_cohort_cells[:10])
            )
            report["status"] = "failed"
        if monotonic_violations:
            report["failures"].append(
                f"modality_table_log_age: {monotonic_violations} timestamp/EFC monotonicity violations detected!"
            )
            report["status"] = "failed"

    except Exception as e:
        report["failures"].append(f"modality_table_log_age: Error reading: {e}")
        report["status"] = "failed"


def run_qa_checks(interim_dir: Path, out_report_path: Path) -> dict:
    """Run comprehensive QA and sanity checks on all ingested interim Parquet tables."""
    report = {
        "status": "passed",
        "timestamp_utc": "",
        "tables": {},
        "failures": [],
    }

    import datetime

    report["timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    # Define paths
    cfg_path = interim_dir / "cell_condition_table.parquet"
    eoc_path = interim_dir / "checkup_event_table.parquet"
    pulse_sum_path = interim_dir / "modality_table_pulse_summary.parquet"
    eis_path = interim_dir / "modality_table_eis.parquet"
    eis_qual_path = interim_dir / "eis_spectrum_quality.parquet"
    log_age_path = interim_dir / "modality_table_log_age.parquet"

    # 1. QA CFG (Condition Table)
    if cfg_path.exists():
        try:
            table = pq.read_table(cfg_path)
            is_valid_schema = validate_table(table, CONDITION_TABLE_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            param_sets = pydict["parameter_set"]
            replicates = pydict["replicate_id"]
            aging_modes = pydict["aging_mode"]

            report["tables"]["cell_condition_table"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
            }

            if not is_valid_schema:
                report["failures"].append("cell_condition_table: Schema mismatch!")
                report["status"] = "failed"

            # Enforce 228 cell cohort limits
            if len(table) != 228 or len(cell_ids) != 228:
                report["failures"].append(
                    f"cell_condition_table: Expected exactly 228 cohort cell records, but found {len(table)} rows ({len(cell_ids)} unique cells)!"
                )
                report["status"] = "failed"

            # Validate parameter sets and replicate indices
            for p, r in zip(param_sets, replicates):
                if not (1 <= p <= 76):
                    report["failures"].append(
                        f"cell_condition_table: Found parameter set {p} outside [1, 76] cohort limits!"
                    )
                    report["status"] = "failed"
                if not (1 <= r <= 3):
                    report["failures"].append(
                        f"cell_condition_table: Found replicate {r} outside [1, 3] cohort limits!"
                    )
                    report["status"] = "failed"

            # Verify parameter set counts by aging family: 16 calendar, 48 cyclic, 12 profile
            unique_param_aging = {}
            for p, mode in zip(param_sets, aging_modes):
                unique_param_aging[p] = mode

            cal_count = sum(1 for p, m in unique_param_aging.items() if m == "calendar")
            cyc_count = sum(1 for p, m in unique_param_aging.items() if m == "cyclic")
            prof_count = sum(1 for p, m in unique_param_aging.items() if m == "profile")

            report["tables"]["cell_condition_table"]["aging_mode_counts"] = {
                "calendar": cal_count,
                "cyclic": cyc_count,
                "profile": prof_count,
            }

            if cal_count != 16 or cyc_count != 48 or prof_count != 12:
                report["failures"].append(
                    f"cell_condition_table: Inconsistent nominal aging family counts! "
                    f"Expected 16 calendar, 48 cyclic, 12 profile sets. "
                    f"Found {cal_count} calendar, {cyc_count} cyclic, {prof_count} profile sets."
                )
                report["status"] = "failed"

        except Exception as e:
            report["failures"].append(f"cell_condition_table: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["cell_condition_table"] = {"exists": False}
        report["failures"].append("cell_condition_table: Missing Parquet file!")
        report["status"] = "failed"

    # 2. QA EOC (Checkup Event Table)
    if eoc_path.exists():
        try:
            table = pq.read_table(eoc_path)
            is_valid_schema = validate_table(table, CHECKUP_EVENT_TABLE_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            caps = pydict["capacity_Ah"]

            # Range checks: NMC-SiO nominal capacity is ~3.0 Ah.
            out_of_bounds = [c for c in caps if not (0.0 <= c <= 4.5)]

            report["tables"]["checkup_event_table"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
                "range_violations": len(out_of_bounds),
            }

            if not is_valid_schema:
                report["failures"].append("checkup_event_table: Schema mismatch!")
                report["status"] = "failed"
            if out_of_bounds:
                report["failures"].append(
                    f"checkup_event_table: {len(out_of_bounds)} capacity values out of physical bounds (0.0-4.5 Ah)!"
                )
                report["status"] = "failed"

            # Check that no cell IDs outside cohort exist in EOC table
            for cid in cell_ids:
                if not _is_cohort_cell_id(cid):
                    report["failures"].append(
                        f"checkup_event_table: Non-cohort cell {cid} present in modeling table!"
                    )
                    report["status"] = "failed"

        except Exception as e:
            report["failures"].append(f"checkup_event_table: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["checkup_event_table"] = {"exists": False}
        report["failures"].append("checkup_event_table: Missing Parquet file!")
        report["status"] = "failed"

    # 3. QA PULSE Raw & Summary
    if pulse_sum_path.exists():
        try:
            table = pq.read_table(pulse_sum_path)
            is_valid_schema = validate_table(table, MODALITY_TABLE_PULSE_SUMMARY_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            r10ms = pydict["pulse_10ms_resistance"]
            r1s = pydict["pulse_1s_resistance"]
            deltas = pydict.get("alignment_delta_s", [])

            # Physical checks (Ohm limits)
            out_of_bounds_10ms = [r for r in r10ms if not (0.0 < r < 0.5)]
            out_of_bounds_1s = [r for r in r1s if not (0.0 < r < 0.5)]

            report["tables"]["modality_table_pulse_summary"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
                "r_10ms_violations": len(out_of_bounds_10ms),
                "r_1s_violations": len(out_of_bounds_1s),
            }

            if not is_valid_schema:
                report["failures"].append("modality_table_pulse_summary: Schema mismatch!")
                report["status"] = "failed"
            if out_of_bounds_10ms or out_of_bounds_1s:
                report["failures"].append(
                    "modality_table_pulse_summary: Out-of-bounds resistance values detected!"
                )
                report["status"] = "failed"

            # Check that no cell IDs outside cohort exist
            for cid in cell_ids:
                if not _is_cohort_cell_id(cid):
                    report["failures"].append(
                        f"modality_table_pulse_summary: Non-cohort cell {cid} present in modeling table!"
                    )
                    report["status"] = "failed"

            # Calculate and check alignment deltas (max threshold = 60 hours = 216000 s)
            if deltas:
                valid_deltas = [float(d) for d in deltas if d is not None and not math.isnan(d)]
                if valid_deltas:
                    valid_deltas.sort()
                    n = len(valid_deltas)
                    med = valid_deltas[n // 2]
                    p95 = valid_deltas[int(n * 0.95)]
                    mx = valid_deltas[-1]

                    report["tables"]["modality_table_pulse_summary"]["alignment_delta_stats"] = {
                        "min_s": valid_deltas[0],
                        "median_s": med,
                        "p95_s": p95,
                        "max_s": mx,
                    }

                    if mx > 216000.0:
                        report["failures"].append(
                            f"modality_table_pulse_summary: Max alignment delta of {mx:.1f}s exceeds configured 60-hour threshold!"
                        )
                        report["status"] = "failed"

        except Exception as e:
            report["failures"].append(f"modality_table_pulse_summary: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["modality_table_pulse_summary"] = {"exists": False}
        report["failures"].append("modality_table_pulse_summary: Missing Parquet file!")
        report["status"] = "failed"

    # 4. QA EIS Modeling and Spectrum Quality
    if eis_path.exists():
        try:
            table = pq.read_table(eis_path)
            is_valid_schema = validate_table(table, MODALITY_TABLE_EIS_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            valid_mod_mask = pydict["is_valid_modeling_frequency"]
            deltas = pydict.get("alignment_delta_s", [])

            valid_count = sum(1 for v in valid_mod_mask if v is True)

            report["tables"]["modality_table_eis"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
                "valid_modeling_freq_count": valid_count,
                "valid_modeling_freq_fraction": (
                    valid_count / len(table) if len(table) > 0 else 0.0
                ),
            }

            if not is_valid_schema:
                report["failures"].append("modality_table_eis: Schema mismatch!")
                report["status"] = "failed"

            # Check that no cell IDs outside cohort exist
            for cid in cell_ids:
                if not _is_cohort_cell_id(cid):
                    report["failures"].append(
                        f"modality_table_eis: Non-cohort cell {cid} present in modeling table!"
                    )
                    report["status"] = "failed"

            # Calculate and check alignment deltas (max threshold = 60 hours = 216000 s)
            if deltas:
                valid_deltas = [float(d) for d in deltas if d is not None and not math.isnan(d)]
                if valid_deltas:
                    valid_deltas.sort()
                    n = len(valid_deltas)
                    med = valid_deltas[n // 2]
                    p95 = valid_deltas[int(n * 0.95)]
                    mx = valid_deltas[-1]

                    report["tables"]["modality_table_eis"]["alignment_delta_stats"] = {
                        "min_s": valid_deltas[0],
                        "median_s": med,
                        "p95_s": p95,
                        "max_s": mx,
                    }

                    if mx > 216000.0:
                        report["failures"].append(
                            f"modality_table_eis: Max alignment delta of {mx:.1f}s exceeds configured 60-hour threshold!"
                        )
                        report["status"] = "failed"

        except Exception as e:
            report["failures"].append(f"modality_table_eis: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["modality_table_eis"] = {"exists": False}
        report["failures"].append("modality_table_eis: Missing Parquet file!")
        report["status"] = "failed"

    # 5. QA EIS Spectrum Quality Table Validation
    if eis_qual_path.exists():
        try:
            table = pq.read_table(eis_qual_path)
            is_valid_schema = validate_table(table, EIS_SPECTRUM_QUALITY_SCHEMA)
            report["tables"]["eis_spectrum_quality"] = {
                "exists": True,
                "row_count": len(table),
                "schema_valid": is_valid_schema,
            }
            if not is_valid_schema:
                report["failures"].append("eis_spectrum_quality: Schema mismatch!")
                report["status"] = "failed"
        except Exception as e:
            report["failures"].append(f"eis_spectrum_quality: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["eis_spectrum_quality"] = {"exists": False}

    # 6. QA LOG_AGE reduced operating table. This deliberately uses Parquet metadata and
    # row-group scans so the full table is never materialized.
    _qa_log_age(log_age_path, report)

    # Write report
    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    with out_report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
