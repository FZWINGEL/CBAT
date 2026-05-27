"""Minimal sequence reopening gate for capacity prediction."""

from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.baselines.capacity import (
    BASELINE_PREDICTION_SCHEMA,
    DIRECT_TARGETS,
    SPLIT_COLUMNS,
    FeatureEncoder,
    _as_float,
    _format_diagnostic_value,
    _leaderboard_rows,
    _mean,
    _normalize_selection,
    _prediction_to_evaluation_space,
    _training_target_value,
    _write_csv,
    assert_no_parameter_set_leakage,
    compute_metrics,
    iter_split_instances,
    load_baseline_rows,
)

SCHEMA_VERSION = "gate71.minimal_sequence_reopening.v1"
MODEL_LEVELS = (
    "S0_ridge_true_sequence",
    "S1_ridge_shuffled_sequence",
    "S2_torch_mlp_true_sequence",
    "S3_torch_mlp_shuffled_sequence",
)
TRUE_MODEL_LEVELS = {"S0_ridge_true_sequence", "S2_torch_mlp_true_sequence"}
SHUFFLED_MODEL_BY_TRUE = {
    "S0_ridge_true_sequence": "S1_ridge_shuffled_sequence",
    "S2_torch_mlp_true_sequence": "S3_torch_mlp_shuffled_sequence",
}
FEATURE_GROUP = "E0_f4_plus_event_sequence"
TARGETS = DIRECT_TARGETS
PRIMARY_TARGET = "delta_capacity_Ah"
PRIMARY_SPLIT = "c_rate_holdout_fold"


def run_minimal_sequence_reopening(
    interval_table_path: Path,
    interval_subsets_path: Path,
    event_sequences_path: Path,
    out_path: Path,
    predictions_out_path: Path,
    *,
    reference_sequence_report_path: Path | None = None,
    reference_stress_report_path: Path | None = None,
    out_dir: Path | None = None,
    subset: str = "baseline_clean_tolerant",
    seed: int = 42,
    model_levels: list[str] | None = None,
    targets: list[str] | None = None,
    split_views: list[str] | None = None,
    mlp_max_iter: int = 200,
) -> dict[str, Any]:
    """Run tiny sequence baselines against shuffled and frozen HGB references."""
    if mlp_max_iter <= 0:
        raise ValueError("mlp_max_iter must be positive.")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, "model level")
    selected_targets = _normalize_selection(targets, TARGETS, "target", default=TARGETS)
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    _preflight_dependencies(selected_models)
    if not event_sequences_path.exists():
        raise FileNotFoundError(f"Event-sequence table not found: {event_sequences_path}")

    all_rows, subset_rows = load_baseline_rows(interval_table_path, interval_subsets_path, subset)
    sequence_by_key = _event_sequences_by_key(event_sequences_path)
    rows = _attach_event_sequences(subset_rows, sequence_by_key)
    if not rows:
        raise ValueError("No rows available after joining event-sequence table.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for model_level in selected_models:
                for target in selected_targets:
                    fold_predictions = _predict_sequence_target(
                        model_level=model_level,
                        train_rows=train_rows,
                        test_rows=test_rows,
                        target=target,
                        seed=seed,
                        mlp_max_iter=mlp_max_iter,
                    )
                    metrics.append(
                        compute_metrics(
                            test_rows,
                            fold_predictions,
                            target=target,
                            subset_name=subset,
                            run_scope="primary",
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level=model_level,
                            feature_group=FEATURE_GROUP,
                            train_rows=train_rows,
                        )
                    )
                    predictions.extend(
                        _prediction_rows(
                            test_rows,
                            fold_predictions,
                            subset_name=subset,
                            split_name=split_name,
                            heldout_fold=heldout_fold,
                            model_level=model_level,
                            target=target,
                        )
                    )

    if not metrics:
        raise ValueError("No minimal sequence reopening metrics were generated.")

    resolved_out_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"interval_table_path": str(interval_table_path).encode(),
                b"interval_subsets_path": str(interval_subsets_path).encode(),
                b"event_sequences_path": str(event_sequences_path).encode(),
            }
        ),
        predictions_out_path,
    )
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "interval_table": str(interval_table_path),
            "interval_subsets": str(interval_subsets_path),
            "event_sequences": str(event_sequences_path),
            "reference_sequence_report": (
                str(reference_sequence_report_path) if reference_sequence_report_path else None
            ),
            "reference_stress_report": (
                str(reference_stress_report_path) if reference_stress_report_path else None
            ),
        },
        "outputs": {
            "report": str(out_path),
            "predictions": str(predictions_out_path),
            "report_dir": str(resolved_out_dir),
        },
        "config": {
            "subset": subset,
            "seed": seed,
            "model_levels": selected_models,
            "targets": selected_targets,
            "split_views": selected_splits,
            "mlp_max_iter": mlp_max_iter,
            "feature_group": FEATURE_GROUP,
            "neural_device_policy": "cuda_required_for_torch_mlp",
        },
        "row_counts": {
            "full_interval_rows": len(all_rows),
            "selected_subset_rows": len(subset_rows),
            "joined_rows": len(rows),
            "selected_parameter_sets": len({int(row["parameter_set"]) for row in rows}),
            "selected_cells": len({str(row["cell_id"]) for row in rows}),
            "prediction_rows": len(predictions),
        },
        "leakage_audit": _leakage_audit(rows),
        "neural_environment": _neural_environment_status(selected_models),
        "metrics": metrics,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_minimal_sequence_artifacts(
        report,
        resolved_out_dir,
        reference_sequence_report_path=reference_sequence_report_path,
        reference_stress_report_path=reference_stress_report_path,
    )
    return report


