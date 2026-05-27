from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.baselines.capacity import BASELINE_PREDICTION_SCHEMA
from mbp.baselines.hierarchical_capacity import (
    SCHEMA_VERSION,
    fit_train_residual_pool,
    pool_offset_for_row,
    pooling_keys,
    replicate_interval_radius,
    run_hierarchical_capacity,
)


def _write_capacity_fixture(tmp_path: Path) -> tuple[Path, Path]:
    interval_rows: list[dict[str, object]] = []
    subset_rows: list[dict[str, object]] = []
    for parameter_set in range(1, 7):
        condition_fold = (parameter_set - 1) % 3
        c_rate_fold = 1 if parameter_set in {5, 6} else 0
        profile_fold = 1 if parameter_set == 6 else 0
        for replicate_id in range(1, 4):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in range(2):
                capacity_k = 3.0 - 0.025 * parameter_set - 0.02 * checkup_k
                c_rate_drop = 0.07 if c_rate_fold else 0.02
                replicate_shift = 0.002 * (replicate_id - 2)
                capacity_k1 = capacity_k - c_rate_drop - 0.003 * parameter_set + replicate_shift
                flagged = parameter_set == 2 and checkup_k == 0
                interval_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": "cyclic" if parameter_set <= 5 else "profile",
                        "nominal_temperature_C": 25.0 if parameter_set <= 3 else 40.0,
                        "voltage_window": "2.50 V - 4.20 V",
                        "voltage_window_family": "approx_0_100",
                        "soc_window_approx": "50%",
                        "nominal_charge_C_rate": 5.0 / 3.0 if c_rate_fold else 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "WLTP" if profile_fold else "CC",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "duration_h": 1.0,
                        "calendar_days": 1.0 / 24.0,
                        "capacity_Ah_k": capacity_k,
                        "capacity_Ah_k1": capacity_k1,
                        "delta_capacity_Ah": capacity_k1 - capacity_k,
                        "condition_fold": condition_fold,
                        "temperature_holdout_fold": 1 if parameter_set >= 4 else 0,
                        "c_rate_holdout_fold": c_rate_fold,
                        "profile_holdout_fold": profile_fold,
                        "voltage_window_holdout_fold": 1 if parameter_set in {3, 6} else 0,
                        "log_age_efc_delta": 0.5 + 0.1 * parameter_set,
                        "log_age_delta_q_Ah": 1.0 + 0.1 * checkup_k,
                        "log_age_mean_voltage_V": 3.5,
                        "log_age_min_voltage_V": 3.2,
                        "log_age_max_voltage_V": 4.1,
                        "log_age_mean_temperature_C": 25.0,
                        "log_age_min_temperature_C": 24.0,
                        "log_age_max_temperature_C": 42.0 if parameter_set >= 4 else 26.0,
                        "log_age_mean_current_A": -0.5,
                        "log_age_mean_abs_current_A": 0.7,
                        "log_age_max_abs_current_A": 1.6 if c_rate_fold else 1.0,
                        "log_age_mean_soc": 50.0,
                        "log_age_min_soc": 40.0,
                        "log_age_max_soc": 80.0,
                        "quality_flags": "LOG_AGE_monotonicity_violation" if flagged else "",
                        "schema_version": "synthetic",
                    }
                )
                subset_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "baseline_clean_tolerant": True,
                        "baseline_clean_strict": not flagged,
                        "sensitivity_flagged_monotonicity": flagged,
                        "schema_version": "synthetic",
                    }
                )
    interval_path = tmp_path / "interval_table.parquet"
    subset_path = tmp_path / "interval_subset_registry_v1.parquet"
    pq.write_table(pa.Table.from_pylist(interval_rows), interval_path)
    pq.write_table(pa.Table.from_pylist(subset_rows), subset_path)
    return interval_path, subset_path


