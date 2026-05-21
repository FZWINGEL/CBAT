import json
from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app


def test_inventory_command_writes_csv(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "LOG_AGE.csv").write_text("cell_id,t\ncell_001,0\n", encoding="utf-8")
    out = tmp_path / "file_inventory.csv"
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["audit", "inventory", "--data-root", str(data_root), "--out", str(out)],
    )

    assert result.exit_code == 0
    assert "Wrote 1 file inventory records" in result.output
    assert "LOG_AGE.csv" in out.read_text(encoding="utf-8")


def test_manifest_command_writes_json_for_missing_data_root(tmp_path: Path) -> None:
    out = tmp_path / "DATASET_MANIFEST.json"
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["audit", "manifest", "--data-root", str(tmp_path / "missing"), "--out", str(out)],
    )

    assert result.exit_code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["file_count"] == 0
    assert payload["provenance"]["data_root_exists"] is False
