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
pulse_app = typer.Typer(help="Milestone 0.7 PULSE QA and target commands.")
coupling_app = typer.Typer(help="Milestone 0.8 coupling diagnostics commands.")
eis_app = typer.Typer(help="Milestone 2.0 EIS QA and feature-gate commands.")
analysis_app = typer.Typer(help="Analysis and uncertainty diagnostic commands.")

app.add_typer(audit_app, name="audit")
app.add_typer(report_app, name="report")
app.add_typer(ingest_app, name="ingest")
app.add_typer(split_app, name="split")
app.add_typer(baseline_app, name="baseline")
app.add_typer(features_app, name="features")
app.add_typer(pulse_app, name="pulse")
app.add_typer(coupling_app, name="coupling")
app.add_typer(eis_app, name="eis")
app.add_typer(analysis_app, name="analysis")


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


@report_app.command("build-manuscript-assets")
def report_build_manuscript_assets(
    out_dir: Path = typer.Option(
        Path("manuscript"),
        "--out-dir",
        help="Manuscript directory where generated assets and the latest continuous draft are written.",
    ),
    reports_dir: Path = typer.Option(
        Path("reports"),
        "--reports-dir",
        help="Reports directory containing tracked synthesis artifacts.",
    ),
    docs_dir: Path = typer.Option(
        Path("docs"),
        "--docs-dir",
        help="Documentation directory containing claim ledgers and status files.",
    ),
) -> None:
    """Build manuscript figures, tables, captions, checks, and the latest continuous draft."""
    from mbp.reporting import build_manuscript_assets

    result = build_manuscript_assets(out_dir=out_dir, reports_dir=reports_dir, docs_dir=docs_dir)
    typer.echo(
        "Manuscript assets generated: "
        f"{len(result['figures'])} figures, {len(result['tables'])} tables, "
        f"status={result['status']}"
    )
    if result["status"] != "passed":
        raise typer.Exit(code=1)


@report_app.command("check-manuscript")
def report_check_manuscript(
    manuscript: Path = typer.Option(
        ...,
        "--manuscript",
        help="Continuous manuscript markdown file to check.",
    ),
    claim_ledger: Path = typer.Option(
        ...,
        "--claim-ledger",
        help="Paper claim ledger markdown file.",
    ),
    traceability: Path = typer.Option(
        ...,
        "--traceability",
        help="Manuscript source traceability markdown file.",
    ),
) -> None:
    """Check a manuscript draft for claim IDs, callouts, and blocked wording."""
    from mbp.reporting import check_manuscript

    result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=claim_ledger,
        traceability=traceability,
    )
    typer.echo(f"Manuscript check {result['status']}: {manuscript}")
    for warning in result["warnings"]:
        typer.echo(f"warning: {warning}")
    for failure in result["failures"]:
        typer.echo(f"failure: {failure}")
    if result["status"] != "passed":
        raise typer.Exit(code=1)


@report_app.command("check-reader-manuscript")
def report_check_reader_manuscript(
    manuscript: Path = typer.Option(
        ...,
        "--manuscript",
        help="Reader-facing manuscript markdown file to check.",
    ),
    claim_ledger: Path = typer.Option(
        ...,
        "--claim-ledger",
        help="Paper claim ledger markdown file.",
    ),
    traceability: Path = typer.Option(
        ...,
        "--traceability",
        help="Reader manuscript source traceability markdown file.",
    ),
) -> None:
    """Check a reader-facing manuscript for internal scaffolding and blocked wording."""
    from mbp.reporting import check_reader_manuscript

    result = check_reader_manuscript(
        manuscript=manuscript,
        claim_ledger=claim_ledger,
        traceability=traceability,
    )
    typer.echo(f"Reader manuscript check {result['status']}: {manuscript}")
    for warning in result["warnings"]:
        typer.echo(f"warning: {warning}")
    for failure in result["failures"]:
        typer.echo(f"failure: {failure}")
    if result["status"] != "passed":
        raise typer.Exit(code=1)


@report_app.command("check-release-candidate")
def report_check_release_candidate(
    claim_ledger: Path = typer.Option(
        Path("docs/MAIN_PROJECT_CLAIM_LEDGER_V2.md"),
        "--claim-ledger",
        help="Main-project v2 claim ledger markdown file.",
    ),
    claim_matrix: Path = typer.Option(
        Path("reports/synthesis/main_project_claim_matrix_v2.csv"),
        "--claim-matrix",
        help="Main-project v2 claim matrix CSV.",
    ),
    artifact_manifest: Path = typer.Option(
        Path("reports/synthesis/artifact_manifest_v2.csv"),
        "--artifact-manifest",
        help="Benchmark release artifact manifest CSV.",
    ),
    repo_status: Path = typer.Option(
        Path("docs/REPO_STATUS.md"),
        "--repo-status",
        help="Repository status markdown file.",
    ),
    agents: Path = typer.Option(
        Path("AGENTS.md"),
        "--agents",
        help="AGENTS.md workflow file.",
    ),
    runbook: Path = typer.Option(
        Path("docs/BENCHMARK_RUNBOOK.md"),
        "--runbook",
        help="Benchmark runbook markdown file.",
    ),
    command_dag: Path = typer.Option(
        Path("docs/COMMAND_DAG.md"),
        "--command-dag",
        help="Benchmark command DAG markdown file.",
    ),
    out: Path = typer.Option(
        Path("reports/synthesis/release_candidate_check.md"),
        "--out",
        help="Output Markdown release-candidate check report.",
    ),
) -> None:
    """Check benchmark release-candidate artifacts, claims, and command coverage."""
    from mbp.reporting import check_release_candidate, write_release_candidate_check

    result = check_release_candidate(
        claim_ledger=claim_ledger,
        claim_matrix=claim_matrix,
        artifact_manifest=artifact_manifest,
        repo_status=repo_status,
        agents=agents,
        runbook=runbook,
        command_dag=command_dag,
    )
    write_release_candidate_check(result, out)
    typer.echo(f"Release candidate check {result['status']}: {out}")
    for warning in result["warnings"]:
        typer.echo(f"warning: {warning}")
    for failure in result["errors"]:
        typer.echo(f"failure: {failure}")
    if result["status"] != "passed":
        raise typer.Exit(code=1)


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


@features_app.command("build-run-events")
def features_build_run_events(
    log_age: Path = typer.Option(..., "--log-age", help="Path to modality_table_log_age.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for run_event_table_v1.parquet."),
    progress_interval: int = typer.Option(
        0,
        "--progress-interval",
        help="Print build progress every N cells; 0 disables progress.",
    ),
) -> None:
    """Build LOG_AGE-derived run-event segments."""
    import pyarrow.parquet as pq

    from mbp.data.products.run_events import build_run_event_table

    build_run_event_table(log_age, interval_table, out, progress_interval=progress_interval)
    row_count = pq.ParquetFile(out).metadata.num_rows
    typer.echo(f"Run-event table generated: {row_count} rows written to {out}")


