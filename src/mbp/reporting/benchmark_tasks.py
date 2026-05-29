"""Benchmark task-registry checks and frozen synthesis renders."""

from __future__ import annotations

import ast
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable


ALLOWED_IGNORED_PREFIXES = (
    "data/raw/",
    "data/interim/",
    "data/splits/",
    "data/processed/",
)

VALID_TASK_STATUSES = {
    "supported",
    "supported_for_diagnostics",
    "supported_for_explanatory_diagnostics",
    "supported_for_selected_splits",
    "partially_supported",
    "diagnostic_only",
    "not_supported",
    "blocked",
}

REQUIRED_TASK_FIELDS = {
    "task_id",
    "task_name",
    "area",
    "primary_claim_id",
    "status",
    "primary_metric",
    "source_artifacts",
    "allowed_wording",
    "forbidden_wording",
    "decision",
}

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


def load_benchmark_task_registry(path: Path) -> dict[str, Any]:
    """Load the dependency-free YAML/JSON benchmark task registry."""
    if not path.exists():
        raise FileNotFoundError(f"Benchmark task registry does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        data = json.loads(text)
    else:
        data = _parse_simple_registry_yaml(text)
    tasks = data.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("Benchmark task registry must contain a list under `tasks`.")
    return data


def check_benchmark_tasks(
    *,
    task_registry: Path,
    claim_ledger: Path,
    claim_matrix: Path,
    artifact_manifest: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Validate frozen benchmark tasks against source artifacts and claim posture."""
    root = repo_root or task_registry.parent.parent
    errors: list[str] = []
    warnings: list[str] = []
    registry = _load_registry_for_check(task_registry, errors)
    tasks = registry.get("tasks", []) if isinstance(registry, dict) else []
    manifest_rows = _load_csv(artifact_manifest)
    claim_rows = _load_csv(claim_matrix)
    ledger_text = _read_text(claim_ledger)
    ledger_ids = set(re.findall(r"\|\s*(C\d{2})\s*\|", ledger_text))
    claim_status_by_id = {row.get("claim_id", "").strip(): row.get("status", "").strip() for row in claim_rows}
    manifest_by_path = {row.get("artifact_path", "").strip(): row for row in manifest_rows}

    if not tasks:
        errors.append(f"Benchmark task registry has no tasks: {task_registry}")
    if not claim_rows:
        errors.append(f"Claim matrix is missing or empty: {claim_matrix}")
    if not ledger_ids:
        errors.append(f"Claim ledger has no claim IDs: {claim_ledger}")
    if not manifest_rows:
        errors.append(f"Artifact manifest is missing or empty: {artifact_manifest}")

    seen_task_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("Benchmark task registry contains a non-object task row.")
            continue
        task_id = str(task.get("task_id", "")).strip()
        missing_fields = sorted(field for field in REQUIRED_TASK_FIELDS if not _present(task.get(field)))
        if missing_fields:
            errors.append(f"Task {task_id or '<missing>'} is missing required fields: {missing_fields}")
        if task_id in seen_task_ids:
            errors.append(f"Duplicate benchmark task_id: {task_id}")
        seen_task_ids.add(task_id)

        status = str(task.get("status", "")).strip()
        if status not in VALID_TASK_STATUSES:
            errors.append(f"Task {task_id} has invalid status: {status}")

        primary_claim_id = str(task.get("primary_claim_id", "")).strip()
        if primary_claim_id not in ledger_ids:
            errors.append(f"Task {task_id} primary claim ID is absent from ledger: {primary_claim_id}")
        matrix_status = claim_status_by_id.get(primary_claim_id)
        if matrix_status is None:
            errors.append(f"Task {task_id} primary claim ID is absent from claim matrix: {primary_claim_id}")
        elif matrix_status != status:
            errors.append(
                f"Task {task_id} status mismatch for {primary_claim_id}: "
                f"registry={status} matrix={matrix_status}"
            )

        for claim_id in _as_list(task.get("claim_ids", [])):
            if claim_id not in ledger_ids:
                errors.append(f"Task {task_id} claim ID is absent from ledger: {claim_id}")
            if claim_id not in claim_status_by_id:
                errors.append(f"Task {task_id} claim ID is absent from claim matrix: {claim_id}")

        for artifact in _as_list(task.get("source_artifacts", [])):
            if artifact.startswith("data/") or artifact.endswith(".parquet"):
                errors.append(f"Task {task_id} source_artifact points to generated data: {artifact}")
            elif not (root / artifact).exists():
                errors.append(f"Task {task_id} source_artifact does not exist: {artifact}")
            elif artifact not in manifest_by_path:
                warnings.append(f"Task {task_id} source_artifact is not listed in artifact manifest: {artifact}")

        for artifact in _as_list(task.get("local_data_artifacts", [])):
            if not artifact.startswith(ALLOWED_IGNORED_PREFIXES):
                errors.append(f"Task {task_id} local data artifact outside ignored locations: {artifact}")
            manifest_row = manifest_by_path.get(artifact)
            if manifest_row and manifest_row.get("tracked_or_ignored", "").strip().lower() != "ignored":
                errors.append(f"Task {task_id} local data artifact is not marked ignored: {artifact}")
            elif not manifest_row:
                warnings.append(f"Task {task_id} local data artifact is not listed in artifact manifest: {artifact}")

        if _supported_status(status):
            supported_scope = " ".join(
                [
                    str(task.get("task_name", "")),
                    str(task.get("area", "")),
                    str(task.get("allowed_wording", "")),
                    str(task.get("decision", "")),
                ]
            )
            for keyword in _blocked_supported_matches(supported_scope):
                errors.append(
                    f"Blocked claim area appears marked supported in task {task_id}: keyword={keyword}"
                )

    return {
        "status": "failed" if errors else "passed",
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "registry_path": str(task_registry),
        "benchmark_version": registry.get("benchmark_version", "") if isinstance(registry, dict) else "",
        "task_count": len(tasks),
        "claim_matrix_rows_checked": len(claim_rows),
        "artifact_manifest_rows_checked": len(manifest_rows),
        "tasks_checked": [str(task.get("task_id", "")) for task in tasks if isinstance(task, dict)],
    }


def benchmark_leaderboard_rows(registry: dict[str, Any]) -> list[dict[str, str]]:
    """Render task-level rows for the frozen benchmark leaderboard."""
    rows = []
    for task in registry.get("tasks", []):
        rows.append(
            {
                "task_id": str(task.get("task_id", "")),
                "area": str(task.get("area", "")),
                "task_name": str(task.get("task_name", "")),
                "primary_claim_id": str(task.get("primary_claim_id", "")),
                "status": str(task.get("status", "")),
                "primary_metric": str(task.get("primary_metric", "")),
                "primary_result": str(task.get("primary_result", "")),
                "best_reference": str(task.get("best_reference", "")),
                "source_artifact": "; ".join(_as_list(task.get("source_artifacts", []))),
                "allowed_wording": str(task.get("allowed_wording", "")),
                "forbidden_wording": str(task.get("forbidden_wording", "")),
                "decision": str(task.get("decision", "")),
            }
        )
    return sorted(rows, key=lambda row: row["task_id"])


def write_benchmark_leaderboard(rows: list[dict[str, str]], out: Path) -> None:
    """Write the frozen task-level benchmark leaderboard CSV."""
    _write_csv(out, rows)


def write_benchmark_task_cards(registry: dict[str, Any], out: Path) -> None:
    """Write Markdown task cards from the benchmark registry."""
    benchmark_label = _benchmark_label(registry, out)
    lines = [
        f"# Benchmark Task Cards - {benchmark_label}",
        "",
        f"Benchmark version: `{registry.get('benchmark_version', '')}`",
        "",
        "These cards freeze the benchmark task definitions and current claim posture. "
        "They do not add new model results.",
        "",
    ]
    for task in registry.get("tasks", []):
        lines.extend(
            [
                f"## {task.get('task_id')} - {task.get('task_name')}",
                "",
                f"- Area: {task.get('area')}",
                f"- Primary claim: {task.get('primary_claim_id')}",
                f"- Status: `{task.get('status')}`",
                f"- Targets: {', '.join(_as_list(task.get('targets', []))) or 'n/a'}",
                f"- Split views: {', '.join(_as_list(task.get('split_views', []))) or 'n/a'}",
                f"- Primary metric: {task.get('primary_metric')}",
                f"- Primary result: {task.get('primary_result', 'n/a')}",
                f"- Best reference: {task.get('best_reference', 'n/a')}",
                f"- Allowed wording: {task.get('allowed_wording')}",
                f"- Forbidden wording: {task.get('forbidden_wording')}",
                f"- Decision: {task.get('decision')}",
                f"- Source artifacts: {', '.join(_as_list(task.get('source_artifacts', [])))}",
                "",
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_benchmark_model_cards(registry: dict[str, Any], out: Path) -> None:
    """Write concise model-family cards from task registry usage."""
    family_to_tasks: dict[str, list[dict[str, Any]]] = {}
    for task in registry.get("tasks", []):
        for family in _as_list(task.get("baseline_families", [])):
            family_to_tasks.setdefault(family, []).append(task)

    benchmark_label = _benchmark_label(registry, out)
    lines = [
        f"# Benchmark Model Cards - {benchmark_label}",
        "",
        f"Benchmark version: `{registry.get('benchmark_version', '')}`",
        "",
        "These cards summarize model families already evaluated in the frozen benchmark. "
        "They are not new model claims.",
        "",
    ]
    for family in sorted(family_to_tasks):
        tasks = family_to_tasks[family]
        statuses = sorted({str(task.get("status", "")) for task in tasks})
        lines.extend(
            [
                f"## {family}",
                "",
                f"- Used in tasks: {', '.join(str(task.get('task_id')) for task in tasks)}",
                f"- Task statuses: {', '.join(statuses)}",
                "- Claim rule: use only the task-specific allowed wording; do not generalize across blocked gates.",
                "",
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_benchmark_task_check(result: dict[str, Any], out: Path) -> None:
    """Write Markdown benchmark task-registry check report."""
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Benchmark Task Registry Check",
        "",
        f"Status: `{result['status']}`",
        "",
        "## Summary",
        "",
        f"- Benchmark version: `{result.get('benchmark_version', '')}`",
        f"- Tasks checked: {result.get('task_count', 0)}",
        f"- Claim matrix rows checked: {result.get('claim_matrix_rows_checked', 0)}",
        f"- Artifact manifest rows checked: {result.get('artifact_manifest_rows_checked', 0)}",
        "",
        "## Errors",
        "",
        _markdown_list(str(value) for value in result.get("errors", [])).rstrip(),
        "",
        "## Warnings",
        "",
        _markdown_list(str(value) for value in result.get("warnings", [])).rstrip(),
        "",
        "## Tasks",
        "",
        _markdown_list(str(value) for value in result.get("tasks_checked", [])).rstrip(),
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_registry_for_check(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return load_benchmark_task_registry(path)
    except Exception as exc:  # pragma: no cover - exact parser error text is unimportant.
        errors.append(f"Could not load benchmark task registry {path}: {exc}")
        return {"tasks": []}


def _benchmark_label(registry: dict[str, Any], out: Path) -> str:
    version = str(registry.get("benchmark_version", "")).strip()
    if version:
        return version
    match = re.search(r"benchmark_(?:task|model)_cards_(v\d+)", out.name)
    if match:
        return match.group(1)
    return "unversioned"


def _parse_simple_registry_yaml(text: str) -> dict[str, Any]:
    """Parse the registry's small YAML subset without adding a dependency."""
    data: dict[str, Any] = {}
    tasks: list[dict[str, Any]] = []
    current_task: dict[str, Any] | None = None
    in_tasks = False
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0 and line == "tasks:":
            in_tasks = True
            data["tasks"] = tasks
            continue
        if indent == 0 and not in_tasks:
            key, value = _split_key_value(line, line_no)
            data[key] = _parse_scalar(value)
            continue
        if in_tasks and indent == 2 and line.startswith("- "):
            current_task = {}
            tasks.append(current_task)
            rest = line[2:].strip()
            if rest:
                key, value = _split_key_value(rest, line_no)
                current_task[key] = _parse_scalar(value)
            continue
        if in_tasks and indent >= 4 and current_task is not None:
            key, value = _split_key_value(line, line_no)
            current_task[key] = _parse_scalar(value)
            continue
        raise ValueError(f"Unsupported registry YAML shape at line {line_no}: {raw_line}")
    data.setdefault("tasks", tasks)
    return data


def _split_key_value(line: str, line_no: int) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Expected key/value at line {line_no}: {line}")
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.startswith("[") and value.endswith("]"):
        return [_clean_scalar(item) for item in _split_inline_list(value[1:-1])]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    return _clean_scalar(value)


def _split_inline_list(value: str) -> list[str]:
    if not value.strip():
        return []
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in value:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char == ",":
            items.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    items.append("".join(current).strip())
    return [item for item in items if item]


def _clean_scalar(value: str) -> str:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip().strip('"').strip("'")
    return str(parsed) if not isinstance(parsed, list) else ",".join(str(item) for item in parsed)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(f)]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return True


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [item.strip() for item in value.split(";") if item.strip()]
    return [str(value).strip()]


def _supported_status(status: str) -> bool:
    normalized = status.strip().strip("`").lower()
    return normalized == "supported" or normalized.startswith("supported_")


def _blocked_supported_matches(text: str) -> list[str]:
    return [
        name
        for name, pattern in BLOCKED_SUPPORTED_PATTERNS.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def _markdown_list(items: Iterable[str]) -> str:
    values = list(items)
    if not values:
        return "- none\n"
    return "\n".join(f"- {value}" for value in values) + "\n"