def test_pooling_keys_exclude_cell_and_parameter_set() -> None:
    row = {
        "cell_id": "P001_1",
        "parameter_set": 1,
        "aging_mode": "cyclic",
        "nominal_temperature_C": 25.0,
        "nominal_charge_C_rate": 1.0,
        "nominal_discharge_C_rate": 1.0,
        "profile_label": "CC",
        "voltage_window_family": "approx_0_100",
    }

    flattened = {part for key in pooling_keys(row) for part in key}

    assert "P001_1" not in flattened
    assert "1" not in flattened
    assert "parameter_set" not in flattened


def test_residual_pool_uses_train_offsets_and_unseen_groups_fallback() -> None:
    train_rows = [
        {
            "capacity_Ah_k1": 1.2,
            "delta_capacity_Ah": -0.1,
            "aging_mode": "cyclic",
            "nominal_temperature_C": 25.0,
            "nominal_charge_C_rate": 1.0,
            "nominal_discharge_C_rate": 1.0,
            "profile_label": "CC",
            "voltage_window_family": "A",
        },
        {
            "capacity_Ah_k1": 1.4,
            "delta_capacity_Ah": -0.1,
            "aging_mode": "cyclic",
            "nominal_temperature_C": 25.0,
            "nominal_charge_C_rate": 1.0,
            "nominal_discharge_C_rate": 1.0,
            "profile_label": "CC",
            "voltage_window_family": "A",
        },
    ]
    predictions = [
        {"y_pred": 1.0, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None},
        {"y_pred": 1.0, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None},
    ]

    pool = fit_train_residual_pool(
        train_rows,
        predictions,
        target="capacity_Ah_k1",
        shrinkage_strength=0.0,
        min_pool_count=2,
    )
    seen_offset, seen_specific = pool_offset_for_row(train_rows[0], pool)
    unseen_offset, unseen_specific = pool_offset_for_row(
        {
            **train_rows[0],
            "aging_mode": "calendar",
            "nominal_temperature_C": 0.0,
            "nominal_charge_C_rate": 5.0 / 3.0,
            "profile_label": "WLTP",
            "voltage_window_family": "B",
        },
        pool,
    )

    assert seen_specific is True
    assert seen_offset == pytest.approx(0.3)
    assert unseen_specific is False
    assert unseen_offset == pytest.approx(0.3)


def test_replicate_interval_radius_uses_train_residuals_and_spread() -> None:
    train_rows = []
    for replicate_id, value in enumerate((1.0, 1.2, 1.4), start=1):
        train_rows.append(
            {
                "parameter_set": 1,
                "replicate_id": replicate_id,
                "checkup_k_next": 2,
                "capacity_Ah_k1": value,
                "delta_capacity_Ah": -0.1,
            }
        )

    radius = replicate_interval_radius(
        train_rows,
        residuals=[0.02, -0.03, 0.01],
        target="capacity_Ah_k1",
    )

    assert radius == pytest.approx(0.2)


def test_hierarchical_capacity_runner_and_reports(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "hierarchical_report.json"
    predictions_path = tmp_path / "hierarchical_predictions.parquet"
    out_dir = tmp_path / "hierarchical"

    report = run_hierarchical_capacity(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        out_dir=out_dir,
        hgb_max_iter=3,
        model_levels=[
            "H0_global_train_mean",
            "H1_state_time_ridge",
            "H2_partial_pooling_ridge",
            "H3_hgb_reference",
            "H4_hgb_residual_partial_pooling",
            "H5_replicate_variance_interval",
        ],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold", "c_rate_holdout_fold"],
    )

    table = pq.read_table(predictions_path)

    assert report["status"] == "passed"
    assert report["row_counts"]["metrics"] > 0
    assert table.schema.remove_metadata() == BASELINE_PREDICTION_SCHEMA
    assert table.schema.metadata[b"schema_version"] == SCHEMA_VERSION.encode()
    assert (out_dir / "leaderboard.csv").exists()
    assert (out_dir / "hierarchical_claim_readiness.md").exists()
    assert (out_dir / "plots" / "c_rate_hierarchical_gain.csv").exists()
