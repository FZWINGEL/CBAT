"""Dataset discovery placeholders for Luh-Blank v2."""

from pathlib import Path

from mbp.audit.inventory import build_inventory
from mbp.audit.models import FileInventoryRecord


def discover_files(data_root: Path) -> list[FileInventoryRecord]:
    """Discover files using the generic Gate 1 inventory implementation."""

    return build_inventory(data_root)
