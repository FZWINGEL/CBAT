"""Milestone 0.5 capacity baseline runner."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
from pathlib import Path
import random
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "gate5.capacity_baseline.v1"
DEFAULT_HGB_MAX_ITER = 10

TARGETS = (
    "capacity_Ah_k1",
    "delta_capacity_Ah",
    "delta_capacity_per_day_target",
    "delta_capacity_per_efc_target",
)
DIRECT_TARGETS = ("capacity_Ah_k1", "delta_capacity_Ah")
RATE_TARGETS = ("delta_capacity_per_day_target", "delta_capacity_per_efc_target")
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)
SUBSET_COLUMNS = ("baseline_clean_tolerant", "baseline_clean_strict")
MODEL_LEVELS = (
    "L0_persistence",
    "L1_ridge",
    "L2_hist_gradient_boosting",
    "L3_quantile_hist_gradient_boosting",
)
FEATURE_GROUPS = (
    "F0_time_only",
    "F1_state_time",
    "F2_state_exposure",
    "F3_state_nominal",
    "F4_state_log_age_scalar",
    "F5_log_age_histograms",
    "F6_coupled_stress",
    "F7_c_rate_focused",
    "F8_timestamp_weighted_stress",
    "F9_event_segmented_stress",
    "F10_c_rate_v1_1",
    "F11_minimal_cold_current",
    "F12_voltage_cold_current_interactions",
    "F13_sparse_c_rate_context",
    "C_P0_state_time_pulse",
    "C_P1_nominal_pulse",
    "C_P2_log_age_pulse",
    "C_P3_stress_pulse",
    "C_E0_state_time_eis",
    "C_E1_nominal_eis",
    "C_E2_log_age_eis",
    "C_E3_stress_eis",
    "F14_event_aggregate",
    "F15_event_order_aware",
    "F16_event_order_shuffled",
    "F17_event_order_plus_stress",
)
DEFAULT_FEATURE_GROUPS = FEATURE_GROUPS[:5]

DIAGNOSTIC_LEAKAGE_FIELDS = {"cap_aged_est_Ah", "R0_mOhm", "R1_mOhm"}
PULSE_FUTURE_LEAKAGE_FIELDS = {
    "pulse_1s_resistance_k1",
    "delta_pulse_1s_resistance",
    "pulse_10ms_resistance_k1",
    "delta_pulse_10ms_resistance",
}
EIS_FUTURE_LEAKAGE_FIELDS = {
    "eis_z_real_1kHz_k1",
    "eis_z_imag_1kHz_k1",
    "eis_z_abs_1kHz_k1",
    "eis_phase_1kHz_k1",
    "nyquist_re_min_k1",
    "nyquist_re_max_k1",
    "nyquist_im_peak_abs_k1",
    "nyquist_semicircle_width_proxy_k1",
    "delta_eis_z_real_1kHz",
    "delta_eis_z_abs_1kHz",
    "delta_nyquist_semicircle_width_proxy",
    "R0_mOhm_k",
    "R1_mOhm_k",
}
EIS_PRIOR_FEATURES = (
    "eis_z_real_1kHz_k",
    "eis_z_imag_1kHz_k",
    "eis_z_abs_1kHz_k",
    "eis_phase_1kHz_k",
    "nyquist_re_min_k",
    "nyquist_re_max_k",
    "nyquist_im_peak_abs_k",
    "nyquist_semicircle_width_proxy_k",
    "valid_modeling_fraction_k",
)
STRESS_FEATURE_GROUPS = {
    "F5_log_age_histograms",
    "F6_coupled_stress",
    "F7_c_rate_focused",
    "F8_timestamp_weighted_stress",
    "F9_event_segmented_stress",
    "F10_c_rate_v1_1",
    "F11_minimal_cold_current",
    "F12_voltage_cold_current_interactions",
    "F13_sparse_c_rate_context",
    "C_P3_stress_pulse",
    "C_E3_stress_eis",
    "F17_event_order_plus_stress",
}
PULSE_FEATURE_GROUPS = {
    "C_P0_state_time_pulse",
    "C_P1_nominal_pulse",
    "C_P2_log_age_pulse",
    "C_P3_stress_pulse",
}
EIS_FEATURE_GROUPS = {
    "C_E0_state_time_eis",
    "C_E1_nominal_eis",
    "C_E2_log_age_eis",
    "C_E3_stress_eis",
}
SEQUENCE_FEATURE_GROUPS = {
    "F14_event_aggregate",
    "F15_event_order_aware",
    "F16_event_order_shuffled",
    "F17_event_order_plus_stress",
}

LOG_AGE_HISTOGRAM_FEATURES = (
    "time_voltage_lt_3p3_h",
    "time_voltage_3p3_3p6_h",
    "time_voltage_3p6_3p9_h",
    "time_voltage_3p9_4p1_h",
    "time_voltage_ge_4p1_h",
    "high_voltage_time_h",
    "voltage_dwell_weighted_h",
    "time_temp_lt_5C_h",
    "time_temp_5_15C_h",
    "time_temp_15_30C_h",
    "time_temp_30_40C_h",
    "time_temp_ge_40C_h",
    "cold_time_h",
    "hot_time_h",
    "time_soc_lt_20_h",
    "time_soc_20_50_h",
    "time_soc_50_80_h",
    "time_soc_ge_80_h",
    "high_soc_time_h",
    "charge_time_h",
    "discharge_time_h",
    "rest_time_h",
    "abs_current_ge_1C_time_h",
    "abs_current_ge_1p5C_time_h",
    "abs_current_ge_5over3C_time_h",
    "charge_current_ge_1C_time_h",
    "charge_current_ge_1p5C_time_h",
    "charge_current_ge_5over3C_time_h",
    "mean_charge_current_A",
    "mean_discharge_current_A",
    "log_age_efc_per_day",
)

COUPLED_STRESS_FEATURES = (
    "cold_high_charge_time_h",
    "cold_high_abs_current_time_h",
    "high_voltage_hot_time_h",
    "high_soc_hot_time_h",
    "high_voltage_high_abs_current_time_h",
    "high_soc_high_abs_current_time_h",
)

C_RATE_FOCUSED_FEATURES = (
    "cold_time_h",
    "hot_time_h",
    "high_voltage_time_h",
    "charge_time_h",
    "discharge_time_h",
    "rest_time_h",
    "mean_charge_current_A",
    "mean_discharge_current_A",
    "abs_current_ge_1C_time_h",
    "abs_current_ge_1p5C_time_h",
    "abs_current_ge_5over3C_time_h",
    "charge_current_ge_1C_time_h",
    "charge_current_ge_1p5C_time_h",
    "charge_current_ge_5over3C_time_h",
    "cold_high_charge_time_h",
    "cold_high_abs_current_time_h",
    "high_voltage_high_abs_current_time_h",
    "high_soc_high_abs_current_time_h",
    "log_age_efc_per_day",
)

TIMESTAMP_WEIGHTED_STRESS_FEATURES = (
    "stress_observed_duration_h",
    "stress_coverage_fraction",
    "median_log_age_dt_s",
    "max_log_age_gap_s",
    "log_age_gap_count_gt_60s",
    "log_age_gap_count_gt_300s",
    *LOG_AGE_HISTOGRAM_FEATURES,
    *COUPLED_STRESS_FEATURES,
)

EVENT_SEGMENTED_STRESS_FEATURES = (
    "n_charge_events",
    "n_discharge_events",
    "n_rest_events",
    "max_charge_event_h",
    "max_discharge_event_h",
    "max_rest_event_h",
    "max_abs_current_ge_1C_event_h",
    "max_abs_current_ge_1p5C_event_h",
    "max_abs_current_ge_5over3C_event_h",
    "max_cold_high_abs_current_event_h",
    "max_high_voltage_high_abs_current_event_h",
    "max_high_soc_high_abs_current_event_h",
)

C_RATE_V1_1_FEATURES = (
    "stress_coverage_fraction",
    "median_log_age_dt_s",
    "max_log_age_gap_s",
    "abs_current_ge_1C_time_h",
    "abs_current_ge_1p5C_time_h",
    "abs_current_ge_5over3C_time_h",
    "cold_high_abs_current_time_h",
    "high_voltage_high_abs_current_time_h",
    "high_soc_high_abs_current_time_h",
    "max_abs_current_ge_1C_event_h",
    "max_abs_current_ge_1p5C_event_h",
    "max_abs_current_ge_5over3C_event_h",
    "max_cold_high_abs_current_event_h",
    "max_high_voltage_high_abs_current_event_h",
    "max_high_soc_high_abs_current_event_h",
    "log_age_efc_per_day",
)

SEQUENCE_AGGREGATE_FEATURES = (
    "sequence_event_count",
    "sequence_total_event_duration_h",
    "sequence_charge_event_count",
    "sequence_discharge_event_count",
    "sequence_rest_event_count",
    "sequence_unknown_event_count",
    "sequence_charge_duration_h",
    "sequence_discharge_duration_h",
    "sequence_rest_duration_h",
    "sequence_max_charge_duration_h",
    "sequence_max_discharge_duration_h",
    "sequence_max_rest_duration_h",
    "sequence_high_current_event_count",
    "sequence_cold_high_current_event_count",
    "sequence_high_voltage_high_current_event_count",
)

SEQUENCE_ORDER_FEATURES = (
    "sequence_transition_charge_rest",
    "sequence_transition_rest_charge",
    "sequence_transition_discharge_rest",
    "sequence_transition_rest_discharge",
    "sequence_alternation_count",
    "sequence_first_high_current_position",
    "sequence_last_high_current_position",
    "sequence_early_high_current_fraction",
    "sequence_mid_high_current_fraction",
    "sequence_late_high_current_fraction",
    "sequence_longest_high_current_burst_h",
    "sequence_longest_cold_high_current_burst_h",
)

SEQUENCE_SHUFFLED_FEATURES = (
    "sequence_shuffled_transition_charge_rest",
    "sequence_shuffled_transition_rest_charge",
    "sequence_shuffled_transition_discharge_rest",
    "sequence_shuffled_transition_rest_discharge",
    "sequence_shuffled_alternation_count",
    "sequence_shuffled_early_high_current_fraction",
    "sequence_shuffled_mid_high_current_fraction",
    "sequence_shuffled_late_high_current_fraction",
)

F4_LOG_AGE_SCALAR_FEATURES = (
    "capacity_Ah_k",
    "duration_h",
    "calendar_days",
    "checkup_k",
    "log_age_efc_delta",
    "log_age_delta_q_Ah",
    "nominal_temperature_C",
    "nominal_charge_C_rate",
    "nominal_discharge_C_rate",
    "log_age_mean_voltage_V",
    "log_age_min_voltage_V",
    "log_age_max_voltage_V",
    "log_age_mean_temperature_C",
    "log_age_min_temperature_C",
    "log_age_max_temperature_C",
    "log_age_mean_current_A",
    "log_age_mean_abs_current_A",
    "log_age_max_abs_current_A",
    "log_age_mean_soc",
    "log_age_min_soc",
    "log_age_max_soc",
)

MINIMAL_COLD_CURRENT_FEATURES = (
    "capacity_Ah_k",
    "duration_h",
    "calendar_days",
    "checkup_k",
    "log_age_efc_delta",
    "nominal_temperature_C",
    "nominal_charge_C_rate",
    "cold_time_h",
    "abs_current_ge_1p5C_time_h",
    "abs_current_ge_5over3C_time_h",
    "cold_high_abs_current_time_h",
    "max_cold_high_abs_current_event_h",
    "stress_coverage_fraction",
    "max_log_age_gap_s",
)

VOLTAGE_COLD_CURRENT_FEATURES = (
    *MINIMAL_COLD_CURRENT_FEATURES,
    "high_voltage_time_h",
    "high_voltage_high_abs_current_time_h",
    "max_high_voltage_high_abs_current_event_h",
    "time_voltage_ge_4p1_h",
    "time_temp_lt_5C_h",
    "time_temp_5_15C_h",
)

SPARSE_C_RATE_CONTEXT_FEATURES = (
    *VOLTAGE_COLD_CURRENT_FEATURES,
    "n_charge_events",
    "n_discharge_events",
    "max_charge_event_h",
    "max_discharge_event_h",
    "parameter_set_interval_count",
)

NUMERIC_FEATURES: dict[str, tuple[str, ...]] = {
    "F0_time_only": ("duration_h", "calendar_days", "checkup_k"),
    "F1_state_time": ("capacity_Ah_k", "duration_h", "calendar_days", "checkup_k"),
    "F2_state_exposure": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
    ),
    "F3_state_nominal": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
    ),
    "F4_state_log_age_scalar": F4_LOG_AGE_SCALAR_FEATURES,
    "F5_log_age_histograms": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "log_age_mean_voltage_V",
            "log_age_min_voltage_V",
            "log_age_max_voltage_V",
            "log_age_mean_temperature_C",
            "log_age_min_temperature_C",
            "log_age_max_temperature_C",
            "log_age_mean_current_A",
            "log_age_mean_abs_current_A",
            "log_age_max_abs_current_A",
            "log_age_mean_soc",
            "log_age_min_soc",
            "log_age_max_soc",
        ),
        *LOG_AGE_HISTOGRAM_FEATURES,
    ),
    "F6_coupled_stress": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "log_age_mean_voltage_V",
            "log_age_min_voltage_V",
            "log_age_max_voltage_V",
            "log_age_mean_temperature_C",
            "log_age_min_temperature_C",
            "log_age_max_temperature_C",
            "log_age_mean_current_A",
            "log_age_mean_abs_current_A",
            "log_age_max_abs_current_A",
            "log_age_mean_soc",
            "log_age_min_soc",
            "log_age_max_soc",
        ),
        *LOG_AGE_HISTOGRAM_FEATURES,
        *COUPLED_STRESS_FEATURES,
    ),
    "F7_c_rate_focused": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        *C_RATE_FOCUSED_FEATURES,
    ),
    "F8_timestamp_weighted_stress": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "log_age_mean_voltage_V",
            "log_age_min_voltage_V",
            "log_age_max_voltage_V",
            "log_age_mean_temperature_C",
            "log_age_min_temperature_C",
            "log_age_max_temperature_C",
            "log_age_mean_current_A",
            "log_age_mean_abs_current_A",
            "log_age_max_abs_current_A",
            "log_age_mean_soc",
            "log_age_min_soc",
            "log_age_max_soc",
        ),
        *TIMESTAMP_WEIGHTED_STRESS_FEATURES,
    ),
    "F9_event_segmented_stress": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
        ),
        *TIMESTAMP_WEIGHTED_STRESS_FEATURES,
        *EVENT_SEGMENTED_STRESS_FEATURES,
    ),
    "F10_c_rate_v1_1": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        *C_RATE_V1_1_FEATURES,
    ),
    "F11_minimal_cold_current": MINIMAL_COLD_CURRENT_FEATURES,
    "F12_voltage_cold_current_interactions": VOLTAGE_COLD_CURRENT_FEATURES,
    "F13_sparse_c_rate_context": SPARSE_C_RATE_CONTEXT_FEATURES,
    "C_P0_state_time_pulse": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "pulse_1s_resistance_k",
    ),
    "C_P1_nominal_pulse": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "pulse_1s_resistance_k",
    ),
    "C_P2_log_age_pulse": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "log_age_mean_voltage_V",
            "log_age_min_voltage_V",
            "log_age_max_voltage_V",
            "log_age_mean_temperature_C",
            "log_age_min_temperature_C",
            "log_age_max_temperature_C",
            "log_age_mean_current_A",
            "log_age_mean_abs_current_A",
            "log_age_max_abs_current_A",
            "log_age_mean_soc",
            "log_age_min_soc",
            "log_age_max_soc",
        ),
        "pulse_1s_resistance_k",
    ),
    "C_P3_stress_pulse": (
        *(
            "capacity_Ah_k",
            "duration_h",
            "calendar_days",
            "checkup_k",
            "log_age_efc_delta",
            "log_age_delta_q_Ah",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "log_age_mean_voltage_V",
            "log_age_min_voltage_V",
            "log_age_max_voltage_V",
            "log_age_mean_temperature_C",
            "log_age_min_temperature_C",
            "log_age_max_temperature_C",
            "log_age_mean_current_A",
            "log_age_mean_abs_current_A",
            "log_age_max_abs_current_A",
            "log_age_mean_soc",
            "log_age_min_soc",
            "log_age_max_soc",
        ),
        *TIMESTAMP_WEIGHTED_STRESS_FEATURES,
        "pulse_1s_resistance_k",
    ),
    "C_E0_state_time_eis": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        *EIS_PRIOR_FEATURES,
    ),
    "C_E1_nominal_eis": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        *EIS_PRIOR_FEATURES,
    ),
    "C_E2_log_age_eis": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_mean_voltage_V",
        "log_age_min_voltage_V",
        "log_age_max_voltage_V",
        "log_age_mean_temperature_C",
        "log_age_min_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_current_A",
        "log_age_mean_abs_current_A",
        "log_age_max_abs_current_A",
        "log_age_mean_soc",
        "log_age_min_soc",
        "log_age_max_soc",
        *EIS_PRIOR_FEATURES,
    ),
    "C_E3_stress_eis": (
        "capacity_Ah_k",
        "duration_h",
        "calendar_days",
        "checkup_k",
        "log_age_efc_delta",
        "log_age_delta_q_Ah",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "nominal_discharge_C_rate",
        "log_age_mean_voltage_V",
        "log_age_min_voltage_V",
        "log_age_max_voltage_V",
        "log_age_mean_temperature_C",
        "log_age_min_temperature_C",
        "log_age_max_temperature_C",
        "log_age_mean_current_A",
        "log_age_mean_abs_current_A",
        "log_age_max_abs_current_A",
        "log_age_mean_soc",
        "log_age_min_soc",
        "log_age_max_soc",
        *TIMESTAMP_WEIGHTED_STRESS_FEATURES,
        *EIS_PRIOR_FEATURES,
    ),
    "F14_event_aggregate": (
        *F4_LOG_AGE_SCALAR_FEATURES,
        *SEQUENCE_AGGREGATE_FEATURES,
    ),
    "F15_event_order_aware": (
        *F4_LOG_AGE_SCALAR_FEATURES,
        *SEQUENCE_AGGREGATE_FEATURES,
        *SEQUENCE_ORDER_FEATURES,
    ),
    "F16_event_order_shuffled": (
        *F4_LOG_AGE_SCALAR_FEATURES,
        *SEQUENCE_AGGREGATE_FEATURES,
        *SEQUENCE_SHUFFLED_FEATURES,
    ),
    "F17_event_order_plus_stress": (
        *F4_LOG_AGE_SCALAR_FEATURES,
        *TIMESTAMP_WEIGHTED_STRESS_FEATURES,
        *SEQUENCE_AGGREGATE_FEATURES,
        *SEQUENCE_ORDER_FEATURES,
    ),
}

CATEGORICAL_FEATURES: dict[str, tuple[str, ...]] = {
    "F0_time_only": (),
    "F1_state_time": (),
    "F2_state_exposure": (),
    "F3_state_nominal": ("aging_mode", "voltage_window_family"),
    "F4_state_log_age_scalar": ("aging_mode", "voltage_window_family"),
    "F5_log_age_histograms": ("aging_mode", "voltage_window_family"),
    "F6_coupled_stress": ("aging_mode", "voltage_window_family"),
    "F7_c_rate_focused": ("aging_mode", "voltage_window_family"),
    "F8_timestamp_weighted_stress": ("aging_mode", "voltage_window_family"),
    "F9_event_segmented_stress": ("aging_mode", "voltage_window_family"),
    "F10_c_rate_v1_1": ("aging_mode", "voltage_window_family"),
    "F11_minimal_cold_current": ("voltage_window_family",),
    "F12_voltage_cold_current_interactions": ("voltage_window_family",),
    "F13_sparse_c_rate_context": (
        "voltage_window_family",
        "parameter_set_interval_count_bucket",
    ),
    "C_P0_state_time_pulse": (),
    "C_P1_nominal_pulse": ("aging_mode", "voltage_window_family"),
    "C_P2_log_age_pulse": ("aging_mode", "voltage_window_family"),
    "C_P3_stress_pulse": ("aging_mode", "voltage_window_family"),
    "C_E0_state_time_eis": (),
    "C_E1_nominal_eis": ("aging_mode", "voltage_window_family"),
    "C_E2_log_age_eis": ("aging_mode", "voltage_window_family"),
    "C_E3_stress_eis": ("aging_mode", "voltage_window_family"),
    "F14_event_aggregate": ("aging_mode", "voltage_window_family"),
    "F15_event_order_aware": ("aging_mode", "voltage_window_family"),
    "F16_event_order_shuffled": ("aging_mode", "voltage_window_family"),
    "F17_event_order_plus_stress": ("aging_mode", "voltage_window_family"),
}

BASELINE_PREDICTION_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("subset_name", pa.string()),
        ("run_scope", pa.string()),
        ("split_name", pa.string()),
        ("heldout_fold", pa.int32()),
        ("model_level", pa.string()),
        ("feature_group", pa.string()),
        ("target", pa.string()),
        ("cell_id", pa.string()),
        ("parameter_set", pa.int32()),
        ("replicate_id", pa.int32()),
        ("checkup_k", pa.int32()),
        ("checkup_k_next", pa.int32()),
        ("sensitivity_flagged_monotonicity", pa.bool_()),
        ("y_true", pa.float64()),
        ("y_pred", pa.float64()),
        ("y_pred_q10", pa.float64()),
        ("y_pred_q50", pa.float64()),
        ("y_pred_q90", pa.float64()),
    ]
)


@dataclass(frozen=True)
class FeatureEncoder:
    """Train-fold-derived feature encoder with numeric imputation and one-hot categories."""

    feature_group: str
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    numeric_impute_values: dict[str, float]
    numeric_scale_values: dict[str, float]
    categorical_values: dict[str, tuple[str, ...]]
    output_columns: tuple[str, ...]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_group: str) -> "FeatureEncoder":
        if feature_group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown feature group: {feature_group}")
        numeric_columns = NUMERIC_FEATURES[feature_group]
        categorical_columns = CATEGORICAL_FEATURES[feature_group]
        leakage = set(numeric_columns) | set(categorical_columns)
        leakage &= DIAGNOSTIC_LEAKAGE_FIELDS
        if leakage:
            raise ValueError(f"Feature group {feature_group} includes leakage fields: {sorted(leakage)}")
        pulse_leakage = (set(numeric_columns) | set(categorical_columns)) & PULSE_FUTURE_LEAKAGE_FIELDS
        if pulse_leakage:
            raise ValueError(
                f"Feature group {feature_group} includes future PULSE fields: {sorted(pulse_leakage)}"
            )
        eis_leakage = (set(numeric_columns) | set(categorical_columns)) & EIS_FUTURE_LEAKAGE_FIELDS
        if eis_leakage:
            raise ValueError(
                f"Feature group {feature_group} includes future EIS fields: {sorted(eis_leakage)}"
            )

        impute_values: dict[str, float] = {}
        scale_values: dict[str, float] = {}
        for column in numeric_columns:
            values = [_as_float(row.get(column)) for row in rows]
            finite_values = [value for value in values if math.isfinite(value)]
            mean = sum(finite_values) / len(finite_values) if finite_values else 0.0
            impute_values[column] = mean
            variance = (
                sum((value - mean) ** 2 for value in finite_values) / len(finite_values)
                if finite_values
                else 0.0
            )
            std = math.sqrt(variance)
            scale_values[column] = std if std > 0 else 1.0

        categorical_values: dict[str, tuple[str, ...]] = {}
        output_columns = list(numeric_columns)
        for column in categorical_columns:
            values = tuple(sorted({_category(row.get(column)) for row in rows}))
            categorical_values[column] = values
            output_columns.extend(f"{column}={value}" for value in values)

        return cls(
            feature_group=feature_group,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            numeric_impute_values=impute_values,
            numeric_scale_values=scale_values,
            categorical_values=categorical_values,
            output_columns=tuple(output_columns),
        )

    def transform(
        self,
        rows: list[dict[str, Any]],
        *,
        standardize_numeric: bool = False,
    ) -> list[list[float]]:
        matrix: list[list[float]] = []
        for row in rows:
            values: list[float] = []
            for column in self.numeric_columns:
                value = _as_float(row.get(column))
                numeric = value if math.isfinite(value) else self.numeric_impute_values[column]
                if standardize_numeric:
                    numeric = (
                        numeric - self.numeric_impute_values[column]
                    ) / self.numeric_scale_values[column]
                values.append(numeric)
            for column in self.categorical_columns:
                observed = _category(row.get(column))
                values.extend(
                    1.0 if observed == category else 0.0
                    for category in self.categorical_values[column]
                )
            matrix.append(values)
        return matrix


def run_capacity_baselines(
    interval_table_path: Path,
    interval_subsets_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    stress_features_path: Path | None = None,
    pulse_targets_path: Path | None = None,
    eis_targets_path: Path | None = None,
    sequence_features_path: Path | None = None,
    report_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
    bias_correction: bool = False,
) -> dict[str, Any]:
    """Run the L0-L3 capacity baseline ladder and write report/predictions."""
    if hgb_max_iter <= 0:
        raise ValueError("hgb_max_iter must be positive.")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, "model level")
    selected_feature_groups = _normalize_selection(
        feature_groups,
        FEATURE_GROUPS,
        "feature group",
        default=DEFAULT_FEATURE_GROUPS,
    )
    selected_targets = _normalize_selection(targets, TARGETS, "target", default=DIRECT_TARGETS)
    selected_split_views = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    if STRESS_FEATURE_GROUPS & set(selected_feature_groups) and stress_features_path is None:
        raise ValueError(
            "Stress feature groups F5-F13 require --stress-features pointing to "
            "an interval stress-feature sidecar parquet."
        )
    if PULSE_FEATURE_GROUPS & set(selected_feature_groups) and pulse_targets_path is None:
        raise ValueError(
            "PULSE capacity feature groups require --pulse-targets pointing to "
            "a pulse target table parquet."
        )
    if EIS_FEATURE_GROUPS & set(selected_feature_groups) and eis_targets_path is None:
        raise ValueError(
            "EIS capacity feature groups require --eis-targets pointing to "
            "an EIS target table parquet."
        )
    if SEQUENCE_FEATURE_GROUPS & set(selected_feature_groups) and sequence_features_path is None:
        raise ValueError(
            "Sequence-value feature groups F14-F17 require --sequence-features pointing "
            "to an interval sequence-feature sidecar parquet."
        )
    _preflight_model_dependencies(selected_models)

    all_rows, subset_rows = load_baseline_rows(
        interval_table_path,
        interval_subsets_path,
        subset,
        stress_features_path=stress_features_path,
        pulse_targets_path=pulse_targets_path,
        eis_targets_path=eis_targets_path,
        sequence_features_path=sequence_features_path,
    )
    sensitivity_rows = [
        row for row in subset_rows if not bool(row["sensitivity_flagged_monotonicity"])
    ]
    if not sensitivity_rows:
        raise ValueError("Sensitivity subset is empty after excluding monotonicity-flagged rows.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for run_scope, rows in (
        ("primary", subset_rows),
        ("sensitivity_excluding_monotonicity", sensitivity_rows),
    ):
        for split_name in selected_split_views:
            for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
                assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
                for model_level in selected_models:
                    model_feature_groups = (
                        ("persistence",)
                        if model_level == "L0_persistence"
                        else tuple(selected_feature_groups)
                    )
                    for feature_group in model_feature_groups:
                        for target in selected_targets:
                            fold_predictions = predict_capacity_target(
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                                test_rows=test_rows,
                                target=target,
                                seed=seed,
                                hgb_max_iter=hgb_max_iter,
                            )
                            metric = compute_metrics(
                                test_rows,
                                fold_predictions,
                                target=target,
                                subset_name=subset,
                                run_scope=run_scope,
                                split_name=split_name,
                                heldout_fold=heldout_fold,
                                model_level=model_level,
                                feature_group=feature_group,
                                train_rows=train_rows,
                            )
                            metrics.append(metric)
                            predictions.extend(
                                _prediction_rows(
                                    test_rows,
                                    fold_predictions,
                                    subset_name=subset,
                                    run_scope=run_scope,
                                    split_name=split_name,
                                    heldout_fold=heldout_fold,
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    target=target,
                                )
                            )
                            if bias_correction and model_level != "L0_persistence":
                                corrected = _bias_corrected_predictions(
                                    model_level=model_level,
                                    feature_group=feature_group,
                                    train_rows=train_rows,
                                    test_rows=test_rows,
                                    target=target,
                                    seed=seed,
                                    hgb_max_iter=hgb_max_iter,
                                    test_predictions=fold_predictions,
                                )
                                corrected_scope = f"{run_scope}_bias_corrected"
                                metrics.append(
                                    compute_metrics(
                                        test_rows,
                                        corrected,
                                        target=target,
                                        subset_name=subset,
                                        run_scope=corrected_scope,
                                        split_name=split_name,
                                        heldout_fold=heldout_fold,
                                        model_level=model_level,
                                        feature_group=feature_group,
                                        train_rows=train_rows,
                                    )
                                )
                                predictions.extend(
                                    _prediction_rows(
                                        test_rows,
                                        corrected,
                                        subset_name=subset,
                                        run_scope=corrected_scope,
                                        split_name=split_name,
                                        heldout_fold=heldout_fold,
                                        model_level=model_level,
                                        feature_group=feature_group,
                                        target=target,
                                    )
                                )

    if not metrics:
        raise ValueError("No baseline metrics were generated.")

    resolved_report_dir = report_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"interval_table_path": str(interval_table_path).encode(),
                b"interval_subsets_path": str(interval_subsets_path).encode(),
            }
        ),
        predictions_out_path,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "stress_features": str(stress_features_path) if stress_features_path else None,
            "pulse_targets": str(pulse_targets_path) if pulse_targets_path else None,
            "eis_targets": str(eis_targets_path) if eis_targets_path else None,
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(resolved_report_dir),
        },
        "seed": seed,
        "hgb_max_iter": hgb_max_iter,
        "numeric_standardization": "train_fold_mean_std",
        "numeric_standardization_applies_to": ["L1_ridge"],
        "bias_correction": (
            "train_fold_group_mean_residual" if bias_correction else "none"
        ),
        "subset": subset,
        "targets": selected_targets,
        "model_levels": selected_models,
        "feature_groups": selected_feature_groups,
        "split_views": selected_split_views,
        "row_counts": _row_counts(all_rows, subset_rows, sensitivity_rows),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_capacity_report_artifacts(report, resolved_report_dir)
    return report


def render_capacity_report_artifacts(report: dict[str, Any], report_dir: Path) -> None:
    """Render human-readable baseline summaries from the metrics JSON."""
    report_dir.mkdir(parents=True, exist_ok=True)
    cards_dir = report_dir / "evaluation_cards"
    plots_dir = report_dir / "plots"
    cards_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    metrics = list(report["metrics"])
    leaderboard_rows = _leaderboard_rows(metrics)
    _write_csv(report_dir / "leaderboard.csv", leaderboard_rows)
    _write_csv(plots_dir / "mae_by_model_and_feature.csv", leaderboard_rows)
    _write_csv(plots_dir / "worst_condition_errors.csv", _worst_condition_rows(metrics))
    _write_csv(plots_dir / "strict_vs_tolerant_delta.csv", _sensitivity_delta_rows(metrics))
    _write_csv(plots_dir / "rate_target_vs_direct_delta.csv", _rate_target_comparison_rows(leaderboard_rows))
    _write_csv(plots_dir / "bias_correction_by_split.csv", _bias_correction_rows(leaderboard_rows))
    _write_csv(plots_dir / "c_rate_bias_before_after.csv", _c_rate_bias_rows(metrics))
    _write_evaluation_cards(metrics, cards_dir, report)
    _write_baseline_summary(report, leaderboard_rows, report_dir / "baseline_summary.md")
    render_capacity_diagnostics(report, report_dir)


def diagnose_capacity_report(
    report_path: Path,
    out_dir: Path,
    reference_report_path: Path | None = None,
) -> dict[str, Any]:
    """Render Milestone 0.5b diagnostics from an existing baseline report."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    reference_report = (
        json.loads(reference_report_path.read_text(encoding="utf-8"))
        if reference_report_path is not None
        else None
    )
    render_capacity_diagnostics(report, out_dir, reference_report=reference_report)
    return report


