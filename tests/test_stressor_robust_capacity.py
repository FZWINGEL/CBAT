from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.baselines.capacity import BASELINE_PREDICTION_SCHEMA
from mbp.baselines import stressor_robust_capacity as robust_module
from mbp.baselines.stressor_robust_capacity import (
    ADAPTIVE_REPLICATION_SCHEMA_VERSION,
    ADAPTIVE_SCHEMA_VERSION,
    ATTRIBUTION_SCHEMA_VERSION,
    PARETO_SCHEMA_VERSION,
    SELECTION_TIE_BREAK_ORDER,
    adaptive_replication_claim_readiness,
    attribution_outside_degradation_rows,
    aggregate_adaptive_weight_selection_rows,
    _condition_bagged_predictions,
    condition_balanced_weights,
    degradation_by_split_target_feature_rows,
    diagnose_stressor_robust_forensics,
    diagnose_stressor_robustness,
    _max_other_split_relative_degradation,
    non_degradation_threshold_sensitivity_rows,
    paired_condition_gain_rows,
    pareto_frontier_rows,
    pareto_model_settings,
    replicate_stressor_robust_adaptive,
    run_stressor_robust_attribution,
    run_stressor_robust_adaptive,
    run_stressor_robust_capacity,
    run_stressor_robust_pareto,
    _sample_condition_rows,
    select_adaptive_weight_strength,
    stressor_balanced_weights,
    stressor_robust_adaptive_claim_readiness,
    stressor_robust_attribution_claim_readiness,
    stressor_robust_pareto_claim_readiness,
    stressor_robust_claim_readiness,
)
from mbp.baselines.stressor_robust_capacity import _internal_condition_validation_split


def _write_capacity_fixture(tmp_path: Path) -> tuple[Path, Path]:
    interval_rows: list[dict[str, object]] = []
    subset_rows: list[dict[str, object]] = []
    for parameter_set in range(1, 7):
        condition_fold = (parameter_set - 1) % 3
        c_rate_fold = 1 if parameter_set in {5, 6} else 0
        profile_fold = 1 if parameter_set == 6 else 0
        for replicate_id in range(1, 4):
            cell_id = f"P{parameter_set:03d}_{replicate_id}"
            for checkup_k in range(2):
                capacity_k = 3.0 - 0.03 * parameter_set - 0.02 * checkup_k
                extra_drop = 0.06 if c_rate_fold else 0.02
                capacity_k1 = capacity_k - extra_drop - 0.003 * parameter_set
                flagged = parameter_set == 2 and checkup_k == 0
                interval_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "aging_mode": "cyclic" if parameter_set <= 5 else "profile",
                        "nominal_temperature_C": 25.0 if parameter_set <= 3 else 40.0,
                        "voltage_window": "2.50 V - 4.20 V",
                        "voltage_window_family": "approx_0_100",
                        "soc_window_approx": "50%",
                        "nominal_charge_C_rate": 5.0 / 3.0 if c_rate_fold else 1.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "WLTP" if profile_fold else "CC",
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "duration_h": 1.0,
                        "calendar_days": 1.0 / 24.0,
                        "capacity_Ah_k": capacity_k,
                        "capacity_Ah_k1": capacity_k1,
                        "delta_capacity_Ah": capacity_k1 - capacity_k,
                        "condition_fold": condition_fold,
                        "temperature_holdout_fold": 1 if parameter_set >= 4 else 0,
                        "c_rate_holdout_fold": c_rate_fold,
                        "profile_holdout_fold": profile_fold,
                        "voltage_window_holdout_fold": 1 if parameter_set in {3, 6} else 0,
                        "log_age_efc_delta": 0.5 + 0.1 * parameter_set,
                        "log_age_delta_q_Ah": 1.0 + 0.1 * checkup_k,
                        "log_age_mean_voltage_V": 3.5,
                        "log_age_min_voltage_V": 3.2,
                        "log_age_max_voltage_V": 4.1,
                        "log_age_mean_temperature_C": 25.0,
                        "log_age_min_temperature_C": 24.0,
                        "log_age_max_temperature_C": 42.0 if parameter_set >= 4 else 26.0,
                        "log_age_mean_current_A": -0.5,
                        "log_age_mean_abs_current_A": 0.7,
                        "log_age_max_abs_current_A": 1.6 if c_rate_fold else 1.0,
                        "log_age_mean_soc": 50.0,
                        "log_age_min_soc": 40.0,
                        "log_age_max_soc": 80.0,
                        "quality_flags": "LOG_AGE_monotonicity_violation" if flagged else "",
                        "schema_version": "synthetic",
                    }
                )
                subset_rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate_id,
                        "checkup_k": checkup_k,
                        "checkup_k_next": checkup_k + 1,
                        "baseline_clean_tolerant": True,
                        "baseline_clean_strict": not flagged,
                        "sensitivity_flagged_monotonicity": flagged,
                        "schema_version": "synthetic",
                    }
                )
    interval_path = tmp_path / "interval_table.parquet"
    subset_path = tmp_path / "interval_subset_registry_v1.parquet"
    pq.write_table(pa.Table.from_pylist(interval_rows), interval_path)
    pq.write_table(pa.Table.from_pylist(subset_rows), subset_path)
    return interval_path, subset_path


