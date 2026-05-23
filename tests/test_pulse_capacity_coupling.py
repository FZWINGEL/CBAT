from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from mbp.baselines.capacity import run_capacity_baselines
from mbp.coupling.pulse_capacity import (
    build_capacity_pulse_coupling_table,
    write_pulse_capacity_diagnostics,
    write_pulse_capacity_robustness_diagnostics,
)
from mbp.data.products.pulse_targets import build_pulse_target_table
from test_pulse_baselines import _write_subset_registry
from test_pulse_targets import _write_pulse_fixture


def test_coupling_table_and_diagnostics_render(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    pulse_targets = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, pulse_targets)
    coupling_table = tmp_path / "capacity_pulse_coupling_table.parquet"

    table = build_capacity_pulse_coupling_table(interval_path, pulse_targets, coupling_table)

    assert table.num_rows > 0
    rows = pq.read_table(coupling_table).to_pylist()
    assert "delta_pulse_1s_resistance" in rows[0]
    assert "delta_capacity_Ah" in rows[0]

    capacity_report = tmp_path / "capacity_report.json"
    capacity_predictions = tmp_path / "capacity_predictions.parquet"
    run_capacity_baselines(
        interval_path,
        subset_path,
        capacity_report,
        capacity_predictions,
        model_levels=["L0_persistence"],
        feature_groups=["F1_state_time"],
        targets=["capacity_Ah_k1"],
        split_views=["condition_fold"],
    )

    report = write_pulse_capacity_diagnostics(
        capacity_report,
        capacity_predictions,
        pulse_targets,
        interval_path,
        tmp_path / "coupling",
        coupling_table_out=tmp_path / "coupling_table.parquet",
    )

    assert report["row_counts"]["coupling_rows"] > 0
    assert (tmp_path / "coupling" / "pulse_capacity_correlation.md").exists()
    assert (tmp_path / "coupling" / "plots" / "capacity_residual_vs_delta_pulse.csv").exists()


def test_capacity_runner_joins_prior_pulse_without_future_targets(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    pulse_targets = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, pulse_targets)

    report = run_capacity_baselines(
        interval_path,
        subset_path,
        tmp_path / "capacity_pulse_report.json",
        tmp_path / "capacity_pulse_predictions.parquet",
        pulse_targets_path=pulse_targets,
        model_levels=["L0_persistence"],
        feature_groups=["C_P0_state_time_pulse"],
        targets=["capacity_Ah_k1"],
        split_views=["condition_fold"],
    )

    assert report["inputs"]["pulse_targets"] == str(pulse_targets)
    assert report["row_counts"]["selected_subset_rows"] > 0


def test_coupling_robustness_outputs_canonical_interval_condition_views(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    pulse_targets = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, pulse_targets)
    capacity_report = tmp_path / "capacity_report.json"
    capacity_predictions = tmp_path / "capacity_predictions.parquet"
    run_capacity_baselines(
        interval_path,
        subset_path,
        capacity_report,
        capacity_predictions,
        model_levels=["L0_persistence"],
        feature_groups=["F1_state_time"],
        targets=["capacity_Ah_k1"],
        split_views=["condition_fold"],
    )

    report = write_pulse_capacity_robustness_diagnostics(
        capacity_report,
        capacity_predictions,
        pulse_targets,
        interval_path,
        tmp_path / "robustness",
        model_level="L0_persistence",
        feature_group="persistence",
        target="capacity_Ah_k1",
        split="condition_fold",
        bootstrap_resamples=10,
        seed=7,
    )

    assert report["row_counts"]["canonical_prediction_rows"] > 0
    assert report["row_counts"]["interval_rows"] > 0
    assert report["row_counts"]["condition_rows"] > 0
    assert (tmp_path / "robustness" / "canonical_model_correlation.md").exists()
    assert (tmp_path / "robustness" / "interval_level_correlation.md").exists()
    assert (tmp_path / "robustness" / "condition_level_correlation.md").exists()
    assert (tmp_path / "robustness" / "bootstrap_correlation_summary.md").exists()
    assert (tmp_path / "robustness" / "residualized_correlation.md").exists()
    assert (tmp_path / "robustness" / "coupling_claim_readiness.md").exists()
