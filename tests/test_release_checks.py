from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app
from mbp.reporting.release_checks import check_release_candidate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_release_fixture(root: Path) -> dict[str, Path]:
    docs = root / "docs"
    reports = root / "reports" / "synthesis"
    src = root / "src" / "mbp"

    _write(
        root / "AGENTS.md",
        "# AGENTS\n\n## Current Phase\n\nMilestone 3.2: Benchmark release candidate v0.1 validation.\n",
    )
    _write(
        docs / "REPO_STATUS.md",
        "# Repository Status\n\nThe repository is in **Milestone 3.2: Benchmark release candidate v0.1 validation**.\n",
    )
    _write(
        docs / "MAIN_PROJECT_CLAIM_LEDGER_V2.md",
        "\n".join(
            [
                "# Ledger",
                "",
                "| ID | Claim | Status |",
                "|---|---|---|",
                "| C01 | Grouped validation is required. | `supported` |",
                "| C11 | CBAT architecture is justified. | `blocked` |",
            ]
        )
        + "\n",
    )
    _write(
        reports / "main_project_claim_matrix_v2.csv",
        "\n".join(
            [
                "claim_id,area,claim,status,primary_metric,source_artifact,allowed_wording,forbidden_wording,next_action",
                "C01,Validation,Grouped validation is required,supported,n/a,docs/VALIDATION_PROTOCOL.md,Grouped validation required,Random splits publishable,Keep",
                "C11,Architecture,CBAT architecture is justified,blocked,n/a,docs/PROJECT_CHARTER.md,CBAT blocked,CBAT validated,Do not open",
            ]
        )
        + "\n",
    )
    for relative in [
        "BENCHMARK_REPRODUCIBILITY.md",
        "BENCHMARK_RUNBOOK.md",
        "BENCHMARK_ARTIFACTS.md",
        "BENCHMARK_RELEASE_CHECKLIST.md",
        "COMMAND_DAG.md",
        "CODEX_NEXT_WORK.md",
        "RELEASE_NOTES_v0.1-rc1.md",
        "TAGGING_RELEASE_CANDIDATE.md",
    ]:
        _write(docs / relative, "mbp audit\nmbp ingest\nmbp split\nmbp features\nmbp pulse\nmbp eis\nmbp baseline\nmbp analysis\n")
    _write(
        reports / "reproducibility_gate_status.md",
        "# Reproducibility Gate\n",
    )
    _write(
        reports / "artifact_manifest_v2.csv",
        "\n".join(
            [
                "artifact_path,artifact_type,tracked_or_ignored,source_command,depends_on,row_count_if_known,schema_version,claim_relevance,notes",
                "docs/BENCHMARK_RUNBOOK.md,release_doc,tracked,manual,n/a,,n/a,repro,tracked doc",
                "data/interim/interval_table.parquet,data_product,ignored,mbp ingest intervals,n/a,1,INTERVAL_TABLE_SCHEMA,baselines,ignored data",
            ]
        )
        + "\n",
    )
    _write(
        src / "cli.py",
        "\n".join(
            [
                'app.add_typer(audit_app, name="audit")',
                'app.add_typer(report_app, name="report")',
                'app.add_typer(ingest_app, name="ingest")',
                'app.add_typer(split_app, name="split")',
                'app.add_typer(features_app, name="features")',
                'app.add_typer(pulse_app, name="pulse")',
                'app.add_typer(eis_app, name="eis")',
                'app.add_typer(baseline_app, name="baseline")',
                'app.add_typer(analysis_app, name="analysis")',
                'app.add_typer(coupling_app, name="coupling")',
                '@ingest_app.command("intervals")',
            ]
        )
        + "\n",
    )
    return {
        "claim_ledger": docs / "MAIN_PROJECT_CLAIM_LEDGER_V2.md",
        "claim_matrix": reports / "main_project_claim_matrix_v2.csv",
        "artifact_manifest": reports / "artifact_manifest_v2.csv",
        "repo_status": docs / "REPO_STATUS.md",
        "agents": root / "AGENTS.md",
        "runbook": docs / "BENCHMARK_RUNBOOK.md",
        "command_dag": docs / "COMMAND_DAG.md",
        "cli_source": src / "cli.py",
    }


def _run_check(root: Path) -> dict[str, object]:
    paths = _minimal_release_fixture(root)
    return check_release_candidate(repo_root=root, **paths)


def test_release_checker_passes_minimal_fixture(tmp_path: Path) -> None:
    result = _run_check(tmp_path)

    assert result["status"] == "passed"
    assert result["errors"] == []


def test_release_checker_fails_missing_tracked_artifact(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    (tmp_path / "docs" / "BENCHMARK_RUNBOOK.md").unlink()

    result = check_release_candidate(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("Missing required release file" in error for error in result["errors"])


def test_release_checker_fails_blocked_claim_supported(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    _write(
        paths["claim_matrix"],
        "\n".join(
            [
                "claim_id,area,claim,status,primary_metric,source_artifact,allowed_wording,forbidden_wording,next_action",
                "C11,Architecture,CBAT architecture is justified,supported,n/a,docs/PROJECT_CHARTER.md,CBAT validated,CBAT blocked,Do not open",
            ]
        )
        + "\n",
    )

    result = check_release_candidate(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("Blocked claim area" in error for error in result["errors"])


def test_release_checker_fails_phase_mismatch(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    _write(paths["repo_status"], "# Repository Status\n\nMilestone 3.1: old phase.\n")

    result = check_release_candidate(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("Phase mismatch" in error for error in result["errors"])


def test_release_checker_fails_ignored_artifact_outside_allowed_locations(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    _write(
        paths["artifact_manifest"],
        "\n".join(
            [
                "artifact_path,artifact_type,tracked_or_ignored,source_command,depends_on,row_count_if_known,schema_version,claim_relevance,notes",
                "tmp/generated.parquet,data_product,ignored,manual,n/a,1,n/a,repro,bad ignored path",
            ]
        )
        + "\n",
    )

    result = check_release_candidate(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("outside allowed" in error for error in result["errors"])


def test_release_checker_fails_matrix_id_missing_from_ledger(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    _write(
        paths["claim_matrix"],
        "\n".join(
            [
                "claim_id,area,claim,status,primary_metric,source_artifact,allowed_wording,forbidden_wording,next_action",
                "C99,Validation,Unknown claim,supported,n/a,docs/VALIDATION_PROTOCOL.md,Unknown,Unknown,Keep",
            ]
        )
        + "\n",
    )

    result = check_release_candidate(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("absent from ledger: C99" in error for error in result["errors"])


def test_release_checker_cli_writes_report(tmp_path: Path) -> None:
    paths = _minimal_release_fixture(tmp_path)
    out = tmp_path / "reports" / "synthesis" / "release_candidate_check.md"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "check-release-candidate",
            "--claim-ledger",
            str(paths["claim_ledger"]),
            "--claim-matrix",
            str(paths["claim_matrix"]),
            "--artifact-manifest",
            str(paths["artifact_manifest"]),
            "--repo-status",
            str(paths["repo_status"]),
            "--agents",
            str(paths["agents"]),
            "--runbook",
            str(paths["runbook"]),
            "--command-dag",
            str(paths["command_dag"]),
            "--out",
            str(out),
        ],
    )

    assert result.exit_code == 0
    assert "Release candidate check passed" in result.output
    assert "Status: `passed`" in out.read_text(encoding="utf-8")
