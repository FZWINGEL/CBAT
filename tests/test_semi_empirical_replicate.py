from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.replicate_uncertainty import (
    model_error_vs_replicate_spread_rows,
    replicate_spread_rows,
)
from mbp.analysis.calibration import calibration_rows, interval_width_summary_rows
from mbp.baselines.semi_empirical import (
    NUMERIC_FEATURES,
    TARGET_DERIVED_FORBIDDEN,
    run_semi_empirical_baselines,
)


def _interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set in (1, 2):
        for replicate_id in (1, 2, 3):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in (0, 1):
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 10.0 if parameter_set == 2 else 25.0,
                        "voltage_window_family": "approx_0_100",
                        "nominal_charge_C_rate": 1.5 if parameter_set == 2 else 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "duration_h": 24.0,
                        "calendar_days": 1.0,
                        "capacity_Ah_k": 3.0 - 0.05 * checkup_k,
                        "capacity_Ah_k1": 2.95 - 0.05 * checkup_k - 0.005 * replicate_id,
                        "delta_capacity_Ah": -0.05 - 0.005 * replicate_id,
                        "log_age_efc_delta": 1.0 + checkup_k,
                        "log_age_delta_q_Ah": 3.0,
                        "log_age_mean_temperature_C": 10.0 if parameter_set == 2 else 25.0,
                        "log_age_max_temperature_C": 12.0 if parameter_set == 2 else 27.0,
                        "log_age_mean_voltage_V": 3.7,
                        "log_age_max_voltage_V": 4.1,
                        "condition_fold": parameter_set - 1,
                        "temperature_holdout_fold": parameter_set - 1,
                        "c_rate_holdout_fold": parameter_set - 1,
                        "profile_holdout_fold": parameter_set - 1,
                        "voltage_window_holdout_fold": parameter_set - 1,
                        "sensitivity_flagged_monotonicity": False,
                    }
                )
    return rows


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    rows = _interval_rows()
    interval = tmp_path / "interval.parquet"
    subsets = tmp_path / "subsets.parquet"
    stress = tmp_path / "stress.parquet"
    pq.write_table(pa.Table.from_pylist(rows), interval)
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "cell_id": row["cell_id"],
                    "parameter_set": row["parameter_set"],
                    "replicate_id": row["replicate_id"],
                    "checkup_k": row["checkup_k"],
                    "checkup_k_next": row["checkup_k_next"],
                    "baseline_clean_tolerant": True,
                    "baseline_clean_strict": True,
                    "sensitivity_flagged_monotonicity": False,
                }
                for row in rows
            ]
        ),
        subsets,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "cell_id": row["cell_id"],
                    "parameter_set": row["parameter_set"],
                    "replicate_id": row["replicate_id"],
                    "checkup_k": row["checkup_k"],
                    "checkup_k_next": row["checkup_k_next"],
                    "high_voltage_time_h": 1.0,
                    "cold_time_h": 2.0 if row["parameter_set"] == 2 else 0.0,
                    "hot_time_h": 0.0,
                    "abs_current_ge_1p5C_time_h": 0.5,
                    "cold_high_abs_current_time_h": 0.25 if row["parameter_set"] == 2 else 0.0,
                    "high_voltage_hot_time_h": 0.0,
                    "high_soc_hot_time_h": 0.0,
                }
                for row in rows
            ]
        ),
        stress,
    )
    return interval, subsets, stress


def test_semi_empirical_excludes_target_derived_features() -> None:
    for features in NUMERIC_FEATURES.values():
        assert not (set(features) & TARGET_DERIVED_FORBIDDEN)


def test_semi_empirical_baseline_runs_synthetic_grouped_split(tmp_path: Path) -> None:
    interval, subsets, stress = _write_inputs(tmp_path)
    report = run_semi_empirical_baselines(
        interval,
        subsets,
        stress,
        tmp_path / "semi.json",
        tmp_path / "semi_predictions.parquet",
        feature_groups=["SE0_time_efc", "SE4_coupled_stress"],
        targets=["capacity_Ah_k1"],
        split_views=["condition_fold"],
    )
    assert report["status"] == "passed"
    assert report["row_counts"]["selected_parameter_sets"] == 2
    assert (tmp_path / "semi_predictions.parquet").exists()


