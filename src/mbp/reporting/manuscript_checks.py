"""No-overclaim and source-traceability checks for manuscript drafts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


FORBIDDEN_PHRASES = [
    "solves degradation",
    "CBAT validated",
    "EIS improves",
    "multimodal model solves",
    "PULSE improves fade-rate prediction",
    "calibrated uncertainty",
]


def _claim_ids(text: str) -> set[str]:
    return set(re.findall(r"\bC\d{2}\b", text))


def _ledger_claim_ids(text: str) -> set[str]:
    return set(re.findall(r"\|\s*(C\d{2})\s*\|", text))


def _callout_numbers(text: str, kind: str) -> set[int]:
    return {int(value) for value in re.findall(rf"(?:\[|\b){kind}\s+(\d+)(?:\]|\b)", text)}


def _has_generated_asset(root: Path, kind: str, number: int) -> bool:
    if kind == "Figure":
        pattern = f"fig{number:02d}_*.svg"
        return (
            any((root / "figures" / "generated").glob(pattern))
            or any((root / "figures" / "generated_v0_4").glob(pattern))
            or any((root / "figures").glob(f"figure_{number:02d}_*.md"))
        )
    pattern = f"table{number:02d}_*.md"
    return any((root / "tables" / "generated").glob(pattern)) or any(
        (root / "tables").glob(f"table_{number:02d}_*.md")
    )


def _supported_eis_or_cbat(text: str) -> list[str]:
    problems: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if ("eis" in lower or "cbat" in lower) and "`supported`" in lower:
            problems.append(line)
    return problems


def _future_pulse_input_phrases(text: str) -> list[str]:
    blocked = [
        "pulse_1s_resistance_k1 as input",
        "delta_pulse_1s_resistance as input",
        "pulse_10ms_resistance_k1 as input",
        "delta_pulse_10ms_resistance as input",
    ]
    lower = text.lower()
    return [phrase for phrase in blocked if phrase.lower() in lower]


def _paper_facing_paths(manuscript: Path, traceability: Path) -> list[Path]:
    root = manuscript.parent
    paths = [manuscript, traceability]
    paths.extend(sorted((root / "captions").glob("*.md")))
    paths.extend(sorted((root / "tables" / "generated").glob("*.md")))
    paths.extend(sorted((root / "figures").glob("*.md")))
    return [path for path in paths if path.exists()]


def _caption_numbers(path: Path, kind: str) -> set[int]:
    if not path.exists():
        return set()
    return {
        int(value)
        for value in re.findall(
            rf"^##\s+{kind}\s+(\d+)\b",
            path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    }


def check_manuscript(
    *,
    manuscript: Path,
    claim_ledger: Path,
    traceability: Path,
) -> dict[str, object]:
    """Check a manuscript draft for claim IDs, callouts, and blocked wording."""

    warnings: list[str] = []
    failures: list[str] = []

    paper_paths = _paper_facing_paths(manuscript, traceability)
    paper_text_by_path = {
        path: path.read_text(encoding="utf-8", errors="replace") for path in paper_paths
    }
    manuscript_text = paper_text_by_path.get(manuscript, "")
    ledger_text = claim_ledger.read_text(encoding="utf-8") if claim_ledger.exists() else ""
    traceability_text = paper_text_by_path.get(traceability, "")

    ledger_ids = _ledger_claim_ids(ledger_text)
    paper_ids: set[str] = set()
    for text in paper_text_by_path.values():
        paper_ids.update(_claim_ids(text))
    unknown_ids = sorted(paper_ids - ledger_ids)
    if unknown_ids:
        failures.append(f"Unknown claim IDs in paper-facing files: {', '.join(unknown_ids)}")
    if not _claim_ids(manuscript_text):
        warnings.append("No explicit claim IDs found in manuscript text.")

    for path, text in paper_text_by_path.items():
        lower_text = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in lower_text:
                failures.append(f"Forbidden phrase found in {path}: {phrase}")

    manuscript_root = manuscript.parent
    for number in sorted(_callout_numbers(manuscript_text, "Figure")):
        if not _has_generated_asset(manuscript_root, "Figure", number):
            failures.append(f"Missing generated/spec artifact for Figure {number}")
    for number in sorted(_callout_numbers(manuscript_text, "Table")):
        if not _has_generated_asset(manuscript_root, "Table", number):
            failures.append(f"Missing generated/spec artifact for Table {number}")

    trace_ids = _claim_ids(traceability_text)
    missing_trace_ids = sorted(_claim_ids(manuscript_text) - trace_ids)
    if missing_trace_ids:
        warnings.append(f"Claim IDs used in manuscript but absent from traceability: {', '.join(missing_trace_ids)}")

    for line in _supported_eis_or_cbat(ledger_text):
        failures.append(f"EIS/CBAT claim appears marked supported: {line}")

    for path, text in paper_text_by_path.items():
        for phrase in _future_pulse_input_phrases(text):
            failures.append(f"Future PULSE feature appears as capacity input in {path}: {phrase}")

    figure_captions = manuscript_root / "captions" / "figure_captions.md"
    table_captions = manuscript_root / "captions" / "table_captions.md"
    captioned_figures = _caption_numbers(figure_captions, "Figure")
    captioned_tables = _caption_numbers(table_captions, "Table")
    for figure_path in sorted((manuscript_root / "figures" / "generated").glob("fig*.svg")):
        match = re.match(r"fig(\d+)_", figure_path.name)
        if match and int(match.group(1)) not in captioned_figures:
            failures.append(f"Generated figure lacks caption: {figure_path}")
    for table_path in sorted((manuscript_root / "tables" / "generated").glob("table*.md")):
        match = re.match(r"table(\d+)_", table_path.name)
        if match and int(match.group(1)) not in captioned_tables:
            failures.append(f"Generated table lacks caption: {table_path}")

    return {
        "status": "failed" if failures else "passed",
        "checked_files": [str(path) for path in [*paper_paths, claim_ledger]],
        "warnings": warnings,
        "failures": failures,
        "claim_ids": sorted(paper_ids),
    }


def check_reader_manuscript(
    *,
    manuscript: Path,
    claim_ledger: Path,
    traceability: Path,
) -> dict[str, object]:
    """Check a reader-facing manuscript for internal scaffolding and overclaims."""

    base = check_manuscript(
        manuscript=manuscript,
        claim_ledger=claim_ledger,
        traceability=traceability,
    )
    failures = [str(value) for value in base.get("failures", [])]
    warnings = [
        str(value)
        for value in base.get("warnings", [])
        if str(value) != "No explicit claim IDs found in manuscript text."
    ]
    manuscript_text = manuscript.read_text(encoding="utf-8") if manuscript.exists() else ""
    lower = manuscript_text.lower()
    blocked_blocks = [
        "allowed claims:",
        "blocked claims:",
        "source artifacts:",
        "source artifact:",
        "referenced assets:",
        "claim ids:",
    ]
    for marker in blocked_blocks:
        if marker in lower:
            failures.append(f"Internal scaffolding remains in reader manuscript: {marker}")
    if _claim_ids(manuscript_text):
        failures.append("Reader-facing manuscript contains raw claim IDs.")

    root = manuscript.parent
    for number in sorted(_callout_numbers(manuscript_text, "Figure")):
        if not (
            any((root / "figures" / "generated_v0_4").glob(f"fig{number:02d}_*.svg"))
            or any((root / "figures" / "generated").glob(f"fig{number:02d}_*.svg"))
        ):
            failures.append(f"Missing generated artifact for reader Figure {number}")
    for number in sorted(_callout_numbers(manuscript_text, "Table")):
        if not any((root / "tables" / "generated").glob(f"table{number:02d}_*.md")):
            failures.append(f"Missing generated artifact for reader Table {number}")

    v04_figure_captions = root / "captions" / "figure_captions_v0_4.md"
    v04_table_captions = root / "captions" / "table_captions_v0_4.md"
    if not v04_figure_captions.exists():
        failures.append(f"Missing reader figure captions: {v04_figure_captions}")
    if not v04_table_captions.exists():
        failures.append(f"Missing reader table captions: {v04_table_captions}")

    return {
        **base,
        "status": "failed" if failures else "passed",
        "warnings": warnings,
        "failures": failures,
    }


def _markdown_list(items: Iterable[str]) -> str:
    items = list(items)
    if not items:
        return "- none\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def write_check_reports(
    *,
    out_dir: Path,
    check_result: dict[str, object],
    figures: list[Path],
    tables: list[Path],
    captions: list[Path],
    extra_reports: list[Path] | None = None,
) -> list[Path]:
    """Write manuscript check summaries."""

    checks_dir = out_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)
    status = str(check_result["status"])
    warnings = [str(value) for value in check_result.get("warnings", [])]
    failures = [str(value) for value in check_result.get("failures", [])]

    claim_check = checks_dir / "manuscript_claim_check.md"
    claim_check.write_text(
        "\n".join(
            [
                "# Manuscript Claim Check",
                "",
                f"Status: `{status}`",
                "",
                "## Checked Files",
                "",
                _markdown_list(str(path) for path in check_result["checked_files"]),
                "## Claim IDs",
                "",
                _markdown_list(str(value) for value in check_result.get("claim_ids", [])),
                "## Warnings",
                "",
                _markdown_list(warnings),
                "## Failures",
                "",
                _markdown_list(failures),
                "## Remaining Manuscript Risks",
                "",
                "- First-pass figures are schematic and should be redesigned before submission.",
                "- Descriptive best-row metrics must remain separated from claim-readiness tests.",
                "- EIS and CBAT remain gated or blocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    source_check = checks_dir / "figure_source_check.md"
    source_check.write_text(
        "\n".join(
            [
                "# Figure and Table Source Check",
                "",
                f"Status: `{status}`",
                "",
                "## Generated Figures",
                "",
                _markdown_list(str(path) for path in figures),
                "## Generated Tables",
                "",
                _markdown_list(str(path) for path in tables),
                "## Caption Files",
                "",
                _markdown_list(str(path) for path in captions),
                "## Additional Check Reports",
                "",
                _markdown_list(str(path) for path in (extra_reports or [])),
                "## Warnings",
                "",
                _markdown_list(warnings),
                "## Failures",
                "",
                _markdown_list(failures),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return [claim_check, source_check]


def write_reader_check_reports(
    *,
    out_dir: Path,
    check_result: dict[str, object],
    reader_result: dict[str, object],
) -> list[Path]:
    checks_dir = out_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)

    claim_check = checks_dir / "manuscript_v0_4_claim_check.md"
    claim_check.write_text(
        "\n".join(
            [
                "# Manuscript v0.4 Claim Check",
                "",
                f"Status: `{check_result['status']}`",
                "",
                "## Checked Files",
                "",
                _markdown_list(str(path) for path in check_result["checked_files"]),
                "## Claim IDs In Sidecars",
                "",
                _markdown_list(str(value) for value in check_result.get("claim_ids", [])),
                "## Warnings",
                "",
                _markdown_list(str(value) for value in check_result.get("warnings", [])),
                "## Failures",
                "",
                _markdown_list(str(value) for value in check_result.get("failures", [])),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    reader_check = checks_dir / "manuscript_v0_4_reader_check.md"
    reader_check.write_text(
        "\n".join(
            [
                "# Manuscript v0.4 Reader Check",
                "",
                f"Status: `{reader_result['status']}`",
                "",
                "## Checked Files",
                "",
                _markdown_list(str(path) for path in reader_result["checked_files"]),
                "## Warnings",
                "",
                _markdown_list(str(value) for value in reader_result.get("warnings", [])),
                "## Failures",
                "",
                _markdown_list(str(value) for value in reader_result.get("failures", [])),
                "## Remaining Publication Risks",
                "",
                "- v0.4 is venue-neutral and still needs target venue formatting.",
                "- Figures are improved draft assets but not final production artwork.",
                "- Supplementary traceability should remain available during review.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return [claim_check, reader_check]
