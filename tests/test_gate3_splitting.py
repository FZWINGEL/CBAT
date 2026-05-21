"""Unit tests for Gate 3: LOG_AGE ingestion, splitting, and new CLI subcommands."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.data.schema_contracts import (
    CONDITION_TABLE_SCHEMA,
    MODALITY_TABLE_LOG_AGE_SCHEMA,
    SPLIT_REGISTRY_SCHEMA,
    validate_table,
)
from mbp.data.splitting import generate_split_registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_condition_parquet(tmp_path: Path, n_params: int = 5) -> Path:
    """Create a synthetic cell_condition_table.parquet with n_params x 3 replicates."""
    records: dict[str, list] = {
        "cell_id": [],
        "parameter_set": [],
        "replicate_id": [],
        "aging_mode": [],
        "nominal_temperature_C": [],
        "voltage_window": [],
        "soc_window_approx": [],
        "nominal_charge_C_rate": [],
        "nominal_discharge_C_rate": [],
        "profile_label": [],
        "source_file": [],
        "source_archive": [],
        "schema_version": [],
    }
    aging_modes = ["calendar", "cyclic", "profile"]
    temps = [25.0, 0.0, 45.0, 10.0, 35.0]
    soc_windows = ["10-90", "0-100", "40-60", "20-80", "45-55"]
    charge_rates = [1.0, 0.5, 2.0, 1.5, 3.0]

    for p in range(1, n_params + 1):
        for r in range(1, 4):
            records["cell_id"].append(f"P{p:03d}_{r}")
            records["parameter_set"].append(p)
            records["replicate_id"].append(r)
            records["aging_mode"].append(aging_modes[p % len(aging_modes)])
            records["nominal_temperature_C"].append(temps[p % len(temps)])
            records["voltage_window"].append("2.5-4.2")
            records["soc_window_approx"].append(soc_windows[p % len(soc_windows)])
            records["nominal_charge_C_rate"].append(charge_rates[p % len(charge_rates)])
            records["nominal_discharge_C_rate"].append(1.0)
            records["profile_label"].append("CC" if p % 3 != 0 else "WLTP")
            records["source_file"].append(f"cell_cfg_P{p:03d}_{r}_S01_C01.csv")
            records["source_archive"].append("cfg.zip")
            records["schema_version"].append("gate2.cfg.v1")

    table = pa.Table.from_pydict(records, schema=CONDITION_TABLE_SCHEMA)
    out_path = tmp_path / "cell_condition_table.parquet"
    pq.write_table(table, out_path)
    return out_path


# ---------------------------------------------------------------------------
# Splitting Engine Tests
# ---------------------------------------------------------------------------


class TestSplittingEngine:
    """Tests for the deterministic condition-grouped splitting engine."""

    def test_generates_valid_split_registry(self, tmp_path: Path) -> None:
        """Split registry should match the schema contract."""
        cond_path = _make_condition_parquet(tmp_path, n_params=10)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)

        assert validate_table(table, SPLIT_REGISTRY_SCHEMA, strict=True)
        assert len(table) == 30  # 10 params x 3 replicates
        assert (out_dir / "split_registry_v1.parquet").exists()

    def test_replicates_share_condition_fold(self, tmp_path: Path) -> None:
        """Replicates of the same parameter_set MUST reside in the same condition_fold.

        This is the critical leakage prevention guarantee.
        """
        cond_path = _make_condition_parquet(tmp_path, n_params=20)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)

        # Group by parameter_set and verify all replicates have the same fold
        param_sets = table.column("parameter_set").to_pylist()
        condition_folds = table.column("condition_fold").to_pylist()

        param_to_folds: dict[int, set[int]] = {}
        for param, fold in zip(param_sets, condition_folds):
            param_to_folds.setdefault(param, set()).add(fold)

        for param, folds in param_to_folds.items():
            assert len(folds) == 1, (
                f"Parameter set {param} has replicates in multiple folds: {folds}. "
                f"This is a data leakage violation!"
            )

    def test_condition_folds_are_balanced(self, tmp_path: Path) -> None:
        """The 5 condition folds should be roughly balanced across parameter sets."""
        cond_path = _make_condition_parquet(tmp_path, n_params=20)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)

        # Count unique parameter sets per fold
        param_sets = table.column("parameter_set").to_pylist()
        condition_folds = table.column("condition_fold").to_pylist()

        fold_params: dict[int, set[int]] = {}
        for param, fold in zip(param_sets, condition_folds):
            fold_params.setdefault(fold, set()).add(param)

        # All 5 folds should be present
        assert len(fold_params) == 5
        # Each fold should have at least 1 and at most ceil(20/5) = 4 parameter sets
        for fold, params in fold_params.items():
            assert 1 <= len(params) <= 6, (
                f"Fold {fold} has {len(params)} parameter sets, expected 1-6"
            )

    def test_temperature_holdout_mapping(self, tmp_path: Path) -> None:
        """Temperature OOD holdouts: 0°C → 1, 45°C → 2, otherwise → 0."""
        cond_path = _make_condition_parquet(tmp_path, n_params=5)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)

        cell_ids = table.column("cell_id").to_pylist()
        temp_folds = table.column("temperature_holdout_fold").to_pylist()

        # Read condition table to get temperature mapping
        cond_table = pq.read_table(cond_path)
        cond_cell_ids = cond_table.column("cell_id").to_pylist()
        cond_temps = cond_table.column("nominal_temperature_C").to_pylist()
        temp_by_cell = dict(zip(cond_cell_ids, cond_temps))

        for cell_id, fold in zip(cell_ids, temp_folds):
            temp = temp_by_cell[cell_id]
            if temp == 0.0:
                assert fold == 1, f"Cell {cell_id} at 0°C should have temp_holdout=1"
            elif temp == 45.0:
                assert fold == 2, f"Cell {cell_id} at 45°C should have temp_holdout=2"
            else:
                assert fold == 0, f"Cell {cell_id} at {temp}°C should have temp_holdout=0"

    def test_replicate_calibration_fold(self, tmp_path: Path) -> None:
        """Replicate 3 should be assigned calibration fold 1, others fold 0."""
        cond_path = _make_condition_parquet(tmp_path, n_params=5)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)

        rep_ids = table.column("replicate_id").to_pylist()
        cal_folds = table.column("replicate_calibration_fold").to_pylist()

        for rep, fold in zip(rep_ids, cal_folds):
            if rep == 3:
                assert fold == 1, f"Replicate {rep} should have calibration fold 1"
            else:
                assert fold == 0, f"Replicate {rep} should have calibration fold 0"

    def test_deterministic_reproducibility(self, tmp_path: Path) -> None:
        """Two independent calls should produce identical splits (seed=42)."""
        cond_path = _make_condition_parquet(tmp_path, n_params=10)
        out_dir_1 = tmp_path / "splits_1"
        out_dir_2 = tmp_path / "splits_2"

        table_1 = generate_split_registry(cond_path, out_dir_1)
        table_2 = generate_split_registry(cond_path, out_dir_2)

        assert table_1.column("condition_fold").to_pylist() == table_2.column("condition_fold").to_pylist()
        assert table_1.column("temperature_holdout_fold").to_pylist() == table_2.column("temperature_holdout_fold").to_pylist()

    def test_missing_condition_table_raises(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for a non-existent condition table."""
        with pytest.raises(FileNotFoundError):
            generate_split_registry(
                tmp_path / "does_not_exist.parquet",
                tmp_path / "splits",
            )

    def test_schema_version_populated(self, tmp_path: Path) -> None:
        """Schema version column should be uniformly populated."""
        cond_path = _make_condition_parquet(tmp_path, n_params=3)
        out_dir = tmp_path / "splits"

        table = generate_split_registry(cond_path, out_dir)
        versions = table.column("schema_version").to_pylist()
        assert all(v == "gate3.split.v1" for v in versions)


