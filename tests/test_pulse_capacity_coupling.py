from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pytest

import mbp.baselines.capacity as capacity_module
from mbp.baselines.capacity import compare_prior_pulse_capacity_reports
from mbp.baselines.capacity import compare_prior_pulse_vs_best_nonpulse_reports
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
    bootstrap_md = (tmp_path / "robustness" / "bootstrap_correlation_summary.md").read_text(
        encoding="utf-8"
    )
    assert "| Level | Pulse | Residual | Correlation | Resamples | Mean | p05 | p50 | p95 |" in bootstrap_md


def test_prior_pulse_capacity_comparison_renders_paired_gains(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    pulse_targets = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, pulse_targets)
    baseline_report = tmp_path / "baseline_report.json"
    baseline_predictions = tmp_path / "baseline_predictions.parquet"
    prior_report = tmp_path / "prior_report.json"
    prior_predictions = tmp_path / "prior_predictions.parquet"
    run_capacity_baselines(
        interval_path,
        subset_path,
        baseline_report,
        baseline_predictions,
        model_levels=["L2_hist_gradient_boosting"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["capacity_Ah_k1", "delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=2,
    )
    run_capacity_baselines(
        interval_path,
        subset_path,
        prior_report,
        prior_predictions,
        pulse_targets_path=pulse_targets,
        model_levels=["L2_hist_gradient_boosting"],
        feature_groups=["F4_state_log_age_scalar", "C_P0_state_time_pulse"],
        targets=["capacity_Ah_k1", "delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=2,
    )

    report = compare_prior_pulse_capacity_reports(
        baseline_report,
        prior_report,
        tmp_path / "compare",
        bootstrap_resamples=10,
        seed=11,
    )

    assert report["row_counts"]["paired_condition_gain_rows"] > 0
    assert (tmp_path / "compare" / "paired_condition_gain.csv").exists()
    assert (tmp_path / "compare" / "split_level_gain_summary.csv").exists()
    assert (tmp_path / "compare" / "coverage_effect_summary.csv").exists()
    assert (tmp_path / "compare" / "prior_pulse_predictive_claim_readiness.md").exists()


def test_prior_pulse_comparison_leakage_guard_catches_future_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        capacity_module.NUMERIC_FEATURES,
        "C_P0_state_time_pulse",
        (*capacity_module.NUMERIC_FEATURES["C_P0_state_time_pulse"], "delta_pulse_1s_resistance"),
    )

    with pytest.raises(ValueError, match="future PULSE leakage"):
        compare_prior_pulse_capacity_reports(
            tmp_path / "missing_baseline.json",
            tmp_path / "missing_prior.json",
            tmp_path / "compare",
        )


def test_prior_pulse_vs_best_nonpulse_comparison_renders(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    pulse_targets = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, pulse_targets)
    nonpulse_report = tmp_path / "nonpulse_report.json"
    nonpulse_predictions = tmp_path / "nonpulse_predictions.parquet"
    prior_report = tmp_path / "prior_report.json"
    prior_predictions = tmp_path / "prior_predictions.parquet"
    run_capacity_baselines(
        interval_path,
        subset_path,
        nonpulse_report,
        nonpulse_predictions,
        model_levels=["L2_hist_gradient_boosting"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["capacity_Ah_k1", "delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=2,
    )
    run_capacity_baselines(
        interval_path,
        subset_path,
        prior_report,
        prior_predictions,
        pulse_targets_path=pulse_targets,
        model_levels=["L2_hist_gradient_boosting"],
        feature_groups=["F4_state_log_age_scalar", "C_P0_state_time_pulse"],
        targets=["capacity_Ah_k1", "delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=2,
    )

    report = compare_prior_pulse_vs_best_nonpulse_reports(
        [nonpulse_report],
        prior_report,
        tmp_path / "best_nonpulse",
        bootstrap_resamples=10,
        seed=13,
    )

    assert report["row_counts"]["paired_gain_rows"] > 0
    assert (tmp_path / "best_nonpulse" / "paired_gain_vs_best_nonpulse.csv").exists()
    assert (tmp_path / "best_nonpulse" / "split_level_gain_vs_best_nonpulse.csv").exists()
    assert (tmp_path / "best_nonpulse" / "prior_pulse_vs_best_nonpulse_claim_readiness.md").exists()
