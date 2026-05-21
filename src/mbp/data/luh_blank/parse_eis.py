import csv
import io
import math
import zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.audit.archives import extract_cell_id
from mbp.data.luh_blank.parse_pulse import build_eoc_lookup, find_closest_checkup_k
from mbp.data.schema_contracts import (
    MODALITY_TABLE_EIS_SCHEMA,
    EIS_SPECTRUM_QUALITY_SCHEMA,
    validate_table,
    record_exclusions,
)

SCHEMA_VERSION = "gate2.eis.v2"
EXPECTED_EXPERIMENTAL_CELL_IDS = {f"P{p:03d}_{r}" for p in range(1, 77) for r in range(1, 4)}


def compute_modeling_mask(
    frequency_Hz: float, z_real: float, z_imag: float, valid_flag: int
) -> bool:
    """Compute the standard EIS modeling frequency validation mask.

    Rules:
    - 0.5 Hz <= frequency_Hz <= 5000 Hz
    - frequency_Hz is not in {100, 208.3, 14700}
    - Neither z_real nor z_imag is NaN
    - The raw valid flag is 1 (valid)
    """
    if valid_flag != 1:
        return False

    if math.isnan(z_real) or math.isnan(z_imag):
        return False

    if not (0.5 <= frequency_Hz <= 5000.0):
        return False

    # Exclude 100 Hz, 208.3 Hz, 14700 Hz with tolerance
    if abs(frequency_Hz - 100.0) < 0.01:
        return False
    if abs(frequency_Hz - 208.3) < 0.1:
        return False
    if abs(frequency_Hz - 14700.0) < 10.0:
        return False

    return True


