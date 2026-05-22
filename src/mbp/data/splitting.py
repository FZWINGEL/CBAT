"""Splitting engine for reproducible condition-grouped and OOD validation splits."""

from __future__ import annotations

import logging
import json
import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import SPLIT_REGISTRY_SCHEMA, validate_table

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "gate3.split.v1"


def generate_split_registry(
    condition_parquet_path: Path,
    out_dir: Path,
) -> pa.Table:
    """Generate the deterministic, condition-grouped split registry.

    Groups replicates of identical parameter sets together to prevent data leakage,
    maps out-of-distribution stressor holdouts, and writes the frozen split_registry_v1.parquet.
    """
    if not condition_parquet_path.exists():
        raise FileNotFoundError(f"Cell condition table not found at '{condition_parquet_path}'")

    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_out = out_dir / "split_registry_v1.parquet"

    # 1. Load cell condition table
    logger.info(f"Loading cell condition table from '{condition_parquet_path}'...")
    condition_table = pq.read_table(condition_parquet_path)

    cell_ids = condition_table.column("cell_id").to_pylist()
    parameter_sets = condition_table.column("parameter_set").to_pylist()
    replicate_ids = condition_table.column("replicate_id").to_pylist()
    aging_modes = condition_table.column("aging_mode").to_pylist()
    nominal_temps = condition_table.column("nominal_temperature_C").to_pylist()
    
    # Optional columns check
    def get_list_col(name: str, default_val: str = "") -> list:
        try:
            return condition_table.column(name).to_pylist()
        except KeyError:
            return [default_val] * len(cell_ids)

    voltage_window_families = [
        _voltage_window_family(row)
        for row in condition_table.to_pylist()
    ]
    charge_rates = get_list_col("nominal_charge_C_rate", 1.0)
    discharge_rates = get_list_col("nominal_discharge_C_rate", 1.0)

    # 2. Determine deterministic S1 condition-grouped ID splits
    # Collect all unique parameter set values in the cohort
    unique_param_sets = sorted(list(set(parameter_sets)))
    logger.info(f"Assigning {len(unique_param_sets)} unique parameter sets deterministically to 5 folds...")

    # We shuffle with a fixed seed to ensure strict reproducibility
    rng = random.Random(42)
    shuffled_params = list(unique_param_sets)
    rng.shuffle(shuffled_params)

    # Map each parameter set to a fold index (0 to 4)
    param_to_fold: dict[int, int] = {}
    for idx, param in enumerate(shuffled_params):
        param_to_fold[param] = idx % 5

    # 3. Process splits for each cell record
    condition_folds: list[int] = []
    temperature_holdouts: list[int] = []
    voltage_window_holdouts: list[int] = []
    soc_window_holdouts: list[int] = []
    c_rate_holdouts: list[int] = []
    profile_holdouts: list[int] = []
    replicate_calibrations: list[int] = []
    time_horizon_folds: list[int] = []

    for i in range(len(cell_ids)):
        param = parameter_sets[i]
        rep = replicate_ids[i]
        mode = aging_modes[i]
        temp = nominal_temps[i]
        voltage_family = str(voltage_window_families[i])
        chg_r = charge_rates[i]
        dis_r = discharge_rates[i]

        # S1: Grouped cross validation fold
        condition_folds.append(param_to_fold[param])

        # S2: Temperature holdout fold
        # 0 = Nominal, 1 = Cold OOD (0C), 2 = Hot OOD (40C)
        if temp == 0.0 or temp == 0:
            temperature_holdouts.append(1)
        elif temp == 40.0 or temp == 40:
            temperature_holdouts.append(2)
        else:
            temperature_holdouts.append(0)

        # S2: Voltage/SOC window holdout fold.
        # 0 = nominal/other, 1 = full/wide voltage window, 2 = reduced cyclic window,
        # 3 = calendar idle-SOC family. Keep the legacy soc_window_holdout_fold
        # populated from the corrected voltage-window logic for backward compatibility.
        voltage_window_fold = _voltage_window_holdout_fold(voltage_family)
        voltage_window_holdouts.append(voltage_window_fold)
        soc_window_holdouts.append(voltage_window_fold)

        # S2: C-rate holdout fold
        # 0 = Nominal, 1 = High Charge/Discharge C-rate OOD (>= 5/3 C)
        if chg_r >= (5.0 / 3.0) or dis_r >= (5.0 / 3.0):
            c_rate_holdouts.append(1)
        else:
            c_rate_holdouts.append(0)

        # S2: Profile family holdout fold
        # 0 = Calendar/Cyclic nominal, 1 = Dynamic Profile holdout
        if mode == "profile":
            profile_holdouts.append(1)
        else:
            profile_holdouts.append(0)

        # Replicate Calibration: Holdout replicate 3 for conformal calibration (1) vs replicates 1 & 2 (0)
        if rep == 3:
            replicate_calibrations.append(1)
        else:
            replicate_calibrations.append(0)

        # Time Horizon: Extrapolation split
        time_horizon_folds.append(0)

    # 4. Create split registry PyArrow table
    pydict = {
        "cell_id": cell_ids,
        "parameter_set": [int(x) for x in parameter_sets],
        "replicate_id": [int(x) for x in replicate_ids],
        "condition_fold": condition_folds,
        "temperature_holdout_fold": temperature_holdouts,
        "voltage_window_holdout_fold": voltage_window_holdouts,
        "soc_window_holdout_fold": soc_window_holdouts,
        "c_rate_holdout_fold": c_rate_holdouts,
        "profile_holdout_fold": profile_holdouts,
        "replicate_calibration_fold": replicate_calibrations,
        "time_horizon_fold": time_horizon_folds,
        "schema_version": [SCHEMA_VERSION] * len(cell_ids),
    }

    split_table = pa.Table.from_pydict(pydict, schema=SPLIT_REGISTRY_SCHEMA)

    # 5. Schema Validation
    logger.info("Validating Split Registry PyArrow table against SPLIT_REGISTRY_SCHEMA...")
    if not validate_table(split_table, SPLIT_REGISTRY_SCHEMA, strict=True):
        raise TypeError("Generated split registry table does not match required SPLIT_REGISTRY_SCHEMA.")

    # 6. Save to Parquet
    logger.info(f"Saving Split Registry ({len(split_table)} rows) to '{parquet_out}'...")
    pq.write_table(split_table, parquet_out)

    return split_table


