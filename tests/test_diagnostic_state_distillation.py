from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines import diagnostic_state_distillation as distill
from mbp.baselines.diagnostic_state_distillation import (
    DIAGNOSTIC_STATE_PREDICTION_SCHEMA,
    leakage_audit,
    run_diagnostic_state_distillation,
    stage_a_auxiliary_predictions,
)


def _base_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parameter_set in range(1, 7):
        for replicate in (1, 2):
            cell_id = f"P{parameter_set:03d}_{replicate}"
            for checkup_k in range(6):
                capacity = 3.15 - 0.03 * checkup_k - 0.015 * parameter_set
                soh = capacity / 3.15
                diag_state = 0.05 * parameter_set + 0.01 * checkup_k
                event_checkup = 4 if parameter_set >= 4 else 8
                time_to_event = event_checkup - checkup_k
                rows.append(
                    {
                        "cell_id": cell_id,
                        "parameter_set": parameter_set,
                        "replicate_id": replicate,
                        "checkup_k": checkup_k,
                        "capacity_Ah_k": capacity,
                        "soh_k": soh,
                        "calendar_day_k": float(checkup_k * 21),
                        "cumulative_efc_k": float(checkup_k * (10 + parameter_set)),
                        "cumulative_q_Ah_k": float(checkup_k * 8),
                        "prior_delta_capacity_Ah": -0.02 - 0.002 * parameter_set,
                        "prior_capacity_slope_per_day": -0.001 - 0.0001 * parameter_set,
                        "aging_mode": "cyclic",
                        "nominal_temperature_C": 25.0 if parameter_set <= 3 else 40.0,
                        "voltage_window_family": "approx_0_100" if parameter_set % 2 else "approx_10_90",
                        "nominal_charge_C_rate": 1.0 if parameter_set <= 3 else 5.0 / 3.0,
                        "nominal_discharge_C_rate": 1.0,
                        "profile_label": "constant" if parameter_set != 6 else "profile",
                        "condition_fold": parameter_set % 3,
                        "temperature_holdout_fold": 1 if parameter_set >= 4 else 0,
                        "c_rate_holdout_fold": 1 if parameter_set >= 4 else 0,
                        "profile_holdout_fold": 1 if parameter_set == 6 else 0,
                        "voltage_window_holdout_fold": 1 if parameter_set % 2 == 0 else 0,
                        "diagnostic_state": diag_state,
                        "event_checkup_k": event_checkup if event_checkup < 7 else None,
                        "time_to_event_checkups": time_to_event if event_checkup < 7 else 10,
                        "event_within_3_checkups": 0 < time_to_event <= 3,
                        "event_observed": True,
                    }
                )
    return rows


def _horizon_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _base_rows():
        for horizon in (2, 3):
            future_drop = horizon * (0.025 + 0.04 * row["diagnostic_state"])
            rows.append(
                {
                    **{key: value for key, value in row.items() if key != "diagnostic_state"},
                    "target_checkup_k": row["checkup_k"] + horizon,
                    "horizon_checkups": horizon,
                    "capacity_Ah_kh": row["capacity_Ah_k"] - future_drop,
                    "delta_capacity_Ah_h": -future_drop,
                }
            )
    return rows


def _warning_rows() -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if key != "diagnostic_state"} for row in _base_rows()]


def _pulse_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _base_rows():
        rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "pulse_1s_resistance_k": 0.1 + row["diagnostic_state"],
                "pulse_10ms_resistance_k": 0.05 + 0.5 * row["diagnostic_state"],
            }
        )
    return rows


def _eis_rows() -> list[dict[str, Any]]:
    rows = []
    for row in _base_rows():
        rows.append(
            {
                "cell_id": row["cell_id"],
                "parameter_set": row["parameter_set"],
                "replicate_id": row["replicate_id"],
                "checkup_k": row["checkup_k"],
                "eis_z_abs_1kHz_k": 0.02 + row["diagnostic_state"],
                "eis_phase_1kHz_k": -5.0 - row["diagnostic_state"],
                "nyquist_im_peak_abs_k": 0.01 + 0.25 * row["diagnostic_state"],
                "nyquist_semicircle_width_proxy_k": 0.03 + 0.33 * row["diagnostic_state"],
            }
        )
    return rows


