from pathlib import Path

from typer.testing import CliRunner

from mbp.cli import app
from mbp.reporting.manuscript_checks import check_manuscript, check_reader_manuscript


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
    (tmp_path / "captions").mkdir()
    (tmp_path / "captions" / "figure_captions.md").write_text(
        "## Figure 1. Example\n\nClaim IDs: C01.\n",
        encoding="utf-8",
    )
    (tmp_path / "tables" / "generated").mkdir(parents=True)
    (tmp_path / "tables" / "generated" / "table01_example.md").write_text(
        "| A |\n|---|\n", encoding="utf-8"
    )
    (tmp_path / "captions" / "table_captions.md").write_text(
        "## Table 1. Example\n\nClaim IDs: C01.\n",
        encoding="utf-8",
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


def test_check_manuscript_scans_captions_for_unknown_claims(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_3.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "source_traceability.md"
    captions = tmp_path / "captions"
    captions.mkdir()
    (tmp_path / "figures" / "generated").mkdir(parents=True)
    (tmp_path / "figures" / "generated" / "fig01_example.svg").write_text(
        "<svg></svg>\n", encoding="utf-8"
    )
    manuscript.write_text("Claim C01 is shown in [Figure 1].\n", encoding="utf-8")
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")
    (captions / "figure_captions.md").write_text(
        "## Figure 1. Example\n\nClaim IDs: C99.\n",
        encoding="utf-8",
    )

    result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=ledger,
        traceability=traceability,
    )

    assert result["status"] == "failed"
    assert any("Unknown claim IDs" in failure for failure in result["failures"])


def test_check_manuscript_requires_captions_for_generated_assets(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_3.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "source_traceability.md"
    (tmp_path / "figures" / "generated").mkdir(parents=True)
    (tmp_path / "figures" / "generated" / "fig01_example.svg").write_text(
        "<svg></svg>\n", encoding="utf-8"
    )
    manuscript.write_text("Claim C01 is shown in [Figure 1].\n", encoding="utf-8")
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")

    result = check_manuscript(
        manuscript=manuscript,
        claim_ledger=ledger,
        traceability=traceability,
    )

    assert result["status"] == "failed"
    assert any("lacks caption" in failure for failure in result["failures"])


def test_reader_manuscript_rejects_internal_scaffolding(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_4.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "manuscript_v0_4_traceability.md"
    manuscript.write_text(
        "Allowed claims:\n\n- C01: internal note.\n\nForbidden wording:\n\n- internal note.\n",
        encoding="utf-8",
    )
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")

    result = check_reader_manuscript(
        manuscript=manuscript,
        claim_ledger=ledger,
        traceability=traceability,
    )

    assert result["status"] == "failed"
    assert any("Internal scaffolding" in failure for failure in result["failures"])
    assert any("forbidden wording:" in failure for failure in result["failures"])
    assert any("raw claim IDs" in failure for failure in result["failures"])


def test_reader_manuscript_cli_passes_clean_reader_prose(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript_v0_4.md"
    ledger = tmp_path / "PAPER_CLAIM_LEDGER.md"
    traceability = tmp_path / "manuscript_v0_4_traceability.md"
    captions = tmp_path / "captions"
    captions.mkdir()
    (tmp_path / "figures" / "generated_v0_4").mkdir(parents=True)
    (tmp_path / "figures" / "generated_v0_4" / "fig01_example.svg").write_text(
        "<svg></svg>\n", encoding="utf-8"
    )
    manuscript.write_text("Figure 1 summarizes the design.\n", encoding="utf-8")
    _write_minimal_ledger(ledger)
    traceability.write_text("C01 source mapping.\n", encoding="utf-8")
    (captions / "figure_captions_v0_4.md").write_text(
        "## Figure 1. Example\n\nSource: test.\n",
        encoding="utf-8",
    )
    (captions / "table_captions_v0_4.md").write_text(
        "# Table Captions\n",
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "report",
            "check-reader-manuscript",
            "--manuscript",
            str(manuscript),
            "--claim-ledger",
            str(ledger),
            "--traceability",
            str(traceability),
        ],
    )

    assert result.exit_code == 0
    assert "Reader manuscript check passed" in result.output