def diagnose_stress_feature_report(
    report_path: Path,
    baseline_report_path: Path,
    l0_reference_report_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Render Milestone 0.6 stress-feature diagnostics against F4 and L0 baselines."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    baseline_report = json.loads(baseline_report_path.read_text(encoding="utf-8"))
    l0_reference_report = json.loads(l0_reference_report_path.read_text(encoding="utf-8"))

    render_capacity_diagnostics(report, out_dir, reference_report=l0_reference_report)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    report_leaderboard = _leaderboard_rows(list(report["metrics"]))
    baseline_leaderboard = _leaderboard_rows(list(baseline_report["metrics"]))
    l0_leaderboard = _leaderboard_rows(list(l0_reference_report["metrics"]))
    report_predictions = _load_prediction_rows(report)
    baseline_predictions = _load_prediction_rows(baseline_report)
    l0_predictions = _load_prediction_rows(l0_reference_report)
    metadata = _condition_metadata_by_parameter_set(report)

    stress_gain_rows = _stress_feature_gain_rows(
        report_leaderboard, baseline_leaderboard, l0_leaderboard
    )
    c_rate_rows = _c_rate_stress_feature_error_rows(
        stress_gain_rows,
        report_predictions,
        baseline_predictions,
        l0_predictions,
        metadata,
    )
    claim_rows = _stress_feature_claim_readiness_rows(stress_gain_rows, c_rate_rows)

    _write_csv(plots_dir / "stress_feature_gain_by_split.csv", stress_gain_rows)
    _write_csv(plots_dir / "c_rate_stress_feature_errors.csv", c_rate_rows)
    _write_csv(plots_dir / "stress_feature_claim_readiness.csv", claim_rows)
    _write_stress_feature_diagnostics_md(
        report,
        baseline_report,
        l0_reference_report,
        stress_gain_rows,
        c_rate_rows,
        claim_rows,
        out_dir / "stress_feature_diagnostics.md",
    )
    return report


def diagnose_target_consistency_report(
    report_path: Path,
    predictions_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Render target-consistency and C-rate failure diagnostics."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    prediction_rows = pq.read_table(predictions_path).to_pylist()
    interval_by_key = _interval_rows_by_key(report)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    target_metric_rows = _target_consistency_metric_rows(prediction_rows, interval_by_key)
    derived_delta_rows = [
        row for row in target_metric_rows if row["target_path"] == "derived_delta_from_capacity"
    ]
    derived_capacity_rows = [
        row for row in target_metric_rows if row["target_path"] == "derived_capacity_from_delta"
    ]
    direct_vs_derived_rows = _direct_vs_derived_target_rows(target_metric_rows)
    c_rate_residual_rows = _c_rate_residual_rows(report, prediction_rows, interval_by_key)
    stress_gain_rows = _stress_ablation_gain_rows(_leaderboard_rows(list(report["metrics"])))
    c_rate_gain_rows = [
        row for row in stress_gain_rows if row["split_name"] == "c_rate_holdout_fold"
    ]

    _write_csv(plots_dir / "derived_delta_from_capacity_metrics.csv", derived_delta_rows)
    _write_csv(plots_dir / "derived_capacity_from_delta_metrics.csv", derived_capacity_rows)
    _write_csv(plots_dir / "direct_vs_derived_target_metrics.csv", direct_vs_derived_rows)
    _write_csv(plots_dir / "c_rate_residuals_by_parameter_set.csv", c_rate_residual_rows)
    _write_csv(
        plots_dir / "c_rate_residuals_by_temperature.csv",
        _residual_group_rows(c_rate_residual_rows, "nominal_temperature_C"),
    )
    _write_csv(
        plots_dir / "c_rate_residuals_by_voltage_window.csv",
        _residual_group_rows(c_rate_residual_rows, "voltage_window_family"),
    )
    _write_csv(
        plots_dir / "c_rate_residuals_by_capacity_bin.csv",
        _residual_group_rows(c_rate_residual_rows, "capacity_Ah_k_bin"),
    )
    _write_csv(
        plots_dir / "c_rate_residuals_by_interval_count.csv",
        _residual_group_rows(c_rate_residual_rows, "interval_count_bucket"),
    )
    _write_csv(
        plots_dir / "c_rate_signed_error_summary.csv",
        _residual_group_rows(c_rate_residual_rows, "target"),
    )
    _write_csv(plots_dir / "f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv", stress_gain_rows)
    _write_csv(plots_dir / "c_rate_gain_by_feature_group.csv", c_rate_gain_rows)
    _write_target_consistency_md(
        report,
        target_metric_rows,
        direct_vs_derived_rows,
        out_dir / "target_consistency_diagnostics.md",
    )
    _write_c_rate_residual_analysis_md(
        c_rate_residual_rows,
        out_dir / "c_rate_residual_analysis.md",
    )
    _write_stress_ablation_summary_md(
        stress_gain_rows,
        out_dir / "stress_feature_ablation_summary.md",
    )
    return report


def compare_prior_pulse_capacity_reports(
    baseline_report_path: Path,
    prior_pulse_report_path: Path,
    out_dir: Path,
    *,
    seed: int = 42,
    bootstrap_resamples: int = 1000,
) -> dict[str, Any]:
    """Compare F4 capacity baselines against prior-PULSE feature groups."""
    _assert_pulse_feature_groups_are_leakage_safe()
    baseline_report = json.loads(baseline_report_path.read_text(encoding="utf-8"))
    prior_report = json.loads(prior_pulse_report_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    prior_predictions = _load_prediction_rows(prior_report)
    baseline_predictions = _load_prediction_rows(baseline_report)
    metadata = _condition_metadata_by_parameter_set(prior_report)
    best_prior = _best_prior_pulse_groups(prior_report)
    paired_rows = _paired_prior_pulse_condition_gain_rows(
        prior_predictions,
        best_prior,
        metadata,
    )
    split_summary = _prior_pulse_split_gain_summary(paired_rows, bootstrap_resamples, seed)
    c_rate_summary = [row for row in split_summary if row["split_name"] == "c_rate_holdout_fold"]
    coverage_summary = _prior_pulse_coverage_summary(
        baseline_report,
        prior_report,
        baseline_predictions,
        prior_predictions,
    )
    claim_rows = _prior_pulse_predictive_claim_rows(split_summary, coverage_summary)

    _write_csv(out_dir / "paired_condition_gain.csv", paired_rows)
    _write_csv(out_dir / "split_level_gain_summary.csv", split_summary)
    _write_csv(out_dir / "c_rate_gain_summary.csv", c_rate_summary)
    _write_csv(out_dir / "coverage_effect_summary.csv", coverage_summary)
    _write_csv(plots_dir / "paired_condition_gain.csv", paired_rows)
    _write_csv(plots_dir / "split_level_gain_summary.csv", split_summary)
    _write_csv(plots_dir / "c_rate_gain_summary.csv", c_rate_summary)
    _write_csv(plots_dir / "coverage_effect_summary.csv", coverage_summary)
    _write_prior_pulse_claim_readiness_md(
        claim_rows,
        split_summary,
        coverage_summary,
        out_dir / "prior_pulse_predictive_claim_readiness.md",
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "baseline_report": str(baseline_report_path),
            "prior_pulse_report": str(prior_pulse_report_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "paired_condition_gain": str(out_dir / "paired_condition_gain.csv"),
            "split_level_gain_summary": str(out_dir / "split_level_gain_summary.csv"),
            "coverage_effect_summary": str(out_dir / "coverage_effect_summary.csv"),
            "claim_readiness": str(out_dir / "prior_pulse_predictive_claim_readiness.md"),
        },
        "bootstrap_resamples": bootstrap_resamples,
        "seed": seed,
        "best_prior_pulse_groups": [
            {
                "target": target,
                "split_name": split_name,
                "feature_group": feature_group,
            }
            for (target, split_name), feature_group in sorted(best_prior.items())
        ],
        "row_counts": {
            "paired_condition_gain_rows": len(paired_rows),
            "split_summary_rows": len(split_summary),
            "coverage_summary_rows": len(coverage_summary),
        },
        "claim_rows": claim_rows,
    }
    (out_dir / "prior_pulse_predictive_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def compare_prior_pulse_vs_best_nonpulse_reports(
    nonpulse_report_paths: list[Path],
    prior_pulse_report_path: Path,
    out_dir: Path,
    *,
    seed: int = 42,
    bootstrap_resamples: int = 1000,
) -> dict[str, Any]:
    """Compare prior-PULSE feature groups against strongest supplied non-PULSE reports."""
    _assert_pulse_feature_groups_are_leakage_safe()
    if not nonpulse_report_paths:
        raise ValueError("At least one non-PULSE report is required.")
    nonpulse_reports = [
        json.loads(path.read_text(encoding="utf-8")) for path in nonpulse_report_paths
    ]
    prior_report = json.loads(prior_pulse_report_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    prior_predictions = _load_prediction_rows(prior_report)
    covered_keys = _all_primary_prediction_keys(prior_predictions)
    metadata = _condition_metadata_by_parameter_set(prior_report)
    prior_condition_rows = _selection_condition_mae_rows(
        prior_predictions,
        allowed_feature_groups=PULSE_FEATURE_GROUPS,
        covered_keys=covered_keys,
        source_report=Path(prior_report["outputs"]["report"]).name,
    )
    nonpulse_condition_rows: list[dict[str, Any]] = []
    for report_path, report in zip(nonpulse_report_paths, nonpulse_reports, strict=True):
        nonpulse_condition_rows.extend(
            _selection_condition_mae_rows(
                _load_prediction_rows(report),
                allowed_feature_groups=None,
                covered_keys=covered_keys,
                source_report=report_path.name,
                exclude_feature_groups=PULSE_FEATURE_GROUPS,
            )
        )
    best_prior = _best_selection_by_target_split(prior_condition_rows)
    best_nonpulse = _best_selection_by_target_split(nonpulse_condition_rows)
    paired_rows = _paired_best_nonpulse_gain_rows(
        prior_condition_rows,
        nonpulse_condition_rows,
        best_prior,
        best_nonpulse,
        metadata,
    )
    split_summary = _prior_pulse_split_gain_summary(paired_rows, bootstrap_resamples, seed)
    c_rate_summary = [row for row in split_summary if row["split_name"] == "c_rate_holdout_fold"]
    claim_rows = _prior_pulse_vs_best_nonpulse_claim_rows(split_summary)

    _write_csv(out_dir / "paired_gain_vs_best_nonpulse.csv", paired_rows)
    _write_csv(out_dir / "split_level_gain_vs_best_nonpulse.csv", split_summary)
    _write_csv(out_dir / "c_rate_gain_vs_best_nonpulse.csv", c_rate_summary)
    _write_csv(out_dir / "bootstrap_gain_vs_best_nonpulse.csv", split_summary)
    _write_csv(plots_dir / "paired_gain_vs_best_nonpulse.csv", paired_rows)
    _write_csv(plots_dir / "split_level_gain_vs_best_nonpulse.csv", split_summary)
    _write_csv(plots_dir / "c_rate_gain_vs_best_nonpulse.csv", c_rate_summary)
    _write_csv(plots_dir / "bootstrap_gain_vs_best_nonpulse.csv", split_summary)
    _write_prior_pulse_vs_best_nonpulse_md(
        claim_rows,
        split_summary,
        out_dir / "prior_pulse_vs_best_nonpulse_claim_readiness.md",
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "nonpulse_reports": [str(path) for path in nonpulse_report_paths],
            "prior_pulse_report": str(prior_pulse_report_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "paired_gain_vs_best_nonpulse": str(out_dir / "paired_gain_vs_best_nonpulse.csv"),
            "split_level_gain_vs_best_nonpulse": str(out_dir / "split_level_gain_vs_best_nonpulse.csv"),
            "claim_readiness": str(out_dir / "prior_pulse_vs_best_nonpulse_claim_readiness.md"),
        },
        "bootstrap_resamples": bootstrap_resamples,
        "seed": seed,
        "best_prior_pulse_groups": _selection_summary_rows(best_prior),
        "best_nonpulse_groups": _selection_summary_rows(best_nonpulse),
        "row_counts": {
            "nonpulse_condition_rows": len(nonpulse_condition_rows),
            "prior_pulse_condition_rows": len(prior_condition_rows),
            "paired_gain_rows": len(paired_rows),
            "split_summary_rows": len(split_summary),
        },
        "claim_rows": claim_rows,
    }
    (out_dir / "prior_pulse_vs_best_nonpulse_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def render_capacity_diagnostics(
    report: dict[str, Any],
    report_dir: Path,
    reference_report: dict[str, Any] | None = None,
) -> None:
    """Render diagnostic tables and a narrative memo for a capacity report."""
    report_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = report_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_rows = _leaderboard_rows(list(report["metrics"]))
    prediction_rows = _load_prediction_rows(report)
    reference_leaderboard_rows = (
        _leaderboard_rows(list(reference_report["metrics"]))
        if reference_report is not None
        else []
    )
    reference_prediction_rows = (
        _load_prediction_rows(reference_report) if reference_report is not None else []
    )
    metadata = _condition_metadata_by_parameter_set(report)
    best_rows = _best_by_target_split_rows(
        leaderboard_rows,
        prediction_rows,
        reference_leaderboard_rows=reference_leaderboard_rows,
    )
    feature_gain_rows = _feature_gain_rows(leaderboard_rows)
    c_rate_rows = _c_rate_holdout_error_rows(
        leaderboard_rows,
        prediction_rows,
        metadata,
        reference_leaderboard_rows=reference_leaderboard_rows,
        reference_prediction_rows=reference_prediction_rows,
    )
    c_rate_grouped_rows = _c_rate_grouped_summary_rows(c_rate_rows)

    _write_csv(plots_dir / "best_by_target_split.csv", best_rows)
    _write_csv(plots_dir / "feature_gain_by_split.csv", feature_gain_rows)
    _write_csv(plots_dir / "c_rate_holdout_errors.csv", c_rate_rows)
    _write_csv(plots_dir / "c_rate_holdout_by_condition.csv", c_rate_rows)
    _write_csv(plots_dir / "c_rate_grouped_summaries.csv", c_rate_grouped_rows)
    _write_baseline_diagnostics_md(
        report,
        reference_report,
        best_rows,
        feature_gain_rows,
        _sensitivity_delta_rows(list(report["metrics"])),
        c_rate_rows,
        c_rate_grouped_rows,
        report_dir / "baseline_diagnostics.md",
    )
    _write_c_rate_error_analysis_md(
        c_rate_rows,
        c_rate_grouped_rows,
        report_dir / "c_rate_holdout_error_analysis.md",
    )
    _write_claim_readiness_md(
        report,
        best_rows,
        feature_gain_rows,
        _sensitivity_delta_rows(list(report["metrics"])),
        c_rate_rows,
        leaderboard_rows,
        report_dir / "claim_readiness.md",
    )


def load_baseline_rows(
    interval_table_path: Path,
    interval_subsets_path: Path,
    subset: str,
    stress_features_path: Path | None = None,
    pulse_targets_path: Path | None = None,
    eis_targets_path: Path | None = None,
    sequence_features_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load and join interval rows with baseline subset flags."""
    if subset not in SUBSET_COLUMNS:
        raise ValueError(f"Unknown subset '{subset}'. Expected one of {', '.join(SUBSET_COLUMNS)}.")
    if not interval_table_path.exists():
        raise FileNotFoundError(f"Interval table not found: {interval_table_path}")
    if not interval_subsets_path.exists():
        raise FileNotFoundError(f"Interval subset registry not found: {interval_subsets_path}")

    interval_rows = pq.read_table(interval_table_path).to_pylist()
    subset_rows = pq.read_table(interval_subsets_path).to_pylist()
    if len(interval_rows) != len(subset_rows):
        raise ValueError(
            "Interval table and interval subset registry row counts differ: "
            f"{len(interval_rows)} vs {len(subset_rows)}."
        )
    stress_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    if stress_features_path is not None:
        if not stress_features_path.exists():
            raise FileNotFoundError(f"Stress-feature table not found: {stress_features_path}")
        stress_rows = pq.read_table(stress_features_path).to_pylist()
        for row in stress_rows:
            key = _interval_key(row)
            if key in stress_by_key:
                raise ValueError(f"Duplicate stress-feature interval key: {key}")
            stress_by_key[key] = row
    pulse_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    if pulse_targets_path is not None:
        if not pulse_targets_path.exists():
            raise FileNotFoundError(f"PULSE target table not found: {pulse_targets_path}")
        pulse_rows = pq.read_table(pulse_targets_path).to_pylist()
        for row in pulse_rows:
            key = _interval_key(row)
            if key in pulse_by_key:
                raise ValueError(f"Duplicate PULSE target interval key: {key}")
            pulse_by_key[key] = row
    eis_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    if eis_targets_path is not None:
        if not eis_targets_path.exists():
            raise FileNotFoundError(f"EIS target table not found: {eis_targets_path}")
        eis_rows = pq.read_table(eis_targets_path).to_pylist()
        for row in eis_rows:
            key = _interval_key(row)
            if key in eis_by_key:
                raise ValueError(f"Duplicate EIS target interval key: {key}")
            eis_by_key[key] = row
    sequence_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    if sequence_features_path is not None:
        if not sequence_features_path.exists():
            raise FileNotFoundError(f"Sequence-feature table not found: {sequence_features_path}")
        sequence_rows = pq.read_table(sequence_features_path).to_pylist()
        for row in sequence_rows:
            key = _interval_key(row)
            if key in sequence_by_key:
                raise ValueError(f"Duplicate sequence-feature interval key: {key}")
            sequence_by_key[key] = row

    subset_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in subset_rows:
        key = _interval_key(row)
        if key in subset_by_key:
            raise ValueError(f"Duplicate interval subset key: {key}")
        subset_by_key[key] = row

    merged_rows: list[dict[str, Any]] = []
    for interval_row in interval_rows:
        key = _interval_key(interval_row)
        subset_row = subset_by_key.get(key)
        if subset_row is None:
            raise ValueError(f"Interval subset registry is missing interval key: {key}")
        merged = dict(interval_row)
        for column, value in subset_row.items():
            if column not in {"cell_id", "parameter_set", "replicate_id", "checkup_k", "checkup_k_next"}:
                merged[column] = value
        if stress_features_path is not None:
            stress_row = stress_by_key.get(key)
            if stress_row is None:
                raise ValueError(f"Stress-feature table is missing interval key: {key}")
            for column, value in stress_row.items():
                if column in {
                    "cell_id",
                    "parameter_set",
                    "replicate_id",
                    "checkup_k",
                    "checkup_k_next",
                    "schema_version",
                }:
                    continue
                merged[column] = value
        if pulse_targets_path is not None:
            pulse_row = pulse_by_key.get(key)
            if pulse_row is None:
                continue
            for column, value in pulse_row.items():
                if column in {
                    "cell_id",
                    "parameter_set",
                    "replicate_id",
                    "checkup_k",
                    "checkup_k_next",
                    "schema_version",
                }:
                    continue
                merged[column] = value
        if eis_targets_path is not None:
            eis_row = eis_by_key.get(key)
            if eis_row is None:
                continue
            for column, value in eis_row.items():
                if column in {
                    "cell_id",
                    "parameter_set",
                    "replicate_id",
                    "checkup_k",
                    "checkup_k_next",
                    "schema_version",
                }:
                    continue
                merged[column] = value
        if sequence_features_path is not None:
            sequence_row = sequence_by_key.get(key)
            if sequence_row is None:
                raise ValueError(f"Sequence-feature table is missing interval key: {key}")
            for column, value in sequence_row.items():
                if column in {
                    "cell_id",
                    "parameter_set",
                    "replicate_id",
                    "checkup_k",
                    "checkup_k_next",
                    "schema_version",
                }:
                    continue
                merged[column] = value
        merged_rows.append(merged)

    parameter_set_counts = Counter(int(row["parameter_set"]) for row in merged_rows)
    for row in merged_rows:
        count = parameter_set_counts[int(row["parameter_set"])]
        row["parameter_set_interval_count"] = count
        row["parameter_set_interval_count_bucket"] = _interval_count_bucket(count)

    selected_rows = [row for row in merged_rows if bool(row[subset])]
    if pulse_targets_path is not None:
        selected_rows = [
            row for row in selected_rows if math.isfinite(_as_float(row.get("pulse_1s_resistance_k")))
        ]
    if eis_targets_path is not None:
        selected_rows = [
            row for row in selected_rows if math.isfinite(_as_float(row.get("eis_z_abs_1kHz_k")))
        ]
    if not selected_rows:
        raise ValueError(f"Requested subset '{subset}' has zero rows.")
    return merged_rows, selected_rows


def iter_split_instances(
    rows: list[dict[str, Any]],
    split_name: str,
) -> list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]]:
    """Return leave-fold-out train/test splits for one split column."""
    if split_name not in SPLIT_COLUMNS:
        raise ValueError(f"Unknown split view: {split_name}")
    folds = sorted({int(row[split_name]) for row in rows})
    if not folds:
        raise ValueError(f"Split {split_name} has no represented folds.")
    heldout_folds = folds if split_name == "condition_fold" else [fold for fold in folds if fold != 0]
    if not heldout_folds:
        raise ValueError(f"Split {split_name} has no non-zero holdout folds.")

    instances: list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]] = []
    for heldout_fold in heldout_folds:
        train_rows = [row for row in rows if int(row[split_name]) != heldout_fold]
        test_rows = [row for row in rows if int(row[split_name]) == heldout_fold]
        if not train_rows or not test_rows:
            raise ValueError(
                f"Split {split_name} fold {heldout_fold} has "
                f"train_rows={len(train_rows)} test_rows={len(test_rows)}."
            )
        instances.append((heldout_fold, train_rows, test_rows))
    return instances


def assert_no_parameter_set_leakage(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    split_name: str,
    heldout_fold: int,
) -> None:
    """Fail if any parameter set appears on both sides of a split instance."""
    train_params = {int(row["parameter_set"]) for row in train_rows}
    test_params = {int(row["parameter_set"]) for row in test_rows}
    overlap = sorted(train_params & test_params)
    if overlap:
        raise ValueError(
            f"Parameter-set leakage in {split_name} fold {heldout_fold}: {overlap}"
        )


def predict_capacity_target(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int = DEFAULT_HGB_MAX_ITER,
) -> list[dict[str, float | None]]:
    """Fit/predict one target for one model and feature group."""
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}")
    if model_level == "L0_persistence":
        return [_persistence_prediction(row, target) for row in test_rows]

    np, Ridge, HistGradientBoostingRegressor = _import_sklearn_stack()
    encoder = FeatureEncoder.fit(train_rows, feature_group)
    x_train = np.asarray(encoder.transform(train_rows), dtype=float)
    x_test = np.asarray(encoder.transform(test_rows), dtype=float)
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not all(math.isfinite(float(value)) for value in y_train):
        raise ValueError(f"Target {target} has non-finite train values.")

    if model_level == "L1_ridge":
        x_train = np.asarray(
            encoder.transform(train_rows, standardize_numeric=True),
            dtype=float,
        )
        x_test = np.asarray(
            encoder.transform(test_rows, standardize_numeric=True),
            dtype=float,
        )
        model = Ridge(alpha=1.0)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        return [
            _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
            for row, value in zip(test_rows, values)
        ]

    if model_level == "L2_hist_gradient_boosting":
        model = HistGradientBoostingRegressor(random_state=seed, max_iter=hgb_max_iter)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        return [
            _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
            for row, value in zip(test_rows, values)
        ]

    if model_level == "L3_quantile_hist_gradient_boosting":
        quantile_predictions: dict[float, Any] = {}
        for quantile in (0.1, 0.5, 0.9):
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                random_state=seed,
                max_iter=hgb_max_iter,
            )
            model.fit(x_train, y_train)
            quantile_predictions[quantile] = model.predict(x_test)
        return [
            {
                "y_pred": _prediction_to_evaluation_space(
                    test_rows[idx], target, float(quantile_predictions[0.5][idx])
                ),
                "y_pred_q10": _prediction_to_evaluation_space(
                    test_rows[idx], target, float(quantile_predictions[0.1][idx])
                ),
                "y_pred_q50": _prediction_to_evaluation_space(
                    test_rows[idx], target, float(quantile_predictions[0.5][idx])
                ),
                "y_pred_q90": _prediction_to_evaluation_space(
                    test_rows[idx], target, float(quantile_predictions[0.9][idx])
                ),
            }
            for idx in range(len(test_rows))
        ]

    raise ValueError(f"Unknown model level: {model_level}")


def _bias_corrected_predictions(
    *,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    hgb_max_iter: int,
    test_predictions: list[dict[str, float | None]],
) -> list[dict[str, float | None]]:
    """Apply train-fold-only group residual means to test predictions."""
    train_predictions = predict_capacity_target(
        model_level=model_level,
        feature_group=feature_group,
        train_rows=train_rows,
        test_rows=train_rows,
        target=target,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
    )
    residuals_by_key: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    global_residuals: list[float] = []
    for row, prediction in zip(train_rows, train_predictions):
        residual = _evaluation_target_value(row, target) - _as_float(prediction["y_pred"])
        if not math.isfinite(residual):
            continue
        residuals_by_key[_bias_correction_key(row)].append(residual)
        global_residuals.append(residual)
    global_correction = _mean(global_residuals) if global_residuals else 0.0

    corrected: list[dict[str, float | None]] = []
    for row, prediction in zip(test_rows, test_predictions):
        key_residuals = residuals_by_key.get(_bias_correction_key(row))
        correction = _mean(key_residuals) if key_residuals else global_correction
        adjusted = dict(prediction)
        adjusted["y_pred"] = _as_float(prediction["y_pred"]) + correction
        for quantile_key in ("y_pred_q10", "y_pred_q50", "y_pred_q90"):
            value = _nullable_float(prediction.get(quantile_key))
            adjusted[quantile_key] = value + correction if value is not None else None
        corrected.append(adjusted)
    return corrected


def _bias_correction_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _group_value(row.get("nominal_temperature_C")),
        _group_value(row.get("voltage_window_family")),
        _c_rate_bucket(row.get("nominal_charge_C_rate")),
    )


def compute_metrics(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    target: str,
    subset_name: str,
    run_scope: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    train_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute row and condition-level regression metrics."""
    if len(test_rows) != len(predictions):
        raise ValueError("Prediction count does not match test row count.")
    errors = [
        _as_float(prediction["y_pred"]) - _evaluation_target_value(row, target)
        for row, prediction in zip(test_rows, predictions)
    ]
    abs_errors = [abs(error) for error in errors]
    condition_abs_errors: dict[int, list[float]] = {}
    for row, abs_error in zip(test_rows, abs_errors):
        condition_abs_errors.setdefault(int(row["parameter_set"]), []).append(abs_error)
    condition_mae = [_mean(values) for values in condition_abs_errors.values()]
    quantile_metrics = _quantile_metrics(test_rows, predictions, target)

    return {
        "subset_name": subset_name,
        "run_scope": run_scope,
        "split_name": split_name,
        "heldout_fold": heldout_fold,
        "model_level": model_level,
        "feature_group": feature_group,
        "target": target,
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "train_parameter_sets": len({int(row["parameter_set"]) for row in train_rows}),
        "test_parameter_sets": len({int(row["parameter_set"]) for row in test_rows}),
        "test_cells": len({str(row["cell_id"]) for row in test_rows}),
        "mae": _mean(abs_errors),
        "rmse": math.sqrt(_mean([error * error for error in errors])),
        "condition_mean_mae": _mean(condition_mae),
        "condition_median_mae": _median(condition_mae),
        "worst_condition_mae": max(condition_mae),
        **quantile_metrics,
    }


def _leaderboard_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        key = (
            str(metric["run_scope"]),
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
        )
        grouped[key].append(metric)

    rows: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        run_scope, model_level, feature_group, target, split_name = key
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "fold_count": len(group),
                "mean_mae": _mean([float(item["mae"]) for item in group]),
                "mean_rmse": _mean([float(item["rmse"]) for item in group]),
                "condition_mean_mae": _mean(
                    [float(item["condition_mean_mae"]) for item in group]
                ),
                "condition_median_mae": _mean(
                    [float(item["condition_median_mae"]) for item in group]
                ),
                "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in group),
                "q10_q90_interval_coverage": _mean_optional(
                    [item.get("q10_q90_interval_coverage") for item in group]
                ),
                "q10_q90_interval_width_mean": _mean_optional(
                    [item.get("q10_q90_interval_width_mean") for item in group]
                ),
                "pinball_loss_q10": _mean_optional(
                    [item.get("pinball_loss_q10") for item in group]
                ),
                "pinball_loss_q50": _mean_optional(
                    [item.get("pinball_loss_q50") for item in group]
                ),
                "pinball_loss_q90": _mean_optional(
                    [item.get("pinball_loss_q90") for item in group]
                ),
                "test_rows": sum(int(item["test_rows"]) for item in group),
                "test_parameter_sets": sum(int(item["test_parameter_sets"]) for item in group),
            }
        )
    return rows


def _worst_condition_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "run_scope": metric["run_scope"],
            "model_level": metric["model_level"],
            "feature_group": metric["feature_group"],
            "target": metric["target"],
            "split_name": metric["split_name"],
            "heldout_fold": metric["heldout_fold"],
            "worst_condition_mae": metric["worst_condition_mae"],
            "condition_mean_mae": metric["condition_mean_mae"],
            "condition_median_mae": metric["condition_median_mae"],
            "test_parameter_sets": metric["test_parameter_sets"],
        }
        for metric in metrics
    ]


def _sensitivity_delta_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for metric in metrics:
        key = (
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
            int(metric["heldout_fold"]),
        )
        by_key[key][str(metric["run_scope"])] = metric

    rows: list[dict[str, Any]] = []
    for key, group in sorted(by_key.items()):
        primary = group.get("primary")
        sensitivity = group.get("sensitivity_excluding_monotonicity")
        if not primary or not sensitivity:
            continue
        model_level, feature_group, target, split_name, heldout_fold = key
        rows.append(
            {
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "primary_mae": primary["mae"],
                "sensitivity_mae": sensitivity["mae"],
                "primary_minus_sensitivity_mae": float(primary["mae"])
                - float(sensitivity["mae"]),
                "primary_condition_mean_mae": primary["condition_mean_mae"],
                "sensitivity_condition_mean_mae": sensitivity["condition_mean_mae"],
                "primary_minus_sensitivity_condition_mean_mae": float(
                    primary["condition_mean_mae"]
                )
                - float(sensitivity["condition_mean_mae"]),
            }
        )
    return rows


def _rate_target_comparison_rows(leaderboard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            row["run_scope"],
            row["model_level"],
            row["feature_group"],
            row["split_name"],
            row["target"],
        ): row
        for row in leaderboard_rows
    }
    rows: list[dict[str, Any]] = []
    bases = sorted(
        {
            (row["run_scope"], row["model_level"], row["feature_group"], row["split_name"])
            for row in leaderboard_rows
        }
    )
    for base in bases:
        direct = by_key.get((*base, "delta_capacity_Ah"))
        if not direct:
            continue
        for rate_target in RATE_TARGETS:
            rate = by_key.get((*base, rate_target))
            if not rate:
                continue
            rows.append(
                {
                    "run_scope": base[0],
                    "model_level": base[1],
                    "feature_group": base[2],
                    "split_name": base[3],
                    "direct_delta_condition_mean_mae": direct["condition_mean_mae"],
                    "rate_target": rate_target,
                    "rate_target_condition_mean_mae": rate["condition_mean_mae"],
                    "rate_minus_direct_condition_mean_mae": float(rate["condition_mean_mae"])
                    - float(direct["condition_mean_mae"]),
                    "rate_target_better": float(rate["condition_mean_mae"])
                    < float(direct["condition_mean_mae"]),
                }
            )
    return rows


