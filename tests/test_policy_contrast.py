from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.policy_contrast import (
    build_policy_contrast_registry,
    evaluate_policy_ranking_feasibility,
    evaluate_observed_policy_contrasts,
    observed_policy_stability_rows,
    policy_claim_readiness_rows,
    policy_contrast_family_rows,
    policy_ranking_bootstrap_rows,
    policy_ranking_pairwise_rows,
    policy_ranking_summary_rows,
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


def _policy_horizon_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter_set, delta in [(1, -0.02), (2, -0.08)]:
        for replicate in (1, 2, 3):
            capacity_k = 3.0 - 0.001 * replicate
            rows.append(
                {
                    "cell_id": f"P{parameter_set:03d}_{replicate}",
                    "parameter_set": parameter_set,
                    "replicate_id": replicate,
                    "checkup_k": 0,
                    "target_checkup_k": 2,
                    "horizon_checkups": 2,
                    "capacity_Ah_k": capacity_k,
                    "capacity_Ah_kh": capacity_k + delta,
                    "delta_capacity_Ah_h": delta,
                    "nominal_temperature_C": 25.0,
                    "voltage_window_family": "wide",
                    "nominal_charge_C_rate": 0.5 if parameter_set == 1 else 1.5,
                    "nominal_discharge_C_rate": 1.0,
                    "profile_label": "constant",
                    "aging_mode": "cyclic",
                    "condition_fold": parameter_set,
                    "temperature_holdout_fold": 0,
                    "c_rate_holdout_fold": parameter_set,
                    "profile_holdout_fold": 0,
                    "voltage_window_holdout_fold": 0,
                    "event_observed": True,
                    "schema_version": "test",
                }
            )
    return rows


def _policy_prediction_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    prediction_specs = [
        ("MH3_hist_gradient_boosting", "K2_nominal_condition", {1: -0.021, 2: -0.075}),
        ("MH1_prior_slope_linear", "prior_slope", {1: -0.070, 2: -0.030}),
        ("MH0_persistence", "persistence", {1: -0.030, 2: -0.031}),
        ("MH3_hist_gradient_boosting", "K3_oracle_exposure_diagnostic", {1: -0.020, 2: -0.080}),
    ]
    true_delta = {1: -0.02, 2: -0.08}
    for model_level, feature_group, by_parameter in prediction_specs:
        for parameter_set, prediction in by_parameter.items():
            for replicate in (1, 2, 3):
                rows.append(
                    {
                        "schema_version": "test",
                        "run_scope": "primary",
                        "split_name": "c_rate_holdout_fold",
                        "heldout_fold": parameter_set,
                        "model_level": model_level,
                        "feature_group": feature_group,
                        "target": "delta_capacity_Ah_h",
                        "cell_id": f"P{parameter_set:03d}_{replicate}",
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "checkup_k": 0,
                        "target_checkup_k": 2,
                        "horizon_checkups": 2,
                        "y_true": true_delta[parameter_set],
                        "y_pred": prediction,
                    }
                )
    return rows


def _single_supported_contrast() -> dict[str, object]:
    return {
        "contrast_id": "PC00001_charge_c_rate",
        "contrast_family": "charge_c_rate",
        "varied_field": "nominal_charge_C_rate",
        "match_key": "{}",
        "arm_a_parameter_set": 1,
        "arm_b_parameter_set": 2,
        "arm_a_value": "0.5",
        "arm_b_value": "1.5",
        "arm_a_cells": 3,
        "arm_b_cells": 3,
        "arm_a_interval_rows": 3,
        "arm_b_interval_rows": 3,
        "arm_a_min_checkup_k": 0,
        "arm_a_max_checkup_k": 2,
        "arm_b_min_checkup_k": 0,
        "arm_b_max_checkup_k": 2,
        "common_checkup_count": 2,
        "has_triplet_support": True,
        "support_quality": "matched_triplets",
        "schema_version": "test",
    }


def test_policy_ranking_pairwise_signs_use_degradation_severity() -> None:
    rows = policy_ranking_pairwise_rows([_single_supported_contrast()], _policy_prediction_rows())
    hgb = [
        row
        for row in rows
        if row["model_level"] == "MH3_hist_gradient_boosting"
        and row["feature_group"] == "K2_nominal_condition"
    ][0]
    prior_slope = [row for row in rows if row["model_level"] == "MH1_prior_slope_linear"][0]

    assert hgb["observed_effect_b_minus_a"] > 0
    assert hgb["predicted_effect_b_minus_a"] > 0
    assert hgb["sign_correct"] is True
    assert prior_slope["predicted_effect_b_minus_a"] < 0
    assert prior_slope["sign_correct"] is False


def test_policy_ranking_excludes_unsupported_contrasts_and_marks_oracle_scope() -> None:
    unsupported = _single_supported_contrast() | {"has_triplet_support": False}
    assert policy_ranking_pairwise_rows([unsupported], _policy_prediction_rows()) == []

    rows = policy_ranking_pairwise_rows([_single_supported_contrast()], _policy_prediction_rows())
    oracle = [row for row in rows if row["feature_group"] == "K3_oracle_exposure_diagnostic"][0]
    assert oracle["claim_scope"] == "oracle_diagnostic_only"


def test_policy_ranking_bootstrap_is_deterministic() -> None:
    rows = policy_ranking_pairwise_rows([_single_supported_contrast()], _policy_prediction_rows())
    first = policy_ranking_bootstrap_rows(rows, bootstrap_count=10, seed=7)
    second = policy_ranking_bootstrap_rows(rows, bootstrap_count=10, seed=7)

    assert first == second
    assert any(row["accuracy_gain"] > 0 for row in first if row["reference_model_level"] == "MH1_prior_slope_linear")


def test_policy_ranking_summary_and_readiness_block_recommendations() -> None:
    rows = policy_ranking_pairwise_rows([_single_supported_contrast()], _policy_prediction_rows())
    summary = policy_ranking_summary_rows(rows)
    by_key = {
        (row["model_level"], row["feature_group"], row["contrast_family"]): row
        for row in summary
        if row["split_name"] == "c_rate_holdout_fold"
    }

    assert by_key[("MH3_hist_gradient_boosting", "K2_nominal_condition", "all")]["sign_accuracy"] == 1.0
    assert by_key[("MH1_prior_slope_linear", "prior_slope", "all")]["sign_accuracy"] == 0.0


def test_evaluate_policy_ranking_feasibility_cli_sized_artifacts(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.parquet"
    horizon_path = tmp_path / "horizon.parquet"
    predictions_path = tmp_path / "predictions.parquet"
    out_dir = tmp_path / "policy"
    pq.write_table(pa.Table.from_pylist([_single_supported_contrast()]), registry_path)
    pq.write_table(pa.Table.from_pylist(_policy_horizon_rows()), horizon_path)
    pq.write_table(pa.Table.from_pylist(_policy_prediction_rows()), predictions_path)

    report = evaluate_policy_ranking_feasibility(
        registry_path,
        horizon_path,
        predictions_path,
        out_dir,
        targets=["delta_capacity_Ah_h"],
        horizons=[2],
        split_views=["c_rate_holdout_fold"],
        model_levels=["MH0_persistence", "MH1_prior_slope_linear", "MH3_hist_gradient_boosting"],
        feature_groups=["persistence", "prior_slope", "K2_nominal_condition", "K3_oracle_exposure_diagnostic"],
        bootstrap_count=10,
    )

    assert report["row_counts"]["pairwise_rows"] == 4
    assert (out_dir / "policy_ranking_pairwise_metrics.csv").exists()
    assert (out_dir / "policy_ranking_claim_readiness.md").exists()
    readiness_text = (out_dir / "policy_ranking_claim_readiness.md").read_text(encoding="utf-8")
    assert "No policy recommendation is made" in readiness_text