def test_condition_balanced_weights_equalize_parameter_sets() -> None:
    rows = [{"parameter_set": 1}, {"parameter_set": 1}, {"parameter_set": 2}]
    weights = condition_balanced_weights(rows)
    total_by_condition = {
        parameter_set: sum(weight for row, weight in zip(rows, weights) if row["parameter_set"] == parameter_set)
        for parameter_set in {1, 2}
    }
    assert abs(total_by_condition[1] - total_by_condition[2]) < 1e-12


def test_stressor_balanced_weights_use_training_rows_only() -> None:
    rows = [
        {"parameter_set": 1, "nominal_charge_C_rate": 1.0, "nominal_discharge_C_rate": 1.0},
        {"parameter_set": 2, "nominal_charge_C_rate": 1.0, "nominal_discharge_C_rate": 1.0},
        {"parameter_set": 3, "nominal_charge_C_rate": 5.0 / 3.0, "nominal_discharge_C_rate": 1.0},
    ]
    weights = stressor_balanced_weights(rows, "c_rate_holdout_fold")
    assert weights[0] == weights[1]
    assert weights[2] > weights[0]


def test_weight_strength_blends_toward_uniform() -> None:
    rows = [{"parameter_set": 1}, {"parameter_set": 1}, {"parameter_set": 2}]
    uniform = condition_balanced_weights(rows, strength=0.0)
    full = condition_balanced_weights(rows, strength=1.0)
    half = condition_balanced_weights(rows, strength=0.5)

    assert uniform == [1.0, 1.0, 1.0]
    assert half[0] == pytest.approx(1.0 + 0.5 * (full[0] - 1.0))
    assert half[2] == pytest.approx(1.0 + 0.5 * (full[2] - 1.0))


def test_internal_validation_split_keeps_conditions_disjoint() -> None:
    rows = [{"parameter_set": parameter_set} for parameter_set in range(1, 8)]
    fit_rows, validation_rows = _internal_condition_validation_split(rows, seed=1)
    fit_sets = {row["parameter_set"] for row in fit_rows}
    validation_sets = {row["parameter_set"] for row in validation_rows}
    assert fit_sets
    assert validation_sets
    assert not fit_sets & validation_sets


def test_paired_condition_gains_compare_cross_feature_references() -> None:
    predictions: list[dict[str, object]] = []
    for parameter_set in (1, 2):
        for feature_group, y_pred in (
            ("F4_state_log_age_scalar", 2.0),
            ("F8_timestamp_weighted_stress", 3.0),
        ):
            predictions.append(
                {
                    "run_scope": "primary",
                    "split_name": "c_rate_holdout_fold",
                    "target": "delta_capacity_Ah",
                    "model_level": "R0_reference_hgb50",
                    "feature_group": feature_group,
                    "heldout_fold": 0,
                    "parameter_set": parameter_set,
                    "y_true": 0.0,
                    "y_pred": y_pred,
                }
            )
        predictions.append(
            {
                "run_scope": "primary",
                "split_name": "c_rate_holdout_fold",
                "target": "delta_capacity_Ah",
                "model_level": "R2_stressor_balanced_hgb",
                "feature_group": "F8_timestamp_weighted_stress",
                "heldout_fold": 0,
                "parameter_set": parameter_set,
                "y_true": 0.0,
                "y_pred": 1.0,
            }
        )

    rows = paired_condition_gain_rows(predictions)

    assert {row["reference_feature_group"] for row in rows} == {
        "F4_state_log_age_scalar",
        "F8_timestamp_weighted_stress",
    }
    assert {row["candidate_feature_group"] for row in rows} == {"F8_timestamp_weighted_stress"}
    assert len(rows) == 4


