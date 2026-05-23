"""Milestone 0.8 capacity/PULSE scalar coupling diagnostics."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

SCHEMA_VERSION = "gate8.capacity_pulse_coupling.v1"

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
                    "nominal_temperature_C",
                    "voltage_window_family",
                    "nominal_charge_C_rate",
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
