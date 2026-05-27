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
POLICY_RANKING_FORENSICS_SCHEMA_VERSION = "gate74.policy_contrast_ordering_forensics.v1"
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
POLICY_RANKING_EFFECT_THRESHOLDS_AH = (0.0, 0.005, 0.01, 0.02, 0.05)
POLICY_RANKING_EFFECT_BINS_AH = (
    ("tiny_lt_0.01Ah", 0.0, 0.01),
    ("small_0.01_to_0.02Ah", 0.01, 0.02),
    ("medium_0.02_to_0.05Ah", 0.02, 0.05),
    ("large_ge_0.05Ah", 0.05, math.inf),
)
POLICY_RANKING_TOPK_VALUES = (3, 5)
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


def diagnose_policy_ranking_feasibility(
    pairwise_metrics_path: Path,
    by_family_path: Path,
    bootstrap_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Diagnose why supported contrast-ordering failed strict readiness.

    This is a report-only forensics step over existing Milestone 7.3 CSVs. It
    does not train models, create features, or authorize policy recommendation.
    """
    pairwise_rows = _read_csv_rows(pairwise_metrics_path)
    by_family_rows = _read_csv_rows(by_family_path)
    bootstrap_rows = _read_csv_rows(bootstrap_path)
    if not pairwise_rows:
        raise ValueError("Policy-ranking pairwise metrics are empty.")
    if not by_family_rows:
        raise ValueError("Policy-ranking by-family summary is empty.")
    if not bootstrap_rows:
        raise ValueError("Policy-ranking bootstrap summary is empty.")

    effect_threshold_rows = policy_ranking_effect_threshold_rows(pairwise_rows)
    rank_rows = policy_ranking_rank_correlation_rows(pairwise_rows)
    topk_rows = policy_ranking_topk_regret_rows(pairwise_rows)
    failure_bin_rows = policy_ranking_hgb_vs_prior_failure_bin_rows(pairwise_rows)
    readiness_rows = policy_ranking_failure_forensics_claim_readiness_rows(
        pairwise_rows=pairwise_rows,
        by_family_rows=by_family_rows,
        bootstrap_rows=bootstrap_rows,
        effect_threshold_rows=effect_threshold_rows,
        rank_rows=rank_rows,
        failure_bin_rows=failure_bin_rows,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(plots_dir / "effect_size_threshold_sign_accuracy.csv", effect_threshold_rows)
    _write_csv(plots_dir / "rank_correlation_diagnostics.csv", rank_rows)
    _write_csv(plots_dir / "topk_regret_diagnostics.csv", topk_rows)
    _write_csv(plots_dir / "hgb_vs_prior_failure_bins.csv", failure_bin_rows)
    _write_csv(plots_dir / "policy_ranking_failure_claim_readiness.csv", readiness_rows)
    _write_policy_ranking_failure_forensics_markdown(
        out_dir / "policy_ranking_failure_forensics.md",
        readiness_rows=readiness_rows,
        failure_bin_rows=failure_bin_rows,
        effect_threshold_rows=effect_threshold_rows,
        rank_rows=rank_rows,
        topk_rows=topk_rows,
        bootstrap_rows=bootstrap_rows,
    )
    _write_policy_ranking_failure_claim_readiness_markdown(
        out_dir / "policy_ranking_failure_claim_readiness.md",
        readiness_rows,
    )

    prospective_rows = _prospective_policy_pairwise_rows(pairwise_rows)
    oracle_rows = [row for row in pairwise_rows if _is_oracle_policy_row(row)]
    report = {
        "status": "passed",
        "schema_version": POLICY_RANKING_FORENSICS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "inputs": {
            "pairwise_metrics": str(pairwise_metrics_path),
            "by_family": str(by_family_path),
            "bootstrap": str(bootstrap_path),
        },
        "row_counts": {
            "pairwise_rows": len(pairwise_rows),
            "prospective_pairwise_rows": len(prospective_rows),
            "oracle_pairwise_rows_excluded_from_readiness": len(oracle_rows),
            "by_family_rows": len(by_family_rows),
            "bootstrap_rows": len(bootstrap_rows),
            "effect_threshold_rows": len(effect_threshold_rows),
            "rank_correlation_rows": len(rank_rows),
            "topk_regret_rows": len(topk_rows),
            "hgb_vs_prior_failure_bin_rows": len(failure_bin_rows),
        },
        "readiness": {str(row["claim_area"]): str(row["status"]) for row in readiness_rows},
        "outputs": {
            "report_markdown": str(out_dir / "policy_ranking_failure_forensics.md"),
            "claim_readiness": str(out_dir / "policy_ranking_failure_claim_readiness.md"),
            "effect_size_threshold_sign_accuracy": str(
                plots_dir / "effect_size_threshold_sign_accuracy.csv"
            ),
            "rank_correlation_diagnostics": str(plots_dir / "rank_correlation_diagnostics.csv"),
            "topk_regret_diagnostics": str(plots_dir / "topk_regret_diagnostics.csv"),
            "hgb_vs_prior_failure_bins": str(plots_dir / "hgb_vs_prior_failure_bins.csv"),
        },
        "claim_scope": "failure_forensics_only_no_policy_recommendation_no_causal_claim",
    }
    (out_dir / "policy_ranking_failure_forensics_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def policy_ranking_effect_threshold_rows(
    pairwise_rows: list[dict[str, Any]],
    *,
    thresholds: tuple[float, ...] = POLICY_RANKING_EFFECT_THRESHOLDS_AH,
) -> list[dict[str, Any]]:
    """Summarize sign accuracy after dropping near-zero observed contrasts."""
    prospective_rows = _prospective_policy_pairwise_rows(pairwise_rows)
    grouped: dict[tuple[str, str, int, str, str, str, str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in prospective_rows:
        observed_abs = abs(_as_float(row.get("observed_effect_b_minus_a")))
        if not math.isfinite(observed_abs):
            continue
        for threshold in thresholds:
            if observed_abs < threshold:
                continue
            threshold_label = _effect_threshold_label(threshold)
            for family in (str(row["contrast_family"]), "all"):
                key = (
                    str(row["split_name"]),
                    str(row["target"]),
                    int(row["horizon_checkups"]),
                    str(row["model_level"]),
                    str(row["feature_group"]),
                    family,
                    threshold_label,
                    float(threshold),
                )
                grouped[key].append(row)

    output = []
    for (
        split_name,
        target,
        horizon,
        model_level,
        feature_group,
        family,
        threshold_label,
        threshold,
    ), rows in sorted(grouped.items()):
        evaluable = [row for row in rows if _as_bool(row.get("sign_evaluable"))]
        correct = [row for row in evaluable if _as_bool(row.get("sign_correct"))]
        effects = [abs(_as_float(row.get("observed_effect_b_minus_a"))) for row in rows]
        errors = [_as_float(row.get("effect_abs_error")) for row in rows]
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "model_level": model_level,
                "feature_group": feature_group,
                "contrast_family": family,
                "effect_threshold_label": threshold_label,
                "effect_threshold_Ah": threshold,
                "pairwise_rows": len(rows),
                "unique_contrasts": len({str(row["contrast_id"]) for row in rows}),
                "sign_evaluable_rows": len(evaluable),
                "sign_correct_rows": len(correct),
                "sign_accuracy": len(correct) / len(evaluable) if evaluable else math.nan,
                "median_abs_observed_effect_Ah": _median([value for value in effects if math.isfinite(value)]),
                "mean_effect_abs_error": _mean([value for value in errors if math.isfinite(value)]),
                "claim_scope": "prospective_supported_contrast_diagnostic",
            }
        )
    return output


def policy_ranking_hgb_vs_prior_failure_bin_rows(
    pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare HGB K2 against prior slope by observed-effect size bins."""
    primary_by_key: dict[tuple[str, str, int, str, str, int, int], dict[str, Any]] = {}
    prior_by_key: dict[tuple[str, str, int, str, str, int, int], dict[str, Any]] = {}
    for row in _prospective_policy_pairwise_rows(pairwise_rows):
        key = _forensics_pairwise_match_key(row)
        model_key = (str(row["model_level"]), str(row["feature_group"]))
        if model_key == POLICY_RANKING_PRIMARY_MODEL:
            primary_by_key[key] = row
        elif model_key == ("MH1_prior_slope_linear", "prior_slope"):
            prior_by_key[key] = row

    grouped: dict[tuple[str, str, int, str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for key in sorted(set(primary_by_key) & set(prior_by_key)):
        primary = primary_by_key[key]
        prior = prior_by_key[key]
        observed_abs = abs(_as_float(primary.get("observed_effect_b_minus_a")))
        if not math.isfinite(observed_abs):
            continue
        effect_bin = _effect_bin_label(observed_abs)
        for family in (str(primary["contrast_family"]), "all"):
            grouped[
                (
                    str(primary["split_name"]),
                    str(primary["target"]),
                    int(primary["horizon_checkups"]),
                    family,
                    effect_bin,
                )
            ].append((primary, prior))

    output = []
    for (split_name, target, horizon, family, effect_bin), rows in sorted(grouped.items()):
        hgb_rows = [primary for primary, _ in rows]
        prior_rows = [prior for _, prior in rows]
        hgb_accuracy = _accuracy_forensics(hgb_rows)
        prior_accuracy = _accuracy_forensics(prior_rows)
        hgb_errors = [_as_float(row.get("effect_abs_error")) for row in hgb_rows]
        prior_errors = [_as_float(row.get("effect_abs_error")) for row in prior_rows]
        hgb_mean_error = _mean([value for value in hgb_errors if math.isfinite(value)])
        prior_mean_error = _mean([value for value in prior_errors if math.isfinite(value)])
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "contrast_family": family,
                "effect_bin": effect_bin,
                "matched_rows": len(rows),
                "matched_contrasts": len({str(primary["contrast_id"]) for primary, _ in rows}),
                "hgb_sign_accuracy": hgb_accuracy,
                "prior_slope_sign_accuracy": prior_accuracy,
                "sign_accuracy_gain_vs_prior": hgb_accuracy - prior_accuracy
                if math.isfinite(hgb_accuracy) and math.isfinite(prior_accuracy)
                else math.nan,
                "hgb_mean_effect_abs_error": hgb_mean_error,
                "prior_slope_mean_effect_abs_error": prior_mean_error,
                "mean_abs_error_gain_vs_prior": prior_mean_error - hgb_mean_error
                if math.isfinite(hgb_mean_error) and math.isfinite(prior_mean_error)
                else math.nan,
                "hgb_sign_correct_rows": sum(_as_bool(row.get("sign_correct")) for row in hgb_rows),
                "prior_slope_sign_correct_rows": sum(_as_bool(row.get("sign_correct")) for row in prior_rows),
                "claim_scope": "prospective_supported_contrast_diagnostic",
            }
        )
    return output


def policy_ranking_rank_correlation_rows(
    pairwise_rows: list[dict[str, Any]],
    *,
    min_contrasts: int = 5,
) -> list[dict[str, Any]]:
    """Compute contrast-level rank correlations between observed and predicted effects."""
    summaries = _contrast_level_effect_rows(_prospective_policy_pairwise_rows(pairwise_rows))
    grouped: dict[tuple[str, str, int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        for family in (str(row["contrast_family"]), "all"):
            grouped[
                (
                    str(row["split_name"]),
                    str(row["target"]),
                    int(row["horizon_checkups"]),
                    str(row["model_level"]),
                    str(row["feature_group"]),
                    family,
                )
            ].append(row)

    output = []
    for (split_name, target, horizon, model_level, feature_group, family), rows in sorted(grouped.items()):
        observed = [_as_float(row["observed_effect_b_minus_a"]) for row in rows]
        predicted = [_as_float(row["predicted_effect_b_minus_a"]) for row in rows]
        paired = [(obs, pred) for obs, pred in zip(observed, predicted, strict=False) if math.isfinite(obs) and math.isfinite(pred)]
        if len(paired) < min_contrasts:
            status = "insufficient_contrasts"
            spearman = math.nan
            kendall = math.nan
        else:
            status = "evaluated"
            spearman = _spearman_correlation([obs for obs, _ in paired], [pred for _, pred in paired])
            kendall = _kendall_tau_b([obs for obs, _ in paired], [pred for _, pred in paired])
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "model_level": model_level,
                "feature_group": feature_group,
                "contrast_family": family,
                "contrast_rows": len(rows),
                "rank_evaluable_contrasts": len(paired),
                "spearman_r": spearman,
                "kendall_tau_b": kendall,
                "status": status,
                "claim_scope": "prospective_supported_contrast_diagnostic",
            }
        )
    return output


def policy_ranking_topk_regret_rows(
    pairwise_rows: list[dict[str, Any]],
    *,
    topk_values: tuple[int, ...] = POLICY_RANKING_TOPK_VALUES,
    min_contrasts: int = 3,
) -> list[dict[str, Any]]:
    """Evaluate whether predicted ranks identify the most harmful supported contrasts."""
    summaries = _contrast_level_effect_rows(_prospective_policy_pairwise_rows(pairwise_rows))
    grouped: dict[tuple[str, str, int, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        for family in (str(row["contrast_family"]), "all"):
            grouped[
                (
                    str(row["split_name"]),
                    str(row["target"]),
                    int(row["horizon_checkups"]),
                    str(row["model_level"]),
                    str(row["feature_group"]),
                    family,
                )
            ].append(row)

    output = []
    for (split_name, target, horizon, model_level, feature_group, family), rows in sorted(grouped.items()):
        finite_rows = [
            row
            for row in rows
            if math.isfinite(_as_float(row["observed_effect_b_minus_a"]))
            and math.isfinite(_as_float(row["predicted_effect_b_minus_a"]))
        ]
        for top_k in topk_values:
            effective_k = min(top_k, len(finite_rows))
            if len(finite_rows) < min_contrasts or effective_k <= 0:
                output.append(
                    {
                        "split_name": split_name,
                        "target": target,
                        "horizon_checkups": horizon,
                        "model_level": model_level,
                        "feature_group": feature_group,
                        "contrast_family": family,
                        "top_k": top_k,
                        "effective_top_k": effective_k,
                        "contrast_rows": len(finite_rows),
                        "topk_overlap_fraction": math.nan,
                        "mean_observed_effect_selected": math.nan,
                        "mean_observed_effect_best": math.nan,
                        "regret_vs_observed_best": math.nan,
                        "status": "insufficient_contrasts",
                        "claim_scope": "prospective_supported_contrast_diagnostic",
                    }
                )
                continue
            observed_best = sorted(
                finite_rows,
                key=lambda row: (_as_float(row["observed_effect_b_minus_a"]), str(row["contrast_id"])),
                reverse=True,
            )[:effective_k]
            predicted_selected = sorted(
                finite_rows,
                key=lambda row: (_as_float(row["predicted_effect_b_minus_a"]), str(row["contrast_id"])),
                reverse=True,
            )[:effective_k]
            observed_ids = {str(row["contrast_id"]) for row in observed_best}
            predicted_ids = {str(row["contrast_id"]) for row in predicted_selected}
            selected_mean = _mean([_as_float(row["observed_effect_b_minus_a"]) for row in predicted_selected])
            best_mean = _mean([_as_float(row["observed_effect_b_minus_a"]) for row in observed_best])
            output.append(
                {
                    "split_name": split_name,
                    "target": target,
                    "horizon_checkups": horizon,
                    "model_level": model_level,
                    "feature_group": feature_group,
                    "contrast_family": family,
                    "top_k": top_k,
                    "effective_top_k": effective_k,
                    "contrast_rows": len(finite_rows),
                    "topk_overlap_fraction": len(observed_ids & predicted_ids) / effective_k,
                    "mean_observed_effect_selected": selected_mean,
                    "mean_observed_effect_best": best_mean,
                    "regret_vs_observed_best": best_mean - selected_mean,
                    "status": "evaluated",
                    "claim_scope": "prospective_supported_contrast_diagnostic",
                }
            )
    return output


def policy_ranking_failure_forensics_claim_readiness_rows(
    *,
    pairwise_rows: list[dict[str, Any]],
    by_family_rows: list[dict[str, Any]],
    bootstrap_rows: list[dict[str, Any]],
    effect_threshold_rows: list[dict[str, Any]],
    rank_rows: list[dict[str, Any]],
    failure_bin_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return conservative readiness rows for the failure-forensics gate."""
    del pairwise_rows, by_family_rows
    strict_prior_rows = [
        row
        for row in bootstrap_rows
        if str(row.get("contrast_family")) == "all"
        and str(row.get("target")) == "delta_capacity_Ah_h"
        and int(row.get("horizon_checkups", 0)) in set(POLICY_RANKING_HORIZONS)
        and str(row.get("candidate_model_level")) == POLICY_RANKING_PRIMARY_MODEL[0]
        and str(row.get("candidate_feature_group")) == POLICY_RANKING_PRIMARY_MODEL[1]
        and str(row.get("reference_model_level")) == "MH1_prior_slope_linear"
        and str(row.get("reference_feature_group")) == "prior_slope"
    ]
    strict_prior_pass = [
        row
        for row in strict_prior_rows
        if _as_float(row.get("accuracy_gain")) > 0 and _as_float(row.get("accuracy_gain_p05")) > 0
    ]
    large_effect_rows = [
        row
        for row in failure_bin_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["effect_bin"]) == "large_ge_0.05Ah"
        and str(row["contrast_family"]) != "all"
    ]
    large_effect_passing_families = {
        str(row["contrast_family"])
        for row in large_effect_rows
        if _as_float(row.get("sign_accuracy_gain_vs_prior")) > 0
        and _as_float(row.get("hgb_sign_accuracy")) >= 0.5
    }
    c_rate_large_rows = [
        row
        for row in failure_bin_rows
        if str(row["split_name"]) == "c_rate_holdout_fold"
        and str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["effect_bin"]) in {"medium_0.02_to_0.05Ah", "large_ge_0.05Ah"}
        and str(row["contrast_family"]) == "all"
    ]
    c_rate_large_pass_rows = [
        row
        for row in c_rate_large_rows
        if _as_float(row.get("sign_accuracy_gain_vs_prior")) > 0
        and _as_float(row.get("hgb_sign_accuracy")) >= 0.5
    ]
    fixed_002_rows = [
        row
        for row in effect_threshold_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["model_level"]) == POLICY_RANKING_PRIMARY_MODEL[0]
        and str(row["feature_group"]) == POLICY_RANKING_PRIMARY_MODEL[1]
        and str(row["effect_threshold_label"]) == "ge_0.02Ah"
        and str(row["contrast_family"]) == "all"
    ]
    threshold_accuracy = _mean([_as_float(row["sign_accuracy"]) for row in fixed_002_rows])
    rank_hgb_better_families = _rank_families_hgb_better_than_prior(rank_rows)
    if len(large_effect_passing_families) >= 2 and len(c_rate_large_pass_rows) >= 2:
        next_gate_status = "possible_next_gate"
        evidence_prefix = "Large-effect HGB-vs-prior diagnostics pass in multiple families and C-rate rows."
    elif large_effect_passing_families or c_rate_large_pass_rows or (
        math.isfinite(threshold_accuracy) and threshold_accuracy >= 0.75
    ):
        next_gate_status = "diagnostic_only"
        evidence_prefix = "Some large-effect or thresholded diagnostics improve, but not enough for a new gate."
    else:
        next_gate_status = "not_supported"
        evidence_prefix = "Large-effect and rank diagnostics do not rescue the prior-slope gate."

    return [
        {
            "claim_area": "contrast-ordering failure forensics",
            "status": "supported_for_diagnostics",
            "evidence": (
                f"Report-only diagnostics generated over existing 7.3 artifacts; "
                f"{len(strict_prior_pass)}/{len(strict_prior_rows)} strict HGB-vs-prior all-family checks pass."
            ),
            "allowed_wording": "The 7.3 failure can be decomposed by effect size, rank metric, split, horizon, and family.",
            "forbidden_wording": "The diagnostics train a new policy model or prove policy utility.",
        },
        {
            "claim_area": "large-effect contrast ordering next gate",
            "status": next_gate_status,
            "evidence": (
                f"{evidence_prefix} Large-effect passing families: "
                f"{', '.join(sorted(large_effect_passing_families)) or 'none'}; "
                f"C-rate medium/large pass rows: {len(c_rate_large_pass_rows)}/{len(c_rate_large_rows)}; "
                f"HGB ge_0.02Ah mean sign accuracy: {_format_float(threshold_accuracy)}."
            ),
            "allowed_wording": "At most, a future predeclared large-effect supported-contrast gate may be considered if diagnostics justify it.",
            "forbidden_wording": "Policy ranking, recommendation, or broad policy-response modeling is authorized.",
        },
        {
            "claim_area": "rank-metric robustness",
            "status": "diagnostic_only" if rank_hgb_better_families else "not_supported",
            "evidence": (
                f"HGB K2 Spearman exceeds prior slope in {len(rank_hgb_better_families)} contrast families: "
                f"{', '.join(sorted(rank_hgb_better_families)) or 'none'}."
            ),
            "allowed_wording": "Rank correlations can contextualize sign-accuracy failures.",
            "forbidden_wording": "Rank metrics validate policy recommendation quality.",
        },
        {
            "claim_area": "K3 oracle exclusion",
            "status": "supported_for_diagnostics",
            "evidence": "Oracle K3 rows are excluded from prospective forensics readiness.",
            "allowed_wording": "K3 remains an oracle/future-exposure diagnostic only.",
            "forbidden_wording": "K3 is a prospective policy input.",
        },
        {
            "claim_area": "policy recommendation",
            "status": "blocked",
            "evidence": "The gate uses observed supported contrasts and existing prediction artifacts only.",
            "allowed_wording": "No operating-policy recommendation is made.",
            "forbidden_wording": "Select, prescribe, optimize, or deploy a battery operating policy.",
        },
        {
            "claim_area": "causal or same-cell counterfactual policy claims",
            "status": "blocked",
            "evidence": "Observed condition-triplet contrasts are not same-cell interventions.",
            "allowed_wording": "Report support-bounded observed contrast diagnostics only.",
            "forbidden_wording": "Changing a policy would cause the estimated degradation effect in the same cell.",
        },
        {
            "claim_area": "calibrated policy risk or CBAT readiness",
            "status": "blocked",
            "evidence": "Calibrated policy utility/risk, CBAT, and architecture claims require later gates that remain blocked.",
            "allowed_wording": "Scores are diagnostic ordering outputs.",
            "forbidden_wording": "Calibrated policy risk, utility, CBAT, or architecture readiness is supported.",
        },
    ]


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


def _write_policy_ranking_failure_forensics_markdown(
    out_path: Path,
    *,
    readiness_rows: list[dict[str, str]],
    failure_bin_rows: list[dict[str, Any]],
    effect_threshold_rows: list[dict[str, Any]],
    rank_rows: list[dict[str, Any]],
    topk_rows: list[dict[str, Any]],
    bootstrap_rows: list[dict[str, Any]],
) -> None:
    primary_prior = [
        row
        for row in bootstrap_rows
        if str(row.get("contrast_family")) == "all"
        and str(row.get("target")) == "delta_capacity_Ah_h"
        and int(row.get("horizon_checkups", 0)) in set(POLICY_RANKING_HORIZONS)
        and str(row.get("reference_model_level")) == "MH1_prior_slope_linear"
    ]
    main_bins = [
        row
        for row in failure_bin_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["contrast_family"]) == "all"
    ][:20]
    primary_thresholds = [
        row
        for row in effect_threshold_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["model_level"]) == POLICY_RANKING_PRIMARY_MODEL[0]
        and str(row["feature_group"]) == POLICY_RANKING_PRIMARY_MODEL[1]
        and str(row["contrast_family"]) == "all"
    ][:20]
    primary_ranks = [
        row
        for row in rank_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["model_level"]) == POLICY_RANKING_PRIMARY_MODEL[0]
        and str(row["feature_group"]) == POLICY_RANKING_PRIMARY_MODEL[1]
        and str(row["contrast_family"]) == "all"
    ][:20]
    primary_topk = [
        row
        for row in topk_rows
        if str(row["target"]) == "delta_capacity_Ah_h"
        and int(row["horizon_checkups"]) in set(POLICY_RANKING_HORIZONS)
        and str(row["model_level"]) == POLICY_RANKING_PRIMARY_MODEL[0]
        and str(row["feature_group"]) == POLICY_RANKING_PRIMARY_MODEL[1]
        and str(row["contrast_family"]) == "all"
    ][:20]
    lines = [
        "# Policy Ranking Failure Forensics",
        "",
        "This report diagnoses the Milestone 7.3 supported contrast-ordering near miss using existing CSV artifacts only. It does not train a model, add features, recommend policies, estimate causal effects, or create same-cell counterfactuals.",
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
            "## Strict Prior-Slope Bootstrap Rows",
            "",
            "| Split | Horizon | Gain | Gain p05 | Candidate accuracy | Prior accuracy |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in primary_prior:
        lines.append(
            "| {split} | {horizon} | {gain} | {p05} | {cand} | {ref} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                gain=_format_float(row["accuracy_gain"]),
                p05=_format_float(row["accuracy_gain_p05"]),
                cand=_format_float(row["candidate_sign_accuracy"]),
                ref=_format_float(row["reference_sign_accuracy"]),
            )
        )
    lines.extend(
        [
            "",
            "## HGB Versus Prior By Effect Bin",
            "",
            "| Split | Horizon | Bin | Rows | HGB sign acc. | Prior sign acc. | Gain | HGB MAE | Prior MAE |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in main_bins:
        lines.append(
            "| {split} | {horizon} | {bin} | {rows} | {hgb} | {prior} | {gain} | {hgb_mae} | {prior_mae} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                bin=row["effect_bin"],
                rows=row["matched_rows"],
                hgb=_format_float(row["hgb_sign_accuracy"]),
                prior=_format_float(row["prior_slope_sign_accuracy"]),
                gain=_format_float(row["sign_accuracy_gain_vs_prior"]),
                hgb_mae=_format_float(row["hgb_mean_effect_abs_error"]),
                prior_mae=_format_float(row["prior_slope_mean_effect_abs_error"]),
            )
        )
    lines.extend(
        [
            "",
            "## HGB Effect-Threshold Sign Accuracy",
            "",
            "| Split | Horizon | Threshold | Rows | Sign accuracy | Median abs effect |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for row in primary_thresholds:
        lines.append(
            "| {split} | {horizon} | {threshold} | {rows} | {acc} | {effect} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                threshold=row["effect_threshold_label"],
                rows=row["pairwise_rows"],
                acc=_format_float(row["sign_accuracy"]),
                effect=_format_float(row["median_abs_observed_effect_Ah"]),
            )
        )
    lines.extend(
        [
            "",
            "## HGB Rank Diagnostics",
            "",
            "| Split | Horizon | Contrasts | Spearman | Kendall tau-b | Status |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in primary_ranks:
        lines.append(
            "| {split} | {horizon} | {rows} | {spearman} | {kendall} | {status} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                rows=row["rank_evaluable_contrasts"],
                spearman=_format_float(row["spearman_r"]),
                kendall=_format_float(row["kendall_tau_b"]),
                status=row["status"],
            )
        )
    lines.extend(
        [
            "",
            "## HGB Top-K Harmful Contrast Diagnostics",
            "",
            "| Split | Horizon | Top-k | Overlap | Regret | Status |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in primary_topk:
        lines.append(
            "| {split} | {horizon} | {top_k} | {overlap} | {regret} | {status} |".format(
                split=row["split_name"],
                horizon=row["horizon_checkups"],
                top_k=row["top_k"],
                overlap=_format_float(row["topk_overlap_fraction"]),
                regret=_format_float(row["regret_vs_observed_best"]),
                status=row["status"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Near-zero observed contrasts can make sign accuracy brittle; thresholded rows show whether that explains the 7.3 strict-gate failure.",
            "- Rank and top-k diagnostics are support-bounded forensics, not policy optimization.",
            "- Policy recommendation, causal effects, same-cell counterfactuals, calibrated policy risk/utility, sequence/neural models, and CBAT remain blocked.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_policy_ranking_failure_claim_readiness_markdown(
    out_path: Path,
    readiness_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Policy Ranking Failure Forensics Claim Readiness",
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


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _prospective_policy_pairwise_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not _is_oracle_policy_row(row)]


def _is_oracle_policy_row(row: dict[str, Any]) -> bool:
    return (
        str(row.get("claim_scope")) == "oracle_diagnostic_only"
        or str(row.get("feature_group")) in ORACLE_POLICY_RANKING_FEATURE_GROUPS
    )


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def _effect_threshold_label(threshold: float) -> str:
    if threshold == 0:
        return "ge_0Ah"
    return f"ge_{threshold:g}Ah"


def _effect_bin_label(abs_effect: float) -> str:
    for label, lower, upper in POLICY_RANKING_EFFECT_BINS_AH:
        if lower <= abs_effect < upper:
            return label
    return "unbinned"


def _forensics_pairwise_match_key(row: dict[str, Any]) -> tuple[str, str, int, str, str, int, int]:
    return (
        str(row["split_name"]),
        str(row["target"]),
        int(row["horizon_checkups"]),
        str(row["contrast_family"]),
        str(row["contrast_id"]),
        int(row["checkup_k"]),
        int(row["target_checkup_k"]),
    )


def _accuracy_forensics(rows: list[dict[str, Any]]) -> float:
    evaluable = [row for row in rows if _as_bool(row.get("sign_evaluable"))]
    if not evaluable:
        return math.nan
    return sum(_as_bool(row.get("sign_correct")) for row in evaluable) / len(evaluable)


def _contrast_level_effect_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["split_name"]),
                str(row["target"]),
                int(row["horizon_checkups"]),
                str(row["model_level"]),
                str(row["feature_group"]),
                str(row["contrast_family"]),
                str(row["contrast_id"]),
            )
        ].append(row)

    output = []
    for (split_name, target, horizon, model_level, feature_group, family, contrast_id), group in sorted(grouped.items()):
        observed = [_as_float(row.get("observed_effect_b_minus_a")) for row in group]
        predicted = [_as_float(row.get("predicted_effect_b_minus_a")) for row in group]
        output.append(
            {
                "split_name": split_name,
                "target": target,
                "horizon_checkups": horizon,
                "model_level": model_level,
                "feature_group": feature_group,
                "contrast_family": family,
                "contrast_id": contrast_id,
                "observed_effect_b_minus_a": _mean([value for value in observed if math.isfinite(value)]),
                "predicted_effect_b_minus_a": _mean([value for value in predicted if math.isfinite(value)]),
                "source_pairwise_rows": len(group),
            }
        )
    return output


def _rank_values(values: list[float]) -> list[float]:
    indexed = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position + 1
        while end < len(indexed) and indexed[end][0] == indexed[position][0]:
            end += 1
        average_rank = (position + 1 + end) / 2.0
        for _, original_index in indexed[position:end]:
            ranks[original_index] = average_rank
        position = end
    return ranks


def _pearson_correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    left_mean = _mean(left)
    right_mean = _mean(right)
    left_centered = [value - left_mean for value in left]
    right_centered = [value - right_mean for value in right]
    numerator = sum(a * b for a, b in zip(left_centered, right_centered, strict=False))
    left_denominator = math.sqrt(sum(value * value for value in left_centered))
    right_denominator = math.sqrt(sum(value * value for value in right_centered))
    denominator = left_denominator * right_denominator
    if denominator == 0:
        return math.nan
    return numerator / denominator


def _spearman_correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    return _pearson_correlation(_rank_values(left), _rank_values(right))


def _kendall_tau_b(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    concordant = 0
    discordant = 0
    left_ties = 0
    right_ties = 0
    for i in range(len(left) - 1):
        for j in range(i + 1, len(left)):
            left_delta = _sign_number(left[i] - left[j])
            right_delta = _sign_number(right[i] - right[j])
            if left_delta == 0 and right_delta == 0:
                continue
            if left_delta == 0:
                left_ties += 1
            elif right_delta == 0:
                right_ties += 1
            elif left_delta == right_delta:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt((concordant + discordant + left_ties) * (concordant + discordant + right_ties))
    if denominator == 0:
        return math.nan
    return (concordant - discordant) / denominator


def _sign_number(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _rank_families_hgb_better_than_prior(rank_rows: list[dict[str, Any]]) -> set[str]:
    hgb_by_key: dict[tuple[str, str, int, str], float] = {}
    prior_by_key: dict[tuple[str, str, int, str], float] = {}
    for row in rank_rows:
        if (
            str(row["target"]) != "delta_capacity_Ah_h"
            or int(row["horizon_checkups"]) not in set(POLICY_RANKING_HORIZONS)
            or str(row["contrast_family"]) == "all"
        ):
            continue
        key = (
            str(row["split_name"]),
            str(row["contrast_family"]),
            int(row["horizon_checkups"]),
            str(row["target"]),
        )
        model_key = (str(row["model_level"]), str(row["feature_group"]))
        if model_key == POLICY_RANKING_PRIMARY_MODEL:
            hgb_by_key[key] = _as_float(row["spearman_r"])
        elif model_key == ("MH1_prior_slope_linear", "prior_slope"):
            prior_by_key[key] = _as_float(row["spearman_r"])
    passing = set()
    for key in sorted(set(hgb_by_key) & set(prior_by_key)):
        hgb = hgb_by_key[key]
        prior = prior_by_key[key]
        if math.isfinite(hgb) and math.isfinite(prior) and hgb > prior:
            passing.add(str(key[1]))
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