def test_missing_other_split_evidence_does_not_pass_non_degradation() -> None:
    leaderboard = [
        {
            "run_scope": "primary",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "model_level": "R0_reference_hgb50",
            "feature_group": "F4_state_log_age_scalar",
            "condition_mean_mae": 0.10,
        },
        {
            "run_scope": "primary",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "model_level": "R2_stressor_balanced_hgb",
            "feature_group": "F4_state_log_age_scalar",
            "condition_mean_mae": 0.08,
        },
    ]

    max_degradation = _max_other_split_relative_degradation(leaderboard, leaderboard[1])
    claim = stressor_robust_claim_readiness(leaderboard, [], bootstrap_resamples=10, seed=1)

    assert max_degradation is None
    assert claim["max_other_split_relative_degradation"] is None
    assert claim["robust_capacity_claim"] == "not_supported"


def test_condition_bagging_uses_stable_encoder_and_balanced_condition_draws(monkeypatch: pytest.MonkeyPatch) -> None:
    train_rows = [
        {
            "parameter_set": 1,
            "capacity_Ah_k": 3.0,
            "duration_h": 1.0,
            "calendar_days": 1.0,
            "checkup_k": 0,
            "log_age_efc_delta": 1.0,
            "log_age_delta_q_Ah": 1.0,
            "aging_mode": "cyclic",
            "voltage_window_family": "A",
            "delta_capacity_Ah": -0.1,
        },
        {
            "parameter_set": 1,
            "capacity_Ah_k": 2.9,
            "duration_h": 1.0,
            "calendar_days": 1.0,
            "checkup_k": 1,
            "log_age_efc_delta": 1.0,
            "log_age_delta_q_Ah": 1.0,
            "aging_mode": "cyclic",
            "voltage_window_family": "A",
            "delta_capacity_Ah": -0.1,
        },
        {
            "parameter_set": 2,
            "capacity_Ah_k": 3.0,
            "duration_h": 1.0,
            "calendar_days": 1.0,
            "checkup_k": 0,
            "log_age_efc_delta": 1.0,
            "log_age_delta_q_Ah": 1.0,
            "aging_mode": "calendar",
            "voltage_window_family": "B",
            "delta_capacity_Ah": -0.2,
        },
    ]
    captured = []

    def fake_fit_hgb_predictions(**kwargs: object) -> list[dict[str, float | None]]:
        sampled_rows = kwargs["train_rows"]
        encoder = kwargs["encoder"]
        captured.append(
            {
                "sampled_count": len(sampled_rows),
                "columns": encoder.output_columns,
            }
        )
        return [{"y_pred": -0.1, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None}]

    monkeypatch.setattr(robust_module, "_fit_hgb_predictions", fake_fit_hgb_predictions)

    predictions = _condition_bagged_predictions(
        feature_group="F4_state_log_age_scalar",
        train_rows=train_rows,
        test_rows=[train_rows[0]],
        target="delta_capacity_Ah",
        split_name="condition_fold",
        heldout_fold=0,
        seed=1,
        hgb_max_iter=2,
        bag_count=3,
    )

    assert len(predictions) == 1
    assert {row["sampled_count"] for row in captured} == {4}
    assert len({row["columns"] for row in captured}) == 1
    assert "voltage_window_family=A" in captured[0]["columns"]
    assert "voltage_window_family=B" in captured[0]["columns"]


def test_sample_condition_rows_uses_fixed_draw_count() -> None:
    rows = [{"idx": idx} for idx in range(2)]
    sampled = _sample_condition_rows(rows, 5, robust_module.random.Random(1))
    assert len(sampled) == 5
    assert {row["idx"] for row in sampled} <= {0, 1}


def test_r4_tie_break_prefers_rebalanced_candidates() -> None:
    assert SELECTION_TIE_BREAK_ORDER["R2_stressor_balanced_hgb"] < SELECTION_TIE_BREAK_ORDER["R1_condition_balanced_hgb"]
    assert SELECTION_TIE_BREAK_ORDER["R1_condition_balanced_hgb"] < SELECTION_TIE_BREAK_ORDER["R0_reference_hgb50"]


