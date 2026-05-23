"""Knee-label stability and degradation-acceleration diagnostics."""

from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import (
    KNEE_CANDIDATE_TABLE_V1_SCHEMA,
    KNEE_RISK_LABEL_TABLE_V1_SCHEMA,
    KNEE_STABLE_CONDITION_REGISTRY_V1_SCHEMA,
    THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA,
    validate_table,
)

SCHEMA_VERSION = "gate25.knee_candidates.v1"
RISK_SCHEMA_VERSION = "gate25.knee_risk_labels.v1"
STABLE_REGISTRY_SCHEMA_VERSION = "gate251.knee_stable_conditions.v1"
THRESHOLD_SCHEMA_VERSION = "gate251.threshold_event_labels.v1"
DETECTORS = (
    "piecewise_linear_bic",
    "max_chord_distance",
    "two_line_l_method",
    "slope_change_threshold",
    "capacity_threshold_80",
    "capacity_threshold_70",
    "capacity_threshold_60",
)
X_AXES = ("checkup_index", "calendar_days", "log_age_efc_cumulative")
SMOOTHING_POLICIES = ("none", "rolling_3")
PRIMARY_DETECTOR = "piecewise_linear_bic"
PRIMARY_X_AXIS = "checkup_index"
PRIMARY_SMOOTHING = "none"
SEVERE_TRAJECTORY_FLAGS = ("few_checkups", "duplicate_checkups", "capacity_increase_gt_0p02Ah")
THRESHOLD_FRACTIONS = (0.8, 0.7, 0.6)


@dataclass(frozen=True)
class Trajectory:
    cell_id: str
    parameter_set: int
    replicate_id: int
    metadata: dict[str, Any]
    checkup_k: np.ndarray
    calendar_days: np.ndarray
    log_age_efc_cumulative: np.ndarray
    capacity_Ah: np.ndarray
    soh: np.ndarray
    quality_flags: tuple[str, ...]


