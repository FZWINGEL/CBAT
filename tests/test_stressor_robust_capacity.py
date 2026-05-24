from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import BASELINE_PREDICTION_SCHEMA
from mbp.baselines.stressor_robust_capacity import (
    condition_balanced_weights,
    diagnose_stressor_robustness,
    paired_condition_gain_rows,
    run_stressor_robust_capacity,
    stressor_balanced_weights,
)
from mbp.baselines.stressor_robust_capacity import _internal_condition_validation_split


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
                capacity_k = 3.0 - 0.03 * parameter_set - 0.02 * checkup_k
                extra_drop = 0.06 if c_rate_fold else 0.02
                capacity_k1 = capacity_k - extra_drop - 0.003 * parameter_set
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


def test_condition_balanced_weights_equalize_parameter_sets() -> None:
    rows = [{"parameter_set": 1}, {"parameter_set": 1}, {"parameter_set": 2}]
    weights = condition_balanced_weights(rows)
    total_by_condition = {
        parameter_set: sum(weight for row, weight in zip(rows, weights) if row["parameter_set"] == parameter_set)
        for parameter_set in {1, 2}
    }
    assert abs(total_by_condition[1] - total_by_condition[2]) < 1e-12


def test_stressor_balanced_weights_use_training_rows_only() -> None:
    rows = [
        {"parameter_set": 1, "nominal_charge_C_rate": 1.0, "nominal_discharge_C_rate": 1.0},
        {"parameter_set": 2, "nominal_charge_C_rate": 1.0, "nominal_discharge_C_rate": 1.0},
        {"parameter_set": 3, "nominal_charge_C_rate": 5.0 / 3.0, "nominal_discharge_C_rate": 1.0},
    ]
    weights = stressor_balanced_weights(rows, "c_rate_holdout_fold")
    assert weights[0] == weights[1]
    assert weights[2] > weights[0]


def test_internal_validation_split_keeps_conditions_disjoint() -> None:
    rows = [{"parameter_set": parameter_set} for parameter_set in range(1, 8)]
    fit_rows, validation_rows = _internal_condition_validation_split(rows, seed=1)
    fit_sets = {row["parameter_set"] for row in fit_rows}
    validation_sets = {row["parameter_set"] for row in validation_rows}
    assert fit_sets
    assert validation_sets
    assert not fit_sets & validation_sets


def test_paired_condition_gains_compare_cross_feature_references() -> None:
    predictions: list[dict[str, object]] = []
    for parameter_set in (1, 2):
        for feature_group, y_pred in (
            ("F4_state_log_age_scalar", 2.0),
            ("F8_timestamp_weighted_stress", 3.0),
        ):
            predictions.append(
                {
                    "run_scope": "primary",
                    "split_name": "c_rate_holdout_fold",
                    "target": "delta_capacity_Ah",
                    "model_level": "R0_reference_hgb50",
                    "feature_group": feature_group,
                    "heldout_fold": 0,
                    "parameter_set": parameter_set,
                    "y_true": 0.0,
                    "y_pred": y_pred,
                }
            )
        predictions.append(
            {
                "run_scope": "primary",
                "split_name": "c_rate_holdout_fold",
                "target": "delta_capacity_Ah",
                "model_level": "R2_stressor_balanced_hgb",
                "feature_group": "F8_timestamp_weighted_stress",
                "heldout_fold": 0,
                "parameter_set": parameter_set,
                "y_true": 0.0,
                "y_pred": 1.0,
            }
        )

    rows = paired_condition_gain_rows(predictions)

    assert {row["reference_feature_group"] for row in rows} == {
        "F4_state_log_age_scalar",
        "F8_timestamp_weighted_stress",
    }
    assert {row["candidate_feature_group"] for row in rows} == {"F8_timestamp_weighted_stress"}
    assert len(rows) == 4


def test_stressor_robust_capacity_runner_and_diagnostics(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "stressor_robust_report.json"
    predictions_path = tmp_path / "stressor_robust_predictions.parquet"
    out_dir = tmp_path / "stressor_robust"

    report = run_stressor_robust_capacity(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        out_dir=out_dir,
        model_levels=["R0_reference_hgb50", "R1_condition_balanced_hgb", "R4_worst_fold_selected_hgb"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=3,
        bag_count=2,
    )

    assert report["status"] == "passed"
    assert report["row_counts"]["metrics"] > 0
    assert pq.read_table(predictions_path).schema == BASELINE_PREDICTION_SCHEMA
    assert (out_dir / "stressor_robustness_claim_readiness.md").exists()
    result = diagnose_stressor_robustness(report_path, predictions_path, tmp_path / "diagnostics", bootstrap_resamples=10)
    assert result["row_counts"]["leaderboard_rows"] > 0
    assert (tmp_path / "diagnostics" / "paired_condition_gains.csv").exists()
