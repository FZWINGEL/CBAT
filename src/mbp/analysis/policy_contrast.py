"""Observed policy-contrast support and stability diagnostics.

This module builds matched observed-condition contrasts only. It does not train
models and does not estimate causal or counterfactual policy effects.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.schema_contracts import POLICY_CONTRAST_REGISTRY_V1_SCHEMA, validate_table

SCHEMA_VERSION = "gate72.policy_contrast_registry.v1"
DEFAULT_CONTRAST_FAMILIES = ("charge_c_rate", "temperature", "voltage_window", "profile")
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
