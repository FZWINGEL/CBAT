"""Command-line interface for Multimodal Battery Prediction."""

from __future__ import annotations

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
app.add_typer(audit_app, name="audit")


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
    write_evidence_memo(manifest, coverage, known_issues, evidence_memo_path)

    typer.echo(f"Wrote dataset manifest with {manifest.file_count} files to {out}")
    typer.echo(f"Wrote SHA-256 manifest to {sha256_path}")
    typer.echo(f"Wrote modality coverage to {coverage_path}")
    typer.echo(f"Wrote known-issue checks to {known_issues_path}")
    typer.echo(f"Wrote evidence memo to {evidence_memo_path}")


if __name__ == "__main__":
    app()
