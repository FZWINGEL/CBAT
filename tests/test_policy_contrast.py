from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.policy_contrast import (
    build_policy_contrast_registry,
    evaluate_observed_policy_contrasts,
    observed_policy_stability_rows,
    policy_claim_readiness_rows,
    policy_contrast_family_rows,
    write_policy_contrast_qa,
)
from mbp.data.schema_contracts import POLICY_CONTRAST_REGISTRY_V1_SCHEMA, validate_table


def _policy_interval_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    specs = [
        {
            "parameter_set": 1,
            "nominal_charge_C_rate": 0.5,
            "nominal_temperature_C": 25.0,
            "voltage_window_family": "wide",
            "profile_label": "constant",
            "drop": 0.01,
        },
        {
            "parameter_set": 2,
            "nominal_charge_C_rate": 1.5,
            "nominal_temperature_C": 25.0,
            "voltage_window_family": "wide",
            "profile_label": "constant",
            "drop": 0.03,
        },
        {
            "parameter_set": 3,
            "nominal_charge_C_rate": 1.0,
            "nominal_temperature_C": 40.0,
            "voltage_window_family": "narrow",
            "profile_label": "constant",
            "drop": 0.02,
        },
    ]
    for spec in specs:
        parameter_set = int(spec["parameter_set"])
        for replicate in (1, 2, 3):
            capacity = 3.0 - 0.002 * replicate
            for checkup_k in range(4):
                next_capacity = capacity - float(spec["drop"])
                rows.append(
                    {
                        "cell_id": f"P{parameter_set:03d}_{replicate}",
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": spec["nominal_temperature_C"],
                        "voltage_window_family": spec["voltage_window_family"],
                        "nominal_charge_C_rate": spec["nominal_charge_C_rate"],
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": spec["profile_label"],
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "capacity_Ah_k": capacity,
                        "capacity_Ah_k1": next_capacity,
                        "delta_capacity_Ah": next_capacity - capacity,
                        "condition_fold": parameter_set,
                        "temperature_holdout_fold": 0,
                        "c_rate_holdout_fold": 1 if parameter_set == 2 else 0,
                        "profile_holdout_fold": 0,
                        "voltage_window_holdout_fold": 0,
                    }
                )
                capacity = next_capacity
    return rows


def test_policy_contrast_registry_builds_matched_triplet_support(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    registry_path = tmp_path / "policy_contrast.parquet"
    pq.write_table(pa.Table.from_pylist(_policy_interval_rows()), interval_path)

    table = build_policy_contrast_registry(
        interval_path,
        registry_path,
        contrast_families=["charge_c_rate"],
    )
    rows = table.to_pylist()

    assert validate_table(table, POLICY_CONTRAST_REGISTRY_V1_SCHEMA)
    assert table.schema.metadata[b"schema_version"] == b"gate72.policy_contrast_registry.v1"
    assert len(rows) == 1
    row = rows[0]
    assert row["contrast_family"] == "charge_c_rate"
    assert row["arm_a_parameter_set"] == 1
    assert row["arm_b_parameter_set"] == 2
    assert row["has_triplet_support"] is True
    assert row["support_quality"] == "matched_triplets"
    assert row["common_checkup_count"] == 5


def test_policy_contrast_qa_reports_family_support(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    registry_path = tmp_path / "policy_contrast.parquet"
    pq.write_table(pa.Table.from_pylist(_policy_interval_rows()), interval_path)
    build_policy_contrast_registry(interval_path, registry_path, contrast_families=["charge_c_rate"])

    report = write_policy_contrast_qa(
        registry_path,
        interval_path,
        tmp_path / "qa.json",
        tmp_path / "registry.csv",
        tmp_path / "family.csv",
    )
    rows = policy_contrast_family_rows(pq.read_table(registry_path).to_pylist())

    assert report["row_counts"]["contrast_rows"] == 1
    assert report["row_counts"]["triplet_supported_contrasts"] == 1
    assert rows[0]["triplet_supported_contrasts"] == 1
    assert (tmp_path / "registry.csv").exists()
    assert (tmp_path / "family.csv").exists()


def test_observed_policy_stability_detects_stable_degradation_sign(tmp_path: Path) -> None:
    interval_path = tmp_path / "interval.parquet"
    registry_path = tmp_path / "policy_contrast.parquet"
    out_dir = tmp_path / "policy"
    pq.write_table(pa.Table.from_pylist(_policy_interval_rows()), interval_path)
    build_policy_contrast_registry(interval_path, registry_path, contrast_families=["charge_c_rate"])

    report = evaluate_observed_policy_contrasts(registry_path, interval_path, out_dir)
    stability_rows = pq.read_table(registry_path).to_pylist()

    assert report["row_counts"]["stability_rows"] == 4
    assert report["row_counts"]["sign_stable_rows"] == 4
    assert (out_dir / "policy_ranking_feasibility.md").exists()
    assert (out_dir / "policy_claim_readiness.md").exists()
    assert stability_rows[0]["support_quality"] == "matched_triplets"


def test_observed_policy_stability_rows_are_observed_only(tmp_path: Path) -> None:
    interval_rows = _policy_interval_rows()
    interval_path = tmp_path / "interval.parquet"
    registry_path = tmp_path / "policy_contrast.parquet"
    pq.write_table(pa.Table.from_pylist(interval_rows), interval_path)
    table = build_policy_contrast_registry(interval_path, registry_path, contrast_families=["charge_c_rate"])

    from mbp.analysis.policy_contrast import _capacity_points_by_condition

    rows = observed_policy_stability_rows(table.to_pylist(), _capacity_points_by_condition(interval_rows))

    assert rows
    assert {row["claim_scope"] for row in rows} == {"observed_support_diagnostic_only"}
    assert all(row["sign_label"] == "arm_b_more_degraded" for row in rows)
    assert all(row["sign_stable"] for row in rows)


def test_policy_claim_readiness_blocks_policy_ranking_on_sparse_support() -> None:
    registry_rows = [
        {
            "contrast_family": "charge_c_rate",
            "has_triplet_support": True,
        }
    ]
    stability_rows = [
        {
            "contrast_family": "charge_c_rate",
            "sign_stable": True,
        }
    ]

    readiness = policy_claim_readiness_rows(registry_rows, stability_rows)
    readiness_by_area = {row["claim_area"]: row for row in readiness}

    assert readiness_by_area["matched observed policy-contrast support"]["status"] == "not_supported"
    assert readiness_by_area["future policy-ranking baseline readiness"]["status"] == "blocked"
    assert readiness_by_area["causal or same-cell counterfactual policy claims"]["status"] == "blocked"
