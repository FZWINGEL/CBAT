"""Milestone 0.8 capacity/PULSE scalar coupling diagnostics."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "gate8.capacity_pulse_coupling.v2"

COUPLING_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("cell_id", pa.string()),
        ("parameter_set", pa.int32()),
        ("replicate_id", pa.int32()),
        ("checkup_k", pa.int32()),
        ("checkup_k_next", pa.int32()),
        ("capacity_Ah_k", pa.float64()),
        ("capacity_Ah_k1", pa.float64()),
        ("delta_capacity_Ah", pa.float64()),
        ("pulse_1s_resistance_k", pa.float64()),
        ("pulse_1s_resistance_k1", pa.float64()),
        ("delta_pulse_1s_resistance", pa.float64()),
        ("pulse_10ms_resistance_k", pa.float64()),
        ("pulse_10ms_resistance_k1", pa.float64()),
        ("delta_pulse_10ms_resistance", pa.float64()),
        ("condition_fold", pa.int32()),
        ("temperature_holdout_fold", pa.int32()),
        ("c_rate_holdout_fold", pa.int32()),
        ("profile_holdout_fold", pa.int32()),
        ("voltage_window_holdout_fold", pa.int32()),
        ("aging_mode", pa.string()),
        ("nominal_temperature_C", pa.float64()),
        ("voltage_window_family", pa.string()),
        ("nominal_charge_C_rate", pa.float64()),
        ("log_age_efc_delta", pa.float64()),
        ("calendar_days", pa.float64()),
        ("quality_flags", pa.string()),
    ]
)


def build_capacity_pulse_coupling_table(
    interval_table_path: Path,
    pulse_targets_path: Path,
    out_path: Path,
) -> pa.Table:
    """Build one row per interval with finite capacity and canonical PULSE targets."""
    intervals = pq.read_table(interval_table_path).to_pylist()
    pulse_rows = pq.read_table(pulse_targets_path).to_pylist()
    pulse_by_key = {_interval_key(row): row for row in pulse_rows}
    rows: list[dict[str, Any]] = []
    for interval in intervals:
        pulse = pulse_by_key.get(_interval_key(interval))
        if pulse is None:
            continue
        required = (
            interval.get("capacity_Ah_k"),
            interval.get("capacity_Ah_k1"),
            interval.get("delta_capacity_Ah"),
            pulse.get("pulse_1s_resistance_k"),
            pulse.get("pulse_1s_resistance_k1"),
            pulse.get("delta_pulse_1s_resistance"),
        )
        if not all(math.isfinite(_as_float(value)) for value in required):
            continue
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "cell_id": str(interval["cell_id"]),
                "parameter_set": int(interval["parameter_set"]),
                "replicate_id": int(interval["replicate_id"]),
                "checkup_k": int(interval["checkup_k"]),
                "checkup_k_next": int(interval["checkup_k_next"]),
                "capacity_Ah_k": _as_float(interval.get("capacity_Ah_k")),
                "capacity_Ah_k1": _as_float(interval.get("capacity_Ah_k1")),
                "delta_capacity_Ah": _as_float(interval.get("delta_capacity_Ah")),
                "pulse_1s_resistance_k": _as_float(pulse.get("pulse_1s_resistance_k")),
                "pulse_1s_resistance_k1": _as_float(pulse.get("pulse_1s_resistance_k1")),
                "delta_pulse_1s_resistance": _as_float(pulse.get("delta_pulse_1s_resistance")),
                "pulse_10ms_resistance_k": _as_float(pulse.get("pulse_10ms_resistance_k")),
                "pulse_10ms_resistance_k1": _as_float(pulse.get("pulse_10ms_resistance_k1")),
                "delta_pulse_10ms_resistance": _as_float(pulse.get("delta_pulse_10ms_resistance")),
                "condition_fold": int(interval["condition_fold"]),
                "temperature_holdout_fold": int(interval["temperature_holdout_fold"]),
                "c_rate_holdout_fold": int(interval["c_rate_holdout_fold"]),
                "profile_holdout_fold": int(interval["profile_holdout_fold"]),
                "voltage_window_holdout_fold": int(interval["voltage_window_holdout_fold"]),
                "aging_mode": str(interval.get("aging_mode", "")),
                "nominal_temperature_C": _as_float(interval.get("nominal_temperature_C")),
                "voltage_window_family": str(interval.get("voltage_window_family", "")),
                "nominal_charge_C_rate": _as_float(interval.get("nominal_charge_C_rate")),
                "log_age_efc_delta": _as_float(interval.get("log_age_efc_delta")),
                "calendar_days": _as_float(interval.get("calendar_days")),
                "quality_flags": str(pulse.get("quality_flags", "")),
            }
        )
    table = pa.Table.from_pylist(rows, schema=COUPLING_SCHEMA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"interval_table_path": str(interval_table_path).encode(),
                b"pulse_targets_path": str(pulse_targets_path).encode(),
            }
        ),
        out_path,
    )
    return table


def write_pulse_capacity_diagnostics(
    capacity_report_path: Path,
    capacity_predictions_path: Path,
    pulse_targets_path: Path,
    interval_table_path: Path,
    out_dir: Path,
    *,
    coupling_table_out: Path | None = None,
) -> dict[str, Any]:
    """Write scalar coupling diagnostics between capacity residuals and PULSE growth."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    coupling_path = coupling_table_out or out_dir / "capacity_pulse_coupling_table.parquet"
    table = build_capacity_pulse_coupling_table(interval_table_path, pulse_targets_path, coupling_path)
    coupling_rows = table.to_pylist()
    coupling_by_key = {_interval_key(row): row for row in coupling_rows}
    prediction_rows = pq.read_table(capacity_predictions_path).to_pylist()
    joined = _joined_residual_rows(prediction_rows, coupling_by_key)

    correlation_rows = _correlation_rows(joined)
    residual_vs_pulse = _residual_vs_pulse_rows(joined)
    by_bin = _residual_by_pulse_growth_bin(joined)
    c_rate_rows = [row for row in residual_vs_pulse if row["split_name"] == "c_rate_holdout_fold"]
    decile_rows = _pulse_growth_by_capacity_error_decile(joined)

    _write_csv(plots_dir / "capacity_residual_vs_delta_pulse.csv", residual_vs_pulse)
    _write_csv(plots_dir / "capacity_residual_by_pulse_growth_bin.csv", by_bin)
    _write_csv(plots_dir / "c_rate_capacity_residual_by_pulse_growth.csv", c_rate_rows)
    _write_csv(plots_dir / "pulse_growth_by_capacity_error_decile.csv", decile_rows)
    _write_correlation_md(
        capacity_report_path,
        capacity_predictions_path,
        coupling_path,
        correlation_rows,
        out_dir / "pulse_capacity_correlation.md",
    )
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "capacity_report": str(capacity_report_path),
            "capacity_predictions": str(capacity_predictions_path),
            "pulse_targets": str(pulse_targets_path),
            "interval_table": str(interval_table_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "coupling_table": str(coupling_path),
        },
        "row_counts": {
            "coupling_rows": len(coupling_rows),
            "joined_prediction_rows": len(joined),
        },
        "correlations": correlation_rows,
    }
    (out_dir / "pulse_capacity_correlation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def write_pulse_capacity_robustness_diagnostics(
    capacity_report_path: Path,
    capacity_predictions_path: Path,
    pulse_targets_path: Path,
    interval_table_path: Path,
    out_dir: Path,
    *,
    model_level: str = "L2_hist_gradient_boosting",
    feature_group: str = "F4_state_log_age_scalar",
    target: str = "capacity_Ah_k1",
    split: str = "all",
    bootstrap_resamples: int = 1000,
    seed: int = 42,
    coupling_table_out: Path | None = None,
) -> dict[str, Any]:
    """Write canonical-model, aggregated, and confound-control coupling diagnostics."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    coupling_path = coupling_table_out or out_dir / "capacity_pulse_coupling_table.parquet"
    table = build_capacity_pulse_coupling_table(interval_table_path, pulse_targets_path, coupling_path)
    coupling_rows = table.to_pylist()
    coupling_by_key = {_interval_key(row): row for row in coupling_rows}
    prediction_rows = pq.read_table(capacity_predictions_path).to_pylist()
    joined = _joined_residual_rows(prediction_rows, coupling_by_key)
    canonical = _canonical_rows(
        joined,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
        split=split,
    )
    interval_rows = _interval_level_rows(canonical)
    condition_rows = _condition_level_rows(interval_rows)
    canonical_corr = _scope_correlation_rows(canonical, level="canonical_prediction_row")
    interval_corr = _scope_correlation_rows(interval_rows, level="interval")
    condition_corr = _scope_correlation_rows(condition_rows, level="condition")
    bootstrap_rows = _bootstrap_correlation_rows(interval_rows, condition_rows, bootstrap_resamples, seed)
    residualized_rows = _residualized_correlation_rows(interval_rows)
    subgroup_rows = _subgroup_correlation_rows(interval_rows)

    _write_csv(plots_dir / "canonical_model_residual_vs_pulse.csv", _canonical_plot_rows(canonical))
    _write_csv(plots_dir / "canonical_model_correlation_by_split.csv", canonical_corr)
    _write_csv(plots_dir / "interval_level_pulse_capacity_correlation.csv", interval_corr)
    _write_csv(plots_dir / "condition_level_pulse_capacity_correlation.csv", condition_corr)
    _write_csv(plots_dir / "pulse_capacity_correlation_bootstrap.csv", bootstrap_rows)
    _write_csv(plots_dir / "residualized_pulse_capacity_correlation.csv", residualized_rows)
    _write_csv(plots_dir / "subgroup_pulse_capacity_correlation.csv", subgroup_rows)

    _write_correlation_table_md(
        "Canonical Model Correlation",
        [
            "These rows are filtered to one model, feature group, target, and optional split.",
            f"Selection: `{model_level}` + `{feature_group}` + `{target}` + split `{split}`.",
        ],
        canonical_corr,
        out_dir / "canonical_model_correlation.md",
    )
    _write_correlation_table_md(
        "Interval-Level Correlation",
        ["Rows are unique physical intervals after canonical-model filtering."],
        interval_corr,
        out_dir / "interval_level_correlation.md",
    )
    _write_correlation_table_md(
        "Condition-Level Correlation",
        ["Rows are parameter-set condition aggregates."],
        condition_corr,
        out_dir / "condition_level_correlation.md",
    )
    _write_bootstrap_summary_md(
        bootstrap_rows,
        out_dir / "bootstrap_correlation_summary.md",
        resamples=bootstrap_resamples,
        seed=seed,
    )
    _write_correlation_table_md(
        "Residualized Correlation",
        [
            "Residualization controls for observed state and condition metadata.",
            "This is a diagnostic association check, not causal evidence.",
        ],
        residualized_rows,
        out_dir / "residualized_correlation.md",
    )
    _write_correlation_table_md(
        "Subgroup Coupling Summary",
        ["Subgroups test whether coupling is concentrated in C-rate/cold-rate regimes."],
        subgroup_rows,
        out_dir / "subgroup_coupling_summary.md",
    )
    _write_claim_readiness(
        interval_corr,
        condition_corr,
        residualized_rows,
        subgroup_rows,
        out_dir / "coupling_claim_readiness.md",
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "selection": {
            "model_level": model_level,
            "feature_group": feature_group,
            "target": target,
            "split": split,
        },
        "inputs": {
            "capacity_report": str(capacity_report_path),
            "capacity_predictions": str(capacity_predictions_path),
            "pulse_targets": str(pulse_targets_path),
            "interval_table": str(interval_table_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "coupling_table": str(coupling_path),
        },
        "row_counts": {
            "coupling_rows": len(coupling_rows),
            "joined_prediction_rows": len(joined),
            "canonical_prediction_rows": len(canonical),
            "interval_rows": len(interval_rows),
            "condition_rows": len(condition_rows),
        },
        "canonical_correlations": canonical_corr,
        "interval_correlations": interval_corr,
        "condition_correlations": condition_corr,
        "residualized_correlations": residualized_rows,
        "subgroup_correlations": subgroup_rows,
    }
    (out_dir / "pulse_capacity_robustness_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _joined_residual_rows(
    prediction_rows: list[dict[str, Any]],
    coupling_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pred in prediction_rows:
        if str(pred.get("run_scope")) != "primary":
            continue
        coupling = coupling_by_key.get(_interval_key(pred))
        if coupling is None:
            continue
        y_true = _as_float(pred.get("y_true"))
        y_pred = _as_float(pred.get("y_pred"))
        pulse_delta = _as_float(coupling.get("delta_pulse_1s_resistance"))
        if not all(math.isfinite(value) for value in (y_true, y_pred, pulse_delta)):
            continue
        residual = y_pred - y_true
        rows.append(
            {
                **{key: coupling.get(key) for key in (
                    "cell_id",
                    "parameter_set",
                    "replicate_id",
                    "checkup_k",
                    "checkup_k_next",
                    "capacity_Ah_k",
                    "log_age_efc_delta",
                    "calendar_days",
                    "aging_mode",
                    "nominal_temperature_C",
                    "voltage_window_family",
                    "nominal_charge_C_rate",
                    "condition_fold",
                    "temperature_holdout_fold",
                    "c_rate_holdout_fold",
                    "profile_holdout_fold",
                    "voltage_window_holdout_fold",
                )},
                "split_name": pred["split_name"],
                "model_level": pred["model_level"],
                "feature_group": pred["feature_group"],
                "target": pred["target"],
                "capacity_residual": residual,
                "capacity_abs_residual": abs(residual),
                "delta_pulse_1s_resistance": pulse_delta,
                "delta_pulse_10ms_resistance": _as_float(coupling.get("delta_pulse_10ms_resistance")),
                "cold_c_rate_subgroup": _cold_c_rate(coupling),
            }
        )
    return rows


def _correlation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    groups = {
        "all": rows,
        "c_rate": [row for row in rows if row["split_name"] == "c_rate_holdout_fold"],
        "cold_c_rate": [row for row in rows if row["split_name"] == "c_rate_holdout_fold" and row["cold_c_rate_subgroup"]],
    }
    for scope, group in groups.items():
        for target in sorted({str(row["target"]) for row in group}):
            target_rows = [row for row in group if row["target"] == target]
            for residual_column in ("capacity_residual", "capacity_abs_residual"):
                x = [_as_float(row["delta_pulse_1s_resistance"]) for row in target_rows]
                y = [_as_float(row[residual_column]) for row in target_rows]
                output.append(
                    {
                        "scope": scope,
                        "target": target,
                        "residual_column": residual_column,
                        "n": len(target_rows),
                        "pearson": _pearson(x, y),
                        "spearman": _pearson(_ranks(x), _ranks(y)),
                    }
                )
    return output


def _residual_vs_pulse_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "split_name": row["split_name"],
            "model_level": row["model_level"],
            "feature_group": row["feature_group"],
            "target": row["target"],
            "parameter_set": row["parameter_set"],
            "nominal_temperature_C": row["nominal_temperature_C"],
            "voltage_window_family": row["voltage_window_family"],
            "capacity_residual": row["capacity_residual"],
            "capacity_abs_residual": row["capacity_abs_residual"],
            "delta_pulse_1s_resistance": row["delta_pulse_1s_resistance"],
            "delta_pulse_10ms_resistance": row["delta_pulse_10ms_resistance"],
            "cold_c_rate_subgroup": row["cold_c_rate_subgroup"],
        }
        for row in rows
    ]


def _residual_by_pulse_growth_bin(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for (split, target, bin_name), group in _group_by(
        rows,
        lambda row: (row["split_name"], row["target"], _pulse_growth_bin(row["delta_pulse_1s_resistance"])),
    ).items():
        output.append(
            {
                "split_name": split,
                "target": target,
                "pulse_growth_bin": bin_name,
                "n": len(group),
                "mean_abs_residual": _mean([row["capacity_abs_residual"] for row in group]),
                "signed_bias": _mean([row["capacity_residual"] for row in group]),
            }
        )
    return output


def _pulse_growth_by_capacity_error_decile(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda row: _as_float(row["capacity_abs_residual"]))
    if not sorted_rows:
        return []
    output = []
    for idx, row in enumerate(sorted_rows):
        decile = min(9, int(10 * idx / len(sorted_rows))) + 1
        output.append(
            {
                "error_decile": decile,
                "target": row["target"],
                "split_name": row["split_name"],
                "capacity_abs_residual": row["capacity_abs_residual"],
                "delta_pulse_1s_resistance": row["delta_pulse_1s_resistance"],
            }
        )
    return output


def _canonical_rows(
    rows: list[dict[str, Any]],
    *,
    model_level: str,
    feature_group: str,
    target: str,
    split: str,
) -> list[dict[str, Any]]:
    output = [
        row
        for row in rows
        if row["model_level"] == model_level
        and row["feature_group"] == feature_group
        and row["target"] == target
        and (split == "all" or row["split_name"] == split)
    ]
    if not output:
        raise ValueError(
            "No canonical prediction rows matched "
            f"model_level={model_level!r}, feature_group={feature_group!r}, target={target!r}, split={split!r}."
        )
    return output


def _canonical_plot_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "cell_id": row["cell_id"],
            "parameter_set": row["parameter_set"],
            "checkup_k": row["checkup_k"],
            "checkup_k_next": row["checkup_k_next"],
            "split_name": row["split_name"],
            "capacity_residual": row["capacity_residual"],
            "capacity_abs_residual": row["capacity_abs_residual"],
            "delta_pulse_1s_resistance": row["delta_pulse_1s_resistance"],
            "delta_pulse_10ms_resistance": row["delta_pulse_10ms_resistance"],
            "nominal_temperature_C": row["nominal_temperature_C"],
            "nominal_charge_C_rate": row["nominal_charge_C_rate"],
            "voltage_window_family": row["voltage_window_family"],
            "cold_c_rate_subgroup": row["cold_c_rate_subgroup"],
        }
        for row in rows
    ]


def _interval_level_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for key, group in _group_by(rows, _interval_key).items():
        first = group[0]
        output.append(
            {
                **_metadata_row(first),
                "level": "interval",
                "n_predictions": len(group),
                "capacity_residual": _mean([row["capacity_residual"] for row in group]),
                "capacity_abs_residual": _mean([row["capacity_abs_residual"] for row in group]),
                "delta_pulse_1s_resistance": _mean([row["delta_pulse_1s_resistance"] for row in group]),
                "delta_pulse_10ms_resistance": _mean([row["delta_pulse_10ms_resistance"] for row in group]),
                "interval_key": "|".join(str(part) for part in key),
            }
        )
    return output


def _condition_level_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for parameter_set, group in _group_by(rows, lambda row: int(row["parameter_set"])).items():
        first = group[0]
        output.append(
            {
                "level": "condition",
                "parameter_set": parameter_set,
                "n_intervals": len(group),
                "capacity_residual": _mean([row["capacity_residual"] for row in group]),
                "capacity_abs_residual": _mean([row["capacity_abs_residual"] for row in group]),
                "delta_pulse_1s_resistance": _mean([row["delta_pulse_1s_resistance"] for row in group]),
                "delta_pulse_10ms_resistance": _mean([row["delta_pulse_10ms_resistance"] for row in group]),
                "capacity_Ah_k": _mean([row["capacity_Ah_k"] for row in group]),
                "checkup_k": _mean([row["checkup_k"] for row in group]),
                "log_age_efc_delta": _mean([row["log_age_efc_delta"] for row in group]),
                "calendar_days": _mean([row["calendar_days"] for row in group]),
                "nominal_temperature_C": first["nominal_temperature_C"],
                "nominal_charge_C_rate": first["nominal_charge_C_rate"],
                "voltage_window_family": first["voltage_window_family"],
                "aging_mode": first["aging_mode"],
                "condition_fold": first["condition_fold"],
                "temperature_holdout_fold": first["temperature_holdout_fold"],
                "c_rate_holdout_fold": first["c_rate_holdout_fold"],
                "profile_holdout_fold": first["profile_holdout_fold"],
                "voltage_window_holdout_fold": first["voltage_window_holdout_fold"],
                "cold_c_rate_subgroup": any(bool(row["cold_c_rate_subgroup"]) for row in group),
            }
        )
    return output


def _scope_correlation_rows(rows: list[dict[str, Any]], *, level: str) -> list[dict[str, Any]]:
    output = []
    for scope, group in _robustness_groups(rows).items():
        for pulse_column in ("delta_pulse_1s_resistance", "delta_pulse_10ms_resistance"):
            for residual_column in ("capacity_residual", "capacity_abs_residual"):
                output.append(_correlation_summary(level, scope, group, pulse_column, residual_column))
    return output


def _subgroup_correlation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for scope, group in _robustness_groups(rows).items():
        output.append(
            _correlation_summary(
                "interval",
                scope,
                group,
                "delta_pulse_1s_resistance",
                "capacity_abs_residual",
            )
        )
    return output


def _robustness_groups(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "all": rows,
        "c_rate_holdout": [row for row in rows if int(row.get("c_rate_holdout_fold", 0)) != 0],
        "cold_c_rate": [row for row in rows if row.get("cold_c_rate_subgroup")],
        "voltage_window_approx_0_100": [
            row for row in rows if str(row.get("voltage_window_family")) == "approx_0_100"
        ],
        "voltage_window_approx_10_100": [
            row for row in rows if str(row.get("voltage_window_family")) == "approx_10_100"
        ],
        "profile_holdout": [row for row in rows if int(row.get("profile_holdout_fold", 0)) != 0],
    }


def _correlation_summary(
    level: str,
    scope: str,
    rows: list[dict[str, Any]],
    pulse_column: str,
    residual_column: str,
) -> dict[str, Any]:
    x = [_as_float(row.get(pulse_column)) for row in rows]
    y = [_as_float(row.get(residual_column)) for row in rows]
    return {
        "level": level,
        "scope": scope,
        "pulse_column": pulse_column,
        "residual_column": residual_column,
        "n": len([(a, b) for a, b in zip(x, y) if math.isfinite(a) and math.isfinite(b)]),
        "pearson": _pearson(x, y),
        "spearman": _pearson(_ranks(x), _ranks(y)),
    }


def _bootstrap_correlation_rows(
    interval_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
    resamples: int,
    seed: int,
) -> list[dict[str, Any]]:
    output = []
    for level, rows in (("interval", interval_rows), ("condition", condition_rows)):
        by_condition = _group_by(rows, lambda row: int(row["parameter_set"]))
        condition_ids = sorted(by_condition)
        if not condition_ids:
            continue
        rng = np.random.default_rng(seed)
        sampled: dict[tuple[str, str, str], list[float]] = {}
        for _ in range(max(1, resamples)):
            picked_ids = rng.choice(condition_ids, size=len(condition_ids), replace=True)
            sample = [row for condition_id in picked_ids for row in by_condition[int(condition_id)]]
            for pulse_column in ("delta_pulse_1s_resistance", "delta_pulse_10ms_resistance"):
                for residual_column in ("capacity_residual", "capacity_abs_residual"):
                    x = [_as_float(row[pulse_column]) for row in sample]
                    y = [_as_float(row[residual_column]) for row in sample]
                    sampled.setdefault((level, pulse_column, residual_column, "pearson"), []).append(_pearson(x, y))
                    sampled.setdefault((level, pulse_column, residual_column, "spearman"), []).append(
                        _pearson(_ranks(x), _ranks(y))
                    )
        for (level_name, pulse_column, residual_column, correlation), values in sampled.items():
            finite = sorted(value for value in values if math.isfinite(value))
            output.append(
                {
                    "level": level_name,
                    "pulse_column": pulse_column,
                    "residual_column": residual_column,
                    "correlation": correlation,
                    "resamples": len(finite),
                    "mean": _mean(finite),
                    "p05": _quantile(finite, 0.05),
                    "p50": _quantile(finite, 0.50),
                    "p95": _quantile(finite, 0.95),
                }
            )
    return output


def _residualized_correlation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for scope, group in _robustness_groups(rows).items():
        if len(group) < 3:
            output.append(
                {
                    "scope": scope,
                    "n": len(group),
                    "pulse_column": "delta_pulse_1s_resistance",
                    "residual_column": "capacity_abs_residual",
                    "pearson": math.nan,
                    "spearman": math.nan,
                }
            )
            continue
        residual_y = _linear_residuals(group, "capacity_abs_residual")
        residual_x = _linear_residuals(group, "delta_pulse_1s_resistance")
        output.append(
            {
                "scope": scope,
                "n": len(group),
                "pulse_column": "delta_pulse_1s_resistance",
                "residual_column": "capacity_abs_residual",
                "pearson": _pearson(residual_x, residual_y),
                "spearman": _pearson(_ranks(residual_x), _ranks(residual_y)),
            }
        )
    return output


def _linear_residuals(rows: list[dict[str, Any]], outcome: str) -> list[float]:
    y = np.array([_as_float(row.get(outcome)) for row in rows], dtype=float)
    x = _control_matrix(rows)
    finite = np.isfinite(y) & np.all(np.isfinite(x), axis=1)
    residuals = np.full(len(rows), math.nan, dtype=float)
    if int(finite.sum()) < 3:
        return residuals.tolist()
    beta, *_ = np.linalg.lstsq(x[finite], y[finite], rcond=None)
    residuals[finite] = y[finite] - x[finite].dot(beta)
    return residuals.tolist()


def _control_matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    numeric_columns = (
        "capacity_Ah_k",
        "checkup_k",
        "log_age_efc_delta",
        "nominal_temperature_C",
        "nominal_charge_C_rate",
    )
    categorical_columns = ("voltage_window_family", "aging_mode")
    numeric = []
    for row in rows:
        numeric.append([1.0, *[_as_float(row.get(column)) for column in numeric_columns]])
    matrices = [np.array(numeric, dtype=float)]
    for column in categorical_columns:
        values = sorted({str(row.get(column, "")) for row in rows})
        if len(values) <= 1:
            continue
        for value in values[1:]:
            matrices.append(np.array([[1.0 if str(row.get(column, "")) == value else 0.0] for row in rows]))
    return np.hstack(matrices)


def _write_correlation_table_md(
    title: str,
    notes: list[str],
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [f"# {title}", ""]
    for note in notes:
        lines.append(note)
    lines.extend(
        [
            "",
            "| Level | Scope | Pulse | Residual | n | Pearson | Spearman |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row.get('level', 'diagnostic')}` | `{row.get('scope', 'all')}` | "
            f"`{row.get('pulse_column', '')}` | `{row.get('residual_column', '')}` | "
            f"{row.get('n', row.get('resamples', ''))} | {_fmt(row.get('pearson', row.get('mean')))} | "
            f"{_fmt(row.get('spearman', row.get('p50')))} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_bootstrap_summary_md(
    rows: list[dict[str, Any]],
    path: Path,
    *,
    resamples: int,
    seed: int,
) -> None:
    lines = [
        "# Bootstrap Correlation Summary",
        "",
        "Bootstrap resampling is clustered by parameter_set.",
        f"Requested resamples: `{resamples}`; seed: `{seed}`.",
        "",
        "| Level | Pulse | Residual | Correlation | Resamples | Mean | p05 | p50 | p95 |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['level']}` | `{row['pulse_column']}` | `{row['residual_column']}` | "
            f"`{row['correlation']}` | {row['resamples']} | {_fmt(row['mean'])} | "
            f"{_fmt(row['p05'])} | {_fmt(row['p50'])} | {_fmt(row['p95'])} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_claim_readiness(
    interval_corr: list[dict[str, Any]],
    condition_corr: list[dict[str, Any]],
    residualized_rows: list[dict[str, Any]],
    subgroup_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    interval_all = _find_corr(interval_corr, "all", "delta_pulse_1s_resistance", "capacity_abs_residual")
    condition_all = _find_corr(condition_corr, "all", "delta_pulse_1s_resistance", "capacity_abs_residual")
    residualized_all = next((row for row in residualized_rows if row.get("scope") == "all"), {})
    c_rate = _find_corr(subgroup_rows, "c_rate_holdout", "delta_pulse_1s_resistance", "capacity_abs_residual")
    cold_c_rate = _find_corr(subgroup_rows, "cold_c_rate", "delta_pulse_1s_resistance", "capacity_abs_residual")
    lines = [
        "# Capacity-PULSE Coupling Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Decision |",
        "|---|---|---|---|",
        (
            "| Interval-level association | "
            f"{_status_from_corr(interval_all)} | Spearman `{_fmt(interval_all.get('spearman'))}` over "
            f"`{interval_all.get('n', 0)}` intervals | Explanatory diagnostic only |"
        ),
        (
            "| Condition-level association | "
            f"{_status_from_corr(condition_all)} | Spearman `{_fmt(condition_all.get('spearman'))}` over "
            f"`{condition_all.get('n', 0)}` conditions | Do not inflate prediction-row evidence |"
        ),
        (
            "| C-rate/cold-rate association | "
            f"{_status_from_corr(c_rate)} | C-rate Spearman `{_fmt(c_rate.get('spearman'))}`, "
            f"cold C-rate Spearman `{_fmt(cold_c_rate.get('spearman'))}` | Keep subgroup diagnostics |"
        ),
        (
            "| Confound-controlled association | "
            f"{_status_from_corr(residualized_all)} | Residualized Spearman "
            f"`{_fmt(residualized_all.get('spearman'))}` | Diagnostic, not causal evidence |"
        ),
        (
            "| Prior-PULSE capacity gain | partially_supported | Prior PULSE helps `capacity_Ah_k1` in 0.8 but "
            "not C-rate `delta_capacity_Ah` | Predictive claim not authorized |"
        ),
        (
            "| Leakage safety | supported_for_explanatory_diagnostics | Capacity feature groups allow "
            "`pulse_1s_resistance_k` only | Future PULSE targets remain blocked |"
        ),
        (
            "| Coverage limitation | partially_supported | PULSE-covered capacity rows drop one tolerant "
            "interval versus capacity-only | Report coverage in any follow-up |"
        ),
        (
            "| Predictive claim readiness | predictive_claim_not_authorized | Coupling remains diagnostic and "
            "delta target is unresolved | No broad capacity+PULSE claim |"
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _find_corr(
    rows: list[dict[str, Any]],
    scope: str,
    pulse_column: str,
    residual_column: str,
) -> dict[str, Any]:
    return next(
        (
            row
            for row in rows
            if row.get("scope") == scope
            and row.get("pulse_column") == pulse_column
            and row.get("residual_column") == residual_column
        ),
        {},
    )


def _status_from_corr(row: dict[str, Any]) -> str:
    spearman = abs(_as_float(row.get("spearman")))
    if not math.isfinite(spearman):
        return "not_supported"
    if spearman >= 0.5:
        return "supported_for_explanatory_diagnostics"
    if spearman >= 0.25:
        return "partially_supported"
    return "not_supported"


def _metadata_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_id": row["cell_id"],
        "parameter_set": row["parameter_set"],
        "replicate_id": row["replicate_id"],
        "checkup_k": row["checkup_k"],
        "checkup_k_next": row["checkup_k_next"],
        "capacity_Ah_k": row["capacity_Ah_k"],
        "log_age_efc_delta": row["log_age_efc_delta"],
        "calendar_days": row["calendar_days"],
        "aging_mode": row["aging_mode"],
        "nominal_temperature_C": row["nominal_temperature_C"],
        "voltage_window_family": row["voltage_window_family"],
        "nominal_charge_C_rate": row["nominal_charge_C_rate"],
        "condition_fold": row["condition_fold"],
        "temperature_holdout_fold": row["temperature_holdout_fold"],
        "c_rate_holdout_fold": row["c_rate_holdout_fold"],
        "profile_holdout_fold": row["profile_holdout_fold"],
        "voltage_window_holdout_fold": row["voltage_window_holdout_fold"],
        "cold_c_rate_subgroup": row["cold_c_rate_subgroup"],
    }


def _write_correlation_md(
    capacity_report_path: Path,
    capacity_predictions_path: Path,
    coupling_table_path: Path,
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# PULSE-Capacity Coupling Diagnostics",
        "",
        f"Capacity report: `{capacity_report_path}`",
        f"Capacity predictions: `{capacity_predictions_path}`",
        f"Coupling table: `{coupling_table_path}`",
        "",
        "| Scope | Target | Residual | n | Pearson | Spearman |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['scope']}` | `{row['target']}` | `{row['residual_column']}` | {row['n']} | "
            f"{_fmt(row['pearson'])} | {_fmt(row['spearman'])} |"
        )
    lines.extend(
        [
            "",
            "These correlations are prediction-row diagnostics over selected model/feature/split predictions and are not independent interval-level correlations.",
            "",
            "This is a scalar diagnostic report. It does not authorize capacity+PULSE multimodal claims.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _group_by(rows: list[dict[str, Any]], key_fn: Any) -> dict[Any, list[dict[str, Any]]]:
    groups: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(key_fn(row), []).append(row)
    return groups


def _cold_c_rate(row: dict[str, Any]) -> bool:
    return _as_float(row.get("nominal_temperature_C")) <= 10 and _as_float(row.get("nominal_charge_C_rate")) >= 1.0


def _pulse_growth_bin(value: Any) -> str:
    numeric = _as_float(value)
    if numeric < -0.001:
        return "negative"
    if numeric < 0.001:
        return "near_zero"
    if numeric < 0.003:
        return "moderate"
    return "high"


def _pearson(x: list[float], y: list[float]) -> float:
    pairs = [(a, b) for a, b in zip(x, y) if math.isfinite(a) and math.isfinite(b)]
    if len(pairs) < 2:
        return math.nan
    xs, ys = zip(*pairs, strict=True)
    mean_x = _mean(xs)
    mean_y = _mean(ys)
    denom_x = math.sqrt(sum((value - mean_x) ** 2 for value in xs))
    denom_y = math.sqrt(sum((value - mean_y) ** 2 for value in ys))
    if denom_x == 0 or denom_y == 0:
        return math.nan
    return sum((a - mean_x) * (b - mean_y) for a, b in pairs) / (denom_x * denom_y)


def _ranks(values: list[float]) -> list[float]:
    finite = sorted((value, idx) for idx, value in enumerate(values) if math.isfinite(value))
    ranks = [math.nan] * len(values)
    for rank, (_, idx) in enumerate(finite, start=1):
        ranks[idx] = float(rank)
    return ranks


def _mean(values: Any) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else math.nan


def _quantile(values: list[float], q: float) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    pos = q * (len(finite) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return finite[lo]
    weight = pos - lo
    return finite[lo] * (1 - weight) + finite[hi] * weight


def _fmt(value: Any) -> str:
    numeric = _as_float(value)
    return "NA" if not math.isfinite(numeric) else f"{numeric:.6g}"


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
