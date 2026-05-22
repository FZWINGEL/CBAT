"""Command-line interface for Multimodal Battery Prediction."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from mbp.audit.coverage import build_modality_coverage, write_modality_coverage
from mbp.audit.inventory import build_inventory
from mbp.audit.known_issues import build_known_issue_checks, write_known_issue_checks
from mbp.audit.manifest import build_manifest
from mbp.audit.reports import write_evidence_memo
from mbp.audit.writers import write_file_inventory, write_manifest_json, write_sha256_manifest

app = typer.Typer(help="Multimodal Battery Prediction research tooling.")
audit_app = typer.Typer(help="Gate 1 dataset audit and provenance commands.")
report_app = typer.Typer(help="Report generation commands.")
ingest_app = typer.Typer(help="Gate 2 result-data ingestion commands.")
split_app = typer.Typer(help="Reproducible dataset splitting commands.")
baseline_app = typer.Typer(help="Milestone 0.5 baseline commands.")
features_app = typer.Typer(help="Milestone 0.6 scalar feature-engineering commands.")

app.add_typer(audit_app, name="audit")
app.add_typer(report_app, name="report")
app.add_typer(ingest_app, name="ingest")
app.add_typer(split_app, name="split")
app.add_typer(baseline_app, name="baseline")
app.add_typer(features_app, name="features")


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_gate2_reports(report_dir: Path) -> dict[str, object]:
    reports: dict[str, object] = {}
    interval_report = _load_optional_json(report_dir / "interval_qa_report.json")
    if interval_report:
        reports["interval_qa"] = interval_report
    split_report = _load_optional_json(report_dir / "split_registry_report.json")
    if split_report:
        reports["split_registry"] = split_report
    interval_subset_report = _load_optional_json(report_dir / "interval_subset_report.json")
    if interval_subset_report:
        reports["interval_subset"] = interval_subset_report

    try:
        import pyarrow.parquet as pq

        monotonicity_path = report_dir / "log_age_monotonicity_violations.parquet"
        if monotonicity_path.exists():
            reports["log_age_monotonicity"] = {
                "path": str(monotonicity_path),
                "row_count": pq.ParquetFile(monotonicity_path).metadata.num_rows,
                "summary_lines": _line_count(report_dir / "log_age_monotonicity_summary.csv"),
            }
        raw_inventory_path = report_dir / "raw_log_archive_inventory.parquet"
        if raw_inventory_path.exists():
            raw_table = pq.read_table(
                raw_inventory_path,
                columns=["sampled_header", "cell_id", "pool_logs_exist", "slave_logs_exist"],
            )
            sampled_headers = [
                value for value in raw_table.column("sampled_header").to_pylist() if value
            ]
            reports["raw_log_inventory"] = {
                "path": str(raw_inventory_path),
                "row_count": raw_table.num_rows,
                "unique_cells": len(
                    {value for value in raw_table.column("cell_id").to_pylist() if value}
                ),
                "sampled_header_available": bool(sampled_headers),
            }
    except Exception:
        pass
    return reports


def _line_count(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


@audit_app.command("inventory")
def audit_inventory(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        exists=False,
        file_okay=False,
        dir_okay=True,
        help="Local dataset root to inspect. It may be absent before download.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output file path ending in .csv or .parquet.",
    ),
) -> None:
    """Write a file inventory with SHA-256 hashes and provenance fields."""

    records = build_inventory(data_root)
    write_file_inventory(records, out)
    typer.echo(f"Wrote {len(records)} file inventory records to {out}")


@audit_app.command("bagit")
def audit_bagit(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        help="Local dataset root to inspect.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path to save the BagIt validation report.",
    ),
) -> None:
    """Validate BagIt container integrity (payload and tag manifest files)."""
    from mbp.audit.bagit import validate_bagit

    result = validate_bagit(data_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    if result["status"] == "passed":
        typer.echo(
            f"BagIt validation PASSED. Checked {len(result['validated_files'])} files. Report written to {out}"
        )
    else:
        typer.echo(
            f"BagIt validation FAILED with {len(result['errors'])} errors. Report written to {out}"
        )


@audit_app.command("archives")
def audit_archives(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        help="Local dataset root containing zip archives.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path ending in .csv or .parquet.",
    ),
) -> None:
    """Inspect zip archives and inventory their members without extraction."""
    from mbp.audit.archives import (
        inventory_zip_archives,
        print_archive_summary,
        write_archive_inventory,
    )

    records = inventory_zip_archives(data_root)
    write_archive_inventory(records, out)
    print_archive_summary(records)
    typer.echo(f"Wrote {len(records)} archive inventory records to {out}")


@audit_app.command("coverage")
def audit_coverage(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        help="Local dataset root.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output CSV path.",
    ),
) -> None:
    """Audit cells and replicates coverage for diagnostic modalities."""
    from mbp.audit.coverage import build_modality_coverage, write_modality_coverage
    from mbp.audit.inventory import build_inventory, utc_now_iso

    generated_at_utc = utc_now_iso()
    file_records = build_inventory(data_root, generated_at_utc=generated_at_utc)
    records = build_modality_coverage(file_records, generated_at_utc)
    write_modality_coverage(records, out)

    typer.echo("=== Modality Coverage Summary ===")
    for r in records:
        if r.modality in ("cfg", "eoc", "eis", "pulse"):
            typer.echo(
                f"  {r.modality}: {r.observed_cells}/{r.expected_cells} cells ({r.coverage_ratio * 100:.1f}%) - status: {r.status}"
            )
    typer.echo(f"Wrote modality coverage to {out}")


@audit_app.command("manifest")
def audit_manifest(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        exists=False,
        file_okay=False,
        dir_okay=True,
        help="Local dataset root to inspect. It may be absent before download.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path, conventionally DATASET_MANIFEST.json.",
    ),
    sha256_out: Path | None = typer.Option(
        None,
        "--sha256-out",
        help="Optional MANIFEST.sha256 output path. Defaults beside --out.",
    ),
    coverage_out: Path | None = typer.Option(
        None,
        "--coverage-out",
        help="Optional modality_coverage.csv output path. Defaults beside --out.",
    ),
    known_issues_out: Path | None = typer.Option(
        None,
        "--known-issues-out",
        help="Optional known_issues.csv output path. Defaults beside --out.",
    ),
    evidence_memo_out: Path | None = typer.Option(
        None,
        "--evidence-memo-out",
        help="Optional generated dataset evidence memo path. Defaults beside --out.",
    ),
) -> None:
    """Write a dataset manifest and Gate 1 audit sidecars from observed evidence."""

    manifest = build_manifest(data_root)
    write_manifest_json(manifest, out)
    generated_at_utc = manifest.provenance.generated_at_utc
    coverage = build_modality_coverage(manifest.file_inventory, generated_at_utc)
    known_issues = build_known_issue_checks(manifest.file_inventory, generated_at_utc)

    sha256_path = sha256_out or out.parent / "MANIFEST.sha256"
    coverage_path = coverage_out or out.parent / "modality_coverage.csv"
    known_issues_path = known_issues_out or out.parent / "known_issues.csv"
    evidence_memo_path = evidence_memo_out or out.parent / "dataset_evidence_memo.md"

    write_sha256_manifest(manifest.file_inventory, sha256_path)
    write_modality_coverage(coverage, coverage_path)
    write_known_issue_checks(known_issues, known_issues_path)

    # If sidecar reports were already generated, include them in the rendered memo.
    bagit_report = _load_optional_json(out.parent / "bagit_validation.json")
    qa_report = _load_optional_json(out.parent / "qa_report.json")
    gate2_reports = _load_gate2_reports(out.parent)

    write_evidence_memo(
        manifest,
        coverage,
        known_issues,
        evidence_memo_path,
        bagit_report=bagit_report,
        qa_report=qa_report,
        gate2_reports=gate2_reports,
    )

    typer.echo(f"Wrote dataset manifest with {manifest.file_count} files to {out}")
    typer.echo(f"Wrote SHA-256 manifest to {sha256_path}")
    typer.echo(f"Wrote modality coverage to {coverage_path}")
    typer.echo(f"Wrote known-issue checks to {known_issues_path}")
    typer.echo(f"Wrote evidence memo to {evidence_memo_path}")


@audit_app.command("collection")
def audit_collection(
    config: Path = typer.Option(
        ...,
        "--config",
        help="Path to the collection configuration YAML file.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for the collection manifest.",
    ),
    result_root: Path | None = typer.Option(
        None,
        "--result-root",
        help="Optional override path for the Result package root.",
    ),
    log_root: Path | None = typer.Option(
        None,
        "--log-root",
        help="Optional override path for the Log package root.",
    ),
) -> None:
    """Audit a multi-package dataset collection and write a unified manifest."""
    from mbp.audit.collection import build_collection_manifest

    manifest = build_collection_manifest(config, result_root=result_root, log_root=log_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    typer.echo(f"Wrote unified collection manifest to {out}")


@report_app.command("evidence-memo")
def report_evidence_memo(
    manifest_path: Path = typer.Option(
        ...,
        "--manifest",
        help="Path to DATASET_MANIFEST.json.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output markdown path, conventionally dataset_evidence_memo.md.",
    ),
) -> None:
    """Generate or update the dataset evidence memo from an existing DATASET_MANIFEST.json."""
    if not manifest_path.exists():
        typer.echo(f"Manifest not found: {manifest_path}")
        raise typer.Exit(code=1)

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Reconstruct provenance
    prov_data = data["provenance"]
    from mbp.audit.models import Provenance

    provenance = Provenance(
        schema_version=prov_data["schema_version"],
        generated_at_utc=prov_data["generated_at_utc"],
        tool_name=prov_data["tool_name"],
        tool_version=prov_data["tool_version"],
        data_root_input=prov_data["data_root_input"],
        data_root_exists=prov_data["data_root_exists"],
        preprocessing_commit=prov_data.get("preprocessing_commit"),
    )

    manifest = build_manifest(Path(provenance.data_root_input))
    coverage = build_modality_coverage(manifest.file_inventory, provenance.generated_at_utc)
    known_issues = build_known_issue_checks(manifest.file_inventory, provenance.generated_at_utc)

    # Try to load sidecar reports if they exist beside the manifest.
    bagit_report = _load_optional_json(manifest_path.parent / "bagit_validation.json")
    qa_report = _load_optional_json(manifest_path.parent / "qa_report.json")
    gate2_reports = _load_gate2_reports(manifest_path.parent)

    write_evidence_memo(
        manifest,
        coverage,
        known_issues,
        out,
        bagit_report=bagit_report,
        qa_report=qa_report,
        gate2_reports=gate2_reports,
    )
    typer.echo(f"Generated dataset evidence memo at {out}")


@ingest_app.command("run-pipeline")
def ingest_run_pipeline(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        help="Local dataset root directory containing raw zip files.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Output directory to save interim Parquet files.",
    ),
    exclusions_report: Path | None = typer.Option(
        None,
        "--exclusions-report",
        help="Optional path to output the excluded records report (CSV).",
    ),
) -> None:
    """Run the complete Gate 2 result-data ingestion pipeline (CFG -> EOC -> PULSE -> EIS)."""
    if not data_root.exists():
        typer.echo(f"Data root directory does not exist: {data_root}")
        raise typer.Exit(code=1)

    def find_zip(root: Path, pattern: str) -> Path | None:
        for path in root.rglob(pattern):
            if path.is_file():
                return path
        return None

    cfg_zip = find_zip(data_root, "cfg.zip")
    eoc_zip = find_zip(data_root, "cell_eocv2.zip")
    pulse_zip = find_zip(data_root, "cell_plsv2.zip")
    eis_zip = find_zip(data_root, "cell_eisv2.zip")

    if not cfg_zip:
        typer.echo("Error: cfg.zip not found in data-root!")
        raise typer.Exit(code=1)
    if not eoc_zip:
        typer.echo("Error: cell_eocv2.zip not found in data-root!")
        raise typer.Exit(code=1)
    if not pulse_zip:
        typer.echo("Error: cell_plsv2.zip not found in data-root!")
        raise typer.Exit(code=1)
    if not eis_zip:
        typer.echo("Error: cell_eisv2.zip not found in data-root!")
        raise typer.Exit(code=1)

    # Output dir setup
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg_parquet = out_dir / "cell_condition_table.parquet"
    eoc_parquet = out_dir / "checkup_event_table.parquet"
    pulse_raw_parquet = out_dir / "modality_table_pulse_raw.parquet"
    pulse_sum_parquet = out_dir / "modality_table_pulse_summary.parquet"
    eis_parquet = out_dir / "modality_table_eis.parquet"
    eis_qual_parquet = out_dir / "eis_spectrum_quality.parquet"

    # Ingest CFG
    typer.echo("Ingesting CFG (condition metadata)...")
    from mbp.data.luh_blank.parse_cfg import ingest_cfg

    ingest_cfg(cfg_zip, cfg_parquet, exclusions_path=exclusions_report)
    typer.echo(f"  Wrote {cfg_parquet}")

    # Ingest EOC
    typer.echo("Ingesting EOC (capacity check-ups)...")
    from mbp.data.luh_blank.parse_eoc import ingest_eoc

    ingest_eoc(eoc_zip, eoc_parquet, exclusions_path=exclusions_report)
    typer.echo(f"  Wrote {eoc_parquet}")

    # Ingest PULSE
    typer.echo("Ingesting PULSE (resistance diagnostics)...")
    from mbp.data.luh_blank.parse_pulse import ingest_pulse

    ingest_pulse(
        pulse_zip,
        eoc_parquet,
        pulse_raw_parquet,
        pulse_sum_parquet,
        exclusions_path=exclusions_report,
    )
    typer.echo(f"  Wrote {pulse_raw_parquet} and {pulse_sum_parquet}")

    # Ingest EIS
    typer.echo("Ingesting EIS (impedance spectra)...")
    from mbp.data.luh_blank.parse_eis import ingest_eis

    ingest_eis(
        eis_zip,
        eoc_parquet,
        eis_parquet,
        eis_qual_parquet,
        exclusions_path=exclusions_report,
    )
    typer.echo(f"  Wrote {eis_parquet} and {eis_qual_parquet}")

    typer.echo("Ingestion pipeline successfully completed!")


@ingest_app.command("qa")
def ingest_qa(
    interim_dir: Path = typer.Option(
        ...,
        "--interim-dir",
        help="Directory containing the interim Parquet data products.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for the structured JSON QA report.",
    ),
) -> None:
    """Run diagnostic QA checks on all ingested interim Parquet data products."""
    from mbp.data.luh_blank.qa_result_data import run_qa_checks

    typer.echo(f"Running quality assurance checks on Parquet files in {interim_dir}...")
    report = run_qa_checks(interim_dir, out)

    typer.echo("=== QA Audit Results ===")
    typer.echo(f"Status: {report['status'].upper()}")
    for table_name, meta in report["tables"].items():
        if meta.get("exists"):
            typer.echo(f"  {table_name}: OK ({meta['row_count']} rows, schema validated)")
        else:
            typer.echo(f"  {table_name}: MISSING")

    if report["status"] == "failed":
        typer.echo("\nFailures detected:")
        for failure in report["failures"]:
            typer.echo(f"  - {failure}")
        raise typer.Exit(code=1)
    else:
        typer.echo("\nAll quality gates passed successfully!")


@ingest_app.command("log-age")
def ingest_log_age_cmd(
    archive: Path = typer.Option(
        ...,
        "--archive",
        help="Path to the cell_log_age_ultracompr.7z archive.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Output directory to save the interim modality_table_log_age.parquet.",
    ),
    exclusions_report: Path | None = typer.Option(
        None,
        "--exclusions-report",
        help="Optional path to output the excluded records report (CSV).",
    ),
    skip_extract: bool = typer.Option(
        False,
        "--skip-extract",
        help="Skip extraction if CSV files are already present in the temp directory.",
    ),
    csv_block_size_bytes: int = typer.Option(
        1 << 20,
        "--csv-block-size-bytes",
        min=1,
        help="Maximum PyArrow CSV stream block size. Lower values reduce peak memory.",
    ),
) -> None:
    """Ingest cell operating logs from cell_log_age_ultracompr.7z into interim Parquet."""
    import pyarrow.parquet as pq

    from mbp.data.luh_blank.parse_log import ingest_log_age

    typer.echo(
        "Ingesting LOG_AGE data from "
        f"{archive} (skip_extract={skip_extract}, csv_block_size_bytes={csv_block_size_bytes})..."
    )
    ingest_log_age(
        archive,
        out_dir,
        exclusions_report_path=exclusions_report,
        skip_extract=skip_extract,
        csv_block_size_bytes=csv_block_size_bytes,
    )
    parquet_out = out_dir / "modality_table_log_age.parquet"
    row_count = pq.ParquetFile(parquet_out).metadata.num_rows
    typer.echo(
        f"LOG_AGE ingestion complete: {row_count} rows written to {parquet_out}"
    )


@ingest_app.command("intervals")
def ingest_intervals(
    interim_dir: Path = typer.Option(
        ...,
        "--interim-dir",
        help="Directory containing Gate 2 interim Parquet data products.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for interval_table.parquet.",
    ),
    monotonicity_violations: Path | None = typer.Option(
        None,
        "--monotonicity-violations",
        help="Optional LOG_AGE monotonicity violation detail Parquet to map onto intervals.",
    ),
) -> None:
    """Build the Gate 2 interval table from check-up events and LOG_AGE exposure."""
    from mbp.data.products.interval_table import build_interval_table

    typer.echo(f"Building interval table from interim products in {interim_dir}...")
    table = build_interval_table(
        interim_dir, out, monotonicity_violations_path=monotonicity_violations
    )
    typer.echo(f"Interval table generated: {len(table)} rows written to {out}")


@ingest_app.command("intervals-qa")
def ingest_intervals_qa(
    interval_table: Path = typer.Option(
        ...,
        "--interval-table",
        help="Path to interval_table.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for interval QA report.",
    ),
    checkup_table: Path | None = typer.Option(
        None,
        "--checkup-table",
        help="Optional path to checkup_event_table.parquet. Defaults beside interval table.",
    ),
) -> None:
    """Run QA checks on the Gate 2 interval table."""
    from mbp.data.products.interval_table import run_interval_qa

    report = run_interval_qa(interval_table, out, checkup_table_path=checkup_table)
    typer.echo(f"Interval QA {report['status']}: wrote {out}")
    if report["status"] == "failed":
        raise typer.Exit(code=1)


@features_app.command("build-stress")
def features_build_stress(
    interim_dir: Path = typer.Option(
        ...,
        "--interim-dir",
        help="Directory containing Gate 2 interim Parquet data products.",
    ),
    interval_table: Path = typer.Option(
        ...,
        "--interval-table",
        help="Path to interval_table.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for interval_stress_features_v1_1.parquet.",
    ),
    current_sign_report: Path | None = typer.Option(
        None,
        "--current-sign-report",
        help="Optional current_sign_audit_report.json for sign-policy metadata.",
    ),
) -> None:
    """Build scalar LOG_AGE stress features for interval capacity baselines."""
    from mbp.data.products.stress_features import build_interval_stress_features

    typer.echo(f"Building interval stress features from {interval_table}...")
    table = build_interval_stress_features(
        interim_dir,
        interval_table,
        out,
        current_sign_report_path=current_sign_report,
    )
    typer.echo(f"Stress-feature table generated: {len(table)} rows written to {out}")


@features_app.command("stress-qa")
def features_stress_qa(
    stress_features: Path = typer.Option(
        ...,
        "--stress-features",
        help="Path to interval_stress_features_v1_1.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for stress-feature QA report.",
    ),
    interval_table: Path | None = typer.Option(
        None,
        "--interval-table",
        help="Optional interval table path. Defaults beside the stress-feature table.",
    ),
) -> None:
    """Run QA checks on the scalar LOG_AGE stress-feature sidecar."""
    from mbp.data.products.stress_features import run_stress_feature_qa

    report = run_stress_feature_qa(
        stress_features,
        out,
        interval_table_path=interval_table,
    )
    typer.echo(f"Stress-feature QA {report['status']}: wrote {out}")
    if report["status"] == "failed":
        raise typer.Exit(code=1)


@features_app.command("current-sign-audit")
def features_current_sign_audit(
    log_age: Path = typer.Option(
        ...,
        "--log-age",
        help="Path to modality_table_log_age.parquet.",
    ),
    interval_table: Path = typer.Option(
        ...,
        "--interval-table",
        help="Path to interval_table.parquet for cohort cell filtering.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for current-sign audit evidence.",
    ),
    max_row_groups: int | None = typer.Option(
        None,
        "--max-row-groups",
        help="Optional bounded row-group count for smoke tests.",
    ),
) -> None:
    """Audit LOG_AGE current-sign convention using voltage/SOC derivatives."""
    from mbp.data.products.current_sign_audit import audit_current_sign

    report = audit_current_sign(
        log_age,
        interval_table,
        out,
        max_row_groups=max_row_groups,
    )
    typer.echo(
        "Current-sign audit "
        f"{report['current_sign_convention']} ({report['confidence']}): wrote {out}"
    )


@split_app.command("generate")
def split_generate(
    condition_table: Path = typer.Option(
        ...,
        "--condition-table",
        help="Path to cell_condition_table.parquet.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Output directory for split_registry_v1.parquet.",
    ),
) -> None:
    """Generate the deterministic, condition-grouped split registry."""
    from mbp.data.splitting import generate_split_registry

    typer.echo(f"Generating split registry from {condition_table}...")
    table = generate_split_registry(condition_table, out_dir)
    typer.echo(f"Split registry generated: {len(table)} rows written to {out_dir / 'split_registry_v1.parquet'}")


@split_app.command("interval-subsets")
def split_interval_subsets(
    interval_table: Path = typer.Option(
        ...,
        "--interval-table",
        help="Path to interval_table.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output path for interval_subset_registry_v1.parquet.",
    ),
    report: Path = typer.Option(
        ...,
        "--report",
        help="Output JSON path for interval subset policy report.",
    ),
    efc_jitter_threshold: float = typer.Option(
        0.00025,
        "--efc-jitter-threshold",
        min=0.0,
        help="EFC drop threshold treated as small LOG_AGE jitter.",
    ),
) -> None:
    """Generate strict/tolerant interval subset labels for baseline readiness."""
    from mbp.data.products.interval_subsets import build_interval_subset_registry

    table = build_interval_subset_registry(
        interval_table,
        out,
        report,
        efc_jitter_threshold=efc_jitter_threshold,
    )
    typer.echo(f"Interval subset registry generated: {len(table)} rows written to {out}")


@baseline_app.command("run-capacity")
def baseline_run_capacity(
    interval_table: Path = typer.Option(
        ...,
        "--interval-table",
        help="Path to interval_table.parquet.",
    ),
    interval_subsets: Path = typer.Option(
        ...,
        "--interval-subsets",
        help="Path to interval_subset_registry_v1.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for capacity baseline metrics.",
    ),
    predictions_out: Path = typer.Option(
        ...,
        "--predictions-out",
        help="Output Parquet path for row-level predictions.",
    ),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1.parquet sidecar for F5-F7 groups.",
    ),
    report_dir: Path | None = typer.Option(
        None,
        "--report-dir",
        help="Optional directory for leaderboard, summary, cards, and plot CSVs.",
    ),
    subset: str = typer.Option(
        "baseline_clean_tolerant",
        "--subset",
        help="Interval subset flag to use as the primary baseline population.",
    ),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(
        10,
        "--hgb-max-iter",
        min=1,
        help="Maximum iterations for HistGradientBoosting baseline models.",
    ),
    model_levels: str = typer.Option(
        "L0_persistence,L1_ridge,L2_hist_gradient_boosting,L3_quantile_hist_gradient_boosting",
        "--model-levels",
        help="Comma-separated model levels to run.",
    ),
    feature_groups: str = typer.Option(
        "F0_time_only,F1_state_time,F2_state_exposure,F3_state_nominal,F4_state_log_age_scalar",
        "--feature-groups",
        help="Comma-separated feature groups for L1-L3 models.",
    ),
    targets: str = typer.Option(
        "capacity_Ah_k1,delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets to run.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split columns to evaluate.",
    ),
) -> None:
    """Run the first L0-L3 scalar capacity baseline ladder."""
    from mbp.baselines.capacity import run_capacity_baselines

    try:
        report = run_capacity_baselines(
            interval_table,
            interval_subsets,
            out,
            predictions_out,
            stress_features_path=stress_features,
            report_dir=report_dir,
            subset=subset,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            model_levels=_comma_values(model_levels),
            feature_groups=_comma_values(feature_groups),
            targets=_comma_values(targets),
            split_views=_comma_values(split_views),
        )
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Capacity baseline report generated: "
        f"{len(report['metrics'])} metric rows written to {out}"
    )


@baseline_app.command("diagnose-capacity")
def baseline_diagnose_capacity(
    report: Path = typer.Option(
        ...,
        "--report",
        help="Path to an existing capacity baseline JSON report.",
    ),
    reference_report: Path | None = typer.Option(
        None,
        "--reference-report",
        help="Optional capacity baseline report containing L0_persistence reference rows.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Directory for diagnostics markdown and plot-ready CSVs.",
    ),
) -> None:
    """Generate Milestone 0.5b diagnostics from a capacity baseline report."""
    from mbp.baselines.capacity import diagnose_capacity_report

    diagnose_capacity_report(report, out_dir, reference_report_path=reference_report)
    typer.echo(f"Capacity baseline diagnostics written to {out_dir}")


@baseline_app.command("diagnose-stress-features")
def baseline_diagnose_stress_features(
    report: Path = typer.Option(
        ...,
        "--report",
        help="Path to a stress-feature capacity baseline JSON report.",
    ),
    baseline_report: Path = typer.Option(
        ...,
        "--baseline-report",
        help="Path to the HGB-50 F4 baseline report for stress-feature comparison.",
    ),
    l0_reference_report: Path = typer.Option(
        ...,
        "--l0-reference-report",
        help="Path to a report containing L0_persistence reference rows.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Directory for stress-feature diagnostics markdown and CSVs.",
    ),
) -> None:
    """Generate Milestone 0.6 diagnostics for stress-feature capacity baselines."""
    from mbp.baselines.capacity import diagnose_stress_feature_report

    diagnose_stress_feature_report(report, baseline_report, l0_reference_report, out_dir)
    typer.echo(f"Stress-feature diagnostics written to {out_dir}")


@baseline_app.command("diagnose-target-consistency")
def baseline_diagnose_target_consistency(
    report: Path = typer.Option(
        ...,
        "--report",
        help="Path to a capacity baseline JSON report.",
    ),
    predictions: Path = typer.Option(
        ...,
        "--predictions",
        help="Path to the matching row-level prediction Parquet.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--out-dir",
        help="Directory for target-consistency and C-rate failure diagnostics.",
    ),
) -> None:
    """Generate Milestone 0.6.2 target-consistency diagnostics."""
    from mbp.baselines.capacity import diagnose_target_consistency_report

    diagnose_target_consistency_report(report, predictions, out_dir)
    typer.echo(f"Target-consistency diagnostics written to {out_dir}")


def _comma_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@audit_app.command("report")
def audit_report(
    manifest: Path = typer.Option(
        ...,
        "--manifest",
        help="Path to DATASET_COLLECTION_MANIFEST.json.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output markdown path for the evidence memo.",
    ),
) -> None:
    """Auto-compile the Dataset Evidence Memo from a collection manifest."""
    if not manifest.exists():
        typer.echo(f"Collection manifest not found: {manifest}")
        raise typer.Exit(code=1)

    with manifest.open("r", encoding="utf-8") as f:
        collection = json.load(f)

    # Extract result package info to build the primary manifest
    result_pkg = collection.get("packages", {}).get("result_package", {})
    result_path_str = result_pkg.get("path")

    if not (result_path_str and Path(result_path_str).exists()):
        typer.echo(f"Result package path not found or does not exist: {result_path_str}")
        raise typer.Exit(code=1)

    manifest_obj = build_manifest(Path(result_path_str))
    generated_at_utc = manifest_obj.provenance.generated_at_utc

    # Merge log package file inventory if available
    all_files = list(manifest_obj.file_inventory)
    log_pkg = collection.get("packages", {}).get("log_package", {})
    log_path_str = log_pkg.get("path")
    if log_path_str and Path(log_path_str).exists() and Path(log_path_str).is_dir():
        log_files = build_inventory(Path(log_path_str), generated_at_utc=generated_at_utc)
        all_files.extend(log_files)
        typer.echo(f"Merged {len(log_files)} log package files into coverage assessment.")

    coverage = build_modality_coverage(all_files, generated_at_utc)
    known_issues = build_known_issue_checks(all_files, generated_at_utc)

    # Try to load existing sidecar reports
    bagit_report = _load_optional_json(manifest.parent / "bagit_validation.json")
    qa_report = _load_optional_json(manifest.parent / "qa_report.json")
    gate2_reports = _load_gate2_reports(manifest.parent)

    write_evidence_memo(
        manifest_obj,
        coverage,
        known_issues,
        out,
        bagit_report=bagit_report,
        qa_report=qa_report,
        gate2_reports=gate2_reports,
    )
    typer.echo(f"Evidence memo compiled and written to {out}")


@audit_app.command("log-age-monotonicity")
def audit_log_age_monotonicity(
    log_age: Path = typer.Option(
        ...,
        "--log-age",
        help="Path to modality_table_log_age.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output Parquet path for monotonicity violation details.",
    ),
    summary: Path = typer.Option(
        ...,
        "--summary",
        help="Output CSV path for per-cell and per-source-file summaries.",
    ),
    timestamp_epsilon_s: float = typer.Option(
        0.0,
        "--timestamp-epsilon-s",
        min=0.0,
        help="Allowed timestamp decrease tolerance in seconds.",
    ),
    efc_epsilon: float = typer.Option(
        1e-9,
        "--efc-epsilon",
        min=0.0,
        help="Allowed EFC decrease tolerance.",
    ),
    workers: int | None = typer.Option(
        None,
        "--workers",
        min=1,
        help="PyArrow reader threads for streaming LOG_AGE batches. Defaults to min(cpu_count, 10).",
    ),
    batch_size_rows: int = typer.Option(
        1_048_576,
        "--batch-size-rows",
        min=1,
        help="Rows per streamed LOG_AGE batch. Larger values reduce overhead but use more memory.",
    ),
) -> None:
    """Classify LOG_AGE timestamp/EFC monotonicity violations."""
    from mbp.audit.log_age_monotonicity import write_log_age_monotonicity_report

    report = write_log_age_monotonicity_report(
        log_age,
        out,
        summary,
        timestamp_epsilon_s=timestamp_epsilon_s,
        efc_epsilon=efc_epsilon,
        workers=workers,
        batch_size_rows=batch_size_rows,
    )
    typer.echo(
        "LOG_AGE monotonicity audit complete: "
        f"{report['violation_count']} violations, "
        f"{report['cells_with_violations']} cells, "
        f"{report['source_files_with_violations']} source files."
    )
    top = report.get("top_20_worst", [])
    if top:
        typer.echo("Top violations:")
        for row in top[:20]:
            typer.echo(
                "  "
                f"{row['cell_id']} {row['violation_type']} "
                f"dt={row['delta_timestamp_s']} dEFC={row['delta_EFC']} "
                f"row_group={row['row_group_idx']} local_row={row['local_row_idx']}"
            )


@audit_app.command("split-registry")
def audit_split_registry_cmd(
    split_registry: Path = typer.Option(
        ...,
        "--split-registry",
        help="Path to split_registry_v1.parquet.",
    ),
    condition_table: Path = typer.Option(
        ...,
        "--condition-table",
        help="Path to cell_condition_table.parquet.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output JSON path for split registry audit report.",
    ),
) -> None:
    """Audit grouped split registry semantics and OOD fold coverage."""
    from mbp.data.splitting import audit_split_registry

    report = audit_split_registry(split_registry, condition_table, out)
    typer.echo(f"Split registry audit {report['status']}: wrote {out}")
    if report["status"] == "failed":
        raise typer.Exit(code=1)


@audit_app.command("raw-log-archives")
def audit_raw_log_archives(
    data_root: Path = typer.Option(
        ...,
        "--data-root",
        help="Raw Log_Raw_Data_Version_2 root.",
    ),
    out: Path = typer.Option(
        ...,
        "--out",
        help="Output Parquet path for raw LOG archive inventory.",
    ),
) -> None:
    """Inventory raw LOG archives without full parsing."""
    from mbp.audit.raw_log_archives import inventory_raw_log_archives

    table = inventory_raw_log_archives(data_root, out)
    typer.echo(f"Raw LOG archive inventory written: {len(table)} rows to {out}")


if __name__ == "__main__":
    app()
