"""Paper-facing report generation helpers."""

from __future__ import annotations

from mbp.reporting.manuscript_checks import check_manuscript, check_reader_manuscript
from mbp.reporting.manuscript_figures import build_manuscript_figures
from mbp.reporting.manuscript_tables import build_manuscript_assets, build_manuscript_tables
from mbp.reporting.release_checks import check_release_candidate, write_release_candidate_check

__all__ = [
    "build_manuscript_assets",
    "build_manuscript_figures",
    "build_manuscript_tables",
    "check_manuscript",
    "check_reader_manuscript",
    "check_release_candidate",
    "write_release_candidate_check",
]