def test_pareto_model_settings_expand_predeclared_grid() -> None:
    settings = pareto_model_settings(
        ["R0_reference_hgb50", "R2_stressor_balanced_hgb", "R3_condition_bagged_hgb"],
        weight_strengths=[0.5, 1.0],
        bag_counts=[3, 5],
    )

    assert [row["model_setting_id"] for row in settings] == [
        "R0_reference_hgb50",
        "R2_stressor_balanced_hgb__w0p5",
        "R2_stressor_balanced_hgb__w1",
        "R3_condition_bagged_hgb__bags3",
        "R3_condition_bagged_hgb__bags5",
    ]


def test_pareto_frontier_and_threshold_sensitivity_gate() -> None:
    leaderboard = [
        {
            "run_scope": "primary",
            "model_setting_id": "R0_reference_hgb50",
            "model_level": "R0_reference_hgb50",
            "feature_group": "F4_state_log_age_scalar",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae": 0.10,
            "worst_condition_mae": 0.20,
            "weight_strength": 0.0,
            "bag_count": 1,
        },
        {
            "run_scope": "primary",
            "model_setting_id": "R0_reference_hgb50",
            "model_level": "R0_reference_hgb50",
            "feature_group": "F8_timestamp_weighted_stress",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae": 0.11,
            "worst_condition_mae": 0.20,
            "weight_strength": 0.0,
            "bag_count": 1,
        },
        {
            "run_scope": "primary",
            "model_setting_id": "R2_stressor_balanced_hgb__w1",
            "model_level": "R2_stressor_balanced_hgb",
            "feature_group": "F8_timestamp_weighted_stress",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae": 0.08,
            "worst_condition_mae": 0.18,
            "weight_strength": 1.0,
            "bag_count": 1,
        },
        {
            "run_scope": "primary",
            "model_setting_id": "R0_reference_hgb50",
            "model_level": "R0_reference_hgb50",
            "feature_group": "F8_timestamp_weighted_stress",
            "target": "delta_capacity_Ah",
            "split_name": "voltage_window_holdout_fold",
            "condition_mean_mae": 0.10,
            "worst_condition_mae": 0.20,
            "weight_strength": 0.0,
            "bag_count": 1,
        },
        {
            "run_scope": "primary",
            "model_setting_id": "R2_stressor_balanced_hgb__w1",
            "model_level": "R2_stressor_balanced_hgb",
            "feature_group": "F8_timestamp_weighted_stress",
            "target": "delta_capacity_Ah",
            "split_name": "voltage_window_holdout_fold",
            "condition_mean_mae": 0.106,
            "worst_condition_mae": 0.20,
            "weight_strength": 1.0,
            "bag_count": 1,
        },
    ]
    paired = [
        {
            "run_scope": "primary",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "candidate_model_level": "R2_stressor_balanced_hgb",
            "candidate_feature_group": "F8_timestamp_weighted_stress",
            "model_setting_id": "R2_stressor_balanced_hgb__w1",
            "reference_feature_group": "F4_state_log_age_scalar",
            "condition_mae_gain": 0.02,
        },
        {
            "run_scope": "primary",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "candidate_model_level": "R2_stressor_balanced_hgb",
            "candidate_feature_group": "F8_timestamp_weighted_stress",
            "model_setting_id": "R2_stressor_balanced_hgb__w1",
            "reference_feature_group": "F8_timestamp_weighted_stress",
            "condition_mae_gain": 0.03,
        },
    ]

    frontier = pareto_frontier_rows(leaderboard, paired, bootstrap_resamples=10, seed=1)
    sensitivity = non_degradation_threshold_sensitivity_rows(frontier)
    claim = stressor_robust_pareto_claim_readiness(frontier)

    assert frontier[0]["max_other_split_relative_degradation"] == pytest.approx(0.06)
    assert any(row["threshold"] == 0.05 and not row["passes_threshold"] for row in sensitivity)
    assert any(row["threshold"] == 0.075 and row["passes_threshold"] for row in sensitivity)
    assert claim["stressor_robust_pareto_claim"] == "not_supported"