def _bias_correction_rows(leaderboard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            row["model_level"],
            row["feature_group"],
            row["target"],
            row["split_name"],
            row["run_scope"],
        ): row
        for row in leaderboard_rows
    }
    rows: list[dict[str, Any]] = []
    for key, corrected in sorted(by_key.items()):
        model_level, feature_group, target, split_name, run_scope = key
        if not str(run_scope).endswith("_bias_corrected"):
            continue
        base_scope = str(run_scope).removesuffix("_bias_corrected")
        base = by_key.get((model_level, feature_group, target, split_name, base_scope))
        if not base:
            continue
        rows.append(
            {
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "split_name": split_name,
                "base_run_scope": base_scope,
                "corrected_run_scope": run_scope,
                "base_condition_mean_mae": base["condition_mean_mae"],
                "corrected_condition_mean_mae": corrected["condition_mean_mae"],
                "condition_mean_mae_gain": float(base["condition_mean_mae"])
                - float(corrected["condition_mean_mae"]),
                "base_worst_condition_mae": base["worst_condition_mae"],
                "corrected_worst_condition_mae": corrected["worst_condition_mae"],
            }
        )
    return rows


def _c_rate_bias_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaderboard_rows = _leaderboard_rows(metrics)
    return [
        row
        for row in _bias_correction_rows(leaderboard_rows)
        if row["split_name"] == "c_rate_holdout_fold"
    ]


