from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app
from mbp.reporting.manuscript_checks import check_manuscript


def _write_minimal_ledger(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Claim Ledger",
                "",
                "| ID | Claim | Status |",
                "|---|---|---|",
                "| C01 | Example supported claim. | `supported` |",
                "| C10 | EIS remains gated. | `gated` |",
                "| C11 | CBAT remains blocked. | `blocked` |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_check_manuscript_passes_with_known_claim_and_assets(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_2.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "source_traceability.md"
    (tmp_path / "figures" / "generated").mkdir(parents=True)
    (tmp_path / "figures" / "generated" / "fig01_example.svg").write_text(
        "<svg></svg>\n", encoding="utf-8"
    )
    (tmp_path / "tables" / "generated").mkdir(parents=True)
    (tmp_path / "tables" / "generated" / "table01_example.md").write_text(
        "| A |\n|---|\n", encoding="utf-8"
    )
    manuscript.write_text(
        "Claim C01 is shown in [Figure 1] and [Table 1].\n",
        encoding="utf-8",
    )
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")

    result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=ledger,
        traceability=traceability,
    )

    assert result["status"] == "passed"
    assert result["failures"] == []


def test_check_manuscript_rejects_forbidden_wording(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_2.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "source_traceability.md"
    manuscript.write_text("Claim C01 says PULSE improves fade-rate prediction.\n", encoding="utf-8")
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")

    result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=ledger,
        traceability=traceability,
    )

    assert result["status"] == "failed"
    assert any("Forbidden phrase" in failure for failure in result["failures"])


def test_check_manuscript_cli_fails_on_unknown_claim(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_2.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "source_traceability.md"
    manuscript.write_text("Unknown claim C99.\n", encoding="utf-8")
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "check-manuscript",
            "--manuscript",
            str(manuscript),
            "--claim-ledger",
            str(ledger),
            "--traceability",
            str(traceability),
        ],
    )

    assert result.exit_code == 1
    assert "Unknown claim IDs" in result.output
