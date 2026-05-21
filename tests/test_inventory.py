import csv
from pathlib import Path

from mbp.audit.inventory import build_archive_inventory, build_inventory
from mbp.audit.writers import write_file_inventory


def test_build_inventory_records_hashes_rows_and_provenance(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    eoc = data_root / "EOC_results.csv"
    eoc.write_text("cell_id,capacity_Ah\ncell_001,3.0\ncell_002,2.9\n", encoding="utf-8")
    archive = data_root / "raw_logs.zip"
    archive.write_bytes(b"not a real zip for inventory only")

    records = build_inventory(data_root, generated_at_utc="2026-05-21T00:00:00+00:00")

    by_name = {record.file_name: record for record in records}
    assert by_name["EOC_results.csv"].file_family == "eoc"
    assert by_name["EOC_results.csv"].row_count == 2
    assert len(by_name["EOC_results.csv"].sha256) == 64
    assert by_name["EOC_results.csv"].provenance_data_root == str(data_root)
    assert by_name["raw_logs.zip"].is_archive is True

    archives = build_archive_inventory(records)
    assert [archive_record.archive_name for archive_record in archives] == ["raw_logs.zip"]


def test_write_file_inventory_csv_includes_header_for_empty_inventory(tmp_path: Path) -> None:
    out = tmp_path / "file_inventory.csv"

    write_file_inventory([], out)

    with out.open(newline="", encoding="utf-8") as file_obj:
        rows = list(csv.reader(file_obj))
    assert rows[0][:4] == ["schema_version", "relative_path", "file_name", "file_suffix"]
    assert len(rows) == 1