# ---------------------------------------------------------------------------
# LOG_AGE Schema Tests
# ---------------------------------------------------------------------------


class TestLogAgeSchema:
    """Tests verifying the LOG_AGE schema contract."""

    def test_log_age_schema_field_count(self) -> None:
        """MODALITY_TABLE_LOG_AGE_SCHEMA should have 15 fields."""
        assert len(MODALITY_TABLE_LOG_AGE_SCHEMA) == 15

    def test_log_age_schema_required_fields(self) -> None:
        """All required field names should be present."""
        expected = {
            "cell_id", "timestamp_s", "v_raw_V", "ocv_est_V", "i_raw_A",
            "t_cell_degC", "soc_est", "delta_q_Ah", "EFC", "cap_aged_est_Ah",
            "R0_mOhm", "R1_mOhm", "source_file", "source_archive", "quality_flags",
        }
        actual = {MODALITY_TABLE_LOG_AGE_SCHEMA.field(i).name for i in range(len(MODALITY_TABLE_LOG_AGE_SCHEMA))}
        assert actual == expected

    def test_log_age_schema_types(self) -> None:
        """Numeric fields should be float64, string fields should be string."""
        for i in range(len(MODALITY_TABLE_LOG_AGE_SCHEMA)):
            field = MODALITY_TABLE_LOG_AGE_SCHEMA.field(i)
            if field.name in ("cell_id", "source_file", "source_archive", "quality_flags"):
                assert field.type == pa.string(), f"{field.name} should be string"
            else:
                assert field.type == pa.float64(), f"{field.name} should be float64"


