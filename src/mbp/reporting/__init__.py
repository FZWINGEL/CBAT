"""Paper-facing report generation helpers."""

from __future__ import annotations

from mbp.reporting.manuscript_checks import check_manuscript
from mbp.reporting.manuscript_figures import build_manuscript_figures
from mbp.reporting.manuscript_tables import build_manuscript_assets, build_manuscript_tables

__all__ = [
    "build_manuscript_assets",
    "build_manuscript_figures",
    "build_manuscript_tables",
    "check_manuscript",
]