def test_stage_a_predictions_are_train_oof(monkeypatch: object) -> None:
    train_rows = [row for row in _horizon_rows() if row["condition_fold"] != 0]
    test_rows = [row for row in _horizon_rows() if row["condition_fold"] == 0]
    aux = {distill._base_key(row): values for row, values in zip(_base_rows(), _pulse_rows())}
    train_rows = [distill._with_auxiliary_values(row, aux) for row in train_rows]
    test_rows = [distill._with_auxiliary_values(row, aux) for row in test_rows]
    overlaps: list[set[tuple[Any, ...]]] = []

    def fake_fit_predict(
        fit_rows: list[dict[str, Any]],
        predict_rows: list[dict[str, Any]],
        target: str,
        *,
        seed: int,
        hgb_max_iter: int,
        auxiliary_model_level: str = "A0_ridge",
    ) -> list[float]:
        assert auxiliary_model_level == "A0_ridge"
        fit_keys = {distill._base_key(row) for row in fit_rows}
        predict_keys = {distill._base_key(row) for row in predict_rows}
        overlaps.append(fit_keys & predict_keys)
        mean_value = sum(float(row[target]) for row in fit_rows) / len(fit_rows)
        return [mean_value for _ in predict_rows]

    monkeypatch.setattr(distill, "_fit_predict_auxiliary", fake_fit_predict)
    result = stage_a_auxiliary_predictions(
        train_rows,
        test_rows,
        task="capacity_horizon",
        split_name="condition_fold",
        heldout_fold=0,
        seed=42,
        hgb_max_iter=3,
        inner_folds=3,
    )
    assert result.prediction_modes["pulse_1s_resistance_k"]["inner_out_of_fold"] > 0
    assert all(not overlap for overlap in overlaps)
    assert "predicted_pulse_1s_resistance_k" in result.train_rows[0]
    assert "predicted_pulse_1s_resistance_k" in result.test_rows[0]


def test_diagnostic_state_distillation_smoke(tmp_path: Path) -> None:
    horizon_path = tmp_path / "horizon.parquet"
    warning_path = tmp_path / "warning.parquet"
    pulse_path = tmp_path / "pulse.parquet"
    eis_path = tmp_path / "eis.parquet"
    report_path = tmp_path / "diagnostic_state_report.json"
    predictions_path = tmp_path / "diagnostic_state_predictions.parquet"
    pq.write_table(pa.Table.from_pylist(_horizon_rows()), horizon_path)
    pq.write_table(pa.Table.from_pylist(_warning_rows()), warning_path)
    pq.write_table(pa.Table.from_pylist(_pulse_rows()), pulse_path)
    pq.write_table(pa.Table.from_pylist(_eis_rows()), eis_path)

    report = run_diagnostic_state_distillation(
        horizon_path,
        warning_path,
        pulse_path,
        eis_path,
        report_path,
        predictions_path,
        tmp_path / "diagnostic_state",
        hgb_max_iter=3,
        tasks=["capacity_horizon", "threshold_warning"],
        capacity_targets=["delta_capacity_Ah_h"],
        warning_targets=["event_within_3_checkups"],
        model_levels=["DS0_regularized_linear", "DS1_hist_gradient_boosting"],
        feature_groups=["D0_capacity_state_reference", "D3_predicted_pulse_eis_state"],
        split_views=["condition_fold", "c_rate_holdout_fold"],
        horizons=[2],
        inner_folds=3,
    )

    prediction_table = pq.read_table(predictions_path)
    assert report["row_counts"]["metrics"] > 0
    assert report["row_counts"]["auxiliary_metrics"] > 0
    assert prediction_table.schema == DIAGNOSTIC_STATE_PREDICTION_SCHEMA
    assert prediction_table.schema.metadata[b"schema_version"] == b"gate81.diagnostic_state_distillation_predictions.v1"
    assert (tmp_path / "diagnostic_state" / "diagnostic_state_distillation_claim_readiness.md").exists()
    assert report["claim_readiness"]["cbat_architecture"] == "blocked"
    assert report["leakage_audit"]["status"] == "passed"


