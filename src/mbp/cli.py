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

app.add_typer(audit_app, name="audit")
app.add_typer(report_app, name="report")
app.add_typer(ingest_app, name="ingest")
app.add_typer(split_app, name="split")


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

    # If the bagit validation report was already generated, pass it, otherwise let rendering compute it
    bagit_report = None
    bagit_report_path = out.parent / "bagit_validation.json"
    if bagit_report_path.exists():
        try:
            with bagit_report_path.open("r", encoding="utf-8") as f:
                bagit_report = json.load(f)
        except Exception:
            pass

    write_evidence_memo(
        manifest, coverage, known_issues, evidence_memo_path, bagit_report=bagit_report
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

    # Try to load bagit validation report if it exists beside the manifest
    bagit_report = None
    bagit_report_path = manifest_path.parent / "bagit_validation.json"
    if bagit_report_path.exists():
        try:
            with bagit_report_path.open("r", encoding="utf-8") as f:
                bagit_report = json.load(f)
        except Exception:
            pass

    write_evidence_memo(manifest, coverage, known_issues, out, bagit_report=bagit_report)
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
) -> None:
    """Ingest cell operating logs from cell_log_age_ultracompr.7z into interim Parquet."""
    from mbp.data.luh_blank.parse_log import ingest_log_age

    typer.echo(f"Ingesting LOG_AGE data from {archive}...")
    table = ingest_log_age(archive, out_dir, exclusions_report_path=exclusions_report)
    typer.echo(f"LOG_AGE ingestion complete: {len(table)} rows written to {out_dir / 'modality_table_log_age.parquet'}")


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

    # Extract result package info to build per-package evidence
    result_pkg = collection.get("packages", {}).get("result_package", {})
    result_path_str = result_pkg.get("path")

    if result_path_str and Path(result_path_str).exists():
        manifest_obj = build_manifest(Path(result_path_str))
        generated_at_utc = manifest_obj.provenance.generated_at_utc
        coverage = build_modality_coverage(manifest_obj.file_inventory, generated_at_utc)
        known_issues = build_known_issue_checks(manifest_obj.file_inventory, generated_at_utc)

        # Try to load existing bagit report
        bagit_report = None
        bagit_path = manifest.parent / "bagit_validation.json"
        if bagit_path.exists():
            try:
                with bagit_path.open("r", encoding="utf-8") as bf:
                    bagit_report = json.load(bf)
            except Exception:
                pass

        write_evidence_memo(manifest_obj, coverage, known_issues, out, bagit_report=bagit_report)
        typer.echo(f"Evidence memo compiled and written to {out}")
    else:
        typer.echo(f"Result package path not found or does not exist: {result_path_str}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
