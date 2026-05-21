"""Splitting engine for reproducible condition-grouped and OOD validation splits."""

from __future__ import annotations

import logging
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

    soc_windows = get_list_col("soc_window_approx", "40-60")
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
        soc = str(soc_windows[i])
        chg_r = charge_rates[i]
        dis_r = discharge_rates[i]

        # S1: Grouped cross validation fold
        condition_folds.append(param_to_fold[param])

        # S2: Temperature holdout fold
        # 0 = Nominal, 1 = Cold OOD (0C), 2 = Hot OOD (45C)
        if temp == 0.0 or temp == 0:
            temperature_holdouts.append(1)
        elif temp == 45.0 or temp == 45:
            temperature_holdouts.append(2)
        else:
            temperature_holdouts.append(0)

        # S2: SOC Window holdout fold
        # 0 = Nominal, 1 = Wide SOC OOD (e.g. containing 0-100 or 0-90), 2 = Narrow SOC OOD
        if "0-100" in soc or "0-90" in soc:
            soc_window_holdouts.append(1)
        elif "40-60" in soc or "45-55" in soc:
            soc_window_holdouts.append(2)
        else:
            soc_window_holdouts.append(0)

        # S2: C-rate holdout fold
        # 0 = Nominal, 1 = High Charge/Discharge C-rate OOD (>= 2.0 C)
        if chg_r >= 2.0 or dis_r >= 2.0:
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
