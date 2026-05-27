import json
from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app
from mbp.reporting.benchmark_tasks import (
    benchmark_leaderboard_rows,
    check_benchmark_tasks,
    load_benchmark_task_registry,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_task_fixture(root: Path) -> dict[str, Path]:
    docs = root / "docs"
    reports = root / "reports" / "synthesis"
    configs = root / "configs"
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
                "C01,Validation,Grouped validation is required,supported,n/a,docs/source.md,Grouped validation required,Random splits publishable,Keep",
                "C11,Architecture,CBAT architecture is justified,blocked,n/a,docs/source.md,CBAT blocked,CBAT validated,Do not open",
            ]
        )
        + "\n",
    )
    _write(
        reports / "artifact_manifest_v2.csv",
        "\n".join(
            [
                "artifact_path,artifact_type,tracked_or_ignored,source_command,depends_on,row_count_if_known,schema_version,claim_relevance,notes",
                "docs/source.md,experiment_memo,tracked,manual,n/a,,n/a,validation,tracked source",
                "data/interim/input.parquet,data_product,ignored,manual,n/a,1,n/a,validation,ignored input",
            ]
        )
        + "\n",
    )
    _write(docs / "source.md", "# Source\n")
    registry = {
        "schema_version": "benchmark_tasks.v1",
        "benchmark_version": "test-freeze",
        "tasks": [
            {
                "task_id": "T01_validation",
                "task_name": "grouped validation task",
                "area": "validation",
                "primary_claim_id": "C01",
                "claim_ids": ["C01"],
                "status": "supported",
                "targets": ["capacity_Ah_k1"],
                "split_views": ["condition_fold"],
                "primary_metric": "MAE",
                "primary_result": "passes",
                "best_reference": "HGB",
                "baseline_families": ["hgb_capacity"],
                "source_artifacts": ["docs/source.md"],
                "local_data_artifacts": ["data/interim/input.parquet"],
                "allowed_wording": "Grouped validation required",
                "forbidden_wording": "Random splits publishable",
                "decision": "Keep grouped validation task",
            }
        ],
    }
    _write(configs / "benchmark_tasks_v1.yaml", json.dumps(registry, indent=2) + "\n")
    return {
        "task_registry": configs / "benchmark_tasks_v1.yaml",
        "claim_ledger": docs / "MAIN_PROJECT_CLAIM_LEDGER_V2.md",
        "claim_matrix": reports / "main_project_claim_matrix_v2.csv",
        "artifact_manifest": reports / "artifact_manifest_v2.csv",
    }


def test_benchmark_task_checker_passes_minimal_fixture(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)

    result = check_benchmark_tasks(repo_root=tmp_path, **paths)

    assert result["status"] == "passed"
    assert result["task_count"] == 1
    assert result["errors"] == []


def test_benchmark_task_checker_fails_missing_source_artifact(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    (tmp_path / "docs" / "source.md").unlink()

    result = check_benchmark_tasks(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("source_artifact does not exist" in error for error in result["errors"])


def test_benchmark_task_checker_fails_status_mismatch(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    registry = json.loads(paths["task_registry"].read_text(encoding="utf-8"))
    registry["tasks"][0]["status"] = "not_supported"
    _write(paths["task_registry"], json.dumps(registry) + "\n")

    result = check_benchmark_tasks(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("status mismatch" in error for error in result["errors"])


def test_benchmark_task_checker_fails_supported_blocked_scope(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    registry = json.loads(paths["task_registry"].read_text(encoding="utf-8"))
    registry["tasks"][0]["allowed_wording"] = "CBAT architecture is validated"
    _write(paths["task_registry"], json.dumps(registry) + "\n")

    result = check_benchmark_tasks(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("Blocked claim area" in error for error in result["errors"])


def test_benchmark_task_checker_fails_local_data_outside_ignored_locations(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    registry = json.loads(paths["task_registry"].read_text(encoding="utf-8"))
    registry["tasks"][0]["local_data_artifacts"] = ["tmp/input.parquet"]
    _write(paths["task_registry"], json.dumps(registry) + "\n")

    result = check_benchmark_tasks(repo_root=tmp_path, **paths)

    assert result["status"] == "failed"
    assert any("outside ignored locations" in error for error in result["errors"])


def test_benchmark_leaderboard_rows_render_from_registry(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    registry = load_benchmark_task_registry(paths["task_registry"])

    rows = benchmark_leaderboard_rows(registry)

    assert rows[0]["task_id"] == "T01_validation"
    assert rows[0]["status"] == "supported"
    assert rows[0]["source_artifact"] == "docs/source.md"


def test_benchmark_task_registry_loads_dependency_free_yaml(tmp_path: Path) -> None:
    registry_path = tmp_path / "configs" / "benchmark_tasks_v1.yaml"
    _write(
        registry_path,
        "\n".join(
            [
                "schema_version: benchmark_tasks.v1",
                "benchmark_version: yaml-test",
                "tasks:",
                "  - task_id: T01_yaml",
                "    task_name: yaml task",
                "    area: validation",
                "    primary_claim_id: C01",
                "    claim_ids: [C01, C12]",
                "    status: supported",
                "    targets: [capacity_Ah_k1, delta_capacity_Ah]",
                "    split_views: [condition_fold]",
                "    primary_metric: MAE",
                "    source_artifacts: [docs/source.md]",
                "    allowed_wording: grouped validation required",
                "    forbidden_wording: random splits",
                "    decision: keep",
            ]
        )
        + "\n",
    )

    registry = load_benchmark_task_registry(registry_path)

    assert registry["benchmark_version"] == "yaml-test"
    assert registry["tasks"][0]["claim_ids"] == ["C01", "C12"]
    assert registry["tasks"][0]["targets"] == ["capacity_Ah_k1", "delta_capacity_Ah"]


def test_benchmark_task_checker_cli_writes_outputs(tmp_path: Path) -> None:
    paths = _minimal_task_fixture(tmp_path)
    out = tmp_path / "reports" / "synthesis" / "benchmark_task_registry_check.md"
    leaderboard = tmp_path / "reports" / "synthesis" / "benchmark_leaderboard_v1.csv"
    task_cards = tmp_path / "reports" / "synthesis" / "benchmark_task_cards_v1.md"
    model_cards = tmp_path / "reports" / "synthesis" / "benchmark_model_cards_v1.md"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "check-benchmark-tasks",
            "--task-registry",
            str(paths["task_registry"]),
            "--claim-ledger",
            str(paths["claim_ledger"]),
            "--claim-matrix",
            str(paths["claim_matrix"]),
            "--artifact-manifest",
            str(paths["artifact_manifest"]),
            "--out",
            str(out),
            "--leaderboard-out",
            str(leaderboard),
            "--task-cards-out",
            str(task_cards),
            "--model-cards-out",
            str(model_cards),
        ],
    )

    assert result.exit_code == 0
    assert "Benchmark task registry check passed" in result.output
    assert "Status: `passed`" in out.read_text(encoding="utf-8")
    assert "T01_validation" in leaderboard.read_text(encoding="utf-8")
    assert "grouped validation task" in task_cards.read_text(encoding="utf-8")
    assert "hgb_capacity" in model_cards.read_text(encoding="utf-8")