def _feature_gain_rows(leaderboard_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_key = {
        (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["target"]),
            str(row["split_name"]),
            str(row["feature_group"]),
        ): row
        for row in leaderboard_rows
        if str(row["feature_group"]) in FEATURE_GROUPS
    }
    feature_pairs = list(zip(FEATURE_GROUPS[1:], FEATURE_GROUPS[2:], strict=False))
    rows: list[dict[str, Any]] = []
    for run_scope in sorted({str(row["run_scope"]) for row in leaderboard_rows}):
        for model_level in sorted(
            {
                str(row["model_level"])
                for row in leaderboard_rows
                if str(row["model_level"]) != "L0_persistence"
            }
        ):
            for target in sorted({str(row["target"]) for row in leaderboard_rows}):
                for split_name in sorted({str(row["split_name"]) for row in leaderboard_rows}):
                    for from_group, to_group in feature_pairs:
                        from_row = rows_by_key.get(
                            (run_scope, model_level, target, split_name, from_group)
                        )
                        to_row = rows_by_key.get(
                            (run_scope, model_level, target, split_name, to_group)
                        )
                        if not from_row or not to_row:
                            continue
                        rows.append(
                            {
                                "run_scope": run_scope,
                                "model_level": model_level,
                                "target": target,
                                "split_name": split_name,
                                "from_feature_group": from_group,
                                "to_feature_group": to_group,
                                "from_condition_mean_mae": from_row["condition_mean_mae"],
                                "to_condition_mean_mae": to_row["condition_mean_mae"],
                                "condition_mean_mae_gain": float(
                                    from_row["condition_mean_mae"]
                                )
                                - float(to_row["condition_mean_mae"]),
                                "from_worst_condition_mae": from_row["worst_condition_mae"],
                                "to_worst_condition_mae": to_row["worst_condition_mae"],
                                "worst_condition_mae_gain": float(
                                    from_row["worst_condition_mae"]
                                )
                                - float(to_row["worst_condition_mae"]),
                            }
                        )
    return rows


