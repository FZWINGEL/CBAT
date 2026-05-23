from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.pulse import FEATURE_GROUPS, NUMERIC_FEATURES, load_pulse_rows, run_pulse_baselines
from mbp.data.schema_contracts import INTERVAL_SUBSET_REGISTRY_SCHEMA
from test_pulse_targets import _write_pulse_fixture
from mbp.data.products.pulse_targets import build_pulse_target_table


def _write_subset_registry(interval_path: Path, tmp_path: Path) -> Path:
    rows = []
    for row in pq.read_table(interval_path).to_pylist():
        rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "checkup_k_next": row["checkup_k_next"],
                "interval_id": f"{row['cell_id']}:{row['checkup_k']}->{row['checkup_k_next']}",
                "baseline_clean_strict": True,
                "baseline_clean_tolerant": True,
                "sensitivity_flagged_monotonicity": False,
                "small_efc_jitter": False,
                "excluded_due_to_large_efc_drop": False,
                "excluded_due_to_timestamp_drop": False,
                "excluded_due_to_missing_log_age": False,
                "excluded_due_to_duration_error": False,
                "monotonicity_policy_version": "test",
                "schema_version": "test",
            }
        )
    path = tmp_path / "subsets.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=INTERVAL_SUBSET_REGISTRY_SCHEMA), path)
    return path


def test_pulse_loader_joins_interval_subset_and_targets(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    targets_path = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, targets_path)

    _, selected = load_pulse_rows(interval_path, subset_path, targets_path, "baseline_clean_tolerant")

    assert selected
    assert "delta_pulse_1s_resistance" in selected[0]
    assert selected[0]["pulse_1s_resistance_k"] is not None


def test_pulse_baseline_l0_runs_grouped_splits(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    targets_path = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, targets_path)

    report = run_pulse_baselines(
        interval_path,
        subset_path,
        targets_path,
        tmp_path / "pulse_report.json",
        tmp_path / "pulse_predictions.parquet",
        model_levels=["L0_persistence"],
        feature_groups=["P0_persistence"],
        split_views=["condition_fold", "c_rate_holdout_fold"],
    )

    assert report["status"] == "passed"
    assert report["metrics"]
    assert (tmp_path / "pulse" / "leaderboard.csv").exists()
    assert (tmp_path / "pulse" / "pulse_diagnostics.md").exists()
    assert (tmp_path / "pulse" / "pulse_claim_readiness.md").exists()


def test_pulse_baseline_alignment_threshold_filters_rows(tmp_path: Path) -> None:
    pulse_summary, _, interval_path = _write_pulse_fixture(tmp_path)
    subset_path = _write_subset_registry(interval_path, tmp_path)
    targets_path = tmp_path / "pulse_targets.parquet"
    build_pulse_target_table(pulse_summary, interval_path, targets_path)

    report = run_pulse_baselines(
        interval_path,
        subset_path,
        targets_path,
        tmp_path / "pulse_threshold_report.json",
        tmp_path / "pulse_threshold_predictions.parquet",
        model_levels=["L0_persistence"],
        feature_groups=["P0_persistence"],
        split_views=["condition_fold"],
        max_alignment_delta_s=12.0,
    )

    assert report["max_alignment_delta_s"] == 12.0
    assert report["row_counts"]["selected_subset_rows"] == 12


def test_pulse_feature_groups_exclude_eis_fields() -> None:
    forbidden = {"z_real", "z_imag", "z_abs", "phase", "frequency_Hz"}
    for feature_group in FEATURE_GROUPS:
        assert not (set(NUMERIC_FEATURES[feature_group]) & forbidden)
