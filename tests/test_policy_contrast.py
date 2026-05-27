from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.analysis.policy_contrast import (
    build_policy_contrast_registry,
    diagnose_policy_ranking_feasibility,
    evaluate_policy_ranking_feasibility,
    evaluate_observed_policy_contrasts,
    observed_policy_stability_rows,
    policy_claim_readiness_rows,
    policy_contrast_family_rows,
    policy_ranking_bootstrap_rows,
    policy_ranking_effect_threshold_rows,
    policy_ranking_failure_forensics_claim_readiness_rows,
    policy_ranking_hgb_vs_prior_failure_bin_rows,
    policy_ranking_pairwise_rows,
    policy_ranking_rank_correlation_rows,
    policy_ranking_summary_rows,
    policy_ranking_topk_regret_rows,
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


def _forensics_pairwise_rows() -> list[dict[str, object]]:
    specs = [
        ("PC001_charge", "charge_c_rate", 0.006, 0.005, -0.004),
        ("PC002_charge", "charge_c_rate", 0.030, 0.026, -0.012),
        ("PC003_charge", "charge_c_rate", 0.080, 0.070, 0.083),
        ("PC004_temperature", "temperature", -0.040, -0.032, 0.018),
        ("PC005_temperature", "temperature", 0.060, 0.052, -0.020),
        ("PC006_temperature", "temperature", 0.015, -0.008, 0.022),
    ]
    rows: list[dict[str, object]] = []
    for contrast_id, family, observed, hgb_predicted, prior_predicted in specs:
        for model_level, feature_group, predicted in [
            ("MH3_hist_gradient_boosting", "K2_nominal_condition", hgb_predicted),
            ("MH1_prior_slope_linear", "prior_slope", prior_predicted),
            ("MH3_hist_gradient_boosting", "K3_oracle_exposure_diagnostic", observed),
        ]:
            observed_sign = _test_effect_sign(observed)
            predicted_sign = _test_effect_sign(predicted)
            rows.append(
                {
                    "contrast_id": contrast_id,
                    "contrast_family": family,
                    "split_name": "c_rate_holdout_fold",
                    "target": "delta_capacity_Ah_h",
                    "horizon_checkups": 2,
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "checkup_k": 1,
                    "target_checkup_k": 3,
                    "arm_a_parameter_set": 1,
                    "arm_b_parameter_set": 2,
                    "arm_a_value": "a",
                    "arm_b_value": "b",
                    "arm_a_prediction_rows": 3,
                    "arm_b_prediction_rows": 3,
                    "arm_a_replicates": 3,
                    "arm_b_replicates": 3,
                    "arm_a_heldout_folds": "1",
                    "arm_b_heldout_folds": "2",
                    "arm_a_observed_severity_mean": 0.0,
                    "arm_b_observed_severity_mean": observed,
                    "arm_a_predicted_severity_mean": 0.0,
                    "arm_b_predicted_severity_mean": predicted,
                    "observed_effect_b_minus_a": observed,
                    "predicted_effect_b_minus_a": predicted,
                    "effect_abs_error": abs(predicted - observed),
                    "observed_sign_label": observed_sign,
                    "predicted_sign_label": predicted_sign,
                    "sign_evaluable": observed_sign != "tie" and predicted_sign != "tie",
                    "sign_correct": observed_sign != "tie" and observed_sign == predicted_sign,
                    "claim_scope": (
                        "oracle_diagnostic_only"
                        if feature_group == "K3_oracle_exposure_diagnostic"
                        else "prospective_supported_contrast_diagnostic"
                    ),
                }
            )
    return rows


def _test_effect_sign(value: float) -> str:
    if value > 0:
        return "arm_b_more_degraded"
    if value < 0:
        return "arm_a_more_degraded"
    return "tie"


def _forensics_bootstrap_rows() -> list[dict[str, object]]:
    return [
        {
            "split_name": "c_rate_holdout_fold",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "contrast_family": "all",
            "candidate_model_level": "MH3_hist_gradient_boosting",
            "candidate_feature_group": "K2_nominal_condition",
            "reference_model_level": "MH1_prior_slope_linear",
            "reference_feature_group": "prior_slope",
            "matched_rows": 6,
            "matched_contrasts": 6,
            "candidate_sign_accuracy": 5 / 6,
            "reference_sign_accuracy": 2 / 6,
            "accuracy_gain": 0.5,
            "accuracy_gain_p05": -0.1,
            "accuracy_gain_p50": 0.5,
            "accuracy_gain_p95": 0.8,
            "bootstrap_count": 10,
            "claim_scope": "prospective_supported_contrast_diagnostic",
        }
    ]


def _write_test_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_policy_ranking_effect_thresholds_exclude_tiny_effects_and_oracle_rows() -> None:
    rows = _forensics_pairwise_rows()
    threshold_rows = policy_ranking_effect_threshold_rows(rows)
    hgb_all_002 = [
        row
        for row in threshold_rows
        if row["model_level"] == "MH3_hist_gradient_boosting"
        and row["feature_group"] == "K2_nominal_condition"
        and row["contrast_family"] == "all"
        and row["effect_threshold_label"] == "ge_0.02Ah"
    ][0]

    assert hgb_all_002["pairwise_rows"] == 4
    assert hgb_all_002["sign_accuracy"] == 1.0
    assert all(row["feature_group"] != "K3_oracle_exposure_diagnostic" for row in threshold_rows)


def test_policy_ranking_rank_metrics_handle_insufficient_and_evaluable_rows() -> None:
    full_rows = policy_ranking_rank_correlation_rows(_forensics_pairwise_rows())
    hgb_all = [
        row
        for row in full_rows
        if row["model_level"] == "MH3_hist_gradient_boosting"
        and row["feature_group"] == "K2_nominal_condition"
        and row["contrast_family"] == "all"
    ][0]
    sparse_rows = policy_ranking_rank_correlation_rows(_forensics_pairwise_rows()[:4], min_contrasts=5)
    sparse_hgb = [
        row
        for row in sparse_rows
        if row["model_level"] == "MH3_hist_gradient_boosting"
        and row["feature_group"] == "K2_nominal_condition"
        and row["contrast_family"] == "all"
    ][0]

    assert hgb_all["status"] == "evaluated"
    assert hgb_all["spearman_r"] > 0.8
    assert sparse_hgb["status"] == "insufficient_contrasts"


def test_policy_ranking_topk_regret_is_reported_for_supported_contrasts() -> None:
    rows = policy_ranking_topk_regret_rows(_forensics_pairwise_rows(), topk_values=(3,))
    hgb_all = [
        row
        for row in rows
        if row["model_level"] == "MH3_hist_gradient_boosting"
        and row["feature_group"] == "K2_nominal_condition"
        and row["contrast_family"] == "all"
    ][0]

    assert hgb_all["status"] == "evaluated"
    assert hgb_all["topk_overlap_fraction"] >= 2 / 3
    assert hgb_all["regret_vs_observed_best"] >= 0


def test_policy_ranking_failure_readiness_blocks_recommendation_and_excludes_oracle() -> None:
    pairwise = _forensics_pairwise_rows()
    threshold_rows = policy_ranking_effect_threshold_rows(pairwise)
    rank_rows = policy_ranking_rank_correlation_rows(pairwise)
    failure_bins = policy_ranking_hgb_vs_prior_failure_bin_rows(pairwise)
    readiness = policy_ranking_failure_forensics_claim_readiness_rows(
        pairwise_rows=pairwise,
        by_family_rows=[{"placeholder": "row"}],
        bootstrap_rows=_forensics_bootstrap_rows(),
        effect_threshold_rows=threshold_rows,
        rank_rows=rank_rows,
        failure_bin_rows=failure_bins,
    )
    by_area = {row["claim_area"]: row for row in readiness}

    assert by_area["K3 oracle exclusion"]["status"] == "supported_for_diagnostics"
    assert by_area["policy recommendation"]["status"] == "blocked"
    assert by_area["causal or same-cell counterfactual policy claims"]["status"] == "blocked"
    assert "K3 remains an oracle" in by_area["K3 oracle exclusion"]["allowed_wording"]


def test_diagnose_policy_ranking_feasibility_writes_forensics_outputs(tmp_path: Path) -> None:
    pairwise_path = tmp_path / "policy_ranking_pairwise_metrics.csv"
    by_family_path = tmp_path / "policy_ranking_by_family.csv"
    bootstrap_path = tmp_path / "policy_ranking_bootstrap.csv"
    out_dir = tmp_path / "policy"
    _write_test_csv(pairwise_path, _forensics_pairwise_rows())
    _write_test_csv(
        by_family_path,
        [
            {
                "split_name": "c_rate_holdout_fold",
                "target": "delta_capacity_Ah_h",
                "horizon_checkups": 2,
                "model_level": "MH3_hist_gradient_boosting",
                "feature_group": "K2_nominal_condition",
                "contrast_family": "all",
                "pairwise_rows": 6,
                "unique_contrasts": 6,
                "sign_evaluable_rows": 6,
                "sign_correct_rows": 5,
                "sign_accuracy": 5 / 6,
                "mean_effect_abs_error": 0.01,
                "median_effect_abs_error": 0.01,
                "observed_tie_rows": 0,
                "predicted_tie_rows": 0,
                "claim_scope": "prospective_supported_contrast_diagnostic",
            }
        ],
    )
    _write_test_csv(bootstrap_path, _forensics_bootstrap_rows())

    report = diagnose_policy_ranking_feasibility(pairwise_path, by_family_path, bootstrap_path, out_dir)

    assert report["row_counts"]["oracle_pairwise_rows_excluded_from_readiness"] == 6
    assert (out_dir / "policy_ranking_failure_forensics.md").exists()
    assert (out_dir / "policy_ranking_failure_claim_readiness.md").exists()
    assert (out_dir / "plots" / "hgb_vs_prior_failure_bins.csv").exists()
