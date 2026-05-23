"""EIS QA, valid-frequency audits, and scalar feature products."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from mbp.data.luh_blank.parse_eis import compute_modeling_mask
from mbp.data.schema_contracts import EIS_FEATURE_TABLE_V1_SCHEMA, validate_table

SCHEMA_VERSION = "gate20.eis_features.v1"
FEATURE_POLICY_VERSION = "eis_feature_policy.v1"
SELECTED_FREQUENCIES: tuple[tuple[str, float], ...] = (
    ("0p5Hz", 0.5),
    ("1Hz", 1.0),
    ("10Hz", 10.0),
    ("1kHz", 1000.0),
    ("5kHz", 5000.0),
)
ALIGNMENT_THRESHOLDS_S: tuple[float, ...] = (21_600.0, 43_200.0, 86_400.0, 129_600.0)
SPLIT_COLUMNS: tuple[str, ...] = (
    "condition_fold",
    "temperature_holdout_fold",
    "c_rate_holdout_fold",
    "profile_holdout_fold",
    "voltage_window_holdout_fold",
)


def write_eis_qa_report(
    eis_table_path: Path,
    eis_quality_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out_path: Path,
    alignment_out_path: Path,
    frequency_out_path: Path,
    *,
    large_alignment_delta_s: float = 86_400.0,
) -> dict[str, Any]:
    """Write EIS coverage, alignment, and valid-frequency QA artifacts."""
    eis_rows = _read_parquet_rows(eis_table_path)
    quality_rows = _read_parquet_rows(eis_quality_path)
    interval_rows = _read_parquet_rows(interval_table_path)
    metadata_by_checkup = _metadata_by_cell_checkup(interval_rows)

    coverage_rows = _coverage_rows(quality_rows, metadata_by_checkup)
    _write_csv(coverage_out_path, coverage_rows)

    frequency_rows = _valid_frequency_audit_rows(eis_rows)
    _write_csv(frequency_out_path, frequency_rows)

    alignment_report = {
        "status": "warning",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "alignment_method_counts": dict(
            Counter(str(row.get("alignment_method", "")) for row in quality_rows)
        ),
        "alignment_delta_s": _numeric_summary(
            [_as_float(row.get("alignment_delta_s")) for row in quality_rows]
        ),
        "large_alignment_delta_s": large_alignment_delta_s,
        "large_alignment_delta_rows": sum(
            _as_float(row.get("alignment_delta_s")) > large_alignment_delta_s
            for row in quality_rows
        ),
    }
    _write_json(alignment_out_path, alignment_report)

    unique_parameter_sets = {
        int(meta["parameter_set"])
        for meta in (
            metadata_by_checkup.get((str(row.get("cell_id")), int(row.get("checkup_k"))))
            for row in quality_rows
            if row.get("checkup_k") is not None
        )
        if meta and meta.get("parameter_set") is not None
    }
    warnings: list[str] = []
    if len({str(row.get("cell_id")) for row in quality_rows}) < 228:
        warnings.append("eis_cell_coverage_below_228")
    if alignment_report["large_alignment_delta_rows"]:
        warnings.append(f"large_alignment_delta_rows={alignment_report['large_alignment_delta_rows']}")
    if any(row["mask_mismatch_rows"] for row in frequency_rows):
        warnings.append("stored_modeling_mask_differs_from_policy")

    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "feature_policy_version": FEATURE_POLICY_VERSION,
        "generated_at_utc": _now(),
        "inputs": {
            "eis_table": str(eis_table_path),
            "eis_quality": str(eis_quality_path),
            "interval_table": str(interval_table_path),
        },
        "row_count": len(eis_rows),
        "spectrum_count": len(quality_rows),
        "unique_cells": len({str(row.get("cell_id")) for row in quality_rows}),
        "unique_parameter_sets": len(unique_parameter_sets),
        "unique_checkups": len({int(row.get("checkup_k")) for row in quality_rows}),
        "soc_context_counts": dict(Counter(_soc_label(row.get("soc_percent")) for row in quality_rows)),
        "temperature_context_counts": dict(
            Counter(str(row.get("temperature_context", "")) for row in quality_rows)
        ),
        "valid_modeling_frequencies": _numeric_summary(
            [_as_float(row.get("valid_modeling_frequencies")) for row in quality_rows]
        ),
        "valid_modeling_fraction": _numeric_summary(
            [_as_float(row.get("valid_modeling_fraction")) for row in quality_rows]
        ),
        "low_valid_fraction_spectra": sum(
            _as_float(row.get("valid_modeling_fraction")) < 0.5 for row in quality_rows
        ),
        "alignment": alignment_report,
        "warnings": warnings,
        "outputs": {
            "coverage": str(coverage_out_path),
            "alignment": str(alignment_out_path),
            "frequency": str(frequency_out_path),
        },
    }
    _write_json(out_path, report)
    _write_spectrum_quality_summary(
        out_path.parent / "eis_spectrum_quality_summary.csv",
        quality_rows,
        metadata_by_checkup,
    )
    return report


def write_eis_alignment_sensitivity_report(
    eis_quality_path: Path,
    interval_table_path: Path,
    out_path: Path,
    coverage_out_path: Path,
    *,
    thresholds_s: tuple[float, ...] = ALIGNMENT_THRESHOLDS_S,
) -> dict[str, Any]:
    """Write retained EIS coverage under alignment-delta thresholds."""
    quality_rows = _read_parquet_rows(eis_quality_path)
    interval_rows = _read_parquet_rows(interval_table_path)
    metadata_by_checkup = _metadata_by_cell_checkup(interval_rows)
    all_thresholds = (*thresholds_s, math.inf)
    rows: list[dict[str, Any]] = []
    for threshold in all_thresholds:
        retained = [
            row
            for row in quality_rows
            if math.isinf(threshold) or _as_float(row.get("alignment_delta_s")) <= threshold
        ]
        split_counts = _split_counts(retained, metadata_by_checkup)
        rows.append(
            {
                "threshold_s": "all" if math.isinf(threshold) else threshold,
                "retained_spectra": len(retained),
                "retained_cells": len({str(row.get("cell_id")) for row in retained}),
                "retained_parameter_sets": len(_parameter_sets(retained, metadata_by_checkup)),
                "c_rate_holdout_rows": split_counts.get("c_rate_holdout_fold=1", 0),
                "profile_holdout_rows": split_counts.get("profile_holdout_fold=1", 0),
                "soc_contexts": "|".join(sorted({_soc_label(row.get("soc_percent")) for row in retained})),
                "temperature_contexts": "|".join(
                    sorted({str(row.get("temperature_context", "")) for row in retained})
                ),
            }
        )
    _write_csv(coverage_out_path, rows)
    warnings = [
        f"threshold_{row['threshold_s']}_low_c_rate_coverage"
        for row in rows
        if row["threshold_s"] != "all" and int(row["c_rate_holdout_rows"]) == 0
    ]
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "inputs": {"eis_quality": str(eis_quality_path), "interval_table": str(interval_table_path)},
        "thresholds": rows,
        "warnings": warnings,
        "outputs": {"coverage": str(coverage_out_path)},
    }
    _write_json(out_path, report)
    return report


def build_eis_feature_table(
    eis_table_path: Path,
    eis_quality_path: Path,
    interval_table_path: Path,
    out_path: Path,
    *,
    soc_percent: float = 50.0,
    temperature_context: str = "RT",
) -> pa.Table:
    """Build an E1/E2/E3 scalar EIS feature sidecar for one canonical context."""
    eis_rows = _read_parquet_rows(eis_table_path)
    quality_rows = _read_parquet_rows(eis_quality_path)
    metadata_by_checkup = _metadata_by_cell_checkup(_read_parquet_rows(interval_table_path))
    temp = temperature_context.upper()

    spectra: dict[tuple[str, int, float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eis_rows:
        if _same_soc(row.get("soc_percent"), soc_percent) and str(row.get("temperature_context", "")).upper() == temp:
            spectra[_spectrum_key(row)].append(row)
    quality_by_key = {_spectrum_key(row): row for row in quality_rows}

    feature_rows: list[dict[str, Any]] = []
    for key, rows in sorted(spectra.items()):
        cell_id, checkup_k, soc, context = key
        quality = quality_by_key.get(key, {})
        metadata = metadata_by_checkup.get((cell_id, checkup_k), {})
        valid_rows = [row for row in rows if _policy_modeling_mask(row)]
        features = _selected_frequency_features(valid_rows)
        features.update(_nyquist_features(valid_rows))
        missing_selected = [
            label
            for label, _freq in SELECTED_FREQUENCIES
            if features.get(f"freq_selected_{label}") is None
        ]
        flags = []
        if not valid_rows:
            flags.append("no_valid_modeling_frequencies")
        if missing_selected:
            flags.append(f"missing_selected_frequencies={','.join(missing_selected)}")
        feature_rows.append(
            {
                "cell_id": cell_id,
                "parameter_set": _maybe_int(metadata.get("parameter_set")),
                "replicate_id": _maybe_int(metadata.get("replicate_id")),
                "checkup_k": checkup_k,
                "soc_percent": soc,
                "temperature_context": context,
                "temperature_C_mean": _maybe_float(quality.get("temperature_C_mean")),
                "valid_modeling_fraction": _as_float(quality.get("valid_modeling_fraction")),
                "valid_modeling_frequencies": _maybe_int(quality.get("valid_modeling_frequencies")) or len(valid_rows),
                "alignment_delta_s": _maybe_float(quality.get("alignment_delta_s")),
                **features,
                "R0_mOhm_k": None,
                "R1_mOhm_k": None,
                "r0_r1_source": "unavailable",
                "r0_r1_leakage_safe": False,
                "quality_flags": ";".join(flags) if flags else "OK",
                "schema_version": SCHEMA_VERSION,
                "feature_policy_version": FEATURE_POLICY_VERSION,
            }
        )
    table = pa.Table.from_pylist(feature_rows, schema=EIS_FEATURE_TABLE_V1_SCHEMA)
    if not validate_table(table, EIS_FEATURE_TABLE_V1_SCHEMA):
        raise ValueError("EIS feature table schema validation failed.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table.replace_schema_metadata(
            {
                b"schema_version": SCHEMA_VERSION.encode(),
                b"feature_policy_version": FEATURE_POLICY_VERSION.encode(),
                b"eis_table_path": str(eis_table_path).encode(),
                b"eis_quality_path": str(eis_quality_path).encode(),
                b"interval_table_path": str(interval_table_path).encode(),
            }
        ),
        out_path,
    )
    return table


def write_eis_feature_qa_report(
    eis_features_path: Path,
    interval_table_path: Path,
    out_path: Path,
    *,
    minimum_canonical_rows: int = 1000,
) -> dict[str, Any]:
    """Write QA for the scalar EIS feature sidecar."""
    rows = _read_parquet_rows(eis_features_path)
    metadata_by_checkup = _metadata_by_cell_checkup(_read_parquet_rows(interval_table_path))
    split_counts = _split_counts(rows, metadata_by_checkup)
    selected_frequency_missing = {
        label: sum(_maybe_float(row.get(f"freq_selected_{label}")) is None for row in rows)
        for label, _freq in SELECTED_FREQUENCIES
    }
    feature_columns = [
        field.name
        for field in EIS_FEATURE_TABLE_V1_SCHEMA
        if field.type == pa.float64() and field.name not in {"soc_percent", "temperature_C_mean"}
    ]
    feature_nan_counts = {
        column: sum(_maybe_float(row.get(column)) is None for row in rows)
        for column in feature_columns
    }
    warnings: list[str] = []
    if len(rows) < minimum_canonical_rows:
        warnings.append(f"low_canonical_feature_rows={len(rows)}")
    if any(selected_frequency_missing.values()):
        warnings.append("missing_selected_frequency_features")
    report = {
        "status": "warning" if warnings else "passed",
        "schema_version": SCHEMA_VERSION,
        "feature_policy_version": FEATURE_POLICY_VERSION,
        "generated_at_utc": _now(),
        "inputs": {"eis_features": str(eis_features_path), "interval_table": str(interval_table_path)},
        "row_count": len(rows),
        "unique_cells": len({str(row.get("cell_id")) for row in rows}),
        "unique_parameter_sets": len(
            {int(row["parameter_set"]) for row in rows if row.get("parameter_set") is not None}
        ),
        "soc_context_counts": dict(Counter(_soc_label(row.get("soc_percent")) for row in rows)),
        "temperature_context_counts": dict(Counter(str(row.get("temperature_context", "")) for row in rows)),
        "valid_modeling_fraction": _numeric_summary(
            [_as_float(row.get("valid_modeling_fraction")) for row in rows]
        ),
        "missing_selected_frequencies": selected_frequency_missing,
        "feature_nan_counts": feature_nan_counts,
        "split_coverage": split_counts,
        "warnings": warnings,
    }
    _write_json(out_path, report)
    return report


def write_eis_claim_readiness_report(
    qa_report_path: Path,
    feature_qa_report_path: Path,
    out_path: Path,
) -> str:
    """Render the EIS QA gate claim-readiness memo."""
    qa = json.loads(qa_report_path.read_text(encoding="utf-8"))
    feature_qa = json.loads(feature_qa_report_path.read_text(encoding="utf-8"))
    rows = [
        ("EIS archive/cell coverage", _status(qa.get("unique_cells") == 228), f"{qa.get('unique_cells')} cells"),
        ("Valid-frequency mask", "supported_for_qa", "0.5-5000 Hz with 100 Hz, 208.3 Hz, and 14.7 kHz excluded"),
        ("SOC/RT-OT coverage", "supported_for_qa", f"SOC counts {qa.get('soc_context_counts')} and temperature counts {qa.get('temperature_context_counts')}"),
        ("Alignment robustness", "diagnostic_only", "Alignment sensitivity is quantified before any EIS baseline."),
        ("Feature table completeness", _status(feature_qa.get("row_count", 0) > 0), f"{feature_qa.get('row_count')} canonical rows"),
        ("R0/R1 leakage safety", "diagnostic_only", "R0/R1 are unavailable in the v1 feature sidecar and remain blocked as predictive inputs until provenance is explicit."),
        ("DRT readiness", "blocked", "DRT remains blocked by policy."),
        ("Learned embedding readiness", "blocked", "Learned EIS embeddings remain blocked by policy."),
        ("EIS predictive claim status", "blocked", "No EIS predictive claim is authorized until grouped baseline evidence exists."),
    ]
    lines = [
        "# EIS Claim Readiness",
        "",
        "Milestone 2.0 opens EIS as a QA and feature-readiness data product only. It does not authorize EIS predictive modeling or EIS improvement claims.",
        "",
        "| Claim area | Status | Evidence |",
        "|---|---|---|",
    ]
    lines.extend(f"| {area} | `{status}` | {evidence} |" for area, status, evidence in rows)
    lines.extend(
        [
            "",
            "## Blocked Claims",
            "",
            "- EIS improves capacity, PULSE, calibration, ranking, or degradation prediction.",
            "- DRT features are stable enough for modeling.",
            "- Learned EIS embeddings are ready.",
            "- Capacity+PULSE+EIS multimodal modeling is authorized.",
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    out_path.write_text(text, encoding="utf-8")
    return text


def _valid_frequency_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        freq = _as_float(row.get("frequency_Hz"))
        stored = bool(row.get("is_valid_modeling_frequency"))
        policy = _policy_modeling_mask(row)
        label = _frequency_bucket(freq)
        buckets[label]["row_count"] += 1
        buckets[label]["stored_modeling_rows"] += int(stored)
        buckets[label]["policy_modeling_rows"] += int(policy)
        buckets[label]["mask_mismatch_rows"] += int(stored != policy)
    return [
        {
            "frequency_bucket": label,
            "row_count": values["row_count"],
            "stored_modeling_rows": values["stored_modeling_rows"],
            "policy_modeling_rows": values["policy_modeling_rows"],
            "mask_mismatch_rows": values["mask_mismatch_rows"],
        }
        for label, values in sorted(buckets.items())
    ]


def _coverage_rows(
    rows: list[dict[str, Any]],
    metadata_by_checkup: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for grouping, column in (
        ("soc_percent", "soc_percent"),
        ("temperature_context", "temperature_context"),
        ("cell_id", "cell_id"),
        ("checkup_k", "checkup_k"),
    ):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[_group_value(row.get(column))].append(row)
        for value, group in sorted(grouped.items()):
            output.append(_coverage_summary_row(grouping, value, group, metadata_by_checkup))
    for split in SPLIT_COLUMNS:
        grouped = defaultdict(list)
        for row in rows:
            meta = metadata_by_checkup.get((str(row.get("cell_id")), int(row.get("checkup_k"))))
            if meta and split in meta:
                grouped[_group_value(meta.get(split))].append(row)
        for value, group in sorted(grouped.items()):
            output.append(_coverage_summary_row(split, value, group, metadata_by_checkup))
    return output


def _coverage_summary_row(
    grouping: str,
    value: str,
    group: list[dict[str, Any]],
    metadata_by_checkup: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    return {
        "grouping": grouping,
        "group_value": value,
        "spectrum_count": len(group),
        "unique_cells": len({str(row.get("cell_id")) for row in group}),
        "unique_parameter_sets": len(_parameter_sets(group, metadata_by_checkup)),
        "unique_checkups": len({int(row.get("checkup_k")) for row in group}),
        "valid_modeling_fraction_median": _numeric_summary(
            [_as_float(row.get("valid_modeling_fraction")) for row in group]
        )["median"],
    }


def _write_spectrum_quality_summary(
    path: Path,
    rows: list[dict[str, Any]],
    metadata_by_checkup: dict[tuple[str, int], dict[str, Any]],
) -> None:
    summary_rows = [
        {
            "summary": "all",
            "spectrum_count": len(rows),
            "unique_cells": len({str(row.get("cell_id")) for row in rows}),
            "unique_parameter_sets": len(_parameter_sets(rows, metadata_by_checkup)),
            "valid_modeling_frequencies_median": _numeric_summary(
                [_as_float(row.get("valid_modeling_frequencies")) for row in rows]
            )["median"],
            "valid_modeling_fraction_median": _numeric_summary(
                [_as_float(row.get("valid_modeling_fraction")) for row in rows]
            )["median"],
            "alignment_delta_s_median": _numeric_summary(
                [_as_float(row.get("alignment_delta_s")) for row in rows]
            )["median"],
        }
    ]
    _write_csv(path, summary_rows)


def _selected_frequency_features(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    features: dict[str, float | None] = {}
    for label, target_freq in SELECTED_FREQUENCIES:
        nearest = _nearest_frequency_row(rows, target_freq)
        features[f"z_real_{label}"] = _maybe_float(nearest.get("z_real")) if nearest else None
        features[f"z_imag_{label}"] = _maybe_float(nearest.get("z_imag")) if nearest else None
        features[f"z_abs_{label}"] = _maybe_float(nearest.get("z_abs")) if nearest else None
        features[f"phase_{label}"] = _maybe_float(nearest.get("phase")) if nearest else None
        features[f"freq_selected_{label}"] = _maybe_float(nearest.get("frequency_Hz")) if nearest else None
    return features


def _nearest_frequency_row(rows: list[dict[str, Any]], target_freq: float) -> dict[str, Any] | None:
    tolerance = max(0.05, target_freq * 0.08)
    candidates = [
        (abs(_as_float(row.get("frequency_Hz")) - target_freq), row)
        for row in rows
        if math.isfinite(_as_float(row.get("frequency_Hz")))
    ]
    if not candidates:
        return None
    distance, row = min(candidates, key=lambda item: item[0])
    return row if distance <= tolerance else None


def _nyquist_features(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    points = [
        (_as_float(row.get("frequency_Hz")), _as_float(row.get("z_real")), _as_float(row.get("z_imag")))
        for row in rows
    ]
    points = [(freq, real, imag) for freq, real, imag in points if all(math.isfinite(v) for v in (freq, real, imag))]
    if not points:
        return {
            "nyquist_re_min": None,
            "nyquist_re_max": None,
            "nyquist_im_min": None,
            "nyquist_im_peak_abs": None,
            "nyquist_semicircle_width_proxy": None,
            "nyquist_high_freq_re_intercept_proxy": None,
            "nyquist_low_freq_tail_slope_proxy": None,
        }
    reals = [real for _freq, real, _imag in points]
    imags = [imag for _freq, _real, imag in points]
    high_freq_real = max(points, key=lambda item: item[0])[1]
    low_tail = sorted(points, key=lambda item: item[0])[:2]
    slope = None
    if len(low_tail) == 2 and abs(low_tail[1][1] - low_tail[0][1]) > 1e-12:
        slope = (low_tail[1][2] - low_tail[0][2]) / (low_tail[1][1] - low_tail[0][1])
    return {
        "nyquist_re_min": min(reals),
        "nyquist_re_max": max(reals),
        "nyquist_im_min": min(imags),
        "nyquist_im_peak_abs": max(abs(value) for value in imags),
        "nyquist_semicircle_width_proxy": max(reals) - min(reals),
        "nyquist_high_freq_re_intercept_proxy": high_freq_real,
        "nyquist_low_freq_tail_slope_proxy": slope,
    }


def _policy_modeling_mask(row: dict[str, Any]) -> bool:
    return compute_modeling_mask(
        _as_float(row.get("frequency_Hz")),
        _as_float(row.get("z_real")),
        _as_float(row.get("z_imag")),
        1 if bool(row.get("is_valid_raw")) else 0,
    )


def _metadata_by_cell_checkup(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    metadata: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        cell_id = str(row.get("cell_id"))
        for key_column in ("checkup_k", "checkup_k_next"):
            if key_column in row and row.get(key_column) is not None:
                metadata.setdefault((cell_id, int(row[key_column])), row)
    return metadata


def _parameter_sets(
    rows: list[dict[str, Any]],
    metadata_by_checkup: dict[tuple[str, int], dict[str, Any]],
) -> set[int]:
    values: set[int] = set()
    for row in rows:
        if row.get("parameter_set") is not None:
            values.add(int(row["parameter_set"]))
            continue
        meta = metadata_by_checkup.get((str(row.get("cell_id")), int(row.get("checkup_k"))))
        if meta and meta.get("parameter_set") is not None:
            values.add(int(meta["parameter_set"]))
    return values


def _split_counts(
    rows: list[dict[str, Any]],
    metadata_by_checkup: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        meta = metadata_by_checkup.get((str(row.get("cell_id")), int(row.get("checkup_k"))))
        if meta is None:
            continue
        for split in SPLIT_COLUMNS:
            if split in meta:
                counts[f"{split}={meta[split]}"] += 1
    return dict(counts)


def _spectrum_key(row: dict[str, Any]) -> tuple[str, int, float, str]:
    return (
        str(row["cell_id"]),
        int(row["checkup_k"]),
        round(_as_float(row.get("soc_percent")), 1),
        str(row.get("temperature_context", "")).upper(),
    )


def _frequency_bucket(freq: float) -> str:
    if not math.isfinite(freq):
        return "nonfinite"
    if abs(freq - 100.0) < 0.01:
        return "excluded_100Hz"
    if abs(freq - 208.3) < 0.1:
        return "excluded_208p3Hz"
    if abs(freq - 14700.0) < 10.0:
        return "excluded_14p7kHz"
    if 0.5 <= freq <= 5000.0:
        return "modeling_band_other"
    if freq < 0.5:
        return "below_0p5Hz"
    return "above_5kHz"


def _numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        return {"count": 0, "min": None, "median": None, "p95": None, "max": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "median": _percentile(finite, 0.5),
        "p95": _percentile(finite, 0.95),
        "max": finite[-1],
    }


def _percentile(sorted_values: list[float], q: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * q
    lower = math.floor(idx)
    upper = math.ceil(idx)
    if lower == upper:
        return sorted_values[lower]
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (idx - lower)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def _same_soc(value: Any, expected: float) -> bool:
    observed = _as_float(value)
    return math.isfinite(observed) and abs(observed - expected) <= 0.25


def _soc_label(value: Any) -> str:
    observed = _as_float(value)
    return "unknown" if not math.isfinite(observed) else f"{observed:g}"


def _group_value(value: Any) -> str:
    if value is None:
        return "unknown"
    numeric = _as_float(value)
    if math.isfinite(numeric):
        return f"{numeric:g}"
    text = str(value).strip()
    return text if text else "unknown"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _maybe_float(value: Any) -> float | None:
    parsed = _as_float(value)
    return parsed if math.isfinite(parsed) else None


def _maybe_int(value: Any) -> int | None:
    parsed = _as_float(value)
    return int(parsed) if math.isfinite(parsed) else None


def _status(condition: bool) -> str:
    return "supported_for_qa" if condition else "partially_supported"


def _now() -> str:
    return datetime.now(UTC).isoformat()
