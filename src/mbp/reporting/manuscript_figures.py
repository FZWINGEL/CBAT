"""Dependency-free SVG figure generation for the manuscript package."""

from __future__ import annotations

import csv
import html
import json
from collections import Counter
from pathlib import Path
from typing import Iterable


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _short_label(value: str, max_len: int = 24) -> str:
    value = value.replace("_holdout_fold", "").replace("_fold", "")
    value = value.replace("capacity_Ah_k1", "capacity").replace("delta_capacity_Ah", "delta")
    value = value.replace("delta_pulse_1s_resistance", "pulse 1s delta")
    value = value.replace("delta_pulse_10ms_resistance", "pulse 10ms delta")
    return value if len(value) <= max_len else value[: max_len - 1] + "."


def _svg_text(x: float, y: float, text: str, *, size: int = 13, weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#1f2937">'
        f"{html.escape(text)}</text>"
    )


def _write_svg(path: Path, body: str, *, width: int = 920, height: int = 560) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">\n'
        '<rect width="100%" height="100%" fill="#ffffff"/>\n'
        f"{body}\n"
        "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def _bar_chart_svg(
    path: Path,
    *,
    title: str,
    subtitle: str,
    rows: list[tuple[str, float]],
    x_label: str,
    positive_good: bool = False,
) -> None:
    width = 980
    height = max(420, 120 + 38 * len(rows))
    left = 280
    right = 70
    top = 92
    row_h = 32
    chart_w = width - left - right
    values = [value for _, value in rows] or [0.0]
    min_v = min(0.0, min(values))
    max_v = max(0.0, max(values))
    if min_v == max_v:
        max_v = min_v + 1.0
    scale = chart_w / (max_v - min_v)
    zero_x = left + (0.0 - min_v) * scale

    body: list[str] = [
        _svg_text(30, 38, title, size=22, weight="700"),
        _svg_text(30, 62, subtitle, size=13),
        f'<line x1="{left}" y1="{top - 18}" x2="{left + chart_w}" y2="{top - 18}" '
        'stroke="#d1d5db"/>',
        f'<line x1="{zero_x:.1f}" y1="{top - 28}" x2="{zero_x:.1f}" '
        f'y2="{top + row_h * len(rows) + 12}" stroke="#6b7280" stroke-dasharray="4 4"/>',
    ]
    for index, (label, value) in enumerate(rows):
        y = top + index * row_h
        x = min(zero_x, left + (value - min_v) * scale)
        bar_w = max(1.0, abs(value) * scale)
        color = "#2563eb"
        if positive_good:
            color = "#0f766e" if value >= 0 else "#b91c1c"
        body.extend(
            [
                _svg_text(30, y + 21, _short_label(label), size=12),
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="22" '
                f'rx="3" fill="{color}" opacity="0.86"/>',
                _svg_text(
                    min(width - 120, max(x + bar_w + 8, zero_x + 8)),
                    y + 17,
                    f"{value:.4g}",
                    size=12,
                ),
            ]
        )
    body.append(_svg_text(left, height - 28, x_label, size=12))
    _write_svg(path, "\n".join(body), width=width, height=height)


def _schematic_svg(path: Path, *, title: str, boxes: Iterable[str], footer: str) -> None:
    boxes = list(boxes)
    width = 980
    height = 420
    box_w = 175
    box_h = 82
    gap = 26
    x0 = 40
    y0 = 148
    body = [_svg_text(30, 42, title, size=22, weight="700")]
    for index, box in enumerate(boxes):
        x = x0 + index * (box_w + gap)
        body.append(
            f'<rect x="{x}" y="{y0}" width="{box_w}" height="{box_h}" rx="6" '
            'fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>'
        )
        for line_no, line in enumerate(box.split("\n")):
            body.append(_svg_text(x + 14, y0 + 30 + line_no * 20, line, size=13, weight="600"))
        if index < len(boxes) - 1:
            x_arrow = x + box_w
            body.append(
                f'<line x1="{x_arrow + 4}" y1="{y0 + box_h / 2}" '
                f'x2="{x_arrow + gap - 8}" y2="{y0 + box_h / 2}" '
                'stroke="#374151" stroke-width="1.5" marker-end="url(#arrow)"/>'
            )
    body.insert(
        0,
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
        'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#374151"/></marker></defs>',
    )
    body.append(_svg_text(30, 352, footer, size=13))
    _write_svg(path, "\n".join(body), width=width, height=height)


