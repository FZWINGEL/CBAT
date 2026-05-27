import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from mbp.baselines import minimal_sequence
from mbp.baselines.minimal_sequence import run_minimal_sequence_reopening
from mbp.cli import app
from mbp.data.products.event_sequences import (
    EVENT_FEATURE_COLUMNS,
    build_interval_event_sequence_table,
    write_interval_event_sequence_qa,
)


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def _interval_row(parameter_set: int, replicate_id: int, checkup_k: int, fold: int) -> dict[str, object]:
    capacity_k = 3.0 - 0.05 * checkup_k - 0.01 * parameter_set
    delta = -0.04 - 0.002 * parameter_set
    return {
        "cell_id": f"cell_{parameter_set}_{replicate_id}",
        "parameter_set": parameter_set,
        "replicate_id": replicate_id,
        "aging_mode": "cyclic",
        "nominal_temperature_C": 25.0,
        "voltage_window_family": "2p5_4p2",
        "nominal_charge_C_rate": 1.0 + 0.1 * parameter_set,
        "nominal_discharge_C_rate": 1.0,
        "profile_label": "constant",
        "checkup_k": checkup_k,
        "checkup_k_next": checkup_k + 1,
        "duration_h": 24.0,
        "calendar_days": 1.0 + checkup_k,
        "capacity_Ah_k": capacity_k,
        "capacity_Ah_k1": capacity_k + delta,
        "delta_capacity_Ah": delta,
        "condition_fold": fold,
        "temperature_holdout_fold": 1,
        "c_rate_holdout_fold": 1,
        "profile_holdout_fold": 1,
        "voltage_window_holdout_fold": 1,
        "log_age_efc_delta": 2.0 + checkup_k,
        "log_age_delta_q_Ah": 5.0 + checkup_k,
        "log_age_mean_voltage_V": 3.8,
        "log_age_min_voltage_V": 3.2,
        "log_age_max_voltage_V": 4.1,
        "log_age_mean_temperature_C": 25.0,
        "log_age_min_temperature_C": 24.0,
        "log_age_max_temperature_C": 27.0,
        "log_age_mean_current_A": 0.2,
        "log_age_mean_abs_current_A": 1.2,
        "log_age_max_abs_current_A": 4.0,
        "log_age_mean_soc": 0.5,
        "log_age_min_soc": 0.2,
        "log_age_max_soc": 0.8,
    }


def _subset_row(interval: dict[str, object]) -> dict[str, object]:
    return {
        "cell_id": interval["cell_id"],
        "parameter_set": interval["parameter_set"],
        "replicate_id": interval["replicate_id"],
        "checkup_k": interval["checkup_k"],
        "checkup_k_next": interval["checkup_k_next"],
        "baseline_clean_tolerant": True,
        "baseline_clean_strict": True,
        "sensitivity_flagged_monotonicity": False,
    }


def _event_row(
    interval: dict[str, object],
    event_index: int,
    event_type: str,
) -> dict[str, object]:
    return {
        "cell_id": interval["cell_id"],
        "parameter_set": interval["parameter_set"],
        "replicate_id": interval["replicate_id"],
        "checkup_k": interval["checkup_k"],
        "checkup_k_next": interval["checkup_k_next"],
        "event_index": event_index,
        "event_type": event_type,
        "event_duration_h": 0.5 + event_index,
        "mean_voltage_V": 3.7 + 0.01 * event_index,
        "mean_abs_current_A": 1.0 + event_index,
        "max_abs_current_A": 2.0 + event_index,
        "mean_temperature_C": 25.0,
        "mean_soc": 0.5,
        "delta_q_Ah": 0.1 * event_index,
        "delta_EFC": 0.2 * event_index,
        "high_voltage_event": event_index % 2 == 0,
        "high_abs_current_event": event_index % 2 == 1,
        "cold_high_current_event": False,
        "high_voltage_high_current_event": event_index % 2 == 0,
    }


def _write_minimal_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    intervals = [
        _interval_row(parameter_set, replicate_id=1, checkup_k=checkup_k, fold=parameter_set % 2)
        for parameter_set in range(1, 5)
        for checkup_k in range(2)
    ]
    run_events = [
        _event_row(interval, event_index, event_type)
        for interval in intervals
        for event_index, event_type in enumerate(["charge", "rest", "discharge", "rest"])
    ]
    interval_path = tmp_path / "interval_table.parquet"
    subsets_path = tmp_path / "interval_subset_registry_v1.parquet"
    run_events_path = tmp_path / "run_event_table_v1.parquet"
    _write_parquet(interval_path, intervals)
    _write_parquet(subsets_path, [_subset_row(row) for row in intervals])
    _write_parquet(run_events_path, run_events)
    return interval_path, subsets_path, run_events_path


