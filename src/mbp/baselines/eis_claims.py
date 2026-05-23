"""Milestone 2.1.1 EIS claim-hardening diagnostics."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import json
import math
from pathlib import Path
import tempfile
from typing import Any

import pyarrow.parquet as pq

from mbp.baselines import capacity as capacity_baselines
from mbp.baselines import pulse as pulse_baselines
from mbp.baselines import eis as eis_baselines
from mbp.baselines.capacity import (
    _all_primary_prediction_keys,
    _as_float,
    _best_selection_by_target_split,
    _bootstrap_gain_summary,
    _condition_metadata_by_parameter_set,
    _format_diagnostic_value,
    _group_by,
    _load_prediction_rows,
    _mean,
    _median,
    _paired_best_nonpulse_gain_rows,
    _selection_condition_mae_rows,
    _selection_summary_rows,
    _write_csv,
)

SCHEMA_VERSION = "gate211.eis_claim_hardening.v1"
PULSE_PRIOR_EIS_GROUPS = set(pulse_baselines.EIS_FEATURE_GROUPS)
CAPACITY_PRIOR_EIS_GROUPS = set(capacity_baselines.EIS_FEATURE_GROUPS)
SELECTED_FREQUENCY_K_FEATURES = (
    "eis_z_real_1kHz_k",
    "eis_z_imag_1kHz_k",
    "eis_z_abs_1kHz_k",
    "eis_phase_1kHz_k",
    "nyquist_semicircle_width_proxy_k",
)


def compare_prior_eis_pulse_reports(
    non_eis_report_path: Path,
    prior_eis_report_path: Path,
    out_dir: Path,
    *,
    stress_report_path: Path | None = None,
    eis_targets_path: Path | None = None,
    max_eis_alignment_delta_s: float | None = None,
    require_complete_selected_frequencies: bool = False,
    min_valid_modeling_fraction: float | None = None,
    seed: int = 42,
    bootstrap_resamples: int = 1000,
) -> dict[str, Any]:
    """Compare prior-EIS PULSE groups against strongest supplied non-EIS PULSE groups."""
    return _compare_prior_eis_reports(
        target_family="pulse",
        non_eis_report_paths=[path for path in (non_eis_report_path, stress_report_path) if path],
        prior_eis_report_path=prior_eis_report_path,
        out_dir=out_dir,
        prior_eis_groups=PULSE_PRIOR_EIS_GROUPS,
        primary_target="delta_pulse_1s_resistance",
        guardrail_target=None,
        eis_targets_path=eis_targets_path,
        max_eis_alignment_delta_s=max_eis_alignment_delta_s,
        require_complete_selected_frequencies=require_complete_selected_frequencies,
        min_valid_modeling_fraction=min_valid_modeling_fraction,
        seed=seed,
        bootstrap_resamples=bootstrap_resamples,
    )


def compare_prior_eis_capacity_reports(
    non_eis_report_paths: list[Path],
    prior_eis_report_path: Path,
    out_dir: Path,
    *,
    eis_targets_path: Path | None = None,
    max_eis_alignment_delta_s: float | None = None,
    require_complete_selected_frequencies: bool = False,
    min_valid_modeling_fraction: float | None = None,
    seed: int = 42,
    bootstrap_resamples: int = 1000,
) -> dict[str, Any]:
    """Compare prior-EIS capacity groups against strongest supplied non-EIS capacity groups."""
    return _compare_prior_eis_reports(
        target_family="capacity",
        non_eis_report_paths=non_eis_report_paths,
        prior_eis_report_path=prior_eis_report_path,
        out_dir=out_dir,
        prior_eis_groups=CAPACITY_PRIOR_EIS_GROUPS,
        primary_target="capacity_Ah_k1",
        guardrail_target="delta_capacity_Ah",
        eis_targets_path=eis_targets_path,
        max_eis_alignment_delta_s=max_eis_alignment_delta_s,
        require_complete_selected_frequencies=require_complete_selected_frequencies,
        min_valid_modeling_fraction=min_valid_modeling_fraction,
        seed=seed,
        bootstrap_resamples=bootstrap_resamples,
    )


def write_eis_hardening_sensitivity_reports(
    *,
    pulse_non_eis_report: Path,
    pulse_prior_eis_report: Path,
    capacity_non_eis_reports: list[Path],
    capacity_prior_eis_report: Path,
    eis_targets_path: Path,
    alignment_out_dir: Path,
    feature_completeness_out: Path,
    feature_completeness_md: Path,
    bootstrap_resamples: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Write alignment and feature-completeness sensitivity summaries."""
    alignment_out_dir.mkdir(parents=True, exist_ok=True)
    alignment_rows: dict[str, list[dict[str, Any]]] = {}
    with tempfile.TemporaryDirectory(prefix="mbp_eis_hardening_") as temp_root_name:
        temp_root = Path(temp_root_name)
        for family, runner, kwargs in (
            (
                "pulse",
                compare_prior_eis_pulse_reports,
                {
                    "non_eis_report_path": pulse_non_eis_report,
                    "prior_eis_report_path": pulse_prior_eis_report,
                },
            ),
            (
                "capacity",
                compare_prior_eis_capacity_reports,
                {
                    "non_eis_report_paths": capacity_non_eis_reports,
                    "prior_eis_report_path": capacity_prior_eis_report,
                },
            ),
        ):
            rows: list[dict[str, Any]] = []
            for label, threshold in (("all", None), ("le_24h", 86400.0), ("le_36h", 129600.0)):
                temp_out = temp_root / f"{family}_{label}"
                report = runner(
                    **kwargs,
                    out_dir=temp_out,
                    eis_targets_path=eis_targets_path,
                    max_eis_alignment_delta_s=threshold,
                    bootstrap_resamples=bootstrap_resamples,
                    seed=seed,
                )
                rows.extend(_sensitivity_rows_from_report(report, label, threshold))
            alignment_rows[family] = rows
            _write_csv(
                alignment_out_dir / f"{family}_prior_eis_alignment_summary.csv",
                rows,
            )

        feature_rows: list[dict[str, Any]] = []
        filters = (
            ("all_rt50", False, None),
            ("complete_selected_frequencies", True, None),
            ("valid_fraction_gt_0", False, 1e-12),
            ("valid_fraction_ge_0p7", False, 0.7),
        )
        for label, complete, min_fraction in filters:
            pulse_report = compare_prior_eis_pulse_reports(
                pulse_non_eis_report,
                pulse_prior_eis_report,
                temp_root / f"pulse_feature_{label}",
                eis_targets_path=eis_targets_path,
                require_complete_selected_frequencies=complete,
                min_valid_modeling_fraction=min_fraction,
                bootstrap_resamples=bootstrap_resamples,
                seed=seed,
            )
            capacity_report = compare_prior_eis_capacity_reports(
                capacity_non_eis_reports,
                capacity_prior_eis_report,
                temp_root / f"capacity_feature_{label}",
                eis_targets_path=eis_targets_path,
                require_complete_selected_frequencies=complete,
                min_valid_modeling_fraction=min_fraction,
                bootstrap_resamples=bootstrap_resamples,
                seed=seed,
            )
            feature_rows.extend(_feature_sensitivity_rows(pulse_report, label))
            feature_rows.extend(_feature_sensitivity_rows(capacity_report, label))

    _write_csv(feature_completeness_out, feature_rows)
    _write_feature_completeness_md(feature_rows, feature_completeness_md)
    _write_alignment_claim_readiness(alignment_rows, alignment_out_dir / "eis_alignment_claim_readiness.md")
    return {
        "status": "passed",
        "alignment": {
            "pulse": str(alignment_out_dir / "pulse_prior_eis_alignment_summary.csv"),
            "capacity": str(alignment_out_dir / "capacity_prior_eis_alignment_summary.csv"),
        },
        "feature_completeness": str(feature_completeness_out),
    }


