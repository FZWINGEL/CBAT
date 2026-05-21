"""CFG parser for Luh-Blank v2 dataset nominal conditions."""

import csv
import io
import re
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.audit.archives import extract_cell_id
from mbp.data.schema_contracts import CONDITION_TABLE_SCHEMA, validate_table, record_exclusions

SCHEMA_VERSION = "gate2.cfg.v2"
EXPECTED_EXPERIMENTAL_CELL_IDS = {f"P{p:03d}_{r}" for p in range(1, 77) for r in range(1, 4)}


def parse_cfg_zip(zip_path: Path, exclusions_path: Path | None = None) -> pa.Table:
    """Parse the cfg.zip file containing nominal cell conditions."""
    data = {
        "cell_id": [],
        "parameter_set": [],
        "replicate_id": [],
        "aging_mode": [],
        "nominal_temperature_C": [],
        "voltage_window": [],
        "soc_window_approx": [],
        "nominal_charge_C_rate": [],
        "nominal_discharge_C_rate": [],
        "profile_label": [],
        "source_file": [],
        "source_archive": [],
        "schema_version": [],
    }

    exclusions = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            # Skip metadata/directories
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

            # Filename parsing matching P###_#
            match = re.search(r"P(\d{3})_(\d)", cell_id)
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
            fn_param_set = int(match.group(1))
            fn_rep_id = int(match.group(2))

            # Read the CSV member
            content = z.read(name).decode("utf-8")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")
            rows = list(reader)
            if not rows:
                continue

            row = rows[0]

            # Parse parameter mapping
            parameter_set = int(float(row.get("parameter_id", 0)))
            replicate_id = int(float(row.get("parameter_nr", 0)))

            # Filename vs CSV consistency check
            if fn_param_set != parameter_set or fn_rep_id != replicate_id:
                raise ValueError(
                    f"Inconsistent metadata for {name}: filename has P{fn_param_set:03d}_{fn_rep_id}, "
                    f"but CSV has parameter_id={parameter_set}, parameter_nr={replicate_id}!"
                )

            # Map age_type to aging_mode (1 = calendar, 2 = cyclic, 3 = profile)
            age_type_val = int(float(row.get("age_type", 0)))
            if age_type_val == 1:
                aging_mode = "calendar"
            elif age_type_val == 2:
                aging_mode = "cyclic"
            elif age_type_val == 3:
                aging_mode = "profile"
            else:
                aging_mode = f"unknown_{age_type_val}"

            nominal_temp = float(row.get("age_temp", 0.0))

            # Voltage Window
            v_min = float(row.get("V_min_cyc_V", 2.5))
            v_max = float(row.get("V_max_cyc_V", 4.2))
            voltage_window = f"{v_min:.2f} V - {v_max:.2f} V"

            # SOC Window
            age_soc = row.get("age_soc", "0")
            soc_window_approx = f"{age_soc}%"

            nominal_chg = float(row.get("age_chg_rate", 0.0))
            nominal_dis = float(row.get("age_dischg_rate", 0.0))

            profile_label = row.get("age_profile", "0")

            data["cell_id"].append(cell_id)
            data["parameter_set"].append(parameter_set)
            data["replicate_id"].append(replicate_id)
            data["aging_mode"].append(aging_mode)
            data["nominal_temperature_C"].append(nominal_temp)
            data["voltage_window"].append(voltage_window)
            data["soc_window_approx"].append(soc_window_approx)
            data["nominal_charge_C_rate"].append(nominal_chg)
            data["nominal_discharge_C_rate"].append(nominal_dis)
            data["profile_label"].append(profile_label)
            data["source_file"].append(name)
            data["source_archive"].append(zip_path.name)
            data["schema_version"].append(SCHEMA_VERSION)

    # Record any exclusions found
    if exclusions:
        record_exclusions(exclusions, exclusions_path)

    table = pa.Table.from_pydict(data, schema=CONDITION_TABLE_SCHEMA)
    return table


def ingest_cfg(zip_path: Path, out_path: Path, exclusions_path: Path | None = None) -> None:
    """Read cfg.zip and save parsed condition table to Parquet."""
    table = parse_cfg_zip(zip_path, exclusions_path)
    if not validate_table(table, CONDITION_TABLE_SCHEMA):
        raise ValueError("Condition table schema validation failed!")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
