"""PULSE parser for Luh-Blank v2 dataset diagnostic resistance response."""

import csv
import io
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.audit.archives import extract_cell_id
from mbp.data.schema_contracts import MODALITY_TABLE_PULSE_SCHEMA, validate_table

SCHEMA_VERSION = "gate2.pulse.v1"


def build_eoc_lookup(eoc_parquet_path: Path) -> dict:
    """Build a lookup map of cell_id -> [(checkup_k, timestamp)] from EOC Parquet."""
    lookup = {}
    if not eoc_parquet_path.exists():
        return lookup

    table = pq.read_table(eoc_parquet_path)
    df = table.to_pydict()

    cell_ids = df["cell_id"]
    checkup_ks = df["checkup_k"]
    timestamps = df["timestamp"]
    for cell_id, k, ts in zip(cell_ids, checkup_ks, timestamps):
        lookup.setdefault(cell_id, []).append((int(k), float(ts)))

    return lookup


def find_closest_checkup_k(cell_id: str, timestamp: float, lookup_map: dict) -> int:
    """Find the checkup_k for a given cell_id that is closest to the given timestamp."""
    events = lookup_map.get(cell_id)
    if not events:
        return 0

    closest_k, min_diff = events[0][0], abs(timestamp - events[0][1])
    for k, eoc_ts in events[1:]:
        diff = abs(timestamp - eoc_ts)
        if diff < min_diff:
            min_diff = diff
            closest_k = k
    return closest_k


def parse_pulse_zip(zip_path: Path, eoc_lookup: dict) -> pa.Table:
    """Parse the cell_plsv2.zip file and align high-res pulse rows to checkups."""
    data = {
        "cell_id": [],
        "checkup_k": [],
        "soc_percent": [],
        "temperature_context": [],
        "temperature_C": [],
        "pulse_direction": [],
        "pulse_10ms_resistance": [],
        "pulse_1s_resistance": [],
        "voltage": [],
        "current": [],
        "source_file": [],
        "quality_flags": [],
    }

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.endswith("/") or name.startswith("__") or ":Zone.Identifier" in name:
                continue

            cell_id = extract_cell_id(name)
            if not cell_id:
                continue

            content = z.read(name).decode("utf-8")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")

            # For faster iteration, read row-by-row
            for r in reader:
                try:
                    ts = float(r["timestamp_s"])
                    checkup_k = find_closest_checkup_k(cell_id, ts, eoc_lookup)

                    soc = float(r["soc_nom"])
                    temp_context = "RT" if int(float(r["is_rt"])) == 1 else "OT"
                    temp_c = float(r["t_avg_degC"])

                    # Direction
                    cyc_charged = int(float(r.get("cyc_charged", 0)))
                    direction = "charge" if cyc_charged == 1 else "discharge"

                    # Convert resistances from mOhm to Ohm
                    r10ms = float(r["r_ref_10ms_mOhm"]) / 1000.0
                    r1s = float(r["r_ref_1s_mOhm"]) / 1000.0

                    v = float(r["v_raw_V"])
                    i = float(r["i_raw_A"])

                    data["cell_id"].append(cell_id)
                    data["checkup_k"].append(checkup_k)
                    data["soc_percent"].append(soc)
                    data["temperature_context"].append(temp_context)
                    data["temperature_C"].append(temp_c)
                    data["pulse_direction"].append(direction)
                    data["pulse_10ms_resistance"].append(r10ms)
                    data["pulse_1s_resistance"].append(r1s)
                    data["voltage"].append(v)
                    data["current"].append(i)
                    data["source_file"].append(name)
                    data["quality_flags"].append("OK")
                except (ValueError, KeyError):
                    continue

    table = pa.Table.from_pydict(data, schema=MODALITY_TABLE_PULSE_SCHEMA)
    return table


def ingest_pulse(zip_path: Path, eoc_parquet_path: Path, out_path: Path) -> None:
    """Read cell_plsv2.zip and save flat pulse modality table to Parquet."""
    eoc_lookup = build_eoc_lookup(eoc_parquet_path)
    table = parse_pulse_zip(zip_path, eoc_lookup)
    if not validate_table(table, MODALITY_TABLE_PULSE_SCHEMA):
        raise ValueError("Modality table pulse schema validation failed!")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
