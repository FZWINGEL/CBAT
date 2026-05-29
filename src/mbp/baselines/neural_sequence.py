"""GPU-backed neural sequence architecture gate for capacity prediction."""

from __future__ import annotations

from collections import defaultdict
import html
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

SCHEMA_VERSION = "gate90.neural_sequence_architecture.v1"
FEATURE_GROUP = "E1_f4_plus_event_sequence_tensor"
PRIMARY_TARGET = "delta_capacity_Ah"
PRIMARY_SPLIT = "c_rate_holdout_fold"
TARGETS = DIRECT_TARGETS
MODEL_LEVELS = (
    "NS1_ridge_flat_true_sequence",
    "NS2_ridge_flat_shuffled_sequence",
    "NS3_cnn1d_true_sequence",
    "NS4_tcn_true_sequence",
    "NS5_cnn_lstm_true_sequence",
    "NS6_cnn_lstm_shuffled_sequence",
)
TRUE_MODEL_LEVELS = {
    "NS1_ridge_flat_true_sequence",
    "NS3_cnn1d_true_sequence",
    "NS4_tcn_true_sequence",
    "NS5_cnn_lstm_true_sequence",
}
SHUFFLED_MODEL_BY_TRUE = {
    "NS1_ridge_flat_true_sequence": "NS2_ridge_flat_shuffled_sequence",
    "NS5_cnn_lstm_true_sequence": "NS6_cnn_lstm_shuffled_sequence",
}
NEURAL_MODEL_LEVELS = {
    "NS3_cnn1d_true_sequence",
    "NS4_tcn_true_sequence",
    "NS5_cnn_lstm_true_sequence",
    "NS6_cnn_lstm_shuffled_sequence",
}


