"""EOC parser for Luh-Blank v2 dataset capacity check-ups."""

import csv
import io
import re
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.audit.archives import extract_cell_id
from mbp.data.schema_contracts import CHECKUP_EVENT_TABLE_SCHEMA, validate_table

SCHEMA_VERSION = "gate2.eoc.v2"
CELL_ID_PARSER = re.compile(r"P(\d{3})_(\d)")
EXPECTED_EXPERIMENTAL_CELL_IDS = {f"P{p:03d}_{r}" for p in range(1, 77) for r in range(1, 4)}


def parse_eoc_zip(zip_path: Path, exclusions_path: Path | None = None) -> pa.Table:
    """Parse the cell_eocv2.zip file and aggregate checkup events."""
    data = {
        "cell_id": [],
        "parameter_set": [],
        "replicate_id": [],
        "checkup_k": [],
        "timestamp": [],
        "capacity_Ah": [],
        "capacity_soh": [],
        "charge_energy_Wh": [],
        "discharge_energy_Wh": [],
        "temperature_context": [],
        "source_file": [],
        "source_archive": [],
        "schema_version": [],
        "quality_flags": [],
    }

    exclusions = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.endswith("/") or name.startswith("__") or ":Zone.Identifier" in name:
                continue

            cell_id = extract_cell_id(name)
            if not cell_id:
                continue

            # Cohort filter check
            if cell_id not in EXPECTED_EXPERIMENTAL_CELL_IDS:
                exclusions.append(
                    {
                        "cell_id": cell_id,
                        "source_archive": zip_path.name,
                        "source_file": name,
                        "reason": "Auxiliary cell outside expected 228-cell cohort",
                    }
                )
                continue

            # Infer parameter set and replicate ID from cell ID P###_#
            match = CELL_ID_PARSER.search(cell_id)
            if not match:
                exclusions.append(
                    {
                        "cell_id": cell_id,
                        "source_archive": zip_path.name,
                        "source_file": name,
                        "reason": "Malformed cell ID pattern",
                    }
                )
                continue

            param_set = int(match.group(1))
            rep_id = int(match.group(2))

            # Read the CSV member
            content = z.read(name).decode("utf-8")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")
            rows = list(reader)

            # Group rows by num_cycles_checkup for which cap_aged_est_Ah is not 'nan'
            checkup_groups = {}
            for r in rows:
                k_str = r.get("num_cycles_checkup")
                cap_val = r.get("cap_aged_est_Ah", "nan")
                if k_str is None or cap_val == "nan" or cap_val == "":
                    continue
                k = int(float(k_str))
                checkup_groups.setdefault(k, []).append(r)

            # Combine charge and discharge cycle per checkup_k
            for k, group_rows in checkup_groups.items():
                discharge_row = None
                charge_row = None
                for r in group_rows:
                    cyc_charged = int(float(r.get("cyc_charged", 0)))
                    if cyc_charged == 0:
                        discharge_row = r
                    elif cyc_charged == 1:
                        charge_row = r

                # We prefer the discharge row for capacity and timestamp
                pref_row = discharge_row if discharge_row is not None else charge_row
                if not pref_row:
                    continue

                capacity_Ah = float(pref_row["cap_aged_est_Ah"])
                capacity_soh = float(pref_row.get("soh_cap", 100.0))
                timestamp = float(pref_row["timestamp_s"])

                # Energys
                charge_energy_Wh = 0.0
                if charge_row:
                    charge_energy_Wh = float(charge_row.get("delta_e_chg_Wh", 0.0))

                discharge_energy_Wh = 0.0
                if discharge_row:
                    discharge_energy_Wh = abs(float(discharge_row.get("delta_e_dischg_Wh", 0.0)))

                data["cell_id"].append(cell_id)
                data["parameter_set"].append(param_set)
                data["replicate_id"].append(rep_id)
                data["checkup_k"].append(k)
                data["timestamp"].append(timestamp)
                data["capacity_Ah"].append(capacity_Ah)
                data["capacity_soh"].append(capacity_soh)
                data["charge_energy_Wh"].append(charge_energy_Wh)
                data["discharge_energy_Wh"].append(discharge_energy_Wh)
                data["temperature_context"].append("RT")
                data["source_file"].append(name)
                data["source_archive"].append(zip_path.name)
                data["schema_version"].append(SCHEMA_VERSION)
                data["quality_flags"].append("OK")

    # Record exclusions if any
    if exclusions:
        from mbp.data.schema_contracts import record_exclusions

        record_exclusions(exclusions, exclusions_path)

    table = pa.Table.from_pydict(data, schema=CHECKUP_EVENT_TABLE_SCHEMA)
    return table


def ingest_eoc(zip_path: Path, out_path: Path, exclusions_path: Path | None = None) -> None:
    """Read cell_eocv2.zip and save checkup event table to Parquet."""
    table = parse_eoc_zip(zip_path, exclusions_path)
    if not validate_table(table, CHECKUP_EVENT_TABLE_SCHEMA):
        raise ValueError("Checkup event table schema validation failed!")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
