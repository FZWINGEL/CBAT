"""Observed policy-contrast support and stability diagnostics.

This module builds matched observed-condition contrasts only. It does not train
models and does not estimate causal or counterfactual policy effects.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import POLICY_CONTRAST_REGISTRY_V1_SCHEMA, validate_table

SCHEMA_VERSION = "gate72.policy_contrast_registry.v1"
POLICY_RANKING_SCHEMA_VERSION = "gate73.policy_contrast_ordering_feasibility.v1"
DEFAULT_CONTRAST_FAMILIES = ("charge_c_rate", "temperature", "voltage_window", "profile")
POLICY_RANKING_TARGETS = ("delta_capacity_Ah_h", "capacity_Ah_kh")
POLICY_RANKING_HORIZONS = (2, 3)
POLICY_RANKING_MODELS = (
    "MH0_persistence",
    "MH1_prior_slope_linear",
    "MH2_ridge",
    "MH3_hist_gradient_boosting",
)
POLICY_RANKING_FEATURE_GROUPS = (
    "persistence",
    "prior_slope",
    "K0_prior_capacity",
    "K1_prior_state_time",
    "K2_nominal_condition",
    "K3_oracle_exposure_diagnostic",
)
POLICY_RANKING_PRIMARY_MODEL = ("MH3_hist_gradient_boosting", "K2_nominal_condition")
POLICY_RANKING_REFERENCE_MODELS = (
    ("MH0_persistence", "persistence"),
    ("MH1_prior_slope_linear", "prior_slope"),
    ("MH2_ridge", "K2_nominal_condition"),
)
ORACLE_POLICY_RANKING_FEATURE_GROUPS = {"K3_oracle_exposure_diagnostic"}
POLICY_RANKING_SIGN_EPSILON = 1e-12
CONTRAST_DEFINITIONS = {
    "charge_c_rate": {
        "varied_field": "nominal_charge_C_rate",
        "match_fields": (
            "aging_mode",
            "nominal_temperature_C",
            "voltage_window_family",
            "nominal_discharge_C_rate",
            "profile_label",
        ),
    },
    "temperature": {
        "varied_field": "nominal_temperature_C",
        "match_fields": (
            "aging_mode",
            "voltage_window_family",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "profile_label",
        ),
    },
    "voltage_window": {
        "varied_field": "voltage_window_family",
        "match_fields": (
            "aging_mode",
            "nominal_temperature_C",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
            "profile_label",
        ),
    },
    "profile": {
        "varied_field": "profile_label",
        "match_fields": (
            "aging_mode",
            "nominal_temperature_C",
            "voltage_window_family",
            "nominal_charge_C_rate",
            "nominal_discharge_C_rate",
        ),
    },
}
ENDPOINT_NAME = "capacity_loss_Ah"
SPLIT_COLUMNS = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)


def build_policy_contrast_registry(
    interval_table_path: Path,
    out_path: Path,
    *,
    contrast_families: list[str] | None = None,
) -> pa.Table:
    """Build a registry of observed matched condition-policy contrasts."""
    selected_families = _normalize_contrast_families(contrast_families)
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    if not interval_rows:
        raise ValueError("Interval table is empty.")

    summaries = _condition_summaries(interval_rows)
    rows: list[dict[str, Any]] = []
    for family in selected_families:
        rows.extend(_family_contrast_rows(family, summaries))
    rows = sorted(
        rows,
        key=lambda row: (
            str(row["contrast_family"]),
            str(row["match_key"]),
            int(row["arm_a_parameter_set"]),
            int(row["arm_b_parameter_set"]),
        ),
    )
    for index, row in enumerate(rows, start=1):
        row["contrast_id"] = f"PC{index:05d}_{row['contrast_family']}"
    if not rows:
        raise ValueError("No matched policy-contrast rows were generated.")

    table = pa.Table.from_pylist(rows, schema=POLICY_CONTRAST_REGISTRY_V1_SCHEMA)
    if not validate_table(table, POLICY_CONTRAST_REGISTRY_V1_SCHEMA):
        raise TypeError("Generated policy contrast registry does not match POLICY_CONTRAST_REGISTRY_V1_SCHEMA.")
    table = table.replace_schema_metadata(
        {
            b"schema_version": SCHEMA_VERSION.encode(),
            b"interval_table_path": str(interval_table_path).encode(),
            b"contrast_families": ",".join(selected_families).encode(),
            b"claim_scope": b"observed_support_diagnostics_only_no_policy_ranking",
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table


def write_policy_contrast_qa(
    contrast_registry_path: Path,
    interval_table_path: Path,
    out_path: Path,
    registry_out: Path,
    family_out: Path,
) -> dict[str, Any]:
    """Write support QA for the observed policy-contrast registry."""
    registry_rows = pq.read_table(contrast_registry_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    if not registry_rows:
        raise ValueError("Policy contrast registry is empty.")
    family_rows = policy_contrast_family_rows(registry_rows)
    _write_csv(registry_out, registry_rows)
    _write_csv(family_out, family_rows)

    warnings = []
    observed_families = {str(row["contrast_family"]) for row in registry_rows}
    for family in DEFAULT_CONTRAST_FAMILIES:
        if family not in observed_families:
            warnings.append(f"zero_contrasts_{family}")
    for row in family_rows:
        if int(row["triplet_supported_contrasts"]) == 0:
            warnings.append(f"zero_triplet_supported_{row['contrast_family']}")
    if not any(bool(row["has_triplet_support"]) for row in registry_rows):
        warnings.append("no_triplet_supported_contrasts")

    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "contrast_rows": len(registry_rows),
            "interval_rows": len(interval_rows),
            "contrast_families": sorted(observed_families),
            "triplet_supported_contrasts": sum(bool(row["has_triplet_support"]) for row in registry_rows),
            "parameter_sets": len(
                {
                    int(row["arm_a_parameter_set"])
                    for row in registry_rows
                }
                | {int(row["arm_b_parameter_set"]) for row in registry_rows}
            ),
        },
        "warnings": sorted(set(warnings)),
        "outputs": {
            "report": str(out_path),
            "registry": str(registry_out),
            "family": str(family_out),
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def evaluate_observed_policy_contrasts(
    contrast_registry_path: Path,
    interval_table_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Evaluate observed replicate-level sign stability for matched contrasts."""
    registry_rows = pq.read_table(contrast_registry_path).to_pylist()
    interval_rows = pq.read_table(interval_table_path).to_pylist()
    if not registry_rows:
        raise ValueError("Policy contrast registry is empty.")
    if not interval_rows:
        raise ValueError("Interval table is empty.")

    points_by_condition = _capacity_points_by_condition(interval_rows)
    stability_rows = observed_policy_stability_rows(registry_rows, points_by_condition)
    if not stability_rows:
        raise ValueError("No observed policy stability rows were generated.")

    by_family = policy_stability_family_rows(stability_rows)
    readiness = policy_claim_readiness_rows(registry_rows, stability_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "observed_policy_ranking_stability.csv", stability_rows)
    _write_csv(plots_dir / "policy_contrast_by_family.csv", by_family)
    _write_csv(plots_dir / "policy_claim_readiness.csv", readiness)
    _write_feasibility_markdown(out_dir / "policy_ranking_feasibility.md", registry_rows, stability_rows, by_family)
    _write_claim_readiness_markdown(out_dir / "policy_claim_readiness.md", readiness)

    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "row_counts": {
            "contrast_rows": len(registry_rows),
            "stability_rows": len(stability_rows),
            "families": sorted({str(row["contrast_family"]) for row in stability_rows}),
            "triplet_supported_contrasts": sum(bool(row["has_triplet_support"]) for row in registry_rows),
            "sign_stable_rows": sum(bool(row["sign_stable"]) for row in stability_rows),
        },
        "readiness": {str(row["claim_area"]): str(row["status"]) for row in readiness},
        "outputs": {
            "stability": str(out_dir / "observed_policy_ranking_stability.csv"),
            "feasibility": str(out_dir / "policy_ranking_feasibility.md"),
            "claim_readiness": str(out_dir / "policy_claim_readiness.md"),
        },
    }
    (out_dir / "observed_policy_contrast_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def evaluate_policy_ranking_feasibility(
    contrast_registry_path: Path,
    horizon_table_path: Path,
    predictions_path: Path,
    out_dir: Path,
    *,
    targets: list[str] | None = None,
    horizons: list[int] | None = None,
    model_levels: list[str] | None = None,
    feature_groups: list[str] | None = None,
    split_views: list[str] | None = None,
    min_replicate_rows_per_arm: int = 2,
    bootstrap_count: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    """Evaluate whether existing forecasts order supported observed contrasts.

    This is a report-only feasibility gate. It consumes existing out-of-fold
    multi-horizon capacity predictions and does not train, refit, or recommend
    a policy.
    """
    selected_targets = _normalize_selection(targets, POLICY_RANKING_TARGETS, "target")
    selected_horizons = _normalize_int_selection(horizons, POLICY_RANKING_HORIZONS, "horizon")
    selected_models = _normalize_selection(model_levels, POLICY_RANKING_MODELS, "model level")
    selected_features = _normalize_selection(feature_groups, POLICY_RANKING_FEATURE_GROUPS, "feature group")
    selected_splits = _normalize_selection(split_views, SPLIT_COLUMNS, "split view")
    if min_replicate_rows_per_arm < 1:
        raise ValueError("min_replicate_rows_per_arm must be at least 1.")
    if bootstrap_count <= 0:
        raise ValueError("bootstrap_count must be positive.")

    registry_rows = pq.read_table(contrast_registry_path).to_pylist()
    horizon_rows = pq.read_table(horizon_table_path).to_pylist()
    prediction_rows_raw = pq.read_table(predictions_path).to_pylist()
    if not registry_rows:
        raise ValueError("Policy contrast registry is empty.")
    if not horizon_rows:
        raise ValueError("Capacity horizon table is empty.")
    if not prediction_rows_raw:
        raise ValueError("Capacity horizon prediction table is empty.")

    horizon_by_key = _horizon_rows_by_key(horizon_rows)
    joined_rows = _joined_policy_prediction_rows(
        prediction_rows_raw,
        horizon_by_key,
        targets=set(selected_targets),
        horizons=set(selected_horizons),
        model_levels=set(selected_models),
        feature_groups=set(selected_features),
        split_views=set(selected_splits),
    )
    if not joined_rows:
        raise ValueError("No prediction rows matched the selected policy-ranking feasibility scope.")

    pairwise_rows = policy_ranking_pairwise_rows(
        registry_rows,
        joined_rows,
        min_replicate_rows_per_arm=min_replicate_rows_per_arm,
    )
    if not pairwise_rows:
        raise ValueError("No supported pairwise policy-ranking rows were generated.")

    by_family = policy_ranking_summary_rows(pairwise_rows)
    bootstrap_rows = policy_ranking_bootstrap_rows(pairwise_rows, bootstrap_count=bootstrap_count, seed=seed)
    readiness = policy_ranking_claim_readiness_rows(pairwise_rows, by_family, bootstrap_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "policy_ranking_pairwise_metrics.csv", pairwise_rows)
    _write_csv(out_dir / "policy_ranking_by_family.csv", by_family)
    _write_csv(out_dir / "policy_ranking_bootstrap.csv", bootstrap_rows)
    _write_csv(plots_dir / "policy_ranking_by_family.csv", by_family)
    _write_csv(plots_dir / "policy_ranking_bootstrap.csv", bootstrap_rows)
    _write_policy_ranking_claim_readiness_markdown(
        out_dir / "policy_ranking_claim_readiness.md",
        readiness,
        by_family,
        bootstrap_rows,
    )

    report = {
        "status": "passed",
        "schema_version": POLICY_RANKING_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "contrast_registry": str(contrast_registry_path),
            "horizon_table": str(horizon_table_path),
            "predictions": str(predictions_path),
        },
        "selection": {
            "targets": selected_targets,
            "horizons": selected_horizons,
            "model_levels": selected_models,
            "feature_groups": selected_features,
            "split_views": selected_splits,
            "min_replicate_rows_per_arm": min_replicate_rows_per_arm,
            "bootstrap_count": bootstrap_count,
            "seed": seed,
        },
        "row_counts": {
            "registry_rows": len(registry_rows),
            "triplet_supported_contrasts": sum(bool(row["has_triplet_support"]) for row in registry_rows),
            "horizon_rows": len(horizon_rows),
            "prediction_rows": len(prediction_rows_raw),
            "joined_prediction_rows": len(joined_rows),
            "pairwise_rows": len(pairwise_rows),
            "summary_rows": len(by_family),
            "bootstrap_rows": len(bootstrap_rows),
        },
        "readiness": {str(row["claim_area"]): str(row["status"]) for row in readiness},
        "outputs": {
            "pairwise_metrics": str(out_dir / "policy_ranking_pairwise_metrics.csv"),
            "by_family": str(out_dir / "policy_ranking_by_family.csv"),
            "bootstrap": str(out_dir / "policy_ranking_bootstrap.csv"),
            "claim_readiness": str(out_dir / "policy_ranking_claim_readiness.md"),
        },
        "claim_scope": "supported_observed_contrast_ordering_diagnostics_only_no_policy_recommendation",
    }
    (out_dir / "policy_ranking_feasibility_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def policy_contrast_family_rows(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize support by contrast family."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in registry_rows:
        grouped[str(row["contrast_family"])].append(row)
    output = []
    for family in sorted(grouped):
        rows = grouped[family]
        common = [int(row["common_checkup_count"]) for row in rows]
        output.append(
            {
                "contrast_family": family,
                "contrast_rows": len(rows),
                "triplet_supported_contrasts": sum(bool(row["has_triplet_support"]) for row in rows),
                "median_common_checkup_count": _median(common),
                "min_common_checkup_count": min(common) if common else 0,
                "max_common_checkup_count": max(common) if common else 0,
                "partial_support_contrasts": sum(str(row["support_quality"]) != "matched_triplets" for row in rows),
            }
        )
    return output


def observed_policy_stability_rows(
    registry_rows: list[dict[str, Any]],
    points_by_condition: dict[int, dict[int, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Compute observed capacity-loss sign stability for registry contrasts."""
    output: list[dict[str, Any]] = []
    for contrast in registry_rows:
        arm_a = int(contrast["arm_a_parameter_set"])
        arm_b = int(contrast["arm_b_parameter_set"])
        a_points = points_by_condition.get(arm_a, {})
        b_points = points_by_condition.get(arm_b, {})
        common_checkups = sorted((set(a_points) & set(b_points)) - {0})
        for checkup_k in common_checkups:
            a_values = [_as_float(row["capacity_loss_Ah"]) for row in a_points[checkup_k]]
            b_values = [_as_float(row["capacity_loss_Ah"]) for row in b_points[checkup_k]]
            a_values = [value for value in a_values if math.isfinite(value)]
            b_values = [value for value in b_values if math.isfinite(value)]
            if not a_values or not b_values:
                continue
            effect = _mean(b_values) - _mean(a_values)
            pairwise = [b_value - a_value for a_value in a_values for b_value in b_values]
            positive_fraction = sum(value > 0 for value in pairwise) / len(pairwise) if pairwise else math.nan
            sign_stable = (
                len(a_values) >= 2
                and len(b_values) >= 2
                and math.isfinite(positive_fraction)
                and (positive_fraction >= 0.75 or positive_fraction <= 0.25)
            )
            output.append(
                {
                    "contrast_id": contrast["contrast_id"],
                    "contrast_family": contrast["contrast_family"],
                    "endpoint": ENDPOINT_NAME,
                    "checkup_k": checkup_k,
                    "arm_a_parameter_set": arm_a,
                    "arm_b_parameter_set": arm_b,
                    "arm_a_value": contrast["arm_a_value"],
                    "arm_b_value": contrast["arm_b_value"],
                    "arm_a_replicates": len(a_values),
                    "arm_b_replicates": len(b_values),
                    "arm_a_mean": _mean(a_values),
                    "arm_b_mean": _mean(b_values),
                    "effect_b_minus_a": effect,
                    "pairwise_positive_fraction": positive_fraction,
                    "sign_label": _sign_label(effect),
                    "sign_stable": sign_stable,
                    "support_quality": contrast["support_quality"],
                    "claim_scope": "observed_support_diagnostic_only",
                }
            )
    return output


def policy_stability_family_rows(stability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize observed sign stability by contrast family."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in stability_rows:
        grouped[str(row["contrast_family"])].append(row)
    output = []
    for family in sorted(grouped):
        rows = grouped[family]
        effects = [_as_float(row["effect_b_minus_a"]) for row in rows]
        stable_count = sum(bool(row["sign_stable"]) for row in rows)
        output.append(
            {
                "contrast_family": family,
                "stability_rows": len(rows),
                "sign_stable_rows": stable_count,
                "sign_stable_fraction": stable_count / len(rows) if rows else math.nan,
                "median_abs_effect_b_minus_a": _median([abs(value) for value in effects]),
                "unique_contrasts": len({str(row["contrast_id"]) for row in rows}),
                "claim_scope": "observed_support_diagnostic_only",
            }
        )
    return output


def policy_ranking_pairwise_rows(
    registry_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    *,
    min_replicate_rows_per_arm: int = 2,
) -> list[dict[str, Any]]:
    """Build pairwise observed-vs-predicted contrast ordering rows."""
    groups_by_parameter = _prediction_groups_by_parameter(prediction_rows)
    output: list[dict[str, Any]] = []
    for contrast in registry_rows:
        if not bool(contrast.get("has_triplet_support")):
            continue
        arm_a = int(contrast["arm_a_parameter_set"])
        arm_b = int(contrast["arm_b_parameter_set"])
        arm_a_groups = groups_by_parameter.get(arm_a, {})
        arm_b_groups = groups_by_parameter.get(arm_b, {})
        for base_key in sorted(set(arm_a_groups) & set(arm_b_groups)):
            a_group = arm_a_groups[base_key]
            b_group = arm_b_groups[base_key]
            if len(a_group["rows"]) < min_replicate_rows_per_arm or len(b_group["rows"]) < min_replicate_rows_per_arm:
                continue
            split_name, target, horizon, model_level, feature_group, checkup_k, target_checkup_k = base_key
            a_observed = [_severity(row["y_true"], target) for row in a_group["rows"]]
            b_observed = [_severity(row["y_true"], target) for row in b_group["rows"]]
            a_predicted = [_severity(row["y_pred"], target) for row in a_group["rows"]]
            b_predicted = [_severity(row["y_pred"], target) for row in b_group["rows"]]
            if not all(math.isfinite(value) for value in (*a_observed, *b_observed, *a_predicted, *b_predicted)):
                continue
            observed_effect = _mean(b_observed) - _mean(a_observed)
            predicted_effect = _mean(b_predicted) - _mean(a_predicted)
            observed_sign = _effect_sign_label(observed_effect)
            predicted_sign = _effect_sign_label(predicted_effect)
            sign_evaluable = observed_sign != "tie" and predicted_sign != "tie"
            claim_scope = (
                "oracle_diagnostic_only"
                if feature_group in ORACLE_POLICY_RANKING_FEATURE_GROUPS
                else "prospective_supported_contrast_diagnostic"
            )
            output.append(
                {
                    "contrast_id": str(contrast["contrast_id"]),
                    "contrast_family": str(contrast["contrast_family"]),
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": horizon,
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "checkup_k": checkup_k,
                    "target_checkup_k": target_checkup_k,
                    "arm_a_parameter_set": arm_a,
                    "arm_b_parameter_set": arm_b,
                    "arm_a_value": contrast["arm_a_value"],
                    "arm_b_value": contrast["arm_b_value"],
                    "arm_a_prediction_rows": len(a_group["rows"]),
                    "arm_b_prediction_rows": len(b_group["rows"]),
                    "arm_a_replicates": len(a_group["replicate_ids"]),
                    "arm_b_replicates": len(b_group["replicate_ids"]),
                    "arm_a_heldout_folds": ",".join(str(value) for value in sorted(a_group["heldout_folds"])),
                    "arm_b_heldout_folds": ",".join(str(value) for value in sorted(b_group["heldout_folds"])),
                    "arm_a_observed_severity_mean": _mean(a_observed),
                    "arm_b_observed_severity_mean": _mean(b_observed),
                    "arm_a_predicted_severity_mean": _mean(a_predicted),
                    "arm_b_predicted_severity_mean": _mean(b_predicted),
                    "observed_effect_b_minus_a": observed_effect,
                    "predicted_effect_b_minus_a": predicted_effect,
                    "effect_abs_error": abs(predicted_effect - observed_effect),
                    "observed_sign_label": observed_sign,
                    "predicted_sign_label": predicted_sign,
                    "sign_evaluable": sign_evaluable,
                    "sign_correct": sign_evaluable and observed_sign == predicted_sign,
                    "claim_scope": claim_scope,
                }
            )
    return sorted(
        output,
        key=lambda row: (
            row["split_name"],
            row["target"],
            int(row["horizon_checkups"]),
            row["model_level"],
            row["feature_group"],
            row["contrast_family"],
            row["contrast_id"],
            int(row["checkup_k"]),
        ),
    )


def policy_ranking_summary_rows(pairwise_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize pairwise contrast-ordering metrics by family and all families."""
    grouped: dict[tuple[str, str, int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pairwise_rows:
        key = (
            str(row["split_name"]),
            str(row["target"]),
            int(row["horizon_checkups"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            str(row["contrast_family"]),
        )
        grouped[key].append(row)
        grouped[key[:-1] + ("all",)].append(row)

    output = []
    for (split_name, target, horizon, model_level, feature_group, family), rows in sorted(grouped.items()):
        evaluable = [row for row in rows if bool(row["sign_evaluable"])]
        correct = [row for row in evaluable if bool(row["sign_correct"])]
        errors = [_as_float(row["effect_abs_error"]) for row in rows]
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "model_level": model_level,
                "feature_group": feature_group,
                "contrast_family": family,
                "pairwise_rows": len(rows),
                "unique_contrasts": len({str(row["contrast_id"]) for row in rows}),
                "sign_evaluable_rows": len(evaluable),
                "sign_correct_rows": len(correct),
                "sign_accuracy": len(correct) / len(evaluable) if evaluable else math.nan,
                "mean_effect_abs_error": _mean([value for value in errors if math.isfinite(value)]),
                "median_effect_abs_error": _median([value for value in errors if math.isfinite(value)]),
                "observed_tie_rows": sum(str(row["observed_sign_label"]) == "tie" for row in rows),
                "predicted_tie_rows": sum(str(row["predicted_sign_label"]) == "tie" for row in rows),
                "claim_scope": (
                    "oracle_diagnostic_only"
                    if feature_group in ORACLE_POLICY_RANKING_FEATURE_GROUPS
                    else "prospective_supported_contrast_diagnostic"
                ),
            }
        )
    return output


def policy_ranking_bootstrap_rows(
    pairwise_rows: list[dict[str, Any]],
    *,
    bootstrap_count: int = 200,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Bootstrap HGB K2 sign-accuracy gains over reference rows by contrast ID."""
    output: list[dict[str, Any]] = []
    group_keys = sorted(
        {
            (str(row["split_name"]), str(row["target"]), int(row["horizon_checkups"]), family)
            for row in pairwise_rows
            for family in (str(row["contrast_family"]), "all")
        }
    )
    for split_name, target, horizon, family in group_keys:
        candidate_rows = _select_pairwise_rows(
            pairwise_rows,
            split_name=split_name,
            target=target,
            horizon=horizon,
            model_level=POLICY_RANKING_PRIMARY_MODEL[0],
            feature_group=POLICY_RANKING_PRIMARY_MODEL[1],
            contrast_family=family,
        )
        candidate_by_key = {_row_match_key(row): row for row in candidate_rows if bool(row["sign_evaluable"])}
        if not candidate_by_key:
            continue
        for reference_model, reference_feature in POLICY_RANKING_REFERENCE_MODELS:
            reference_rows = _select_pairwise_rows(
                pairwise_rows,
                split_name=split_name,
                target=target,
                horizon=horizon,
                model_level=reference_model,
                feature_group=reference_feature,
                contrast_family=family,
            )
            reference_by_key = {_row_match_key(row): row for row in reference_rows if bool(row["sign_evaluable"])}
            matched_keys = sorted(set(candidate_by_key) & set(reference_by_key))
            if not matched_keys:
                continue
            matched = [(candidate_by_key[key], reference_by_key[key]) for key in matched_keys]
            clusters: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
            for candidate, reference in matched:
                clusters[str(candidate["contrast_id"])].append((candidate, reference))
            gains = _bootstrap_accuracy_gains(clusters, bootstrap_count=bootstrap_count, seed=_stable_seed(seed, split_name, target, horizon, family, reference_model, reference_feature))
            candidate_accuracy = _accuracy([candidate for candidate, _ in matched])
            reference_accuracy = _accuracy([reference for _, reference in matched])
            output.append(
                {
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": horizon,
                    "contrast_family": family,
                    "candidate_model_level": POLICY_RANKING_PRIMARY_MODEL[0],
                    "candidate_feature_group": POLICY_RANKING_PRIMARY_MODEL[1],
                    "reference_model_level": reference_model,
                    "reference_feature_group": reference_feature,
                    "matched_rows": len(matched),
                    "matched_contrasts": len(clusters),
                    "candidate_sign_accuracy": candidate_accuracy,
                    "reference_sign_accuracy": reference_accuracy,
                    "accuracy_gain": candidate_accuracy - reference_accuracy,
                    "accuracy_gain_p05": _quantile(gains, 0.05),
                    "accuracy_gain_p50": _quantile(gains, 0.50),
                    "accuracy_gain_p95": _quantile(gains, 0.95),
                    "bootstrap_count": bootstrap_count,
                    "claim_scope": "prospective_supported_contrast_diagnostic",
                }
            )
    return output


def policy_ranking_claim_readiness_rows(
    pairwise_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    bootstrap_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return conservative claim-readiness rows for contrast-ordering feasibility."""
    primary_rows = [
        row
        for row in summary_rows
        if row["contrast_family"] == "all"
        and row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["model_level"] == POLICY_RANKING_PRIMARY_MODEL[0]
        and row["feature_group"] == POLICY_RANKING_PRIMARY_MODEL[1]
    ]
    reference_pass_rows = [
        row
        for row in bootstrap_rows
        if row["contrast_family"] == "all"
        and row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["reference_model_level"] in {"MH0_persistence", "MH1_prior_slope_linear"}
        and _as_float(row["accuracy_gain"]) > 0
        and _as_float(row["accuracy_gain_p05"]) > 0
    ]
    required_reference_rows = [
        row
        for row in bootstrap_rows
        if row["contrast_family"] == "all"
        and row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["reference_model_level"] in {"MH0_persistence", "MH1_prior_slope_linear"}
    ]
    families_passing = _families_with_primary_reference_gain(summary_rows)
    c_rate_rows = [
        row
        for row in primary_rows
        if row["split_name"] == "c_rate_holdout_fold" and _as_float(row["sign_accuracy"]) >= 0.5
    ]
    primary_accuracy = _mean([_as_float(row["sign_accuracy"]) for row in primary_rows])
    strict_reference_pass = bool(required_reference_rows) and len(reference_pass_rows) == len(required_reference_rows)
    c_rate_pass = len(c_rate_rows) >= 2
    family_pass = len(families_passing) >= 2

    if strict_reference_pass and family_pass and c_rate_pass:
        ordering_status = "supported_for_diagnostics"
    elif primary_rows and (reference_pass_rows or family_pass or c_rate_pass):
        ordering_status = "partially_supported"
    else:
        ordering_status = "not_supported"

    oracle_rows = [row for row in pairwise_rows if row["claim_scope"] == "oracle_diagnostic_only"]
    return [
        {
            "claim_area": "supported observed contrast ordering feasibility",
            "status": ordering_status,
            "evidence": (
                f"Primary HGB K2 mean sign accuracy {primary_accuracy:.3f}; "
                f"{len(reference_pass_rows)}/{len(required_reference_rows)} primary bootstrap reference checks pass; "
                f"{len(families_passing)} families pass reference comparison"
            ),
            "allowed_wording": "Existing prospective forecasts can be evaluated for supported observed contrast ordering diagnostics.",
            "forbidden_wording": "Policy recommendation, causal ranking, or deployment utility is supported.",
        },
        {
            "claim_area": "C-rate contrast ordering",
            "status": "supported_for_diagnostics" if c_rate_pass and ordering_status == "supported_for_diagnostics" else "diagnostic_only",
            "evidence": f"{len(c_rate_rows)} C-rate primary horizon rows have sign accuracy at or above 0.5.",
            "allowed_wording": "C-rate contrast ordering may be discussed only as a held-out diagnostic if the primary gate passes.",
            "forbidden_wording": "C-rate policy optimization is authorized.",
        },
        {
            "claim_area": "K3 oracle exposure ordering diagnostic",
            "status": "diagnostic_only" if oracle_rows else "not_supported",
            "evidence": f"{len(oracle_rows)} oracle K3 pairwise rows are labeled oracle_diagnostic_only.",
            "allowed_wording": "K3 can be used only to bound the value of future exposure information.",
            "forbidden_wording": "K3 is a prospective policy input.",
        },
        {
            "claim_area": "policy recommendation",
            "status": "blocked",
            "evidence": "The gate evaluates observed support and out-of-fold ordering only; it does not optimize interventions.",
            "allowed_wording": "No policy recommendation is made.",
            "forbidden_wording": "Choose, prescribe, or deploy an operating policy from these diagnostics.",
        },
        {
            "claim_area": "causal or same-cell counterfactual policy claims",
            "status": "blocked",
            "evidence": "Contrasts are between observed condition triplets, not randomized same-cell interventions.",
            "allowed_wording": "Effects are observed contrast diagnostics inside support.",
            "forbidden_wording": "Changing a policy would cause the estimated effect in the same cell.",
        },
        {
            "claim_area": "calibrated policy risk or utility",
            "status": "blocked",
            "evidence": "Capacity and threshold-warning calibration gates still block calibrated risk/uncertainty wording.",
            "allowed_wording": "Scores are diagnostic ordering outputs only.",
            "forbidden_wording": "The probabilities or utilities are calibrated for policy decisions.",
        },
    ]


def policy_claim_readiness_rows(
    registry_rows: list[dict[str, Any]],
    stability_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return conservative claim-readiness rows for policy-contrast support."""
    triplet_supported = sum(bool(row["has_triplet_support"]) for row in registry_rows)
    triplet_families = {
        str(row["contrast_family"])
        for row in registry_rows
        if bool(row["has_triplet_support"])
    }
    stable_fraction = (
        sum(bool(row["sign_stable"]) for row in stability_rows) / len(stability_rows)
        if stability_rows
        else 0.0
    )
    stable_families = {
        str(row["contrast_family"])
        for row in stability_rows
        if bool(row["sign_stable"])
    }
    if triplet_supported >= 10 and len(triplet_families) >= 2:
        support_status = "supported_for_diagnostics"
    elif triplet_supported >= 3:
        support_status = "partially_supported"
    else:
        support_status = "not_supported"

    if stable_fraction >= 0.6 and len(stable_families) >= 2:
        stability_status = "supported_for_diagnostics"
    elif stable_fraction >= 0.4:
        stability_status = "partially_supported"
    else:
        stability_status = "not_supported"

    next_gate_status = "possible_next_gate" if (
        support_status == "supported_for_diagnostics"
        and stability_status in {"supported_for_diagnostics", "partially_supported"}
    ) else "blocked"
    return [
        {
            "claim_area": "matched observed policy-contrast support",
            "status": support_status,
            "evidence": f"{triplet_supported} triplet-supported contrasts across {len(triplet_families)} families",
            "allowed_wording": "Observed matched policy contrasts are available for diagnostics.",
            "forbidden_wording": "Policy ranking or intervention effects are supported.",
        },
        {
            "claim_area": "observed contrast sign stability",
            "status": stability_status,
            "evidence": f"{stable_fraction:.3f} sign-stable capacity-loss rows across {len(stable_families)} families",
            "allowed_wording": "Observed degradation ordering can be summarized for matched contrasts.",
            "forbidden_wording": "The ordering is causal, counterfactual, or deployment-ready.",
        },
        {
            "claim_area": "future policy-ranking baseline readiness",
            "status": next_gate_status,
            "evidence": "Requires support/stability plus grouped uncertainty before any ranking baseline.",
            "allowed_wording": "A future ranking feasibility gate may be considered if support is sufficient.",
            "forbidden_wording": "A policy-ranking model is authorized.",
        },
        {
            "claim_area": "causal or same-cell counterfactual policy claims",
            "status": "blocked",
            "evidence": "Only observed matched contrasts are evaluated; no randomized policy intervention exists.",
            "allowed_wording": "No causal policy claim is made.",
            "forbidden_wording": "Changing a policy would cause the observed effect.",
        },
    ]


def _family_contrast_rows(
    family: str,
    summaries: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    definition = CONTRAST_DEFINITIONS[family]
    varied_field = str(definition["varied_field"])
    match_fields = tuple(definition["match_fields"])
    grouped: dict[tuple[tuple[str, str], ...], list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries.values():
        key = tuple((field, _stringify_value(summary.get(field))) for field in match_fields)
        grouped[key].append(summary)

    output: list[dict[str, Any]] = []
    for match_key, group in grouped.items():
        candidates = sorted(
            group,
            key=lambda row: (_sort_value(row.get(varied_field)), int(row["parameter_set"])),
        )
        for left_index, left in enumerate(candidates):
            for right in candidates[left_index + 1 :]:
                if _stringify_value(left.get(varied_field)) == _stringify_value(right.get(varied_field)):
                    continue
                common_checkups = sorted(set(left["checkups"]) & set(right["checkups"]))
                support_quality = _support_quality(left, right, common_checkups)
                output.append(
                    {
                        "contrast_id": "pending",
                        "contrast_family": family,
                        "varied_field": varied_field,
                        "match_key": json.dumps(dict(match_key), sort_keys=True),
                        "arm_a_parameter_set": int(left["parameter_set"]),
                        "arm_b_parameter_set": int(right["parameter_set"]),
                        "arm_a_value": _stringify_value(left.get(varied_field)),
                        "arm_b_value": _stringify_value(right.get(varied_field)),
                        "arm_a_cells": int(left["cells"]),
                        "arm_b_cells": int(right["cells"]),
                        "arm_a_interval_rows": int(left["interval_rows"]),
                        "arm_b_interval_rows": int(right["interval_rows"]),
                        "arm_a_min_checkup_k": int(left["min_checkup_k"]),
                        "arm_a_max_checkup_k": int(left["max_checkup_k"]),
                        "arm_b_min_checkup_k": int(right["min_checkup_k"]),
                        "arm_b_max_checkup_k": int(right["max_checkup_k"]),
                        "common_checkup_count": len(common_checkups),
                        "has_triplet_support": support_quality == "matched_triplets",
                        "support_quality": support_quality,
                        "schema_version": SCHEMA_VERSION,
                    }
                )
    return output


def _condition_summaries(interval_rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in interval_rows:
        grouped[int(row["parameter_set"])].append(row)
    summaries = {}
    for parameter_set, rows in grouped.items():
        cells = {str(row["cell_id"]) for row in rows}
        checkups = {int(row["checkup_k"]) for row in rows} | {int(row["checkup_k_next"]) for row in rows}
        first = sorted(rows, key=lambda row: (str(row["cell_id"]), int(row["checkup_k"])))[0]
        summary = {
            "parameter_set": parameter_set,
            "cells": len(cells),
            "interval_rows": len(rows),
            "checkups": checkups,
            "min_checkup_k": min(checkups),
            "max_checkup_k": max(checkups),
        }
        for field in _metadata_fields():
            summary[field] = first.get(field)
        summaries[parameter_set] = summary
    return summaries


def _capacity_points_by_condition(
    interval_rows: list[dict[str, Any]],
) -> dict[int, dict[int, list[dict[str, Any]]]]:
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in interval_rows:
        by_cell[str(row["cell_id"])].append(row)

    output: dict[int, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for cell_id, rows in by_cell.items():
        rows = sorted(rows, key=lambda row: int(row["checkup_k"]))
        points: dict[int, dict[str, Any]] = {}
        parameter_set = int(rows[0]["parameter_set"])
        replicate_id = int(rows[0]["replicate_id"])
        for row in rows:
            points[int(row["checkup_k"])] = {
                "cell_id": cell_id,
                "parameter_set": parameter_set,
                "replicate_id": replicate_id,
                "checkup_k": int(row["checkup_k"]),
                "capacity_Ah": _as_float(row["capacity_Ah_k"]),
            }
            points[int(row["checkup_k_next"])] = {
                "cell_id": cell_id,
                "parameter_set": parameter_set,
                "replicate_id": replicate_id,
                "checkup_k": int(row["checkup_k_next"]),
                "capacity_Ah": _as_float(row["capacity_Ah_k1"]),
            }
        if not points:
            continue
        initial_k = min(points)
        initial_capacity = _as_float(points[initial_k]["capacity_Ah"])
        if not math.isfinite(initial_capacity):
            continue
        for checkup_k, point in points.items():
            capacity = _as_float(point["capacity_Ah"])
            if not math.isfinite(capacity):
                continue
            output[parameter_set][checkup_k].append(
                point
                | {
                    "initial_capacity_Ah": initial_capacity,
                    "capacity_loss_Ah": initial_capacity - capacity,
                }
            )
    return {key: dict(value) for key, value in output.items()}


def _support_quality(
    left: dict[str, Any],
    right: dict[str, Any],
    common_checkups: list[int],
) -> str:
    flags = []
    if int(left["cells"]) >= 3 and int(right["cells"]) >= 3:
        flags.append("matched_triplets")
    elif int(left["cells"]) >= 2 and int(right["cells"]) >= 2:
        flags.append("partial_replicates")
    else:
        flags.append("insufficient_replicates")
    if len(common_checkups) < 3:
        flags.append("insufficient_common_horizon")
    return flags[0] if len(flags) == 1 else ";".join(flags)


def _write_feasibility_markdown(
    out_path: Path,
    registry_rows: list[dict[str, Any]],
    stability_rows: list[dict[str, Any]],
    by_family: list[dict[str, Any]],
) -> None:
    triplet_supported = sum(bool(row["has_triplet_support"]) for row in registry_rows)
    stable_rows = sum(bool(row["sign_stable"]) for row in stability_rows)
    lines = [
        "# Observed Policy-Contrast Feasibility",
        "",
        "This report evaluates matched observed condition contrasts only. It does not train a model, rank policies, or estimate causal/counterfactual effects.",
        "",
        "## Summary",
        "",
        f"- Contrast rows: {len(registry_rows)}",
        f"- Triplet-supported contrasts: {triplet_supported}",
        f"- Observed stability rows: {len(stability_rows)}",
        f"- Sign-stable rows: {stable_rows}",
        "",
        "## Family Summary",
        "",
        "| Family | Contrasts | Triplet-supported | Stability rows | Sign-stable fraction |",
        "|---|---:|---:|---:|---:|",
    ]
    stability_by_family = {str(row["contrast_family"]): row for row in by_family}
    for row in policy_contrast_family_rows(registry_rows):
        stability = stability_by_family.get(str(row["contrast_family"]), {})
        lines.append(
            "| {family} | {contrasts} | {triplets} | {stability_rows} | {stable_fraction} |".format(
                family=row["contrast_family"],
                contrasts=row["contrast_rows"],
                triplets=row["triplet_supported_contrasts"],
                stability_rows=stability.get("stability_rows", 0),
                stable_fraction=_format_float(stability.get("sign_stable_fraction")),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Supported wording is limited to observed support and observed degradation-order diagnostics.",
            "- Policy ranking, policy recommendation, same-cell counterfactual, and causal intervention claims remain blocked.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_claim_readiness_markdown(out_path: Path, readiness_rows: list[dict[str, str]]) -> None:
    lines = [
        "# Policy Contrast Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in readiness_rows:
        lines.append(
            "| {area} | {status} | {evidence} | {allowed} | {forbidden} |".format(
                area=row["claim_area"],
                status=row["status"],
                evidence=row["evidence"],
                allowed=row["allowed_wording"],
                forbidden=row["forbidden_wording"],
            )
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_policy_ranking_claim_readiness_markdown(
    out_path: Path,
    readiness_rows: list[dict[str, str]],
    summary_rows: list[dict[str, Any]],
    bootstrap_rows: list[dict[str, Any]],
) -> None:
    primary_summary = [
        row
        for row in summary_rows
        if row["contrast_family"] == "all"
        and row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["model_level"] == POLICY_RANKING_PRIMARY_MODEL[0]
        and row["feature_group"] == POLICY_RANKING_PRIMARY_MODEL[1]
    ]
    primary_bootstrap = [
        row
        for row in bootstrap_rows
        if row["contrast_family"] == "all"
        and row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["reference_model_level"] in {"MH0_persistence", "MH1_prior_slope_linear"}
    ]
    lines = [
        "# Supported Contrast Ordering Claim Readiness",
        "",
        "This report evaluates existing out-of-fold multi-horizon predictions on matched observed condition contrasts. It does not train a model, optimize policies, estimate causal effects, or create same-cell counterfactuals.",
        "",
        "## Claim Readiness",
        "",
        "| Claim area | Status | Evidence | Allowed wording | Forbidden wording |",
        "|---|---|---|---|---|",
    ]
    for row in readiness_rows:
        lines.append(
            "| {area} | {status} | {evidence} | {allowed} | {forbidden} |".format(
                area=row["claim_area"],
                status=row["status"],
                evidence=row["evidence"],
                allowed=row["allowed_wording"],
                forbidden=row["forbidden_wording"],
            )
        )
    lines.extend(
        [
            "",
            "## Primary HGB K2 Rows",
            "",
            "| Split | Horizon | Rows | Sign accuracy | Mean effect abs error |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in primary_summary:
        lines.append(
            "| {split} | {horizon} | {rows} | {accuracy} | {error} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                rows=row["pairwise_rows"],
                accuracy=_format_float(row["sign_accuracy"]),
                error=_format_float(row["mean_effect_abs_error"]),
            )
        )
    lines.extend(
        [
            "",
            "## Primary Bootstrap Reference Checks",
            "",
            "| Split | Horizon | Reference | Gain | Gain p05 | Matched contrasts |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for row in primary_bootstrap:
        lines.append(
            "| {split} | {horizon} | {reference} / {feature} | {gain} | {p05} | {contrasts} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                reference=row["reference_model_level"],
                feature=row["reference_feature_group"],
                gain=_format_float(row["accuracy_gain"]),
                p05=_format_float(row["accuracy_gain_p05"]),
                contrasts=row["matched_contrasts"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Supported wording is limited to observed-support contrast-ordering diagnostics.",
            "- K3 oracle rows are diagnostic only because they include future exposure over the forecast horizon.",
            "- Policy recommendations, causal claims, same-cell counterfactual claims, calibrated risk, CBAT, and broad architecture claims remain blocked.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _normalize_contrast_families(values: list[str] | None) -> list[str]:
    raw_values = list(DEFAULT_CONTRAST_FAMILIES if values is None else values)
    selected = []
    seen = set()
    for value in raw_values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        selected.append(item)
        seen.add(item)
    if not selected:
        raise ValueError("At least one contrast family must be selected.")
    unknown = sorted(set(selected) - set(DEFAULT_CONTRAST_FAMILIES))
    if unknown:
        raise ValueError(f"Unknown contrast families: {unknown}. Allowed: {list(DEFAULT_CONTRAST_FAMILIES)}")
    return selected


def _normalize_selection(values: list[str] | None, allowed: tuple[str, ...], label: str) -> list[str]:
    raw_values = list(allowed if values is None else values)
    selected = []
    seen = set()
    for value in raw_values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        selected.append(item)
        seen.add(item)
    if not selected:
        raise ValueError(f"At least one {label} must be selected.")
    unknown = sorted(set(selected) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}s: {unknown}. Allowed: {list(allowed)}")
    return selected


def _normalize_int_selection(values: list[int] | None, allowed: tuple[int, ...], label: str) -> list[int]:
    raw_values = list(allowed if values is None else values)
    selected = []
    seen = set()
    for value in raw_values:
        item = int(value)
        if item in seen:
            continue
        selected.append(item)
        seen.add(item)
    if not selected:
        raise ValueError(f"At least one {label} must be selected.")
    unknown = sorted(set(selected) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {label}s: {unknown}. Allowed: {list(allowed)}")
    return selected


def _horizon_rows_by_key(rows: list[dict[str, Any]]) -> dict[tuple[str, int, int, int, int, int], dict[str, Any]]:
    output = {}
    for row in rows:
        key = _horizon_prediction_key(row)
        output[key] = row
    return output


def _joined_policy_prediction_rows(
    prediction_rows: list[dict[str, Any]],
    horizon_by_key: dict[tuple[str, int, int, int, int, int], dict[str, Any]],
    *,
    targets: set[str],
    horizons: set[int],
    model_levels: set[str],
    feature_groups: set[str],
    split_views: set[str],
) -> list[dict[str, Any]]:
    output = []
    for prediction in prediction_rows:
        target = str(prediction["target"])
        horizon = int(prediction["horizon_checkups"])
        if (
            target not in targets
            or horizon not in horizons
            or str(prediction["model_level"]) not in model_levels
            or str(prediction["feature_group"]) not in feature_groups
            or str(prediction["split_name"]) not in split_views
        ):
            continue
        horizon_row = horizon_by_key.get(_horizon_prediction_key(prediction))
        if horizon_row is None:
            continue
        observed = _as_float(horizon_row.get(target))
        predicted_y_true = _as_float(prediction.get("y_true"))
        if math.isfinite(observed) and math.isfinite(predicted_y_true) and abs(observed - predicted_y_true) > 1e-8:
            raise ValueError(
                "Prediction y_true does not match capacity horizon table for "
                f"{prediction['cell_id']} k={prediction['checkup_k']} h={horizon} target={target}."
            )
        output.append(
            prediction
            | {
                "y_true": observed,
                "parameter_set": int(horizon_row["parameter_set"]),
                "replicate_id": int(horizon_row["replicate_id"]),
                "checkup_k": int(horizon_row["checkup_k"]),
                "target_checkup_k": int(horizon_row["target_checkup_k"]),
                "horizon_checkups": horizon,
            }
        )
    return output


def _horizon_prediction_key(row: dict[str, Any]) -> tuple[str, int, int, int, int, int]:
    return (
        str(row["cell_id"]),
        int(row["parameter_set"]),
        int(row["replicate_id"]),
        int(row["checkup_k"]),
        int(row["target_checkup_k"]),
        int(row["horizon_checkups"]),
    )


def _prediction_groups_by_parameter(
    prediction_rows: list[dict[str, Any]],
) -> dict[int, dict[tuple[str, str, int, str, str, int, int], dict[str, Any]]]:
    groups: dict[int, dict[tuple[str, str, int, str, str, int, int], dict[str, Any]]] = defaultdict(dict)
    for row in prediction_rows:
        parameter_set = int(row["parameter_set"])
        base_key = (
            str(row["split_name"]),
            str(row["target"]),
            int(row["horizon_checkups"]),
            str(row["model_level"]),
            str(row["feature_group"]),
            int(row["checkup_k"]),
            int(row["target_checkup_k"]),
        )
        group = groups[parameter_set].setdefault(
            base_key,
            {"rows": [], "replicate_ids": set(), "heldout_folds": set()},
        )
        group["rows"].append(row)
        group["replicate_ids"].add(int(row["replicate_id"]))
        group["heldout_folds"].add(int(row["heldout_fold"]))
    return groups


def _severity(value: Any, target: str) -> float:
    number = _as_float(value)
    if target in {"delta_capacity_Ah_h", "capacity_Ah_kh"}:
        return -number
    raise ValueError(f"Unknown policy-ranking target: {target}")


def _effect_sign_label(effect: float) -> str:
    if effect > POLICY_RANKING_SIGN_EPSILON:
        return "arm_b_more_degraded"
    if effect < -POLICY_RANKING_SIGN_EPSILON:
        return "arm_a_more_degraded"
    return "tie"


def _select_pairwise_rows(
    rows: list[dict[str, Any]],
    *,
    split_name: str,
    target: str,
    horizon: int,
    model_level: str,
    feature_group: str,
    contrast_family: str,
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["split_name"] == split_name
        and row["target"] == target
        and int(row["horizon_checkups"]) == horizon
        and row["model_level"] == model_level
        and row["feature_group"] == feature_group
        and (contrast_family == "all" or row["contrast_family"] == contrast_family)
    ]


def _row_match_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return (str(row["contrast_id"]), int(row["checkup_k"]), int(row["target_checkup_k"]))


def _accuracy(rows: list[dict[str, Any]]) -> float:
    evaluable = [row for row in rows if bool(row["sign_evaluable"])]
    if not evaluable:
        return math.nan
    return sum(bool(row["sign_correct"]) for row in evaluable) / len(evaluable)


def _bootstrap_accuracy_gains(
    clusters: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]],
    *,
    bootstrap_count: int,
    seed: int,
) -> list[float]:
    cluster_ids = sorted(clusters)
    if not cluster_ids:
        return []
    rng = random.Random(seed)
    gains = []
    for _ in range(bootstrap_count):
        candidate_rows = []
        reference_rows = []
        for _ in cluster_ids:
            contrast_id = rng.choice(cluster_ids)
            for candidate, reference in clusters[contrast_id]:
                candidate_rows.append(candidate)
                reference_rows.append(reference)
        gains.append(_accuracy(candidate_rows) - _accuracy(reference_rows))
    return gains


def _stable_seed(seed: int, *values: object) -> int:
    text = "|".join(str(value) for value in (seed, *values))
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _quantile(values: list[float], probability: float) -> float:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return math.nan
    if len(finite) == 1:
        return finite[0]
    position = (len(finite) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return finite[int(position)]
    fraction = position - lower
    return finite[lower] * (1 - fraction) + finite[upper] * fraction


def _families_with_primary_reference_gain(summary_rows: list[dict[str, Any]]) -> set[str]:
    primary = {
        (
            row["split_name"],
            int(row["horizon_checkups"]),
            row["contrast_family"],
        ): _as_float(row["sign_accuracy"])
        for row in summary_rows
        if row["target"] == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and row["model_level"] == POLICY_RANKING_PRIMARY_MODEL[0]
        and row["feature_group"] == POLICY_RANKING_PRIMARY_MODEL[1]
        and row["contrast_family"] != "all"
    }
    reference_by_key: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    for row in summary_rows:
        if (
            row["target"] == "delta_capacity_Ah_h"
            and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
            and row["contrast_family"] != "all"
            and (row["model_level"], row["feature_group"]) in POLICY_RANKING_REFERENCE_MODELS[:2]
        ):
            reference_by_key[
                (
                    row["split_name"],
                    int(row["horizon_checkups"]),
                    row["contrast_family"],
                )
            ].append(_as_float(row["sign_accuracy"]))
    passing = set()
    for key, accuracy in primary.items():
        references = [value for value in reference_by_key.get(key, []) if math.isfinite(value)]
        if math.isfinite(accuracy) and references and accuracy > max(references):
            passing.add(str(key[2]))
    return passing


def _metadata_fields() -> tuple[str, ...]:
    fields = set()
    for definition in CONTRAST_DEFINITIONS.values():
        fields.add(str(definition["varied_field"]))
        fields.update(str(field) for field in definition["match_fields"])
    fields.update(SPLIT_COLUMNS)
    return tuple(sorted(fields))


def _sort_value(value: Any) -> tuple[int, float | str]:
    number = _as_float(value)
    if math.isfinite(number):
        return (0, number)
    return (1, _stringify_value(value))


def _stringify_value(value: Any) -> str:
    if value is None:
        return "missing"
    number = _as_float(value)
    if math.isfinite(number):
        return f"{number:.6g}"
    text = str(value).strip()
    return text if text else "missing"


def _as_float(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def _median(values: list[float | int]) -> float:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return math.nan
    mid = len(finite) // 2
    if len(finite) % 2:
        return finite[mid]
    return (finite[mid - 1] + finite[mid]) / 2.0


def _sign_label(effect: float) -> str:
    if effect > 0:
        return "arm_b_more_degraded"
    if effect < 0:
        return "arm_a_more_degraded"
    return "tie"


def _format_float(value: Any) -> str:
    number = _as_float(value)
    return "nan" if not math.isfinite(number) else f"{number:.6g}"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
