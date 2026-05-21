import json
import math
from pathlib import Path
import pyarrow.parquet as pq

from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    CONDITION_TABLE_SCHEMA,
    MODALITY_TABLE_EIS_SCHEMA,
    MODALITY_TABLE_PULSE_SUMMARY_SCHEMA,
    EIS_SPECTRUM_QUALITY_SCHEMA,
    validate_table,
)


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
                import re

                m = re.match(r"^P(\d{3})_([1-3])$", cid)
                if not m or not (1 <= int(m.group(1)) <= 76):
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
                import re

                m = re.match(r"^P(\d{3})_([1-3])$", cid)
                if not m or not (1 <= int(m.group(1)) <= 76):
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
                import re

                m = re.match(r"^P(\d{3})_([1-3])$", cid)
                if not m or not (1 <= int(m.group(1)) <= 76):
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

    # Write report
    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    with out_report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
