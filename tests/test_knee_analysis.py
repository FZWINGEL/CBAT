from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.knee import (
    build_knee_risk_label_table,
    detector_agreement_rows,
    extract_capacity_trajectories,
    knee_candidate_rows,
    knee_inconsistent_condition_rows,
    replicate_consistency_rows,
    stable_condition_rows,
    threshold_by_condition_rows,
    threshold_event_label_rows,
    threshold_stability_rows,
    write_knee_forensics,
    write_knee_label_report,
    write_knee_stable_registry,
    write_threshold_event_labels,
)
from mbp.data.schema_contracts import (
    KNEE_CANDIDATE_TABLE_V1_SCHEMA,
    THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA,
    validate_table,
)


def _interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set in (1, 2):
        for replicate in (1, 2, 3):
            cell_id = f"P{parameter_set:03d}_{replicate}"
            capacity = 3.0
            for k in range(8):
                drop = 0.03 if k < 4 else 0.16
                next_capacity = capacity - drop if parameter_set == 1 else 3.0 - 0.03 * (k + 1)
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0,
                        "voltage_window_family": "approx_0_100",
                        "nominal_charge_C_rate": 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "constant",
                        "checkup_k": k,
                        "checkup_k_next": k + 1,
                        "t_result_k_s": float(k * 86400),
                        "t_result_k1_s": float((k + 1) * 86400),
                        "duration_h": 24.0,
                        "calendar_days": 1.0,
                        "capacity_Ah_k": capacity,
                        "capacity_Ah_k1": next_capacity,
                        "delta_capacity_Ah": next_capacity - capacity,
                        "log_age_efc_delta": 10.0,
                    }
                )
                capacity = next_capacity
    return rows


def _condition_metadata(rows: list[dict[str, object]]) -> dict[int, dict[str, object]]:
    output: dict[int, dict[str, object]] = {}
    for row in rows:
        output.setdefault(
            int(row["parameter_set"]),
            {
                "aging_mode": row["aging_mode"],
                "nominal_temperature_C": row["nominal_temperature_C"],
                "voltage_window_family": row["voltage_window_family"],
                "nominal_charge_C_rate": row["nominal_charge_C_rate"],
                "nominal_discharge_C_rate": row["nominal_discharge_C_rate"],
                "profile_label": row["profile_label"],
            },
        )
    return output


def test_knee_candidate_generation_known_and_no_knee() -> None:
    trajectories = extract_capacity_trajectories(_interval_rows())
    candidates = knee_candidate_rows(trajectories)
    assert validate_table(pa.Table.from_pylist(candidates, schema=KNEE_CANDIDATE_TABLE_V1_SCHEMA), KNEE_CANDIDATE_TABLE_V1_SCHEMA)
    primary_known = [
        row
        for row in candidates
        if row["parameter_set"] == 1
        and row["detector_name"] == "piecewise_linear_bic"
        and row["x_axis"] == "checkup_index"
        and row["smoothing_policy"] == "none"
    ]
    assert {row["knee_checkup_k"] for row in primary_known} <= {4, 5}
    threshold_no_knee = [
        row
        for row in candidates
        if row["parameter_set"] == 2 and row["detector_name"] == "capacity_threshold_60"
    ]
    assert all(row["knee_checkup_k"] is None for row in threshold_no_knee)


def test_agreement_and_replicate_consistency_metrics() -> None:
    candidates = knee_candidate_rows(extract_capacity_trajectories(_interval_rows()))
    agreement = detector_agreement_rows(candidates)
    replicate = replicate_consistency_rows(candidates)
    assert agreement
    assert any(row["agreement_within_2_checkups"] >= 0 for row in agreement)
    primary = [
        row
        for row in replicate
        if row["parameter_set"] == 1
        and row["detector_name"] == "piecewise_linear_bic"
        and row["x_axis"] == "checkup_index"
        and row["smoothing_policy"] == "none"
    ]
    assert primary[0]["replicate_consistent_within_2_checkups"]


def test_knee_report_and_risk_labels(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    candidate_path = tmp_path / "knee_candidates.parquet"
    risk_path = tmp_path / "risk.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)

    report = write_knee_label_report(interval_path, tmp_path / "knee", candidate_path)
    assert report["row_counts"]["candidate_rows"] > 0
    assert (tmp_path / "knee" / "knee_claim_readiness.md").exists()

    risk = build_knee_risk_label_table(candidate_path, interval_path, risk_path)
    row = risk.to_pylist()[0]
    assert risk.num_rows == len(_interval_rows())
    assert row["knee_label_quality"].startswith("exploratory")


def test_forensics_and_stable_registry_classification() -> None:
    rows = _interval_rows()
    candidates = knee_candidate_rows(extract_capacity_trajectories(rows))
    primary = [
        row
        for row in candidates
        if row["parameter_set"] == 1
        and row["detector_name"] == "piecewise_linear_bic"
        and row["x_axis"] == "checkup_index"
        and row["smoothing_policy"] == "none"
    ]
    primary[0]["knee_checkup_k"] = 1
    primary[1]["knee_checkup_k"] = 6
    primary[2]["knee_checkup_k"] = 6
    lookup = {trajectory.cell_id: trajectory for trajectory in extract_capacity_trajectories(rows)}
    inconsistent = knee_inconsistent_condition_rows(candidates, lookup, _condition_metadata(rows))
    stable = stable_condition_rows(candidates, _condition_metadata(rows))
    assert any(row["parameter_set"] == 1 and row["knee_spread_checkups"] == 5.0 for row in inconsistent)
    assert any(row["parameter_set"] == 1 and row["stability_status"] == "unstable" for row in stable)


def test_threshold_event_labels_and_stability() -> None:
    rows = _interval_rows()
    trajectories = extract_capacity_trajectories(rows)
    labels = threshold_event_label_rows(rows, trajectories)
    stability = threshold_stability_rows(rows, trajectories)
    by_condition = threshold_by_condition_rows(trajectories)
    assert validate_table(
        pa.Table.from_pylist(labels, schema=THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA),
        THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA,
    )
    assert any(row["threshold_label"] == "soh_below_80" for row in labels)
    assert any(row["threshold_label"] == "soh_below_80" for row in stability)
    assert any(row["threshold_label"] == "soh_below_80" for row in by_condition)


def test_forensics_and_threshold_reports_render(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    candidate_path = tmp_path / "knee_candidates.parquet"
    stable_path = tmp_path / "stable.parquet"
    threshold_path = tmp_path / "threshold.parquet"
    pq.write_table(pa.Table.from_pylist(_interval_rows()), interval_path)
    write_knee_label_report(interval_path, tmp_path / "knee", candidate_path)

    forensics = write_knee_forensics(candidate_path, interval_path, tmp_path / "knee")
    stable = write_knee_stable_registry(
        candidate_path,
        interval_path,
        stable_path,
        tmp_path / "knee" / "stable.json",
        tmp_path / "knee" / "stable.csv",
    )
    threshold = write_threshold_event_labels(interval_path, tmp_path / "knee", threshold_path)
    assert (tmp_path / "knee" / "knee_inconsistency_forensics.md").exists()
    assert (tmp_path / "knee" / "threshold_event_claim_readiness.md").exists()
    assert forensics["row_counts"]["inconsistent_conditions"] >= 0
    assert stable["row_counts"]["conditions"] == 2
    assert threshold["row_counts"]["label_rows"] == len(_interval_rows()) * 6