def test_adaptive_selection_prefers_guarded_positive_gain() -> None:
    rows = aggregate_adaptive_weight_selection_rows(
        [
            {
                "weight_strength": 0.25,
                "candidate_condition_mean_mae": 0.09,
                "condition_mean_mae_gain": 0.01,
                "relative_degradation": 0.02,
            },
            {
                "weight_strength": 0.5,
                "candidate_condition_mean_mae": 0.08,
                "condition_mean_mae_gain": 0.02,
                "relative_degradation": 0.04,
            },
            {
                "weight_strength": 1.0,
                "candidate_condition_mean_mae": 0.07,
                "condition_mean_mae_gain": 0.03,
                "relative_degradation": 0.08,
            },
        ]
    )

    selected = select_adaptive_weight_strength(rows)

    assert selected["weight_strength"] == 0.5
    assert [row["selected_by_train_only_rule"] for row in rows] == [False, True, False]


def test_conservative_adaptive_selection_prefers_lowest_guarded_strength() -> None:
    rows = aggregate_adaptive_weight_selection_rows(
        [
            {
                "weight_strength": 0.25,
                "candidate_condition_mean_mae": 0.09,
                "condition_mean_mae_gain": 0.01,
                "relative_degradation": 0.02,
            },
            {
                "weight_strength": 0.5,
                "candidate_condition_mean_mae": 0.08,
                "condition_mean_mae_gain": 0.02,
                "relative_degradation": 0.04,
            },
        ],
        selection_policy="conservative_guarded",
    )

    selected = select_adaptive_weight_strength(rows, policy="conservative_guarded")

    assert selected["weight_strength"] == 0.25
    assert [row["selected_by_train_only_rule"] for row in rows] == [True, False]


def test_adaptive_claim_readiness_requires_outer_guardrail() -> None:
    frontier = [
        {
            "model_setting_id": "R5_train_only_stressor_selected_hgb",
            "model_level": "R5_train_only_stressor_selected_hgb",
            "feature_group": "F8_timestamp_weighted_stress",
            "gain_vs_f4": 0.02,
            "gain_vs_stress_reference": 0.01,
            "paired_p05_vs_f4": 0.005,
            "paired_p05_vs_stress_reference": 0.002,
            "max_other_split_relative_degradation": 0.049,
        }
    ]

    claim = stressor_robust_adaptive_claim_readiness(frontier)

    assert claim["stressor_robust_adaptive_claim"] == "supported_for_diagnostics"
    assert claim["adaptive_passes_5pct"] is True


def test_adaptive_replication_claim_requires_all_seeds_and_leakage_pass() -> None:
    rows = [
        {
            "seed": 1,
            "selection_policy": "conservative_guarded",
            "adaptive_passes_5pct": True,
            "c_rate_gain_vs_f4": 0.02,
            "c_rate_gain_vs_stress_reference": 0.01,
            "paired_p05_vs_f4": 0.002,
            "paired_p05_vs_stress_reference": 0.001,
            "max_other_split_relative_degradation": 0.03,
        },
        {
            "seed": 2,
            "selection_policy": "conservative_guarded",
            "adaptive_passes_5pct": False,
            "c_rate_gain_vs_f4": 0.02,
            "c_rate_gain_vs_stress_reference": 0.01,
            "paired_p05_vs_f4": 0.002,
            "paired_p05_vs_stress_reference": 0.001,
            "max_other_split_relative_degradation": 0.06,
        },
    ]

    claim = adaptive_replication_claim_readiness(
        rows,
        expected_seeds=[1, 2],
        leakage_audit={"status": "passed"},
    )

    assert claim["adaptive_replication_claim"] == "partially_supported"
    assert claim["all_required_seeds_pass"] is False
    assert claim["failing_seeds"] == "2"


def test_attribution_claim_requires_incremental_f8_gain_and_guardrail() -> None:
    comparison_rows = [
        {
            "comparison_id": "incremental_f8_under_adaptive",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae_gain": 0.01,
            "paired_p05": 0.002,
        },
        {
            "comparison_id": "reweighting_only",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae_gain": 0.02,
            "paired_p05": 0.004,
        },
        {
            "comparison_id": "raw_f8_stress_feature_value",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae_gain": -0.01,
            "paired_p05": -0.002,
        },
        {
            "comparison_id": "combined_adaptive_f8_vs_f4",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "condition_mean_mae_gain": 0.03,
            "paired_p05": 0.006,
        },
    ]
    outside_rows = [
        {
            "comparison_id": "incremental_f8_under_adaptive",
            "max_other_split_relative_degradation": 0.02,
        }
    ]

    claim = stressor_robust_attribution_claim_readiness(
        comparison_rows,
        outside_rows,
        leakage_audit={"status": "passed"},
    )

    assert claim["stressor_feature_attribution_claim"] == "supported_for_diagnostics"
    assert claim["incremental_f8_gain_vs_adaptive_f4"] == 0.01