def write_knee_label_report(
    interval_table_path: Path,
    out_dir: Path,
    candidate_out: Path,
) -> dict[str, Any]:
    """Build knee candidate labels and write stability diagnostics."""
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_out.parent.mkdir(parents=True, exist_ok=True)
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    trajectories = extract_capacity_trajectories(interval_rows)
    candidate_rows = knee_candidate_rows(trajectories)
    table = pa.Table.from_pylist(candidate_rows, schema=KNEE_CANDIDATE_TABLE_V1_SCHEMA)
    if not validate_table(table, KNEE_CANDIDATE_TABLE_V1_SCHEMA):
        raise TypeError("Generated knee candidate table does not match KNEE_CANDIDATE_TABLE_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"primary_detector": PRIMARY_DETECTOR.encode(),
        }
    )
    pq.write_table(table, candidate_out)

    agreement_rows = detector_agreement_rows(candidate_rows)
    stability_report = label_stability_report(candidate_rows, trajectories)
    condition_rows = knee_by_condition_rows(candidate_rows)
    replicate_rows = replicate_consistency_rows(candidate_rows)
    claim_rows = knee_claim_readiness_rows(stability_report, replicate_rows)

    _write_csv(out_dir / "knee_detector_agreement.csv", agreement_rows)
    _write_csv(out_dir / "knee_by_condition.csv", condition_rows)
    _write_csv(out_dir / "knee_replicate_consistency.csv", replicate_rows)
    _write_claim_readiness(claim_rows, out_dir / "knee_claim_readiness.md")
    stability_report["outputs"] = {
        "candidate_table": str(candidate_out),
        "detector_agreement": str(out_dir / "knee_detector_agreement.csv"),
        "knee_by_condition": str(out_dir / "knee_by_condition.csv"),
        "replicate_consistency": str(out_dir / "knee_replicate_consistency.csv"),
        "claim_readiness": str(out_dir / "knee_claim_readiness.md"),
    }
    (out_dir / "knee_label_stability_report.json").write_text(
        json.dumps(stability_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "status": stability_report["status"],
        "schema_version": SCHEMA_VERSION,
        "row_counts": {
            "trajectories": len(trajectories),
            "candidate_rows": len(candidate_rows),
            "detector_agreement_rows": len(agreement_rows),
            "replicate_consistency_rows": len(replicate_rows),
        },
        "outputs": stability_report["outputs"],
    }


def build_knee_risk_label_table(
    knee_candidates_path: Path,
    interval_table_path: Path,
    out_path: Path,
) -> pa.Table:
    """Build exploratory interval-level knee-risk labels from primary knee candidates."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    candidates = pq.read_table(knee_candidates_path).to_pylist()
    intervals = pq.read_table(interval_table_path).to_pylist()
    primary_by_cell = {
        str(row["cell_id"]): row
        for row in candidates
        if row["detector_name"] == PRIMARY_DETECTOR
        and row["x_axis"] == PRIMARY_X_AXIS
        and row["smoothing_policy"] == PRIMARY_SMOOTHING
    }
    rows: list[dict[str, Any]] = []
    for interval in intervals:
        candidate = primary_by_cell.get(str(interval["cell_id"]))
        knee_k = _as_int(candidate.get("knee_checkup_k")) if candidate else None
        quality = str(candidate.get("detector_quality_flags")) if candidate else "missing_primary_candidate"
        time_to_knee = knee_k - int(interval["checkup_k"]) if knee_k is not None else None
        time_to_days = (
            _time_to_knee_days(intervals, str(interval["cell_id"]), int(interval["checkup_k"]), knee_k)
            if knee_k is not None
            else None
        )
        rows.append(
            {
                "cell_id": str(interval["cell_id"]),
                "parameter_set": int(interval["parameter_set"]),
                "replicate_id": int(interval["replicate_id"]),
                "checkup_k": int(interval["checkup_k"]),
                "checkup_k_next": int(interval["checkup_k_next"]),
                "detector_name": PRIMARY_DETECTOR,
                "x_axis": PRIMARY_X_AXIS,
                "smoothing_policy": PRIMARY_SMOOTHING,
                "knee_within_1_checkup": time_to_knee is not None and 0 < time_to_knee <= 1,
                "knee_within_2_checkups": time_to_knee is not None and 0 < time_to_knee <= 2,
                "knee_within_3_checkups": time_to_knee is not None and 0 < time_to_knee <= 3,
                "time_to_knee_checkups": time_to_knee,
                "time_to_knee_days": time_to_days,
                "knee_label_quality": f"exploratory;{quality}",
                "schema_version": RISK_SCHEMA_VERSION,
            }
        )
    table = pa.Table.from_pylist(rows, schema=KNEE_RISK_LABEL_TABLE_V1_SCHEMA)
    if not validate_table(table, KNEE_RISK_LABEL_TABLE_V1_SCHEMA):
        raise TypeError("Generated knee risk label table does not match KNEE_RISK_LABEL_TABLE_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": RISK_SCHEMA_VERSION.encode(),
            b"knee_candidates_path": str(knee_candidates_path).encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"label_status": b"exploratory_only",
        }
    )
    pq.write_table(table, out_path)
    return table


def write_knee_forensics(
    knee_candidates_path: Path,
    interval_table_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Write condition-level forensics for primary knee replicate failures."""
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = pq.read_table(knee_candidates_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    trajectories = extract_capacity_trajectories(interval_rows)
    trajectory_lookup = {trajectory.cell_id: trajectory for trajectory in trajectories}
    metadata = _condition_metadata(interval_rows)
    rows = knee_inconsistent_condition_rows(candidates, trajectory_lookup, metadata)
    _write_csv(out_dir / "knee_inconsistent_conditions.csv", rows)
    _write_knee_inconsistency_forensics(rows, out_dir / "knee_inconsistency_forensics.md")
    return {
        "row_counts": {
            "inconsistent_conditions": len(rows),
        },
        "outputs": {
            "inconsistent_conditions": str(out_dir / "knee_inconsistent_conditions.csv"),
            "forensics": str(out_dir / "knee_inconsistency_forensics.md"),
        },
    }


def write_knee_stable_registry(
    knee_candidates_path: Path,
    interval_table_path: Path,
    out_path: Path,
    report_path: Path,
    coverage_out: Path,
) -> dict[str, Any]:
    """Write a registry of stable, unstable, and insufficient knee-label conditions."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_out.parent.mkdir(parents=True, exist_ok=True)
    candidates = pq.read_table(knee_candidates_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    metadata = _condition_metadata(interval_rows)
    rows = stable_condition_rows(candidates, metadata)
    table = pa.Table.from_pylist(rows, schema=KNEE_STABLE_CONDITION_REGISTRY_V1_SCHEMA)
    if not validate_table(table, KNEE_STABLE_CONDITION_REGISTRY_V1_SCHEMA):
        raise TypeError("Generated stable knee registry does not match KNEE_STABLE_CONDITION_REGISTRY_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": STABLE_REGISTRY_SCHEMA_VERSION.encode(),
            b"knee_candidates_path": str(knee_candidates_path).encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"label_status": b"diagnostic_only",
        }
    )
    pq.write_table(table, out_path)
    coverage_rows = stable_condition_coverage_rows(rows)
    _write_csv(coverage_out, coverage_rows)
    report = stable_condition_report(rows, coverage_rows)
    report["outputs"] = {
        "stable_registry": str(out_path),
        "report": str(report_path),
        "coverage": str(coverage_out),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def write_threshold_event_labels(
    interval_table_path: Path,
    out_dir: Path,
    labels_out: Path,
) -> dict[str, Any]:
    """Write threshold-event labels and stability diagnostics."""
    out_dir.mkdir(parents=True, exist_ok=True)
    labels_out.parent.mkdir(parents=True, exist_ok=True)
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    trajectories = extract_capacity_trajectories(interval_rows)
    label_rows = threshold_event_label_rows(interval_rows, trajectories)
    table = pa.Table.from_pylist(label_rows, schema=THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA)
    if not validate_table(table, THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA):
        raise TypeError("Generated threshold event label table does not match THRESHOLD_EVENT_LABEL_TABLE_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": THRESHOLD_SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"label_status": b"exploratory_only",
        }
    )
    pq.write_table(table, labels_out)
    stability_rows = threshold_stability_rows(interval_rows, trajectories)
    condition_rows = threshold_by_condition_rows(trajectories)
    claim_rows = threshold_claim_readiness_rows(stability_rows)
    _write_csv(out_dir / "threshold_event_stability.csv", stability_rows)
    _write_csv(out_dir / "threshold_event_by_condition.csv", condition_rows)
    _write_threshold_claim_readiness(claim_rows, out_dir / "threshold_event_claim_readiness.md")
    _write_knee_vs_threshold_decision(
        candidates_path=None,
        threshold_rows=stability_rows,
        out_path=out_dir / "knee_vs_threshold_decision.md",
    )
    return {
        "row_counts": {
            "label_rows": len(label_rows),
            "stability_rows": len(stability_rows),
            "condition_rows": len(condition_rows),
        },
        "outputs": {
            "labels": str(labels_out),
            "stability": str(out_dir / "threshold_event_stability.csv"),
            "by_condition": str(out_dir / "threshold_event_by_condition.csv"),
            "claim_readiness": str(out_dir / "threshold_event_claim_readiness.md"),
            "decision": str(out_dir / "knee_vs_threshold_decision.md"),
        },
    }


def write_knee_vs_threshold_decision(
    knee_candidates_path: Path,
    interval_table_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Write a decision memo comparing primary knee labels with threshold events."""
    candidates = pq.read_table(knee_candidates_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    trajectories = extract_capacity_trajectories(interval_rows)
    threshold_rows = threshold_stability_rows(interval_rows, trajectories)
    _write_knee_vs_threshold_decision(knee_candidates_path, threshold_rows, out_path, candidates)
    return {"outputs": {"decision": str(out_path)}}


def extract_capacity_trajectories(interval_rows: list[dict[str, Any]]) -> list[Trajectory]:
    """Create one capacity trajectory per cell from adjacent interval rows."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in interval_rows:
        grouped[str(row["cell_id"])].append(row)
    trajectories: list[Trajectory] = []
    for cell_id, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: int(row["checkup_k"]))
        if not ordered:
            continue
        points: dict[int, dict[str, float]] = {}
        first_t = _as_float(ordered[0].get("t_result_k_s"))
        cumulative_efc = 0.0
        first_k = int(ordered[0]["checkup_k"])
        points[first_k] = {
            "checkup_k": float(first_k),
            "calendar_days": 0.0,
            "log_age_efc_cumulative": 0.0,
            "capacity_Ah": _as_float(ordered[0].get("capacity_Ah_k")),
        }
        previous_k_next: int | None = None
        duplicate_count = 0
        for row in ordered:
            checkup_k_next = int(row["checkup_k_next"])
            duplicate_count += int(checkup_k_next in points)
            cumulative_efc += max(0.0, _as_float(row.get("log_age_efc_delta"), default=0.0))
            points[checkup_k_next] = {
                "checkup_k": float(checkup_k_next),
                "calendar_days": (_as_float(row.get("t_result_k1_s")) - first_t) / 86400.0,
                "log_age_efc_cumulative": cumulative_efc,
                "capacity_Ah": _as_float(row.get("capacity_Ah_k1")),
            }
            previous_k_next = checkup_k_next
        ordered_points = [points[key] for key in sorted(points)]
        capacity = np.asarray([point["capacity_Ah"] for point in ordered_points], dtype=float)
        initial = capacity[0] if len(capacity) and math.isfinite(float(capacity[0])) and capacity[0] else np.nan
        soh = capacity / initial if math.isfinite(float(initial)) and initial > 0 else np.full(len(capacity), np.nan)
        quality_flags = []
        if len(capacity) < 6:
            quality_flags.append("few_checkups")
        if duplicate_count:
            quality_flags.append("duplicate_checkups")
        if bool(np.any(np.diff(capacity[np.isfinite(capacity)]) > 0.02)):
            quality_flags.append("capacity_increase_gt_0p02Ah")
        if previous_k_next is None:
            quality_flags.append("no_intervals")
        first = ordered[0]
        trajectories.append(
            Trajectory(
                cell_id=cell_id,
                parameter_set=int(first["parameter_set"]),
                replicate_id=int(first["replicate_id"]),
                metadata={
                    "aging_mode": str(first.get("aging_mode", "")),
                    "nominal_temperature_C": _as_float(first.get("nominal_temperature_C")),
                    "voltage_window_family": str(first.get("voltage_window_family", "")),
                    "nominal_charge_C_rate": _as_float(first.get("nominal_charge_C_rate")),
                    "nominal_discharge_C_rate": _as_float(first.get("nominal_discharge_C_rate")),
                    "profile_label": str(first.get("profile_label", "")),
                },
                checkup_k=np.asarray([point["checkup_k"] for point in ordered_points], dtype=float),
                calendar_days=np.asarray([point["calendar_days"] for point in ordered_points], dtype=float),
                log_age_efc_cumulative=np.asarray(
                    [point["log_age_efc_cumulative"] for point in ordered_points], dtype=float
                ),
                capacity_Ah=capacity,
                soh=soh,
                quality_flags=tuple(quality_flags),
            )
        )
    return trajectories


def knee_candidate_rows(trajectories: list[Trajectory]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trajectory in trajectories:
        for smoothing_policy in SMOOTHING_POLICIES:
            y = _smooth(trajectory.capacity_Ah, smoothing_policy)
            soh = _smooth(trajectory.soh, smoothing_policy)
            for x_axis in X_AXES:
                x = _trajectory_axis(trajectory, x_axis)
                for detector_name in DETECTORS:
                    result = _detect_knee(detector_name, x, y, soh)
                    rows.append(_candidate_row(trajectory, detector_name, x_axis, smoothing_policy, result))
    return rows


def detector_agreement_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[(str(row["cell_id"]), str(row["x_axis"]), str(row["smoothing_policy"]))].append(row)
    pair_values: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for (_cell, x_axis, smoothing), rows in grouped.items():
        valid = [row for row in rows if _as_int(row.get("knee_checkup_k")) is not None]
        by_detector = {str(row["detector_name"]): row for row in valid}
        for left, right in itertools.combinations(sorted(by_detector), 2):
            diff = abs(int(by_detector[left]["knee_checkup_k"]) - int(by_detector[right]["knee_checkup_k"]))
            pair_values[(x_axis, smoothing, left, right)].append(float(diff))
    output = []
    for (x_axis, smoothing, left, right), diffs in sorted(pair_values.items()):
        output.append(
            {
                "x_axis": x_axis,
                "smoothing_policy": smoothing,
                "detector_a": left,
                "detector_b": right,
                "n_cells": len(diffs),
                "agreement_within_1_checkup": sum(value <= 1 for value in diffs) / len(diffs),
                "agreement_within_2_checkups": sum(value <= 2 for value in diffs) / len(diffs),
                "median_abs_disagreement_checkups": _median(diffs),
                "mean_abs_disagreement_checkups": _mean(diffs),
            }
        )
    return output


def label_stability_report(
    candidate_rows: list[dict[str, Any]],
    trajectories: list[Trajectory],
) -> dict[str, Any]:
    valid = [row for row in candidate_rows if _as_int(row.get("knee_checkup_k")) is not None]
    no_valid_by_cell = {
        row["cell_id"]
        for row in candidate_rows
        if row["detector_quality_flags"] == "no_valid_knee"
    }
    x_sensitivity = _sensitivity_rows(candidate_rows, group_fields=("cell_id", "detector_name", "smoothing_policy"), vary="x_axis")
    smoothing_sensitivity = _sensitivity_rows(candidate_rows, group_fields=("cell_id", "detector_name", "x_axis"), vary="smoothing_policy")
    primary = [
        row
        for row in candidate_rows
        if row["detector_name"] == PRIMARY_DETECTOR
        and row["x_axis"] == PRIMARY_X_AXIS
        and row["smoothing_policy"] == PRIMARY_SMOOTHING
    ]
    primary_valid = [row for row in primary if _as_int(row.get("knee_checkup_k")) is not None]
    return {
        "status": "warning",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "cells": len(trajectories),
            "candidate_rows": len(candidate_rows),
            "valid_candidate_rows": len(valid),
            "primary_rows": len(primary),
            "primary_valid_rows": len(primary_valid),
        },
        "trajectory_qa": {
            "few_checkup_cells": sum("few_checkups" in trajectory.quality_flags for trajectory in trajectories),
            "capacity_increase_cells": sum(
                "capacity_increase_gt_0p02Ah" in trajectory.quality_flags for trajectory in trajectories
            ),
        },
        "label_coverage": {
            "fraction_valid_candidate_rows": len(valid) / len(candidate_rows) if candidate_rows else 0.0,
            "fraction_primary_valid": len(primary_valid) / len(primary) if primary else 0.0,
            "cells_with_no_valid_detector_rows": len(no_valid_by_cell),
        },
        "x_axis_sensitivity": _sensitivity_summary(x_sensitivity),
        "smoothing_sensitivity": _sensitivity_summary(smoothing_sensitivity),
        "warnings": [
            "prediction_readiness_blocked",
            "candidate_labels_exploratory_until_detector_and_replicate_stability_pass",
        ],
    }


def knee_by_condition_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[
            (
                int(row["parameter_set"]),
                str(row["detector_name"]),
                str(row["x_axis"]),
                str(row["smoothing_policy"]),
            )
        ].append(row)
    output = []
    for (parameter_set, detector, x_axis, smoothing), rows in sorted(grouped.items()):
        knees = [_as_float(row.get("knee_checkup_k")) for row in rows]
        knees = [value for value in knees if math.isfinite(value)]
        output.append(
            {
                "parameter_set": parameter_set,
                "detector_name": detector,
                "x_axis": x_axis,
                "smoothing_policy": smoothing,
                "n_cells": len(rows),
                "n_valid_knees": len(knees),
                "median_knee_checkup_k": _median(knees) if knees else None,
                "knee_checkup_spread": max(knees) - min(knees) if len(knees) > 1 else 0.0 if knees else None,
                "aging_mode": _first(rows, "aging_mode"),
                "nominal_temperature_C": _first(rows, "nominal_temperature_C"),
                "voltage_window_family": _first(rows, "voltage_window_family"),
                "nominal_charge_C_rate": _first(rows, "nominal_charge_C_rate"),
                "profile_label": _first(rows, "profile_label"),
            }
        )
    return output


def replicate_consistency_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[
            (
                int(row["parameter_set"]),
                str(row["detector_name"]),
                str(row["x_axis"]),
                str(row["smoothing_policy"]),
            )
        ].append(row)
    output = []
    for (parameter_set, detector, x_axis, smoothing), rows in sorted(grouped.items()):
        knees = [_as_float(row.get("knee_checkup_k")) for row in rows]
        knees = [value for value in knees if math.isfinite(value)]
        spread = max(knees) - min(knees) if len(knees) > 1 else 0.0 if knees else None
        output.append(
            {
                "parameter_set": parameter_set,
                "detector_name": detector,
                "x_axis": x_axis,
                "smoothing_policy": smoothing,
                "n_replicates": len({str(row["cell_id"]) for row in rows}),
                "n_valid_knees": len(knees),
                "knee_spread_checkups": spread,
                "replicate_consistent_within_2_checkups": bool(spread is not None and spread <= 2.0),
            }
        )
    return output


def knee_claim_readiness_rows(
    stability_report: dict[str, Any],
    replicate_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    consistency = [
        row
        for row in replicate_rows
        if row["detector_name"] == PRIMARY_DETECTOR
        and row["x_axis"] == PRIMARY_X_AXIS
        and row["smoothing_policy"] == PRIMARY_SMOOTHING
        and row["n_valid_knees"]
    ]
    consistent_fraction = (
        sum(bool(row["replicate_consistent_within_2_checkups"]) for row in consistency) / len(consistency)
        if consistency
        else 0.0
    )
    primary_valid = stability_report["label_coverage"]["fraction_primary_valid"]
    x_median = stability_report["x_axis_sensitivity"]["median_abs_disagreement_checkups"]
    smoothing_median = stability_report["smoothing_sensitivity"]["median_abs_disagreement_checkups"]
    detector_status = "partially_supported" if primary_valid >= 0.8 else "not_supported"
    x_status = "partially_supported" if x_median is not None and x_median <= 2 else "not_supported"
    smoothing_status = "partially_supported" if smoothing_median is not None and smoothing_median <= 2 else "not_supported"
    replicate_status = "partially_supported" if consistent_fraction >= 0.8 else "not_supported"
    label_ready = all(status == "partially_supported" for status in (detector_status, x_status, smoothing_status, replicate_status))
    return [
        {
            "claim_area": "Detector stability",
            "status": detector_status,
            "evidence": f"Primary detector valid fraction={primary_valid:.3f}.",
        },
        {
            "claim_area": "X-axis robustness",
            "status": x_status,
            "evidence": f"Median x-axis disagreement={_fmt(x_median)} checkups.",
        },
        {
            "claim_area": "Smoothing robustness",
            "status": smoothing_status,
            "evidence": f"Median smoothing disagreement={_fmt(smoothing_median)} checkups.",
        },
        {
            "claim_area": "Replicate consistency",
            "status": replicate_status,
            "evidence": f"Primary condition fraction within 2 checkups={consistent_fraction:.3f}.",
        },
        {
            "claim_area": "Early-warning label readiness",
            "status": "exploratory_only" if not label_ready else "partially_supported",
            "evidence": "Risk labels are generated for sensitivity analysis only until label stability passes.",
        },
        {
            "claim_area": "Prediction readiness",
            "status": "blocked",
            "evidence": "No knee prediction model is authorized by this label-stability gate.",
        },
    ]


def knee_inconsistent_condition_rows(
    candidate_rows: list[dict[str, Any]],
    trajectory_lookup: dict[str, Trajectory],
    metadata: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return primary-valid conditions with replicate knee spread above two checkups."""
    rows = _primary_rows_by_condition(candidate_rows)
    output = []
    for parameter_set, condition_rows in sorted(rows.items()):
        valid = [row for row in condition_rows if _as_int(row.get("knee_checkup_k")) is not None]
        if len(valid) < 2:
            continue
        knees = [int(row["knee_checkup_k"]) for row in valid]
        spread = max(knees) - min(knees)
        if spread <= 2:
            continue
        meta = metadata.get(parameter_set, {})
        day_values = []
        efc_values = []
        checkup_counts = []
        qa_flags = []
        detector_flags = []
        knee_pairs = []
        for row in sorted(valid, key=lambda item: int(item["replicate_id"])):
            cell_id = str(row["cell_id"])
            knee_k = int(row["knee_checkup_k"])
            trajectory = trajectory_lookup.get(cell_id)
            if trajectory:
                checkup_counts.append(str(len(trajectory.checkup_k)))
                day = _trajectory_value_at_checkup(trajectory, "calendar_days", knee_k)
                efc = _trajectory_value_at_checkup(trajectory, "log_age_efc_cumulative", knee_k)
                if day is not None:
                    day_values.append(day)
                if efc is not None:
                    efc_values.append(efc)
            flags = str(row.get("detector_quality_flags", ""))
            qa_flags.extend(flag for flag in flags.split(";") if flag in SEVERE_TRAJECTORY_FLAGS)
            detector_flags.extend(flag for flag in flags.split(";") if flag and flag not in SEVERE_TRAJECTORY_FLAGS)
            knee_pairs.append(f"r{int(row['replicate_id'])}:{knee_k}")
        output.append(
            {
                "parameter_set": parameter_set,
                "replicate_knee_checkup_k": ";".join(knee_pairs),
                "knee_spread_checkups": float(spread),
                "knee_spread_days": max(day_values) - min(day_values) if len(day_values) > 1 else None,
                "knee_spread_efc": max(efc_values) - min(efc_values) if len(efc_values) > 1 else None,
                "aging_mode": str(meta.get("aging_mode", "")),
                "nominal_temperature_C": _as_float(meta.get("nominal_temperature_C")),
                "voltage_window_family": str(meta.get("voltage_window_family", "")),
                "nominal_charge_C_rate": _as_float(meta.get("nominal_charge_C_rate")),
                "nominal_discharge_C_rate": _as_float(meta.get("nominal_discharge_C_rate")),
                "profile_label": str(meta.get("profile_label", "")),
                "checkups_per_replicate": ";".join(checkup_counts),
                "trajectory_qa_flags": ";".join(sorted(set(qa_flags))) or "none",
                "detector_quality_flags": ";".join(sorted(set(detector_flags))) or "none",
            }
        )
    return output


def stable_condition_rows(
    candidate_rows: list[dict[str, Any]],
    metadata: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped = _primary_rows_by_condition(candidate_rows)
    output = []
    for parameter_set in sorted(metadata):
        rows = grouped.get(parameter_set, [])
        knees = [int(row["knee_checkup_k"]) for row in rows if _as_int(row.get("knee_checkup_k")) is not None]
        spread = max(knees) - min(knees) if len(knees) > 1 else 0.0 if knees else None
        flags = sorted(
            {
                flag
                for row in rows
                for flag in str(row.get("detector_quality_flags", "")).split(";")
                if flag
            }
        )
        has_severe = any(flag in SEVERE_TRAJECTORY_FLAGS for flag in flags)
        if len(knees) < 2:
            status = "insufficient_label"
        elif spread is not None and spread <= 2 and not has_severe:
            status = "stable"
        else:
            status = "unstable"
        meta = metadata[parameter_set]
        output.append(
            {
                "parameter_set": parameter_set,
                "stability_status": status,
                "n_replicates": len({str(row["cell_id"]) for row in rows}),
                "n_valid_knees": len(knees),
                "knee_spread_checkups": spread,
                "median_knee_checkup_k": _median([float(value) for value in knees]) if knees else None,
                "aging_mode": str(meta.get("aging_mode", "")),
                "nominal_temperature_C": _as_float(meta.get("nominal_temperature_C")),
                "voltage_window_family": str(meta.get("voltage_window_family", "")),
                "nominal_charge_C_rate": _as_float(meta.get("nominal_charge_C_rate")),
                "nominal_discharge_C_rate": _as_float(meta.get("nominal_discharge_C_rate")),
                "profile_label": str(meta.get("profile_label", "")),
                "has_severe_qa_flags": has_severe,
                "quality_flags": ";".join(flags) or "none",
                "schema_version": STABLE_REGISTRY_SCHEMA_VERSION,
            }
        )
    return output


def stable_condition_coverage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for field in (
        "aging_mode",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
        "voltage_window_family",
        "profile_label",
    ):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[str(row.get(field))].append(row)
        for value, group_rows in sorted(groups.items()):
            stable = sum(row["stability_status"] == "stable" for row in group_rows)
            output.append(
                {
                    "group_field": field,
                    "group_value": value,
                    "n_conditions": len(group_rows),
                    "stable_conditions": stable,
                    "unstable_conditions": sum(row["stability_status"] == "unstable" for row in group_rows),
                    "insufficient_label_conditions": sum(
                        row["stability_status"] == "insufficient_label" for row in group_rows
                    ),
                    "stable_fraction": stable / len(group_rows) if group_rows else 0.0,
                }
            )
    return output


def stable_condition_report(
    rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    stable = [row for row in rows if row["stability_status"] == "stable"]
    c_rate_rows = [row for row in coverage_rows if row["group_field"] == "nominal_charge_C_rate"]
    profile_rows = [row for row in coverage_rows if row["group_field"] == "profile_label"]
    warnings = []
    if len(stable) < 0.8 * len(rows):
        warnings.append("stable_condition_fraction_below_0p8")
    if any(row["stable_conditions"] == 0 for row in c_rate_rows):
        warnings.append("some_c_rate_groups_have_no_stable_conditions")
    if any(row["stable_conditions"] == 0 for row in profile_rows):
        warnings.append("some_profile_groups_have_no_stable_conditions")
    return {
        "status": "warning" if warnings else "passed",
        "schema_version": STABLE_REGISTRY_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "conditions": len(rows),
            "stable_conditions": len(stable),
            "unstable_conditions": sum(row["stability_status"] == "unstable" for row in rows),
            "insufficient_label_conditions": sum(row["stability_status"] == "insufficient_label" for row in rows),
        },
        "stable_fraction": len(stable) / len(rows) if rows else 0.0,
        "warnings": warnings,
    }


def threshold_event_label_rows(
    interval_rows: list[dict[str, Any]],
    trajectories: list[Trajectory],
) -> list[dict[str, Any]]:
    events = _threshold_events_by_cell(trajectories)
    start_days = _interval_start_days_by_cell(interval_rows)
    rows = []
    for interval in interval_rows:
        cell_id = str(interval["cell_id"])
        checkup_k = int(interval["checkup_k"])
        for label, event in events[cell_id].items():
            event_k = event["event_checkup_k"]
            time_to = event_k - checkup_k if event_k is not None else None
            rows.append(
                {
                    "cell_id": cell_id,
                    "parameter_set": int(interval["parameter_set"]),
                    "replicate_id": int(interval["replicate_id"]),
                    "checkup_k": checkup_k,
                    "checkup_k_next": int(interval["checkup_k_next"]),
                    "threshold_label": label,
                    "threshold_fraction": float(event["threshold_fraction"]),
                    "threshold_event_checkup_k": event_k,
                    "threshold_event_days": event["event_days"],
                    "threshold_event_efc": event["event_efc"],
                    "event_within_1_checkup": time_to is not None and 0 < time_to <= 1,
                    "event_within_2_checkups": time_to is not None and 0 < time_to <= 2,
                    "event_within_3_checkups": time_to is not None and 0 < time_to <= 3,
                    "time_to_event_checkups": time_to,
                    "time_to_event_days": (
                        event["event_days"] - start_days.get((cell_id, checkup_k), math.nan)
                        if event["event_days"] is not None
                        else None
                    ),
                    "target_quality_flags": event["quality_flags"],
                    "schema_version": THRESHOLD_SCHEMA_VERSION,
                }
            )
    return rows


def threshold_stability_rows(interval_rows: list[dict[str, Any]], trajectories: list[Trajectory]) -> list[dict[str, Any]]:
    events = _threshold_events_by_cell(trajectories)
    label_rows = threshold_event_label_rows(interval_rows, trajectories)
    horizon_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"h1": 0, "h2": 0, "h3": 0})
    for row in label_rows:
        label = str(row["threshold_label"])
        horizon_counts[label]["h1"] += int(bool(row["event_within_1_checkup"]))
        horizon_counts[label]["h2"] += int(bool(row["event_within_2_checkups"]))
        horizon_counts[label]["h3"] += int(bool(row["event_within_3_checkups"]))
    by_label_condition: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for trajectory in trajectories:
        for label, event in events[trajectory.cell_id].items():
            by_label_condition[(label, trajectory.parameter_set)].append(event)
    output = []
    for label in sorted({label for cell_events in events.values() for label in cell_events}):
        label_events = [cell_events[label] for cell_events in events.values()]
        reached = [event for event in label_events if event["event_checkup_k"] is not None]
        condition_rows = [rows for (row_label, _), rows in by_label_condition.items() if row_label == label]
        valid_condition_rows = [rows for rows in condition_rows if sum(event["event_checkup_k"] is not None for event in rows) >= 2]
        within_1 = 0
        within_2 = 0
        spreads = []
        for rows in valid_condition_rows:
            knees = [int(event["event_checkup_k"]) for event in rows if event["event_checkup_k"] is not None]
            spread = max(knees) - min(knees)
            spreads.append(float(spread))
            within_1 += int(spread <= 1)
            within_2 += int(spread <= 2)
        output.append(
            {
                "threshold_label": label,
                "threshold_fraction": float(label_events[0]["threshold_fraction"]) if label_events else None,
                "cells_reaching_threshold": len(reached),
                "cell_coverage_fraction": len(reached) / len(label_events) if label_events else 0.0,
                "conditions_with_at_least_2_events": len(valid_condition_rows),
                "condition_coverage_fraction": len(valid_condition_rows) / 76.0,
                "replicate_consistency_within_1_checkup": within_1 / len(valid_condition_rows)
                if valid_condition_rows
                else None,
                "replicate_consistency_within_2_checkups": within_2 / len(valid_condition_rows)
                if valid_condition_rows
                else None,
                "median_spread_checkups": _median(spreads) if spreads else None,
                "median_event_checkup_k": _median([float(event["event_checkup_k"]) for event in reached])
                if reached
                else None,
                "event_within_1_checkup_rows": horizon_counts[label]["h1"],
                "event_within_2_checkup_rows": horizon_counts[label]["h2"],
                "event_within_3_checkup_rows": horizon_counts[label]["h3"],
                "warnings": _threshold_warnings(len(reached), len(valid_condition_rows), label_events),
            }
        )
    return output


def threshold_by_condition_rows(trajectories: list[Trajectory]) -> list[dict[str, Any]]:
    events = _threshold_events_by_cell(trajectories)
    grouped: dict[tuple[str, int], list[tuple[Trajectory, dict[str, Any]]]] = defaultdict(list)
    for trajectory in trajectories:
        for label, event in events[trajectory.cell_id].items():
            grouped[(label, trajectory.parameter_set)].append((trajectory, event))
    output = []
    for (label, parameter_set), rows in sorted(grouped.items()):
        reached = [event for _, event in rows if event["event_checkup_k"] is not None]
        checkups = [int(event["event_checkup_k"]) for event in reached]
        first_trajectory = rows[0][0]
        spread = max(checkups) - min(checkups) if len(checkups) > 1 else 0.0 if checkups else None
        output.append(
            {
                "threshold_label": label,
                "parameter_set": parameter_set,
                "n_replicates": len(rows),
                "n_reaching_threshold": len(reached),
                "median_event_checkup_k": _median([float(value) for value in checkups]) if checkups else None,
                "event_spread_checkups": spread,
                "replicate_consistent_within_1_checkup": bool(spread is not None and spread <= 1),
                "replicate_consistent_within_2_checkups": bool(spread is not None and spread <= 2),
                "aging_mode": str(first_trajectory.metadata.get("aging_mode", "")),
                "nominal_temperature_C": _as_float(first_trajectory.metadata.get("nominal_temperature_C")),
                "voltage_window_family": str(first_trajectory.metadata.get("voltage_window_family", "")),
                "nominal_charge_C_rate": _as_float(first_trajectory.metadata.get("nominal_charge_C_rate")),
                "nominal_discharge_C_rate": _as_float(first_trajectory.metadata.get("nominal_discharge_C_rate")),
                "profile_label": str(first_trajectory.metadata.get("profile_label", "")),
            }
        )
    return output


def threshold_claim_readiness_rows(stability_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    best = _best_threshold_row(stability_rows)
    if best is None:
        best_status = "not_supported"
        evidence = "No threshold event reached enough cells for diagnostics."
    else:
        consistency = _as_float(best.get("replicate_consistency_within_2_checkups"), default=0.0)
        coverage = _as_float(best.get("condition_coverage_fraction"), default=0.0)
        median_k = _as_float(best.get("median_event_checkup_k"))
        if consistency >= 0.8 and coverage >= 0.5:
            best_status = "partially_supported"
        else:
            best_status = "diagnostic_only"
        evidence = (
            f"Best label={best['threshold_label']}, consistency_within_2={consistency:.3f}, "
            f"condition_coverage={coverage:.3f}, median_event_checkup={_fmt(median_k)}."
        )
    return [
        {
            "claim_area": "Threshold-event label stability",
            "status": best_status,
            "evidence": evidence,
        },
        {
            "claim_area": "Threshold-event warning usefulness",
            "status": "diagnostic_only",
            "evidence": "Threshold events may be stable but can be late degradation milestones rather than early-warning targets.",
        },
        {
            "claim_area": "Threshold-event prediction readiness",
            "status": "blocked" if best_status != "partially_supported" else "possible_next_gate",
            "evidence": "No prediction model is trained in this label-readiness milestone.",
        },
    ]


def _condition_metadata(interval_rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    output: dict[int, dict[str, Any]] = {}
    for row in interval_rows:
        parameter_set = int(row["parameter_set"])
        output.setdefault(
            parameter_set,
            {
                "aging_mode": str(row.get("aging_mode", "")),
                "nominal_temperature_C": _as_float(row.get("nominal_temperature_C")),
                "voltage_window_family": str(row.get("voltage_window_family", "")),
                "nominal_charge_C_rate": _as_float(row.get("nominal_charge_C_rate")),
                "nominal_discharge_C_rate": _as_float(row.get("nominal_discharge_C_rate")),
                "profile_label": str(row.get("profile_label", "")),
            },
        )
    return output


def _primary_rows_by_condition(candidate_rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if (
            row["detector_name"] == PRIMARY_DETECTOR
            and row["x_axis"] == PRIMARY_X_AXIS
            and row["smoothing_policy"] == PRIMARY_SMOOTHING
        ):
            grouped[int(row["parameter_set"])].append(row)
    return grouped


def _trajectory_value_at_checkup(trajectory: Trajectory, field: str, checkup_k: int) -> float | None:
    values = getattr(trajectory, field)
    for idx, value in enumerate(trajectory.checkup_k):
        if int(value) == checkup_k and math.isfinite(float(values[idx])):
            return float(values[idx])
    return None


def _threshold_events_by_cell(trajectories: list[Trajectory]) -> dict[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, dict[str, Any]]] = {}
    for trajectory in trajectories:
        cell_events: dict[str, dict[str, Any]] = {}
        for threshold in THRESHOLD_FRACTIONS:
            crossing_indices = np.flatnonzero(np.isfinite(trajectory.soh) & (trajectory.soh <= threshold))
            idx = int(crossing_indices[0]) if len(crossing_indices) else None
            base = {
                "threshold_fraction": threshold,
                "event_checkup_k": int(trajectory.checkup_k[idx]) if idx is not None else None,
                "event_days": float(trajectory.calendar_days[idx]) if idx is not None else None,
                "event_efc": float(trajectory.log_age_efc_cumulative[idx]) if idx is not None else None,
                "quality_flags": ";".join(trajectory.quality_flags) if trajectory.quality_flags else "none",
            }
            pct = int(round(threshold * 100))
            cell_events[f"soh_below_{pct}"] = dict(base)
            cell_events[f"capacity_below_{pct}pct_initial"] = dict(base)
        output[trajectory.cell_id] = cell_events
    return output


def _interval_start_days_by_cell(interval_rows: list[dict[str, Any]]) -> dict[tuple[str, int], float]:
    first_time_by_cell: dict[str, float] = {}
    for row in interval_rows:
        cell_id = str(row["cell_id"])
        first_time_by_cell[cell_id] = min(
            first_time_by_cell.get(cell_id, math.inf),
            _as_float(row.get("t_result_k_s")),
        )
    output = {}
    for row in interval_rows:
        cell_id = str(row["cell_id"])
        first_time = first_time_by_cell.get(cell_id, math.nan)
        output[(cell_id, int(row["checkup_k"]))] = (_as_float(row.get("t_result_k_s")) - first_time) / 86400.0
    return output


def _threshold_warnings(reached_cells: int, covered_conditions: int, events: list[dict[str, Any]]) -> str:
    warnings = []
    if reached_cells < 0.5 * len(events):
        warnings.append("sparse_cell_coverage")
    if covered_conditions < 0.5 * 76:
        warnings.append("sparse_condition_coverage")
    event_ks = [float(event["event_checkup_k"]) for event in events if event["event_checkup_k"] is not None]
    median_k = _median(event_ks)
    if median_k is not None and median_k <= 2:
        warnings.append("possibly_too_early")
    if median_k is not None and median_k >= 24:
        warnings.append("possibly_too_late")
    return ";".join(warnings) or "none"


def _best_threshold_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [
        row
        for row in rows
        if row.get("replicate_consistency_within_2_checkups") is not None
        and _as_float(row.get("condition_coverage_fraction"), default=0.0) > 0
    ]
    if not eligible:
        return None
    ready = [
        row
        for row in eligible
        if _as_float(row.get("replicate_consistency_within_2_checkups"), default=0.0) >= 0.8
        and _as_float(row.get("condition_coverage_fraction"), default=0.0) >= 0.5
    ]
    if ready:
        return max(
            ready,
            key=lambda row: (
                _as_float(row.get("condition_coverage_fraction"), default=0.0),
                _as_float(row.get("replicate_consistency_within_2_checkups"), default=0.0),
                _as_float(row.get("cell_coverage_fraction"), default=0.0),
            ),
        )
    return max(
        eligible,
        key=lambda row: (
            _as_float(row.get("replicate_consistency_within_2_checkups"), default=0.0),
            _as_float(row.get("condition_coverage_fraction"), default=0.0),
            _as_float(row.get("cell_coverage_fraction"), default=0.0),
        ),
    )


def _write_knee_inconsistency_forensics(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# Knee Inconsistency Forensics",
        "",
        "This report diagnoses primary detector replicate inconsistency. It does not authorize knee prediction.",
        "",
        f"Inconsistent primary-valid conditions: {len(rows)}",
        "",
    ]
    if rows:
        max_spread = max(_as_float(row["knee_spread_checkups"]) for row in rows)
        severe = sum(row["trajectory_qa_flags"] != "none" for row in rows)
        lines.extend(
            [
                f"Maximum knee spread: {max_spread:.3g} check-ups",
                f"Conditions with severe trajectory QA flags: {severe}",
                "",
                "Interpretation: replicate inconsistency is treated as a label-stability failure, not as a model target.",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_threshold_claim_readiness(rows: list[dict[str, str]], path: Path) -> None:
    lines = [
        "# Threshold-Event Claim Readiness",
        "",
        "This report evaluates threshold-event label stability only. It does not train or authorize prediction models.",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_knee_vs_threshold_decision(
    candidates_path: Path | None,
    threshold_rows: list[dict[str, Any]],
    out_path: Path,
    candidate_rows: list[dict[str, Any]] | None = None,
) -> None:
    best = _best_threshold_row(threshold_rows)
    knee_consistency = None
    if candidate_rows is not None:
        replicate_rows = replicate_consistency_rows(candidate_rows)
        primary = [
            row
            for row in replicate_rows
            if row["detector_name"] == PRIMARY_DETECTOR
            and row["x_axis"] == PRIMARY_X_AXIS
            and row["smoothing_policy"] == PRIMARY_SMOOTHING
            and row["n_valid_knees"]
        ]
        knee_consistency = (
            sum(bool(row["replicate_consistent_within_2_checkups"]) for row in primary) / len(primary)
            if primary
            else None
        )
    lines = [
        "# Knee vs Threshold Decision",
        "",
        "This is a target-readiness comparison. It does not authorize a prediction model.",
        "",
    ]
    if knee_consistency is not None:
        lines.append(f"Primary knee replicate consistency within 2 check-ups: {knee_consistency:.3f}")
    if best is not None:
        consistency = _as_float(best.get("replicate_consistency_within_2_checkups"), default=0.0)
        coverage = _as_float(best.get("condition_coverage_fraction"), default=0.0)
        lines.extend(
            [
                f"Best threshold label: `{best['threshold_label']}`",
                f"Best threshold replicate consistency within 2 check-ups: {consistency:.3f}",
                f"Best threshold condition coverage: {coverage:.3f}",
                f"Best threshold median event check-up: {_fmt(best.get('median_event_checkup_k'))}",
                "",
            ]
        )
        if knee_consistency is not None and consistency > knee_consistency:
            lines.append("Threshold events are more replicate-consistent than detector knees in this diagnostic.")
        else:
            lines.append("Threshold events do not clearly dominate detector knees on replicate consistency.")
    else:
        lines.append("No threshold label has enough crossings for a stable comparison.")
    if candidates_path is not None:
        lines.append(f"\nSource knee candidates: `{candidates_path}`")
    lines.append("\nDetector-knee prediction remains blocked. Threshold-event labels remain a candidate next gate only if stability and timing are acceptable.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _detect_knee(detector: str, x: np.ndarray, capacity: np.ndarray, soh: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(x) & np.isfinite(capacity) & np.isfinite(soh)
    x = x[finite]
    capacity = capacity[finite]
    soh = soh[finite]
    if len(x) < 5:
        return _empty_detection("too_few_points")
    if detector.startswith("capacity_threshold_"):
        threshold = float(detector.rsplit("_", maxsplit=1)[-1]) / 100.0
        indices = np.flatnonzero(soh <= threshold)
        if not len(indices):
            return _empty_detection("threshold_not_reached")
        return _detection_from_index(int(indices[0]), x, capacity, soh, "threshold_reference")
    if detector == "max_chord_distance":
        return _max_chord_detection(x, capacity, soh)
    if detector == "piecewise_linear_bic":
        return _piecewise_detection(x, capacity, soh, use_bic=True)
    if detector == "two_line_l_method":
        return _piecewise_detection(x, capacity, soh, use_bic=False)
    if detector == "slope_change_threshold":
        return _slope_change_detection(x, capacity, soh)
    return _empty_detection("unknown_detector")


def _piecewise_detection(x: np.ndarray, capacity: np.ndarray, soh: np.ndarray, use_bic: bool) -> dict[str, Any]:
    if len(x) < 6 or len(np.unique(x)) < 5:
        return _empty_detection("too_few_unique_points")
    best_idx: int | None = None
    best_score = math.inf
    for idx in range(2, len(x) - 2):
        left = _linear_sse(x[: idx + 1], capacity[: idx + 1])
        right = _linear_sse(x[idx:], capacity[idx:])
        score = left + right
        if use_bic:
            score += 4 * math.log(len(x))
        if score < best_score:
            best_score = score
            best_idx = idx
    if best_idx is None:
        return _empty_detection("no_valid_split")
    return _detection_from_index(best_idx, x, capacity, soh, "")


def _max_chord_detection(x: np.ndarray, capacity: np.ndarray, soh: np.ndarray) -> dict[str, Any]:
    x_span = x[-1] - x[0]
    y_span = capacity[-1] - capacity[0]
    denom = math.hypot(float(x_span), float(y_span))
    if denom <= 0:
        return _empty_detection("degenerate_chord")
    distances = np.abs(y_span * x - x_span * capacity + x[-1] * capacity[0] - capacity[-1] * x[0]) / denom
    idx = int(np.argmax(distances))
    if idx == 0 or idx == len(x) - 1:
        return _empty_detection("edge_knee")
    return _detection_from_index(idx, x, capacity, soh, "")


def _slope_change_detection(x: np.ndarray, capacity: np.ndarray, soh: np.ndarray) -> dict[str, Any]:
    dx = np.diff(x)
    dy = np.diff(capacity)
    finite = np.isfinite(dx) & np.isfinite(dy) & (np.abs(dx) > 1e-12)
    slopes = np.full(len(dx), np.nan)
    slopes[finite] = dy[finite] / dx[finite]
    if np.isfinite(slopes).sum() < 4:
        return _empty_detection("too_few_slopes")
    changes = np.abs(np.diff(slopes))
    if not np.isfinite(changes).any():
        return _empty_detection("no_slope_change")
    idx = int(np.nanargmax(changes)) + 1
    result = _detection_from_index(idx, x, capacity, soh, "")
    if result["slope_change_ratio"] is not None and result["slope_change_ratio"] < 1.25:
        result["detector_quality_flags"] = "weak_slope_change"
    return result


def _detection_from_index(
    idx: int,
    x: np.ndarray,
    capacity: np.ndarray,
    soh: np.ndarray,
    extra_flag: str,
) -> dict[str, Any]:
    pre_slope = _slope(x[: idx + 1], capacity[: idx + 1])
    post_slope = _slope(x[idx:], capacity[idx:])
    ratio = abs(post_slope) / max(abs(pre_slope), 1e-12) if pre_slope is not None and post_slope is not None else None
    return {
        "knee_index": idx,
        "knee_checkup_k": int(round(float(x[idx]))) if np.allclose(x, np.round(x), equal_nan=False) else None,
        "knee_x_value": float(x[idx]),
        "knee_capacity_Ah": float(capacity[idx]),
        "knee_soh": float(soh[idx]),
        "pre_knee_slope": pre_slope,
        "post_knee_slope": post_slope,
        "slope_change_ratio": ratio,
        "detector_quality_flags": extra_flag,
    }


def _empty_detection(flag: str) -> dict[str, Any]:
    return {
        "knee_index": None,
        "knee_checkup_k": None,
        "knee_x_value": None,
        "knee_capacity_Ah": None,
        "knee_soh": None,
        "pre_knee_slope": None,
        "post_knee_slope": None,
        "slope_change_ratio": None,
        "detector_quality_flags": flag or "no_valid_knee",
    }


def _candidate_row(
    trajectory: Trajectory,
    detector: str,
    x_axis: str,
    smoothing: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    knee_checkup = result["knee_checkup_k"]
    if knee_checkup is None and result["knee_index"] is not None:
        knee_checkup = int(trajectory.checkup_k[int(result["knee_index"])])
    return {
        "cell_id": trajectory.cell_id,
        "parameter_set": trajectory.parameter_set,
        "replicate_id": trajectory.replicate_id,
        "aging_mode": str(trajectory.metadata["aging_mode"]),
        "nominal_temperature_C": float(trajectory.metadata["nominal_temperature_C"]),
        "voltage_window_family": str(trajectory.metadata["voltage_window_family"]),
        "nominal_charge_C_rate": float(trajectory.metadata["nominal_charge_C_rate"]),
        "profile_label": str(trajectory.metadata["profile_label"]),
        "detector_name": detector,
        "x_axis": x_axis,
        "smoothing_policy": smoothing,
        "knee_checkup_k": knee_checkup,
        "knee_x_value": result["knee_x_value"],
        "knee_capacity_Ah": result["knee_capacity_Ah"],
        "knee_soh": result["knee_soh"],
        "pre_knee_slope": result["pre_knee_slope"],
        "post_knee_slope": result["post_knee_slope"],
        "slope_change_ratio": result["slope_change_ratio"],
        "detector_quality_flags": ";".join(filter(None, (*trajectory.quality_flags, result["detector_quality_flags"]))),
        "schema_version": SCHEMA_VERSION,
    }


def _smooth(values: np.ndarray, policy: str) -> np.ndarray:
    if policy != "rolling_3" or len(values) < 3:
        return values.copy()
    output = values.copy()
    for idx in range(1, len(values) - 1):
        window = values[idx - 1 : idx + 2]
        finite = window[np.isfinite(window)]
        output[idx] = float(np.mean(finite)) if len(finite) else np.nan
    return output


def _trajectory_axis(trajectory: Trajectory, x_axis: str) -> np.ndarray:
    if x_axis == "checkup_index":
        return trajectory.checkup_k
    return getattr(trajectory, x_axis)


def _linear_sse(x: np.ndarray, y: np.ndarray) -> float:
    finite = np.isfinite(x) & np.isfinite(y)
    if finite.sum() < 2 or len(np.unique(x[finite])) < 2:
        return math.inf
    coeff = np.polyfit(x[finite], y[finite], 1)
    pred = coeff[0] * x[finite] + coeff[1]
    return float(np.sum((y[finite] - pred) ** 2))


def _slope(x: np.ndarray, y: np.ndarray) -> float | None:
    finite = np.isfinite(x) & np.isfinite(y)
    if finite.sum() < 2 or len(np.unique(x[finite])) < 2:
        return None
    coeff = np.polyfit(x[finite], y[finite], 1)
    return float(coeff[0])


def _sensitivity_rows(
    candidate_rows: list[dict[str, Any]],
    group_fields: tuple[str, ...],
    vary: str,
) -> list[float]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[tuple(row[field] for field in group_fields)].append(row)
    diffs = []
    for rows in grouped.values():
        by_value = {
            str(row[vary]): int(row["knee_checkup_k"])
            for row in rows
            if _as_int(row.get("knee_checkup_k")) is not None
        }
        if len(by_value) < 2:
            continue
        values = list(by_value.values())
        diffs.append(float(max(values) - min(values)))
    return diffs


def _sensitivity_summary(diffs: list[float]) -> dict[str, Any]:
    return {
        "n_comparisons": len(diffs),
        "median_abs_disagreement_checkups": _median(diffs) if diffs else None,
        "mean_abs_disagreement_checkups": _mean(diffs) if diffs else None,
        "agreement_within_2_checkups": sum(value <= 2 for value in diffs) / len(diffs) if diffs else None,
    }


def _write_claim_readiness(rows: list[dict[str, str]], path: Path) -> None:
    lines = [
        "# Knee Claim Readiness",
        "",
        "This report evaluates label stability only. It does not authorize knee prediction.",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _time_to_knee_days(intervals: list[dict[str, Any]], cell_id: str, checkup_k: int, knee_k: int | None) -> float | None:
    if knee_k is None:
        return None
    by_cell = [row for row in intervals if str(row["cell_id"]) == cell_id]
    start = next((_as_float(row["t_result_k_s"]) for row in by_cell if int(row["checkup_k"]) == checkup_k), None)
    end = next((_as_float(row["t_result_k_s"]) for row in by_cell if int(row["checkup_k"]) == knee_k), None)
    if start is None:
        return None
    if end is None:
        end = next((_as_float(row["t_result_k1_s"]) for row in by_cell if int(row["checkup_k_next"]) == knee_k), None)
    return (end - start) / 86400.0 if end is not None else None


def _as_float(value: Any, default: float = math.nan) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if math.isfinite(output) else default


def _as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        output = int(value)
    except (TypeError, ValueError):
        return None
    return output


def _mean(values: list[float]) -> float | None:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else None


def _median(values: list[float]) -> float | None:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return None
    mid = len(finite) // 2
    return finite[mid] if len(finite) % 2 else (finite[mid - 1] + finite[mid]) / 2.0


def _first(rows: list[dict[str, Any]], field: str) -> Any:
    return rows[0].get(field) if rows else None


def _fmt(value: Any) -> str:
    number = _as_float(value)
    return "NA" if not math.isfinite(number) else f"{number:.3g}"
