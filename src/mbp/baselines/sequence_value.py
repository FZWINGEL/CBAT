"""Temporal history value diagnostics for non-neural capacity baselines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mbp.baselines.capacity import _as_float, _format_diagnostic_value, _write_csv

SCHEMA_VERSION = "gate24.sequence_value_diagnostics.v1"


def diagnose_sequence_value(
    report_path: Path,
    baseline_report_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    baseline_report = json.loads(baseline_report_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    metrics = _primary_hgb_metrics(report)
    baseline_metrics = _primary_hgb_metrics(baseline_report)
    aggregate_vs_order = _comparison_rows(metrics, "F14_event_aggregate", "F15_event_order_aware")
    order_vs_shuffled = _comparison_rows(metrics, "F16_event_order_shuffled", "F15_event_order_aware")
    order_vs_stress = _comparison_rows(
        [*metrics, *baseline_metrics],
        "F8_timestamp_weighted_stress",
        "F17_event_order_plus_stress",
    )
    c_rate_rows = [
        row
        for row in [*aggregate_vs_order, *order_vs_shuffled, *order_vs_stress]
        if row["split_name"] == "c_rate_holdout_fold"
    ]
    readiness = _claim_rows(aggregate_vs_order, order_vs_shuffled, order_vs_stress)

    _write_csv(plots_dir / "aggregate_vs_order_gain.csv", aggregate_vs_order)
    _write_csv(plots_dir / "order_vs_shuffled_gain.csv", order_vs_shuffled)
    _write_csv(plots_dir / "c_rate_sequence_value.csv", c_rate_rows)
    _write_csv(plots_dir / "sequence_value_claim_readiness.csv", readiness)
    _write_markdown(
        out_dir / "sequence_value_diagnostics.md",
        aggregate_vs_order,
        order_vs_shuffled,
        order_vs_stress,
    )
    _write_claim_readiness(out_dir / "sequence_value_claim_readiness.md", readiness)
    result = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "report": str(report_path),
            "baseline_report": str(baseline_report_path),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "aggregate_vs_order_gain": str(plots_dir / "aggregate_vs_order_gain.csv"),
            "order_vs_shuffled_gain": str(plots_dir / "order_vs_shuffled_gain.csv"),
            "c_rate_sequence_value": str(plots_dir / "c_rate_sequence_value.csv"),
            "claim_readiness": str(out_dir / "sequence_value_claim_readiness.md"),
        },
        "row_counts": {
            "aggregate_vs_order": len(aggregate_vs_order),
            "order_vs_shuffled": len(order_vs_shuffled),
            "order_vs_stress": len(order_vs_stress),
        },
    }
    (out_dir / "sequence_value_diagnostics_report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _primary_hgb_metrics(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in report.get("metrics", [])
        if row.get("run_scope") == "primary" and row.get("model_level") == "L2_hist_gradient_boosting"
    ]


def _comparison_rows(
    metrics: list[dict[str, Any]],
    reference_group: str,
    candidate_group: str,
) -> list[dict[str, Any]]:
    by_key = {
        (
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
            str(row["feature_group"]),
        ): row
        for row in metrics
    }
    output = []
    keys = sorted({(target, split, fold) for target, split, fold, _ in by_key})
    for target, split_name, heldout_fold in keys:
        ref = by_key.get((target, split_name, heldout_fold, reference_group))
        cand = by_key.get((target, split_name, heldout_fold, candidate_group))
        if ref is None or cand is None:
            continue
        ref_mae = _as_float(ref.get("condition_mean_mae"))
        cand_mae = _as_float(cand.get("condition_mean_mae"))
        output.append(
            {
                "target": target,
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "reference_group": reference_group,
                "candidate_group": candidate_group,
                "reference_condition_mean_mae": ref_mae,
                "candidate_condition_mean_mae": cand_mae,
                "gain": ref_mae - cand_mae,
                "test_rows": cand.get("test_rows"),
                "test_parameter_sets": cand.get("test_parameter_sets"),
            }
        )
    return output


def _claim_rows(
    aggregate_vs_order: list[dict[str, Any]],
    order_vs_shuffled: list[dict[str, Any]],
    order_vs_stress: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _claim_row("Aggregate event features help", aggregate_vs_order, "diagnostic_only"),
        _claim_row("Order-aware features beat aggregate-only", aggregate_vs_order, "not_supported"),
        _claim_row("Order-aware features beat shuffled-order", order_vs_shuffled, "not_supported"),
        _claim_row("Order-aware features improve over stress baseline", order_vs_stress, "not_supported"),
        _claim_row(
            "Order-aware features improve C-rate",
            [row for row in order_vs_shuffled + order_vs_stress if row["split_name"] == "c_rate_holdout_fold"],
            "not_supported",
        ),
        {
            "claim_area": "Sequence model readiness",
            "status": "blocked",
            "evidence": "Sequence models remain blocked unless order-aware features beat aggregate and shuffled controls under grouped validation.",
        },
    ]


def _claim_row(claim_area: str, rows: list[dict[str, Any]], default_status: str) -> dict[str, Any]:
    if not rows:
        return {"claim_area": claim_area, "status": "blocked", "evidence": "No comparison rows available."}
    gains = [_as_float(row["gain"]) for row in rows]
    positive = sum(gain > 0 for gain in gains)
    mean_gain = sum(gains) / len(gains)
    status = "partially_supported" if mean_gain > 0 and positive / len(gains) >= 0.5 else default_status
    return {
        "claim_area": claim_area,
        "status": status,
        "evidence": (
            f"mean gain={_format_diagnostic_value(mean_gain)}; "
            f"positive rows={positive}/{len(gains)}."
        ),
    }


def _write_markdown(
    path: Path,
    aggregate_vs_order: list[dict[str, Any]],
    order_vs_shuffled: list[dict[str, Any]],
    order_vs_stress: list[dict[str, Any]],
) -> None:
    lines = [
        "# Sequence Value Diagnostics",
        "",
        "Positive gain means the candidate feature group has lower condition-mean MAE.",
        "",
        "| Comparison | Target | Split | Mean gain | Positive rows | Rows |",
        "|---|---|---|---:|---:|---:|",
    ]
    for label, rows in (
        ("order_vs_aggregate", aggregate_vs_order),
        ("order_vs_shuffled", order_vs_shuffled),
        ("order_plus_stress_vs_stress", order_vs_stress),
    ):
        for summary in _summary_rows(rows):
            lines.append(
                f"| `{label}` | `{summary['target']}` | `{summary['split_name']}` | "
                f"{_format_diagnostic_value(summary['mean_gain'])} | {summary['positive_rows']} | {summary['rows']} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Sequence Value Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        grouped.setdefault((str(row["target"]), str(row["split_name"])), []).append(_as_float(row["gain"]))
    return [
        {
            "target": target,
            "split_name": split_name,
            "mean_gain": sum(gains) / len(gains),
            "positive_rows": sum(gain > 0 for gain in gains),
            "rows": len(gains),
        }
        for (target, split_name), gains in sorted(grouped.items())
    ]