def write_eis_self_endpoint_claim_readiness(
    eis_report_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    report = json.loads(eis_report_path.read_text(encoding="utf-8"))
    metrics = [
        row
        for row in report.get("metrics", [])
        if row.get("run_scope") == "primary"
        and row.get("model_level") in {"L0_persistence", "L2_hist_gradient_boosting"}
    ]
    by_target_split: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in metrics:
        key = (str(row["target"]), str(row["split_name"]))
        by_target_split[key][str(row["model_level"])] = row
    rows: list[dict[str, Any]] = []
    for (target, split_name), grouped in sorted(by_target_split.items()):
        l0 = grouped.get("L0_persistence")
        hgb = grouped.get("L2_hist_gradient_boosting")
        if not l0 or not hgb:
            continue
        gain = float(l0["condition_mean_mae"]) - float(hgb["condition_mean_mae"])
        rows.append(
            {
                "target": target,
                "split_name": split_name,
                "l0_condition_mean_mae": l0["condition_mean_mae"],
                "hgb_condition_mean_mae": hgb["condition_mean_mae"],
                "hgb_gain_vs_persistence": gain,
                "status": "supported_for_diagnostics" if gain > 0 else "not_supported",
            }
        )
    supported = [row for row in rows if row["status"] == "supported_for_diagnostics"]
    lines = [
        "# EIS Self-Endpoint Claim Readiness",
        "",
        "This report separates EIS scalar endpoint predictability from EIS-as-input improvement claims.",
        "",
        "| Target | Split | L0 condition MAE | HGB condition MAE | HGB gain | Status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | {_format_diagnostic_value(row['l0_condition_mean_mae'])} | "
            f"{_format_diagnostic_value(row['hgb_condition_mean_mae'])} | {_format_diagnostic_value(row['hgb_gain_vs_persistence'])} | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "Decision: EIS scalar endpoints are supported for diagnostics when HGB improves over persistence under grouped splits. This does not authorize EIS predictive improvement claims for capacity or PULSE.",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"rows": rows, "supported_rows": len(supported)}


def write_eis_leakage_audit(out_path: Path) -> dict[str, Any]:
    forbidden = set(eis_baselines.EIS_FORBIDDEN_FEATURES)
    failures: dict[str, list[str]] = {}
    checks = {
        "capacity": (
            capacity_baselines.NUMERIC_FEATURES,
            capacity_baselines.CATEGORICAL_FEATURES,
            capacity_baselines.EIS_FEATURE_GROUPS,
        ),
        "pulse": (
            pulse_baselines.NUMERIC_FEATURES,
            pulse_baselines.CATEGORICAL_FEATURES,
            pulse_baselines.EIS_FEATURE_GROUPS,
        ),
        "eis_self": (
            eis_baselines.NUMERIC_FEATURES,
            eis_baselines.CATEGORICAL_FEATURES,
            eis_baselines.FEATURE_GROUPS,
        ),
    }
    for family, (numeric, categorical, groups) in checks.items():
        for group in groups:
            fields = set(numeric.get(group, ())) | set(categorical.get(group, ()))
            hits = sorted(fields & forbidden)
            bad_tokens = sorted(
                field
                for field in fields
                if "drt" in field.lower() or "embedding" in field.lower()
            )
            if hits or bad_tokens:
                failures[f"{family}:{group}"] = hits + bad_tokens
    status = "failed" if failures else "passed"
    lines = [
        "# EIS Leakage Audit",
        "",
        f"Status: `{status}`",
        "",
        "Allowed non-EIS target inputs are prior EIS `k` scalar features only.",
        "Future EIS `k1`, EIS deltas, R0/R1 without leakage-safe provenance, DRT features, and learned embeddings are forbidden.",
        "",
        "| Scope | Result |",
        "|---|---|",
        f"| Capacity prior-EIS groups | `{'failed' if any(key.startswith('capacity:') for key in failures) else 'passed'}` |",
        f"| PULSE prior-EIS groups | `{'failed' if any(key.startswith('pulse:') for key in failures) else 'passed'}` |",
        f"| EIS self-endpoint groups | `{'failed' if any(key.startswith('eis_self:') for key in failures) else 'passed'}` |",
    ]
    if failures:
        lines.extend(["", "## Forbidden Fields", ""])
        for key, fields in sorted(failures.items()):
            lines.append(f"- `{key}`: {', '.join(f'`{field}`' for field in fields)}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise ValueError(f"EIS leakage audit failed: {failures}")
    return {"status": status, "failures": failures}


def _compare_prior_eis_reports(
    *,
    target_family: str,
    non_eis_report_paths: list[Path],
    prior_eis_report_path: Path,
    out_dir: Path,
    prior_eis_groups: set[str],
    primary_target: str,
    guardrail_target: str | None,
    eis_targets_path: Path | None,
    max_eis_alignment_delta_s: float | None,
    require_complete_selected_frequencies: bool,
    min_valid_modeling_fraction: float | None,
    seed: int,
    bootstrap_resamples: int,
) -> dict[str, Any]:
    if not non_eis_report_paths:
        raise ValueError("At least one non-EIS report is required.")
    prior_report = json.loads(prior_eis_report_path.read_text(encoding="utf-8"))
    prior_predictions = _load_prediction_rows(prior_report)
    target_path = eis_targets_path or _input_path(prior_report, "eis_targets")
    eligible_interval_keys = (
        _eligible_interval_keys(
            target_path,
            max_alignment_delta_s=max_eis_alignment_delta_s,
            require_complete_selected_frequencies=require_complete_selected_frequencies,
            min_valid_modeling_fraction=min_valid_modeling_fraction,
        )
        if target_path is not None
        else None
    )
    covered_keys = _filtered_primary_prediction_keys(prior_predictions, eligible_interval_keys)
    metadata = _condition_metadata_by_parameter_set(prior_report)
    prior_condition_rows = _selection_condition_mae_rows(
        prior_predictions,
        allowed_feature_groups=prior_eis_groups,
        covered_keys=covered_keys,
        source_report=Path(prior_report["outputs"]["report"]).name,
    )
    non_eis_condition_rows: list[dict[str, Any]] = []
    for report_path in non_eis_report_paths:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        non_eis_condition_rows.extend(
            _selection_condition_mae_rows(
                _load_prediction_rows(report),
                allowed_feature_groups=None,
                covered_keys=covered_keys,
                source_report=report_path.name,
                exclude_feature_groups=prior_eis_groups,
            )
        )
    best_prior = _best_selection_by_target_split(prior_condition_rows)
    best_non_eis = _best_selection_by_target_split(non_eis_condition_rows)
    paired_rows = _rename_prior_gain_columns(
        _paired_best_nonpulse_gain_rows(
            prior_condition_rows,
            non_eis_condition_rows,
            best_prior,
            best_non_eis,
            metadata,
        )
    )
    split_summary = _prior_eis_split_gain_summary(paired_rows, bootstrap_resamples, seed)
    c_rate_summary = [row for row in split_summary if row["split_name"] == "c_rate_holdout_fold"]
    claim_rows = _prior_eis_claim_rows(split_summary, target_family, primary_target, guardrail_target)
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "paired_gain_vs_best_noneis.csv", paired_rows)
    _write_csv(out_dir / "split_level_gain_vs_best_noneis.csv", split_summary)
    _write_csv(out_dir / "c_rate_gain_vs_best_noneis.csv", c_rate_summary)
    _write_csv(out_dir / "bootstrap_gain_vs_best_noneis.csv", split_summary)
    _write_csv(plots_dir / "paired_gain_vs_best_noneis.csv", paired_rows)
    _write_csv(plots_dir / "split_level_gain_vs_best_noneis.csv", split_summary)
    _write_csv(plots_dir / "c_rate_gain_vs_best_noneis.csv", c_rate_summary)
    _write_csv(plots_dir / "bootstrap_gain_vs_best_noneis.csv", split_summary)
    readiness_path = out_dir / f"prior_eis_{target_family}_claim_readiness.md"
    _write_prior_eis_claim_readiness_md(claim_rows, split_summary, target_family, readiness_path)
    report = {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "target_family": target_family,
        "inputs": {
            "non_eis_reports": [str(path) for path in non_eis_report_paths],
            "prior_eis_report": str(prior_eis_report_path),
            "eis_targets": str(target_path) if target_path else None,
        },
        "filters": {
            "max_eis_alignment_delta_s": max_eis_alignment_delta_s,
            "require_complete_selected_frequencies": require_complete_selected_frequencies,
            "min_valid_modeling_fraction": min_valid_modeling_fraction,
        },
        "outputs": {
            "out_dir": str(out_dir),
            "paired_gain_vs_best_noneis": str(out_dir / "paired_gain_vs_best_noneis.csv"),
            "split_level_gain_vs_best_noneis": str(out_dir / "split_level_gain_vs_best_noneis.csv"),
            "claim_readiness": str(readiness_path),
        },
        "bootstrap_resamples": bootstrap_resamples,
        "seed": seed,
        "best_prior_eis_groups": _selection_summary_rows(best_prior),
        "best_noneis_groups": _selection_summary_rows(best_non_eis),
        "row_counts": {
            "eligible_interval_keys": len(eligible_interval_keys) if eligible_interval_keys is not None else "not_filtered",
            **_eligible_interval_metadata_counts(target_path, eligible_interval_keys),
            "covered_prediction_keys": len(covered_keys),
            "covered_c_rate_prediction_keys": len(
                {key for key in covered_keys if key[1] == "c_rate_holdout_fold"}
            ),
            "covered_profile_prediction_keys": len(
                {key for key in covered_keys if key[1] == "profile_holdout_fold"}
            ),
            "non_eis_condition_rows": len(non_eis_condition_rows),
            "prior_eis_condition_rows": len(prior_condition_rows),
            "paired_gain_rows": len(paired_rows),
            "split_summary_rows": len(split_summary),
        },
        "claim_rows": claim_rows,
    }
    (out_dir / f"prior_eis_{target_family}_comparison_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _input_path(report: dict[str, Any], key: str) -> Path | None:
    value = report.get("inputs", {}).get(key)
    return Path(str(value)) if value else None


def _filtered_primary_prediction_keys(
    prediction_rows: list[dict[str, Any]],
    eligible_interval_keys: set[tuple[str, int, int]] | None,
) -> set[tuple[str, str, int, str, int, int]]:
    keys = _all_primary_prediction_keys(prediction_rows)
    if eligible_interval_keys is None:
        return keys
    return {
        key
        for key in keys
        if (key[3], key[4], key[5]) in eligible_interval_keys
    }


def _eligible_interval_keys(
    eis_targets_path: Path,
    *,
    max_alignment_delta_s: float | None,
    require_complete_selected_frequencies: bool,
    min_valid_modeling_fraction: float | None,
) -> set[tuple[str, int, int]]:
    rows = pq.read_table(eis_targets_path).to_pylist()
    eligible: set[tuple[str, int, int]] = set()
    for row in rows:
        if max_alignment_delta_s is not None:
            k_delta = _as_float(row.get("alignment_delta_s_k"))
            k1_delta = _as_float(row.get("alignment_delta_s_k1"))
            if not (
                math.isfinite(k_delta)
                and math.isfinite(k1_delta)
                and k_delta <= max_alignment_delta_s
                and k1_delta <= max_alignment_delta_s
            ):
                continue
        if require_complete_selected_frequencies and any(
            not math.isfinite(_as_float(row.get(column)))
            for column in SELECTED_FREQUENCY_K_FEATURES
        ):
            continue
        if min_valid_modeling_fraction is not None:
            fraction = _as_float(row.get("valid_modeling_fraction_k"))
            if not math.isfinite(fraction) or fraction < min_valid_modeling_fraction:
                continue
        eligible.add((str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"])))
    return eligible


def _eligible_interval_metadata_counts(
    eis_targets_path: Path | None,
    eligible_interval_keys: set[tuple[str, int, int]] | None,
) -> dict[str, int | str]:
    if eis_targets_path is None or eligible_interval_keys is None:
        return {
            "eligible_cells": "not_filtered",
            "eligible_parameter_sets": "not_filtered",
            "eligible_c_rate_rows": "not_filtered",
            "eligible_profile_rows": "not_filtered",
        }
    rows = pq.read_table(
        eis_targets_path,
        columns=[
            "cell_id",
            "parameter_set",
            "checkup_k",
            "checkup_k_next",
            "c_rate_holdout_fold",
            "profile_holdout_fold",
        ],
    ).to_pylist()
    retained = [
        row
        for row in rows
        if (str(row["cell_id"]), int(row["checkup_k"]), int(row["checkup_k_next"]))
        in eligible_interval_keys
    ]
    return {
        "eligible_cells": len({str(row["cell_id"]) for row in retained}),
        "eligible_parameter_sets": len({int(row["parameter_set"]) for row in retained}),
        "eligible_c_rate_rows": len([row for row in retained if int(row["c_rate_holdout_fold"]) == 1]),
        "eligible_profile_rows": len([row for row in retained if int(row["profile_holdout_fold"]) == 1]),
    }


def _rename_prior_gain_columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    renamed: list[dict[str, Any]] = []
    for row in rows:
        output = dict(row)
        output["prior_eis_feature_group"] = output.pop("prior_pulse_feature_group")
        output["prior_eis_source_report"] = output.pop("prior_pulse_source_report")
        output["best_noneis_feature_group"] = output.pop("best_nonpulse_feature_group")
        output["best_noneis_source_report"] = output.pop("best_nonpulse_source_report")
        output["best_noneis_condition_mae"] = output.pop("best_nonpulse_condition_mae")
        output["prior_eis_condition_mae"] = output.pop("prior_pulse_condition_mae")
        renamed.append(output)
    return renamed


def _prior_eis_split_gain_summary(
    paired_rows: list[dict[str, Any]],
    bootstrap_resamples: int,
    seed: int,
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    grouped = _group_by(
        paired_rows,
        lambda row: (row["target"], row["split_name"], row["prior_eis_feature_group"]),
    )
    for (target, split_name, feature_group), rows in sorted(grouped.items()):
        gains = [float(row["gain"]) for row in rows]
        boot = _bootstrap_gain_summary(rows, bootstrap_resamples, seed)
        summaries.append(
            {
                "target": target,
                "split_name": split_name,
                "prior_eis_feature_group": feature_group,
                "best_noneis_feature_group": rows[0].get("best_noneis_feature_group", ""),
                "best_noneis_source_report": rows[0].get("best_noneis_source_report", ""),
                "n_conditions": len(rows),
                "mean_gain": _mean(gains),
                "median_gain": _median(gains),
                "win_rate": sum(1 for gain in gains if gain > 0) / len(gains),
                "worst_condition_gain": min(gains),
                **boot,
            }
        )
    return summaries


def _prior_eis_claim_rows(
    split_summary: list[dict[str, Any]],
    target_family: str,
    primary_target: str,
    guardrail_target: str | None,
) -> list[dict[str, str]]:
    primary_supported_rows = [
        row
        for row in split_summary
        if row["target"] == primary_target and _as_float(row.get("gain_p05")) > 0
    ]
    c_rate = _summary_row(split_summary, primary_target, "c_rate_holdout_fold")
    rows = [
        {
            "claim": f"Prior EIS beats strongest non-EIS for {target_family} primary target",
            "status": "supported" if primary_supported_rows else "not_supported",
            "evidence": (
                f"{len(primary_supported_rows)} split rows have bootstrap p05 > 0; "
                f"C-rate mean {_format_diagnostic_value(c_rate.get('mean_gain'))}, "
                f"p05 {_format_diagnostic_value(c_rate.get('gain_p05'))}"
            ),
            "decision": "Allow only narrow split-specific EIS claim" if primary_supported_rows else "Keep EIS improvement claim blocked",
        }
    ]
    if guardrail_target:
        guardrail = _summary_row(split_summary, guardrail_target, "c_rate_holdout_fold")
        guardrail_supported = _as_float(guardrail.get("gain_p05")) > 0
        rows.append(
            {
                "claim": f"Prior EIS improves {guardrail_target}",
                "status": "supported" if guardrail_supported else "not_supported",
                "evidence": (
                    f"C-rate mean {_format_diagnostic_value(guardrail.get('mean_gain'))}, "
                    f"p05 {_format_diagnostic_value(guardrail.get('gain_p05'))}"
                ),
                "decision": "Do not claim fade-rate improvement" if not guardrail_supported else "Report cautiously",
            }
        )
    rows.append(
        {
            "claim": "Leakage safety",
            "status": "supported",
            "evidence": "Only prior EIS `k` scalar features are allowed for non-EIS targets.",
            "decision": "Future EIS state, EIS deltas, R0/R1, DRT, and embeddings remain blocked.",
        }
    )
    return rows


def _summary_row(rows: list[dict[str, Any]], target: str, split_name: str) -> dict[str, Any]:
    return next((row for row in rows if row["target"] == target and row["split_name"] == split_name), {})


def _write_prior_eis_claim_readiness_md(
    claim_rows: list[dict[str, str]],
    split_summary: list[dict[str, Any]],
    target_family: str,
    path: Path,
) -> None:
    lines = [
        f"# Prior-EIS {target_family.title()} Claim Readiness",
        "",
        "This report compares prior-EIS feature groups against the strongest supplied non-EIS groups on the same EIS-covered prediction population.",
        "It does not authorize broad EIS, DRT, embedding, neural, CBAT, or multimodal claims.",
        "",
        "| Claim | Status | Evidence | Decision |",
        "|---|---|---|---|",
    ]
    for row in claim_rows:
        lines.append(f"| {row['claim']} | `{row['status']}` | {row['evidence']} | {row['decision']} |")
    lines.extend(
        [
            "",
            "## Paired Gain Summary",
            "",
            "| Target | Split | Prior-EIS group | Non-EIS group | Conditions | Mean gain | p05 | p50 | p95 | Win rate |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in split_summary:
        lines.append(
            f"| `{row['target']}` | `{row['split_name']}` | `{row['prior_eis_feature_group']}` | "
            f"`{row.get('best_noneis_feature_group', 'see_csv')}` | {row['n_conditions']} | "
            f"{_format_diagnostic_value(row['mean_gain'])} | {_format_diagnostic_value(row['gain_p05'])} | "
            f"{_format_diagnostic_value(row['gain_p50'])} | {_format_diagnostic_value(row['gain_p95'])} | "
            f"{_format_diagnostic_value(row['win_rate'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sensitivity_rows_from_report(
    report: dict[str, Any],
    label: str,
    threshold: float | None,
) -> list[dict[str, Any]]:
    rows = []
    for row in report.get("outputs", {}) and _read_csv(Path(report["outputs"]["split_level_gain_vs_best_noneis"])):
        output = dict(row)
        output["target_family"] = report["target_family"]
        output["alignment_threshold"] = label
        output["max_eis_alignment_delta_s"] = "all" if threshold is None else threshold
        output["eligible_interval_keys"] = report["row_counts"]["eligible_interval_keys"]
        output["eligible_parameter_sets"] = report["row_counts"]["eligible_parameter_sets"]
        output["eligible_c_rate_rows"] = report["row_counts"]["eligible_c_rate_rows"]
        output["eligible_profile_rows"] = report["row_counts"]["eligible_profile_rows"]
        output["covered_prediction_keys"] = report["row_counts"]["covered_prediction_keys"]
        output["covered_c_rate_prediction_keys"] = report["row_counts"]["covered_c_rate_prediction_keys"]
        output["covered_profile_prediction_keys"] = report["row_counts"]["covered_profile_prediction_keys"]
        rows.append(output)
    return rows


def _feature_sensitivity_rows(report: dict[str, Any], label: str) -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(Path(report["outputs"]["split_level_gain_vs_best_noneis"])):
        output = dict(row)
        output["target_family"] = report["target_family"]
        output["feature_completeness_filter"] = label
        output["eligible_interval_keys"] = report["row_counts"]["eligible_interval_keys"]
        rows.append(output)
    return rows


def _write_alignment_claim_readiness(
    alignment_rows: dict[str, list[dict[str, Any]]],
    path: Path,
) -> None:
    lines = [
        "# EIS Alignment Sensitivity Claim Readiness",
        "",
        "Alignment thresholds are diagnostic filters for Milestone 2.1.1; they do not redefine the canonical EIS target table.",
        "",
        "| Target family | Conclusion |",
        "|---|---|",
    ]
    for family, rows in sorted(alignment_rows.items()):
        all_rows = [row for row in rows if row["alignment_threshold"] == "all"]
        le24_rows = [row for row in rows if row["alignment_threshold"] == "le_24h"]
        conclusion = "diagnostic_only"
        if all_rows and le24_rows:
            conclusion = "sensitivity_quantified"
        lines.append(f"| `{family}` | `{conclusion}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_feature_completeness_md(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        "# EIS Feature-Completeness Sensitivity",
        "",
        "This report checks whether selected-frequency completeness or valid modeling fraction filters alter prior-EIS comparison conclusions.",
        "",
        "| Filter | Target family | Target | Split | Mean gain | p05 | Covered keys |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['feature_completeness_filter']}` | `{row['target_family']}` | `{row['target']}` | "
            f"`{row['split_name']}` | {_format_diagnostic_value(row['mean_gain'])} | "
            f"{_format_diagnostic_value(row['gain_p05'])} | {row['eligible_interval_keys']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