def render_minimal_sequence_artifacts(
    report: dict[str, Any],
    out_dir: Path,
    *,
    reference_sequence_report_path: Path | None = None,
    reference_stress_report_path: Path | None = None,
) -> None:
    """Render leaderboard, comparisons, and claim-readiness artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    sequence_value_metrics = _load_reference_metrics(reference_sequence_report_path)
    stress_metrics = _load_reference_metrics(reference_stress_report_path)
    leaderboard = _leaderboard_rows(metrics)
    true_vs_shuffled = _true_vs_shuffled_rows(metrics)
    sequence_vs_aggregate = _reference_comparison_rows(
        metrics,
        sequence_value_metrics,
        reference_model_level="L2_hist_gradient_boosting",
        reference_feature_group="F14_event_aggregate",
        comparison_name="true_sequence_vs_event_aggregate_hgb",
    )
    sequence_vs_stress = _reference_comparison_rows(
        metrics,
        stress_metrics,
        reference_model_level="L2_hist_gradient_boosting",
        reference_feature_group="F8_timestamp_weighted_stress",
        comparison_name="true_sequence_vs_timestamp_stress_hgb",
    )
    c_rate_rows = [
        row
        for row in [*true_vs_shuffled, *sequence_vs_aggregate, *sequence_vs_stress]
        if row["split_name"] == PRIMARY_SPLIT
    ]
    readiness = _claim_readiness_rows(
        true_vs_shuffled,
        sequence_vs_aggregate,
        sequence_vs_stress,
        report["leakage_audit"],
        report.get("neural_environment", {}),
    )

    _write_csv(out_dir / "leaderboard.csv", leaderboard)
    _write_csv(plots_dir / "sequence_vs_shuffled.csv", true_vs_shuffled)
    _write_csv(plots_dir / "sequence_vs_aggregate.csv", sequence_vs_aggregate)
    _write_csv(plots_dir / "sequence_vs_stress.csv", sequence_vs_stress)
    _write_csv(plots_dir / "c_rate_sequence_reopening.csv", c_rate_rows)
    _write_csv(plots_dir / "sequence_reopening_claim_readiness.csv", readiness)
    _write_diagnostics_md(
        out_dir / "minimal_sequence_reopening_diagnostics.md",
        true_vs_shuffled,
        sequence_vs_aggregate,
        sequence_vs_stress,
    )
    _write_claim_readiness_md(
        out_dir / "sequence_reopening_claim_readiness.md",
        readiness,
    )


def _predict_sequence_target(
    *,
    model_level: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    mlp_max_iter: int,
) -> list[dict[str, float | None]]:
    np, Ridge = _import_sklearn_sequence_stack()
    encoder = FeatureEncoder.fit(train_rows, "F4_state_log_age_scalar")
    base_train = np.asarray(encoder.transform(train_rows, standardize_numeric=True), dtype=float)
    base_test = np.asarray(encoder.transform(test_rows, standardize_numeric=True), dtype=float)
    sequence_column = _sequence_column(model_level)
    sequence_train = np.asarray([row[sequence_column] + row["event_mask"] for row in train_rows], dtype=float)
    sequence_test = np.asarray([row[sequence_column] + row["event_mask"] for row in test_rows], dtype=float)
    x_train = np.concatenate([base_train, sequence_train], axis=1)
    x_test = np.concatenate([base_test, sequence_test], axis=1)
    x_train, x_test = _standardize_matrices(np, x_train, x_test)
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not bool(np.isfinite(y_train).all()):
        raise ValueError(f"Target {target} has non-finite train values.")

    if model_level.startswith("S0_") or model_level.startswith("S1_"):
        model = Ridge(alpha=1.0)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
    elif model_level.startswith("S2_") or model_level.startswith("S3_"):
        values = _fit_torch_mlp_predictions(
            x_train,
            y_train,
            x_test,
            seed=seed,
            max_iter=mlp_max_iter,
        )
    else:
        raise ValueError(f"Unknown sequence model level: {model_level}")
    return [
        _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
        for row, value in zip(test_rows, values)
    ]


def _event_sequences_by_key(path: Path) -> dict[tuple[str, int, int], dict[str, Any]]:
    rows = pq.read_table(path).to_pylist()
    by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        key = _interval_key(row)
        if key in by_key:
            raise ValueError(f"Duplicate event-sequence interval key: {key}")
        expected = int(row["max_events"]) * int(row["event_feature_count"])
        if len(row["true_sequence_vector"]) != expected:
            raise ValueError(f"Invalid true sequence vector length for {key}.")
        if len(row["shuffled_sequence_vector"]) != expected:
            raise ValueError(f"Invalid shuffled sequence vector length for {key}.")
        by_key[key] = row
    return by_key


def _attach_event_sequences(
    rows: list[dict[str, Any]],
    sequence_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        sequence = sequence_by_key.get(_interval_key(row))
        if sequence is None:
            raise ValueError(f"Event-sequence table is missing interval key: {_interval_key(row)}")
        merged = dict(row)
        merged["true_sequence_vector"] = [float(value) for value in sequence["true_sequence_vector"]]
        merged["shuffled_sequence_vector"] = [
            float(value) for value in sequence["shuffled_sequence_vector"]
        ]
        merged["event_mask"] = [float(value) for value in sequence["event_mask"]]
        merged["event_count"] = int(sequence["event_count"])
        merged["selected_event_count"] = int(sequence["selected_event_count"])
        merged["event_feature_columns"] = str(sequence["event_feature_columns"])
        output.append(merged)
    return output


def _standardize_matrices(np: Any, x_train: Any, x_test: Any) -> tuple[Any, Any]:
    center = np.nanmean(x_train, axis=0)
    scale = np.nanstd(x_train, axis=0)
    scale = np.where(scale <= 1e-12, 1.0, scale)
    x_train = np.where(np.isfinite(x_train), x_train, center)
    x_test = np.where(np.isfinite(x_test), x_test, center)
    return (x_train - center) / scale, (x_test - center) / scale


def _true_vs_shuffled_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            str(row["model_level"]),
            str(row["target"]),
            str(row["split_name"]),
            int(row["heldout_fold"]),
        ): row
        for row in metrics
    }
    rows = []
    for true_model, shuffled_model in SHUFFLED_MODEL_BY_TRUE.items():
        for key, candidate in sorted(by_key.items()):
            model_level, target, split_name, heldout_fold = key
            if model_level != true_model:
                continue
            reference = by_key.get((shuffled_model, target, split_name, heldout_fold))
            if reference is None:
                continue
            rows.append(_comparison_row("true_sequence_vs_shuffled", reference, candidate))
    return rows


def _reference_comparison_rows(
    metrics: list[dict[str, Any]],
    reference_metrics: list[dict[str, Any]],
    *,
    reference_model_level: str,
    reference_feature_group: str,
    comparison_name: str,
) -> list[dict[str, Any]]:
    if not reference_metrics:
        return []
    references = {
        (str(row["target"]), str(row["split_name"]), int(row["heldout_fold"])): row
        for row in reference_metrics
        if str(row.get("run_scope")) == "primary"
        and str(row.get("model_level")) == reference_model_level
        and str(row.get("feature_group")) == reference_feature_group
    }
    rows = []
    for candidate in metrics:
        if str(candidate["model_level"]) not in TRUE_MODEL_LEVELS:
            continue
        key = (
            str(candidate["target"]),
            str(candidate["split_name"]),
            int(candidate["heldout_fold"]),
        )
        reference = references.get(key)
        if reference is not None:
            rows.append(_comparison_row(comparison_name, reference, candidate))
    return rows


def _comparison_row(
    comparison: str,
    reference: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    reference_mae = _as_float(reference["condition_mean_mae"])
    candidate_mae = _as_float(candidate["condition_mean_mae"])
    return {
        "comparison": comparison,
        "target": candidate["target"],
        "split_name": candidate["split_name"],
        "heldout_fold": candidate["heldout_fold"],
        "reference_model_level": reference["model_level"],
        "reference_feature_group": reference["feature_group"],
        "candidate_model_level": candidate["model_level"],
        "candidate_feature_group": candidate["feature_group"],
        "reference_condition_mean_mae": reference_mae,
        "candidate_condition_mean_mae": candidate_mae,
        "gain": reference_mae - candidate_mae,
        "test_rows": candidate["test_rows"],
        "test_parameter_sets": candidate["test_parameter_sets"],
    }


def _claim_readiness_rows(
    true_vs_shuffled: list[dict[str, Any]],
    sequence_vs_aggregate: list[dict[str, Any]],
    sequence_vs_stress: list[dict[str, Any]],
    leakage_audit: dict[str, Any],
    neural_environment: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _summary_claim("True sequence beats shuffled order", true_vs_shuffled),
        _summary_claim("True sequence beats aggregate event HGB", sequence_vs_aggregate),
        _summary_claim("True sequence beats timestamp-stress HGB", sequence_vs_stress),
        _c_rate_claim(true_vs_shuffled, sequence_vs_aggregate, sequence_vs_stress),
        {
            "claim_area": "Leakage audit",
            "status": "supported_for_diagnostics"
            if leakage_audit["status"] == "passed"
            else "blocked",
            "evidence": leakage_audit["evidence"],
        },
        _neural_environment_claim(neural_environment),
        _reopening_gate_claim(true_vs_shuffled, sequence_vs_aggregate, sequence_vs_stress),
        {
            "claim_area": "CBAT readiness",
            "status": "blocked",
            "evidence": "This gate can only authorize a later narrow sequence baseline, not CBAT or policy ranking.",
        },
    ]


def _neural_environment_claim(neural_environment: dict[str, Any]) -> dict[str, Any]:
    if neural_environment.get("torch_mlp_models_evaluated"):
        return {
            "claim_area": "Torch MLP GPU execution",
            "status": "supported_for_diagnostics",
            "evidence": str(neural_environment.get("evidence", "CUDA Torch MLP rows evaluated.")),
        }
    return {
        "claim_area": "Torch MLP GPU execution",
        "status": "blocked",
        "evidence": str(
            neural_environment.get(
                "evidence",
                "Torch MLP rows were not evaluated; neural models must run on CUDA.",
            )
        ),
    }


def _summary_claim(claim_area: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"claim_area": claim_area, "status": "blocked", "evidence": "No comparison rows."}
    gains = [_as_float(row["gain"]) for row in rows]
    positive = sum(gain > 0 for gain in gains)
    mean_gain = _mean(gains)
    status = "supported_for_diagnostics" if mean_gain > 0 and positive / len(gains) >= 0.6 else "not_supported"
    return {
        "claim_area": claim_area,
        "status": status,
        "evidence": (
            f"mean gain={_format_diagnostic_value(mean_gain)}; "
            f"positive rows={positive}/{len(gains)}."
        ),
    }


def _c_rate_claim(
    true_vs_shuffled: list[dict[str, Any]],
    sequence_vs_aggregate: list[dict[str, Any]],
    sequence_vs_stress: list[dict[str, Any]],
) -> dict[str, Any]:
    c_rate_rows = [
        row
        for row in [*true_vs_shuffled, *sequence_vs_aggregate, *sequence_vs_stress]
        if row["target"] == PRIMARY_TARGET and row["split_name"] == PRIMARY_SPLIT
    ]
    if not c_rate_rows:
        return {
            "claim_area": "C-rate sequence reopening",
            "status": "blocked",
            "evidence": "No C-rate delta-capacity comparison rows.",
        }
    gains = [_as_float(row["gain"]) for row in c_rate_rows]
    positive = sum(gain > 0 for gain in gains)
    status = "supported_for_diagnostics" if positive == len(gains) else "not_supported"
    return {
        "claim_area": "C-rate sequence reopening",
        "status": status,
        "evidence": (
            f"C-rate delta comparison positive rows={positive}/{len(gains)}; "
            f"mean gain={_format_diagnostic_value(_mean(gains))}."
        ),
    }


def _reopening_gate_claim(
    true_vs_shuffled: list[dict[str, Any]],
    sequence_vs_aggregate: list[dict[str, Any]],
    sequence_vs_stress: list[dict[str, Any]],
) -> dict[str, Any]:
    for model in TRUE_MODEL_LEVELS:
        if _model_passes_reopening_gate(model, true_vs_shuffled, sequence_vs_aggregate, sequence_vs_stress):
            return {
                "claim_area": "Sequence/neural next-gate readiness",
                "status": "supported_for_diagnostics",
                "evidence": (
                    f"{model} beats shuffled, aggregate, and stress references "
                    "for C-rate delta and at least one non-C-rate grouped view."
                ),
            }
    return {
        "claim_area": "Sequence/neural next-gate readiness",
        "status": "blocked",
        "evidence": (
            "No predeclared true-sequence model beats shuffled, aggregate, and stress "
            "references across the required C-rate and non-C-rate checks."
        ),
    }


def _model_passes_reopening_gate(
    model: str,
    true_vs_shuffled: list[dict[str, Any]],
    sequence_vs_aggregate: list[dict[str, Any]],
    sequence_vs_stress: list[dict[str, Any]],
) -> bool:
    groups = [true_vs_shuffled, sequence_vs_aggregate, sequence_vs_stress]
    c_rate_pass = all(_mean_gain(rows, model, PRIMARY_TARGET, PRIMARY_SPLIT) > 0 for rows in groups)
    if not c_rate_pass:
        return False
    non_c_rate_splits = {
        str(row["split_name"])
        for row in [*true_vs_shuffled, *sequence_vs_aggregate, *sequence_vs_stress]
        if row["split_name"] != PRIMARY_SPLIT
    }
    return any(
        all(_mean_gain(rows, model, PRIMARY_TARGET, split_name) > 0 for rows in groups)
        for split_name in non_c_rate_splits
    )


def _mean_gain(rows: list[dict[str, Any]], model: str, target: str, split_name: str) -> float:
    gains = [
        _as_float(row["gain"])
        for row in rows
        if row["candidate_model_level"] == model
        and row["target"] == target
        and row["split_name"] == split_name
    ]
    return _mean(gains) if gains else -math.inf


def _write_diagnostics_md(
    path: Path,
    true_vs_shuffled: list[dict[str, Any]],
    sequence_vs_aggregate: list[dict[str, Any]],
    sequence_vs_stress: list[dict[str, Any]],
) -> None:
    lines = [
        "# Minimal Sequence Reopening Diagnostics",
        "",
        "Positive gain means the true-sequence candidate has lower condition-mean MAE.",
        "",
        "| Comparison | Target | Split | Model | Mean gain | Positive rows | Rows |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for rows in (true_vs_shuffled, sequence_vs_aggregate, sequence_vs_stress):
        for summary in _summary_rows(rows):
            lines.append(
                f"| `{summary['comparison']}` | `{summary['target']}` | "
                f"`{summary['split_name']}` | `{summary['candidate_model_level']}` | "
                f"{_format_diagnostic_value(summary['mean_gain'])} | "
                f"{summary['positive_rows']} | {summary['rows']} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Minimal Sequence Reopening Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["comparison"]),
                str(row["target"]),
                str(row["split_name"]),
                str(row["candidate_model_level"]),
            )
        ].append(_as_float(row["gain"]))
    return [
        {
            "comparison": comparison,
            "target": target,
            "split_name": split_name,
            "candidate_model_level": model,
            "mean_gain": _mean(gains),
            "positive_rows": sum(gain > 0 for gain in gains),
            "rows": len(gains),
        }
        for (comparison, target, split_name, model), gains in sorted(grouped.items())
    ]


def _load_reference_metrics(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf-8"))
    return list(report.get("metrics", []))


def _leakage_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden = {
        "capacity_Ah_k1",
        "delta_capacity_Ah",
        "delta_capacity_soh",
        "pulse_1s_resistance_k1",
        "delta_pulse_1s_resistance",
        "eis_z_abs_1kHz_k1",
        "delta_eis_z_abs_1kHz",
    }
    event_columns = set()
    for row in rows[:10]:
        event_columns.update(str(row["event_feature_columns"]).split(","))
    overlap = sorted(forbidden & event_columns)
    status = "failed" if overlap else "passed"
    return {
        "status": status,
        "forbidden_feature_overlap": overlap,
        "evidence": (
            "Event-sequence vectors use run-event summaries plus F4 current-state features; "
            "future diagnostic and target-derived fields are excluded."
            if status == "passed"
            else f"Forbidden event-sequence columns present: {overlap}"
        ),
    }


def _sequence_column(model_level: str) -> str:
    if "shuffled" in model_level:
        return "shuffled_sequence_vector"
    if "true" in model_level:
        return "true_sequence_vector"
    raise ValueError(f"Unknown sequence model level: {model_level}")


def _prediction_rows(
    test_rows: list[dict[str, Any]],
    predictions: list[dict[str, float | None]],
    *,
    subset_name: str,
    split_name: str,
    heldout_fold: int,
    model_level: str,
    target: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row, prediction in zip(test_rows, predictions):
        y_true = _evaluation_target_value(row, target)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "subset_name": subset_name,
                "run_scope": "primary",
                "split_name": split_name,
                "heldout_fold": heldout_fold,
                "model_level": model_level,
                "feature_group": FEATURE_GROUP,
                "target": target,
                "cell_id": row["cell_id"],
                "parameter_set": int(row["parameter_set"]),
                "replicate_id": int(row["replicate_id"]),
                "checkup_k": int(row["checkup_k"]),
                "checkup_k_next": int(row["checkup_k_next"]),
                "sensitivity_flagged_monotonicity": bool(
                    row["sensitivity_flagged_monotonicity"]
                ),
                "y_true": y_true,
                "y_pred": _as_float(prediction["y_pred"]),
                "y_pred_q10": None,
                "y_pred_q50": None,
                "y_pred_q90": None,
            }
        )
    return rows


def _evaluation_target_value(row: dict[str, Any], target: str) -> float:
    if target == "capacity_Ah_k1":
        return _as_float(row.get("capacity_Ah_k1"))
    if target == "delta_capacity_Ah":
        return _as_float(row.get("delta_capacity_Ah"))
    raise ValueError(f"Unknown target: {target}")


def _point_prediction(value: float) -> dict[str, float | None]:
    return {"y_pred": value, "y_pred_q10": None, "y_pred_q50": None, "y_pred_q90": None}


def _interval_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return (str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"]))


def _preflight_dependencies(model_levels: list[str]) -> None:
    if any(model.startswith("S2_") or model.startswith("S3_") for model in model_levels):
        _import_torch_stack()
    elif model_levels:
        _import_sklearn_sequence_stack()


def _import_sklearn_sequence_stack() -> tuple[Any, Any]:
    try:
        import numpy as np
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Minimal sequence reopening Ridge baselines require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry."
        ) from exc
    return np, Ridge


def _neural_environment_status(model_levels: list[str]) -> dict[str, Any]:
    torch_models = [model for model in model_levels if model.startswith("S2_") or model.startswith("S3_")]
    if torch_models:
        return {
            "torch_mlp_models_requested": torch_models,
            "torch_mlp_models_evaluated": True,
            "cuda_required": True,
            "torch_available": True,
            "cuda_available": True,
            "evidence": f"CUDA Torch MLP model rows evaluated for {', '.join(torch_models)}.",
        }
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return {
            "torch_mlp_models_requested": [],
            "torch_mlp_models_evaluated": False,
            "cuda_required": True,
            "torch_available": False,
            "cuda_available": False,
            "evidence": (
                "Torch MLP rows were not evaluated. PyTorch is not installed in the "
                "project environment, and CPU fallback is disabled."
            ),
        }
    cuda_available = bool(torch.cuda.is_available())
    return {
        "torch_mlp_models_requested": [],
        "torch_mlp_models_evaluated": False,
        "cuda_required": True,
        "torch_available": True,
        "cuda_available": cuda_available,
        "evidence": (
            "Torch MLP rows were not evaluated in this run. CUDA is available."
            if cuda_available
            else "Torch MLP rows were not evaluated. PyTorch is installed but CUDA is unavailable."
        ),
    }


def _import_torch_stack() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Torch MLP sequence baselines require PyTorch. Install the neural dependency "
            "extra and retry; CPU fallback is intentionally disabled."
        ) from exc
    if not torch.cuda.is_available():
        raise RuntimeError(
            "Torch MLP sequence baselines require CUDA. GPU execution is mandatory for "
            "neural models in this gate; CPU fallback is intentionally disabled."
        )
    return torch


def _fit_torch_mlp_predictions(
    x_train: Any,
    y_train: Any,
    x_test: Any,
    *,
    seed: int,
    max_iter: int,
) -> list[float]:
    torch = _import_torch_stack()
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    device = torch.device("cuda")
    x_train_tensor = torch.as_tensor(x_train, dtype=torch.float32, device=device)
    y_train_tensor = torch.as_tensor(y_train.reshape(-1, 1), dtype=torch.float32, device=device)
    x_test_tensor = torch.as_tensor(x_test, dtype=torch.float32, device=device)
    model = torch.nn.Sequential(
        torch.nn.Linear(x_train_tensor.shape[1], 32),
        torch.nn.ReLU(),
        torch.nn.Linear(32, 1),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    loss_fn = torch.nn.MSELoss()
    model.train()
    for _ in range(max_iter):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(x_train_tensor), y_train_tensor)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        values = model(x_test_tensor).detach().cpu().numpy().reshape(-1)
    del x_train_tensor, y_train_tensor, x_test_tensor, model
    torch.cuda.empty_cache()
    return [float(value) for value in values]


def _default_report_dir(out_path: Path) -> Path:
    return out_path.with_suffix("")
