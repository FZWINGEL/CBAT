"""Tests for Milestone 0.5 capacity baseline tooling."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import mbp.baselines.capacity as capacity_module
from mbp.baselines.capacity import BASELINE_PREDICTION_SCHEMA
from mbp.baselines.capacity import DIAGNOSTIC_LEAKAGE_FIELDS
from mbp.baselines.capacity import FEATURE_GROUPS
from mbp.baselines.capacity import FeatureEncoder
from mbp.baselines.capacity import NUMERIC_FEATURES
from mbp.baselines.capacity import assert_no_parameter_set_leakage
from mbp.baselines.capacity import compute_metrics
from mbp.baselines.capacity import load_baseline_rows
from mbp.baselines.capacity import predict_capacity_target
from mbp.baselines.capacity import run_capacity_baselines
from mbp.data.schema_contracts import INTERVAL_SUBSET_REGISTRY_SCHEMA, INTERVAL_TABLE_SCHEMA


def _write_capacity_fixture(tmp_path: Path) -> tuple[Path, Path]:
    interval_rows = []
    subset_rows = []
    aging_modes = {0: "calendar", 1: "cyclic", 2: "profile"}
    voltage_families = {1: "approx_0_100", 2: "approx_10_100", 3: "calendar_soc_50"}
    for parameter_set in range(1, 7):
        condition_fold = (parameter_set - 1) % 3
        temperature_fold = (
            1 if parameter_set in {2, 5} else 2 if parameter_set in {3, 6} else 0
        )
        voltage_fold = ((parameter_set - 1) % 3) + 1
        c_rate_fold = 1 if parameter_set in {5, 6} else 0
        profile_fold = 1 if parameter_set == 6 else 0
        for replicate_id in range(1, 4):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in range(2):
                capacity_k = 3.0 - 0.03 * parameter_set - 0.02 * checkup_k
                capacity_k1 = capacity_k - 0.02 - 0.005 * parameter_set
                flagged = parameter_set == 2 and checkup_k == 0
                interval_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": aging_modes[condition_fold],
                        "nominal_temperature_C": [25.0, 0.0, 40.0][condition_fold],
                        "voltage_window": "2.50 V - 4.20 V",
                        "voltage_window_family": voltage_families[voltage_fold],
                        "soc_window_approx": "50%",
                        "nominal_charge_C_rate": 5.0 / 3.0 if c_rate_fold else 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "WLTP" if profile_fold else "CC",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "t_result_k_s": 100.0 * checkup_k,
                        "t_result_k1_s": 100.0 * (checkup_k + 1),
                        "duration_s": 100.0,
                        "duration_h": 100.0 / 3600.0,
                        "calendar_days": 100.0 / 86400.0,
                        "capacity_Ah_k": capacity_k,
                        "capacity_Ah_k1": capacity_k1,
                        "delta_capacity_Ah": capacity_k1 - capacity_k,
                        "delta_capacity_soh": -0.01,
                        "condition_fold": condition_fold,
                        "temperature_holdout_fold": temperature_fold,
                        "voltage_window_holdout_fold": voltage_fold,
                        "soc_window_holdout_fold": voltage_fold,
                        "c_rate_holdout_fold": c_rate_fold,
                        "profile_holdout_fold": profile_fold,
                        "replicate_calibration_fold": 1 if replicate_id == 3 else 0,
                        "time_horizon_fold": 0,
                        "log_age_row_count": 10,
                        "log_age_elapsed_s": 100.0,
                        "log_age_efc_delta": 0.5 + 0.1 * parameter_set,
                        "log_age_delta_q_Ah": 1.0 + 0.1 * checkup_k,
                        "log_age_mean_voltage_V": 3.5,
                        "log_age_min_voltage_V": 3.3,
                        "log_age_max_voltage_V": 4.0,
                        "log_age_mean_temperature_C": 25.0,
                        "log_age_min_temperature_C": 24.0,
                        "log_age_max_temperature_C": 26.0,
                        "log_age_mean_current_A": -0.5,
                        "log_age_mean_abs_current_A": 0.6,
                        "log_age_max_abs_current_A": 1.0,
                        "log_age_mean_soc": 50.0,
                        "log_age_min_soc": 40.0,
                        "log_age_max_soc": 60.0,
                        "log_age_capacity_diag_rows_masked": 1,
                        "log_age_r0_diag_rows_masked": 1,
                        "log_age_r1_diag_rows_masked": 1,
                        "LOG_AGE_available": True,
                        "log_age_monotonicity_violation_count": 1 if flagged else 0,
                        "log_age_timestamp_decrease_count": 0,
                        "log_age_efc_decrease_count": 1 if flagged else 0,
                        "log_age_max_timestamp_drop_s": 0.0,
                        "log_age_max_efc_drop": 0.0002 if flagged else 0.0,
                        "LOG_AGE_monotonicity_clean": not flagged,
                        "quality_flags": "LOG_AGE_monotonicity_violation" if flagged else "",
                        "schema_version": "gate2.interval.v1",
                    }
                )
                subset_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "interval_id": f"{cell_id}:{checkup_k}->{checkup_k + 1}",
                        "baseline_clean_strict": not flagged,
                        "baseline_clean_tolerant": True,
                        "sensitivity_flagged_monotonicity": flagged,
                        "small_efc_jitter": flagged,
                        "excluded_due_to_large_efc_drop": False,
                        "excluded_due_to_timestamp_drop": False,
                        "excluded_due_to_missing_log_age": False,
                        "excluded_due_to_duration_error": False,
                        "monotonicity_policy_version": "log_age_monotonicity.v1",
                        "schema_version": "gate4.interval_subset.v1",
                    }
                )

    interval_path = tmp_path / "interval_table.parquet"
    subset_path = tmp_path / "interval_subset_registry_v1.parquet"
    pq.write_table(pa.Table.from_pylist(interval_rows, schema=INTERVAL_TABLE_SCHEMA), interval_path)
    pq.write_table(
        pa.Table.from_pylist(subset_rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA),
        subset_path,
    )
    return interval_path, subset_path


def test_capacity_baseline_l0_writes_report_and_predictions(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "capacity_baseline_report.json"
    predictions_path = tmp_path / "capacity_baseline_predictions.parquet"

    report = run_capacity_baselines(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        model_levels=["L0_persistence"],
        feature_groups=["F0_time_only"],
    )

    assert report["status"] == "passed"
    assert report["row_counts"]["full_interval_rows"] == 36
    assert report["row_counts"]["selected_subset_rows"] == 36
    assert report["row_counts"]["sensitivity_flagged_monotonicity_rows"] == 3
    assert len(report["metrics"]) == 40
    prediction_table = pq.read_table(predictions_path)
    assert prediction_table.schema == BASELINE_PREDICTION_SCHEMA
    assert prediction_table.num_rows > 0
    report_dir = tmp_path / "capacity_baseline"
    assert (report_dir / "leaderboard.csv").exists()
    assert (report_dir / "baseline_summary.md").exists()
    assert (report_dir / "plots" / "strict_vs_tolerant_delta.csv").exists()
    assert any((report_dir / "evaluation_cards").glob("*.json"))
    assert {metric["run_scope"] for metric in report["metrics"]} == {
        "primary",
        "sensitivity_excluding_monotonicity",
    }


def test_capacity_baseline_cli_runs_l0_on_synthetic_fixture(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from mbp.cli import app

    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "capacity_baseline_report.json"
    predictions_path = tmp_path / "capacity_baseline_predictions.parquet"

    result = CliRunner().invoke(
        app,
        [
            "baseline",
            "run-capacity",
            "--interval-table",
            str(interval_path),
            "--interval-subsets",
            str(subset_path),
            "--out",
            str(report_path),
            "--predictions-out",
            str(predictions_path),
            "--model-levels",
            "L0_persistence",
        ],
    )

    assert result.exit_code == 0, result.output
    assert report_path.exists()
    assert predictions_path.exists()
    assert "Capacity baseline report generated" in result.output


def test_capacity_baseline_l1_l3_dependency_error_is_actionable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)

    def missing_dependencies() -> tuple[object, object, object]:
        raise RuntimeError("Run `uv sync --extra baseline` and retry")

    monkeypatch.setattr(capacity_module, "_import_sklearn_stack", missing_dependencies)

    with pytest.raises(RuntimeError, match="uv sync --extra baseline"):
        run_capacity_baselines(
            interval_path,
            subset_path,
            tmp_path / "report.json",
            tmp_path / "predictions.parquet",
            model_levels=["L1_ridge"],
        )


def test_state_feature_groups_include_prior_capacity() -> None:
    assert "capacity_Ah_k" not in NUMERIC_FEATURES["F0_time_only"]
    state_groups = [group for group in FEATURE_GROUPS if group != "F0_time_only"]
    assert state_groups
    assert all("capacity_Ah_k" in NUMERIC_FEATURES[group] for group in state_groups)


def test_persistence_predictions_use_prior_capacity_and_zero_delta() -> None:
    rows = [{"capacity_Ah_k": 2.75, "capacity_Ah_k1": 2.5, "delta_capacity_Ah": -0.25}]

    next_capacity = predict_capacity_target(
        model_level="L0_persistence",
        feature_group="persistence",
        train_rows=[],
        test_rows=rows,
        target="capacity_Ah_k1",
        seed=42,
    )
    delta = predict_capacity_target(
        model_level="L0_persistence",
        feature_group="persistence",
        train_rows=[],
        test_rows=rows,
        target="delta_capacity_Ah",
        seed=42,
    )

    assert next_capacity[0]["y_pred"] == 2.75
    assert delta[0]["y_pred"] == 0.0


def test_capacity_baseline_requires_existing_subset_registry(tmp_path: Path) -> None:
    interval_path, _ = _write_capacity_fixture(tmp_path)

    with pytest.raises(FileNotFoundError, match="Interval subset registry not found"):
        load_baseline_rows(interval_path, tmp_path / "missing.parquet", "baseline_clean_tolerant")


def test_capacity_baseline_rejects_zero_row_subset(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    subset_rows = pq.read_table(subset_path).to_pylist()
    for row in subset_rows:
        row["baseline_clean_strict"] = False
    zero_subset_path = tmp_path / "zero_interval_subset_registry.parquet"
    pq.write_table(
        pa.Table.from_pylist(subset_rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA),
        zero_subset_path,
    )

    with pytest.raises(ValueError, match="zero rows"):
        load_baseline_rows(interval_path, zero_subset_path, "baseline_clean_strict")


def test_feature_groups_exclude_inserted_diagnostics(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    _, rows = load_baseline_rows(interval_path, subset_path, "baseline_clean_tolerant")

    for feature_group in FEATURE_GROUPS:
        encoder = FeatureEncoder.fit(rows, feature_group)
        assert not (set(encoder.output_columns) & DIAGNOSTIC_LEAKAGE_FIELDS)


def test_parameter_set_leakage_guard_rejects_overlap() -> None:
    train_rows = [{"parameter_set": 1}, {"parameter_set": 2}]
    test_rows = [{"parameter_set": 2}, {"parameter_set": 3}]

    with pytest.raises(ValueError, match="Parameter-set leakage"):
        assert_no_parameter_set_leakage(train_rows, test_rows, "condition_fold", 0)


def test_condition_level_metrics_are_reported() -> None:
    test_rows = [
        {"parameter_set": 1, "cell_id": "P001_1", "capacity_Ah_k1": 3.0},
        {"parameter_set": 1, "cell_id": "P001_2", "capacity_Ah_k1": 2.8},
        {"parameter_set": 2, "cell_id": "P002_1", "capacity_Ah_k1": 2.0},
    ]
    predictions = [
        {"y_pred": 2.9},
        {"y_pred": 2.6},
        {"y_pred": 1.5},
    ]

    metrics = compute_metrics(
        test_rows,
        predictions,
        target="capacity_Ah_k1",
        subset_name="baseline_clean_tolerant",
        run_scope="primary",
        split_name="condition_fold",
        heldout_fold=0,
        model_level="L0_persistence",
        feature_group="persistence",
        train_rows=[{"parameter_set": 3}],
    )

    assert metrics["mae"] == pytest.approx((0.1 + 0.2 + 0.5) / 3)
    assert metrics["condition_mean_mae"] == pytest.approx((0.15 + 0.5) / 2)
    assert metrics["condition_median_mae"] == pytest.approx((0.15 + 0.5) / 2)
    assert metrics["worst_condition_mae"] == pytest.approx(0.5)