def test_replicate_spread_and_model_error_diagnostics() -> None:
    rows = _interval_rows()
    spread = replicate_spread_rows(rows)
    assert spread
    assert any(float(row["replicate_spread"]) > 0 for row in spread)
    predictions = [
        {
            "run_scope": "primary",
            "target": "capacity_Ah_k1",
            "split_name": "condition_fold",
            "model_level": "L2_hist_gradient_boosting",
            "feature_group": "F4_state_log_age_scalar",
            "parameter_set": row["parameter_set"],
            "checkup_k_next": row["checkup_k_next"],
            "y_true": row["capacity_Ah_k1"],
            "y_pred": float(row["capacity_Ah_k1"]) + 0.01,
        }
        for row in rows
    ]
    error_rows = model_error_vs_replicate_spread_rows(predictions, spread)
    assert error_rows
    assert {"model_mae", "mean_replicate_spread"} <= set(error_rows[0])


def test_grouped_conformal_excludes_test_parameter_sets() -> None:
    predictions: list[dict[str, object]] = []
    for parameter_set, heldout_fold, error in (
        (1, 0, 9.0),
        (2, 1, 0.1),
        (3, 2, 0.2),
    ):
        for checkup_k in (0, 1):
            y_true = 1.0
            predictions.append(
                {
                    "run_scope": "primary",
                    "target": "capacity_Ah_k1",
                    "split_name": "condition_fold",
                    "heldout_fold": heldout_fold,
                    "model_level": "L2_hist_gradient_boosting",
                    "feature_group": "F4_state_log_age_scalar",
                    "parameter_set": parameter_set,
                    "checkup_k_next": checkup_k + 1,
                    "y_true": y_true,
                    "y_pred": y_true + error,
                }
            )
    spread_lookup = {
        (parameter_set, checkup_k, "capacity_Ah_k1"): 0.05
        for parameter_set in (1, 2, 3)
        for checkup_k in (1, 2)
    }
    split_rows, condition_rows = calibration_rows(
        predictions,
        spread_lookup,
        nominal_coverage=0.9,
        min_calibration_conditions=2,
    )
    q1 = [
        row
        for row in split_rows
        if row["method"] == "Q1_split_conformal_abs_residual"
        and row["target"] == "capacity_Ah_k1"
        and row["heldout_fold"] == 0
    ][0]
    assert q1["n_calibration_conditions"] == 2
    assert float(q1["conformal_radius"]) < 1.0
    assert q1["calibration_source"] == "same_split_excluding_test_conditions"
    assert condition_rows


def test_interval_width_summary_and_hybrid_rows_render() -> None:
    predictions: list[dict[str, object]] = []
    for parameter_set, heldout_fold in ((1, 0), (2, 1), (3, 2)):
        predictions.append(
            {
                "run_scope": "primary",
                "target": "delta_capacity_Ah",
                "split_name": "condition_fold",
                "heldout_fold": heldout_fold,
                "model_level": "L2_hist_gradient_boosting",
                "feature_group": "F4_state_log_age_scalar",
                "parameter_set": parameter_set,
                "checkup_k_next": 1,
                "y_true": -0.1,
                "y_pred": -0.11,
            }
        )
    spread_lookup = {
        (parameter_set, 1, "delta_capacity_Ah"): 0.2 for parameter_set in (1, 2, 3)
    }
    split_rows, _ = calibration_rows(
        predictions,
        spread_lookup,
        nominal_coverage=0.9,
        min_calibration_conditions=2,
    )
    hybrid = [row for row in split_rows if row["method"] == "Q3_replicate_tolerance_hybrid"]
    assert hybrid
    assert all(float(row["replicate_radius"]) == 0.2 for row in hybrid)
    width_rows = interval_width_summary_rows(split_rows)
    assert width_rows
    assert {"mean_interval_width", "interval_score"} <= set(width_rows[0])