def test_event_sequence_table_builds_fixed_length_vectors(tmp_path: Path) -> None:
    interval_path, _, run_events_path = _write_minimal_inputs(tmp_path)
    out = tmp_path / "interval_event_sequence_table_v1.parquet"

    table = build_interval_event_sequence_table(run_events_path, interval_path, out, max_events=3, seed=7)
    rows = table.to_pylist()

    assert table.num_rows == 8
    assert len(rows[0]["true_sequence_vector"]) == 3 * len(EVENT_FEATURE_COLUMNS)
    assert len(rows[0]["shuffled_sequence_vector"]) == 3 * len(EVENT_FEATURE_COLUMNS)
    assert rows[0]["event_mask"] == [1, 1, 1]
    assert rows[0]["truncated_event_count"] == 1


def test_event_sequence_qa_catches_valid_lengths(tmp_path: Path) -> None:
    interval_path, _, run_events_path = _write_minimal_inputs(tmp_path)
    event_sequences = tmp_path / "interval_event_sequence_table_v1.parquet"
    qa_out = tmp_path / "event_sequence_qa.json"
    build_interval_event_sequence_table(run_events_path, interval_path, event_sequences, max_events=4)

    report = write_interval_event_sequence_qa(event_sequences, interval_path, qa_out)

    assert report["status"] == "passed"
    assert report["row_count"] == 8
    assert report["leakage_check"]["status"] == "passed"


def test_minimal_sequence_runner_writes_reports(tmp_path: Path) -> None:
    interval_path, subsets_path, run_events_path = _write_minimal_inputs(tmp_path)
    event_sequences = tmp_path / "interval_event_sequence_table_v1.parquet"
    build_interval_event_sequence_table(run_events_path, interval_path, event_sequences, max_events=4)

    report = run_minimal_sequence_reopening(
        interval_path,
        subsets_path,
        event_sequences,
        tmp_path / "minimal_sequence_report.json",
        tmp_path / "minimal_sequence_predictions.parquet",
        out_dir=tmp_path / "minimal_sequence",
        model_levels=["S0_ridge_true_sequence", "S1_ridge_shuffled_sequence"],
        targets=["capacity_Ah_k1"],
        split_views=["condition_fold"],
    )

    assert report["status"] == "passed"
    assert report["metrics"]
    assert (tmp_path / "minimal_sequence" / "leaderboard.csv").exists()
    assert (
        tmp_path / "minimal_sequence" / "sequence_reopening_claim_readiness.md"
    ).exists()


def test_minimal_sequence_cli_builds_event_sequences(tmp_path: Path) -> None:
    interval_path, _, run_events_path = _write_minimal_inputs(tmp_path)
    out = tmp_path / "interval_event_sequence_table_v1.parquet"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "features",
            "build-event-sequences",
            "--run-events",
            str(run_events_path),
            "--interval-table",
            str(interval_path),
            "--out",
            str(out),
            "--max-events",
            "4",
        ],
    )

    assert result.exit_code == 0
    assert out.exists()
    assert "Event-sequence table generated" in result.output


def test_minimal_sequence_cli_runs_ridge_gate(tmp_path: Path) -> None:
    interval_path, subsets_path, run_events_path = _write_minimal_inputs(tmp_path)
    event_sequences = tmp_path / "interval_event_sequence_table_v1.parquet"
    build_interval_event_sequence_table(run_events_path, interval_path, event_sequences, max_events=4)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "baseline",
            "run-minimal-sequence-reopening",
            "--interval-table",
            str(interval_path),
            "--interval-subsets",
            str(subsets_path),
            "--event-sequences",
            str(event_sequences),
            "--out",
            str(tmp_path / "report.json"),
            "--predictions-out",
            str(tmp_path / "predictions.parquet"),
            "--out-dir",
            str(tmp_path / "diagnostics"),
            "--model-levels",
            "S0_ridge_true_sequence,S1_ridge_shuffled_sequence",
            "--targets",
            "capacity_Ah_k1",
            "--split-views",
            "condition_fold",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert (tmp_path / "diagnostics" / "plots" / "sequence_vs_shuffled.csv").exists()


def test_torch_sequence_models_require_gpu_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_import() -> object:
        raise RuntimeError("CUDA required")

    monkeypatch.setattr(minimal_sequence, "_import_torch_stack", fail_import)

    with pytest.raises(RuntimeError, match="CUDA required"):
        minimal_sequence._preflight_dependencies(["S2_torch_mlp_true_sequence"])
