from pathlib import Path

from mbp.audit.hashing import sha256_file


def test_sha256_file(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.txt"
    fixture.write_text("battery audit\n", encoding="utf-8")

    assert sha256_file(fixture) == (
        "34c4bf785fe64c139b0351e12d618b2910acf6dbe10257a16f27696fd5759870"
    )