def test_attribution_outside_degradation_rows_use_non_c_rate_only() -> None:
    rows = [
        {
            "comparison_id": "incremental_f8_under_adaptive",
            "target": "delta_capacity_Ah",
            "split_name": "c_rate_holdout_fold",
            "relative_degradation": 0.2,
        },
        {
            "comparison_id": "incremental_f8_under_adaptive",
            "target": "delta_capacity_Ah",
            "split_name": "profile_holdout_fold",
            "relative_degradation": 0.03,
        },
    ]

    outside = attribution_outside_degradation_rows(rows)

    assert outside[0]["max_other_split_relative_degradation"] == 0.03
    assert outside[0]["passes_5pct"] is True


def test_degradation_by_split_target_feature_rows() -> None:
    rows = degradation_by_split_target_feature_rows(
        [
            {
                "run_scope": "primary",
                "model_level": "R0_reference_hgb50",
                "feature_group": "F8_timestamp_weighted_stress",
                "target": "delta_capacity_Ah",
                "split_name": "voltage_window_holdout_fold",
                "condition_mean_mae": 0.10,
            },
            {
                "run_scope": "primary",
                "model_level": "R2_stressor_balanced_hgb",
                "feature_group": "F8_timestamp_weighted_stress",
                "target": "delta_capacity_Ah",
                "split_name": "voltage_window_holdout_fold",
                "condition_mean_mae": 0.106,
            },
        ]
    )

    assert rows[0]["relative_degradation"] == pytest.approx(0.06)
    assert rows[0]["exceeds_5pct_guardrail"] is True


def test_stressor_robust_runner_fails_when_no_metrics_generated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = {"sensitivity_flagged_monotonicity": False}
    monkeypatch.setattr(robust_module, "load_baseline_rows", lambda *args, **kwargs: ([row], [row]))
    monkeypatch.setattr(robust_module, "iter_split_instances", lambda *args, **kwargs: iter(()))

    with pytest.raises(ValueError, match="No metrics were generated"):
        run_stressor_robust_capacity(
            tmp_path / "interval.parquet",
            tmp_path / "subsets.parquet",
            tmp_path / "report.json",
            tmp_path / "predictions.parquet",
            model_levels=["R0_reference_hgb50"],
            feature_groups=["F4_state_log_age_scalar"],
            targets=["delta_capacity_Ah"],
            split_views=["condition_fold"],
            hgb_max_iter=1,
        )


