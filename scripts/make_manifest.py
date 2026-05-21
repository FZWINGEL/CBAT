"""Convenience wrapper for manifest generation.

Prefer `uv run mbp audit manifest ...` for normal use.
"""

from mbp.cli import app


if __name__ == "__main__":
    app()
