"""Quality Assurance and integrity checks for parsed Luh-Blank v2 data products."""

import json
from pathlib import Path
import pyarrow.parquet as pq

from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    CONDITION_TABLE_SCHEMA,
    MODALITY_TABLE_EIS_SCHEMA,
    MODALITY_TABLE_PULSE_SCHEMA,
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
    pulse_path = interim_dir / "modality_table_pulse.parquet"
    eis_path = interim_dir / "modality_table_eis.parquet"

    # 1. QA CFG (Condition Table)
    if cfg_path.exists():
        try:
            table = pq.read_table(cfg_path)
            is_valid_schema = validate_table(table, CONDITION_TABLE_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])

            report["tables"]["cell_condition_table"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
            }
            if not is_valid_schema:
                report["failures"].append("cell_condition_table: Schema mismatch!")
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

            # Range checks: NM/C-SiO nominal cell capacity is ~3.0 Ah. Range should be 0.0 to 4.5 Ah.
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
        except Exception as e:
            report["failures"].append(f"checkup_event_table: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["checkup_event_table"] = {"exists": False}
        report["failures"].append("checkup_event_table: Missing Parquet file!")
        report["status"] = "failed"

    # 3. QA PULSE (Modality Table Pulse)
    if pulse_path.exists():
        try:
            table = pq.read_table(pulse_path)
            is_valid_schema = validate_table(table, MODALITY_TABLE_PULSE_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            r10ms = pydict["pulse_10ms_resistance"]
            r1s = pydict["pulse_1s_resistance"]

            # Physical check: resistance should be positive and small (e.g. 0 to 0.5 Ohm)
            out_of_bounds_10ms = [r for r in r10ms if not (0.0 < r < 0.5)]
            out_of_bounds_1s = [r for r in r1s if not (0.0 < r < 0.5)]

            report["tables"]["modality_table_pulse"] = {
                "exists": True,
                "row_count": len(table),
                "unique_cells": len(cell_ids),
                "schema_valid": is_valid_schema,
                "r_10ms_violations": len(out_of_bounds_10ms),
                "r_1s_violations": len(out_of_bounds_1s),
            }
            if not is_valid_schema:
                report["failures"].append("modality_table_pulse: Schema mismatch!")
                report["status"] = "failed"
            if out_of_bounds_10ms or out_of_bounds_1s:
                report["failures"].append(
                    f"modality_table_pulse: Out-of-bounds resistance values detected (10ms violations: {len(out_of_bounds_10ms)}, 1s violations: {len(out_of_bounds_1s)})!"
                )
                report["status"] = "failed"
        except Exception as e:
            report["failures"].append(f"modality_table_pulse: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["modality_table_pulse"] = {"exists": False}
        report["failures"].append("modality_table_pulse: Missing Parquet file!")
        report["status"] = "failed"

    # 4. QA EIS (Modality Table EIS)
    if eis_path.exists():
        try:
            table = pq.read_table(eis_path)
            is_valid_schema = validate_table(table, MODALITY_TABLE_EIS_SCHEMA)
            pydict = table.to_pydict()
            cell_ids = set(pydict["cell_id"])
            valid_mod_mask = pydict["is_valid_modeling_frequency"]

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
        except Exception as e:
            report["failures"].append(f"modality_table_eis: Error reading: {e}")
            report["status"] = "failed"
    else:
        report["tables"]["modality_table_eis"] = {"exists": False}
        report["failures"].append("modality_table_eis: Missing Parquet file!")
        report["status"] = "failed"

    # Write report
    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    with out_report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
