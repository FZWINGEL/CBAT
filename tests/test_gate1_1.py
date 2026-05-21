"""Tests verifying Gate 1.1 BagIt validation, zip introspection, cell coverage, and memo report generation."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from mbp.audit.archives import inventory_zip_archives
from mbp.audit.bagit import parse_manifest, validate_bagit
from mbp.audit.coverage import build_modality_coverage
from mbp.cli import app


def test_parse_manifest(tmp_path: Path) -> None:
    manifest_file = tmp_path / "manifest-md5.txt"
    manifest_file.write_text(
        "8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a  data/dataset/cell_eocv2.zip\n"
        "9b9b9b9b9b9b9b9b9b9b9b9b9b9b9b9b *data/dataset/cell_eisv2.zip\n",
        encoding="utf-8",
    )

    mapping = parse_manifest(manifest_file)
    assert len(mapping) == 2
    assert mapping["data/dataset/cell_eocv2.zip"] == "8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a"
    assert mapping["data/dataset/cell_eisv2.zip"] == "9b9b9b9b9b9b9b9b9b9b9b9b9b9b9b9b"


def test_bagit_validation_passes_with_perfect_structure(tmp_path: Path) -> None:
    # 1. Create a synthetic BagIt container
    bag_dir = tmp_path / "Result_Package"
    bag_dir.mkdir()

    payload_dir = bag_dir / "data"
    payload_dir.mkdir()

    file1 = payload_dir / "file1.txt"
    file_content = "Hello payload"
    file1.write_text(file_content, encoding="utf-8")

    # Compute MD5 of file1.txt
    hash_file1 = hashlib.md5(file1.read_bytes()).hexdigest()

    manifest = bag_dir / "manifest-md5.txt"
    manifest.write_text(f"{hash_file1}  data/file1.txt\n", encoding="utf-8")

    bagit_txt = bag_dir / "bagit.txt"
    bagit_txt.write_text(
        "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n", encoding="utf-8"
    )

    hash_bagit = hashlib.md5(bagit_txt.read_bytes()).hexdigest()
    hash_manifest = hashlib.md5(manifest.read_bytes()).hexdigest()

    tagmanifest = bag_dir / "tagmanifest-md5.txt"
    tagmanifest.write_text(
        f"{hash_bagit}  bagit.txt\n{hash_manifest}  manifest-md5.txt\n", encoding="utf-8"
    )

    report = validate_bagit(bag_dir)
    assert report["status"] == "passed"
    assert report["manifest_status"] == "passed"
    assert report["tagmanifest_status"] == "passed"
    assert len(report["errors"]) == 0
    assert len(report["validated_files"]) == 3


def test_bagit_validation_fails_with_missing_or_mismatched_files(tmp_path: Path) -> None:
    bag_dir = tmp_path / "Result_Package_Corrupt"
    bag_dir.mkdir()

    payload_dir = bag_dir / "data"
    payload_dir.mkdir()

    file1 = payload_dir / "file1.txt"
    file1.write_text("Corrupted content", encoding="utf-8")

    manifest = bag_dir / "manifest-md5.txt"
    manifest.write_text("wronghashvalue  data/file1.txt\n", encoding="utf-8")

    report = validate_bagit(bag_dir)
    assert report["status"] == "failed"
    assert len(report["errors"]) > 0


def test_archives_introspection_without_extraction(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()

    dataset_dir = data_root / "data" / "dataset"
    dataset_dir.mkdir(parents=True)

    # Create a synthetic zip file containing dummy filenames representing different cell IDs
    zip_path = dataset_dir / "cell_eocv2.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("cell_eocv2_P001_1_S01_C10.csv", "timestamp,capacity_Ah\n")
        zf.writestr("cell_eocv2_P001_2_S02_C05.csv", "timestamp,capacity_Ah\n")
        zf.writestr("cell_eocv2_P001_3_S03_C08.csv", "timestamp,capacity_Ah\n")
        zf.writestr("cell_eocv2_P002_1_S04_C09.csv", "timestamp,capacity_Ah\n")

    records = inventory_zip_archives(data_root)
    assert len(records) == 4

    for r in records:
        assert r.archive_name == "cell_eocv2.zip"
        assert r.inferred_modality == "eoc"
        assert r.suffix == ".csv"
        assert r.cell_id is not None
        assert r.cell_id.startswith("P")

    # Verify that the cell IDs match what we wrote
    cell_ids = {r.cell_id for r in records}
    assert cell_ids == {"P001_1", "P001_2", "P001_3", "P002_1"}


def test_coverage_evaluation(tmp_path: Path) -> None:
    # Build coverage against the inventory of the synthetic zip
    data_root = tmp_path / "data"
    data_root.mkdir()

    dataset_dir = data_root / "data" / "dataset"
    dataset_dir.mkdir(parents=True)

    zip_path = dataset_dir / "cell_eisv2.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # 1. Complete replicates for parameter set P001: P001_1, P001_2, P001_3
        zf.writestr("cell_eisv2_P001_1_S01.csv", "")
        zf.writestr("cell_eisv2_P001_2_S01.csv", "")
        zf.writestr("cell_eisv2_P001_3_S01.csv", "")
        # 2. Incomplete replicates for P002: only P002_1
        zf.writestr("cell_eisv2_P002_1_S01.csv", "")

    # Reconstruct FileInventoryRecords to trigger the zip loading in coverage module
    from mbp.audit.inventory import build_inventory, utc_now_iso

    file_records = build_inventory(data_root, generated_at_utc=utc_now_iso())

    records = build_modality_coverage(file_records, utc_now_iso())
    eis_cov = next(r for r in records if r.modality == "eis")

    assert eis_cov.status == "incomplete"
    assert eis_cov.expected_cells == 228
    assert eis_cov.observed_cells == 4
    assert eis_cov.missing_cells_count == 224
    assert eis_cov.parameter_sets_with_any_replicate == 2
    assert eis_cov.parameter_sets_with_all_replicates == 1


def test_cli_audit_bagit_and_archives_and_coverage(tmp_path: Path) -> None:
    # 1. Set up synthetic directories and zip archives
    data_root = tmp_path / "data"
    data_root.mkdir()

    dataset_dir = data_root / "data" / "dataset"
    dataset_dir.mkdir(parents=True)

    zip_path = dataset_dir / "cell_plsv2.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("cell_plsv2_P001_1.csv", "")

    bagit_txt = data_root / "bagit.txt"
    bagit_txt.write_text("BagIt-Version: 1.0\nCharacter-Encoding: UTF-8\n", encoding="utf-8")

    hash_bagit = hashlib.md5(bagit_txt.read_bytes()).hexdigest()
    hash_zip = hashlib.md5(zip_path.read_bytes()).hexdigest()

    manifest_md5 = data_root / "manifest-md5.txt"
    manifest_md5.write_text(f"{hash_zip}  data/dataset/cell_plsv2.zip\n", encoding="utf-8")
    hash_manifest = hashlib.md5(manifest_md5.read_bytes()).hexdigest()

    tagmanifest_md5 = data_root / "tagmanifest-md5.txt"
    tagmanifest_md5.write_text(
        f"{hash_bagit}  bagit.txt\n{hash_manifest}  manifest-md5.txt\n", encoding="utf-8"
    )

    runner = CliRunner()

    # 2. Test mbp audit bagit
    bagit_out = tmp_path / "bagit_validation.json"
    result = runner.invoke(
        app, ["audit", "bagit", "--data-root", str(data_root), "--out", str(bagit_out)]
    )
    assert result.exit_code == 0
    assert bagit_out.exists()

    bagit_data = json.loads(bagit_out.read_text(encoding="utf-8"))
    assert bagit_data["status"] == "passed"

    # 3. Test mbp audit archives
    archives_out = tmp_path / "archive_inventory.csv"
    result = runner.invoke(
        app, ["audit", "archives", "--data-root", str(data_root), "--out", str(archives_out)]
    )
    assert result.exit_code == 0
    assert archives_out.exists()

    with archives_out.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["archive_name"] == "cell_plsv2.zip"
    assert rows[0]["inferred_modality"] == "pulse"
    assert rows[0]["cell_id"] == "P001_1"

    # 4. Test mbp audit coverage
    coverage_out = tmp_path / "modality_coverage.csv"
    result = runner.invoke(
        app, ["audit", "coverage", "--data-root", str(data_root), "--out", str(coverage_out)]
    )
    assert result.exit_code == 0
    assert coverage_out.exists()

    with coverage_out.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        coverage_rows = {r["modality"]: r for r in reader}

    assert coverage_rows["pulse"]["status"] == "incomplete"
    assert int(coverage_rows["pulse"]["observed_cells"]) == 1
    assert int(coverage_rows["pulse"]["parameter_sets_with_any_replicate"]) == 1

    # 5. Test mbp report evidence-memo
    manifest_out = tmp_path / "DATASET_MANIFEST.json"
    memo_out = tmp_path / "dataset_evidence_memo.md"

    # Write a base manifest first
    result_manifest = runner.invoke(
        app,
        [
            "audit",
            "manifest",
            "--data-root",
            str(data_root),
            "--out",
            str(manifest_out),
            "--evidence-memo-out",
            str(memo_out),
        ],
    )
    assert result_manifest.exit_code == 0
    assert manifest_out.exists()
    assert memo_out.exists()

    # Re-run mbp report evidence-memo
    result_memo = runner.invoke(
        app, ["report", "evidence-memo", "--manifest", str(manifest_out), "--out", str(memo_out)]
    )
    assert result_memo.exit_code == 0

    memo_content = memo_out.read_text(encoding="utf-8")
    assert "# Dataset Evidence Memo" in memo_content
    assert "Modality & Cell Coverage Summary" in memo_content
    assert "BagIt Integrity Verification" in memo_content
