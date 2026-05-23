"""Release-candidate consistency checks for the benchmark package."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable


REQUIRED_RELEASE_FILES = [
    "docs/BENCHMARK_REPRODUCIBILITY.md",
    "docs/BENCHMARK_RUNBOOK.md",
    "docs/BENCHMARK_ARTIFACTS.md",
    "docs/BENCHMARK_RELEASE_CHECKLIST.md",
    "docs/COMMAND_DAG.md",
    "docs/CODEX_NEXT_WORK.md",
    "docs/RELEASE_NOTES_v0.1-rc1.md",
    "docs/TAGGING_RELEASE_CANDIDATE.md",
    "reports/synthesis/artifact_manifest_v2.csv",
    "reports/synthesis/reproducibility_gate_status.md",
]

ALLOWED_IGNORED_PREFIXES = (
    "data/raw/",
    "data/interim/",
    "data/splits/",
    "data/processed/",
)

REQUIRED_COMMAND_FAMILIES = [
    "audit",
    "ingest",
    "intervals",
    "split",
    "features",
    "pulse",
    "eis",
    "baseline",
    "analysis",
    "coupling",
    "report",
]

REQUIRED_RUNBOOK_COMMANDS = [
    "mbp audit",
    "mbp ingest",
    "mbp split",
    "mbp features",
    "mbp pulse",
    "mbp eis",
    "mbp baseline",
    "mbp analysis",
]

BLOCKED_SUPPORTED_PATTERNS = {
    "cbat": r"\bcbat\b",
    "policy": r"\bpolicy(?:-|\s+)ranking\b",
    "causal": r"\bcausal\b",
    "counterfactual": r"\bcounterfactual\b",
    "detector-knee": r"\bdetector-knee\b",
    "knee prediction": r"\bknee(?:-|\s+)prediction\b",
    "calibrated risk": r"\bcalibrated\s+risk\b",
    "calibrated uncertainty": r"\bcalibrated\s+uncertainty\b",
    "broad multimodal": r"\bbroad\s+multimodal\b",
    "sequence models": r"\bsequence\s+models?\b",
    "neural": r"(?<!non-)\bneural\b",
    "drt": r"\bdrt\b",
    "eis embeddings": r"\beis\s+embeddings?\b",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _status_from_errors(errors: list[str]) -> str:
    return "failed" if errors else "passed"


def _markdown_list(items: Iterable[str]) -> str:
    values = list(items)
    if not values:
        return "- none\n"
    return "\n".join(f"- {value}" for value in values) + "\n"


def _ledger_claim_ids(text: str) -> set[str]:
    return set(re.findall(r"\|\s*(C\d{2})\s*\|", text))


def _current_milestone(text: str) -> str | None:
    match = re.search(r"Milestone\s+\d+(?:\.\d+)*", text)
    return match.group(0) if match else None


def _load_claim_matrix(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(f)]


def _load_artifact_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(f)]


def _supported_status(status: str) -> bool:
    normalized = status.strip().strip("`").lower()
    return normalized == "supported" or normalized.startswith("supported_")


def _blocked_supported_matches(text: str) -> list[str]:
    return [
        name
        for name, pattern in BLOCKED_SUPPORTED_PATTERNS.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def _registered_command_families(cli_source: Path) -> set[str]:
    text = _read_text(cli_source)
    families = set(re.findall(r"app\.add_typer\([^,\n]+,\s*name=\"([^\"]+)\"", text))
    command_names = set(re.findall(r"@(?:\w+)_app\.command\(\"([^\"]+)\"\)", text))
    families.update(command_names)
    return families


def check_release_candidate(
    *,
    claim_ledger: Path,
    claim_matrix: Path,
    artifact_manifest: Path,
    repo_status: Path,
    agents: Path,
    runbook: Path,
    command_dag: Path,
    repo_root: Path | None = None,
    cli_source: Path | None = None,
) -> dict[str, object]:
    """Validate release-candidate docs, claims, artifacts, and command coverage."""

    root = repo_root or Path.cwd()
    cli_path = cli_source or root / "src" / "mbp" / "cli.py"
    errors: list[str] = []
    warnings: list[str] = []

    required_paths = [root / path for path in REQUIRED_RELEASE_FILES]
    for path in required_paths:
        if not path.exists():
            errors.append(f"Missing required release file: {path}")

    agents_text = _read_text(agents)
    repo_status_text = _read_text(repo_status)
    agents_phase = _current_milestone(agents_text)
    repo_phase = _current_milestone(repo_status_text)
    if not agents_phase or not repo_phase:
        errors.append("Could not determine current milestone from AGENTS.md or REPO_STATUS.md.")
    elif agents_phase != repo_phase:
        errors.append(f"Phase mismatch: AGENTS.md has {agents_phase}, REPO_STATUS has {repo_phase}.")

    manifest_rows = _load_artifact_manifest(artifact_manifest)
    if not manifest_rows:
        errors.append(f"Artifact manifest is missing or empty: {artifact_manifest}")
    for row in manifest_rows:
        artifact_path = row.get("artifact_path", "").strip()
        tracked_or_ignored = row.get("tracked_or_ignored", "").strip().lower()
        if not artifact_path:
            errors.append("Artifact manifest contains a row without artifact_path.")
            continue
        if tracked_or_ignored == "tracked":
            if artifact_path.startswith("data/") or artifact_path.endswith(".parquet"):
                errors.append(f"Tracked artifact points to generated data: {artifact_path}")
            if not (root / artifact_path).exists():
                errors.append(f"Tracked artifact listed in manifest does not exist: {artifact_path}")
        elif tracked_or_ignored == "ignored":
            if not artifact_path.startswith(ALLOWED_IGNORED_PREFIXES):
                errors.append(f"Ignored artifact outside allowed generated-data locations: {artifact_path}")
        else:
            errors.append(
                f"Artifact manifest row has invalid tracked_or_ignored value for {artifact_path}: {tracked_or_ignored}"
            )

    ledger_text = _read_text(claim_ledger)
    ledger_ids = _ledger_claim_ids(ledger_text)
    matrix_rows = _load_claim_matrix(claim_matrix)
    if not matrix_rows:
        errors.append(f"Claim matrix is missing or empty: {claim_matrix}")
    for row in matrix_rows:
        claim_id = row.get("claim_id", "").strip()
        if claim_id and claim_id not in ledger_ids:
            errors.append(f"Claim matrix ID is absent from ledger: {claim_id}")
        status = row.get("status", "")
        claim_scope = " ".join(
            [
                row.get("area", ""),
                row.get("claim", ""),
                row.get("allowed_wording", ""),
            ]
        ).lower()
        if _supported_status(status):
            for keyword in _blocked_supported_matches(claim_scope):
                errors.append(
                    f"Blocked claim area appears marked supported: {claim_id} status={status} keyword={keyword}"
                )

    for claim_id, claim_status in re.findall(r"\|\s*(C\d{2})\s*\|[^|]*\|\s*`?([^`|\s]+)`?", ledger_text):
        scope_match = re.search(rf"\|\s*{claim_id}\s*\|([^|\n]+\|){{1,2}}", ledger_text)
        scope = scope_match.group(0).lower() if scope_match else claim_id.lower()
        if _supported_status(claim_status):
            for keyword in _blocked_supported_matches(scope):
                errors.append(
                    f"Blocked claim area appears marked supported in ledger: {claim_id} keyword={keyword}"
                )

    runbook_text = _read_text(runbook).lower()
    command_dag_text = _read_text(command_dag).lower()
    for command in REQUIRED_RUNBOOK_COMMANDS:
        if command not in runbook_text and command not in command_dag_text:
            errors.append(f"Runbook/command DAG does not mention required command: {command}")

    command_families = _registered_command_families(cli_path)
    for family in REQUIRED_COMMAND_FAMILIES:
        if family not in command_families:
            errors.append(f"CLI source does not register required command family/name: {family}")

    return {
        "status": _status_from_errors(errors),
        "errors": errors,
        "warnings": warnings,
        "required_files_checked": [str(path) for path in required_paths],
        "tracked_artifacts_checked": sum(
            1 for row in manifest_rows if row.get("tracked_or_ignored", "").strip().lower() == "tracked"
        ),
        "ignored_artifacts_checked": sum(
            1 for row in manifest_rows if row.get("tracked_or_ignored", "").strip().lower() == "ignored"
        ),
        "claim_matrix_rows_checked": len(matrix_rows),
        "command_families_checked": sorted(command_families),
    }


def write_release_candidate_check(result: dict[str, object], out: Path) -> None:
    """Write a Markdown release-candidate check report."""

    out.parent.mkdir(parents=True, exist_ok=True)
    status = str(result["status"])
    errors = [str(value) for value in result.get("errors", [])]
    warnings = [str(value) for value in result.get("warnings", [])]
    out.write_text(
        "\n".join(
            [
                "# Release Candidate Check",
                "",
                f"Status: `{status}`",
                "",
                "## Summary",
                "",
                f"- Required files checked: {len(result.get('required_files_checked', []))}",
                f"- Tracked artifacts checked: {result.get('tracked_artifacts_checked', 0)}",
                f"- Ignored artifacts checked: {result.get('ignored_artifacts_checked', 0)}",
                f"- Claim matrix rows checked: {result.get('claim_matrix_rows_checked', 0)}",
                "",
                "## Errors",
                "",
                _markdown_list(errors).rstrip(),
                "",
                "## Warnings",
                "",
                _markdown_list(warnings).rstrip(),
                "",
                "## Checked Command Families",
                "",
                _markdown_list(str(value) for value in result.get("command_families_checked", [])).rstrip(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
