"""Luh-Blank audit entry points."""

from pathlib import Path

from mbp.audit.manifest import build_manifest
from mbp.audit.models import DatasetManifest


def audit_dataset(data_root: Path) -> DatasetManifest:
    """Build a provenance manifest for a Luh-Blank local data root."""

    return build_manifest(data_root)
