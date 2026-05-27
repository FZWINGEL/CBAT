"""Paper-facing report generation helpers."""

from __future__ import annotations

from mbp.reporting.manuscript_checks import check_manuscript, check_reader_manuscript
from mbp.reporting.manuscript_figures import build_manuscript_figures
from mbp.reporting.manuscript_tables import build_manuscript_assets, build_manuscript_tables
from mbp.reporting.benchmark_tasks import (
    benchmark_leaderboard_rows,
    check_benchmark_tasks,
    load_benchmark_task_registry,
    write_benchmark_leaderboard,
    write_benchmark_model_cards,
    write_benchmark_task_cards,
    write_benchmark_task_check,
)
from mbp.reporting.release_checks import check_release_candidate, write_release_candidate_check

__all__ = [
    "benchmark_leaderboard_rows",
    "build_manuscript_assets",
    "build_manuscript_figures",
    "build_manuscript_tables",
    "check_benchmark_tasks",
    "check_manuscript",
    "check_reader_manuscript",
    "check_release_candidate",
    "load_benchmark_task_registry",
    "write_benchmark_leaderboard",
    "write_benchmark_model_cards",
    "write_benchmark_task_cards",
    "write_benchmark_task_check",
    "write_release_candidate_check",
]
