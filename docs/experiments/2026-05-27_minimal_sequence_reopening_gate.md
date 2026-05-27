# Milestone 7.1 - Minimal Sequence/Neural Reopening Gate

Date: 2026-05-27

## Purpose

This gate tests the charter H7 requirement more directly than Milestone 2.4:
true operational histories must beat shuffled-history and aggregate-only
baselines before any broader sequence or neural model branch is justified.

This is not a CBAT, transformer, multimodal architecture, policy-ranking, or
causal milestone.

## CUDA/PyTorch Environment

WSL can see the Windows NVIDIA driver through `nvidia-smi`:

- GPU: NVIDIA GeForce RTX 5060 Ti
- VRAM: 16,311 MiB
- Driver CUDA capability: 13.2

The project virtualenv now has CUDA-enabled PyTorch installed:

- PyTorch: `2.12.0+cu130`
- CUDA runtime: `13.0`
- `torch.cuda.is_available()`: `True`
- CUDA smoke test: 512 x 512 tensor matmul completed on GPU

Neural rows are valid only with CUDA. CPU fallback is disabled.

## Data Product

Command:

```bash
mbp features build-event-sequences \
  --run-events data/interim/run_event_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/interval_event_sequence_table_v1.parquet \
  --max-events 64 \
  --seed 42
```

QA command:

```bash
mbp features event-sequences-qa \
  --event-sequences data/interim/interval_event_sequence_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/interval_event_sequence_qa_report.json
```

QA result:

| Item | Result |
|---|---:|
| Rows | 3,827 |
| Missing intervals | 0 |
| Extra intervals | 0 |
| Vector length errors | 0 |
| Mask length errors | 0 |
| Leakage check | passed |
| Truncated intervals | 3,826 |
| Max source events per interval | 247,393 |
| Median source events per interval | 627 |

The high truncation count is expected because this gate intentionally uses a
small fixed-length diagnostic vector. It is a reopening falsification check,
not a final sequence representation.

## Baseline Run

Command:

```bash
mbp baseline run-minimal-sequence-reopening \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --event-sequences data/interim/interval_event_sequence_table_v1.parquet \
  --out reports/baselines/minimal_sequence_reopening_report.json \
  --predictions-out data/processed/minimal_sequence_reopening_predictions.parquet \
  --out-dir reports/baselines/minimal_sequence_reopening \
  --reference-sequence-report reports/baselines/capacity_sequence_value_hgb50_report.json \
  --reference-stress-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --model-levels S0_ridge_true_sequence,S1_ridge_shuffled_sequence,S2_torch_mlp_true_sequence,S3_torch_mlp_shuffled_sequence \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --mlp-max-iter 200
```

The run produced 96 metric rows and 82,920 ignored prediction rows.

## Results

Positive gain means the true-sequence candidate has lower condition-mean MAE.

| Comparison | Mean gain | Positive rows | Status |
|---|---:|---:|---|
| True sequence vs shuffled order | 0.0290673 | 26 / 48 | not supported |
| True sequence vs aggregate-event HGB | -0.227321 | 0 / 48 | not supported |
| True sequence vs timestamp-stress HGB | -0.190925 | 0 / 44 | not supported |
| C-rate `delta_capacity_Ah` comparisons | -0.159493 | 1 / 6 | not supported |

The Torch MLP true-sequence rows sometimes beat their shuffled counterparts,
but they do not beat the stronger aggregate-event or timestamp-stress HGB
references. That is the relevant charter test.

## Decision

Milestone 7.1 does not reopen sequence or neural modeling.

Allowed wording:

> Fixed-length event-sequence and CUDA Torch MLP diagnostics do not beat the
> aggregate-event HGB or timestamp-stress HGB controls under grouped validation.

Forbidden wording:

- sequence models are justified;
- neural models are justified;
- CBAT is justified;
- transformers are justified;
- policy ranking is justified;
- true event order improves C-rate fade under the current evidence.

## Remaining Blockers

- True sequence does not beat aggregate-event HGB.
- True sequence does not beat timestamp-stress HGB.
- C-rate `delta_capacity_Ah` remains negative under the sequence reopening
  comparisons.
- The fixed-length 64-event representation truncates most intervals and should
  be treated as a minimal falsification artifact, not a definitive sequence
  encoder.

The next best path remains benchmark maintenance, synthesis, or a separate
fresh predeclared technical question. Do not open CBAT, transformers, policy
ranking, or broad neural architecture work from this result.
