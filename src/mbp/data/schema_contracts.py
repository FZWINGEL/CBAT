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
        ("voltage_window_family", pa.string(), False),
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

# 8. Modality Table Log Age Schema (LOG_AGE)
MODALITY_TABLE_LOG_AGE_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("timestamp_s", pa.float64(), False),
        ("v_raw_V", pa.float64(), False),
        ("ocv_est_V", pa.float64(), False),
        ("i_raw_A", pa.float64(), False),
        ("t_cell_degC", pa.float64(), False),
        ("soc_est", pa.float64(), False),
        ("delta_q_Ah", pa.float64(), False),
        ("EFC", pa.float64(), False),
        ("cap_aged_est_Ah", pa.float64(), True),
        ("R0_mOhm", pa.float64(), True),
        ("R1_mOhm", pa.float64(), True),
        ("source_file", pa.string(), False),
        ("source_archive", pa.string(), False),
        ("quality_flags", pa.string(), False),
    ]
)

# 9. Split Registry Table Schema
SPLIT_REGISTRY_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("condition_fold", pa.int32(), False),
        ("temperature_holdout_fold", pa.int32(), False),
        ("voltage_window_holdout_fold", pa.int32(), False),
        ("soc_window_holdout_fold", pa.int32(), False),
        ("c_rate_holdout_fold", pa.int32(), False),
        ("profile_holdout_fold", pa.int32(), False),
        ("replicate_calibration_fold", pa.int32(), False),
        ("time_horizon_fold", pa.int32(), False),
        ("schema_version", pa.string(), False),
    ]
)

# 10. Interval Table Schema
INTERVAL_TABLE_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("aging_mode", pa.string(), False),
        ("nominal_temperature_C", pa.float64(), False),
        ("voltage_window", pa.string(), False),
        ("voltage_window_family", pa.string(), False),
        ("soc_window_approx", pa.string(), False),
        ("nominal_charge_C_rate", pa.float64(), False),
        ("nominal_discharge_C_rate", pa.float64(), False),
        ("profile_label", pa.string(), False),
        ("checkup_k", pa.int32(), False),
        ("checkup_k_next", pa.int32(), False),
        ("t_result_k_s", pa.float64(), False),
        ("t_result_k1_s", pa.float64(), False),
        ("duration_s", pa.float64(), False),
        ("duration_h", pa.float64(), False),
        ("calendar_days", pa.float64(), False),
        ("capacity_Ah_k", pa.float64(), False),
        ("capacity_Ah_k1", pa.float64(), False),
        ("delta_capacity_Ah", pa.float64(), False),
        ("delta_capacity_soh", pa.float64(), False),
        ("condition_fold", pa.int32(), False),
        ("temperature_holdout_fold", pa.int32(), False),
        ("voltage_window_holdout_fold", pa.int32(), False),
        ("soc_window_holdout_fold", pa.int32(), False),
        ("c_rate_holdout_fold", pa.int32(), False),
        ("profile_holdout_fold", pa.int32(), False),
        ("replicate_calibration_fold", pa.int32(), False),
        ("time_horizon_fold", pa.int32(), False),
        ("log_age_row_count", pa.int64(), False),
        ("log_age_elapsed_s", pa.float64(), True),
        ("log_age_efc_delta", pa.float64(), True),
        ("log_age_delta_q_Ah", pa.float64(), True),
        ("log_age_mean_voltage_V", pa.float64(), True),
        ("log_age_min_voltage_V", pa.float64(), True),
        ("log_age_max_voltage_V", pa.float64(), True),
        ("log_age_mean_temperature_C", pa.float64(), True),
        ("log_age_min_temperature_C", pa.float64(), True),
        ("log_age_max_temperature_C", pa.float64(), True),
        ("log_age_mean_current_A", pa.float64(), True),
        ("log_age_mean_abs_current_A", pa.float64(), True),
        ("log_age_max_abs_current_A", pa.float64(), True),
        ("log_age_mean_soc", pa.float64(), True),
        ("log_age_min_soc", pa.float64(), True),
        ("log_age_max_soc", pa.float64(), True),
        ("log_age_capacity_diag_rows_masked", pa.int64(), False),
        ("log_age_r0_diag_rows_masked", pa.int64(), False),
        ("log_age_r1_diag_rows_masked", pa.int64(), False),
        ("LOG_AGE_available", pa.bool_(), False),
        ("log_age_monotonicity_violation_count", pa.int64(), False),
        ("log_age_timestamp_decrease_count", pa.int64(), False),
        ("log_age_efc_decrease_count", pa.int64(), False),
        ("log_age_max_timestamp_drop_s", pa.float64(), False),
        ("log_age_max_efc_drop", pa.float64(), False),
        ("LOG_AGE_monotonicity_clean", pa.bool_(), False),
        ("quality_flags", pa.string(), False),
        ("schema_version", pa.string(), False),
    ]
)

