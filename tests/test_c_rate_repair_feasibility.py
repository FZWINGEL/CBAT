from __future__ import annotations

import json
from pathlib import Path

from mbp.analysis.c_rate_repair_feasibility import (
    c_rate_repair_claim_readiness_rows,
    c_rate_repair_evidence_rows,
    c_rate_support_summary_rows,
    finalize_c_rate_repair_feasibility,
)


def _c_rate_report() -> dict[str, object]:
    return {
        "schema_version": "gate84.c_rate_generalization.v1",
        "readiness": {
            "C-rate root-cause diagnostics": "supported_for_diagnostics",
            "train-only C-rate support overlap": "supported_for_diagnostics",
        },
        "row_counts": {
            "condition_hotspot_rows": 336,
            "support_overlap_rows": 76,
        },
    }


def _adaptive_replication_report(*, passing: bool = True) -> dict[str, object]:
    return {
        "schema_version": "gate56.stressor_robust_adaptive_replication.v1",
        "claim_readiness": {
            "adaptive_replication_claim": "supported_for_diagnostics" if passing else "not_supported",
            "all_required_seeds_pass": passing,
            "leakage_audit": "passed",
            "min_c_rate_gain_vs_f4": 0.020,
            "min_c_rate_gain_vs_stress_reference": 0.021,
            "min_paired_p05_vs_f4": 0.007,
            "min_paired_p05_vs_stress_reference": 0.004,
            "max_other_split_relative_degradation": 0.028 if passing else 0.06,
        },
    }


def _arm_selector_report(*, passing: bool = True) -> dict[str, object]:
    return {
        "schema_version": "gate58.stressor_robust_arm_selector.v1",
        "claim_readiness": {
            "arm_selector_claim": "supported_for_diagnostics" if passing else "not_supported",
            "leakage_audit": "passed",
            "c_rate_gain_vs_d0_f4": 0.010,
            "c_rate_paired_p05": 0.005,
            "max_other_split_relative_degradation": 0.0 if passing else 0.08,
        },
    }


def test_c_rate_repair_readiness_supports_narrow_repair_only() -> None:
    rows = c_rate_repair_claim_readiness_rows(
        c_rate_report=_c_rate_report(),
        adaptive_replication=_adaptive_replication_report(),
        arm_selector=_arm_selector_report(),
    )
    statuses = {row["claim_area"]: row["status"] for row in rows}

    assert statuses["C-rate failure and support diagnosis"] == "supported_for_diagnostics"
    assert statuses["train-only adaptive C-rate delta repair"] == "supported_for_diagnostics"
    assert statuses["targeted stressor-family routing"] == "supported_for_diagnostics"
    assert statuses["broad robust capacity"] == "not_supported"
    assert statuses["architecture, policy, calibration, and causality"] == "blocked"


def test_c_rate_repair_readiness_blocks_failed_adaptive_guardrail() -> None:
    rows = c_rate_repair_claim_readiness_rows(
        c_rate_report=_c_rate_report(),
        adaptive_replication=_adaptive_replication_report(passing=False),
        arm_selector=_arm_selector_report(),
    )
    statuses = {row["claim_area"]: row["status"] for row in rows}

    assert statuses["train-only adaptive C-rate delta repair"] == "not_supported"
    assert statuses["targeted stressor-family routing"] == "supported_for_diagnostics"


def test_c_rate_repair_evidence_rows_require_leakage_and_guardrails() -> None:
    rows = c_rate_repair_evidence_rows(
        c_rate_report=_c_rate_report(),
        adaptive_replication=_adaptive_replication_report(),
        arm_selector=_arm_selector_report(passing=False),
    )
    by_area = {row["evidence_area"]: row for row in rows}

    assert by_area["adaptive_conservative_repair"]["passes_gate"] is True
    assert by_area["targeted_stressor_family_router"]["passes_gate"] is False


def test_c_rate_support_summary_counts_low_support_rows() -> None:
    rows = c_rate_support_summary_rows(
        [
            {"support_score": "0.2", "nearest_distance": "1.0"},
            {"support_score": "0.8", "nearest_distance": "0.1"},
            {"support_score": "0.4", "nearest_distance": "0.5"},
        ]
    )

    assert rows[0]["rows"] == 3
    assert rows[0]["low_support_rows"] == 2
    assert rows[0]["low_support_fraction"] == 2 / 3


def test_finalize_c_rate_repair_feasibility_writes_report_bundle(tmp_path: Path) -> None:
    c_rate = tmp_path / "c_rate.json"
    adaptive = tmp_path / "adaptive.json"
    selector = tmp_path / "selector.json"
    support = tmp_path / "support.csv"
    out_dir = tmp_path / "out"
    c_rate.write_text(json.dumps(_c_rate_report()), encoding="utf-8")
    adaptive.write_text(json.dumps(_adaptive_replication_report()), encoding="utf-8")
    selector.write_text(json.dumps(_arm_selector_report()), encoding="utf-8")
    support.write_text(
        "support_score,nearest_distance\n0.2,1.0\n0.8,0.1\n",
        encoding="utf-8",
    )

    report = finalize_c_rate_repair_feasibility(
        c_rate,
        adaptive,
        selector,
        out_dir,
        support_overlap_path=support,
    )

    assert report["status"] == "passed"
    assert report["readiness"]["train-only adaptive C-rate delta repair"] == "supported_for_diagnostics"
    assert (out_dir / "c_rate_repair_feasibility_report.json").exists()
    assert (out_dir / "c_rate_repair_claim_readiness.md").exists()
    assert (out_dir / "plots" / "c_rate_repair_evidence_matrix.csv").exists()
