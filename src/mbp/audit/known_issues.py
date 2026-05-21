"""Known-issue checks initialized from charter risks."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from mbp.audit.models import FileInventoryRecord, SCHEMA_VERSION


@dataclass(frozen=True)
class KnownIssueRecord:
    schema_version: str
    issue_id: str
    issue_name: str
    severity: str
    status: str
    evidence: str
    handling_decision: str
    provenance_tool: str
    provenance_generated_at_utc: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_known_issue_checks(
    records: list[FileInventoryRecord],
    generated_at_utc: str,
) -> list[KnownIssueRecord]:
    families = {record.file_family for record in records}
    has_eis = "eis" in families
    has_pulse = "pulse" in families
    has_log = "log" in families
    has_log_age = "log_age" in families

    return [
        issue(
            "KI001",
            "EIS coverage and valid-frequency masks",
            "high",
            "pending_audit" if has_eis else "blocked_missing_evidence",
            "EIS-like files observed" if has_eis else "No EIS-like files observed",
            "Do not make EIS-supervised claims until coverage and valid masks pass.",
            generated_at_utc,
        ),
        issue(
            "KI002",
            "PULSE provenance",
            "high",
            "pending_audit" if has_pulse else "blocked_missing_evidence",
            "PULSE-like files observed" if has_pulse else "No PULSE-like files observed",
            "Verify pulse source and extraction path before resistance claims.",
            generated_at_utc,
        ),
        issue(
            "KI003",
            "LOG gaps and runtime anomalies",
            "medium",
            "pending_audit" if has_log else "blocked_missing_evidence",
            "LOG-like files observed" if has_log else "No LOG-like files observed",
            "Quantify gaps, reboots, pool incidents, and EOL truncation from logs.",
            generated_at_utc,
        ),
        issue(
            "KI004",
            "LOG_AGE leakage risk",
            "high",
            "pending_audit" if has_log_age else "blocked_missing_evidence",
            "LOG_AGE-like files observed" if has_log_age else "No LOG_AGE-like files observed",
            "Mask inserted future diagnostics before interval modeling.",
            generated_at_utc,
        ),
        issue(
            "KI005",
            "Version and source metadata",
            "high",
            "pending_manual_metadata",
            f"{len(records)} local files observed",
            "Record DOI, source URL, archive names, download dates, and SHA-256 hashes.",
            generated_at_utc,
        ),
    ]


def issue(
    issue_id: str,
    issue_name: str,
    severity: str,
    status: str,
    evidence: str,
    handling_decision: str,
    generated_at_utc: str,
) -> KnownIssueRecord:
    return KnownIssueRecord(
        schema_version=SCHEMA_VERSION,
        issue_id=issue_id,
        issue_name=issue_name,
        severity=severity,
        status=status,
        evidence=evidence,
        handling_decision=handling_decision,
        provenance_tool="mbp audit manifest",
        provenance_generated_at_utc=generated_at_utc,
    )


def write_known_issue_checks(records: list[KnownIssueRecord], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "schema_version",
        "issue_id",
        "issue_name",
        "severity",
        "status",
        "evidence",
        "handling_decision",
        "provenance_tool",
        "provenance_generated_at_utc",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
