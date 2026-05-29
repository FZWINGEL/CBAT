import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app


def test_manifest_command_writes_gate1_sidecars(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "EOC.csv").write_text("cell_id,capacity_Ah\ncell_001,3.0\n", encoding="utf-8")
    (data_root / "PULSE.csv").write_text("cell_id,r\ncell_001,0.1\n", encoding="utf-8")

    manifest_out = tmp_path / "data" / "manifests" / "DATASET_MANIFEST.json"
    coverage_out = tmp_path / "reports" / "audit" / "modality_coverage.csv"
    memo_out = tmp_path / "reports" / "audit" / "dataset_evidence_memo.md"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "audit",
            "manifest",
            "--data-root",
            str(data_root),
            "--out",
            str(manifest_out),
            "--coverage-out",
            str(coverage_out),
            "--evidence-memo-out",
            str(memo_out),
        ],
    )

    assert result.exit_code == 0
    assert (manifest_out.parent / "MANIFEST.sha256").exists()
    assert (manifest_out.parent / "known_issues.csv").exists()
    assert coverage_out.exists()
    assert memo_out.exists()

    payload = json.loads(manifest_out.read_text(encoding="utf-8"))
    assert payload["file_count"] == 2
    assert payload["modality_file_count"]["eoc"] == 1
    assert payload["modality_file_count"]["pulse"] == 1

    with coverage_out.open(newline="", encoding="utf-8") as file_obj:
        coverage_rows = {row["modality"]: row for row in csv.DictReader(file_obj)}
    assert coverage_rows["eoc"]["status"] == "observed"
    assert coverage_rows["eis"]["status"] == "missing"
    assert "Modeling authorized | No" in memo_out.read_text(encoding="utf-8")


def test_required_repo_skeleton_files_exist() -> None:
    required_paths = [
        "AGENTS.md",
        ".env.example",
        "configs/paths.example.yaml",
        "configs/dataset_luh_blank_v2.yaml",
        "configs/audit.yaml",
        "docs/ASSUMPTION_REGISTER.md",
        "docs/DECISION_LOG.md",
        "docs/KNOWN_DATA_ISSUES.md",
        "docs/SCHEMA_REGISTRY.md",
        "docs/VALIDATION_PROTOCOL.md",
        "docs/archive/PAPER_SKELETON.md",
        "data/README.md",
        "scripts/audit_dataset.py",
        "scripts/make_manifest.py",
        "src/mbp/data/luh_blank/discover.py",
        "src/mbp/data/products/interval_table.py",
    ]

    for path in required_paths:
        assert Path(path).exists(), path
