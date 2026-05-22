"""Unit tests for Gate 3: LOG_AGE ingestion, splitting, and new CLI subcommands."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from mbp.data.schema_contracts import (
    CHECKUP_EVENT_TABLE_SCHEMA,
    CONDITION_TABLE_SCHEMA,
    INTERVAL_SUBSET_REGISTRY_SCHEMA,
    INTERVAL_TABLE_SCHEMA,
    MODALITY_TABLE_LOG_AGE_SCHEMA,
    SPLIT_REGISTRY_SCHEMA,
    validate_table,
)
from mbp.audit.log_age_monotonicity import write_log_age_monotonicity_report
from mbp.data.products.interval_table import build_interval_table
from mbp.data.products.interval_table import run_interval_qa
from mbp.data.products.interval_subsets import build_interval_subset_registry
from mbp.data.products.interval_subsets import classify_interval_policy
from mbp.data.splitting import audit_split_registry, generate_split_registry


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
        "voltage_window_family": [],
        "soc_window_approx": [],
        "nominal_charge_C_rate": [],
        "nominal_discharge_C_rate": [],
        "profile_label": [],
        "source_file": [],
        "source_archive": [],
        "schema_version": [],
    }
    aging_modes = ["calendar", "cyclic", "profile"]
    temps = [25.0, 0.0, 40.0, 10.0, 35.0]
    voltage_windows = [
        ("2.50 V - 4.20 V", "approx_0_100"),
        ("3.25 V - 4.20 V", "approx_10_100"),
        ("3.25 V - 4.09 V", "approx_10_90"),
        ("3.30 V - 3.30 V", "calendar_soc_50"),
        ("4.20 V - 4.20 V", "calendar_soc_100"),
    ]
    soc_windows = ["10%", "0%", "90%", "50%", "100%"]
    charge_rates = [1.0, 0.5, 5.0 / 3.0, 1.5, 3.0]

    for p in range(1, n_params + 1):
        for r in range(1, 4):
            records["cell_id"].append(f"P{p:03d}_{r}")
            records["parameter_set"].append(p)
            records["replicate_id"].append(r)
            records["aging_mode"].append(aging_modes[p % len(aging_modes)])
            records["nominal_temperature_C"].append(temps[p % len(temps)])
            voltage_window, voltage_family = voltage_windows[p % len(voltage_windows)]
            records["voltage_window"].append(voltage_window)
            records["voltage_window_family"].append(voltage_family)
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


def _make_checkup_parquet(interim_dir: Path, *, timestamp_offset: float = 0.0) -> Path:
    records = {
        "cell_id": ["P001_1", "P001_1", "P001_1"],
        "parameter_set": [1, 1, 1],
        "replicate_id": [1, 1, 1],
        "checkup_k": [0, 1, 2],
        "timestamp": [
            timestamp_offset + 100.0,
            timestamp_offset + 200.0,
            timestamp_offset + 350.0,
        ],
        "capacity_Ah": [3.0, 2.9, 2.7],
        "capacity_soh": [1.0, 0.966, 0.9],
        "charge_energy_Wh": [10.0, 9.0, 8.0],
        "discharge_energy_Wh": [9.0, 8.0, 7.0],
        "temperature_context": ["RT", "RT", "RT"],
        "source_file": ["eoc.csv", "eoc.csv", "eoc.csv"],
        "source_archive": ["eoc.zip", "eoc.zip", "eoc.zip"],
        "schema_version": ["gate2.eoc.v2", "gate2.eoc.v2", "gate2.eoc.v2"],
        "quality_flags": ["", "", ""],
    }
    path = interim_dir / "checkup_event_table.parquet"
    pq.write_table(pa.Table.from_pydict(records, schema=CHECKUP_EVENT_TABLE_SCHEMA), path)
    return path


def _make_log_age_parquet(interim_dir: Path, *, out_of_order: bool = False) -> Path:
    timestamps = [20.0, 80.0, 140.0, 200.0]
    efc = [10.0, 11.0, 12.0, 13.0]
    if out_of_order:
        timestamps = [20.0, 80.0, 70.0, 200.0]
        efc = [10.0, 11.0, 10.5, 13.0]
    records = {
        "cell_id": ["P001_1"] * 4,
        "timestamp_s": timestamps,
        "v_raw_V": [3.4, 3.5, 3.6, 3.7],
        "ocv_est_V": [3.45, 3.55, 3.65, 3.75],
        "i_raw_A": [-1.0, -2.0, 1.0, 2.0],
        "t_cell_degC": [24.0, 25.0, 26.0, 27.0],
        "soc_est": [40.0, 45.0, 50.0, 55.0],
        "delta_q_Ah": [0.0, 1.0, 2.0, 3.0],
        "EFC": efc,
        "cap_aged_est_Ah": [None, 2.9, None, None],
        "R0_mOhm": [None, None, 20.0, None],
        "R1_mOhm": [None, None, None, 25.0],
        "source_file": ["log.csv"] * 4,
        "source_archive": ["log.7z"] * 4,
        "quality_flags": [""] * 4,
    }
    path = interim_dir / "modality_table_log_age.parquet"
    pq.write_table(pa.Table.from_pydict(records, schema=MODALITY_TABLE_LOG_AGE_SCHEMA), path)
    return path


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
        """Temperature OOD holdouts: 0°C -> 1, 40°C -> 2, otherwise -> 0."""
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
            elif temp == 40.0:
                assert fold == 2, f"Cell {cell_id} at 40°C should have temp_holdout=2"
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

    def test_split_registry_audit_reports_non_empty_ood_folds(self, tmp_path: Path) -> None:
        cond_path = _make_condition_parquet(tmp_path, n_params=10)
        out_dir = tmp_path / "splits"
        split_table = generate_split_registry(cond_path, out_dir)
        report_path = tmp_path / "split_registry_report.json"

        report = audit_split_registry(out_dir / "split_registry_v1.parquet", cond_path, report_path)

        assert report_path.exists()
        assert len(split_table) == report["row_count"]
        assert report["status"] == "passed"
        assert report["replicates_grouped_by_parameter_set"] is True
        assert report["temperature_holdout_fold_counts"]["2"] > 0
        assert report["c_rate_holdout_fold_counts"]["1"] > 0
        assert report["voltage_window_holdout_fold_counts"]["1"] > 0
        assert report["voltage_window_holdout_fold_counts"]["2"] > 0

    def test_replicates_share_all_split_views(self, tmp_path: Path) -> None:
        cond_path = _make_condition_parquet(tmp_path, n_params=10)
        table = generate_split_registry(cond_path, tmp_path / "splits")
        rows = table.to_pylist()
        split_columns = [
            "condition_fold",
            "temperature_holdout_fold",
            "voltage_window_holdout_fold",
            "soc_window_holdout_fold",
            "c_rate_holdout_fold",
            "profile_holdout_fold",
            "replicate_calibration_fold",
            "time_horizon_fold",
        ]

        for column in split_columns:
            folds_by_param: dict[int, set[int]] = {}
            for row in rows:
                if column == "replicate_calibration_fold":
                    continue
                folds_by_param.setdefault(row["parameter_set"], set()).add(row[column])
            assert all(len(folds) == 1 for folds in folds_by_param.values())


# ---------------------------------------------------------------------------
# LOG_AGE Monotonicity Report Tests
# ---------------------------------------------------------------------------


class TestLogAgeMonotonicityReport:
    """Tests for detailed LOG_AGE monotonicity violation reporting."""

    def test_writes_detail_parquet_and_summary_csv(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        log_age_path = _make_log_age_parquet(interim_dir, out_of_order=True)
        out = tmp_path / "violations.parquet"
        summary = tmp_path / "summary.csv"

        report = write_log_age_monotonicity_report(log_age_path, out, summary)

        assert report["violation_count"] == 1
        assert report["timestamp_decrease_count"] == 1
        assert report["efc_decrease_count"] == 1
        detail = pq.read_table(out).to_pylist()
        assert detail[0]["violation_type"] == "both"
        assert detail[0]["cell_id"] == "P001_1"
        assert "cell,P001_1,1,1,1,1" in summary.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Interval Table Tests
# ---------------------------------------------------------------------------


class TestIntervalTable:
    """Tests for the Gate 2 interval-table MVP."""

    def test_builds_interval_rows_and_log_age_summaries(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir)
        _make_log_age_parquet(interim_dir)
        generate_split_registry(cond_path, tmp_path / "splits")

        out_path = interim_dir / "interval_table.parquet"
        table = build_interval_table(interim_dir, out_path)

        assert validate_table(table, INTERVAL_TABLE_SCHEMA, strict=True)
        assert out_path.exists()
        assert len(table) == 2

        rows = table.to_pylist()
        first = rows[0]
        assert first["cell_id"] == "P001_1"
        assert first["checkup_k"] == 0
        assert first["checkup_k_next"] == 1
        assert first["log_age_row_count"] == 2
        assert first["log_age_efc_delta"] == 1.0
        assert first["log_age_delta_q_Ah"] == 1.0
        assert first["log_age_mean_voltage_V"] == 3.45
        assert first["log_age_capacity_diag_rows_masked"] == 1
        assert first["log_age_r0_diag_rows_masked"] == 0
        assert first["log_age_monotonicity_violation_count"] == 0
        assert first["LOG_AGE_monotonicity_clean"] is True
        assert "LOG_AGE_inserted_diagnostics_masked" in first["quality_flags"]

        metadata = pq.read_metadata(out_path).metadata
        assert metadata is not None
        assert metadata[b"schema_version"] == b"gate2.interval.v1"
        assert b"split_registry_sha256" in metadata

    def test_aligns_epoch_checkups_to_relative_log_age_time(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir, timestamp_offset=1_665_626_000.0)
        _make_log_age_parquet(interim_dir)
        generate_split_registry(cond_path, tmp_path / "splits")

        table = build_interval_table(interim_dir, interim_dir / "interval_table.parquet")

        first = table.to_pylist()[0]
        assert first["t_result_k_s"] > 1_000_000_000
        assert first["log_age_row_count"] == 2
        assert first["LOG_AGE_available"] is True

    def test_maps_log_age_monotonicity_violations_to_intervals(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir)
        log_age_path = _make_log_age_parquet(interim_dir, out_of_order=True)
        generate_split_registry(cond_path, tmp_path / "splits")
        violations_path = tmp_path / "violations.parquet"
        summary_path = tmp_path / "summary.csv"
        write_log_age_monotonicity_report(log_age_path, violations_path, summary_path)

        table = build_interval_table(
            interim_dir,
            interim_dir / "interval_table.parquet",
            monotonicity_violations_path=violations_path,
        )

        first = table.to_pylist()[0]
        assert first["log_age_monotonicity_violation_count"] == 1
        assert first["log_age_timestamp_decrease_count"] == 1
        assert first["log_age_efc_decrease_count"] == 1
        assert first["LOG_AGE_monotonicity_clean"] is False
        assert "LOG_AGE_monotonicity_violation" in first["quality_flags"]

    def test_interval_qa_reports_contaminated_intervals(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir)
        log_age_path = _make_log_age_parquet(interim_dir, out_of_order=True)
        generate_split_registry(cond_path, tmp_path / "splits")
        violations_path = tmp_path / "violations.parquet"
        write_log_age_monotonicity_report(log_age_path, violations_path, tmp_path / "summary.csv")
        interval_path = interim_dir / "interval_table.parquet"
        build_interval_table(interim_dir, interval_path, monotonicity_violations_path=violations_path)

        report = run_interval_qa(interval_path, tmp_path / "interval_qa_report.json")

        assert report["status"] == "passed"
        assert report["row_count"] == 2
        assert report["expected_interval_count"] == 2
        assert report["intervals_with_monotonicity_violations"] == 1

    def test_interval_cli(self, tmp_path: Path) -> None:
        from typer.testing import CliRunner
        from mbp.cli import app

        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir)
        _make_log_age_parquet(interim_dir)
        generate_split_registry(cond_path, tmp_path / "splits")

        runner = CliRunner()
        out_path = interim_dir / "interval_table.parquet"
        result = runner.invoke(
            app,
            [
                "ingest", "intervals",
                "--interim-dir", str(interim_dir),
                "--out", str(out_path),
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Interval table generated: 2 rows written" in result.output


# ---------------------------------------------------------------------------
# Interval Subset Registry Tests
# ---------------------------------------------------------------------------


class TestIntervalSubsetRegistry:
    """Tests for baseline-readiness interval subset policy outputs."""

    def test_monotonicity_policy_classification(self) -> None:
        small = classify_interval_policy(
            duration_s=100.0,
            log_age_available=True,
            log_age_row_count=10,
            monotonicity_violation_count=1,
            timestamp_decrease_count=0,
            max_timestamp_drop_s=0.0,
            max_efc_drop=0.0002,
        )
        assert small.baseline_clean_strict is False
        assert small.baseline_clean_tolerant is True
        assert small.small_efc_jitter is True

        timestamp_drop = classify_interval_policy(
            duration_s=100.0,
            log_age_available=True,
            log_age_row_count=10,
            monotonicity_violation_count=1,
            timestamp_decrease_count=1,
            max_timestamp_drop_s=1.0,
            max_efc_drop=0.0,
        )
        assert timestamp_drop.baseline_clean_tolerant is False
        assert timestamp_drop.excluded_due_to_timestamp_drop is True

        large_efc = classify_interval_policy(
            duration_s=100.0,
            log_age_available=True,
            log_age_row_count=10,
            monotonicity_violation_count=1,
            timestamp_decrease_count=0,
            max_timestamp_drop_s=0.0,
            max_efc_drop=0.001,
        )
        assert large_efc.baseline_clean_tolerant is False
        assert large_efc.excluded_due_to_large_efc_drop is True

    def test_interval_subset_registry_generation(self, tmp_path: Path) -> None:
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        cond_path = _make_condition_parquet(interim_dir, n_params=1)
        _make_checkup_parquet(interim_dir)
        log_age_path = _make_log_age_parquet(interim_dir, out_of_order=True)
        generate_split_registry(cond_path, tmp_path / "splits")
        violations_path = tmp_path / "violations.parquet"
        write_log_age_monotonicity_report(log_age_path, violations_path, tmp_path / "summary.csv")
        interval_path = interim_dir / "interval_table.parquet"
        build_interval_table(interim_dir, interval_path, monotonicity_violations_path=violations_path)

        registry_path = tmp_path / "interval_subset_registry_v1.parquet"
        report_path = tmp_path / "interval_subset_report.json"
        table = build_interval_subset_registry(interval_path, registry_path, report_path)

        assert validate_table(table, INTERVAL_SUBSET_REGISTRY_SCHEMA, strict=True)
        rows = table.to_pylist()
        assert rows[0]["baseline_clean_strict"] is False
        assert rows[0]["baseline_clean_tolerant"] is False
        assert rows[0]["excluded_due_to_timestamp_drop"] is True
        assert rows[1]["baseline_clean_strict"] is True
        assert rows[1]["baseline_clean_tolerant"] is True
        report = report_path.read_text(encoding="utf-8")
        assert '"row_count": 2' in report


# ---------------------------------------------------------------------------
# LOG_AGE QA Tests
# ---------------------------------------------------------------------------


class TestLogAgeQA:
    """Tests for LOG_AGE QA checks that avoid full-table materialization."""

    def test_log_age_qa_flags_out_of_order_timestamp_and_efc(self, tmp_path: Path) -> None:
        from mbp.data.luh_blank.qa_result_data import _qa_log_age

        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        log_age_path = _make_log_age_parquet(interim_dir, out_of_order=True)
        report = {"status": "passed", "tables": {}, "failures": []}

        _qa_log_age(log_age_path, report)

        assert report["status"] == "failed"
        assert report["tables"]["modality_table_log_age"]["monotonic_timestamp_efc_violations"] == 1
        assert any("monotonicity violations" in failure for failure in report["failures"])

    def test_log_age_qa_reports_diagnostic_null_rates(self, tmp_path: Path) -> None:
        from mbp.data.luh_blank.qa_result_data import _qa_log_age

        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        log_age_path = _make_log_age_parquet(interim_dir)
        report = {"status": "passed", "tables": {}, "failures": []}

        _qa_log_age(log_age_path, report)

        meta = report["tables"]["modality_table_log_age"]
        assert meta["row_count"] == 4
        assert meta["diagnostic_null_counts"]["cap_aged_est_Ah"] == 3
        assert meta["diagnostic_nonnull_counts"]["R0_mOhm"] == 1


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
        """SPLIT_REGISTRY_SCHEMA should have 12 fields."""
        assert len(SPLIT_REGISTRY_SCHEMA) == 12

    def test_split_registry_schema_required_fields(self) -> None:
        """All required field names should be present."""
        expected = {
            "cell_id", "parameter_set", "replicate_id",
            "condition_fold", "temperature_holdout_fold",
            "voltage_window_holdout_fold",
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

    def test_ingest_log_age_cli(self, tmp_path: Path) -> None:
        """Test `mbp ingest log-age` CLI command."""
        from typer.testing import CliRunner
        from mbp.cli import app
        import py7zr

        archive_path = tmp_path / "cell_log_age_ultracompr.7z"
        out_dir = tmp_path / "interim"
        exclusions_path = tmp_path / "excluded_records_report.csv"

        csv_header = "timestamp_s;v_raw_V;ocv_est_V;i_raw_A;t_cell_degC;soc_est;delta_q_Ah;EFC;cap_aged_est_Ah;R0_mOhm;R1_mOhm\n"
        cohort_csv = csv_header + "100.0;3.4;3.5;-1.0;25.0;50.0;1.2;10.0;2.9;20.0;25.0\n"

        with py7zr.SevenZipFile(archive_path, "w") as z:
            z.writestr(cohort_csv, "cell_log_age_2s_P001_1_S01_C01.csv")

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "ingest", "log-age",
                "--archive", str(archive_path),
                "--out-dir", str(out_dir),
                "--exclusions-report", str(exclusions_path),
                "--csv-block-size-bytes", "128",
            ],
        )
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert (out_dir / "modality_table_log_age.parquet").exists()
        assert "LOG_AGE ingestion complete: 1 rows written" in result.output


class TestLogAgeIngestion:
    """Tests verifying the LOG_AGE ingestion logic, semicolon CSV parsing, and cohort filtering."""

    def test_ingest_log_age_parser(self, tmp_path: Path) -> None:
        """Test LOG_AGE ingestion from a synthetic 7z archive."""
        import py7zr
        from mbp.data.luh_blank.parse_log import ingest_log_age

        archive_path = tmp_path / "cell_log_age_ultracompr.7z"
        out_dir = tmp_path / "interim"
        exclusions_path = tmp_path / "excluded_records_report.csv"

        csv_header = "timestamp_s;v_raw_V;ocv_est_V;i_raw_A;t_cell_degC;soc_est;delta_q_Ah;EFC;cap_aged_est_Ah;R0_mOhm;R1_mOhm\n"
        cohort_csv = csv_header + "100.0;3.4;3.5;-1.0;25.0;50.0;1.2;10.0;2.9;20.0;25.0\n" + "200.0;3.3;3.4;-1.0;25.0;48.0;1.4;10.5;nan;nan;nan\n"
        auxiliary_csv = csv_header + "100.0;3.4;3.5;-1.0;25.0;50.0;1.2;10.0;2.9;20.0;25.0\n"

        # Create synthetic 7z archive
        with py7zr.SevenZipFile(archive_path, "w") as z:
            z.writestr(cohort_csv, "cell_log_age_2s_P001_1_S01_C01.csv")
            z.writestr(auxiliary_csv, "cell_log_age_2s_P000_0_S01_C01.csv")

        # Parse and ingest
        table = ingest_log_age(
            archive_path,
            out_dir,
            exclusions_report_path=exclusions_path,
            csv_block_size_bytes=128,
        )
        assert isinstance(table, pa.Table)

        # Verify return value and parquet exist
        assert out_dir.exists()
        parquet_path = out_dir / "modality_table_log_age.parquet"
        assert parquet_path.exists()

        # Read back table and validate
        table_read = pq.read_table(parquet_path)
        assert validate_table(table_read, MODALITY_TABLE_LOG_AGE_SCHEMA, strict=True)

        # Assert cohort data is correct and parsed cleanly
        pydict = table_read.to_pydict()
        assert pydict["cell_id"] == ["P001_1", "P001_1"]
        assert pydict["timestamp_s"] == [100.0, 200.0]
        assert pydict["cap_aged_est_Ah"] == [2.9, None]  # nan mapped to null
        assert pydict["R0_mOhm"] == [20.0, None]
        assert pydict["R1_mOhm"] == [25.0, None]
        assert pydict["source_file"] == ["cell_log_age_2s_P001_1_S01_C01.csv", "cell_log_age_2s_P001_1_S01_C01.csv"]
        assert pydict["source_archive"] == ["cell_log_age_ultracompr.7z", "cell_log_age_ultracompr.7z"]

        # Verify exclusion of auxiliary cell
        assert exclusions_path.exists()
        exclusions_text = exclusions_path.read_text(encoding="utf-8")
        assert "P000_0" in exclusions_text
        assert "Auxiliary cell outside expected 228-cell cohort" in exclusions_text