# ---------------------------------------------------------------------------
# Split Registry Schema Tests
# ---------------------------------------------------------------------------


class TestSplitRegistrySchema:
    """Tests verifying the split registry schema contract."""

    def test_split_registry_schema_field_count(self) -> None:
        """SPLIT_REGISTRY_SCHEMA should have 11 fields."""
        assert len(SPLIT_REGISTRY_SCHEMA) == 11

    def test_split_registry_schema_required_fields(self) -> None:
        """All required field names should be present."""
        expected = {
            "cell_id", "parameter_set", "replicate_id",
            "condition_fold", "temperature_holdout_fold",
            "soc_window_holdout_fold", "c_rate_holdout_fold",
            "profile_holdout_fold", "replicate_calibration_fold",
            "time_horizon_fold", "schema_version",
        }
        actual = {SPLIT_REGISTRY_SCHEMA.field(i).name for i in range(len(SPLIT_REGISTRY_SCHEMA))}
        assert actual == expected


# ---------------------------------------------------------------------------
# CLI Subcommand Tests
# ---------------------------------------------------------------------------


class TestCLISubcommands:
    """Tests for the new CLI subcommands using CliRunner."""

    def test_split_generate_cli(self, tmp_path: Path) -> None:
        """Test `mbp split generate` via CliRunner."""
        from typer.testing import CliRunner
        from mbp.cli import app

        runner = CliRunner()
        cond_path = _make_condition_parquet(tmp_path, n_params=5)
        out_dir = tmp_path / "splits"

        result = runner.invoke(
            app,
            [
                "split", "generate",
                "--condition-table", str(cond_path),
                "--out-dir", str(out_dir),
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert (out_dir / "split_registry_v1.parquet").exists()
        assert "Split registry generated" in result.output

    def test_split_generate_missing_input(self, tmp_path: Path) -> None:
        """Test `mbp split generate` with a non-existent condition table."""
        from typer.testing import CliRunner
        from mbp.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "split", "generate",
                "--condition-table", str(tmp_path / "missing.parquet"),
                "--out-dir", str(tmp_path / "splits"),
            ],
        )
        assert result.exit_code != 0