def _status_chart(path: Path, claim_matrix: Path) -> None:
    rows = read_csv_rows(claim_matrix)
    counts = Counter(row.get("status", "unknown") for row in rows)
    ordered = sorted(counts.items(), key=lambda item: item[0])
    _bar_chart_svg(
        path,
        title="Claim Ladder",
        subtitle="Paper-facing claim statuses from reports/synthesis/claim_matrix.csv.",
        rows=[(status, float(count)) for status, count in ordered],
        x_label="Number of claims",
    )


def build_manuscript_figures(out_dir: Path, reports_dir: Path, docs_dir: Path) -> list[Path]:
    """Generate manuscript SVG figures from existing tracked artifacts."""

    figure_dir = out_dir / "figures" / "generated"
    paths: list[Path] = []

    fig01 = figure_dir / "fig01_data_product_architecture.svg"
    _schematic_svg(
        fig01,
        title="Data Product Architecture",
        boxes=[
            "Audited\nresult data",
            "Interval\nproducts",
            "Stress and\nPULSE sidecars",
            "Grouped\nbaselines",
            "Claim\nledger",
        ],
        footer="Source: docs/PAPER_FIGURE_PLAN.md and docs/REPO_STATUS.md.",
    )
    paths.append(fig01)

    fig02 = figure_dir / "fig02_grouped_validation_design.svg"
    _schematic_svg(
        fig02,
        title="Grouped Validation Design",
        boxes=[
            "228 cells",
            "76 condition\ntriplets",
            "Held-out\nstressor folds",
            "Condition\nmetrics",
            "Claim\nchecks",
        ],
        footer="Random row or cell splits are not used for paper-facing claims.",
    )
    paths.append(fig02)

    ladder = read_csv_rows(reports_dir / "synthesis" / "model_ladder_summary.csv")
    capacity_rows = [
        (
            f"{row['ladder_stage']} {row['target']}",
            _float(row.get("best_metric")),
        )
        for row in ladder
        if row.get("split") == "c_rate_holdout_fold"
        and row.get("target") in {"capacity_Ah_k1", "delta_capacity_Ah"}
    ]
    fig03 = figure_dir / "fig03_capacity_baseline_ladder.svg"
    _bar_chart_svg(
        fig03,
        title="Capacity Baseline Ladder on C-rate Holdout",
        subtitle="Condition-mean MAE; lower is better. Descriptive best rows do not override claim tests.",
        rows=capacity_rows,
        x_label="Condition-mean MAE",
    )
    paths.append(fig03)

    split_rows = read_csv_rows(reports_dir / "synthesis" / "split_difficulty_summary.csv")
    fig04 = figure_dir / "fig04_c_rate_failure_analysis.svg"
    _bar_chart_svg(
        fig04,
        title="Split Difficulty Summary",
        subtitle="Best-known capacity_Ah_k1 metrics by grouped split; lower is better.",
        rows=[
            (row["split"], _float(row.get("capacity_Ah_k1_best_known"))) for row in split_rows
        ],
        x_label="Best-known condition-mean MAE",
    )
    paths.append(fig04)

    stress_rows = read_csv_rows(
        reports_dir
        / "baselines"
        / "capacity_stress_features_v1_1_hgb50"
        / "plots"
        / "c_rate_gain_by_feature_group.csv"
    )
    fig05 = figure_dir / "fig05_stress_feature_decision.svg"
    _bar_chart_svg(
        fig05,
        title="Stress-Feature C-rate Decision",
        subtitle="Gain versus F4 on C-rate holdout; positive is better.",
        rows=[
            (f"{row['target']} {row['to_feature_group']}", _float(row["condition_mean_mae_gain"]))
            for row in stress_rows[:12]
        ],
        x_label="Condition-mean MAE gain versus F4",
        positive_good=True,
    )
    paths.append(fig05)

    qa_path = reports_dir / "audit" / "pulse_qa_report.json"
    if qa_path.exists():
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        qa_rows = [
            ("summary rows", _float(str(qa.get("row_count", 0)))),
            ("unique cells", _float(str(qa.get("unique_cells", 0)))),
            ("canonical checkups", _float(str(qa.get("canonical_available_cell_checkups", 0)))),
            ("missing canonical", _float(str(qa.get("missing_canonical_cell_checkups", 0)))),
        ]
    else:
        qa_rows = [("PULSE QA report missing", 0.0)]
    fig06 = figure_dir / "fig06_pulse_qa_coverage.svg"
    _bar_chart_svg(
        fig06,
        title="PULSE QA and Canonical Target Coverage",
        subtitle="Counts from reports/audit/pulse_qa_report.json.",
        rows=qa_rows,
        x_label="Count",
    )
    paths.append(fig06)

    pulse_rows = read_csv_rows(
        reports_dir
        / "baselines"
        / "pulse_resistance_target_robustness"
        / "plots"
        / "pulse_target_comparison.csv"
    )
    fig07 = figure_dir / "fig07_pulse_resistance_baseline.svg"
    _bar_chart_svg(
        fig07,
        title="PULSE Resistance Baseline",
        subtitle="Best target rows by split; condition-mean MAE, lower is better.",
        rows=[
            (f"{row['target']} {row['split_name']}", _float(row["condition_mean_mae"]))
            for row in pulse_rows
            if row.get("target") in {"delta_pulse_1s_resistance", "delta_pulse_10ms_resistance"}
        ][:10],
        x_label="Condition-mean MAE",
    )
    paths.append(fig07)

    coupling_rows = read_csv_rows(
        reports_dir
        / "coupling"
        / "pulse_capacity_robustness"
        / "capacity_Ah_k1"
        / "plots"
        / "condition_level_pulse_capacity_correlation.csv"
    )
    fig08 = figure_dir / "fig08_pulse_capacity_coupling.svg"
    _bar_chart_svg(
        fig08,
        title="Capacity Residual and PULSE Growth Coupling",
        subtitle="Condition-level Pearson correlations for capacity_Ah_k1 residual diagnostics.",
        rows=[
            (f"{row['scope']} {row['residual_column']}", _float(row["pearson"]))
            for row in coupling_rows
            if row.get("pulse_column") == "delta_pulse_1s_resistance"
        ][:8],
        x_label="Pearson correlation",
    )
    paths.append(fig08)

    gain_rows = read_csv_rows(
        reports_dir
        / "baselines"
        / "capacity_prior_pulse_vs_best_nonpulse"
        / "plots"
        / "split_level_gain_vs_best_nonpulse.csv"
    )
    fig09 = figure_dir / "fig09_prior_pulse_vs_nonpulse.svg"
    _bar_chart_svg(
        fig09,
        title="Prior PULSE Versus Strongest Non-PULSE",
        subtitle="Mean paired gain by split; positive favors prior PULSE.",
        rows=[
            (f"{row['target']} {row['split_name']}", _float(row["mean_gain"]))
            for row in gain_rows
        ],
        x_label="Mean condition-level gain",
        positive_good=True,
    )
    paths.append(fig09)

    fig10 = figure_dir / "fig10_claim_ladder.svg"
    _status_chart(fig10, reports_dir / "synthesis" / "claim_matrix.csv")
    paths.append(fig10)

    return paths
