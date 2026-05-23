from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import NUMERIC_FEATURES
from mbp.data.products.run_events import (
    build_run_event_table,
    build_sequence_feature_table,
    write_run_event_qa,
    write_sequence_feature_qa,
)


def _interval_rows() -> list[dict[str, object]]:
    return [
        {
            "cell_id": "cell_1",
            "parameter_set": 1,
            "replicate_id": 1,
            "checkup_k": 0,
            "checkup_k_next": 1,
            "t_result_k_s": 100.0,
            "t_result_k1_s": 500.0,
            "duration_h": 400.0 / 3600.0,
            "capacity_Ah_k": 3.0,
            "capacity_Ah_k1": 2.9,
            "delta_capacity_Ah": -0.1,
        }
    ]


def _log_rows() -> list[dict[str, object]]:
    currents = [0.0, 5.0, 5.2, 0.0, -5.1, -5.0, 0.0]
    return [
        {
            "cell_id": "cell_1",
            "timestamp_s": timestamp,
            "v_raw_V": 3.7 + idx * 0.05,
            "i_raw_A": current,
            "t_cell_degC": 8.0 if abs(current) > 1 else 25.0,
            "soc_est": 40.0 + idx,
            "delta_q_Ah": idx * 0.01,
            "EFC": idx * 0.1,
        }
        for idx, (timestamp, current) in enumerate(zip([1, 120, 180, 240, 300, 360, 420], currents, strict=True))
    ]


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    interval_path = tmp_path / "interval.parquet"
    log_path = tmp_path / "log.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    pq.write_table(pa.Table.from_pylist(_log_rows()), log_path)
    return log_path, interval_path


def test_run_event_segmentation_and_qa(tmp_path: Path) -> None:
    log_path, interval_path = _write_inputs(tmp_path)
    run_events = tmp_path / "run_events.parquet"
    table = build_run_event_table(log_path, interval_path, run_events)
    rows = table.to_pylist()
    assert [row["event_type"] for row in rows] == ["rest", "charge", "rest", "discharge"]
    assert rows[1]["source_rows"] == 2
    assert any(row["cold_high_current_event"] for row in rows)
    report = write_run_event_qa(
        run_events,
        interval_path,
        tmp_path / "run_event_qa.json",
        tmp_path / "coverage.csv",
    )
    assert report["intervals_covered"] == 1
    assert report["event_type_counts"]["charge"] == 1


def test_sequence_features_and_shuffled_reproducibility(tmp_path: Path) -> None:
    log_path, interval_path = _write_inputs(tmp_path)
    run_events = tmp_path / "run_events.parquet"
    seq_a = tmp_path / "seq_a.parquet"
    seq_b = tmp_path / "seq_b.parquet"
    build_run_event_table(log_path, interval_path, run_events)
    table_a = build_sequence_feature_table(run_events, interval_path, seq_a, seed=7)
    table_b = build_sequence_feature_table(run_events, interval_path, seq_b, seed=7)
    row_a = table_a.to_pylist()[0]
    row_b = table_b.to_pylist()[0]
    assert row_a == row_b
    assert row_a["sequence_event_count"] == 4
    assert row_a["sequence_transition_charge_rest"] == 1
    assert row_a["sequence_cold_high_current_event_count"] > 0
    qa = write_sequence_feature_qa(seq_a, interval_path, tmp_path / "sequence_qa.json")
    assert qa["status"] == "passed"


def test_sequence_feature_groups_exclude_target_derived_rates() -> None:
    forbidden = {"delta_capacity_per_day", "delta_capacity_per_efc", "delta_capacity_per_Ah_throughput"}
    for group in ("F14_event_aggregate", "F15_event_order_aware", "F16_event_order_shuffled", "F17_event_order_plus_stress"):
        assert not (set(NUMERIC_FEATURES[group]) & forbidden)
