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
    return {int(value) for value in re.findall(rf"\[{kind}\s+(\d+)\]", text)}


def _has_generated_asset(root: Path, kind: str, number: int) -> bool:
    if kind == "Figure":
        pattern = f"fig{number:02d}_*.svg"
        return any((root / "figures" / "generated").glob(pattern)) or any(
            (root / "figures").glob(f"figure_{number:02d}_*.md")
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


def check_manuscript(
    *,
    manuscript: Path,
    claim_ledger: Path,
    traceability: Path,
) -> dict[str, object]:
    """Check a manuscript draft for claim IDs, callouts, and blocked wording."""

    warnings: list[str] = []
    failures: list[str] = []

    manuscript_text = manuscript.read_text(encoding="utf-8") if manuscript.exists() else ""
    ledger_text = claim_ledger.read_text(encoding="utf-8") if claim_ledger.exists() else ""
    traceability_text = traceability.read_text(encoding="utf-8") if traceability.exists() else ""

    ledger_ids = _ledger_claim_ids(ledger_text)
    manuscript_ids = _claim_ids(manuscript_text)
    unknown_ids = sorted(manuscript_ids - ledger_ids)
    if unknown_ids:
        failures.append(f"Unknown claim IDs in manuscript: {', '.join(unknown_ids)}")
    if not manuscript_ids:
        warnings.append("No explicit claim IDs found in manuscript text.")

    lower_text = manuscript_text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in lower_text:
            failures.append(f"Forbidden phrase found in manuscript: {phrase}")

    manuscript_root = manuscript.parent
    for number in sorted(_callout_numbers(manuscript_text, "Figure")):
        if not _has_generated_asset(manuscript_root, "Figure", number):
            failures.append(f"Missing generated/spec artifact for Figure {number}")
    for number in sorted(_callout_numbers(manuscript_text, "Table")):
        if not _has_generated_asset(manuscript_root, "Table", number):
            failures.append(f"Missing generated/spec artifact for Table {number}")

    trace_ids = _claim_ids(traceability_text)
    missing_trace_ids = sorted(manuscript_ids - trace_ids)
    if missing_trace_ids:
        warnings.append(f"Claim IDs used in manuscript but absent from traceability: {', '.join(missing_trace_ids)}")

    for line in _supported_eis_or_cbat(ledger_text):
        failures.append(f"EIS/CBAT claim appears marked supported: {line}")

    for phrase in _future_pulse_input_phrases(manuscript_text):
        failures.append(f"Future PULSE feature appears as capacity input: {phrase}")

    return {
        "status": "failed" if failures else "passed",
        "checked_files": [str(manuscript), str(claim_ledger), str(traceability)],
        "warnings": warnings,
        "failures": failures,
        "claim_ids": sorted(manuscript_ids),
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