def parse_eis_zip(
    zip_path: Path, eoc_lookup: dict, exclusions_path: Path | None = None
) -> tuple[pa.Table, pa.Table]:
    """Parse the cell_eisv2.zip file and evaluate spectrum quality.

    Returns a tuple of (modeling_eis_table, spectrum_quality_table).
    """
    data = {
        "cell_id": [],
        "checkup_k": [],
        "soc_percent": [],
        "temperature_context": [],
        "temperature_C": [],
        "frequency_Hz": [],
        "z_real": [],
        "z_imag": [],
        "z_abs": [],
        "phase": [],
        "is_valid_raw": [],
        "is_valid_modeling_frequency": [],
        "alignment_method": [],
        "alignment_delta_s": [],
        "source_file": [],
        "source_archive": [],
        "quality_flags": [],
    }

    quality_groups = {}
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

                    freq = float(r["freq_Hz"])
                    valid_raw = int(float(r["valid"]))
                    is_valid_raw_bool = valid_raw == 1

                    # Real and imaginary components (convert from mOhm to Ohm)
                    re_mOhm_str = r.get("z_re_comp_mOhm", "nan")
                    im_mOhm_str = r.get("z_im_comp_mOhm", "nan")

                    z_real = float(re_mOhm_str) / 1000.0 if re_mOhm_str != "nan" else float("nan")
                    z_imag = float(im_mOhm_str) / 1000.0 if im_mOhm_str != "nan" else float("nan")

                    # Calculate z_abs
                    amp_mOhm_str = r.get("z_amp_comp_mOhm", "nan")
                    if amp_mOhm_str != "nan" and amp_mOhm_str != "":
                        z_abs = float(amp_mOhm_str) / 1000.0
                    else:
                        if not math.isnan(z_real) and not math.isnan(z_imag):
                            z_abs = math.sqrt(z_real**2 + z_imag**2)
                        else:
                            z_abs = float("nan")

                    # Phase
                    ph_deg_str = r.get("z_ph_comp_deg", "nan")
                    phase = float(ph_deg_str) if ph_deg_str != "nan" else float("nan")

                    # Quality flag / mask
                    is_valid_mod = compute_modeling_mask(freq, z_real, z_imag, valid_raw)

                    data["cell_id"].append(cell_id)
                    data["checkup_k"].append(checkup_k)
                    data["soc_percent"].append(soc)
                    data["temperature_context"].append(temp_context)
                    data["temperature_C"].append(temp_c)
                    data["frequency_Hz"].append(freq)
                    data["z_real"].append(z_real)
                    data["z_imag"].append(z_imag)
                    data["z_abs"].append(z_abs)
                    data["phase"].append(phase)
                    data["is_valid_raw"].append(is_valid_raw_bool)
                    data["is_valid_modeling_frequency"].append(is_valid_mod)
                    data["alignment_method"].append("nearest_eoc_timestamp")
                    data["alignment_delta_s"].append(delta_s)
                    data["source_file"].append(name)
                    data["source_archive"].append(zip_path.name)
                    data["quality_flags"].append("OK")

                    # Group for spectrum quality table
                    soc_key = round(soc, 1)
                    key = (cell_id, checkup_k, soc_key, temp_context)
                    if key not in quality_groups:
                        quality_groups[key] = {
                            "temp_sum": 0.0,
                            "count": 0,
                            "total_freq": 0,
                            "valid_raw": 0,
                            "valid_mod": 0,
                            "delta_s": delta_s,
                            "source_file": name,
                        }
                    quality_groups[key]["temp_sum"] += temp_c
                    quality_groups[key]["count"] += 1
                    quality_groups[key]["total_freq"] += 1
                    if is_valid_raw_bool:
                        quality_groups[key]["valid_raw"] += 1
                    if is_valid_mod:
                        quality_groups[key]["valid_mod"] += 1
                except (ValueError, KeyError):
                    continue

    quality_data = {
        "cell_id": [],
        "checkup_k": [],
        "soc_percent": [],
        "temperature_context": [],
        "temperature_C_mean": [],
        "total_frequencies": [],
        "valid_raw_frequencies": [],
        "valid_modeling_frequencies": [],
        "valid_modeling_fraction": [],
        "alignment_method": [],
        "alignment_delta_s": [],
        "quality_flags": [],
        "source_file": [],
        "source_archive": [],
    }

    for key, val in quality_groups.items():
        cell_id, checkup_k, soc_percent, temp_context = key
        mean_temp = val["temp_sum"] / val["count"]
        tot = val["total_freq"]
        mod_frac = val["valid_mod"] / tot if tot > 0 else 0.0

        quality_data["cell_id"].append(cell_id)
        quality_data["checkup_k"].append(checkup_k)
        quality_data["soc_percent"].append(float(soc_percent))
        quality_data["temperature_context"].append(temp_context)
        quality_data["temperature_C_mean"].append(mean_temp)
        quality_data["total_frequencies"].append(tot)
        quality_data["valid_raw_frequencies"].append(val["valid_raw"])
        quality_data["valid_modeling_frequencies"].append(val["valid_mod"])
        quality_data["valid_modeling_fraction"].append(mod_frac)
        quality_data["alignment_method"].append("nearest_eoc_timestamp")
        quality_data["alignment_delta_s"].append(val["delta_s"])
        quality_data["quality_flags"].append("OK")
        quality_data["source_file"].append(val["source_file"])
        quality_data["source_archive"].append(zip_path.name)

    # Record exclusions if any
    if exclusions:
        record_exclusions(exclusions, exclusions_path)

    modeling_eis_table = pa.Table.from_pydict(data, schema=MODALITY_TABLE_EIS_SCHEMA)
    spectrum_quality_table = pa.Table.from_pydict(quality_data, schema=EIS_SPECTRUM_QUALITY_SCHEMA)

    return modeling_eis_table, spectrum_quality_table


def ingest_eis(
    zip_path: Path,
    eoc_parquet_path: Path,
    out_eis_path: Path,
    out_quality_path: Path,
    exclusions_path: Path | None = None,
) -> None:
    """Read cell_eisv2.zip and save flat EIS modality and quality tables to Parquet."""
    eoc_lookup = build_eoc_lookup(eoc_parquet_path)
    modeling_eis_table, spectrum_quality_table = parse_eis_zip(
        zip_path, eoc_lookup, exclusions_path
    )

    if not validate_table(modeling_eis_table, MODALITY_TABLE_EIS_SCHEMA):
        raise ValueError("Modality table eis schema validation failed!")
    if not validate_table(spectrum_quality_table, EIS_SPECTRUM_QUALITY_SCHEMA):
        raise ValueError("Spectrum quality table schema validation failed!")

    out_eis_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(modeling_eis_table, out_eis_path)

    out_quality_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(spectrum_quality_table, out_quality_path)