def test_stressor_robust_capacity_runner_and_diagnostics(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "stressor_robust_report.json"
    predictions_path = tmp_path / "stressor_robust_predictions.parquet"
    out_dir = tmp_path / "stressor_robust"

    report = run_stressor_robust_capacity(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        out_dir=out_dir,
        model_levels=["R0_reference_hgb50", "R1_condition_balanced_hgb", "R4_worst_fold_selected_hgb"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        hgb_max_iter=3,
        bag_count=2,
    )

    assert report["status"] == "passed"
    assert report["row_counts"]["metrics"] > 0
    assert pq.read_table(predictions_path).schema == BASELINE_PREDICTION_SCHEMA
    assert (out_dir / "stressor_robustness_claim_readiness.md").exists()
    result = diagnose_stressor_robustness(report_path, predictions_path, tmp_path / "diagnostics", bootstrap_resamples=10)
    assert result["row_counts"]["leaderboard_rows"] > 0
    assert (tmp_path / "diagnostics" / "paired_condition_gains.csv").exists()
    forensics = diagnose_stressor_robust_forensics(report_path, predictions_path, tmp_path / "forensics")
    assert forensics["row_counts"]["split_degradation_rows"] > 0
    assert (tmp_path / "forensics" / "stressor_failure_forensics.md").exists()


def test_stressor_robust_pareto_runner_smoke(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "stressor_robust_pareto_report.json"
    predictions_path = tmp_path / "stressor_robust_pareto_predictions.parquet"
    out_dir = tmp_path / "stressor_robust_pareto"

    report = run_stressor_robust_pareto(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        out_dir=out_dir,
        model_levels=["R0_reference_hgb50", "R2_stressor_balanced_hgb"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        weight_strengths=[0.5, 1.0],
        bag_counts=[3],
        hgb_max_iter=2,
    )

    metadata = pq.read_table(predictions_path).schema.metadata or {}
    assert report["status"] == "passed"
    assert report["row_counts"]["metrics"] > 0
    assert metadata[b"schema_version"] == PARETO_SCHEMA_VERSION.encode()
    assert (out_dir / "plots" / "pareto_frontier.csv").exists()
    assert (out_dir / "plots" / "non_degradation_threshold_sensitivity.csv").exists()
    assert (out_dir / "stressor_robust_pareto_claim_readiness.md").exists()


def test_stressor_robust_adaptive_runner_smoke(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "stressor_robust_adaptive_report.json"
    predictions_path = tmp_path / "stressor_robust_adaptive_predictions.parquet"
    out_dir = tmp_path / "stressor_robust_adaptive"

    report = run_stressor_robust_adaptive(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        out_dir=out_dir,
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        weight_strengths=[0.5, 1.0],
        selection_split_views=["condition_fold"],
        hgb_max_iter=2,
    )

    metadata = pq.read_table(predictions_path).schema.metadata or {}
    assert report["status"] == "passed"
    assert report["row_counts"]["metrics"] > 0
    assert report["row_counts"]["selection_rows"] > 0
    assert metadata[b"schema_version"] == ADAPTIVE_SCHEMA_VERSION.encode()
    assert (out_dir / "adaptive_selection_summary.csv").exists()
    assert (out_dir / "plots" / "adaptive_frontier.csv").exists()
    assert (out_dir / "stressor_robust_adaptive_claim_readiness.md").exists()


def test_stressor_robust_adaptive_replication_runner_smoke(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    out_dir = tmp_path / "stressor_robust_adaptive_replication"

    report = replicate_stressor_robust_adaptive(
        interval_path,
        subset_path,
        out_dir,
        seeds=[1, 2],
        selection_policies=["conservative_guarded"],
        feature_groups=["F4_state_log_age_scalar"],
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        weight_strengths=[0.5, 1.0],
        selection_split_views=["condition_fold"],
        hgb_max_iter=2,
    )

    assert report["status"] == "passed"
    assert report["schema_version"] == ADAPTIVE_REPLICATION_SCHEMA_VERSION
    assert report["seed_reuse_mode"] == "deterministic_hgb_no_bagging_reuse"
    assert report["effective_fit_seeds"] == [1]
    assert report["row_counts"]["replication_rows"] == 2
    assert {row["computed_seed"] for row in report["replication_rows"]} == {1}
    assert report["leakage_audit"]["status"] == "passed"
    assert (out_dir / "replication_summary.json").exists()
    assert (out_dir / "plots" / "seed_sensitivity.csv").exists()
    assert (out_dir / "plots" / "policy_sensitivity.csv").exists()
    assert (out_dir / "adaptive_replication_claim_readiness.md").exists()


def test_stressor_robust_attribution_runner_smoke(tmp_path: Path) -> None:
    interval_path, subset_path = _write_capacity_fixture(tmp_path)
    report_path = tmp_path / "stressor_robust_attribution_report.json"
    predictions_path = tmp_path / "stressor_robust_attribution_predictions.parquet"
    out_dir = tmp_path / "stressor_robust_attribution"

    report = run_stressor_robust_attribution(
        interval_path,
        subset_path,
        report_path,
        predictions_path,
        stress_features_path=interval_path,
        out_dir=out_dir,
        targets=["delta_capacity_Ah"],
        split_views=["condition_fold"],
        weight_strengths=[0.5, 1.0],
        selection_split_views=["condition_fold"],
        hgb_max_iter=2,
    )

    metadata = pq.read_table(predictions_path).schema.metadata or {}
    assert report["status"] == "passed"
    assert report["schema_version"] == ATTRIBUTION_SCHEMA_VERSION
    assert report["row_counts"]["comparison_rows"] > 0
    assert metadata[b"schema_version"] == ATTRIBUTION_SCHEMA_VERSION.encode()
    assert (out_dir / "attribution_claim_readiness.md").exists()
    assert (out_dir / "attribution_comparisons.csv").exists()
    assert (out_dir / "plots" / "c_rate_attribution.csv").exists()
