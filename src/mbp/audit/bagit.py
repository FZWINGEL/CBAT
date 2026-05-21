"""BagIt package integrity auditing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mbp import __version__
from mbp.audit.hashing import md5_file
from mbp.audit.inventory import utc_now_iso
from mbp.audit.manifest import current_commit

SCHEMA_VERSION = "gate1.audit.bagit.v1"


def parse_manifest(manifest_path: Path) -> dict[str, str]:
    """Parse a BagIt manifest-md5.txt or tagmanifest-md5.txt.

    Returns a dict mapping relative path (str) to expected MD5 hex hash (str).
    """
    if not manifest_path.exists():
        return {}

    mapping: dict[str, str] = {}
    with manifest_path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            # Splitting by first whitespace chunk.
            # Standard is: hex_hash  relative_path (or hex_hash *relative_path)
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            hash_val = parts[0].strip()
            rel_path = parts[1].strip()
            if rel_path.startswith("*"):
                rel_path = rel_path[1:]
            mapping[rel_path] = hash_val
    return mapping


def validate_bagit(data_root: Path) -> dict[str, Any]:
    """Perform a deep validation of the BagIt container at ``data_root``.

    Validates manifest-md5.txt and tagmanifest-md5.txt.
    Reports ok, missing, hash_mismatch, and unexpected files.
    """
    generated_at_utc = utc_now_iso()
    provenance = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "tool_name": "mbp audit bagit",
        "tool_version": __version__,
        "data_root_input": str(data_root),
        "data_root_exists": data_root.exists(),
        "preprocessing_commit": current_commit(Path.cwd()),
    }

    if not data_root.exists():
        return {
            "provenance": provenance,
            "status": "failed",
            "errors": [f"Data root directory '{data_root}' does not exist."],
            "validated_files": [],
        }

    manifest_path = data_root / "manifest-md5.txt"
    tagmanifest_path = data_root / "tagmanifest-md5.txt"

    errors: list[str] = []
    validated_files: list[dict[str, Any]] = []

    # 1. Validate tagmanifest
    tagmanifest_status = "passed"
    tag_manifest_exists = tagmanifest_path.exists()
    if not tag_manifest_exists:
        # A tagmanifest is technically optional in BagIt spec, but we require it or warn
        errors.append("tagmanifest-md5.txt is missing from package root.")
        tagmanifest_status = "failed"
    else:
        tag_expected = parse_manifest(tagmanifest_path)
        for rel_path, expected_hash in sorted(tag_expected.items()):
            full_path = data_root / rel_path
            if not full_path.exists():
                errors.append(
                    f"Tag file '{rel_path}' is listed in tagmanifest but missing from disk."
                )
                validated_files.append(
                    {
                        "file": rel_path,
                        "expected_hash": expected_hash,
                        "actual_hash": None,
                        "status": "missing",
                        "type": "tag",
                    }
                )
                tagmanifest_status = "failed"
            else:
                actual_hash = md5_file(full_path)
                if actual_hash.lower() != expected_hash.lower():
                    errors.append(
                        f"Hash mismatch for tag file '{rel_path}': expected {expected_hash}, got {actual_hash}."
                    )
                    validated_files.append(
                        {
                            "file": rel_path,
                            "expected_hash": expected_hash,
                            "actual_hash": actual_hash,
                            "status": "hash_mismatch",
                            "type": "tag",
                        }
                    )
                    tagmanifest_status = "failed"
                else:
                    validated_files.append(
                        {
                            "file": rel_path,
                            "expected_hash": expected_hash,
                            "actual_hash": actual_hash,
                            "status": "ok",
                            "type": "tag",
                        }
                    )

    # 2. Validate payload manifest
    manifest_status = "passed"
    payload_manifest_exists = manifest_path.exists()
    if not payload_manifest_exists:
        errors.append("manifest-md5.txt is missing from package root.")
        manifest_status = "failed"
    else:
        payload_expected = parse_manifest(manifest_path)

        # Track which files inside data/ are expected
        expected_payload_paths: set[str] = set()

        for rel_path, expected_hash in sorted(payload_expected.items()):
            expected_payload_paths.add(rel_path)
            full_path = data_root / rel_path
            if not full_path.exists():
                errors.append(
                    f"Payload file '{rel_path}' is listed in manifest but missing from disk."
                )
                validated_files.append(
                    {
                        "file": rel_path,
                        "expected_hash": expected_hash,
                        "actual_hash": None,
                        "status": "missing",
                        "type": "payload",
                    }
                )
                manifest_status = "failed"
            else:
                actual_hash = md5_file(full_path)
                if actual_hash.lower() != expected_hash.lower():
                    errors.append(
                        f"Hash mismatch for payload file '{rel_path}': expected {expected_hash}, got {actual_hash}."
                    )
                    validated_files.append(
                        {
                            "file": rel_path,
                            "expected_hash": expected_hash,
                            "actual_hash": actual_hash,
                            "status": "hash_mismatch",
                            "type": "payload",
                        }
                    )
                    manifest_status = "failed"
                else:
                    validated_files.append(
                        {
                            "file": rel_path,
                            "expected_hash": expected_hash,
                            "actual_hash": actual_hash,
                            "status": "ok",
                            "type": "payload",
                        }
                    )

        # 3. Check for unexpected files in data/
        data_dir = data_root / "data"
        if data_dir.exists():
            for p in sorted(data_dir.rglob("*")):
                if p.is_file():
                    rel_p = p.relative_to(data_root).as_posix()
                    if (
                        ":Zone.Identifier" in rel_p
                        or p.name.startswith(".")
                        or p.name == "Thumbs.db"
                    ):
                        continue
                    if rel_p not in expected_payload_paths:
                        # Exclude some common system/git ignore artifacts if needed,
                        # but strictly report all unexpected files.
                        errors.append(f"Unexpected payload file found: '{rel_p}'")
                        validated_files.append(
                            {
                                "file": rel_p,
                                "expected_hash": None,
                                "actual_hash": None,
                                "status": "unexpected",
                                "type": "payload",
                            }
                        )
                        manifest_status = "failed"

    status = (
        "passed" if (tagmanifest_status == "passed" and manifest_status == "passed") else "failed"
    )

    return {
        "provenance": provenance,
        "status": status,
        "manifest_status": manifest_status,
        "tagmanifest_status": tagmanifest_status,
        "validated_files": validated_files,
        "errors": errors,
    }