def audit_split_registry(
    split_registry_path: Path,
    condition_table_path: Path,
    out_path: Path,
) -> dict[str, object]:
    """Audit split registry semantics and write a JSON report."""
    if not split_registry_path.exists():
        raise FileNotFoundError(f"Split registry not found: {split_registry_path}")
    if not condition_table_path.exists():
        raise FileNotFoundError(f"Condition table not found: {condition_table_path}")

    split_rows = pq.read_table(split_registry_path).to_pylist()
    condition_rows = pq.read_table(condition_table_path).to_pylist()
    condition_by_cell = {row["cell_id"]: row for row in condition_rows}
    failures: list[str] = []

    condition_fold_params: dict[int, set[int]] = {}
    replicate_fold_by_param: dict[int, set[int]] = {}
    temperature_counts: dict[int, int] = {}
    temperature_values: dict[int, set[float]] = {}
    soc_counts: dict[int, int] = {}
    soc_values: dict[int, set[str]] = {}
    voltage_window_counts: dict[int, int] = {}
    voltage_window_values: dict[int, set[str]] = {}
    c_rate_counts: dict[int, int] = {}
    c_rate_values: dict[int, set[str]] = {}
    profile_counts: dict[int, int] = {}
    profile_modes: dict[int, set[str]] = {}

    for row in split_rows:
        cell_id = row["cell_id"]
        condition = condition_by_cell[cell_id]
        param = int(row["parameter_set"])
        condition_fold = int(row["condition_fold"])
        replicate_fold_by_param.setdefault(param, set()).add(condition_fold)
        condition_fold_params.setdefault(condition_fold, set()).add(param)

        temp_fold = int(row["temperature_holdout_fold"])
        temperature_counts[temp_fold] = temperature_counts.get(temp_fold, 0) + 1
        temperature_values.setdefault(temp_fold, set()).add(float(condition["nominal_temperature_C"]))

        soc_fold = int(row["soc_window_holdout_fold"])
        soc_counts[soc_fold] = soc_counts.get(soc_fold, 0) + 1
        soc_values.setdefault(soc_fold, set()).add(str(condition["soc_window_approx"]))

        voltage_fold = int(row.get("voltage_window_holdout_fold", soc_fold))
        voltage_window_counts[voltage_fold] = voltage_window_counts.get(voltage_fold, 0) + 1
        voltage_window_values.setdefault(voltage_fold, set()).add(
            _voltage_window_family(condition)
        )

        c_fold = int(row["c_rate_holdout_fold"])
        c_rate_counts[c_fold] = c_rate_counts.get(c_fold, 0) + 1
        c_rate_values.setdefault(c_fold, set()).add(
            f"{condition['nominal_charge_C_rate']}/{condition['nominal_discharge_C_rate']}"
        )

        p_fold = int(row["profile_holdout_fold"])
        profile_counts[p_fold] = profile_counts.get(p_fold, 0) + 1
        profile_modes.setdefault(p_fold, set()).add(str(condition["aging_mode"]))

    for param, folds in replicate_fold_by_param.items():
        if len(folds) != 1:
            failures.append(f"parameter_set {param} has replicates across folds {sorted(folds)}")

    headline_folds = {
        "temperature_holdout_fold cold": temperature_counts.get(1, 0),
        "temperature_holdout_fold hot": temperature_counts.get(2, 0),
        "voltage_window_holdout_fold wide": voltage_window_counts.get(1, 0),
        "voltage_window_holdout_fold reduced": voltage_window_counts.get(2, 0),
        "c_rate_holdout_fold high": c_rate_counts.get(1, 0),
        "profile_holdout_fold profile": profile_counts.get(1, 0),
    }
    for name, count in headline_folds.items():
        if count == 0:
            failures.append(f"{name} is empty")

    report = {
        "status": "failed" if failures else "passed",
        "split_registry": str(split_registry_path),
        "condition_table": str(condition_table_path),
        "row_count": len(split_rows),
        "condition_fold_parameter_set_counts": {
            str(fold): len(params) for fold, params in sorted(condition_fold_params.items())
        },
        "replicates_grouped_by_parameter_set": not any(
            len(folds) != 1 for folds in replicate_fold_by_param.values()
        ),
        "temperature_holdout_fold_counts": _string_key_counts(temperature_counts),
        "temperature_holdout_represented_temperatures": _string_key_values(temperature_values),
        "voltage_window_holdout_fold_counts": _string_key_counts(voltage_window_counts),
        "voltage_window_holdout_represented_families": _string_key_values(
            voltage_window_values
        ),
        "soc_window_holdout_fold_counts": _string_key_counts(soc_counts),
        "soc_window_holdout_represented_windows": _string_key_values(soc_values),
        "c_rate_holdout_fold_counts": _string_key_counts(c_rate_counts),
        "c_rate_holdout_represented_rates": _string_key_values(c_rate_values),
        "profile_holdout_fold_counts": _string_key_counts(profile_counts),
        "profile_holdout_represented_aging_modes": _string_key_values(profile_modes),
        "failures": failures,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _string_key_counts(counts: dict[int, int]) -> dict[str, int]:
    return {str(key): counts[key] for key in sorted(counts)}


def _string_key_values(values: dict[int, set]) -> dict[str, list]:
    return {str(key): sorted(values[key]) for key in sorted(values)}


def _voltage_window_family(row: dict[str, object]) -> str:
    existing = row.get("voltage_window_family")
    if existing:
        return str(existing)
    aging_mode = str(row.get("aging_mode", ""))
    soc = str(row.get("soc_window_approx", "0%")).replace("%", "")
    if aging_mode == "calendar":
        return f"calendar_soc_{soc}"
    voltage_window = str(row.get("voltage_window", ""))
    if voltage_window.startswith("2.50 V - 4.20 V") or voltage_window.startswith("2.5-4.2"):
        return "approx_0_100"
    if voltage_window.startswith("3.25 V - 4.20 V") or voltage_window.startswith("3.249-4.20"):
        return "approx_10_100"
    if voltage_window.startswith("3.25 V - 4.09 V") or voltage_window.startswith("3.249-4.092"):
        return "approx_10_90"
    return f"custom_{voltage_window}"


def _voltage_window_holdout_fold(family: str) -> int:
    if family == "approx_0_100":
        return 1
    if family in {"approx_10_100", "approx_10_90"}:
        return 2
    if family.startswith("calendar_soc_"):
        return 3
    return 0
