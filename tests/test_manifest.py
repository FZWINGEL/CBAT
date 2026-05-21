from pathlib import Path

from mbp.audit.manifest import build_manifest
from mbp.audit.writers import write_manifest_json, write_sha256_manifest


def test_manifest_for_missing_data_root_has_provenance_and_warning(tmp_path: Path) -> None:
    missing_root = tmp_path / "not_downloaded"

    manifest = build_manifest(missing_root)

    assert manifest.file_count == 0
    assert manifest.provenance.data_root_input == str(missing_root)
    assert manifest.provenance.data_root_exists is False
    assert manifest.audit_warnings == [
        "data_root does not exist; manifest contains no dataset file evidence"
    ]
    assert (
        "SHA-256 hash for every observed file and archive" in manifest.expected_audit_requirements
    )


def test_write_manifest_json(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "PULSE.csv").write_text("cell_id,r\ncell_001,0.1\n", encoding="utf-8")
    out = tmp_path / "DATASET_MANIFEST.json"

    manifest = build_manifest(data_root)
    write_manifest_json(manifest, out)

    text = out.read_text(encoding="utf-8")
    assert '"file_count": 1' in text
    assert '"pulse": 1' in text
    assert '"provenance"' in text


def test_write_sha256_manifest(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    (data_root / "EIS.csv").write_text("cell_id,z\ncell_001,0.1\n", encoding="utf-8")
    manifest = build_manifest(data_root)
    out = tmp_path / "MANIFEST.sha256"

    write_sha256_manifest(manifest.file_inventory, out)

    line = out.read_text(encoding="utf-8").strip()
    digest, relative_path = line.split("  ")
    assert len(digest) == 64
    assert relative_path == "EIS.csv"