def _best_by_target_split_rows(
    leaderboard_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    reference_leaderboard_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    primary_rows = [row for row in leaderboard_rows if row["run_scope"] == "primary"]
    l0_reference_rows = _l0_reference_rows(reference_leaderboard_rows or [])
    rows: list[dict[str, Any]] = []
    for target in sorted({str(row["target"]) for row in primary_rows}):
        for split_name in sorted({str(row["split_name"]) for row in primary_rows}):
            group = [
                row
                for row in primary_rows
                if row["target"] == target and row["split_name"] == split_name
            ]
            if not group:
                continue
            best = min(
                group,
                key=lambda row: (
                    float(row["condition_mean_mae"]),
                    float(row["worst_condition_mae"]),
                ),
            )
            l0 = next(
                (
                    row
                    for row in group
                    if row["model_level"] == "L0_persistence"
                    and row["feature_group"] == "persistence"
                ),
                None,
            )
            l0_reference_status = "current_report" if l0 is not None else "reference_missing"
            if l0 is None:
                l0 = l0_reference_rows.get((target, split_name))
                if l0 is not None:
                    l0_reference_status = "reference_report"
            worst_parameter_set, worst_mae = _worst_condition_for_selection(
                prediction_rows,
                run_scope="primary",
                model_level=str(best["model_level"]),
                feature_group=str(best["feature_group"]),
                target=target,
                split_name=split_name,
            )
            l0_condition_mean = _optional_float(
                l0["condition_mean_mae"] if l0 is not None else None
            )
            best_condition_mean = float(best["condition_mean_mae"])
            improvement = (
                l0_condition_mean - best_condition_mean
                if l0_condition_mean is not None
                else "reference_missing"
            )
            rows.append(
                {
                    "target": target,
                    "split_name": split_name,
                    "best_model_level": best["model_level"],
                    "best_feature_group": best["feature_group"],
                    "best_condition_mean_mae": best_condition_mean,
                    "best_worst_condition_mae": best["worst_condition_mae"],
                    "worst_parameter_set": worst_parameter_set,
                    "worst_parameter_set_mae": worst_mae,
                    "l0_condition_mean_mae": (
                        l0_condition_mean
                        if l0_condition_mean is not None
                        else "reference_missing"
                    ),
                    "l0_reference_status": l0_reference_status,
                    "condition_mean_mae_improvement_vs_l0": improvement,
                }
            )
    return rows


def _c_rate_holdout_error_rows(
    leaderboard_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    metadata: dict[int, dict[str, Any]],
    reference_leaderboard_rows: list[dict[str, Any]] | None = None,
    reference_prediction_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    best_rows = [
        row
        for row in _best_by_target_split_rows(
            leaderboard_rows,
            prediction_rows,
            reference_leaderboard_rows=reference_leaderboard_rows,
        )
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    output_rows: list[dict[str, Any]] = []
    for best in best_rows:
        target = str(best["target"])
        best_errors = _condition_mae_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level=str(best["best_model_level"]),
            feature_group=str(best["best_feature_group"]),
            target=target,
            split_name="c_rate_holdout_fold",
        )
        l0_errors = _condition_mae_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level="L0_persistence",
            feature_group="persistence",
            target=target,
            split_name="c_rate_holdout_fold",
        )
        persistence_reference_status = "current_report"
        if not l0_errors and reference_prediction_rows:
            l0_errors = _condition_mae_for_selection(
                reference_prediction_rows,
                run_scope="primary",
                model_level="L0_persistence",
                feature_group="persistence",
                target=target,
                split_name="c_rate_holdout_fold",
            )
            persistence_reference_status = (
                "reference_report" if l0_errors else "reference_missing"
            )
        elif not l0_errors:
            persistence_reference_status = "reference_missing"
        for parameter_set, best_error in sorted(best_errors.items()):
            meta = metadata.get(parameter_set, {})
            persistence_error = l0_errors.get(parameter_set)
            improvement = (
                persistence_error - best_error
                if persistence_error is not None
                else "reference_missing"
            )
            output_rows.append(
                {
                    "target": target,
                    "parameter_set": parameter_set,
                    "replicate_count": meta.get("replicate_count"),
                    "aging_mode": meta.get("aging_mode"),
                    "nominal_temperature_C": meta.get("nominal_temperature_C"),
                    "voltage_window_family": meta.get("voltage_window_family"),
                    "nominal_charge_C_rate": meta.get("nominal_charge_C_rate"),
                    "nominal_discharge_C_rate": meta.get("nominal_discharge_C_rate"),
                    "n_intervals": meta.get("n_intervals"),
                    "capacity_Ah_k_min": meta.get("capacity_Ah_k_min"),
                    "capacity_Ah_k_max": meta.get("capacity_Ah_k_max"),
                    "delta_capacity_Ah_min": meta.get("delta_capacity_Ah_min"),
                    "delta_capacity_Ah_max": meta.get("delta_capacity_Ah_max"),
                    "best_model_level": best["best_model_level"],
                    "best_feature_group": best["best_feature_group"],
                    "best_model_error": best_error,
                    "persistence_error": (
                        persistence_error
                        if persistence_error is not None
                        else "reference_missing"
                    ),
                    "persistence_reference_status": persistence_reference_status,
                    "error_improvement_vs_persistence": improvement,
                }
            )
    return output_rows


def _l0_reference_rows(
    leaderboard_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for row in leaderboard_rows:
        if (
            str(row.get("run_scope")) != "primary"
            or str(row.get("model_level")) != "L0_persistence"
            or str(row.get("feature_group")) != "persistence"
        ):
            continue
        rows[(str(row["target"]), str(row["split_name"]))] = row
    return rows


def _c_rate_grouped_summary_rows(c_rate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouping_specs = (
        ("temperature", lambda row: _group_value(row.get("nominal_temperature_C"))),
        ("voltage_window_family", lambda row: _group_value(row.get("voltage_window_family"))),
        ("target", lambda row: _group_value(row.get("target"))),
        ("parameter_set", lambda row: _group_value(row.get("parameter_set"))),
        ("interval_count_bucket", lambda row: _interval_count_bucket(row.get("n_intervals"))),
        ("capacity_Ah_k_range", lambda row: _value_range_bucket(
            row.get("capacity_Ah_k_min"),
            row.get("capacity_Ah_k_max"),
            thresholds=(2.4, 2.6, 2.8),
            labels=("<2.4", "2.4-2.6", "2.6-2.8", ">=2.8"),
        )),
        ("delta_capacity_Ah_range", lambda row: _value_range_bucket(
            row.get("delta_capacity_Ah_min"),
            row.get("delta_capacity_Ah_max"),
            thresholds=(-0.6, -0.4, -0.2),
            labels=("<-0.6", "-0.6--0.4", "-0.4--0.2", ">=-0.2"),
        )),
    )
    output_rows: list[dict[str, Any]] = []
    for group_name, key_fn in grouping_specs:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in c_rate_rows:
            grouped[key_fn(row)].append(row)
        for group_value, rows in sorted(grouped.items()):
            best_errors = [_nullable_float(row.get("best_model_error")) for row in rows]
            persistence_errors = [
                _nullable_float(row.get("persistence_error")) for row in rows
            ]
            improvements = [
                _nullable_float(row.get("error_improvement_vs_persistence"))
                for row in rows
            ]
            output_rows.append(
                {
                    "grouping": group_name,
                    "group_value": group_value,
                    "row_count": len(rows),
                    "parameter_set_count": len({int(row["parameter_set"]) for row in rows}),
                    "total_intervals": sum(
                        int(row["n_intervals"]) for row in rows if row.get("n_intervals") is not None
                    ),
                    "mean_best_model_error": _mean_optional(best_errors),
                    "mean_persistence_error": _mean_optional(persistence_errors),
                    "mean_error_improvement_vs_persistence": _mean_optional(improvements),
                    "max_best_model_error": _max_optional(best_errors),
                }
            )
    return output_rows


def _target_consistency_metric_rows(
    prediction_rows: list[dict[str, Any]],
    interval_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in prediction_rows:
        interval = interval_by_key.get(_interval_key(row))
        if interval is None:
            continue
        capacity_k = _as_float(interval.get("capacity_Ah_k"))
        capacity_k1 = _as_float(interval.get("capacity_Ah_k1"))
        delta = _as_float(interval.get("delta_capacity_Ah"))
        prediction = _as_float(row.get("y_pred"))
        if not all(math.isfinite(value) for value in (capacity_k, capacity_k1, delta, prediction)):
            continue
        base_key = (
            str(row["run_scope"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
        )
        if str(row["target"]) == "capacity_Ah_k1":
            grouped[(*base_key, "capacity_Ah_k1", "direct_capacity")].append(
                _metric_row_payload(row, capacity_k1, prediction)
            )
            grouped[(*base_key, "delta_capacity_Ah", "derived_delta_from_capacity")].append(
                _metric_row_payload(row, delta, prediction - capacity_k)
            )
        elif str(row["target"]) == "delta_capacity_Ah":
            grouped[(*base_key, "delta_capacity_Ah", "direct_delta")].append(
                _metric_row_payload(row, delta, prediction)
            )
            grouped[(*base_key, "capacity_Ah_k1", "derived_capacity_from_delta")].append(
                _metric_row_payload(row, capacity_k1, capacity_k + prediction)
            )

    rows: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items()):
        run_scope, model_level, feature_group, split_name, heldout_fold, target, target_path = key
        rows.append(
            {
                "run_scope": run_scope,
                "model_level": model_level,
                "feature_group": feature_group,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "target": target,
                "target_path": target_path,
                **_prediction_metric_summary(values),
            }
        )
    return rows


def _direct_vs_derived_target_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            row["run_scope"],
            row["model_level"],
            row["feature_group"],
            row["split_name"],
            row["heldout_fold"],
            row["target"],
            row["target_path"],
        ): row
        for row in metric_rows
    }
    pairs = (
        ("capacity_Ah_k1", "direct_capacity", "derived_capacity_from_delta"),
        ("delta_capacity_Ah", "direct_delta", "derived_delta_from_capacity"),
    )
    rows: list[dict[str, Any]] = []
    bases = sorted(
        {
            (row["run_scope"], row["model_level"], row["feature_group"], row["split_name"], row["heldout_fold"])
            for row in metric_rows
        }
    )
    for base in bases:
        for target, direct_path, derived_path in pairs:
            direct = by_key.get((*base, target, direct_path))
            derived = by_key.get((*base, target, derived_path))
            if not direct or not derived:
                continue
            direct_mae = float(direct["mae"])
            derived_mae = float(derived["mae"])
            rows.append(
                {
                    "run_scope": base[0],
                    "model_level": base[1],
                    "feature_group": base[2],
                    "split_name": base[3],
                    "heldout_fold": base[4],
                    "target": target,
                    "direct_path": direct_path,
                    "derived_path": derived_path,
                    "direct_mae": direct_mae,
                    "derived_mae": derived_mae,
                    "derived_minus_direct_mae": derived_mae - direct_mae,
                    "derived_better": derived_mae < direct_mae,
                    "direct_condition_mean_mae": direct["condition_mean_mae"],
                    "derived_condition_mean_mae": derived["condition_mean_mae"],
                    "derived_minus_direct_condition_mean_mae": float(
                        derived["condition_mean_mae"]
                    )
                    - float(direct["condition_mean_mae"]),
                }
            )
    return rows


def _c_rate_residual_rows(
    report: dict[str, Any],
    prediction_rows: list[dict[str, Any]],
    interval_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    leaderboard = _leaderboard_rows(list(report["metrics"]))
    best = _best_reference_by_target_split(
        leaderboard,
        allowed_feature_groups=set(FEATURE_GROUPS),
    )
    param_interval_counts = Counter(
        int(row["parameter_set"]) for row in interval_by_key.values()
    )
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        selection = best.get((target, "c_rate_holdout_fold"))
        if not selection:
            continue
        selected_predictions = [
            row
            for row in prediction_rows
            if row["run_scope"] == "primary"
            and row["target"] == target
            and row["split_name"] == "c_rate_holdout_fold"
            and row["model_level"] == selection["model_level"]
            and row["feature_group"] == selection["feature_group"]
        ]
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in selected_predictions:
            interval = interval_by_key.get(_interval_key(row))
            if interval is None:
                continue
            y_true = _as_float(row.get("y_true"))
            y_pred = _as_float(row.get("y_pred"))
            if not math.isfinite(y_true) or not math.isfinite(y_pred):
                continue
            payload = dict(interval)
            payload["error"] = y_pred - y_true
            payload["abs_error"] = abs(y_pred - y_true)
            grouped[int(row["parameter_set"])].append(payload)
        for parameter_set, values in sorted(grouped.items()):
            errors = [float(row["error"]) for row in values]
            abs_errors = [float(row["abs_error"]) for row in values]
            capacity_values = [_as_float(row.get("capacity_Ah_k")) for row in values]
            delta_values = [_as_float(row.get("delta_capacity_Ah")) for row in values]
            finite_capacity = [value for value in capacity_values if math.isfinite(value)]
            finite_delta = [value for value in delta_values if math.isfinite(value)]
            first = values[0]
            n_intervals = param_interval_counts[parameter_set]
            rows.append(
                {
                    "target": target,
                    "parameter_set": parameter_set,
                    "best_model_level": selection["model_level"],
                    "best_feature_group": selection["feature_group"],
                    "n_intervals": n_intervals,
                    "nominal_temperature_C": first.get("nominal_temperature_C"),
                    "voltage_window_family": first.get("voltage_window_family"),
                    "aging_mode": first.get("aging_mode"),
                    "nominal_charge_C_rate": first.get("nominal_charge_C_rate"),
                    "nominal_discharge_C_rate": first.get("nominal_discharge_C_rate"),
                    "capacity_Ah_k_min": min(finite_capacity) if finite_capacity else None,
                    "capacity_Ah_k_max": max(finite_capacity) if finite_capacity else None,
                    "delta_capacity_Ah_min": min(finite_delta) if finite_delta else None,
                    "delta_capacity_Ah_max": max(finite_delta) if finite_delta else None,
                    "capacity_Ah_k_bin": _value_range_bucket(
                        min(finite_capacity) if finite_capacity else None,
                        max(finite_capacity) if finite_capacity else None,
                        thresholds=(2.4, 2.6, 2.8),
                        labels=("<2.4", "2.4-2.6", "2.6-2.8", ">=2.8"),
                    ),
                    "interval_count_bucket": _interval_count_bucket(n_intervals),
                    "mae": _mean(abs_errors),
                    "rmse": math.sqrt(_mean([error * error for error in errors])),
                    "signed_bias": _mean(errors),
                    "worst_abs_error": max(abs_errors),
                }
            )
    return rows


def _residual_group_rows(
    residual_rows: list[dict[str, Any]],
    group_column: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in residual_rows:
        grouped[(str(row["target"]), _group_value(row.get(group_column)))].append(row)
    rows: list[dict[str, Any]] = []
    for (target, group_value), values in sorted(grouped.items()):
        maes = [_as_float(row["mae"]) for row in values]
        biases = [_as_float(row["signed_bias"]) for row in values]
        rmses = [_as_float(row["rmse"]) for row in values]
        rows.append(
            {
                "target": target,
                "grouping": group_column,
                "group_value": group_value,
                "parameter_set_count": len(values),
                "total_intervals": sum(int(row["n_intervals"]) for row in values),
                "mean_mae": _mean(maes),
                "mean_rmse": _mean(rmses),
                "mean_signed_bias": _mean(biases),
                "worst_parameter_set": max(values, key=lambda row: float(row["mae"]))[
                    "parameter_set"
                ],
                "worst_mae": max(float(row["mae"]) for row in values),
            }
        )
    return rows


def _stress_ablation_gain_rows(
    leaderboard_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stress_groups = (
        "F5_log_age_histograms",
        "F6_coupled_stress",
        "F7_c_rate_focused",
        "F8_timestamp_weighted_stress",
        "F9_event_segmented_stress",
        "F10_c_rate_v1_1",
        "F11_minimal_cold_current",
        "F12_voltage_cold_current_interactions",
        "F13_sparse_c_rate_context",
    )
    by_key = {
        (
            row["run_scope"],
            row["model_level"],
            row["target"],
            row["split_name"],
            row["feature_group"],
        ): row
        for row in leaderboard_rows
        if row["run_scope"] == "primary"
    }
    rows: list[dict[str, Any]] = []
    base_keys = sorted(
        {
            (row["run_scope"], row["model_level"], row["target"], row["split_name"])
            for row in leaderboard_rows
            if row["run_scope"] == "primary"
        }
    )
    for base in base_keys:
        f4 = by_key.get((*base, "F4_state_log_age_scalar"))
        if not f4:
            continue
        f4_error = float(f4["condition_mean_mae"])
        for feature_group in stress_groups:
            row = by_key.get((*base, feature_group))
            if not row:
                continue
            error = float(row["condition_mean_mae"])
            rows.append(
                {
                    "run_scope": base[0],
                    "model_level": base[1],
                    "target": base[2],
                    "split_name": base[3],
                    "from_feature_group": "F4_state_log_age_scalar",
                    "to_feature_group": feature_group,
                    "f4_condition_mean_mae": f4_error,
                    "feature_condition_mean_mae": error,
                    "condition_mean_mae_gain": f4_error - error,
                    "f4_worst_condition_mae": f4["worst_condition_mae"],
                    "feature_worst_condition_mae": row["worst_condition_mae"],
                    "success_vs_f4": error < f4_error,
                }
            )
    return rows


def _metric_row_payload(
    prediction_row: dict[str, Any],
    y_true: float,
    y_pred: float,
) -> dict[str, Any]:
    return {
        "parameter_set": int(prediction_row["parameter_set"]),
        "cell_id": str(prediction_row["cell_id"]),
        "y_true": y_true,
        "y_pred": y_pred,
        "error": y_pred - y_true,
        "abs_error": abs(y_pred - y_true),
    }


def _prediction_metric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [float(row["error"]) for row in rows]
    abs_errors = [float(row["abs_error"]) for row in rows]
    by_condition: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        by_condition[int(row["parameter_set"])].append(float(row["abs_error"]))
    condition_maes = [_mean(values) for values in by_condition.values()]
    return {
        "test_rows": len(rows),
        "test_parameter_sets": len(by_condition),
        "mae": _mean(abs_errors),
        "rmse": math.sqrt(_mean([error * error for error in errors])),
        "signed_bias": _mean(errors),
        "condition_mean_mae": _mean(condition_maes),
        "condition_median_mae": _median(condition_maes),
        "worst_condition_mae": max(condition_maes),
    }


def _interval_rows_by_key(report: dict[str, Any]) -> dict[tuple[str, int, int], dict[str, Any]]:
    interval_path = Path(report["inputs"]["interval_table"])
    if not interval_path.exists():
        return {}
    return {_interval_key(row): row for row in pq.read_table(interval_path).to_pylist()}


def _write_target_consistency_md(
    report: dict[str, Any],
    target_metric_rows: list[dict[str, Any]],
    direct_vs_derived_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    c_rate_rows = [
        row
        for row in direct_vs_derived_rows
        if row["run_scope"] == "primary" and row["split_name"] == "c_rate_holdout_fold"
    ]
    best_c_rate = sorted(
        c_rate_rows,
        key=lambda row: (
            row["target"],
            min(float(row["direct_mae"]), float(row["derived_mae"])),
        ),
    )
    delta_c_rate = [
        row for row in c_rate_rows if row["target"] == "delta_capacity_Ah"
    ]
    derived_delta_wins = sum(bool(row["derived_better"]) for row in delta_c_rate)
    lines = [
        "# Capacity Target Consistency Diagnostics",
        "",
        f"Source report: `{report['outputs']['report']}`",
        f"Generated at UTC: `{datetime.now(UTC).isoformat()}`",
        "",
        "This diagnostic checks whether the algebraic relationship",
        "`capacity_Ah_k1 = capacity_Ah_k + delta_capacity_Ah` changes the",
        "interpretation of direct target-specific predictions.",
        "",
        "## C-Rate Direct Vs Derived",
        "",
        "| Target | Model | Feature group | Direct MAE | Derived MAE | Derived - direct | Derived better |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in best_c_rate[:20]:
        lines.append(
            "| "
            f"`{row['target']}` | `{row['model_level']}` | `{row['feature_group']}` | "
            f"{float(row['direct_mae']):.6g} | {float(row['derived_mae']):.6g} | "
            f"{float(row['derived_minus_direct_mae']):.6g} | {row['derived_better']} |"
        )
    lines.extend(
        [
            "",
            "## Decision Signal",
            "",
            f"C-rate delta rows where derived delta beats direct delta: `{derived_delta_wins}/{len(delta_c_rate)}`.",
            "",
            "If derived delta consistently beats direct delta on C-rate, report a",
            "capacity-first target path before adding new stress features. If direct",
            "delta remains stronger, the failure is not only target formulation.",
            "",
            "## Outputs",
            "",
            "- `plots/derived_delta_from_capacity_metrics.csv`",
            "- `plots/derived_capacity_from_delta_metrics.csv`",
            "- `plots/direct_vs_derived_target_metrics.csv`",
            f"- Target metric rows: `{len(target_metric_rows)}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_c_rate_residual_analysis_md(
    residual_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    worst = sorted(residual_rows, key=lambda row: float(row["mae"]), reverse=True)[:12]
    lines = [
        "# C-Rate Residual Analysis",
        "",
        "This diagnostic uses row-level predictions for the best primary C-rate",
        "selection per target in the focused stress-feature report.",
        "",
        "| Target | Parameter set | Feature group | Temperature C | Voltage family | Intervals | MAE | Bias | RMSE |",
        "|---|---:|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in worst:
        lines.append(
            "| "
            f"`{row['target']}` | {row['parameter_set']} | `{row['best_feature_group']}` | "
            f"{_format_optional_float(row['nominal_temperature_C'])} | "
            f"`{row['voltage_window_family']}` | {row['n_intervals']} | "
            f"{float(row['mae']):.6g} | {float(row['signed_bias']):.6g} | "
            f"{float(row['rmse']):.6g} |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `plots/c_rate_residuals_by_parameter_set.csv`",
            "- `plots/c_rate_residuals_by_temperature.csv`",
            "- `plots/c_rate_residuals_by_voltage_window.csv`",
            "- `plots/c_rate_residuals_by_capacity_bin.csv`",
            "- `plots/c_rate_residuals_by_interval_count.csv`",
            "- `plots/c_rate_signed_error_summary.csv`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_stress_ablation_summary_md(
    stress_gain_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    c_rate_rows = [
        row
        for row in stress_gain_rows
        if row["run_scope"] == "primary" and row["split_name"] == "c_rate_holdout_fold"
    ]
    best = sorted(c_rate_rows, key=lambda row: float(row["condition_mean_mae_gain"]), reverse=True)
    lines = [
        "# Stress Feature Ablation Summary",
        "",
        "This table compares F5-F10 against F4 within the existing v1.1 report.",
        "No new model training is performed.",
        "",
        "| Target | Model | Feature group | Gain vs F4 | Success |",
        "|---|---|---|---:|---|",
    ]
    for row in best[:20]:
        lines.append(
            "| "
            f"`{row['target']}` | `{row['model_level']}` | `{row['to_feature_group']}` | "
            f"{float(row['condition_mean_mae_gain']):.6g} | {row['success_vs_f4']} |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `plots/f4_to_f5_f6_f7_f8_f9_f10_gain_matrix.csv`",
            "- `plots/c_rate_gain_by_feature_group.csv`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_baseline_diagnostics_md(
    report: dict[str, Any],
    reference_report: dict[str, Any] | None,
    best_rows: list[dict[str, Any]],
    feature_gain_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    c_rate_grouped_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    primary_best = sorted(
        best_rows,
        key=lambda row: float(row["best_condition_mean_mae"]),
    )[:10]
    c_rate_best = sorted(
        [row for row in best_rows if row["split_name"] == "c_rate_holdout_fold"],
        key=lambda row: float(row["best_condition_mean_mae"]),
    )
    gains = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
    ]
    sensitivity_deltas = [
        float(row["primary_minus_sensitivity_condition_mean_mae"])
        for row in sensitivity_rows
    ]
    lines = [
        "# Capacity Baseline Diagnostics",
        "",
        f"Source report: `{report['outputs']['report']}`",
        f"Generated at UTC: `{datetime.now(UTC).isoformat()}`",
        f"Schema version: `{report['schema_version']}`",
        f"HGB max iterations: `{report.get('hgb_max_iter')}`",
        f"Numeric standardization: `{report.get('numeric_standardization', 'none')}`",
        f"L0 reference report: `{_reference_report_label(reference_report)}`",
        "",
        "## Best Rows By Target And Split",
        "",
        "| Target | Split | Model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 | Worst parameter set |",
        "|---|---|---|---|---:|---|---:|---:|",
    ]
    for row in primary_best:
        improvement = row["condition_mean_mae_improvement_vs_l0"]
        lines.append(
            "| "
            f"`{row['target']}` | `{row['split_name']}` | `{row['best_model_level']}` | "
            f"`{row['best_feature_group']}` | {float(row['best_condition_mean_mae']):.6g} | "
            f"`{row['l0_reference_status']}` | "
            f"{_format_diagnostic_value(improvement)} | {row['worst_parameter_set']} |"
        )

    lines.extend(
        [
            "",
            "## C-Rate Holdout",
            "",
            "The C-rate holdout remains the hardest split in the bounded capacity runs.",
            "",
            "| Target | Best model | Feature group | Condition mean MAE | L0 source | Improvement vs L0 |",
            "|---|---|---|---:|---|---:|",
        ]
    )
    for row in c_rate_best:
        lines.append(
            "| "
            f"`{row['target']}` | `{row['best_model_level']}` | `{row['best_feature_group']}` | "
            f"{float(row['best_condition_mean_mae']):.6g} | "
            f"`{row['l0_reference_status']}` | "
            f"{_format_diagnostic_value(row['condition_mean_mae_improvement_vs_l0'])} |"
        )

    lines.extend(
        [
            "",
            "## Feature Gains",
            "",
            f"Primary feature-gain rows: `{len(gains)}`",
            f"Mean primary adjacent-feature gain: `{_format_optional_float(_mean(gains) if gains else None)}`",
            "",
            "Positive gain means the later feature group reduced condition-mean MAE.",
            "",
            "## Strict Vs Tolerant Sensitivity",
            "",
            f"Sensitivity rows: `{len(sensitivity_rows)}`",
            f"Mean primary-minus-sensitivity condition-mean MAE: `{_format_optional_float(_mean(sensitivity_deltas) if sensitivity_deltas else None)}`",
            f"Median primary-minus-sensitivity condition-mean MAE: `{_format_optional_float(_median(sensitivity_deltas) if sensitivity_deltas else None)}`",
            "",
            "## Diagnostic Tables",
            "",
            "- `plots/best_by_target_split.csv`",
            "- `plots/feature_gain_by_split.csv`",
            "- `plots/c_rate_holdout_errors.csv`",
            "- `plots/c_rate_holdout_by_condition.csv`",
            "- `plots/c_rate_grouped_summaries.csv`",
            "- `plots/strict_vs_tolerant_delta.csv`",
            "- `plots/worst_condition_errors.csv`",
            "- `c_rate_holdout_error_analysis.md`",
            "- `claim_readiness.md`",
            "",
            f"C-rate diagnostic rows: `{len(c_rate_rows)}`",
            f"C-rate grouped summary rows: `{len(c_rate_grouped_rows)}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_c_rate_error_analysis_md(
    c_rate_rows: list[dict[str, Any]],
    c_rate_grouped_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    worst_rows = sorted(
        c_rate_rows,
        key=lambda row: float(row["best_model_error"]),
        reverse=True,
    )[:10]
    lines = [
        "# C-Rate Holdout Error Analysis",
        "",
        "This diagnostic focuses on the high-C-rate holdout conditions because the",
        "bounded L0-L3 baseline report identified C-rate transfer as the hardest",
        "split.",
        "",
        f"Diagnostic rows: `{len(c_rate_rows)}`",
        "",
        "## Worst Held-Out Conditions",
        "",
        "| Target | Parameter set | Temperature C | Voltage family | Charge C-rate | Intervals | Best model | Error | Persistence error | Improvement |",
        "|---|---:|---:|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in worst_rows:
        lines.append(
            "| "
            f"`{row['target']}` | {row['parameter_set']} | "
            f"{_format_optional_float(row['nominal_temperature_C'])} | "
            f"`{row['voltage_window_family']}` | "
            f"{_format_optional_float(row['nominal_charge_C_rate'])} | "
            f"{row['n_intervals']} | "
            f"`{row['best_model_level']}:{row['best_feature_group']}` | "
            f"{_format_diagnostic_value(row['best_model_error'])} | "
            f"{_format_diagnostic_value(row['persistence_error'])} | "
            f"{_format_diagnostic_value(row['error_improvement_vs_persistence'])} |"
        )

    lines.extend(["", "## Grouped Summaries", ""])
    for grouping in (
        "temperature",
        "voltage_window_family",
        "target",
        "parameter_set",
        "interval_count_bucket",
        "capacity_Ah_k_range",
        "delta_capacity_Ah_range",
    ):
        rows = [row for row in c_rate_grouped_rows if row["grouping"] == grouping]
        if not rows:
            continue
        lines.extend(
            [
                f"### {grouping}",
                "",
                "| Group | Rows | Parameter sets | Intervals | Mean error | Mean persistence | Mean improvement | Max error |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in rows:
            lines.append(
                "| "
                f"`{row['group_value']}` | {row['row_count']} | "
                f"{row['parameter_set_count']} | {row['total_intervals']} | "
                f"{_format_diagnostic_value(row['mean_best_model_error'])} | "
                f"{_format_diagnostic_value(row['mean_persistence_error'])} | "
                f"{_format_diagnostic_value(row['mean_error_improvement_vs_persistence'])} | "
                f"{_format_diagnostic_value(row['max_best_model_error'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "",
            "## Table",
            "",
            "Condition-level details are in `plots/c_rate_holdout_by_condition.csv`.",
            "Grouped summaries are in `plots/c_rate_grouped_summaries.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_claim_readiness_md(
    report: dict[str, Any],
    best_rows: list[dict[str, Any]],
    feature_gain_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    leaderboard_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    f2_to_f3 = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
        and row["from_feature_group"] == "F2_state_exposure"
        and row["to_feature_group"] == "F3_state_nominal"
    ]
    f3_to_f4 = [
        float(row["condition_mean_mae_gain"])
        for row in feature_gain_rows
        if row["run_scope"] == "primary"
        and row["from_feature_group"] == "F3_state_nominal"
        and row["to_feature_group"] == "F4_state_log_age_scalar"
    ]
    sensitivity_deltas = [
        abs(float(row["primary_minus_sensitivity_condition_mean_mae"]))
        for row in sensitivity_rows
    ]
    quantile_coverages = [
        _nullable_float(metric.get("q10_q90_interval_coverage"))
        for metric in report["metrics"]
        if str(metric.get("run_scope")) == "primary"
        and str(metric.get("model_level")) == "L3_quantile_hist_gradient_boosting"
    ]
    c_rate_best_errors = [
        _nullable_float(row.get("best_condition_mean_mae"))
        for row in best_rows
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    other_best_errors = [
        _nullable_float(row.get("best_condition_mean_mae"))
        for row in best_rows
        if row["split_name"] != "c_rate_holdout_fold"
    ]
    lines = [
        "# Capacity Baseline Claim Readiness",
        "",
        "This table is a Milestone 0.5c synthesis aid. It does not authorize",
        "EIS/PULSE modeling, knee prediction, sequence models, neural models,",
        "policy ranking, or CBAT.",
        "",
        "| Claim | Status | Evidence | Decision |",
        "|---|---|---|---|",
        "| State-aware baselines beat weak time-only baselines | Supported | "
        "`F1_state_time` and later groups include prior capacity state and dominate "
        "the weak `F0_time_only` sanity baseline in the capacity ladder. | Keep "
        "state-aware groups as the first forecast baseline. |",
        "| Nominal protocol features help | Supported | "
        f"`F2_state_exposure -> F3_state_nominal` mean gain "
        f"{_format_diagnostic_value(_mean(f2_to_f3) if f2_to_f3 else None)} "
        f"across {len(f2_to_f3)} primary rows. | Keep nominal protocol features. |",
        "| LOG_AGE scalar features help | Partially supported | "
        f"`F3_state_nominal -> F4_state_log_age_scalar` mean gain "
        f"{_format_diagnostic_value(_mean(f3_to_f4) if f3_to_f4 else None)}; "
        "the benefit is model-dependent and strongest in focused HGB. | Build "
        "stronger log-derived stress features before adding modalities. |",
        "| C-rate holdout is hardest | Supported | "
        f"Best C-rate condition-mean MAE max "
        f"{_format_diagnostic_value(_max_optional(c_rate_best_errors))}, "
        f"other split best max {_format_diagnostic_value(_max_optional(other_best_errors))}. | "
        "Focus next engineering on C-rate/stress exposure. |",
        "| Monotonicity policy changes conclusions | Not supported | "
        f"Mean absolute strict-vs-tolerant delta "
        f"{_format_diagnostic_value(_mean(sensitivity_deltas) if sensitivity_deltas else None)}. | "
        "Keep tolerant subset as primary with strict sensitivity. |",
        "| Quantile HGB is calibrated | Not supported | "
        f"Mean q10-q90 coverage "
        f"{_format_diagnostic_value(_mean_optional(quantile_coverages))}; nominal "
        "central coverage is 0.8. | Treat quantile metrics as diagnostics only. |",
        "",
        "C-rate condition rows used for stress analysis: "
        f"`{len(c_rate_rows)}`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _stress_feature_gain_rows(
    stress_leaderboard: list[dict[str, Any]],
    baseline_leaderboard: list[dict[str, Any]],
    l0_leaderboard: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_f4 = _best_reference_by_target_split(
        baseline_leaderboard,
        allowed_feature_groups={"F4_state_log_age_scalar"},
    )
    l0_reference = _l0_reference_rows(l0_leaderboard)
    rows: list[dict[str, Any]] = []
    primary_stress = [
        row
        for row in stress_leaderboard
        if row["run_scope"] == "primary" and row["feature_group"] in STRESS_FEATURE_GROUPS
    ]
    for target in sorted({str(row["target"]) for row in primary_stress}):
        for split_name in sorted({str(row["split_name"]) for row in primary_stress}):
            group = [
                row
                for row in primary_stress
                if row["target"] == target and row["split_name"] == split_name
            ]
            if not group:
                continue
            best = min(
                group,
                key=lambda row: (
                    float(row["condition_mean_mae"]),
                    float(row["worst_condition_mae"]),
                ),
            )
            baseline = baseline_f4.get((target, split_name))
            l0 = l0_reference.get((target, split_name))
            best_error = float(best["condition_mean_mae"])
            baseline_error = _optional_float(
                baseline["condition_mean_mae"] if baseline else None
            )
            l0_error = _optional_float(l0["condition_mean_mae"] if l0 else None)
            rows.append(
                {
                    "target": target,
                    "split_name": split_name,
                    "best_stress_model_level": best["model_level"],
                    "best_stress_feature_group": best["feature_group"],
                    "best_stress_condition_mean_mae": best_error,
                    "best_stress_worst_condition_mae": best["worst_condition_mae"],
                    "baseline_f4_model_level": baseline["model_level"]
                    if baseline
                    else "reference_missing",
                    "baseline_f4_condition_mean_mae": baseline_error
                    if baseline_error is not None
                    else "reference_missing",
                    "condition_mean_mae_gain_vs_f4": baseline_error - best_error
                    if baseline_error is not None
                    else "reference_missing",
                    "l0_condition_mean_mae": l0_error
                    if l0_error is not None
                    else "reference_missing",
                    "condition_mean_mae_gain_vs_l0": l0_error - best_error
                    if l0_error is not None
                    else "reference_missing",
                    "success_vs_f4": bool(baseline_error is not None and best_error < baseline_error),
                    "material_degradation_vs_f4": bool(
                        baseline_error is not None
                        and split_name in {"condition_fold", "temperature_holdout_fold"}
                        and best_error > baseline_error + 0.005
                    ),
                }
            )
    return rows


def _best_reference_by_target_split(
    leaderboard_rows: list[dict[str, Any]],
    *,
    allowed_feature_groups: set[str],
) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in leaderboard_rows:
        if row["run_scope"] != "primary" or row["feature_group"] not in allowed_feature_groups:
            continue
        grouped[(str(row["target"]), str(row["split_name"]))].append(row)
    return {
        key: min(
            rows,
            key=lambda row: (
                float(row["condition_mean_mae"]),
                float(row["worst_condition_mae"]),
            ),
        )
        for key, rows in grouped.items()
    }


def _c_rate_stress_feature_error_rows(
    stress_gain_rows: list[dict[str, Any]],
    stress_predictions: list[dict[str, Any]],
    baseline_predictions: list[dict[str, Any]],
    l0_predictions: list[dict[str, Any]],
    metadata: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary in stress_gain_rows:
        if summary["split_name"] != "c_rate_holdout_fold":
            continue
        target = str(summary["target"])
        stress_errors = _condition_mae_for_selection(
            stress_predictions,
            run_scope="primary",
            model_level=str(summary["best_stress_model_level"]),
            feature_group=str(summary["best_stress_feature_group"]),
            target=target,
            split_name="c_rate_holdout_fold",
        )
        baseline_errors = _condition_mae_for_selection(
            baseline_predictions,
            run_scope="primary",
            model_level=str(summary["baseline_f4_model_level"]),
            feature_group="F4_state_log_age_scalar",
            target=target,
            split_name="c_rate_holdout_fold",
        )
        l0_errors = _condition_mae_for_selection(
            l0_predictions,
            run_scope="primary",
            model_level="L0_persistence",
            feature_group="persistence",
            target=target,
            split_name="c_rate_holdout_fold",
        )
        for parameter_set, stress_error in sorted(stress_errors.items()):
            baseline_error = baseline_errors.get(parameter_set)
            l0_error = l0_errors.get(parameter_set)
            meta = metadata.get(parameter_set, {})
            rows.append(
                {
                    "target": target,
                    "parameter_set": parameter_set,
                    "nominal_temperature_C": meta.get("nominal_temperature_C"),
                    "voltage_window_family": meta.get("voltage_window_family"),
                    "nominal_charge_C_rate": meta.get("nominal_charge_C_rate"),
                    "n_intervals": meta.get("n_intervals"),
                    "best_stress_model_level": summary["best_stress_model_level"],
                    "best_stress_feature_group": summary["best_stress_feature_group"],
                    "stress_model_error": stress_error,
                    "baseline_f4_error": baseline_error
                    if baseline_error is not None
                    else "reference_missing",
                    "gain_vs_f4": baseline_error - stress_error
                    if baseline_error is not None
                    else "reference_missing",
                    "l0_error": l0_error if l0_error is not None else "reference_missing",
                    "gain_vs_l0": l0_error - stress_error
                    if l0_error is not None
                    else "reference_missing",
                }
            )
    return rows


def _stress_feature_claim_readiness_rows(
    stress_gain_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    c_rate_gains = [
        _nullable_float(row.get("condition_mean_mae_gain_vs_f4"))
        for row in stress_gain_rows
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    condition_degradations = [
        row
        for row in stress_gain_rows
        if row["split_name"] == "condition_fold" and row["material_degradation_vs_f4"]
    ]
    temperature_degradations = [
        row
        for row in stress_gain_rows
        if row["split_name"] == "temperature_holdout_fold"
        and row["material_degradation_vs_f4"]
    ]
    c_rate_success = all(gain is not None and gain > 0 for gain in c_rate_gains)
    no_material_degradation = not condition_degradations and not temperature_degradations
    return [
        {
            "claim": "Stress features improve C-rate holdout",
            "status": "supported" if c_rate_success else "not_supported",
            "evidence": (
                f"C-rate gains vs F4: {_format_gain_list(c_rate_gains)}; "
                f"condition rows: {len(c_rate_rows)}"
            ),
            "decision": "Use stress features for C-rate generalization"
            if c_rate_success
            else "Do not claim stress-feature improvement",
        },
        {
            "claim": "Stress features do not degrade condition/temperature folds",
            "status": "supported" if no_material_degradation else "not_supported",
            "evidence": (
                f"condition degradation rows: {len(condition_degradations)}; "
                f"temperature degradation rows: {len(temperature_degradations)}"
            ),
            "decision": "Keep focused stress-feature ladder"
            if no_material_degradation
            else "Inspect degraded split rows before promoting",
        },
        {
            "claim": "Stress features authorize new modalities",
            "status": "blocked",
            "evidence": "Milestone 0.6 remains capacity-only and scalar-interval only.",
            "decision": "Keep EIS/PULSE/CBAT blocked.",
        },
    ]


def _write_stress_feature_diagnostics_md(
    report: dict[str, Any],
    baseline_report: dict[str, Any],
    l0_reference_report: dict[str, Any],
    stress_gain_rows: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, str]],
    path: Path,
) -> None:
    c_rate_rows_summary = [
        row for row in stress_gain_rows if row["split_name"] == "c_rate_holdout_fold"
    ]
    lines = [
        "# Stress Feature Diagnostics",
        "",
        f"Source report: `{report['outputs']['report']}`",
        f"F4 baseline report: `{baseline_report['outputs']['report']}`",
        f"L0 reference report: `{l0_reference_report['outputs']['report']}`",
        f"Generated at UTC: `{datetime.now(UTC).isoformat()}`",
        "",
        "## Success Criteria",
        "",
        "| Target | Split | Stress feature group | Stress MAE | F4 MAE | Gain vs F4 | Success |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in c_rate_rows_summary:
        lines.append(
            "| "
            f"`{row['target']}` | `{row['split_name']}` | "
            f"`{row['best_stress_feature_group']}` | "
            f"{_format_diagnostic_value(row['best_stress_condition_mean_mae'])} | "
            f"{_format_diagnostic_value(row['baseline_f4_condition_mean_mae'])} | "
            f"{_format_diagnostic_value(row['condition_mean_mae_gain_vs_f4'])} | "
            f"{row['success_vs_f4']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Readiness",
            "",
            "| Claim | Status | Evidence | Decision |",
            "|---|---|---|---|",
        ]
    )
    for row in claim_rows:
        lines.append(
            f"| {row['claim']} | {row['status']} | {row['evidence']} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- `plots/stress_feature_gain_by_split.csv`",
            "- `plots/c_rate_stress_feature_errors.csv`",
            "- `plots/stress_feature_claim_readiness.csv`",
            f"- C-rate condition rows: `{len(c_rate_rows)}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _best_prior_pulse_groups(report: dict[str, Any]) -> dict[tuple[str, str], str]:
    leaderboard = _leaderboard_rows(list(report["metrics"]))
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in leaderboard:
        if row["run_scope"] != "primary" or row["feature_group"] not in PULSE_FEATURE_GROUPS:
            continue
        grouped[(str(row["target"]), str(row["split_name"]), str(row["feature_group"]))].append(row)
    best: dict[tuple[str, str], tuple[str, float, float]] = {}
    for (target, split_name, feature_group), rows in grouped.items():
        condition_mean = _mean([float(row["condition_mean_mae"]) for row in rows])
        worst = max(float(row["worst_condition_mae"]) for row in rows)
        key = (target, split_name)
        if key not in best or (condition_mean, worst) < (best[key][1], best[key][2]):
            best[key] = (feature_group, condition_mean, worst)
    return {key: value[0] for key, value in best.items()}


def _paired_prior_pulse_condition_gain_rows(
    prediction_rows: list[dict[str, Any]],
    best_prior: dict[tuple[str, str], str],
    metadata: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for (target, split_name), prior_feature_group in sorted(best_prior.items()):
        f4_errors = _condition_mae_by_fold_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level="L2_hist_gradient_boosting",
            feature_group="F4_state_log_age_scalar",
            target=target,
            split_name=split_name,
        )
        pulse_errors = _condition_mae_by_fold_for_selection(
            prediction_rows,
            run_scope="primary",
            model_level="L2_hist_gradient_boosting",
            feature_group=prior_feature_group,
            target=target,
            split_name=split_name,
        )
        for key in sorted(set(f4_errors) & set(pulse_errors)):
            heldout_fold, parameter_set = key
            meta = metadata.get(parameter_set, {})
            f4_error = f4_errors[key]["mae"]
            pulse_error = pulse_errors[key]["mae"]
            rows.append(
                {
                    "target": target,
                    "split_name": split_name,
                    "heldout_fold": heldout_fold,
                    "parameter_set": parameter_set,
                    "prior_pulse_feature_group": prior_feature_group,
                    "f4_condition_mae": f4_error,
                    "prior_pulse_condition_mae": pulse_error,
                    "gain": f4_error - pulse_error,
                    "n_intervals": pulse_errors[key]["n_intervals"],
                    "nominal_temperature_C": meta.get("nominal_temperature_C"),
                    "voltage_window_family": meta.get("voltage_window_family"),
                    "nominal_charge_C_rate": meta.get("nominal_charge_C_rate"),
                    "aging_mode": meta.get("aging_mode"),
                }
            )
    return rows


def _selection_condition_mae_rows(
    prediction_rows: list[dict[str, Any]],
    *,
    allowed_feature_groups: set[str] | None,
    covered_keys: set[tuple[str, str, int, str, int, int]],
    source_report: str,
    exclude_feature_groups: set[str] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, int, str, str, str], list[float]] = defaultdict(list)
    for row in prediction_rows:
        if str(row.get("run_scope")) != "primary":
            continue
        feature_group = str(row["feature_group"])
        model_level = str(row["model_level"])
        if model_level != "L2_hist_gradient_boosting":
            continue
        if allowed_feature_groups is not None and feature_group not in allowed_feature_groups:
            continue
        if exclude_feature_groups is not None and feature_group in exclude_feature_groups:
            continue
        key = _prediction_covered_key(row)
        if key not in covered_keys:
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        group_key = (
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            int(row["parameter_set"]),
            model_level,
            feature_group,
            source_report,
        )
        grouped[group_key].append(abs(y_pred - y_true))
    rows = []
    for (
        target,
        split_name,
        heldout_fold,
        parameter_set,
        model_level,
        feature_group,
        source_report,
    ), errors in sorted(grouped.items()):
        rows.append(
            {
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "parameter_set": parameter_set,
                "model_level": model_level,
                "feature_group": feature_group,
                "source_report": source_report,
                "condition_mae": _mean(errors),
                "n_intervals": len(errors),
            }
        )
    return rows


def _best_selection_by_target_split(
    condition_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in condition_rows:
        grouped[
            (
                str(row["target"]),
                str(row["split_name"]),
                str(row["model_level"]),
                str(row["feature_group"]),
                str(row["source_report"]),
            )
        ].append(row)
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for (target, split_name, model_level, feature_group, source_report), rows in grouped.items():
        errors = [float(row["condition_mae"]) for row in rows]
        candidate = {
            "target": target,
            "split_name": split_name,
            "model_level": model_level,
            "feature_group": feature_group,
            "source_report": source_report,
            "condition_mean_mae": _mean(errors),
            "worst_condition_mae": max(errors),
            "n_conditions": len(rows),
        }
        key = (target, split_name)
        if key not in best or (
            candidate["condition_mean_mae"],
            candidate["worst_condition_mae"],
        ) < (
            float(best[key]["condition_mean_mae"]),
            float(best[key]["worst_condition_mae"]),
        ):
            best[key] = candidate
    return best


def _paired_best_nonpulse_gain_rows(
    prior_rows: list[dict[str, Any]],
    nonpulse_rows: list[dict[str, Any]],
    best_prior: dict[tuple[str, str], dict[str, Any]],
    best_nonpulse: dict[tuple[str, str], dict[str, Any]],
    metadata: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    prior_lookup = _condition_selection_lookup(prior_rows)
    nonpulse_lookup = _condition_selection_lookup(nonpulse_rows)
    rows = []
    for key in sorted(set(best_prior) & set(best_nonpulse)):
        target, split_name = key
        prior = best_prior[key]
        nonpulse = best_nonpulse[key]
        prior_key = (
            target,
            split_name,
            str(prior["model_level"]),
            str(prior["feature_group"]),
            str(prior["source_report"]),
        )
        nonpulse_key = (
            target,
            split_name,
            str(nonpulse["model_level"]),
            str(nonpulse["feature_group"]),
            str(nonpulse["source_report"]),
        )
        for condition_key in sorted(set(prior_lookup[prior_key]) & set(nonpulse_lookup[nonpulse_key])):
            heldout_fold, parameter_set = condition_key
            prior_row = prior_lookup[prior_key][condition_key]
            nonpulse_row = nonpulse_lookup[nonpulse_key][condition_key]
            meta = metadata.get(parameter_set, {})
            rows.append(
                {
                    "target": target,
                    "split_name": split_name,
                    "heldout_fold": heldout_fold,
                    "parameter_set": parameter_set,
                    "prior_pulse_feature_group": prior["feature_group"],
                    "prior_pulse_source_report": prior["source_report"],
                    "best_nonpulse_feature_group": nonpulse["feature_group"],
                    "best_nonpulse_source_report": nonpulse["source_report"],
                    "best_nonpulse_condition_mae": nonpulse_row["condition_mae"],
                    "prior_pulse_condition_mae": prior_row["condition_mae"],
                    "gain": float(nonpulse_row["condition_mae"]) - float(prior_row["condition_mae"]),
                    "n_intervals": prior_row["n_intervals"],
                    "nominal_temperature_C": meta.get("nominal_temperature_C"),
                    "voltage_window_family": meta.get("voltage_window_family"),
                    "nominal_charge_C_rate": meta.get("nominal_charge_C_rate"),
                    "aging_mode": meta.get("aging_mode"),
                }
            )
    return rows


def _condition_selection_lookup(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str, str, str, str], dict[tuple[int, int], dict[str, Any]]]:
    output: dict[tuple[str, str, str, str, str], dict[tuple[int, int], dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        selection_key = (
            str(row["target"]),
            str(row["split_name"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["source_report"]),
        )
        output[selection_key][(int(row["heldout_fold"]), int(row["parameter_set"]))] = row
    return output


def _all_primary_prediction_keys(
    prediction_rows: list[dict[str, Any]],
) -> set[tuple[str, str, int, str, int, int]]:
    return {
        _prediction_covered_key(row)
        for row in prediction_rows
        if str(row.get("run_scope")) == "primary"
    }


def _prediction_covered_key(row: dict[str, Any]) -> tuple[str, str, int, str, int, int]:
    return (
        str(row["target"]),
        str(row["split_name"]),
        int(row["parameter_set"]),
        str(row["cell_id"]),
        int(row["checkup_k"]),
        int(row["checkup_k_next"]),
    )


def _selection_summary_rows(
    selections: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "target": target,
            "split_name": split_name,
            "model_level": row["model_level"],
            "feature_group": row["feature_group"],
            "source_report": row["source_report"],
            "condition_mean_mae": row["condition_mean_mae"],
            "n_conditions": row["n_conditions"],
        }
        for (target, split_name), row in sorted(selections.items())
    ]


def _prior_pulse_vs_best_nonpulse_claim_rows(
    split_summary: list[dict[str, Any]],
) -> list[dict[str, str]]:
    capacity_c_rate = _summary_row(split_summary, "capacity_Ah_k1", "c_rate_holdout_fold")
    capacity_temp = _summary_row(split_summary, "capacity_Ah_k1", "temperature_holdout_fold")
    capacity_profile = _summary_row(split_summary, "capacity_Ah_k1", "profile_holdout_fold")
    delta_c_rate = _summary_row(split_summary, "delta_capacity_Ah", "c_rate_holdout_fold")
    beats_c_rate = _as_float(capacity_c_rate.get("gain_p05")) > 0
    beats_temp = _as_float(capacity_temp.get("gain_p05")) > 0
    beats_profile = _as_float(capacity_profile.get("gain_p05")) > 0
    delta_beats = _as_float(delta_c_rate.get("gain_p05")) > 0
    return [
        {
            "claim": "Prior PULSE beats strongest non-PULSE for capacity_Ah_k1",
            "status": "supported" if beats_c_rate and (beats_temp or beats_profile) else "not_supported",
            "evidence": (
                f"C-rate p05 {_format_diagnostic_value(capacity_c_rate.get('gain_p05'))}; "
                f"temperature p05 {_format_diagnostic_value(capacity_temp.get('gain_p05'))}; "
                f"profile p05 {_format_diagnostic_value(capacity_profile.get('gain_p05'))}"
            ),
            "decision": "Allow narrow prior-PULSE level-prediction claim"
            if beats_c_rate and (beats_temp or beats_profile)
            else "Claim only improvement over weaker baselines or selected splits",
        },
        {
            "claim": "Prior PULSE beats strongest non-PULSE for delta_capacity_Ah",
            "status": "supported" if delta_beats else "not_supported",
            "evidence": (
                f"C-rate delta mean {_format_diagnostic_value(delta_c_rate.get('mean_gain'))}; "
                f"p05 {_format_diagnostic_value(delta_c_rate.get('gain_p05'))}"
            ),
            "decision": "Do not claim fade-rate improvement" if not delta_beats else "Report cautiously",
        },
        {
            "claim": "Leakage safety",
            "status": "supported",
            "evidence": "Prior-PULSE groups allow `pulse_1s_resistance_k` only.",
            "decision": "Future PULSE state and PULSE deltas remain blocked.",
        },
    ]


def _write_prior_pulse_vs_best_nonpulse_md(
    claim_rows: list[dict[str, str]],
    split_summary: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# Prior-PULSE vs Strongest Non-PULSE Claim Readiness",
        "",
        "This Milestone 0.9.1 report compares prior-PULSE feature groups against",
        "the strongest supplied non-PULSE HGB feature group on the same",
        "PULSE-covered interval population.",
        "",
        "| Claim | Status | Evidence | Decision |",
        "|---|---|---|---|",
    ]
    for row in claim_rows:
        lines.append(
            f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Paired Gain Summary",
            "",
            "| Target | Split | Prior-PULSE group | Non-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in split_summary:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | `{row['prior_pulse_feature_group']}` | "
            f"`{row.get('best_nonpulse_feature_group', 'see_csv')}` | {row['n_conditions']} | "
            f"{_format_diagnostic_value(row['mean_gain'])} | {_format_diagnostic_value(row['gain_p05'])} | "
            f"{_format_diagnostic_value(row['gain_p50'])} | {_format_diagnostic_value(row['gain_p95'])} | "
            f"{_format_diagnostic_value(row['win_rate'])} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _condition_mae_by_fold_for_selection(
    prediction_rows: list[dict[str, Any]],
    *,
    run_scope: str,
    model_level: str,
    feature_group: str,
    target: str,
    split_name: str,
) -> dict[tuple[int, int], dict[str, Any]]:
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
    for row in prediction_rows:
        if (
            str(row["run_scope"]) != run_scope
            or str(row["model_level"]) != model_level
            or str(row["feature_group"]) != feature_group
            or str(row["target"]) != target
            or str(row["split_name"]) != split_name
        ):
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        grouped[(int(row["heldout_fold"]), int(row["parameter_set"]))].append(abs(y_pred - y_true))
    return {
        key: {"mae": _mean(errors), "n_intervals": len(errors)}
        for key, errors in grouped.items()
        if errors
    }


def _prior_pulse_split_gain_summary(
    paired_rows: list[dict[str, Any]],
    bootstrap_resamples: int,
    seed: int,
) -> list[dict[str, Any]]:
    summaries = []
    grouped = _group_by(
        paired_rows,
        lambda row: (row["target"], row["split_name"], row["prior_pulse_feature_group"]),
    )
    for (target, split_name, feature_group), rows in sorted(grouped.items()):
        gains = [float(row["gain"]) for row in rows]
        boot = _bootstrap_gain_summary(rows, bootstrap_resamples, seed)
        summaries.append(
            {
                "target": target,
                "split_name": split_name,
                "prior_pulse_feature_group": feature_group,
                "best_nonpulse_feature_group": rows[0].get("best_nonpulse_feature_group", ""),
                "best_nonpulse_source_report": rows[0].get("best_nonpulse_source_report", ""),
                "n_conditions": len(rows),
                "mean_gain": _mean(gains),
                "median_gain": _median(gains),
                "win_rate": sum(1 for gain in gains if gain > 0) / len(gains),
                "worst_condition_gain": min(gains),
                **boot,
            }
        )
    return summaries


def _bootstrap_gain_summary(
    rows: list[dict[str, Any]],
    resamples: int,
    seed: int,
) -> dict[str, float | int]:
    by_condition = _group_by(rows, lambda row: int(row["parameter_set"]))
    condition_ids = sorted(by_condition)
    rng = random.Random(seed)
    mean_gains = []
    win_rates = []
    for _ in range(max(1, resamples)):
        sampled = [row for _cid in condition_ids for row in by_condition[rng.choice(condition_ids)]]
        gains = [float(row["gain"]) for row in sampled]
        mean_gains.append(_mean(gains))
        win_rates.append(sum(1 for gain in gains if gain > 0) / len(gains))
    return {
        "bootstrap_resamples": resamples,
        "gain_mean": _mean(mean_gains),
        "gain_p05": _quantile(mean_gains, 0.05),
        "gain_p50": _quantile(mean_gains, 0.50),
        "gain_p95": _quantile(mean_gains, 0.95),
        "win_rate_mean": _mean(win_rates),
    }


def _prior_pulse_coverage_summary(
    baseline_report: dict[str, Any],
    prior_report: dict[str, Any],
    baseline_predictions: list[dict[str, Any]],
    prior_predictions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "scope": "report_row_counts",
            "target": "all",
            "split_name": "all",
            "capacity_only_interval_count": baseline_report["row_counts"].get("selected_subset_rows"),
            "pulse_covered_interval_count": prior_report["row_counts"].get("selected_subset_rows"),
            "rows_dropped_by_requiring_prior_pulse": int(
                baseline_report["row_counts"].get("selected_subset_rows", 0)
            )
            - int(prior_report["row_counts"].get("selected_subset_rows", 0)),
            "capacity_only_parameter_sets": baseline_report["row_counts"].get("selected_parameter_sets"),
            "pulse_covered_parameter_sets": prior_report["row_counts"].get("selected_parameter_sets"),
        }
    ]
    baseline_keys = _prediction_interval_keys(
        baseline_predictions,
        feature_group="F4_state_log_age_scalar",
    )
    prior_keys = _prediction_interval_keys(
        prior_predictions,
        feature_group="F4_state_log_age_scalar",
    )
    for (target, split_name), base_keys in sorted(baseline_keys.items()):
        pulse_keys = prior_keys.get((target, split_name), set())
        dropped = base_keys - pulse_keys
        rows.append(
            {
                "scope": "prediction_interval_keys",
                "target": target,
                "split_name": split_name,
                "capacity_only_interval_count": len(base_keys),
                "pulse_covered_interval_count": len(pulse_keys),
                "rows_dropped_by_requiring_prior_pulse": len(dropped),
                "capacity_only_parameter_sets": len({key[0] for key in base_keys}),
                "pulse_covered_parameter_sets": len({key[0] for key in pulse_keys}),
            }
        )
    return rows


def _prediction_interval_keys(
    rows: list[dict[str, Any]],
    *,
    feature_group: str,
) -> dict[tuple[str, str], set[tuple[int, str, int, int]]]:
    grouped: dict[tuple[str, str], set[tuple[int, str, int, int]]] = defaultdict(set)
    for row in rows:
        if (
            str(row.get("run_scope")) != "primary"
            or str(row.get("model_level")) != "L2_hist_gradient_boosting"
            or str(row.get("feature_group")) != feature_group
        ):
            continue
        key = (
            str(row["target"]),
            str(row["split_name"]),
        )
        grouped[key].add(
            (
                int(row["parameter_set"]),
                str(row["cell_id"]),
                int(row["checkup_k"]),
                int(row["checkup_k_next"]),
            )
        )
    return grouped


def _prior_pulse_predictive_claim_rows(
    split_summary: list[dict[str, Any]],
    coverage_summary: list[dict[str, Any]],
) -> list[dict[str, str]]:
    capacity_c_rate = _summary_row(split_summary, "capacity_Ah_k1", "c_rate_holdout_fold")
    capacity_temp = _summary_row(split_summary, "capacity_Ah_k1", "temperature_holdout_fold")
    delta_c_rate = _summary_row(split_summary, "delta_capacity_Ah", "c_rate_holdout_fold")
    coverage = coverage_summary[0] if coverage_summary else {}
    capacity_supported = (
        _as_float(capacity_c_rate.get("gain_p05")) > 0
        and _as_float(capacity_temp.get("gain_p05")) > 0
    )
    delta_supported = _as_float(delta_c_rate.get("gain_p05")) > 0
    return [
        {
            "claim": "Prior PULSE improves capacity_Ah_k1 under OOD splits",
            "status": "supported" if capacity_supported else "partially_supported",
            "evidence": (
                f"C-rate gain mean {_format_diagnostic_value(capacity_c_rate.get('mean_gain'))}, "
                f"bootstrap p05 {_format_diagnostic_value(capacity_c_rate.get('gain_p05'))}; "
                f"temperature p05 {_format_diagnostic_value(capacity_temp.get('gain_p05'))}"
            ),
            "decision": "Allow a narrow level-prediction claim"
            if capacity_supported
            else "Keep as diagnostic until paired uncertainty is stronger",
        },
        {
            "claim": "Prior PULSE improves delta_capacity_Ah",
            "status": "supported" if delta_supported else "not_supported",
            "evidence": (
                f"C-rate delta gain mean {_format_diagnostic_value(delta_c_rate.get('mean_gain'))}, "
                f"bootstrap p05 {_format_diagnostic_value(delta_c_rate.get('gain_p05'))}"
            ),
            "decision": "Do not claim fade-rate improvement" if not delta_supported else "Report cautiously",
        },
        {
            "claim": "Coverage loss changes fold composition",
            "status": "not_supported"
            if int(coverage.get("rows_dropped_by_requiring_prior_pulse", 0)) <= 1
            else "partially_supported",
            "evidence": (
                f"Dropped intervals: {coverage.get('rows_dropped_by_requiring_prior_pulse', 'NA')}; "
                f"parameter sets: {coverage.get('pulse_covered_parameter_sets', 'NA')}"
            ),
            "decision": "Coverage loss is small but must be reported",
        },
        {
            "claim": "Leakage safety",
            "status": "supported",
            "evidence": "Prior-PULSE groups include `pulse_1s_resistance_k` and forbid future PULSE targets.",
            "decision": "Keep future PULSE state and deltas blocked.",
        },
    ]


def _summary_row(
    rows: list[dict[str, Any]],
    target: str,
    split_name: str,
) -> dict[str, Any]:
    return next(
        (row for row in rows if row["target"] == target and row["split_name"] == split_name),
        {},
    )


def _write_prior_pulse_claim_readiness_md(
    claim_rows: list[dict[str, str]],
    split_summary: list[dict[str, Any]],
    coverage_summary: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# Prior-PULSE Capacity Predictive Claim Readiness",
        "",
        "This Milestone 0.9 report tests a narrow non-neural claim: prior PULSE",
        "state at check-up `k` may improve `capacity_Ah_k1` prediction under",
        "grouped validation. It does not authorize broad multimodal claims, future",
        "PULSE leakage, EIS, sequence models, neural models, policy ranking, or CBAT.",
        "",
        "| Claim | Status | Evidence | Decision |",
        "|---|---|---|---|",
    ]
    for row in claim_rows:
        lines.append(
            f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Best Paired Gain Summary",
            "",
            "| Target | Split | Prior-PULSE group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in split_summary:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | `{row['prior_pulse_feature_group']}` | "
            f"{row['n_conditions']} | {_format_diagnostic_value(row['mean_gain'])} | "
            f"{_format_diagnostic_value(row['gain_p05'])} | {_format_diagnostic_value(row['gain_p50'])} | "
            f"{_format_diagnostic_value(row['gain_p95'])} | {_format_diagnostic_value(row['win_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "| Scope | Target | Split | Capacity-only intervals | PULSE-covered intervals | Dropped | Parameter sets |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in coverage_summary:
        lines.append(
            f"| `{row['scope']}` | `{row['target']}` | `{row['split_name']}` | "
            f"{row['capacity_only_interval_count']} | {row['pulse_covered_interval_count']} | "
            f"{row['rows_dropped_by_requiring_prior_pulse']} | {row['pulse_covered_parameter_sets']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _assert_pulse_feature_groups_are_leakage_safe() -> None:
    for feature_group in PULSE_FEATURE_GROUPS:
        fields = set(NUMERIC_FEATURES.get(feature_group, ()))
        forbidden = fields & PULSE_FUTURE_LEAKAGE_FIELDS
        if forbidden:
            raise ValueError(
                f"Feature group {feature_group} contains future PULSE leakage fields: {sorted(forbidden)}"
            )


def _group_by(rows: list[dict[str, Any]], key_fn: Any) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(key_fn(row), []).append(row)
    return grouped


def _format_gain_list(values: list[float | None]) -> str:
    return ", ".join(_format_diagnostic_value(value) for value in values)


def _write_evaluation_cards(
    metrics: list[dict[str, Any]],
    cards_dir: Path,
    report: dict[str, Any],
) -> None:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for metric in metrics:
        key = (
            str(metric["model_level"]),
            str(metric["feature_group"]),
            str(metric["target"]),
            str(metric["split_name"]),
        )
        grouped[key].append(metric)

    for key, group in sorted(grouped.items()):
        model_level, feature_group, target, split_name = key
        primary = [item for item in group if item["run_scope"] == "primary"]
        sensitivity = [
            item for item in group if item["run_scope"] == "sensitivity_excluding_monotonicity"
        ]
        card = {
            "schema_version": SCHEMA_VERSION,
            "model_level": model_level,
            "feature_group": feature_group,
            "target": target,
            "split_name": split_name,
            "row_counts": report["row_counts"],
            "primary_summary": _metric_summary(primary),
            "sensitivity_excluding_monotonicity_summary": _metric_summary(sensitivity),
            "fold_metrics": group,
        }
        filename = "__".join(_slug(part) for part in key) + ".json"
        (cards_dir / filename).write_text(
            json.dumps(card, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _metric_summary(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not metrics:
        return {}
    return {
        "fold_count": len(metrics),
        "mean_mae": _mean([float(item["mae"]) for item in metrics]),
        "mean_rmse": _mean([float(item["rmse"]) for item in metrics]),
        "condition_mean_mae": _mean([float(item["condition_mean_mae"]) for item in metrics]),
        "condition_median_mae": _mean(
            [float(item["condition_median_mae"]) for item in metrics]
        ),
        "worst_condition_mae": max(float(item["worst_condition_mae"]) for item in metrics),
    }


def _write_baseline_summary(
    report: dict[str, Any],
    leaderboard_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    row_counts = report["row_counts"]
    primary_rows = [row for row in leaderboard_rows if row["run_scope"] == "primary"]
    best_rows = sorted(primary_rows, key=lambda row: float(row["condition_mean_mae"]))[:10]
    lines = [
        "# Capacity Baseline Summary",
        "",
        f"Schema version: `{report['schema_version']}`",
        f"Generated at UTC: `{report['generated_at_utc']}`",
        f"Primary subset: `{report['subset']}`",
        "",
        "## Row Counts",
        "",
        "| Count | Value |",
        "|---|---:|",
    ]
    for key, value in row_counts.items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Best Primary Rows",
            "",
            "| Model | Feature group | Target | Split | Condition mean MAE | Worst condition MAE |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for row in best_rows:
        lines.append(
            "| "
            f"`{row['model_level']}` | `{row['feature_group']}` | `{row['target']}` | "
            f"`{row['split_name']}` | {float(row['condition_mean_mae']):.6g} | "
            f"{float(row['worst_condition_mae']):.6g} |"
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `leaderboard.csv`",
            "- `evaluation_cards/*.json`",
            "- `plots/mae_by_model_and_feature.csv`",
            "- `plots/worst_condition_errors.csv`",
            "- `plots/strict_vs_tolerant_delta.csv`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    subset_name: str,
    run_scope: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    feature_group: str,
    target: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row, prediction in zip(test_rows, predictions):
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "subset_name": subset_name,
                "run_scope": run_scope,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": feature_group,
                "target": target,
                "cell_id": row["cell_id"],
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "checkup_k_next": int(row["checkup_k_next"]),
                "sensitivity_flagged_monotonicity": bool(
                    row["sensitivity_flagged_monotonicity"]
                ),
                "y_true": _evaluation_target_value(row, target),
                "y_pred": _as_float(prediction["y_pred"]),
                "y_pred_q10": _nullable_float(prediction.get("y_pred_q10")),
                "y_pred_q50": _nullable_float(prediction.get("y_pred_q50")),
                "y_pred_q90": _nullable_float(prediction.get("y_pred_q90")),
            }
        )
    return rows


def _row_counts(
    all_rows: list[dict[str, Any]],
    subset_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "full_interval_rows": len(all_rows),
        "selected_subset_rows": len(subset_rows),
        "sensitivity_excluding_monotonicity_rows": len(sensitivity_rows),
        "baseline_clean_strict_rows": sum(bool(row["baseline_clean_strict"]) for row in all_rows),
        "baseline_clean_tolerant_rows": sum(
            bool(row["baseline_clean_tolerant"]) for row in all_rows
        ),
        "sensitivity_flagged_monotonicity_rows": sum(
            bool(row["sensitivity_flagged_monotonicity"]) for row in all_rows
        ),
        "selected_cells": len({str(row["cell_id"]) for row in subset_rows}),
        "selected_parameter_sets": len({int(row["parameter_set"]) for row in subset_rows}),
    }


def _load_prediction_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    predictions_path = Path(report["outputs"]["predictions"])
    if not predictions_path.exists():
        return []
    return pq.read_table(predictions_path).to_pylist()


def _condition_metadata_by_parameter_set(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    interval_path = Path(report["inputs"]["interval_table"])
    if not interval_path.exists():
        return {}
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in pq.read_table(interval_path).to_pylist():
        groups[int(row["parameter_set"])].append(row)

    metadata: dict[int, dict[str, Any]] = {}
    for parameter_set, rows in groups.items():
        capacity_values = [_as_float(row.get("capacity_Ah_k")) for row in rows]
        delta_values = [_as_float(row.get("delta_capacity_Ah")) for row in rows]
        finite_capacity = [value for value in capacity_values if math.isfinite(value)]
        finite_delta = [value for value in delta_values if math.isfinite(value)]
        metadata[parameter_set] = {
            "replicate_count": len({str(row["cell_id"]) for row in rows}),
            "aging_mode": _first_non_empty(row.get("aging_mode") for row in rows),
            "nominal_temperature_C": _first_finite(
                _as_float(row.get("nominal_temperature_C")) for row in rows
            ),
            "voltage_window_family": _first_non_empty(
                row.get("voltage_window_family") for row in rows
            ),
            "nominal_charge_C_rate": _first_finite(
                _as_float(row.get("nominal_charge_C_rate")) for row in rows
            ),
            "nominal_discharge_C_rate": _first_finite(
                _as_float(row.get("nominal_discharge_C_rate")) for row in rows
            ),
            "n_intervals": len(rows),
            "capacity_Ah_k_min": min(finite_capacity) if finite_capacity else None,
            "capacity_Ah_k_max": max(finite_capacity) if finite_capacity else None,
            "delta_capacity_Ah_min": min(finite_delta) if finite_delta else None,
            "delta_capacity_Ah_max": max(finite_delta) if finite_delta else None,
        }
    return metadata


def _condition_mae_for_selection(
    prediction_rows: list[dict[str, Any]],
    *,
    run_scope: str,
    model_level: str,
    feature_group: str,
    target: str,
    split_name: str,
) -> dict[int, float]:
    grouped_errors: dict[int, list[float]] = defaultdict(list)
    for row in prediction_rows:
        if (
            str(row["run_scope"]) != run_scope
            or str(row["model_level"]) != model_level
            or str(row["feature_group"]) != feature_group
            or str(row["target"]) != target
            or str(row["split_name"]) != split_name
        ):
            continue
        y_true = _as_float(row.get("y_true"))
        y_pred = _as_float(row.get("y_pred"))
        if not math.isfinite(y_true) or not math.isfinite(y_pred):
            continue
        grouped_errors[int(row["parameter_set"])].append(abs(y_pred - y_true))
    return {
        parameter_set: _mean(errors)
        for parameter_set, errors in grouped_errors.items()
        if errors
    }


def _worst_condition_for_selection(
    prediction_rows: list[dict[str, Any]],
    *,
    run_scope: str,
    model_level: str,
    feature_group: str,
    target: str,
    split_name: str,
) -> tuple[int | None, float | None]:
    errors = _condition_mae_for_selection(
        prediction_rows,
        run_scope=run_scope,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
        split_name=split_name,
    )
    if not errors:
        return None, None
    return max(errors.items(), key=lambda item: item[1])


def _quantile_metrics(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    target: str,
) -> dict[str, float | None]:
    quantile_rows: list[tuple[float, float, float, float]] = []
    for row, prediction in zip(test_rows, predictions):
        y_true = _evaluation_target_value(row, target)
        q10 = _nullable_float(prediction.get("y_pred_q10"))
        q50 = _nullable_float(prediction.get("y_pred_q50"))
        q90 = _nullable_float(prediction.get("y_pred_q90"))
        if (
            not math.isfinite(y_true)
            or q10 is None
            or q50 is None
            or q90 is None
        ):
            return _empty_quantile_metrics()
        quantile_rows.append((y_true, q10, q50, q90))

    if not quantile_rows:
        return _empty_quantile_metrics()
    return {
        "q10_q90_interval_coverage": _mean(
            [1.0 if q10 <= y_true <= q90 else 0.0 for y_true, q10, _, q90 in quantile_rows]
        ),
        "q10_q90_interval_width_mean": _mean(
            [q90 - q10 for _, q10, _, q90 in quantile_rows]
        ),
        "pinball_loss_q10": _mean(
            [_pinball_loss(y_true, q10, 0.1) for y_true, q10, _, _ in quantile_rows]
        ),
        "pinball_loss_q50": _mean(
            [_pinball_loss(y_true, q50, 0.5) for y_true, _, q50, _ in quantile_rows]
        ),
        "pinball_loss_q90": _mean(
            [_pinball_loss(y_true, q90, 0.9) for y_true, _, _, q90 in quantile_rows]
        ),
    }


def _empty_quantile_metrics() -> dict[str, None]:
    return {
        "q10_q90_interval_coverage": None,
        "q10_q90_interval_width_mean": None,
        "pinball_loss_q10": None,
        "pinball_loss_q50": None,
        "pinball_loss_q90": None,
    }


def _pinball_loss(y_true: float, prediction: float, quantile: float) -> float:
    error = y_true - prediction
    return max(quantile * error, (quantile - 1.0) * error)


def _normalize_selection(
    selected: list[str] | None,
    allowed: tuple[str, ...],
    label: str,
    default: tuple[str, ...] | None = None,
) -> list[str]:
    if selected is None:
        return list(default or allowed)
    normalized = [item.strip() for item in selected if item.strip()]
    unknown = sorted(set(normalized) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}(s): {unknown}. Allowed: {list(allowed)}")
    if not normalized:
        raise ValueError(f"At least one {label} must be selected.")
    return normalized


def _preflight_model_dependencies(model_levels: list[str]) -> None:
    if model_levels == ["L0_persistence"]:
        return
    if any(model != "L0_persistence" for model in model_levels):
        _import_sklearn_stack()


def _import_sklearn_stack() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Capacity baselines L1-L3 require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry, or select "
            "`--model-levels L0_persistence` for the dependency-free persistence baseline."
        ) from exc
    return np, Ridge, HistGradientBoostingRegressor


def _persistence_prediction(row: dict[str, Any], target: str) -> dict[str, float | None]:
    if target == "capacity_Ah_k1":
        return _point_prediction(_as_float(row["capacity_Ah_k"]))
    if target in {"delta_capacity_Ah", *RATE_TARGETS}:
        return _point_prediction(0.0)
    raise ValueError(f"Unknown target: {target}")


def _evaluation_target_value(row: dict[str, Any], target: str) -> float:
    if target == "capacity_Ah_k1":
        return _as_float(row.get("capacity_Ah_k1"))
    if target in {"delta_capacity_Ah", *RATE_TARGETS}:
        return _as_float(row.get("delta_capacity_Ah"))
    raise ValueError(f"Unknown target: {target}")


def _training_target_value(row: dict[str, Any], target: str) -> float:
    if target in DIRECT_TARGETS:
        return _as_float(row.get(target))
    delta = _as_float(row.get("delta_capacity_Ah"))
    if target == "delta_capacity_per_day_target":
        return _safe_ratio(delta, _as_float(row.get("calendar_days")))
    if target == "delta_capacity_per_efc_target":
        return _safe_ratio(delta, _as_float(row.get("log_age_efc_delta")))
    raise ValueError(f"Unknown target: {target}")


def _prediction_to_evaluation_space(row: dict[str, Any], target: str, prediction: float) -> float:
    if target in DIRECT_TARGETS:
        return prediction
    if target == "delta_capacity_per_day_target":
        return prediction * _as_float(row.get("calendar_days"))
    if target == "delta_capacity_per_efc_target":
        return prediction * _as_float(row.get("log_age_efc_delta"))
    raise ValueError(f"Unknown target: {target}")


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or abs(denominator) <= 1e-12:
        return math.nan
    return numerator / denominator


def _point_prediction(value: float) -> dict[str, float | None]:
    return {"y_pred": value, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None}


def _default_report_dir(out_path: Path) -> Path:
    stem = out_path.stem
    if stem.endswith("_report"):
        stem = stem[: -len("_report")]
    return out_path.with_name(stem)


def _slug(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace("=", "-")
        .replace(".", "p")
    )


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    numeric = _as_float(value)
    return numeric if math.isfinite(numeric) else None


def _category(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _optional_float(value: Any) -> float | None:
    numeric = _nullable_float(value)
    return numeric


def _format_optional_float(value: Any) -> str:
    numeric = _optional_float(value)
    return "NA" if numeric is None else f"{numeric:.6g}"


def _format_diagnostic_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _format_optional_float(value)


def _mean_optional(values: list[Any]) -> float | None:
    numeric_values = [_nullable_float(value) for value in values]
    finite_values = [value for value in numeric_values if value is not None]
    return _mean(finite_values) if finite_values else None


def _max_optional(values: list[Any]) -> float | None:
    numeric_values = [_nullable_float(value) for value in values]
    finite_values = [value for value in numeric_values if value is not None]
    return max(finite_values) if finite_values else None


def _reference_report_label(reference_report: dict[str, Any] | None) -> str:
    if reference_report is None:
        return "none"
    return str(reference_report.get("outputs", {}).get("report", "provided"))


def _group_value(value: Any) -> str:
    if value is None:
        return "unknown"
    numeric = _nullable_float(value)
    if numeric is not None:
        return f"{numeric:g}"
    text = str(value).strip()
    return text if text else "unknown"


def _interval_count_bucket(value: Any) -> str:
    numeric = _nullable_float(value)
    if numeric is None:
        return "unknown"
    count = int(numeric)
    if count <= 5:
        return "<=5"
    if count <= 10:
        return "6-10"
    if count <= 20:
        return "11-20"
    return ">20"


def _c_rate_bucket(value: Any) -> str:
    numeric = _nullable_float(value)
    if numeric is None:
        return "unknown"
    if numeric < 1.0:
        return "<1C"
    if numeric < 1.5:
        return "1C-1.5C"
    if numeric < 5.0 / 3.0:
        return "1.5C-5over3C"
    return ">=5over3C"


def _value_range_bucket(
    minimum: Any,
    maximum: Any,
    *,
    thresholds: tuple[float, float, float],
    labels: tuple[str, str, str, str],
) -> str:
    values = [_nullable_float(minimum), _nullable_float(maximum)]
    finite_values = [value for value in values if value is not None]
    if not finite_values:
        return "unknown"
    midpoint = sum(finite_values) / len(finite_values)
    if midpoint < thresholds[0]:
        return labels[0]
    if midpoint < thresholds[1]:
        return labels[1]
    if midpoint < thresholds[2]:
        return labels[2]
    return labels[3]


def _first_non_empty(values: Any) -> str | None:
    for value in values:
        text = _category(value)
        if text:
            return text
    return None


def _first_finite(values: Any) -> float | None:
    for value in values:
        if math.isfinite(value):
            return value
    return None


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute mean of empty values.")
    return sum(values) / len(values)


def _median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot compute median of empty values.")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Cannot compute quantile of empty values.")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    weight = pos - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight
