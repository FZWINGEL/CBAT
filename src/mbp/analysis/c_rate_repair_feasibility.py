"""C-rate repair feasibility synthesis.

This module consumes existing C-rate diagnostics and existing non-neural
stressor-robust repair artifacts. It does not train models, add features,
recommend policies, or make causal claims.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "gate85.c_rate_repair_feasibility.v1"
PRIMARY_TARGET = "delta_capacity_Ah"
PRIMARY_SPLIT = "c_rate_holdout_fold"
GUARDRAIL_MAX_OUTSIDE_DEGRADATION = 0.05


def finalize_c_rate_repair_feasibility(
    c_rate_report_path: Path,
    adaptive_replication_report_path: Path,
    arm_selector_report_path: Path,
    out_dir: Path,
    *,
    support_overlap_path: Path | None = None,
) -> dict[str, Any]:
    """Finalize C-rate repair feasibility from existing tracked artifacts."""
    c_rate_report = _read_json(c_rate_report_path, "C-rate diagnostic report")
    adaptive_replication = _read_json(adaptive_replication_report_path, "adaptive replication report")
    arm_selector = _read_json(arm_selector_report_path, "arm-selector report")
    support_rows = _read_csv(support_overlap_path) if support_overlap_path else []

    evidence_rows = c_rate_repair_evidence_rows(
        c_rate_report=c_rate_report,
        adaptive_replication=adaptive_replication,
        arm_selector=arm_selector,
    )
    support_summary = c_rate_support_summary_rows(support_rows)
    readiness_rows = c_rate_repair_claim_readiness_rows(
        c_rate_report=c_rate_report,
        adaptive_replication=adaptive_replication,
        arm_selector=arm_selector,
    )
    readiness = {str(row["claim_area"]): str(row["status"]) for row in readiness_rows}

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "c_rate_repair_evidence_matrix.csv", evidence_rows)
    _write_csv(plots_dir / "c_rate_repair_support_summary.csv", support_summary)
    _write_claim_readiness_md(out_dir / "c_rate_repair_claim_readiness.md", readiness_rows)
    _write_decision_md(
        out_dir / "c_rate_repair_decision.md",
        evidence_rows=evidence_rows,
        support_summary=support_summary,
        readiness_rows=readiness_rows,
    )

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "c_rate_report": str(c_rate_report_path),
            "support_overlap": str(support_overlap_path) if support_overlap_path else None,
            "adaptive_replication_report": str(adaptive_replication_report_path),
            "arm_selector_report": str(arm_selector_report_path),
        },
        "primary_target": PRIMARY_TARGET,
        "primary_split": PRIMARY_SPLIT,
        "guardrail_max_outside_degradation": GUARDRAIL_MAX_OUTSIDE_DEGRADATION,
        "row_counts": {
            "evidence_rows": len(evidence_rows),
            "support_summary_rows": len(support_summary),
            "claim_readiness_rows": len(readiness_rows),
        },
        "readiness": readiness,
        "outputs": {
            "report": str(out_dir / "c_rate_repair_feasibility_report.json"),
            "decision": str(out_dir / "c_rate_repair_decision.md"),
            "claim_readiness": str(out_dir / "c_rate_repair_claim_readiness.md"),
            "evidence_matrix": str(plots_dir / "c_rate_repair_evidence_matrix.csv"),
            "support_summary": str(plots_dir / "c_rate_repair_support_summary.csv"),
        },
        "claim_scope": "narrow_non_neural_c_rate_delta_repair_diagnostic_only",
    }
    (out_dir / "c_rate_repair_feasibility_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def c_rate_repair_evidence_rows(
    *,
    c_rate_report: dict[str, Any],
    adaptive_replication: dict[str, Any],
    arm_selector: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return a compact evidence matrix for the repair finalization gate."""
    c_rate_readiness = dict(c_rate_report.get("readiness", {}))
    adaptive_claim = dict(adaptive_replication.get("claim_readiness", {}))
    selector_claim = dict(arm_selector.get("claim_readiness", {}))
    return [
        {
            "evidence_area": "c_rate_root_cause",
            "artifact_schema": c_rate_report.get("schema_version"),
            "status": c_rate_readiness.get("C-rate root-cause diagnostics"),
            "primary_metric": "condition_hotspot_rows",
            "primary_value": _as_float(c_rate_report.get("row_counts", {}).get("condition_hotspot_rows")),
            "passes_gate": c_rate_readiness.get("C-rate root-cause diagnostics") == "supported_for_diagnostics",
            "claim_scope": "diagnostic_failure_forensics",
        },
        {
            "evidence_area": "train_only_support_overlap",
            "artifact_schema": c_rate_report.get("schema_version"),
            "status": c_rate_readiness.get("train-only C-rate support overlap"),
            "primary_metric": "support_overlap_rows",
            "primary_value": _as_float(c_rate_report.get("row_counts", {}).get("support_overlap_rows")),
            "passes_gate": c_rate_readiness.get("train-only C-rate support overlap") == "supported_for_diagnostics",
            "claim_scope": "support_diagnostic_not_deployment_reliability",
        },
        {
            "evidence_area": "adaptive_conservative_repair",
            "artifact_schema": adaptive_replication.get("schema_version"),
            "status": adaptive_claim.get("adaptive_replication_claim"),
            "primary_metric": "min_c_rate_gain_vs_stress_reference",
            "primary_value": _as_float(adaptive_claim.get("min_c_rate_gain_vs_stress_reference")),
            "paired_p05": _as_float(adaptive_claim.get("min_paired_p05_vs_stress_reference")),
            "outside_degradation": _as_float(adaptive_claim.get("max_other_split_relative_degradation")),
            "passes_gate": _adaptive_replication_passes(adaptive_claim),
            "claim_scope": "narrow_train_only_delta_capacity_repair_diagnostic",
        },
        {
            "evidence_area": "targeted_stressor_family_router",
            "artifact_schema": arm_selector.get("schema_version"),
            "status": selector_claim.get("arm_selector_claim"),
            "primary_metric": "c_rate_gain_vs_d0_f4",
            "primary_value": _as_float(selector_claim.get("c_rate_gain_vs_d0_f4")),
            "paired_p05": _as_float(selector_claim.get("c_rate_paired_p05")),
            "outside_degradation": _as_float(selector_claim.get("max_other_split_relative_degradation")),
            "passes_gate": _arm_selector_passes(selector_claim),
            "claim_scope": "targeted_router_diagnostic_not_policy",
        },
    ]


def c_rate_support_summary_rows(support_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize C-rate support overlap rows when provided."""
    if not support_rows:
        return []
    scores = [_as_float(row.get("support_score")) for row in support_rows]
    low_support = [score for score in scores if math.isfinite(score) and score < 0.5]
    distances = [_as_float(row.get("nearest_distance")) for row in support_rows]
    return [
        {
            "summary_area": "c_rate_support_overlap",
            "rows": len(support_rows),
            "low_support_rows": len(low_support),
            "low_support_fraction": len(low_support) / len(support_rows),
            "mean_support_score": _mean(scores),
            "median_support_score": _median(scores),
            "mean_nearest_distance": _mean(distances),
            "claim_scope": "support_context_for_repair_interpretation",
        }
    ]


def c_rate_repair_claim_readiness_rows(
    *,
    c_rate_report: dict[str, Any],
    adaptive_replication: dict[str, Any],
    arm_selector: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return conservative claim-readiness rows for C-rate repair finalization."""
    c_rate_readiness = dict(c_rate_report.get("readiness", {}))
    adaptive_claim = dict(adaptive_replication.get("claim_readiness", {}))
    selector_claim = dict(arm_selector.get("claim_readiness", {}))
    c_rate_diagnostics_pass = (
        c_rate_readiness.get("C-rate root-cause diagnostics") == "supported_for_diagnostics"
        and c_rate_readiness.get("train-only C-rate support overlap") == "supported_for_diagnostics"
    )
    adaptive_pass = _adaptive_replication_passes(adaptive_claim)
    selector_pass = _arm_selector_passes(selector_claim)
    return [
        {
            "claim_area": "C-rate failure and support diagnosis",
            "status": "supported_for_diagnostics" if c_rate_diagnostics_pass else "not_supported",
            "evidence": (
                "C-rate root-cause diagnostics and train-only support overlap are present."
                if c_rate_diagnostics_pass
                else "C-rate diagnostics or support-overlap evidence is missing or unsupported."
            ),
            "allowed_wording": "C-rate failures can be localized to held-out condition/support regimes.",
            "forbidden_wording": "Support diagnostics prove out-of-distribution reliability.",
        },
        {
            "claim_area": "train-only adaptive C-rate delta repair",
            "status": "supported_for_diagnostics" if adaptive_pass else "not_supported",
            "evidence": _adaptive_evidence(adaptive_claim),
            "allowed_wording": "A narrow non-neural train-only adaptive selector improves C-rate delta capacity diagnostics.",
            "forbidden_wording": "C-rate fade is solved globally.",
        },
        {
            "claim_area": "targeted stressor-family routing",
            "status": "supported_for_diagnostics" if selector_pass else "not_supported",
            "evidence": _selector_evidence(selector_claim),
            "allowed_wording": "A targeted report-based router preserves the C-rate delta diagnostic gain without outside-split degradation.",
            "forbidden_wording": "The router is a deployable policy recommendation system.",
        },
        {
            "claim_area": "broad robust capacity",
            "status": "not_supported",
            "evidence": "The repair evidence is scoped to C-rate delta capacity and does not solve capacity level, all targets, or all stressor views.",
            "allowed_wording": "Broad robust-capacity wording remains unsupported.",
            "forbidden_wording": "The benchmark now has a globally robust capacity model.",
        },
        {
            "claim_area": "architecture, policy, calibration, and causality",
            "status": "blocked",
            "evidence": "This finalization consumes existing non-neural reports and adds no calibrated-risk, policy, causal, neural, sequence, or CBAT evidence.",
            "allowed_wording": "CBAT, policy ranking, calibrated risk/uncertainty, causal claims, and broad sequence/neural branches remain blocked.",
            "forbidden_wording": "The repair gate authorizes CBAT, policy ranking, causal effects, or calibrated risk.",
        },
    ]


def _adaptive_replication_passes(claim: dict[str, Any]) -> bool:
    return (
        claim.get("adaptive_replication_claim") == "supported_for_diagnostics"
        and bool(claim.get("all_required_seeds_pass"))
        and claim.get("leakage_audit") == "passed"
        and _as_float(claim.get("min_c_rate_gain_vs_f4")) > 0
        and _as_float(claim.get("min_c_rate_gain_vs_stress_reference")) > 0
        and _as_float(claim.get("min_paired_p05_vs_f4")) > 0
        and _as_float(claim.get("min_paired_p05_vs_stress_reference")) > 0
        and _as_float(claim.get("max_other_split_relative_degradation")) <= GUARDRAIL_MAX_OUTSIDE_DEGRADATION
    )


def _arm_selector_passes(claim: dict[str, Any]) -> bool:
    return (
        claim.get("arm_selector_claim") == "supported_for_diagnostics"
        and claim.get("leakage_audit") == "passed"
        and _as_float(claim.get("c_rate_gain_vs_d0_f4")) > 0
        and _as_float(claim.get("c_rate_paired_p05")) > 0
        and _as_float(claim.get("max_other_split_relative_degradation")) <= GUARDRAIL_MAX_OUTSIDE_DEGRADATION
    )


def _adaptive_evidence(claim: dict[str, Any]) -> str:
    return (
        f"min gain vs F4 `{_fmt(claim.get('min_c_rate_gain_vs_f4'))}`, "
        f"min gain vs stress `{_fmt(claim.get('min_c_rate_gain_vs_stress_reference'))}`, "
        f"paired p05 floors `{_fmt(claim.get('min_paired_p05_vs_f4'))}`/`{_fmt(claim.get('min_paired_p05_vs_stress_reference'))}`, "
        f"outside degradation `{_fmt(claim.get('max_other_split_relative_degradation'))}`, "
        f"leakage `{claim.get('leakage_audit')}`."
    )


def _selector_evidence(claim: dict[str, Any]) -> str:
    return (
        f"C-rate gain `{_fmt(claim.get('c_rate_gain_vs_d0_f4'))}`, "
        f"paired p05 `{_fmt(claim.get('c_rate_paired_p05'))}`, "
        f"outside degradation `{_fmt(claim.get('max_other_split_relative_degradation'))}`, "
        f"leakage `{claim.get('leakage_audit')}`."
    )


def _write_claim_readiness_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# C-Rate Repair Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} | "
            f"{row['allowed_wording']} | {row['forbidden_wording']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_decision_md(
    path: Path,
    *,
    evidence_rows: list[dict[str, Any]],
    support_summary: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> None:
    statuses = {row["claim_area"]: row["status"] for row in readiness_rows}
    lines = [
        "# C-Rate Repair Feasibility Decision",
        "",
        "## Scope",
        "",
        "This gate synthesizes existing C-rate root-cause diagnostics with existing train-only non-neural repair artifacts. It does not train a new model, add features, recommend policies, or make causal claims.",
        "",
        "## Evidence Matrix",
        "",
        "| Evidence area | Status | Metric | Value | Paired p05 | Outside degradation | Passes |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in evidence_rows:
        lines.append(
            "| {area} | `{status}` | {metric} | {value} | {p05} | {degradation} | `{passes}` |".format(
                area=row["evidence_area"],
                status=row.get("status"),
                metric=row.get("primary_metric"),
                value=_fmt(row.get("primary_value")),
                p05=_fmt(row.get("paired_p05")),
                degradation=_fmt(row.get("outside_degradation")),
                passes=bool(row.get("passes_gate")),
            )
        )
    if support_summary:
        support = support_summary[0]
        lines.extend(
            [
                "",
                "## Support Context",
                "",
                f"- C-rate support rows: `{support['rows']}`",
                f"- Low-support rows: `{support['low_support_rows']}`",
                f"- Low-support fraction: `{_fmt(support['low_support_fraction'])}`",
                f"- Median support score: `{_fmt(support['median_support_score'])}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- C-rate diagnosis: `{statuses.get('C-rate failure and support diagnosis')}`",
            f"- Adaptive C-rate delta repair: `{statuses.get('train-only adaptive C-rate delta repair')}`",
            f"- Targeted stressor-family routing: `{statuses.get('targeted stressor-family routing')}`",
            f"- Broad robust capacity: `{statuses.get('broad robust capacity')}`",
            f"- Architecture/policy/calibration/causality: `{statuses.get('architecture, policy, calibration, and causality')}`",
            "",
            "The narrow supported wording is limited to diagnostic C-rate `delta_capacity_Ah` repair with train-only non-neural selection and targeted routing. It does not authorize broad robust-capacity wording, solved C-rate fade, CBAT, policy ranking, calibrated risk, calibrated uncertainty, neural/sequence branches, or causal claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return content


def _read_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"Missing support-overlap CSV: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _finite(values: list[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def _mean(values: list[float]) -> float:
    finite = _finite(values)
    return sum(finite) / len(finite) if finite else math.nan


def _median(values: list[float]) -> float:
    finite = sorted(_finite(values))
    if not finite:
        return math.nan
    midpoint = len(finite) // 2
    if len(finite) % 2:
        return finite[midpoint]
    return (finite[midpoint - 1] + finite[midpoint]) / 2.0


def _fmt(value: Any) -> str:
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:.6g}"
    return ""
