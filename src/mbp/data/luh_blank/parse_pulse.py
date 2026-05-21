import csv
import io
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.audit.archives import extract_cell_id
from mbp.data.schema_contracts import (
    MODALITY_TABLE_PULSE_SCHEMA,
    MODALITY_TABLE_PULSE_SUMMARY_SCHEMA,
    validate_table,
    record_exclusions,
)

SCHEMA_VERSION = "gate2.pulse.v2"
EXPECTED_EXPERIMENTAL_CELL_IDS = {f"P{p:03d}_{r}" for p in range(1, 77) for r in range(1, 4)}


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


def find_closest_checkup_k(cell_id: str, timestamp: float, lookup_map: dict) -> tuple[int, float]:
    """Find the checkup_k for a given cell_id that is closest to the given timestamp.

    Returns a tuple of (checkup_k, alignment_delta_s).
    """
    events = lookup_map.get(cell_id)
    if not events:
        return 0, 0.0

    closest_k, min_diff = events[0][0], abs(timestamp - events[0][1])
    for k, eoc_ts in events[1:]:
        diff = abs(timestamp - eoc_ts)
        if diff < min_diff:
            min_diff = diff
            closest_k = k
    return closest_k, min_diff


def parse_pulse_zip(
    zip_path: Path, eoc_lookup: dict, exclusions_path: Path | None = None
) -> tuple[pa.Table, pa.Table]:
    """Parse the cell_plsv2.zip file and align pulse events to checkups.

    Returns a tuple of (raw_table, summary_table).
    """
    raw_data = {
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
        "alignment_method": [],
        "alignment_delta_s": [],
        "source_file": [],
        "quality_flags": [],
    }

    summary_groups = {}
    exclusions = []

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.endswith("/") or name.startswith("__") or ":Zone.Identifier" in name:
                continue

            cell_id = extract_cell_id(name)
            if not cell_id:
                continue

            # Cohort filter
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

            content = z.read(name).decode("utf-8")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")

            for r in reader:
                try:
                    ts = float(r["timestamp_s"])
                    checkup_k, delta_s = find_closest_checkup_k(cell_id, ts, eoc_lookup)

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

                    raw_data["cell_id"].append(cell_id)
                    raw_data["checkup_k"].append(checkup_k)
                    raw_data["soc_percent"].append(soc)
                    raw_data["temperature_context"].append(temp_context)
                    raw_data["temperature_C"].append(temp_c)
                    raw_data["pulse_direction"].append(direction)
                    raw_data["pulse_10ms_resistance"].append(r10ms)
                    raw_data["pulse_1s_resistance"].append(r1s)
                    raw_data["voltage"].append(v)
                    raw_data["current"].append(i)
                    raw_data["alignment_method"].append("nearest_eoc_timestamp")
                    raw_data["alignment_delta_s"].append(delta_s)
                    raw_data["source_file"].append(name)
                    raw_data["quality_flags"].append("OK")

                    # Group for summary table
                    soc_key = round(soc, 1)
                    key = (cell_id, checkup_k, soc_key, temp_context, direction)
                    if key not in summary_groups:
                        summary_groups[key] = {
                            "temp_sum": 0.0,
                            "count": 0,
                            "r10ms": r10ms,
                            "r1s": r1s,
                            "delta_s": delta_s,
                            "source_file": name,
                        }
                    summary_groups[key]["temp_sum"] += temp_c
                    summary_groups[key]["count"] += 1
                except (ValueError, KeyError):
                    continue

    summary_data = {
        "cell_id": [],
        "checkup_k": [],
        "soc_percent": [],
        "temperature_context": [],
        "temperature_C": [],
        "pulse_direction": [],
        "pulse_10ms_resistance": [],
        "pulse_1s_resistance": [],
        "alignment_method": [],
        "alignment_delta_s": [],
        "source_file": [],
        "quality_flags": [],
    }

    for key, val in summary_groups.items():
        cell_id, checkup_k, soc_percent, temp_context, direction = key
        mean_temp = val["temp_sum"] / val["count"]
        summary_data["cell_id"].append(cell_id)
        summary_data["checkup_k"].append(checkup_k)
        summary_data["soc_percent"].append(float(soc_percent))
        summary_data["temperature_context"].append(temp_context)
        summary_data["temperature_C"].append(mean_temp)
        summary_data["pulse_direction"].append(direction)
        summary_data["pulse_10ms_resistance"].append(val["r10ms"])
        summary_data["pulse_1s_resistance"].append(val["r1s"])
        summary_data["alignment_method"].append("nearest_eoc_timestamp")
        summary_data["alignment_delta_s"].append(val["delta_s"])
        summary_data["source_file"].append(val["source_file"])
        summary_data["quality_flags"].append("OK")

    # Record exclusions if any
    if exclusions:
        record_exclusions(exclusions, exclusions_path)

    raw_table = pa.Table.from_pydict(raw_data, schema=MODALITY_TABLE_PULSE_SCHEMA)
    summary_table = pa.Table.from_pydict(summary_data, schema=MODALITY_TABLE_PULSE_SUMMARY_SCHEMA)

    return raw_table, summary_table


def ingest_pulse(
    zip_path: Path,
    eoc_parquet_path: Path,
    out_raw_path: Path,
    out_summary_path: Path,
    exclusions_path: Path | None = None,
) -> None:
    """Read cell_plsv2.zip and save raw and summary pulse modality tables to Parquet."""
    eoc_lookup = build_eoc_lookup(eoc_parquet_path)
    raw_table, summary_table = parse_pulse_zip(zip_path, eoc_lookup, exclusions_path)

    if not validate_table(raw_table, MODALITY_TABLE_PULSE_SCHEMA):
        raise ValueError("Modality table pulse schema validation failed!")
    if not validate_table(summary_table, MODALITY_TABLE_PULSE_SUMMARY_SCHEMA):
        raise ValueError("Modality table pulse summary schema validation failed!")

    out_raw_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(raw_table, out_raw_path)

    out_summary_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(summary_table, out_summary_path)