def test_leakage_audit_blocks_true_and_future_diagnostic_fields(monkeypatch: object) -> None:
    assert leakage_audit(["D0_capacity_state_reference", "D3_predicted_pulse_eis_state"])["status"] == "passed"
    original = distill.CAPACITY_BASE_NUMERIC_FEATURES
    monkeypatch.setattr(
        distill,
        "CAPACITY_BASE_NUMERIC_FEATURES",
        original + ("capacity_Ah_kh", "pulse_1s_resistance_k", "pulse_1s_resistance_k1"),
    )
    audit = leakage_audit(["D0_capacity_state_reference"])
    assert audit["status"] == "failed"
    assert "capacity_Ah_kh" in audit["rows"][0]["future_or_target_fields"]
    assert "pulse_1s_resistance_k" in audit["rows"][0]["true_auxiliary_fields_as_features"]
    assert "pulse_1s_resistance_k1" in audit["rows"][0]["future_auxiliary_fields"]


def test_claim_readiness_requires_primary_gain_and_c_rate_noncollapse() -> None:
    metrics = [
        {
            "task": "capacity_horizon",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "split_name": "condition_fold",
            "heldout_fold": 0,
            "model_level": "DS1_hist_gradient_boosting",
            "feature_group": "D0_capacity_state_reference",
            "n_test": 10,
            "mae": 1.0,
            "rmse": 1.0,
            "condition_mean_mae": 1.0,
            "worst_condition_mae": 1.0,
        },
        {
            "task": "capacity_horizon",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "split_name": "condition_fold",
            "heldout_fold": 0,
            "model_level": "DS1_hist_gradient_boosting",
            "feature_group": "D3_predicted_pulse_eis_state",
            "n_test": 10,
            "mae": 0.8,
            "rmse": 0.8,
            "condition_mean_mae": 0.8,
            "worst_condition_mae": 0.8,
        },
        {
            "task": "capacity_horizon",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "split_name": "c_rate_holdout_fold",
            "heldout_fold": 1,
            "model_level": "DS1_hist_gradient_boosting",
            "feature_group": "D0_capacity_state_reference",
            "n_test": 10,
            "mae": 1.0,
            "rmse": 1.0,
            "condition_mean_mae": 1.0,
            "worst_condition_mae": 1.0,
        },
        {
            "task": "capacity_horizon",
            "target": "delta_capacity_Ah_h",
            "horizon_checkups": 2,
            "split_name": "c_rate_holdout_fold",
            "heldout_fold": 1,
            "model_level": "DS1_hist_gradient_boosting",
            "feature_group": "D3_predicted_pulse_eis_state",
            "n_test": 10,
            "mae": 0.9,
            "rmse": 0.9,
            "condition_mean_mae": 0.9,
            "worst_condition_mae": 0.9,
        },
    ]
    auxiliary_metrics = [
        {
            "task": "capacity_horizon",
            "auxiliary_target": "pulse_1s_resistance_k",
            "auxiliary_family": "pulse",
            "split_name": "condition_fold",
            "heldout_fold": 0,
            "n_train_finite": 10,
            "n_test_finite": 10,
            "mae": 0.4,
            "baseline_mae": 1.0,
            "mae_gain_vs_train_mean": 0.6,
            "relative_mae_gain_vs_train_mean": 0.6,
            "status": "evaluated",
        }
    ]
    readiness = distill.diagnostic_state_claim_readiness(
        metrics,
        auxiliary_metrics,
        leakage_audit(["D3_predicted_pulse_eis_state"]),
    )
    assert readiness["diagnostic_state_distillation"] == "supported_for_diagnostics"
    assert readiness["capacity_horizon_gain"] == "supported_for_diagnostics"
    assert readiness["c_rate_noncollapse"] == "supported_for_diagnostics"