def run_neural_sequence_gate(
    interval_table_path: Path,
    interval_subsets_path: Path,
    sequence_tensors_path: Path,
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
    max_epochs: int = 150,
    patience: int = 20,
    batch_size: int = 64,
    device: str = "cuda",
) -> dict[str, Any]:
    """Run grouped neural sequence baselines against shuffled and HGB references."""
    if max_epochs <= 0:
        raise ValueError("max_epochs must be positive.")
    if patience <= 0:
        raise ValueError("patience must be positive.")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")
    selected_models = _normalize_selection(model_levels, MODEL_LEVELS, "model level")
    selected_targets = _normalize_selection(targets, TARGETS, "target", default=TARGETS)
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    _preflight_dependencies(selected_models, device=device)
    if not sequence_tensors_path.exists():
        raise FileNotFoundError(f"Event-sequence tensor table not found: {sequence_tensors_path}")

    all_rows, subset_rows = load_baseline_rows(interval_table_path, interval_subsets_path, subset)
    tensor_by_key = _sequence_tensors_by_key(sequence_tensors_path)
    rows = _attach_sequence_tensors(subset_rows, tensor_by_key)
    if not rows:
        raise ValueError("No rows available after joining event-sequence tensor table.")

    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    training_history: list[dict[str, Any]] = []
    for split_name in selected_splits:
        for heldout_fold, train_rows, test_rows in iter_split_instances(rows, split_name):
            assert_no_parameter_set_leakage(train_rows, test_rows, split_name, heldout_fold)
            for model_level in selected_models:
                for target in selected_targets:
                    fold_predictions, history_rows = _predict_sequence_target(
                        model_level=model_level,
                        train_rows=train_rows,
                        test_rows=test_rows,
                        target=target,
                        seed=seed,
                        max_epochs=max_epochs,
                        patience=patience,
                        batch_size=batch_size,
                        device=device,
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
                    training_history.extend(
                        {
                            **history,
                            "target": target,
                            "split_name": split_name,
                            "heldout_fold": heldout_fold,
                            "model_level": model_level,
                        }
                        for history in history_rows
                    )

    if not metrics:
        raise ValueError("No neural sequence gate metrics were generated.")

    resolved_out_dir = out_dir or _default_report_dir(out_path)
    predictions_out_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_table = pa.Table.from_pylist(predictions, schema=BASELINE_PREDICTION_SCHEMA)
    pq.write_table(
        prediction_table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"interval_table_path": str(interval_table_path).encode(),
                b"interval_subsets_path": str(interval_subsets_path).encode(),
                b"sequence_tensors_path": str(sequence_tensors_path).encode(),
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
            "sequence_tensors": str(sequence_tensors_path),
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
            "max_epochs": max_epochs,
            "patience": patience,
            "batch_size": batch_size,
            "device": device,
            "feature_group": FEATURE_GROUP,
            "neural_device_policy": "cuda_required_for_neural_sequence_models",
        },
        "row_counts": {
            "full_interval_rows": len(all_rows),
            "selected_subset_rows": len(subset_rows),
            "joined_rows": len(rows),
            "selected_parameter_sets": len({int(row["parameter_set"]) for row in rows}),
            "selected_cells": len({str(row["cell_id"]) for row in rows}),
            "prediction_rows": len(predictions),
            "training_history_rows": len(training_history),
        },
        "sequence_tensor_summary": _tensor_summary(rows),
        "leakage_audit": _leakage_audit(rows),
        "neural_environment": _neural_environment_status(selected_models, device=device),
        "metrics": metrics,
        "training_history": training_history,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_neural_sequence_artifacts(
        report,
        resolved_out_dir,
        reference_sequence_report_path=reference_sequence_report_path,
        reference_stress_report_path=reference_stress_report_path,
    )
    return report


def render_neural_sequence_artifacts(
    report: dict[str, Any],
    out_dir: Path,
    *,
    reference_sequence_report_path: Path | None = None,
    reference_stress_report_path: Path | None = None,
) -> dict[str, Any]:
    """Render leaderboard, comparisons, claim readiness, and SVG figures."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    figures_dir = out_dir / "figures"
    plots_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    metrics = list(report["metrics"])
    sequence_value_metrics = _load_reference_metrics(reference_sequence_report_path)
    stress_metrics = _load_reference_metrics(reference_stress_report_path)
    leaderboard = _leaderboard_rows(metrics)
    true_vs_shuffled = _true_vs_shuffled_rows(metrics)
    neural_vs_aggregate = _reference_comparison_rows(
        metrics,
        sequence_value_metrics,
        reference_model_level="L2_hist_gradient_boosting",
        reference_feature_group="F14_event_aggregate",
        comparison_name="true_neural_sequence_vs_event_aggregate_hgb",
    )
    neural_vs_stress = _reference_comparison_rows(
        metrics,
        stress_metrics,
        reference_model_level="L2_hist_gradient_boosting",
        reference_feature_group="F8_timestamp_weighted_stress",
        comparison_name="true_neural_sequence_vs_timestamp_stress_hgb",
    )
    c_rate_rows = [
        row
        for row in [*true_vs_shuffled, *neural_vs_aggregate, *neural_vs_stress]
        if row["split_name"] == PRIMARY_SPLIT and row["target"] == PRIMARY_TARGET
    ]
    condition_hotspots = _condition_error_hotspots(metrics)
    readiness = _claim_readiness_rows(
        true_vs_shuffled,
        neural_vs_aggregate,
        neural_vs_stress,
        report["leakage_audit"],
        report.get("neural_environment", {}),
    )
    training_history = list(report.get("training_history", []))

    _write_csv(out_dir / "leaderboard.csv", leaderboard)
    _write_csv(plots_dir / "neural_vs_shuffled_gain.csv", true_vs_shuffled)
    _write_csv(plots_dir / "neural_vs_aggregate_gain.csv", neural_vs_aggregate)
    _write_csv(plots_dir / "neural_vs_stress_gain.csv", neural_vs_stress)
    _write_csv(plots_dir / "c_rate_neural_sequence.csv", c_rate_rows)
    _write_csv(plots_dir / "condition_error_hotspots.csv", condition_hotspots)
    _write_csv(plots_dir / "training_curves.csv", training_history)
    _write_csv(plots_dir / "neural_sequence_claim_readiness.csv", readiness)
    _write_diagnostics_md(
        out_dir / "neural_sequence_diagnostics.md",
        true_vs_shuffled,
        neural_vs_aggregate,
        neural_vs_stress,
    )
    _write_claim_readiness_md(out_dir / "neural_sequence_claim_readiness.md", readiness)
    _write_leakage_audit_md(out_dir / "neural_sequence_leakage_audit.md", report["leakage_audit"])
    figure_paths = _write_figures(
        figures_dir,
        true_vs_shuffled,
        neural_vs_aggregate,
        neural_vs_stress,
        c_rate_rows,
        condition_hotspots,
        training_history,
        report.get("sequence_tensor_summary", {}),
        readiness,
    )
    figure_qa = _figure_qa_rows(figure_paths, plots_dir)
    _write_csv(plots_dir / "figure_qa.csv", figure_qa)
    return {
        "leaderboard_rows": len(leaderboard),
        "true_vs_shuffled_rows": len(true_vs_shuffled),
        "neural_vs_aggregate_rows": len(neural_vs_aggregate),
        "neural_vs_stress_rows": len(neural_vs_stress),
        "figure_rows": len(figure_qa),
    }


def _predict_sequence_target(
    *,
    model_level: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    target: str,
    seed: int,
    max_epochs: int,
    patience: int,
    batch_size: int,
    device: str,
) -> tuple[list[dict[str, float | None]], list[dict[str, Any]]]:
    np, Ridge = _import_sklearn_stack()
    encoder = FeatureEncoder.fit(train_rows, "F4_state_log_age_scalar")
    base_train = np.asarray(encoder.transform(train_rows, standardize_numeric=True), dtype=float)
    base_test = np.asarray(encoder.transform(test_rows, standardize_numeric=True), dtype=float)
    sequence_column = _sequence_column(model_level)
    seq_train, mask_train, seq_test, mask_test = _sequence_arrays(
        np,
        train_rows,
        test_rows,
        sequence_column,
    )
    y_train = np.asarray([_training_target_value(row, target) for row in train_rows], dtype=float)
    if not bool(np.isfinite(y_train).all()):
        raise ValueError(f"Target {target} has non-finite train values.")

    if model_level.startswith("NS1_") or model_level.startswith("NS2_"):
        flat_train = seq_train.reshape(seq_train.shape[0], -1)
        flat_test = seq_test.reshape(seq_test.shape[0], -1)
        x_train = np.concatenate([base_train, flat_train, mask_train], axis=1)
        x_test = np.concatenate([base_test, flat_test, mask_test], axis=1)
        x_train, x_test = _standardize_matrices(np, x_train, x_test)
        model = Ridge(alpha=1.0)
        model.fit(x_train, y_train)
        values = model.predict(x_test)
        history_rows: list[dict[str, Any]] = []
    elif model_level in NEURAL_MODEL_LEVELS:
        values, history_rows = _fit_torch_sequence_predictions(
            model_level,
            base_train,
            seq_train,
            mask_train,
            y_train,
            base_test,
            seq_test,
            mask_test,
            train_rows=train_rows,
            seed=seed,
            max_epochs=max_epochs,
            patience=patience,
            batch_size=batch_size,
            device=device,
        )
    else:
        raise ValueError(f"Unknown neural sequence model level: {model_level}")
    return (
        [
            _point_prediction(_prediction_to_evaluation_space(row, target, float(value)))
            for row, value in zip(test_rows, values)
        ],
        history_rows,
    )


def _sequence_tensors_by_key(path: Path) -> dict[tuple[str, int, int], dict[str, Any]]:
    rows = pq.read_table(path).to_pylist()
    by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        key = _interval_key(row)
        if key in by_key:
            raise ValueError(f"Duplicate event-sequence tensor interval key: {key}")
        expected = int(row["max_events"]) * int(row["event_feature_count"])
        if len(row["true_sequence_vector"]) != expected:
            raise ValueError(f"Invalid true sequence vector length for {key}.")
        if len(row["shuffled_sequence_vector"]) != expected:
            raise ValueError(f"Invalid shuffled sequence vector length for {key}.")
        by_key[key] = row
    return by_key


def _attach_sequence_tensors(
    rows: list[dict[str, Any]],
    tensor_by_key: dict[tuple[str, int, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        tensor = tensor_by_key.get(_interval_key(row))
        if tensor is None:
            raise ValueError(f"Event-sequence tensor table is missing interval key: {_interval_key(row)}")
        merged = dict(row)
        merged["true_sequence_vector"] = [float(value) for value in tensor["true_sequence_vector"]]
        merged["shuffled_sequence_vector"] = [
            float(value) for value in tensor["shuffled_sequence_vector"]
        ]
        merged["event_mask"] = [float(value) for value in tensor["event_mask"]]
        merged["event_count"] = int(tensor["event_count"])
        merged["selected_event_count"] = int(tensor["selected_event_count"])
        merged["truncated_event_count"] = int(tensor["truncated_event_count"])
        merged["max_events"] = int(tensor["max_events"])
        merged["event_feature_count"] = int(tensor["event_feature_count"])
        merged["event_feature_columns"] = str(tensor["event_feature_columns"])
        merged["sampling_policy"] = str(tensor["sampling_policy"])
        output.append(merged)
    return output


def _sequence_arrays(
    np: Any,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    sequence_column: str,
) -> tuple[Any, Any, Any, Any]:
    max_events = int(train_rows[0]["max_events"])
    width = int(train_rows[0]["event_feature_count"])
    train = np.asarray(
        [row[sequence_column] for row in train_rows],
        dtype=float,
    ).reshape(len(train_rows), max_events, width)
    test = np.asarray(
        [row[sequence_column] for row in test_rows],
        dtype=float,
    ).reshape(len(test_rows), max_events, width)
    train_mask = np.asarray([row["event_mask"] for row in train_rows], dtype=float)
    test_mask = np.asarray([row["event_mask"] for row in test_rows], dtype=float)
    valid = train_mask > 0.0
    center = np.zeros(width, dtype=float)
    scale = np.ones(width, dtype=float)
    for col in range(width):
        values = train[:, :, col][valid]
        values = values[np.isfinite(values)]
        if values.size:
            center[col] = float(values.mean())
            std = float(values.std())
            scale[col] = std if std > 1e-12 else 1.0
    train = np.where(np.isfinite(train), train, center)
    test = np.where(np.isfinite(test), test, center)
    return (train - center) / scale, train_mask, (test - center) / scale, test_mask


def _fit_torch_sequence_predictions(
    model_level: str,
    base_train: Any,
    seq_train: Any,
    mask_train: Any,
    y_train: Any,
    base_test: Any,
    seq_test: Any,
    mask_test: Any,
    *,
    train_rows: list[dict[str, Any]],
    seed: int,
    max_epochs: int,
    patience: int,
    batch_size: int,
    device: str,
) -> tuple[list[float], list[dict[str, Any]]]:
    torch = _import_torch_stack(device)
    np, _ = _import_sklearn_stack()
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    train_idx, val_idx = _train_validation_indices(np, train_rows, seed)
    y_mean = float(y_train[train_idx].mean()) if len(train_idx) else float(y_train.mean())
    y_std = float(y_train[train_idx].std()) if len(train_idx) else float(y_train.std())
    if y_std <= 1e-12:
        y_std = 1.0
    y_scaled = (y_train - y_mean) / y_std
    torch_device = torch.device(device)
    base_tensor = torch.as_tensor(base_train, dtype=torch.float32, device=torch_device)
    seq_tensor = torch.as_tensor(seq_train, dtype=torch.float32, device=torch_device)
    mask_tensor = torch.as_tensor(mask_train, dtype=torch.float32, device=torch_device)
    y_tensor = torch.as_tensor(y_scaled.reshape(-1, 1), dtype=torch.float32, device=torch_device)
    base_test_tensor = torch.as_tensor(base_test, dtype=torch.float32, device=torch_device)
    seq_test_tensor = torch.as_tensor(seq_test, dtype=torch.float32, device=torch_device)
    mask_test_tensor = torch.as_tensor(mask_test, dtype=torch.float32, device=torch_device)
    model = _build_torch_model(
        torch,
        model_level,
        sequence_width=int(seq_train.shape[2]),
        base_width=int(base_train.shape[1]),
    ).to(torch_device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    loss_fn = torch.nn.SmoothL1Loss()
    history_rows: list[dict[str, Any]] = []
    best_state: dict[str, Any] | None = None
    best_val = math.inf
    stale_epochs = 0
    generator = torch.Generator(device=torch_device)
    generator.manual_seed(seed)
    train_idx_tensor = torch.as_tensor(train_idx, dtype=torch.long, device=torch_device)
    val_idx_tensor = torch.as_tensor(val_idx, dtype=torch.long, device=torch_device)
    for epoch in range(1, max_epochs + 1):
        model.train()
        order = train_idx_tensor[
            torch.randperm(len(train_idx_tensor), generator=generator, device=torch_device)
        ]
        train_losses = []
        for start in range(0, len(order), batch_size):
            batch_idx = order[start : start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            pred = model(base_tensor[batch_idx], seq_tensor[batch_idx], mask_tensor[batch_idx])
            loss = loss_fn(pred, y_tensor[batch_idx])
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach().cpu()))
        model.eval()
        with torch.no_grad():
            val_pred = model(base_tensor[val_idx_tensor], seq_tensor[val_idx_tensor], mask_tensor[val_idx_tensor])
            val_loss = float(loss_fn(val_pred, y_tensor[val_idx_tensor]).detach().cpu())
        train_loss = _mean(train_losses)
        history_rows.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if val_loss < best_val - 1e-7:
            best_val = val_loss
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= patience:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        values = model(base_test_tensor, seq_test_tensor, mask_test_tensor).detach().cpu().numpy().reshape(-1)
    del base_tensor, seq_tensor, mask_tensor, y_tensor, base_test_tensor, seq_test_tensor, mask_test_tensor, model
    torch.cuda.empty_cache()
    return [float(value * y_std + y_mean) for value in values], history_rows


def _build_torch_model(torch: Any, model_level: str, *, sequence_width: int, base_width: int) -> Any:
    if model_level == "NS3_cnn1d_true_sequence":
        return _CnnSequenceRegressor(torch, sequence_width, base_width)
    if model_level == "NS4_tcn_true_sequence":
        return _TcnSequenceRegressor(torch, sequence_width, base_width)
    if model_level in {"NS5_cnn_lstm_true_sequence", "NS6_cnn_lstm_shuffled_sequence"}:
        return _CnnLstmSequenceRegressor(torch, sequence_width, base_width)
    raise ValueError(f"Unknown neural model level: {model_level}")


def _train_validation_indices(np: Any, train_rows: list[dict[str, Any]], seed: int) -> tuple[Any, Any]:
    parameter_sets = sorted({int(row["parameter_set"]) for row in train_rows})
    if len(parameter_sets) < 3:
        indices = np.arange(len(train_rows))
        return indices, indices
    rng = np.random.default_rng(seed)
    shuffled = list(parameter_sets)
    rng.shuffle(shuffled)
    validation_count = max(1, math.ceil(0.2 * len(shuffled)))
    validation_sets = set(shuffled[:validation_count])
    train_idx = np.asarray(
        [idx for idx, row in enumerate(train_rows) if int(row["parameter_set"]) not in validation_sets],
        dtype=int,
    )
    val_idx = np.asarray(
        [idx for idx, row in enumerate(train_rows) if int(row["parameter_set"]) in validation_sets],
        dtype=int,
    )
    if len(train_idx) == 0 or len(val_idx) == 0:
        indices = np.arange(len(train_rows))
        return indices, indices
    return train_idx, val_idx


class _CnnSequenceRegressor:
    def __new__(cls, torch: Any, sequence_width: int, base_width: int) -> Any:
        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Sequential(
                    torch.nn.Conv1d(sequence_width, 32, kernel_size=5, padding=2),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.2),
                    torch.nn.Conv1d(32, 64, kernel_size=5, padding=2),
                    torch.nn.ReLU(),
                )
                self.head = torch.nn.Sequential(
                    torch.nn.Linear(64 + base_width, 64),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.2),
                    torch.nn.Linear(64, 1),
                )

            def forward(self, base: Any, sequence: Any, mask: Any) -> Any:
                features = self.conv(sequence.transpose(1, 2)).transpose(1, 2)
                pooled = _masked_mean(torch, features, mask)
                return self.head(torch.cat([base, pooled], dim=1))

        return Model()


class _TcnSequenceRegressor:
    def __new__(cls, torch: Any, sequence_width: int, base_width: int) -> Any:
        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.input = torch.nn.Conv1d(sequence_width, 64, kernel_size=1)
                self.blocks = torch.nn.ModuleList(
                    [
                        torch.nn.Conv1d(64, 64, kernel_size=3, padding=dilation, dilation=dilation)
                        for dilation in (1, 2, 4)
                    ]
                )
                self.dropout = torch.nn.Dropout(0.2)
                self.head = torch.nn.Sequential(
                    torch.nn.Linear(64 + base_width, 64),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.2),
                    torch.nn.Linear(64, 1),
                )

            def forward(self, base: Any, sequence: Any, mask: Any) -> Any:
                x = self.input(sequence.transpose(1, 2))
                for block in self.blocks:
                    residual = x
                    x = torch.relu(block(x))
                    x = self.dropout(x) + residual
                pooled = _masked_mean(torch, x.transpose(1, 2), mask)
                return self.head(torch.cat([base, pooled], dim=1))

        return Model()


class _CnnLstmSequenceRegressor:
    def __new__(cls, torch: Any, sequence_width: int, base_width: int) -> Any:
        class Model(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Sequential(
                    torch.nn.Conv1d(sequence_width, 32, kernel_size=5, padding=2),
                    torch.nn.ReLU(),
                )
                self.lstm = torch.nn.LSTM(
                    input_size=32,
                    hidden_size=64,
                    num_layers=1,
                    batch_first=True,
                )
                self.head = torch.nn.Sequential(
                    torch.nn.Linear(64 + base_width, 64),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.2),
                    torch.nn.Linear(64, 1),
                )

            def forward(self, base: Any, sequence: Any, mask: Any) -> Any:
                x = self.conv(sequence.transpose(1, 2)).transpose(1, 2)
                output, _ = self.lstm(x)
                pooled = _masked_mean(torch, output, mask)
                return self.head(torch.cat([base, pooled], dim=1))

        return Model()


def _masked_mean(torch: Any, values: Any, mask: Any) -> Any:
    weights = mask.unsqueeze(-1)
    total = (values * weights).sum(dim=1)
    denominator = weights.sum(dim=1).clamp_min(1.0)
    return total / denominator


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
            rows.append(_comparison_row("true_neural_sequence_vs_shuffled", reference, candidate))
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


def _condition_error_hotspots(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in sorted(
        metrics,
        key=lambda item: _as_float(item.get("worst_condition_mae")),
        reverse=True,
    )[:60]:
        rows.append(
            {
                "model_level": row["model_level"],
                "target": row["target"],
                "split_name": row["split_name"],
                "heldout_fold": row["heldout_fold"],
                "condition_mean_mae": row["condition_mean_mae"],
                "worst_condition_mae": row["worst_condition_mae"],
                "test_parameter_sets": row["test_parameter_sets"],
                "test_rows": row["test_rows"],
            }
        )
    return rows


def _claim_readiness_rows(
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
    leakage_audit: dict[str, Any],
    neural_environment: dict[str, Any],
) -> list[dict[str, Any]]:
    sequence_gate = _sequence_value_gate_claim(
        true_vs_shuffled,
        neural_vs_aggregate,
        neural_vs_stress,
    )
    return [
        _summary_claim("True neural sequence beats shuffled order", true_vs_shuffled),
        _summary_claim("True neural sequence beats aggregate event HGB", neural_vs_aggregate),
        _summary_claim("True neural sequence beats timestamp-stress HGB", neural_vs_stress),
        _c_rate_claim(true_vs_shuffled, neural_vs_aggregate, neural_vs_stress),
        {
            "claim_area": "Leakage audit",
            "status": "supported_for_diagnostics"
            if leakage_audit["status"] == "passed"
            else "blocked",
            "evidence": leakage_audit["evidence"],
        },
        _neural_environment_claim(neural_environment),
        sequence_gate,
        {
            "claim_area": "CBAT prototype readiness",
            "status": "partially_supported"
            if sequence_gate["status"] == "supported_for_diagnostics"
            else "blocked",
            "evidence": (
                "A later narrow CBAT prototype gate is justified only because neural "
                "sequence value passed all predeclared controls."
                if sequence_gate["status"] == "supported_for_diagnostics"
                else "CBAT remains blocked because neural sequence value did not pass all controls."
            ),
        },
    ]


def _summary_claim(claim_area: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"claim_area": claim_area, "status": "blocked", "evidence": "No comparison rows."}
    gains = [_as_float(row["gain"]) for row in rows]
    positive = sum(gain > 0 for gain in gains)
    p05 = _bootstrap_p05(gains)
    mean_gain = _mean(gains)
    status = (
        "supported_for_diagnostics"
        if mean_gain > 0 and p05 > 0 and positive / len(gains) >= 0.6
        else "not_supported"
    )
    return {
        "claim_area": claim_area,
        "status": status,
        "evidence": (
            f"mean gain={_format_diagnostic_value(mean_gain)}; "
            f"bootstrap p05={_format_diagnostic_value(p05)}; "
            f"positive rows={positive}/{len(gains)}."
        ),
    }


def _c_rate_claim(
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
) -> dict[str, Any]:
    c_rate_rows = [
        row
        for row in [*true_vs_shuffled, *neural_vs_aggregate, *neural_vs_stress]
        if row["target"] == PRIMARY_TARGET and row["split_name"] == PRIMARY_SPLIT
    ]
    if not c_rate_rows:
        return {
            "claim_area": "C-rate neural sequence value",
            "status": "blocked",
            "evidence": "No C-rate delta-capacity comparison rows.",
        }
    gains = [_as_float(row["gain"]) for row in c_rate_rows]
    positive = sum(gain > 0 for gain in gains)
    p05 = _bootstrap_p05(gains)
    status = "supported_for_diagnostics" if positive == len(gains) and p05 > 0 else "not_supported"
    return {
        "claim_area": "C-rate neural sequence value",
        "status": status,
        "evidence": (
            f"C-rate delta positive rows={positive}/{len(gains)}; "
            f"mean gain={_format_diagnostic_value(_mean(gains))}; "
            f"bootstrap p05={_format_diagnostic_value(p05)}."
        ),
    }


def _sequence_value_gate_claim(
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
) -> dict[str, Any]:
    for model in TRUE_MODEL_LEVELS:
        if _model_passes_gate(model, true_vs_shuffled, neural_vs_aggregate, neural_vs_stress):
            return {
                "claim_area": "Neural sequence architecture next-gate readiness",
                "status": "supported_for_diagnostics",
                "evidence": (
                    f"{model} beats shuffled, aggregate-event HGB, and timestamp-stress HGB "
                    "on the primary C-rate delta task and at least three grouped split views."
                ),
            }
    return {
        "claim_area": "Neural sequence architecture next-gate readiness",
        "status": "blocked",
        "evidence": (
            "No predeclared neural sequence model beats shuffled, aggregate-event HGB, "
            "and timestamp-stress HGB across the required primary checks."
        ),
    }


def _model_passes_gate(
    model: str,
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
) -> bool:
    groups = [true_vs_shuffled, neural_vs_aggregate, neural_vs_stress]
    if not all(_mean_gain(rows, model, PRIMARY_TARGET, PRIMARY_SPLIT) > 0 for rows in groups):
        return False
    split_names = {
        str(row["split_name"])
        for row in [*true_vs_shuffled, *neural_vs_aggregate, *neural_vs_stress]
    }
    passing_splits = sum(
        all(_mean_gain(rows, model, PRIMARY_TARGET, split_name) > 0 for rows in groups)
        for split_name in split_names
    )
    return passing_splits >= 3


def _mean_gain(rows: list[dict[str, Any]], model: str, target: str, split_name: str) -> float:
    gains = [
        _as_float(row["gain"])
        for row in rows
        if row["candidate_model_level"] == model
        and row["target"] == target
        and row["split_name"] == split_name
    ]
    return _mean(gains) if gains else -math.inf


def _bootstrap_p05(values: list[float], *, seed: int = 42, iterations: int = 500) -> float:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    import random

    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        sample = [finite[rng.randrange(len(finite))] for _ in finite]
        means.append(_mean(sample))
    means.sort()
    return means[max(0, int(0.05 * (len(means) - 1)))]


def _write_diagnostics_md(
    path: Path,
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
) -> None:
    lines = [
        "# Neural Sequence Gate Diagnostics",
        "",
        "Positive gain means the neural sequence candidate has lower condition-mean MAE.",
        "",
        "| Comparison | Target | Split | Model | Mean gain | P05 gain | Positive rows | Rows |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for rows in (true_vs_shuffled, neural_vs_aggregate, neural_vs_stress):
        for summary in _summary_rows(rows):
            lines.append(
                f"| `{summary['comparison']}` | `{summary['target']}` | "
                f"`{summary['split_name']}` | `{summary['candidate_model_level']}` | "
                f"{_format_diagnostic_value(summary['mean_gain'])} | "
                f"{_format_diagnostic_value(summary['p05_gain'])} | "
                f"{summary['positive_rows']} | {summary['rows']} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Neural Sequence Gate Claim Readiness",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_area']} | `{row['status']}` | {row['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_leakage_audit_md(path: Path, leakage_audit: dict[str, Any]) -> None:
    lines = [
        "# Neural Sequence Leakage Audit",
        "",
        f"Status: `{leakage_audit['status']}`",
        "",
        leakage_audit["evidence"],
        "",
        f"Forbidden feature overlap: `{leakage_audit['forbidden_feature_overlap']}`",
    ]
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
            "p05_gain": _bootstrap_p05(gains),
            "positive_rows": sum(gain > 0 for gain in gains),
            "rows": len(gains),
        }
        for (comparison, target, split_name, model), gains in sorted(grouped.items())
    ]


def _write_figures(
    figures_dir: Path,
    true_vs_shuffled: list[dict[str, Any]],
    neural_vs_aggregate: list[dict[str, Any]],
    neural_vs_stress: list[dict[str, Any]],
    c_rate_rows: list[dict[str, Any]],
    condition_hotspots: list[dict[str, Any]],
    training_history: list[dict[str, Any]],
    tensor_summary: dict[str, Any],
    readiness: list[dict[str, Any]],
) -> list[Path]:
    paths = [
        figures_dir / "neural_sequence_gain_matrix.svg",
        figures_dir / "true_vs_shuffled_by_split.svg",
        figures_dir / "c_rate_delta_leaderboard.svg",
        figures_dir / "condition_error_hotspots.svg",
        figures_dir / "training_curves.svg",
        figures_dir / "sequence_sampling_coverage.svg",
        figures_dir / "claim_readiness_summary.svg",
    ]
    _bar_svg(
        paths[0],
        "Neural Sequence Gain Matrix",
        "Mean condition-MAE gain versus non-neural references.",
        _figure_values([*neural_vs_aggregate, *neural_vs_stress], limit=14),
    )
    _bar_svg(
        paths[1],
        "True Order Versus Shuffled Order",
        "Positive bars favor true event order.",
        _figure_values(true_vs_shuffled, limit=14),
    )
    _bar_svg(
        paths[2],
        "C-rate Delta-Capacity Comparisons",
        "Primary held-out C-rate delta-capacity gate.",
        _figure_values(c_rate_rows, limit=14),
    )
    _bar_svg(
        paths[3],
        "Condition Error Hotspots",
        "Worst condition-level MAE rows among evaluated models.",
        [
            (f"{row['model_level']} {row['split_name']}", _as_float(row["worst_condition_mae"]))
            for row in condition_hotspots[:12]
        ],
        value_label="MAE",
    )
    _training_curve_svg(paths[4], training_history)
    _sampling_svg(paths[5], tensor_summary)
    _claim_svg(paths[6], readiness)
    return paths


def _figure_values(rows: list[dict[str, Any]], *, limit: int) -> list[tuple[str, float]]:
    summaries = _summary_rows(rows)
    summaries.sort(key=lambda item: abs(_as_float(item["mean_gain"])), reverse=True)
    return [
        (
            f"{row['candidate_model_level']} {row['target']} {row['split_name']}",
            _as_float(row["mean_gain"]),
        )
        for row in summaries[:limit]
    ]


def _bar_svg(
    path: Path,
    title: str,
    subtitle: str,
    values: list[tuple[str, float]],
    *,
    value_label: str = "gain",
) -> None:
    width = 980
    height = max(320, 110 + 32 * max(1, len(values)))
    max_abs = max([abs(value) for _, value in values] + [1e-12])
    zero_x = 410
    plot_width = 500
    body = [
        _svg_text(24, 36, title, size=22, weight="700"),
        _svg_text(24, 62, subtitle, size=13),
        f'<line x1="{zero_x}" y1="86" x2="{zero_x}" y2="{height - 34}" stroke="#555" stroke-width="1"/>',
    ]
    for idx, (label, value) in enumerate(values or [("no rows", 0.0)]):
        y = 94 + idx * 32
        length = abs(value) / max_abs * (plot_width / 2)
        x = zero_x if value >= 0 else zero_x - length
        color = "#2f855a" if value >= 0 else "#c53030"
        body.append(_svg_text(24, y + 15, _short_label(label), size=11))
        body.append(
            f'<rect x="{x:.1f}" y="{y}" width="{max(1.0, length):.1f}" height="20" '
            f'fill="{color}" opacity="0.85"/>'
        )
        body.append(
            _svg_text(
                zero_x + plot_width / 2 + 16,
                y + 15,
                f"{value_label}={_format_diagnostic_value(value)}",
                size=11,
            )
        )
    _write_svg(path, "\n".join(body), width=width, height=height)


def _training_curve_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    filtered = [
        row
        for row in rows
        if row.get("target") == PRIMARY_TARGET and row.get("split_name") == PRIMARY_SPLIT
    ][:120]
    values = [
        (
            f"{row['model_level']} epoch {row['epoch']}",
            _as_float(row["val_loss"]),
        )
        for row in filtered
    ]
    _bar_svg(
        path,
        "Training Curves",
        "Primary C-rate delta validation losses, first 120 epoch rows.",
        values,
        value_label="val loss",
    )


def _sampling_svg(path: Path, tensor_summary: dict[str, Any]) -> None:
    values = [
        ("rows", _as_float(tensor_summary.get("rows", 0))),
        ("mean events", _as_float(tensor_summary.get("event_count_mean", 0))),
        ("mean selected", _as_float(tensor_summary.get("selected_event_count_mean", 0))),
        ("truncated intervals", _as_float(tensor_summary.get("truncated_intervals", 0))),
    ]
    _bar_svg(
        path,
        "Sequence Sampling Coverage",
        "v2 tensor coverage and time-stratified sampling summary.",
        values,
        value_label="value",
    )


def _claim_svg(path: Path, readiness: list[dict[str, Any]]) -> None:
    status_value = {
        "supported_for_diagnostics": 1.0,
        "partially_supported": 0.5,
        "diagnostic_only": 0.25,
        "not_supported": -0.5,
        "blocked": -1.0,
    }
    values = [
        (str(row["claim_area"]), status_value.get(str(row["status"]), 0.0))
        for row in readiness
    ]
    _bar_svg(
        path,
        "Claim Readiness Summary",
        "Positive status values indicate diagnostic support; blocked stays negative.",
        values,
        value_label="status",
    )


def _write_svg(path: Path, body: str, *, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="#ffffff"/>\n'
        f"{body}\n"
        "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def _svg_text(x: float, y: float, text: str, *, size: int = 12, weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#1a202c">'
        f"{html.escape(str(text))}</text>"
    )


def _short_label(label: str, *, limit: int = 54) -> str:
    return label if len(label) <= limit else label[: limit - 3] + "..."


def _figure_qa_rows(figure_paths: list[Path], plots_dir: Path) -> list[dict[str, Any]]:
    source_csvs = sorted(plots_dir.glob("*.csv"))
    source_rows = sum(1 for path in source_csvs if path.stat().st_size > 0)
    return [
        {
            "figure_path": str(path),
            "exists": path.exists(),
            "nonempty": path.exists() and path.stat().st_size > 0,
            "source_csv_count": len(source_csvs),
            "nonempty_source_csv_count": source_rows,
        }
        for path in figure_paths
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
            "Event-sequence tensors use run-event summaries plus F4 current-state features; "
            "future diagnostic and target-derived fields are excluded."
            if status == "passed"
            else f"Forbidden event-sequence tensor columns present: {overlap}"
        ),
    }


def _tensor_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    event_counts = [int(row["event_count"]) for row in rows]
    selected_counts = [int(row["selected_event_count"]) for row in rows]
    return {
        "rows": len(rows),
        "max_events": int(rows[0]["max_events"]) if rows else 0,
        "event_feature_count": int(rows[0]["event_feature_count"]) if rows else 0,
        "sampling_policy": str(rows[0]["sampling_policy"]) if rows else "",
        "event_count_mean": _mean(event_counts) if event_counts else 0.0,
        "event_count_max": max(event_counts) if event_counts else 0,
        "selected_event_count_mean": _mean(selected_counts) if selected_counts else 0.0,
        "truncated_intervals": sum(
            int(row["truncated_event_count"]) > 0 for row in rows
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
                "y_true": _evaluation_target_value(row, target),
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


def _preflight_dependencies(model_levels: list[str], *, device: str) -> None:
    if any(model in NEURAL_MODEL_LEVELS for model in model_levels):
        _import_torch_stack(device)
    elif model_levels:
        _import_sklearn_stack()


def _import_sklearn_stack() -> tuple[Any, Any]:
    try:
        import numpy as np
        from sklearn.linear_model import Ridge
    except ImportError as exc:
        raise RuntimeError(
            "Neural sequence gate Ridge controls require the baseline dependency extra. "
            "Run `uv sync --extra baseline` and retry."
        ) from exc
    return np, Ridge


def _import_torch_stack(device: str) -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "Neural sequence baselines require PyTorch. Install the neural dependency "
            "extra and retry."
        ) from exc
    if device != "cuda":
        raise RuntimeError(
            "Neural sequence baselines must run with --device cuda for milestone evidence."
        )
    if not torch.cuda.is_available():
        raise RuntimeError(
            "Neural sequence baselines require CUDA. GPU execution is mandatory for "
            "this gate; CPU fallback is intentionally disabled."
        )
    return torch


def _neural_environment_status(model_levels: list[str], *, device: str) -> dict[str, Any]:
    neural_models = [model for model in model_levels if model in NEURAL_MODEL_LEVELS]
    if neural_models:
        return {
            "neural_models_requested": neural_models,
            "neural_models_evaluated": True,
            "cuda_required": True,
            "torch_available": True,
            "cuda_available": True,
            "device": device,
            "evidence": f"CUDA neural sequence rows evaluated for {', '.join(neural_models)}.",
        }
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return {
            "neural_models_requested": [],
            "neural_models_evaluated": False,
            "cuda_required": True,
            "torch_available": False,
            "cuda_available": False,
            "device": device,
            "evidence": "Neural rows were not evaluated because PyTorch is unavailable.",
        }
    return {
        "neural_models_requested": [],
        "neural_models_evaluated": False,
        "cuda_required": True,
        "torch_available": True,
        "cuda_available": bool(torch.cuda.is_available()),
        "device": device,
        "evidence": "Neural rows were not requested in this run.",
    }


def _neural_environment_claim(neural_environment: dict[str, Any]) -> dict[str, Any]:
    if neural_environment.get("neural_models_evaluated"):
        return {
            "claim_area": "GPU neural execution",
            "status": "supported_for_diagnostics",
            "evidence": str(neural_environment.get("evidence", "CUDA neural rows evaluated.")),
        }
    return {
        "claim_area": "GPU neural execution",
        "status": "blocked",
        "evidence": str(
            neural_environment.get(
                "evidence",
                "Neural rows were not evaluated; neural evidence must run on CUDA.",
            )
        ),
    }


def _default_report_dir(out_path: Path) -> Path:
    return out_path.with_suffix("")
