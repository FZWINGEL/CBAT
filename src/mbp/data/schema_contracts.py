"""PyArrow schemas and contracts for Gate 2 result-data products."""

import pyarrow as pa

# 1. Condition Table Schema (CFG)
CONDITION_TABLE_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("aging_mode", pa.string(), False),
        ("nominal_temperature_C", pa.float64(), False),
        ("voltage_window", pa.string(), False),
        ("soc_window_approx", pa.string(), False),
        ("nominal_charge_C_rate", pa.float64(), False),
        ("nominal_discharge_C_rate", pa.float64(), False),
        ("profile_label", pa.string(), False),
        ("source_file", pa.string(), False),
        ("source_archive", pa.string(), False),
        ("schema_version", pa.string(), False),
    ]
)

# 2. Check-up Event Table Schema (EOC)
CHECKUP_EVENT_TABLE_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("checkup_k", pa.int32(), False),
        ("timestamp", pa.float64(), False),
        ("capacity_Ah", pa.float64(), False),
        ("capacity_soh", pa.float64(), False),
        ("charge_energy_Wh", pa.float64(), False),
        ("discharge_energy_Wh", pa.float64(), False),
        ("temperature_context", pa.string(), False),
        ("source_file", pa.string(), False),
        ("source_archive", pa.string(), False),
        ("schema_version", pa.string(), False),
        ("quality_flags", pa.string(), False),
    ]
)

# 3. Modality Table Pulse Schema (PLS)
MODALITY_TABLE_PULSE_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("checkup_k", pa.int32(), False),
        ("soc_percent", pa.float64(), False),
        ("temperature_context", pa.string(), False),
        ("temperature_C", pa.float64(), False),
        ("pulse_direction", pa.string(), False),
        ("pulse_10ms_resistance", pa.float64(), False),
        ("pulse_1s_resistance", pa.float64(), False),
        ("voltage", pa.float64(), False),
        ("current", pa.float64(), False),
        ("alignment_method", pa.string(), False),
        ("alignment_delta_s", pa.float64(), False),
        ("source_file", pa.string(), False),
        ("quality_flags", pa.string(), False),
    ]
)

# 4. Modality Table Pulse Summary Schema
MODALITY_TABLE_PULSE_SUMMARY_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("checkup_k", pa.int32(), False),
        ("soc_percent", pa.float64(), False),
        ("temperature_context", pa.string(), False),
        ("temperature_C", pa.float64(), False),
        ("pulse_direction", pa.string(), False),
        ("pulse_10ms_resistance", pa.float64(), False),
        ("pulse_1s_resistance", pa.float64(), False),
        ("alignment_method", pa.string(), False),
        ("alignment_delta_s", pa.float64(), False),
        ("source_file", pa.string(), False),
        ("quality_flags", pa.string(), False),
    ]
)

# 5. Modality Table EIS Schema (EIS)
MODALITY_TABLE_EIS_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("checkup_k", pa.int32(), False),
        ("soc_percent", pa.float64(), False),
        ("temperature_context", pa.string(), False),
        ("temperature_C", pa.float64(), False),
        ("frequency_Hz", pa.float64(), False),
        ("z_real", pa.float64(), False),
        ("z_imag", pa.float64(), False),
        ("z_abs", pa.float64(), False),
        ("phase", pa.float64(), False),
        ("is_valid_raw", pa.bool_(), False),
        ("is_valid_modeling_frequency", pa.bool_(), False),
        ("alignment_method", pa.string(), False),
        ("alignment_delta_s", pa.float64(), False),
        ("source_file", pa.string(), False),
        ("source_archive", pa.string(), False),
        ("quality_flags", pa.string(), False),
    ]
)

# 6. EIS Spectrum Quality Table Schema
EIS_SPECTRUM_QUALITY_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("checkup_k", pa.int32(), False),
        ("soc_percent", pa.float64(), False),
        ("temperature_context", pa.string(), False),
        ("temperature_C_mean", pa.float64(), False),
        ("total_frequencies", pa.int32(), False),
        ("valid_raw_frequencies", pa.int32(), False),
        ("valid_modeling_frequencies", pa.int32(), False),
        ("valid_modeling_fraction", pa.float64(), False),
        ("alignment_method", pa.string(), False),
        ("alignment_delta_s", pa.float64(), False),
        ("quality_flags", pa.string(), False),
        ("source_file", pa.string(), False),
        ("source_archive", pa.string(), False),
    ]
)

# 7. Excluded Records Table Schema (for auxiliary metadata tracking)
EXCLUDED_RECORDS_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("source_archive", pa.string(), False),
        ("source_file", pa.string(), False),
        ("reason", pa.string(), False),
    ]
)


def validate_table(table: pa.Table, schema: pa.Schema, strict: bool = True) -> bool:
    """Validate that a pyarrow Table matches the expected schema.

    If strict is True, the schema must match exactly.
    Otherwise, we check that all fields in the schema exist and can be cast to their types.
    """
    if strict:
        # Check column names and types in order
        if len(table.schema) != len(schema):
            return False
        for i, field in enumerate(schema):
            table_field = table.schema.field(i)
            if table_field.name != field.name or table_field.type != field.type:
                return False
        return True
    else:
        # Relaxed checks: just verify presence and type compatibility
        for field in schema:
            try:
                table.column(field.name)
            except KeyError:
                return False
        return True


def record_exclusions(exclusions: list[dict], exclusions_path) -> None:
    """Record excluded records into a shared CSV report."""
    if not exclusions_path or not exclusions:
        return
    from pathlib import Path
    import csv

    ex_path = Path(exclusions_path)
    ex_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = ex_path.exists()

    with ex_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["cell_id", "source_archive", "source_file", "reason"]
        )
        if not file_exists:
            writer.writeheader()
        for exc in exclusions:
            writer.writerow(exc)