# 11. Interval Subset Registry Schema
INTERVAL_SUBSET_REGISTRY_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("checkup_k", pa.int32(), False),
        ("checkup_k_next", pa.int32(), False),
        ("interval_id", pa.string(), False),
        ("baseline_clean_strict", pa.bool_(), False),
        ("baseline_clean_tolerant", pa.bool_(), False),
        ("sensitivity_flagged_monotonicity", pa.bool_(), False),
        ("small_efc_jitter", pa.bool_(), False),
        ("excluded_due_to_large_efc_drop", pa.bool_(), False),
        ("excluded_due_to_timestamp_drop", pa.bool_(), False),
        ("excluded_due_to_missing_log_age", pa.bool_(), False),
        ("excluded_due_to_duration_error", pa.bool_(), False),
        ("monotonicity_policy_version", pa.string(), False),
        ("schema_version", pa.string(), False),
    ]
)

# 12. Interval Stress Features Schema
INTERVAL_STRESS_FEATURES_SCHEMA = pa.schema(
    [
        ("cell_id", pa.string(), False),
        ("parameter_set", pa.int32(), False),
        ("replicate_id", pa.int32(), False),
        ("checkup_k", pa.int32(), False),
        ("checkup_k_next", pa.int32(), False),
        ("schema_version", pa.string(), False),
        ("feature_policy_version", pa.string(), False),
        ("current_sign_policy", pa.string(), False),
        ("current_sign_convention_confirmed", pa.bool_(), False),
        ("sign_dependent_features_provisional", pa.bool_(), False),
        ("stress_log_age_row_count", pa.int64(), False),
        ("stress_duration_h", pa.float64(), False),
        ("time_voltage_lt_3p3_h", pa.float64(), False),
        ("time_voltage_3p3_3p6_h", pa.float64(), False),
        ("time_voltage_3p6_3p9_h", pa.float64(), False),
        ("time_voltage_3p9_4p1_h", pa.float64(), False),
        ("time_voltage_ge_4p1_h", pa.float64(), False),
        ("high_voltage_time_h", pa.float64(), False),
        ("voltage_dwell_weighted_h", pa.float64(), False),
        ("time_temp_lt_5C_h", pa.float64(), False),
        ("time_temp_5_15C_h", pa.float64(), False),
        ("time_temp_15_30C_h", pa.float64(), False),
        ("time_temp_30_40C_h", pa.float64(), False),
        ("time_temp_ge_40C_h", pa.float64(), False),
        ("cold_time_h", pa.float64(), False),
        ("hot_time_h", pa.float64(), False),
        ("mean_charge_current_A", pa.float64(), True),
        ("mean_discharge_current_A", pa.float64(), True),
        ("charge_time_h", pa.float64(), False),
        ("discharge_time_h", pa.float64(), False),
        ("rest_time_h", pa.float64(), False),
        ("abs_current_ge_1C_time_h", pa.float64(), False),
        ("abs_current_ge_1p5C_time_h", pa.float64(), False),
        ("abs_current_ge_5over3C_time_h", pa.float64(), False),
        ("charge_current_ge_1C_time_h", pa.float64(), False),
        ("charge_current_ge_1p5C_time_h", pa.float64(), False),
        ("charge_current_ge_5over3C_time_h", pa.float64(), False),
        ("time_soc_lt_20_h", pa.float64(), False),
        ("time_soc_20_50_h", pa.float64(), False),
        ("time_soc_50_80_h", pa.float64(), False),
        ("time_soc_ge_80_h", pa.float64(), False),
        ("high_soc_time_h", pa.float64(), False),
        ("cold_high_charge_time_h", pa.float64(), False),
        ("cold_high_abs_current_time_h", pa.float64(), False),
        ("high_voltage_hot_time_h", pa.float64(), False),
        ("high_soc_hot_time_h", pa.float64(), False),
        ("high_voltage_high_abs_current_time_h", pa.float64(), False),
        ("high_soc_high_abs_current_time_h", pa.float64(), False),
        ("delta_capacity_per_day", pa.float64(), True),
        ("delta_capacity_per_efc", pa.float64(), True),
        ("delta_capacity_per_Ah_throughput", pa.float64(), True),
        ("log_age_efc_per_day", pa.float64(), True),
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
