"""Collection manifest assembly and aggregation for multi-package datasets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mbp import __version__
from mbp.audit.bagit import validate_bagit
from mbp.audit.coverage import build_modality_coverage
from mbp.audit.inventory import build_inventory, utc_now_iso
from mbp.audit.manifest import parse_bag_info, parse_desc_metadata, parse_tech_metadata

COLLECTION_SCHEMA_VERSION = "gate1.collection.v1"


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse key-value metadata from a YAML file without external dependencies."""
    result: dict[str, Any] = {}
    if not path.exists():
        return result

    current_key = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            # Strip comments and whitespaces
            line = line.split("#")[0].rstrip()
            stripped = line.strip()
            if not stripped:
                continue

            # Check for list items
            if stripped.startswith("-"):
                item = stripped[1:].strip().strip('"').strip("'")
                if current_key and isinstance(result.get(current_key), list):
                    result[current_key].append(item)
                continue

            # Standard key: value match
            match = re.match(r"^([a-zA-Z0-9_]+)\s*:\s*(.*)$", stripped)
            if match:
                key, val = match.groups()
                val = val.strip()

                if val == "null" or val == "None" or not val:
                    val = None
                elif val.startswith("[") and val.endswith("]"):
                    val = [
                        item.strip().strip('"').strip("'")
                        for item in val[1:-1].split(",")
                        if item.strip()
                    ]
                elif val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                elif val.isdigit():
                    val = int(val)
                elif re.match(r"^\d+\.\d+$", val):
                    val = float(val)
                else:
                    # Check if nested list starting
                    if val == "":
                        result[key] = []
                        current_key = key
                        continue

                result[key] = val
                current_key = key

    return result


def build_collection_manifest(
    config_path: Path,
    result_root: Path | None = None,
    log_root: Path | None = None,
) -> dict[str, Any]:
    """Build a unified multi-package collection manifest JSON.

    Combines metadata, provenance, BagIt validations, and aggregated coverage.
    """
    generated_at_utc = utc_now_iso()
    config = parse_simple_yaml(config_path)

    # Setup standard paths
    result_path = result_root or Path("data/raw/Result_Raw_Data_Version_2")
    log_path = log_root or Path("data/raw/Log_Raw_Data_Version_2.zip")

    packages_status = {}
    aggregated_files = []

    # 1. Audit Result Package
    if result_path.exists():
        is_dir = result_path.is_dir()
        bagit_report = validate_bagit(result_path) if is_dir else {"status": "unsupported_non_dir"}

        # Extract desc/tech metadata if exists
        bag_info = parse_bag_info(result_path / "bag-info.txt")
        desc_meta = parse_desc_metadata(
            result_path / "data" / "descriptive-md" / "dataset.desc_md.xml"
        )
        tech_meta = parse_tech_metadata(
            result_path / "data" / "technical-md" / "dataset.tech_md.xml"
        )

        # Compile result inventory records for aggregation
        res_inventory = build_inventory(result_path, generated_at_utc)
        aggregated_files.extend(res_inventory)

        packages_status["result_package"] = {
            "name": result_path.name,
            "path": result_path.as_posix(),
            "exists": True,
            "is_dir": is_dir,
            "bagit_status": bagit_report.get("status", "failed"),
            "file_count": len(res_inventory),
            "doi": desc_meta.get("doi") or config.get("doi"),
            "source_url": desc_meta.get("source_url") or config.get("source_url"),
            "metadata": {
                "title": desc_meta.get("title") or config.get("title"),
                "bag_info": bag_info,
                "descriptive": desc_meta,
                "technical": tech_meta,
            },
        }
    else:
        packages_status["result_package"] = {
            "name": result_path.name,
            "path": result_path.as_posix(),
            "exists": False,
            "required": True,
        }

    # 2. Audit Log Package (could be zip/tar, incomplete, or dir)
    if log_path.exists():
        is_dir = log_path.is_dir()
        log_size = log_path.stat().st_size
        archive_status = "ok"

        # Try to scan zip or check if incomplete
        log_inventory = []
        if is_dir:
            log_inventory = build_inventory(log_path, generated_at_utc)
            aggregated_files.extend(log_inventory)
        else:
            # It's a file. If it's a zip or tar, we can record standard archive details.
            # In our case, the 18GB Log archive might be incomplete. We handle it safely:
            suffix = log_path.suffix.lower()
            if suffix == ".zip":
                import zipfile

                try:
                    with zipfile.ZipFile(log_path, "r") as zf:
                        zf.testzip()
                except Exception:
                    archive_status = "incomplete_or_corrupt_archive"
            elif suffix == ".tar" or (
                suffix == ".zip" and log_size > 0
            ):  # Handles tar named as zip
                import tarfile

                try:
                    with tarfile.open(log_path, "r"):
                        pass
                except Exception:
                    archive_status = "incomplete_or_corrupt_archive"

        packages_status["log_package"] = {
            "name": log_path.name,
            "path": log_path.as_posix(),
            "exists": True,
            "is_dir": is_dir,
            "size_bytes": log_size,
            "archive_status": archive_status,
            "file_count": len(log_inventory) if is_dir else None,
        }
    else:
        packages_status["log_package"] = {
            "name": log_path.name,
            "path": log_path.as_posix(),
            "exists": False,
            "required": False,
        }

    # 3. Calculate aggregated coverage
    coverage_records = build_modality_coverage(aggregated_files, generated_at_utc)
    coverage_summary = {}
    for r in coverage_records:
        coverage_summary[r.modality] = {
            "file_count": r.file_count,
            "row_count": r.row_count,
            "total_size_bytes": r.total_size_bytes,
            "expected_cells": r.expected_cells,
            "observed_cells": r.observed_cells,
            "coverage_ratio": r.coverage_ratio,
            "status": r.status,
        }

    # 4. Construct Manifest JSON
    manifest = {
        "schema_version": COLLECTION_SCHEMA_VERSION,
        "dataset_id": config.get("dataset_id", "unknown"),
        "title": config.get("title", "unknown"),
        "generated_at_utc": generated_at_utc,
        "provenance": {
            "tool_name": "mbp audit collection",
            "tool_version": __version__,
        },
        "packages": packages_status,
        "aggregated_modality_coverage": coverage_summary,
    }

    return manifest