@features_app.command("run-events-qa")
def features_run_events_qa(
    run_events: Path = typer.Option(..., "--run-events", help="Path to run_event_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON path for run-event QA."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output CSV path for run-event coverage."),
) -> None:
    """Run QA checks on LOG_AGE-derived run events."""
    from mbp.data.products.run_events import write_run_event_qa

    report = write_run_event_qa(run_events, interval_table, out, coverage_out)
    typer.echo(
        "Run-event QA "
        f"{report['status']}: rows={report['row_count']} covered={report['intervals_covered']}"
    )


@features_app.command("build-sequence-features")
def features_build_sequence_features(
    run_events: Path = typer.Option(..., "--run-events", help="Path to run_event_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for interval_sequence_features_v1.parquet."),
    seed: int = typer.Option(42, "--seed", help="Deterministic event-order shuffle seed."),
) -> None:
    """Build non-neural event-order feature sidecar."""
    from mbp.data.products.run_events import build_sequence_feature_table

    table = build_sequence_feature_table(run_events, interval_table, out, seed=seed)
    typer.echo(f"Sequence-feature table generated: {table.num_rows} rows written to {out}")


@features_app.command("sequence-qa")
def features_sequence_qa(
    sequence_features: Path = typer.Option(..., "--sequence-features", help="Path to interval_sequence_features_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON path for sequence-feature QA."),
) -> None:
    """Run QA checks on interval sequence features."""
    from mbp.data.products.run_events import write_sequence_feature_qa

    report = write_sequence_feature_qa(sequence_features, interval_table, out)
    typer.echo(f"Sequence-feature QA {report['status']}: rows={report['row_count']}")


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
    pulse_targets: Path | None = typer.Option(
        None,
        "--pulse-targets",
        help="Optional pulse_target_table.parquet sidecar for prior-PULSE capacity feature groups.",
    ),
    eis_targets: Path | None = typer.Option(
        None,
        "--eis-targets",
        help="Optional eis_target_table_v1.parquet sidecar for prior-EIS capacity feature groups.",
    ),
    sequence_features: Path | None = typer.Option(
        None,
        "--sequence-features",
        help="Optional interval_sequence_features_v1.parquet sidecar for event-order feature groups.",
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
    bias_correction: bool = typer.Option(
        False,
        "--bias-correction/--no-bias-correction",
        help="Add train-fold group-mean residual correction diagnostics.",
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
            pulse_targets_path=pulse_targets,
            eis_targets_path=eis_targets,
            sequence_features_path=sequence_features,
            report_dir=report_dir,
            subset=subset,
            seed=seed,
            hgb_max_iter=hgb_max_iter,
            model_levels=_comma_values(model_levels),
            feature_groups=_comma_values(feature_groups),
            targets=_comma_values(targets),
            split_views=_comma_values(split_views),
            bias_correction=bias_correction,
        )
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Capacity baseline report generated: "
        f"{len(report['metrics'])} metric rows written to {out}"
    )


@baseline_app.command("run-stressor-robust-capacity")
def baseline_run_stressor_robust_capacity(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1_1.parquet sidecar for stress feature groups.",
    ),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for diagnostics."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    bag_count: int = typer.Option(5, "--bag-count", min=1, help="Condition-bagging ensemble size."),
    model_levels: str = typer.Option(
        "R0_reference_hgb50,R1_condition_balanced_hgb,R2_stressor_balanced_hgb,R3_condition_bagged_hgb,R4_worst_fold_selected_hgb",
        "--model-levels",
        help="Comma-separated robust model levels.",
    ),
    feature_groups: str = typer.Option(
        "F4_state_log_age_scalar,F8_timestamp_weighted_stress",
        "--feature-groups",
        help="Comma-separated supported robust feature groups: F4_state_log_age_scalar,F8_timestamp_weighted_stress.",
    ),
    targets: str = typer.Option(
        "capacity_Ah_k1,delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
) -> None:
    """Run grouped stressor-robust non-neural capacity baselines."""
    from mbp.baselines.stressor_robust_capacity import run_stressor_robust_capacity

    report = run_stressor_robust_capacity(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        bag_count=bag_count,
        model_levels=_comma_values(model_levels),
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
    )
    typer.echo(
        "Stressor-robust capacity report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("run-hierarchical-capacity")
def baseline_run_hierarchical_capacity(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1_1.parquet sidecar for stress feature groups.",
    ),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for diagnostics."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    shrinkage_strength: float = typer.Option(
        5.0,
        "--shrinkage-strength",
        min=0.0,
        help="Residual-pool shrinkage denominator; larger values shrink family offsets toward zero.",
    ),
    min_pool_count: int = typer.Option(
        3,
        "--min-pool-count",
        min=1,
        help="Minimum train residual count before a stressor-family offset is used.",
    ),
    model_levels: str = typer.Option(
        "H0_global_train_mean,H1_state_time_ridge,H2_partial_pooling_ridge,H3_hgb_reference,H4_hgb_residual_partial_pooling,H5_replicate_variance_interval",
        "--model-levels",
        help="Comma-separated hierarchical model levels.",
    ),
    feature_groups: str = typer.Option(
        "F4_state_log_age_scalar",
        "--feature-groups",
        help="Comma-separated feature groups: F4_state_log_age_scalar or F8_timestamp_weighted_stress.",
    ),
    targets: str = typer.Option(
        "capacity_Ah_k1,delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
) -> None:
    """Run non-neural train-only hierarchical replicate capacity comparators."""
    from mbp.baselines.hierarchical_capacity import run_hierarchical_capacity

    report = run_hierarchical_capacity(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        shrinkage_strength=shrinkage_strength,
        min_pool_count=min_pool_count,
        model_levels=_comma_values(model_levels),
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
    )
    typer.echo(
        "Hierarchical capacity report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("diagnose-stressor-robustness")
def baseline_diagnose_stressor_robustness(
    report: Path = typer.Option(..., "--report", help="Stressor-robust capacity JSON report."),
    predictions: Path = typer.Option(..., "--predictions", help="Stressor-robust prediction Parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for diagnostics."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", min=1, help="Bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap seed."),
) -> None:
    """Render stressor-robust capacity diagnostics from an existing run."""
    from mbp.baselines.stressor_robust_capacity import diagnose_stressor_robustness

    result = diagnose_stressor_robustness(
        report,
        predictions,
        out_dir,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(
        "Stressor-robust capacity diagnostics generated: "
        f"{result['row_counts']['leaderboard_rows']} leaderboard rows"
    )


@baseline_app.command("diagnose-stressor-robust-forensics")
def baseline_diagnose_stressor_robust_forensics(
    report: Path = typer.Option(..., "--report", help="Stressor-robust capacity JSON report."),
    predictions: Path = typer.Option(..., "--predictions", help="Stressor-robust prediction Parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for forensics."),
) -> None:
    """Render stressor-robust failure-source forensics from an existing run."""
    from mbp.baselines.stressor_robust_capacity import diagnose_stressor_robust_forensics

    result = diagnose_stressor_robust_forensics(report, predictions, out_dir)
    typer.echo(
        "Stressor-robust forensics generated: "
        f"{result['row_counts']['split_degradation_rows']} split rows"
    )


@baseline_app.command("run-stressor-robust-pareto")
def baseline_run_stressor_robust_pareto(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1_1.parquet sidecar for stress feature groups.",
    ),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for Pareto diagnostics."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    model_levels: str = typer.Option(
        "R0_reference_hgb50,R1_condition_balanced_hgb,R2_stressor_balanced_hgb,R3_condition_bagged_hgb,R4_worst_fold_selected_hgb",
        "--model-levels",
        help="Comma-separated robust model levels.",
    ),
    feature_groups: str = typer.Option(
        "F4_state_log_age_scalar,F8_timestamp_weighted_stress",
        "--feature-groups",
        help="Comma-separated supported robust feature groups.",
    ),
    targets: str = typer.Option(
        "capacity_Ah_k1,delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
    weight_strengths: str = typer.Option(
        "0.25,0.5,0.75,1.0",
        "--weight-strengths",
        help="Comma-separated R1/R2/R4 reweighting strengths.",
    ),
    bag_counts: str = typer.Option(
        "3,5,9",
        "--bag-counts",
        help="Comma-separated R3 condition-bagging ensemble sizes.",
    ),
) -> None:
    """Run bounded stressor-robust Pareto diagnostics."""
    from mbp.baselines.stressor_robust_capacity import run_stressor_robust_pareto

    report = run_stressor_robust_pareto(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        model_levels=_comma_values(model_levels),
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
        weight_strengths=_comma_floats(weight_strengths),
        bag_counts=_comma_ints(bag_counts),
    )
    typer.echo(
        "Stressor-robust Pareto report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("run-stressor-robust-adaptive")
def baseline_run_stressor_robust_adaptive(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1_1.parquet sidecar for stress feature groups.",
    ),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for adaptive diagnostics."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    feature_groups: str = typer.Option(
        "F4_state_log_age_scalar,F8_timestamp_weighted_stress",
        "--feature-groups",
        help="Comma-separated supported robust feature groups.",
    ),
    targets: str = typer.Option(
        "delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
    weight_strengths: str = typer.Option(
        "0.25,0.5,0.75,1.0",
        "--weight-strengths",
        help="Comma-separated train-only candidate R2 reweighting strengths.",
    ),
    selection_split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold",
        "--selection-split-views",
        help="Comma-separated inner grouped split views used inside each outer train fold.",
    ),
    selection_policy: str = typer.Option(
        "max_gain_guarded",
        "--selection-policy",
        help="Adaptive selector policy: max_gain_guarded or conservative_guarded.",
    ),
) -> None:
    """Run train-only adaptive stressor-robust HGB diagnostics."""
    from mbp.baselines.stressor_robust_capacity import run_stressor_robust_adaptive

    report = run_stressor_robust_adaptive(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
        weight_strengths=_comma_floats(weight_strengths),
        selection_split_views=_comma_values(selection_split_views),
        selection_policy=selection_policy,
    )
    typer.echo(
        "Stressor-robust adaptive report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("replicate-stressor-robust-adaptive")
def baseline_replicate_stressor_robust_adaptive(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for adaptive replication diagnostics."),
    stress_features: Path | None = typer.Option(
        None,
        "--stress-features",
        help="Optional interval_stress_features_v1_1.parquet sidecar for stress feature groups.",
    ),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seeds: str = typer.Option(
        "42,101,202,303,404",
        "--seeds",
        help="Comma-separated deterministic replication seeds.",
    ),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    feature_groups: str = typer.Option(
        "F4_state_log_age_scalar,F8_timestamp_weighted_stress",
        "--feature-groups",
        help="Comma-separated supported robust feature groups.",
    ),
    targets: str = typer.Option(
        "delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
    weight_strengths: str = typer.Option(
        "0.25,0.5,0.75,1.0",
        "--weight-strengths",
        help="Comma-separated train-only candidate R2 reweighting strengths.",
    ),
    selection_split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold",
        "--selection-split-views",
        help="Comma-separated inner grouped split views used inside each outer train fold.",
    ),
    selection_policies: str = typer.Option(
        "conservative_guarded,max_gain_guarded",
        "--selection-policies",
        help="Comma-separated adaptive selector policies.",
    ),
    recompute_seeds: bool = typer.Option(
        False,
        "--recompute-seeds",
        help="Recompute every seed instead of reusing the deterministic HGB/no-bagging fit.",
    ),
) -> None:
    """Replicate adaptive stressor-robust HGB diagnostics across seeds."""
    from mbp.baselines.stressor_robust_capacity import replicate_stressor_robust_adaptive

    report = replicate_stressor_robust_adaptive(
        interval_table,
        interval_subsets,
        out_dir,
        stress_features_path=stress_features,
        subset=subset,
        seeds=_comma_ints(seeds),
        hgb_max_iter=hgb_max_iter,
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
        weight_strengths=_comma_floats(weight_strengths),
        selection_split_views=_comma_values(selection_split_views),
        selection_policies=_comma_values(selection_policies),
        recompute_seeds=recompute_seeds,
    )
    typer.echo(
        "Stressor-robust adaptive replication generated: "
        f"{report['row_counts']['replication_rows']} seed/policy rows written to {out_dir}"
    )


@baseline_app.command("run-stressor-robust-attribution")
def baseline_run_stressor_robust_attribution(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    stress_features: Path = typer.Option(
        ...,
        "--stress-features",
        help="interval_stress_features_v1_1.parquet sidecar for F8 stress feature groups.",
    ),
    out: Path = typer.Option(..., "--out", help="Output attribution report JSON."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Ignored row-level predictions parquet."),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for attribution diagnostics."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    targets: str = typer.Option(
        "delta_capacity_Ah,capacity_Ah_k1",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
    weight_strengths: str = typer.Option(
        "0.25,0.5,0.75,1.0",
        "--weight-strengths",
        help="Comma-separated train-only candidate R2 reweighting strengths.",
    ),
    selection_split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold",
        "--selection-split-views",
        help="Comma-separated inner grouped split views used inside each outer train fold.",
    ),
) -> None:
    """Decompose adaptive stressor-robust gains into F8 feature and reweighting components."""
    from mbp.baselines.stressor_robust_capacity import run_stressor_robust_attribution

    report = run_stressor_robust_attribution(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
        weight_strengths=_comma_floats(weight_strengths),
        selection_split_views=_comma_values(selection_split_views),
    )
    typer.echo(
        "Stressor-robust attribution report generated: "
        f"{report['row_counts']['comparison_rows']} comparison rows written to {out}"
    )


@baseline_app.command("run-stressor-robust-arm-selector")
def baseline_run_stressor_robust_arm_selector(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    stress_features: Path = typer.Option(
        ...,
        "--stress-features",
        help="interval_stress_features_v1_1.parquet sidecar for F8 stress feature groups.",
    ),
    out: Path = typer.Option(..., "--out", help="Output arm-selector report JSON."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Ignored row-level predictions parquet."),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for arm-selector diagnostics."),
    attribution_report: Path | None = typer.Option(
        None,
        "--attribution-report",
        help="Optional existing stressor-robust attribution report for fast report-based routing.",
    ),
    attribution_predictions: Path | None = typer.Option(
        None,
        "--attribution-predictions",
        help="Optional existing stressor-robust attribution predictions parquet.",
    ),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max_iter."),
    targets: str = typer.Option(
        "delta_capacity_Ah",
        "--targets",
        help="Comma-separated capacity targets.",
    ),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split views.",
    ),
    weight_strengths: str = typer.Option(
        "0.25,0.5,0.75,1.0",
        "--weight-strengths",
        help="Comma-separated train-only candidate R2 reweighting strengths.",
    ),
    selection_split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold,c_rate_holdout_fold",
        "--selection-split-views",
        help="Comma-separated inner grouped split views used inside each outer train fold.",
    ),
) -> None:
    """Select among existing stressor-robust arms using train-only grouped validation."""
    from mbp.baselines.stressor_robust_capacity import run_stressor_robust_arm_selector

    report = run_stressor_robust_arm_selector(
        interval_table,
        interval_subsets,
        out,
        predictions_out,
        stress_features_path=stress_features,
        attribution_report_path=attribution_report,
        attribution_predictions_path=attribution_predictions,
        out_dir=out_dir,
        subset=subset,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
        weight_strengths=_comma_floats(weight_strengths),
        selection_split_views=_comma_values(selection_split_views),
    )
    typer.echo(
        "Stressor-robust arm-selector report generated: "
        f"{report['row_counts']['comparison_rows']} comparison rows written to {out}"
    )


@baseline_app.command("compare-prior-pulse-capacity")
def baseline_compare_prior_pulse_capacity(
    baseline_report: Path = typer.Option(..., "--baseline-report", help="Capacity baseline report without prior-PULSE feature groups."),
    prior_pulse_report: Path = typer.Option(..., "--prior-pulse-report", help="Capacity baseline report with F4 and prior-PULSE feature groups."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for paired prior-PULSE predictive diagnostics."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
) -> None:
    """Compare F4 against prior-PULSE feature groups for capacity prediction."""
    from mbp.baselines.capacity import compare_prior_pulse_capacity_reports

    report = compare_prior_pulse_capacity_reports(
        baseline_report,
        prior_pulse_report,
        out_dir,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(
        "Prior-PULSE capacity comparison generated: "
        f"{report['row_counts']['paired_condition_gain_rows']} paired condition rows"
    )


@baseline_app.command("compare-prior-pulse-vs-best-nonpulse")
def baseline_compare_prior_pulse_vs_best_nonpulse(
    nonpulse_reports: str = typer.Option(..., "--nonpulse-reports", help="Comma-separated capacity reports without prior-PULSE feature groups."),
    prior_pulse_report: Path = typer.Option(..., "--prior-pulse-report", help="Capacity baseline report with prior-PULSE feature groups."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for strongest non-PULSE comparison diagnostics."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
) -> None:
    """Compare prior-PULSE groups against strongest supplied non-PULSE reports."""
    from mbp.baselines.capacity import compare_prior_pulse_vs_best_nonpulse_reports

    report = compare_prior_pulse_vs_best_nonpulse_reports(
        [Path(value) for value in _comma_values(nonpulse_reports)],
        prior_pulse_report,
        out_dir,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(
        "Prior-PULSE vs best non-PULSE comparison generated: "
        f"{report['row_counts']['paired_gain_rows']} paired condition rows"
    )


@baseline_app.command("compare-prior-eis-pulse")
def baseline_compare_prior_eis_pulse(
    non_eis_report: Path = typer.Option(..., "--non-eis-report", help="PULSE report without prior-EIS feature groups."),
    prior_eis_report: Path = typer.Option(..., "--prior-eis-report", help="PULSE report with prior-EIS feature groups."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for prior-EIS PULSE hardening diagnostics."),
    stress_report: Path | None = typer.Option(None, "--stress-report", help="Optional additional non-EIS PULSE report."),
    eis_targets: Path | None = typer.Option(None, "--eis-targets", help="Optional EIS target table for filtering."),
    max_eis_alignment_delta_s: float | None = typer.Option(None, "--max-eis-alignment-delta-s", help="Optional max EIS alignment delta filter."),
    require_complete_selected_frequencies: bool = typer.Option(False, "--complete-selected-frequencies", help="Require complete prior selected-frequency EIS features."),
    min_valid_modeling_fraction: float | None = typer.Option(None, "--min-valid-modeling-fraction", help="Optional minimum prior valid modeling fraction."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
) -> None:
    """Compare prior-EIS PULSE groups against strongest supplied non-EIS groups."""
    from mbp.baselines.eis_claims import compare_prior_eis_pulse_reports

    report = compare_prior_eis_pulse_reports(
        non_eis_report,
        prior_eis_report,
        out_dir,
        stress_report_path=stress_report,
        eis_targets_path=eis_targets,
        max_eis_alignment_delta_s=max_eis_alignment_delta_s,
        require_complete_selected_frequencies=require_complete_selected_frequencies,
        min_valid_modeling_fraction=min_valid_modeling_fraction,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(
        "Prior-EIS PULSE comparison generated: "
        f"{report['row_counts']['paired_gain_rows']} paired condition rows"
    )


@baseline_app.command("compare-prior-eis-capacity")
def baseline_compare_prior_eis_capacity(
    non_eis_reports: str = typer.Option(..., "--non-eis-reports", help="Comma-separated capacity reports without prior-EIS feature groups."),
    prior_eis_report: Path = typer.Option(..., "--prior-eis-report", help="Capacity report with prior-EIS feature groups."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for prior-EIS capacity hardening diagnostics."),
    eis_targets: Path | None = typer.Option(None, "--eis-targets", help="Optional EIS target table for filtering."),
    max_eis_alignment_delta_s: float | None = typer.Option(None, "--max-eis-alignment-delta-s", help="Optional max EIS alignment delta filter."),
    require_complete_selected_frequencies: bool = typer.Option(False, "--complete-selected-frequencies", help="Require complete prior selected-frequency EIS features."),
    min_valid_modeling_fraction: float | None = typer.Option(None, "--min-valid-modeling-fraction", help="Optional minimum prior valid modeling fraction."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
) -> None:
    """Compare prior-EIS capacity groups against strongest supplied non-EIS groups."""
    from mbp.baselines.eis_claims import compare_prior_eis_capacity_reports

    report = compare_prior_eis_capacity_reports(
        [Path(value) for value in _comma_values(non_eis_reports)],
        prior_eis_report,
        out_dir,
        eis_targets_path=eis_targets,
        max_eis_alignment_delta_s=max_eis_alignment_delta_s,
        require_complete_selected_frequencies=require_complete_selected_frequencies,
        min_valid_modeling_fraction=min_valid_modeling_fraction,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(
        "Prior-EIS capacity comparison generated: "
        f"{report['row_counts']['paired_gain_rows']} paired condition rows"
    )


@baseline_app.command("eis-hardening-sensitivity")
def baseline_eis_hardening_sensitivity(
    pulse_non_eis_report: Path = typer.Option(..., "--pulse-non-eis-report", help="PULSE report without prior-EIS feature groups."),
    pulse_prior_eis_report: Path = typer.Option(..., "--pulse-prior-eis-report", help="PULSE report with prior-EIS feature groups."),
    capacity_non_eis_reports: str = typer.Option(..., "--capacity-non-eis-reports", help="Comma-separated capacity reports without prior-EIS feature groups."),
    capacity_prior_eis_report: Path = typer.Option(..., "--capacity-prior-eis-report", help="Capacity report with prior-EIS feature groups."),
    eis_targets: Path = typer.Option(..., "--eis-targets", help="EIS target table for sensitivity filters."),
    alignment_out_dir: Path = typer.Option(..., "--alignment-out-dir", help="Output directory for alignment sensitivity summaries."),
    feature_completeness_out: Path = typer.Option(..., "--feature-completeness-out", help="Feature-completeness sensitivity CSV."),
    feature_completeness_md: Path = typer.Option(..., "--feature-completeness-md", help="Feature-completeness claim-readiness Markdown."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
) -> None:
    """Write EIS alignment and feature-completeness sensitivity summaries."""
    from mbp.baselines.eis_claims import write_eis_hardening_sensitivity_reports

    report = write_eis_hardening_sensitivity_reports(
        pulse_non_eis_report=pulse_non_eis_report,
        pulse_prior_eis_report=pulse_prior_eis_report,
        capacity_non_eis_reports=[Path(value) for value in _comma_values(capacity_non_eis_reports)],
        capacity_prior_eis_report=capacity_prior_eis_report,
        eis_targets_path=eis_targets,
        alignment_out_dir=alignment_out_dir,
        feature_completeness_out=feature_completeness_out,
        feature_completeness_md=feature_completeness_md,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
    )
    typer.echo(f"EIS hardening sensitivity written: {report['status']}")


@baseline_app.command("eis-claim-readiness")
def baseline_eis_claim_readiness(
    eis_report: Path = typer.Option(..., "--eis-report", help="EIS scalar baseline report."),
    self_endpoint_out: Path = typer.Option(..., "--self-endpoint-out", help="EIS self-endpoint claim-readiness Markdown."),
    leakage_out: Path = typer.Option(..., "--leakage-out", help="EIS leakage audit Markdown."),
) -> None:
    """Write EIS self-endpoint and leakage claim-readiness reports."""
    from mbp.baselines.eis_claims import (
        write_eis_leakage_audit,
        write_eis_self_endpoint_claim_readiness,
    )

    self_report = write_eis_self_endpoint_claim_readiness(eis_report, self_endpoint_out)
    leakage_report = write_eis_leakage_audit(leakage_out)
    typer.echo(
        "EIS claim-readiness reports written: "
        f"{self_report['supported_rows']} supported self-endpoint rows; leakage {leakage_report['status']}"
    )


@baseline_app.command("run-semi-empirical")
def baseline_run_semi_empirical(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    stress_features: Path = typer.Option(..., "--stress-features", help="Path to interval_stress_features_v1_1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON path for semi-empirical baseline metrics."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output Parquet path for row-level semi-empirical predictions."),
    report_dir: Path | None = typer.Option(None, "--report-dir", help="Optional directory for rendered semi-empirical artifacts."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag to use."),
    seed: int = typer.Option(42, "--seed", help="Deterministic seed recorded for provenance."),
    feature_groups: str = typer.Option(
        "SE0_time_efc,SE1_calendar_cycling,SE2_temperature_voltage,SE3_c_rate_interactions,SE4_coupled_stress",
        "--feature-groups",
        help="Comma-separated semi-empirical feature groups.",
    ),
    targets: str = typer.Option("capacity_Ah_k1,delta_capacity_Ah", "--targets", help="Comma-separated capacity targets."),
    split_views: str = typer.Option(
        "condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold",
        "--split-views",
        help="Comma-separated split columns to evaluate.",
    ),
) -> None:
    """Run non-neural semi-empirical ridge capacity baselines."""
    from mbp.baselines.semi_empirical import run_semi_empirical_baselines

    report = run_semi_empirical_baselines(
        interval_table,
        interval_subsets,
        stress_features,
        out,
        predictions_out,
        report_dir=report_dir,
        subset=subset,
        seed=seed,
        feature_groups=_comma_values(feature_groups),
        targets=_comma_values(targets),
        split_views=_comma_values(split_views),
    )
    typer.echo(
        "Semi-empirical capacity report generated: "
        f"{len(report['metrics'])} metric rows written to {out}"
    )


@baseline_app.command("compare-semi-empirical")
def baseline_compare_semi_empirical(
    semi_empirical_report: Path = typer.Option(..., "--semi-empirical-report", help="Semi-empirical baseline report."),
    hgb_f4_report: Path = typer.Option(..., "--hgb-f4-report", help="Focused HGB F4 report."),
    stress_report: Path = typer.Option(..., "--stress-report", help="Strong non-PULSE stress-feature report."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for semi-empirical comparisons."),
) -> None:
    """Compare semi-empirical baselines against HGB F4 and stress reports."""
    from mbp.baselines.semi_empirical import compare_semi_empirical_reports

    report = compare_semi_empirical_reports(
        semi_empirical_report,
        hgb_f4_report,
        stress_report,
        out_dir,
    )
    typer.echo(
        "Semi-empirical comparison generated: "
        f"{report['row_counts']['paired_vs_hgb_f4']} paired F4 rows"
    )


@baseline_app.command("diagnose-sequence-value")
def baseline_diagnose_sequence_value(
    report: Path = typer.Option(..., "--report", help="Capacity sequence-value baseline report."),
    baseline_report: Path = typer.Option(..., "--baseline-report", help="Reference stress-feature baseline report."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for sequence-value diagnostics."),
) -> None:
    """Compare aggregate, order-aware, shuffled, and stress feature groups."""
    from mbp.baselines.sequence_value import diagnose_sequence_value

    result = diagnose_sequence_value(report, baseline_report, out_dir)
    typer.echo(
        "Sequence-value diagnostics generated: "
        f"{result['row_counts']['aggregate_vs_order']} aggregate/order rows"
    )


@analysis_app.command("replicate-uncertainty")
def analysis_replicate_uncertainty(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    capacity_report: Path = typer.Option(..., "--capacity-report", help="Capacity baseline JSON report."),
    capacity_predictions: Path = typer.Option(..., "--capacity-predictions", help="Capacity prediction Parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for replicate uncertainty diagnostics."),
) -> None:
    """Write condition-triplet replicate uncertainty diagnostics."""
    from mbp.analysis.replicate_uncertainty import write_replicate_uncertainty_report

    report = write_replicate_uncertainty_report(
        interval_table,
        capacity_report,
        capacity_predictions,
        out_dir,
    )
    typer.echo(
        "Replicate uncertainty report generated: "
        f"{report['row_counts']['model_error_rows']} model-error rows"
    )


@analysis_app.command("calibrate-capacity")
def analysis_calibrate_capacity(
    capacity_report: Path = typer.Option(..., "--capacity-report", help="Capacity baseline JSON report."),
    capacity_predictions: Path = typer.Option(..., "--capacity-predictions", help="Capacity prediction Parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    replicate_spread: Path = typer.Option(..., "--replicate-spread", help="Replicate spread CSV from replicate-uncertainty."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for calibration diagnostics."),
    nominal_coverage: float = typer.Option(0.9, "--nominal-coverage", help="Nominal conformal coverage."),
    min_calibration_conditions: int = typer.Option(
        5,
        "--min-calibration-conditions",
        min=1,
        help="Minimum disjoint calibration parameter sets required.",
    ),
) -> None:
    """Evaluate grouped capacity interval calibration diagnostics."""
    from mbp.analysis.calibration import write_capacity_calibration_report

    report = write_capacity_calibration_report(
        capacity_report,
        capacity_predictions,
        interval_table,
        replicate_spread,
        out_dir,
        nominal_coverage=nominal_coverage,
        min_calibration_conditions=min_calibration_conditions,
    )
    typer.echo(
        "Capacity calibration report generated: "
        f"{report['row_counts']['coverage_rows']} split-level rows"
    )


@analysis_app.command("knee-labels")
def analysis_knee_labels(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for knee label stability diagnostics."),
    candidate_out: Path = typer.Option(..., "--candidate-out", help="Output path for knee_candidate_table_v1.parquet."),
) -> None:
    """Build knee candidate labels and detector-stability diagnostics."""
    from mbp.analysis.knee import write_knee_label_report

    report = write_knee_label_report(interval_table, out_dir, candidate_out)
    typer.echo(
        "Knee label stability report generated: "
        f"{report['row_counts']['candidate_rows']} candidate rows"
    )


@analysis_app.command("build-knee-risk-labels")
def analysis_build_knee_risk_labels(
    knee_candidates: Path = typer.Option(..., "--knee-candidates", help="Path to knee_candidate_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for exploratory knee_risk_label_table_v1.parquet."),
) -> None:
    """Build exploratory interval-level knee-risk labels. This does not train a model."""
    from mbp.analysis.knee import build_knee_risk_label_table

    table = build_knee_risk_label_table(knee_candidates, interval_table, out)
    typer.echo(f"Knee risk label table generated: {table.num_rows} rows written to {out}")


@analysis_app.command("knee-forensics")
def analysis_knee_forensics(
    knee_candidates: Path = typer.Option(..., "--knee-candidates", help="Path to knee_candidate_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for knee forensics reports."),
) -> None:
    """Diagnose primary knee replicate inconsistency. This does not train a model."""
    from mbp.analysis.knee import write_knee_forensics

    report = write_knee_forensics(knee_candidates, interval_table, out_dir)
    typer.echo(
        "Knee inconsistency forensics generated: "
        f"{report['row_counts']['inconsistent_conditions']} inconsistent conditions"
    )


@analysis_app.command("knee-stable-registry")
def analysis_knee_stable_registry(
    knee_candidates: Path = typer.Option(..., "--knee-candidates", help="Path to knee_candidate_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for knee_stable_condition_registry_v1.parquet."),
    report: Path = typer.Option(..., "--report", help="Output JSON summary path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output CSV coverage summary path."),
) -> None:
    """Build a stable/unstable/insufficient knee-condition registry."""
    from mbp.analysis.knee import write_knee_stable_registry

    summary = write_knee_stable_registry(knee_candidates, interval_table, out, report, coverage_out)
    typer.echo(
        "Knee stable-condition registry generated: "
        f"{summary['row_counts']['stable_conditions']} stable conditions"
    )


@analysis_app.command("threshold-event-labels")
def analysis_threshold_event_labels(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for threshold-event diagnostics."),
    labels_out: Path = typer.Option(..., "--labels-out", help="Output path for threshold_event_label_table_v1.parquet."),
) -> None:
    """Build exploratory threshold-event labels and stability diagnostics."""
    from mbp.analysis.knee import write_threshold_event_labels

    report = write_threshold_event_labels(interval_table, out_dir, labels_out)
    typer.echo(
        "Threshold-event labels generated: "
        f"{report['row_counts']['label_rows']} interval-label rows"
    )


@analysis_app.command("knee-vs-threshold")
def analysis_knee_vs_threshold(
    knee_candidates: Path = typer.Option(..., "--knee-candidates", help="Path to knee_candidate_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output Markdown decision path."),
) -> None:
    """Compare primary knee labels with threshold-event alternatives."""
    from mbp.analysis.knee import write_knee_vs_threshold_decision

    write_knee_vs_threshold_decision(knee_candidates, interval_table, out)
    typer.echo(f"Knee-vs-threshold decision written to {out}")


@analysis_app.command("build-threshold-warning-table")
def analysis_build_threshold_warning_table(
    threshold_labels: Path = typer.Option(..., "--threshold-labels", help="Path to threshold_event_label_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for threshold_warning_table_v1.parquet."),
    threshold: str = typer.Option("capacity_below_80pct_initial", "--threshold", help="Threshold label to use."),
) -> None:
    """Build prospective threshold-event warning rows using only check-up-k state."""
    from mbp.analysis.knee import build_threshold_warning_table

    table = build_threshold_warning_table(threshold_labels, interval_table, out, threshold)
    typer.echo(f"Threshold-warning table generated: {table.num_rows} rows written to {out}")


@analysis_app.command("threshold-warning-qa")
def analysis_threshold_warning_qa(
    warning_table: Path = typer.Option(..., "--warning-table", help="Path to threshold_warning_table_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON QA report path."),
    class_balance_out: Path = typer.Option(..., "--class-balance-out", help="Output class-balance CSV path."),
    split_coverage_out: Path = typer.Option(..., "--split-coverage-out", help="Output split-coverage CSV path."),
) -> None:
    """Write threshold-event warning class-balance and split-coverage QA."""
    from mbp.analysis.knee import write_threshold_warning_qa

    report = write_threshold_warning_qa(warning_table, out, class_balance_out, split_coverage_out)
    typer.echo(f"Threshold-warning QA {report['status']}: rows={report['row_counts']['rows']}")


@analysis_app.command("build-capacity-horizon-table")
def analysis_build_capacity_horizon_table(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output path for capacity_horizon_table_v1.parquet."),
    horizons: str | None = typer.Option(None, "--horizons", help="Comma-separated check-up horizons, e.g. 1,2,3,5."),
) -> None:
    """Build observed multi-check-up capacity forecasting targets."""
    from mbp.analysis.capacity_horizon import build_capacity_horizon_table

    table = build_capacity_horizon_table(
        interval_table,
        out,
        horizons=_comma_ints(horizons) if horizons else None,
    )
    typer.echo(f"Capacity horizon table generated: {table.num_rows} rows written to {out}")


@analysis_app.command("capacity-horizon-qa")
def analysis_capacity_horizon_qa(
    horizon_table: Path = typer.Option(..., "--horizon-table", help="Path to capacity_horizon_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON QA report path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output horizon coverage CSV path."),
) -> None:
    """Write multi-horizon capacity target coverage diagnostics."""
    from mbp.analysis.capacity_horizon import write_capacity_horizon_qa

    report = write_capacity_horizon_qa(horizon_table, interval_table, out, coverage_out)
    typer.echo(f"Capacity horizon QA {report['status']}: rows={report['row_counts']['rows']}")


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


@baseline_app.command("run-threshold-warning")
def baseline_run_threshold_warning(
    warning_table: Path = typer.Option(..., "--warning-table", help="Path to threshold_warning_table_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB classifier max_iter."),
    targets: str | None = typer.Option(None, "--targets", help="Comma-separated target labels."),
    model_levels: str | None = typer.Option(None, "--model-levels", help="Comma-separated model levels."),
    feature_groups: str | None = typer.Option(None, "--feature-groups", help="Comma-separated feature groups."),
    split_views: str | None = typer.Option(None, "--split-views", help="Comma-separated split views."),
    label_policy: str = typer.Option(
        "all_rows",
        "--label-policy",
        help="Threshold-label policy: all_rows, verified_only, or censored_as_negative.",
    ),
) -> None:
    """Run non-neural grouped threshold-event warning baselines."""
    from mbp.baselines.threshold_warning import run_threshold_warning_baselines

    report = run_threshold_warning_baselines(
        warning_table,
        out,
        predictions_out,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        targets=_comma_values(targets) if targets else None,
        model_levels=_comma_values(model_levels) if model_levels else None,
        feature_groups=_comma_values(feature_groups) if feature_groups else None,
        split_views=_comma_values(split_views) if split_views else None,
        label_policy=label_policy,
    )
    typer.echo(
        "Threshold-warning baseline report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("run-capacity-horizon")
def baseline_run_capacity_horizon(
    horizon_table: Path = typer.Option(..., "--horizon-table", help="Path to capacity_horizon_table_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output prediction Parquet path."),
    out_dir: Path | None = typer.Option(None, "--out-dir", help="Output directory for diagnostics."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB regressor max_iter."),
    targets: str | None = typer.Option(None, "--targets", help="Comma-separated target labels."),
    model_levels: str | None = typer.Option(None, "--model-levels", help="Comma-separated model levels."),
    feature_groups: str | None = typer.Option(None, "--feature-groups", help="Comma-separated feature groups."),
    split_views: str | None = typer.Option(None, "--split-views", help="Comma-separated split views."),
    horizons: str | None = typer.Option(None, "--horizons", help="Comma-separated check-up horizons."),
) -> None:
    """Run non-neural grouped multi-horizon capacity forecasting baselines."""
    from mbp.baselines.capacity_horizon import run_capacity_horizon_baselines

    report = run_capacity_horizon_baselines(
        horizon_table,
        out,
        predictions_out,
        out_dir,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        targets=_comma_values(targets) if targets else None,
        model_levels=_comma_values(model_levels) if model_levels else None,
        feature_groups=_comma_values(feature_groups) if feature_groups else None,
        split_views=_comma_values(split_views) if split_views else None,
        horizons=_comma_ints(horizons) if horizons else None,
    )
    typer.echo(
        "Capacity horizon baseline report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("calibrate-threshold-warning")
def baseline_calibrate_threshold_warning(
    warning_table: Path = typer.Option(..., "--warning-table", help="Path to threshold_warning_table_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON calibration report path."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output calibrated prediction Parquet path."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for calibration diagnostics."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB classifier max_iter."),
    targets: str | None = typer.Option(None, "--targets", help="Comma-separated target labels."),
    split_views: str | None = typer.Option(None, "--split-views", help="Comma-separated split views."),
    label_policies: str | None = typer.Option(
        None,
        "--label-policies",
        help="Comma-separated label policies: all_rows, verified_only, censored_as_negative.",
    ),
    calibration_methods: str | None = typer.Option(
        None,
        "--calibration-methods",
        help="Comma-separated calibration methods: C0_raw_hgb_w2, C1_platt_logistic, C2_isotonic.",
    ),
    calibration_fraction: float = typer.Option(
        0.25,
        "--calibration-fraction",
        min=0.0,
        max=1.0,
        help="Fraction of non-test conditions reserved for calibration.",
    ),
    min_calibration_conditions: int = typer.Option(
        5,
        "--min-calibration-conditions",
        min=1,
        help="Minimum condition groups reserved for calibration when available.",
    ),
    min_calibration_class_count: int = typer.Option(
        3,
        "--min-calibration-class-count",
        min=1,
        help="Minimum positive and negative calibration rows required for fitted calibrators.",
    ),
) -> None:
    """Calibrate non-neural threshold-warning probabilities under grouped splits."""
    from mbp.baselines.threshold_warning import run_threshold_warning_calibration

    report = run_threshold_warning_calibration(
        warning_table,
        out,
        predictions_out,
        out_dir,
        seed=seed,
        hgb_max_iter=hgb_max_iter,
        targets=_comma_values(targets) if targets else None,
        split_views=_comma_values(split_views) if split_views else None,
        label_policies=_comma_values(label_policies) if label_policies else None,
        calibration_methods=_comma_values(calibration_methods) if calibration_methods else None,
        calibration_fraction=calibration_fraction,
        min_calibration_conditions=min_calibration_conditions,
        min_calibration_class_count=min_calibration_class_count,
    )
    typer.echo(
        "Threshold-warning calibration report generated: "
        f"{report['row_counts']['metrics']} metric rows written to {out}"
    )


@baseline_app.command("compare-threshold-warning-censoring")
def baseline_compare_threshold_warning_censoring(
    all_rows_report: Path = typer.Option(..., "--all-rows-report", help="All-row threshold-warning JSON report."),
    verified_only_report: Path = typer.Option(
        ...,
        "--verified-only-report",
        help="Verified-only threshold-warning JSON report.",
    ),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for censoring sensitivity comparison."),
) -> None:
    """Compare threshold-warning results across censoring label policies."""
    from mbp.baselines.threshold_warning import compare_threshold_warning_censoring

    result = compare_threshold_warning_censoring(all_rows_report, verified_only_report, out_dir)
    typer.echo(
        "Threshold-warning censoring comparison generated: "
        f"{result['row_counts']['metric_rows']} metric rows"
    )


@baseline_app.command("finalize-threshold-warning-claim")
def baseline_finalize_threshold_warning_claim(
    report: Path = typer.Option(..., "--report", help="Threshold-warning JSON report."),
    predictions: Path = typer.Option(..., "--predictions", help="Threshold-warning prediction Parquet."),
    warning_table: Path = typer.Option(..., "--warning-table", help="Threshold warning table Parquet."),
    censoring_sensitivity: Path = typer.Option(
        ...,
        "--censoring-sensitivity",
        help="Censoring sensitivity summary markdown.",
    ),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for final claim artifacts."),
) -> None:
    """Finalize threshold-warning claim-readiness reports."""
    from mbp.baselines.threshold_warning import finalize_threshold_warning_claim

    result = finalize_threshold_warning_claim(report, predictions, warning_table, censoring_sensitivity, out_dir)
    typer.echo(
        "Threshold-warning final claim readiness generated: "
        f"{result['outputs']['claim_readiness']}"
    )


@baseline_app.command("diagnose-threshold-warning")
def baseline_diagnose_threshold_warning(
    report: Path = typer.Option(..., "--report", help="Threshold-warning JSON report."),
    predictions: Path = typer.Option(..., "--predictions", help="Threshold-warning prediction Parquet."),
    warning_table: Path = typer.Option(..., "--warning-table", help="Threshold warning table Parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for threshold-warning diagnostics."),
) -> None:
    """Write lead-time, proximity, censoring, and reliability diagnostics."""
    from mbp.baselines.threshold_warning import diagnose_threshold_warning

    result = diagnose_threshold_warning(report, predictions, warning_table, out_dir)
    typer.echo(
        "Threshold-warning diagnostics generated: "
        f"{result['row_counts']['lead_time_rows']} lead-time rows"
    )


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


@baseline_app.command("run-pulse")
def baseline_run_pulse(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON path for PULSE baseline metrics."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output Parquet path for row-level PULSE predictions."),
    stress_features: Path | None = typer.Option(None, "--stress-features", help="Optional interval_stress_features_v1_1.parquet sidecar."),
    eis_targets: Path | None = typer.Option(None, "--eis-targets", help="Optional eis_target_table_v1.parquet sidecar for prior-EIS PULSE feature groups."),
    report_dir: Path | None = typer.Option(None, "--report-dir", help="Optional report artifact directory."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag to use."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="HGB max iterations."),
    model_levels: str = typer.Option("L0_persistence,L1_ridge,L2_hist_gradient_boosting", "--model-levels", help="Comma-separated PULSE model levels."),
    feature_groups: str = typer.Option("P0_persistence,P1_state_time,P2_state_capacity,P3_state_nominal,P4_state_log_age_scalar", "--feature-groups", help="Comma-separated PULSE feature groups."),
    targets: str = typer.Option("delta_pulse_1s_resistance", "--targets", help="Comma-separated PULSE targets."),
    split_views: str = typer.Option("condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold", "--split-views", help="Comma-separated split views."),
    max_alignment_delta_s: float | None = typer.Option(None, "--max-alignment-delta-s", help="Optional maximum PULSE alignment delta at k and k+1."),
) -> None:
    """Run grouped scalar PULSE resistance baselines."""
    from mbp.baselines.pulse import run_pulse_baselines

    report = run_pulse_baselines(
        interval_table,
        interval_subsets,
        pulse_targets,
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
        max_alignment_delta_s=max_alignment_delta_s,
        eis_targets_path=eis_targets,
    )
    typer.echo(f"PULSE baseline report generated: {len(report['metrics'])} metric rows written to {out}")


@baseline_app.command("run-eis")
def baseline_run_eis(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    interval_subsets: Path = typer.Option(..., "--interval-subsets", help="Path to interval_subset_registry_v1.parquet."),
    eis_targets: Path = typer.Option(..., "--eis-targets", help="Path to eis_target_table_v1.parquet."),
    out: Path = typer.Option(..., "--out", help="Output JSON path for EIS scalar baseline metrics."),
    predictions_out: Path = typer.Option(..., "--predictions-out", help="Output Parquet path for row-level EIS predictions."),
    stress_features: Path | None = typer.Option(None, "--stress-features", help="Optional interval_stress_features_v1_1.parquet sidecar."),
    report_dir: Path | None = typer.Option(None, "--report-dir", help="Optional directory for EIS baseline artifacts."),
    subset: str = typer.Option("baseline_clean_tolerant", "--subset", help="Interval subset flag to use."),
    seed: int = typer.Option(42, "--seed", help="Deterministic model seed."),
    hgb_max_iter: int = typer.Option(50, "--hgb-max-iter", min=1, help="Maximum iterations for HGB EIS baselines."),
    model_levels: str = typer.Option("L0_persistence,L1_ridge,L2_hist_gradient_boosting", "--model-levels", help="Comma-separated EIS model levels."),
    feature_groups: str = typer.Option("E0_persistence,E1_state_time,E2_state_capacity,E3_state_nominal,E4_log_age_scalar,E5_stress_v1_1", "--feature-groups", help="Comma-separated EIS feature groups."),
    targets: str = typer.Option("delta_eis_z_abs_1kHz,eis_z_abs_1kHz_k1,delta_nyquist_semicircle_width_proxy,nyquist_semicircle_width_proxy_k1", "--targets", help="Comma-separated EIS targets."),
    split_views: str = typer.Option("condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold", "--split-views", help="Comma-separated split views."),
) -> None:
    """Run grouped scalar EIS diagnostic baselines."""
    from mbp.baselines.eis import run_eis_baselines

    report = run_eis_baselines(
        interval_table,
        interval_subsets,
        eis_targets,
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
    typer.echo(f"EIS baseline report generated: {len(report['metrics'])} metric rows written to {out}")


@pulse_app.command("qa")
def pulse_qa(
    pulse_summary: Path = typer.Option(..., "--pulse-summary", help="Path to modality_table_pulse_summary.parquet."),
    checkup_table: Path = typer.Option(..., "--checkup-table", help="Path to checkup_event_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output PULSE QA JSON path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output PULSE target coverage CSV."),
    alignment_out: Path = typer.Option(..., "--alignment-out", help="Output PULSE alignment JSON report."),
) -> None:
    """Write PULSE target coverage and alignment QA reports."""
    from mbp.data.products.pulse_targets import write_pulse_qa_report

    report = write_pulse_qa_report(pulse_summary, checkup_table, out, coverage_out, alignment_out)
    typer.echo(f"PULSE QA report generated: {report['row_count']} rows written to {out}")


@pulse_app.command("build-targets")
def pulse_build_targets(
    pulse_summary: Path = typer.Option(..., "--pulse-summary", help="Path to modality_table_pulse_summary.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output pulse_target_table.parquet path."),
    soc_percent: float = typer.Option(50.0, "--soc-percent", help="Canonical SOC percent."),
    temperature_context: str = typer.Option("RT", "--temperature-context", help="Canonical temperature context."),
    direction: str = typer.Option("mean", "--direction", help="Direction handling: mean, charge, or discharge."),
) -> None:
    """Build canonical PULSE interval target table."""
    from mbp.data.products.pulse_targets import build_pulse_target_table

    table = build_pulse_target_table(
        pulse_summary,
        interval_table,
        out,
        soc_percent=soc_percent,
        temperature_context=temperature_context,
        direction=direction,
    )
    typer.echo(f"PULSE target table generated: {table.num_rows} rows written to {out}")


@pulse_app.command("alignment-sensitivity")
def pulse_alignment_sensitivity(
    pulse_summary: Path = typer.Option(..., "--pulse-summary", help="Path to modality_table_pulse_summary.parquet."),
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output alignment sensitivity JSON report."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output alignment sensitivity coverage CSV."),
) -> None:
    """Write PULSE alignment-threshold sensitivity diagnostics."""
    from mbp.data.products.pulse_targets import write_pulse_alignment_sensitivity_report

    report = write_pulse_alignment_sensitivity_report(
        pulse_summary,
        pulse_targets,
        interval_table,
        out,
        coverage_out,
    )
    typer.echo(f"PULSE alignment sensitivity report generated: {len(report['thresholds'])} thresholds written to {out}")


@pulse_app.command("missingness")
def pulse_missingness(
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    missing_out: Path = typer.Option(..., "--missing-out", help="Output missing canonical endpoint CSV."),
    by_condition_out: Path = typer.Option(..., "--by-condition-out", help="Output missingness by condition CSV."),
    by_split_out: Path = typer.Option(..., "--by-split-out", help="Output missingness by split CSV."),
) -> None:
    """Write missing canonical PULSE endpoint diagnostics."""
    from mbp.data.products.pulse_targets import write_pulse_missingness_reports

    report = write_pulse_missingness_reports(
        pulse_targets,
        interval_table,
        missing_out,
        by_condition_out,
        by_split_out,
    )
    typer.echo(f"PULSE missingness reports generated: {report['missing_rows']} missing rows")


@eis_app.command("qa")
def eis_qa(
    eis_table: Path = typer.Option(..., "--eis-table", help="Path to modality_table_eis.parquet."),
    eis_quality: Path = typer.Option(..., "--eis-quality", help="Path to eis_spectrum_quality.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS QA JSON path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output EIS coverage CSV."),
    alignment_out: Path = typer.Option(..., "--alignment-out", help="Output EIS alignment JSON report."),
    frequency_out: Path = typer.Option(..., "--frequency-out", help="Output EIS valid-frequency audit CSV."),
) -> None:
    """Write EIS coverage, alignment, spectrum quality, and frequency-mask QA reports."""
    from mbp.data.products.eis_features import write_eis_qa_report

    report = write_eis_qa_report(
        eis_table,
        eis_quality,
        interval_table,
        out,
        coverage_out,
        alignment_out,
        frequency_out,
    )
    typer.echo(f"EIS QA report generated: {report['row_count']} rows written to {out}")


@eis_app.command("alignment-sensitivity")
def eis_alignment_sensitivity(
    eis_quality: Path = typer.Option(..., "--eis-quality", help="Path to eis_spectrum_quality.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS alignment sensitivity JSON path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output EIS alignment sensitivity coverage CSV."),
) -> None:
    """Write EIS alignment-threshold sensitivity diagnostics."""
    from mbp.data.products.eis_features import write_eis_alignment_sensitivity_report

    report = write_eis_alignment_sensitivity_report(eis_quality, interval_table, out, coverage_out)
    typer.echo(f"EIS alignment sensitivity report generated: {len(report['thresholds'])} thresholds written to {out}")


@eis_app.command("build-features")
def eis_build_features(
    eis_table: Path = typer.Option(..., "--eis-table", help="Path to modality_table_eis.parquet."),
    eis_quality: Path = typer.Option(..., "--eis-quality", help="Path to eis_spectrum_quality.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS feature table Parquet path."),
    soc_percent: float = typer.Option(50.0, "--soc-percent", help="Canonical EIS SOC percent."),
    temperature_context: str = typer.Option("RT", "--temperature-context", help="Canonical EIS temperature context."),
) -> None:
    """Build an E1/E2/E3 scalar EIS feature sidecar table."""
    from mbp.data.products.eis_features import build_eis_feature_table

    table = build_eis_feature_table(
        eis_table,
        eis_quality,
        interval_table,
        out,
        soc_percent=soc_percent,
        temperature_context=temperature_context,
    )
    typer.echo(f"EIS feature table generated: {table.num_rows} rows written to {out}")


@eis_app.command("feature-qa")
def eis_feature_qa(
    eis_features: Path = typer.Option(..., "--eis-features", help="Path to eis_feature_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS feature QA JSON path."),
) -> None:
    """Write EIS scalar feature-table QA report."""
    from mbp.data.products.eis_features import write_eis_feature_qa_report

    report = write_eis_feature_qa_report(eis_features, interval_table, out)
    typer.echo(f"EIS feature QA report generated: {report['row_count']} rows written to {out}")


@eis_app.command("build-targets")
def eis_build_targets(
    eis_features: Path = typer.Option(..., "--eis-features", help="Path to eis_feature_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS target table Parquet path."),
    soc_percent: float = typer.Option(50.0, "--soc-percent", help="Canonical EIS SOC percent."),
    temperature_context: str = typer.Option("RT", "--temperature-context", help="Canonical EIS temperature context."),
) -> None:
    """Build one canonical EIS target row per interval."""
    from mbp.data.products.eis_features import build_eis_target_table

    table = build_eis_target_table(
        eis_features,
        interval_table,
        out,
        soc_percent=soc_percent,
        temperature_context=temperature_context,
    )
    typer.echo(f"EIS target table generated: {table.num_rows} rows written to {out}")


@eis_app.command("target-qa")
def eis_target_qa(
    eis_targets: Path = typer.Option(..., "--eis-targets", help="Path to eis_target_table_v1.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output EIS target QA JSON path."),
    coverage_out: Path = typer.Option(..., "--coverage-out", help="Output EIS target coverage CSV."),
) -> None:
    """Write EIS interval target QA report."""
    from mbp.data.products.eis_features import write_eis_target_qa_report

    report = write_eis_target_qa_report(eis_targets, interval_table, out, coverage_out)
    typer.echo(f"EIS target QA report generated: {report['row_count']} rows written to {out}")


@eis_app.command("claim-readiness")
def eis_claim_readiness(
    qa_report: Path = typer.Option(..., "--qa-report", help="Path to EIS QA JSON report."),
    feature_qa_report: Path = typer.Option(..., "--feature-qa-report", help="Path to EIS feature QA JSON report."),
    out: Path = typer.Option(..., "--out", help="Output EIS claim-readiness markdown path."),
) -> None:
    """Render the Milestone 2.0 EIS claim-readiness report."""
    from mbp.data.products.eis_features import write_eis_claim_readiness_report

    write_eis_claim_readiness_report(qa_report, feature_qa_report, out)
    typer.echo(f"EIS claim-readiness report generated: {out}")


@coupling_app.command("build-pulse-capacity-table")
def coupling_build_pulse_capacity_table(
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    out: Path = typer.Option(..., "--out", help="Output capacity_pulse_coupling_table.parquet path."),
) -> None:
    """Build the scalar capacity/PULSE coupling sidecar table."""
    from mbp.coupling.pulse_capacity import build_capacity_pulse_coupling_table

    table = build_capacity_pulse_coupling_table(interval_table, pulse_targets, out)
    typer.echo(f"Capacity/PULSE coupling table generated: {table.num_rows} rows written to {out}")


@coupling_app.command("pulse-capacity")
def coupling_pulse_capacity(
    capacity_report: Path = typer.Option(..., "--capacity-report", help="Capacity baseline report JSON."),
    capacity_predictions: Path = typer.Option(..., "--capacity-predictions", help="Capacity row-level predictions parquet."),
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for coupling diagnostics."),
    coupling_table_out: Path | None = typer.Option(None, "--coupling-table-out", help="Optional output coupling-table parquet path."),
) -> None:
    """Generate capacity residual versus PULSE growth diagnostics."""
    from mbp.coupling.pulse_capacity import write_pulse_capacity_diagnostics

    report = write_pulse_capacity_diagnostics(
        capacity_report,
        capacity_predictions,
        pulse_targets,
        interval_table,
        out_dir,
        coupling_table_out=coupling_table_out,
    )
    typer.echo(
        "Capacity/PULSE coupling diagnostics generated: "
        f"{report['row_counts']['joined_prediction_rows']} joined prediction rows"
    )


@coupling_app.command("pulse-capacity-robustness")
def coupling_pulse_capacity_robustness(
    capacity_report: Path = typer.Option(..., "--capacity-report", help="Capacity baseline report JSON."),
    capacity_predictions: Path = typer.Option(..., "--capacity-predictions", help="Capacity row-level predictions parquet."),
    pulse_targets: Path = typer.Option(..., "--pulse-targets", help="Path to pulse_target_table.parquet."),
    interval_table: Path = typer.Option(..., "--interval-table", help="Path to interval_table.parquet."),
    out_dir: Path = typer.Option(..., "--out-dir", help="Output directory for coupling robustness diagnostics."),
    model_level: str = typer.Option("L2_hist_gradient_boosting", "--model-level", help="Canonical capacity model level."),
    feature_group: str = typer.Option("F4_state_log_age_scalar", "--feature-group", help="Canonical capacity feature group."),
    target: str = typer.Option("capacity_Ah_k1", "--target", help="Canonical capacity target."),
    split: str = typer.Option("all", "--split", help="Canonical split view, or 'all'."),
    bootstrap_resamples: int = typer.Option(1000, "--bootstrap-resamples", help="Parameter-set bootstrap resamples."),
    seed: int = typer.Option(42, "--seed", help="Bootstrap random seed."),
    coupling_table_out: Path | None = typer.Option(None, "--coupling-table-out", help="Optional output coupling-table parquet path."),
) -> None:
    """Generate canonical, interval-level, condition-level, and controlled coupling diagnostics."""
    from mbp.coupling.pulse_capacity import write_pulse_capacity_robustness_diagnostics

    report = write_pulse_capacity_robustness_diagnostics(
        capacity_report,
        capacity_predictions,
        pulse_targets,
        interval_table,
        out_dir,
        model_level=model_level,
        feature_group=feature_group,
        target=target,
        split=split,
        bootstrap_resamples=bootstrap_resamples,
        seed=seed,
        coupling_table_out=coupling_table_out,
    )
    typer.echo(
        "Capacity/PULSE coupling robustness diagnostics generated: "
        f"{report['row_counts']['interval_rows']} interval rows, "
        f"{report['row_counts']['condition_rows']} condition rows"
    )


def _comma_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _comma_floats(value: str) -> list[float]:
    return [float(item) for item in _comma_values(value)]


def _comma_ints(value: str) -> list[int]:
    return [int(item) for item in _comma_values(value)]


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
