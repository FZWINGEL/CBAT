# Milestone 9 - Neural Sequence Architecture Gate Before CBAT

Date: 2026-05-28

## Purpose

This gate reopens the charter H7 sequence question only as a pre-CBAT
architecture test. It does not implement CBAT. The question is whether a
stronger fixed-length event tensor plus CNN/TCN/CNN-LSTM baselines can recover
temporal-history value that the Milestone 7.1 minimal 64-event sequence gate did
not find.

The gate remains claim-bounded: true histories must beat shuffled-order
controls, aggregate-event HGB, and timestamp-stress HGB under grouped
validation before any later CBAT prototype can be opened.

## Implemented Artifacts

New commands:

```bash
mbp features build-event-sequence-tensors
mbp features event-sequence-tensor-qa
mbp baseline run-neural-sequence
mbp baseline diagnose-neural-sequence
```

New source modules and schemas:

- `INTERVAL_EVENT_SEQUENCE_TENSOR_V2_SCHEMA`
- `mbp.data.products.event_sequences.build_interval_event_sequence_tensor_table`
- `mbp.baselines.neural_sequence`

Tracked reports:

- `reports/audit/event_sequence_tensor_v2_qa_report.json`
- `reports/baselines/neural_sequence_gate_report.json`
- `reports/baselines/neural_sequence_gate/leaderboard.csv`
- `reports/baselines/neural_sequence_gate/neural_sequence_diagnostics.md`
- `reports/baselines/neural_sequence_gate/neural_sequence_claim_readiness.md`
- `reports/baselines/neural_sequence_gate/neural_sequence_leakage_audit.md`
- `reports/baselines/neural_sequence_gate/plots/*.csv`
- `reports/baselines/neural_sequence_gate/figures/*.svg`

Ignored generated data:

- `data/interim/interval_event_sequence_tensor_v2.parquet`
- `data/processed/neural_sequence_gate_predictions.parquet`

The earlier ridge-only smoke reports generated before CUDA became visible in
WSL are superseded by the full CUDA gate report and are not part of the
claim-bearing evidence set.

## Tensor QA Result

Command:

```bash
mbp features build-event-sequence-tensors \
  --run-events data/interim/run_event_table_v1.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out data/interim/interval_event_sequence_tensor_v2.parquet \
  --max-events 256 \
  --sampling-policy time_stratified \
  --seed 42

mbp features event-sequence-tensor-qa \
  --sequence-tensors data/interim/interval_event_sequence_tensor_v2.parquet \
  --interval-table data/interim/interval_table.parquet \
  --out reports/audit/event_sequence_tensor_v2_qa_report.json
```

QA summary:

| Item | Result |
|---|---:|
| Rows | 3,827 |
| Missing intervals | 0 |
| Extra intervals | 0 |
| Truncated/sampled intervals | 3,103 |
| Median source events per interval | 627 |
| Max source events per interval | 247,393 |
| Mean selected events | 248.123 |
| Estimated tensor memory | 389.6 MiB |
| Leakage check | passed |

Compared with the v1 64-event product, the v2 product keeps a larger
time-stratified sample and richer per-event features. It is still a fixed-length
diagnostic tensor, not a proof that full raw event histories are unnecessary.

## CUDA Run

The full neural run used the escalated WSL execution path because the Codex
sandbox itself blocks NVML/GPU access. CUDA was visible outside the sandbox:

```text
PyTorch: 2.12.0+cu130
torch.cuda.is_available(): True
GPU: NVIDIA GeForce RTX 5060 Ti
```

The runner intentionally fails rather than silently using CPU if CUDA is not
available.

Full command:

```bash
mbp baseline run-neural-sequence \
  --interval-table data/interim/interval_table.parquet \
  --interval-subsets data/splits/interval_subset_registry_v1.parquet \
  --sequence-tensors data/interim/interval_event_sequence_tensor_v2.parquet \
  --out reports/baselines/neural_sequence_gate_report.json \
  --predictions-out data/processed/neural_sequence_gate_predictions.parquet \
  --out-dir reports/baselines/neural_sequence_gate \
  --reference-sequence-report reports/baselines/capacity_sequence_value_hgb50_report.json \
  --reference-stress-report reports/baselines/capacity_stress_features_v1_1_hgb50_report.json \
  --model-levels NS1_ridge_flat_true_sequence,NS2_ridge_flat_shuffled_sequence,NS3_cnn1d_true_sequence,NS4_tcn_true_sequence,NS5_cnn_lstm_true_sequence,NS6_cnn_lstm_shuffled_sequence \
  --targets capacity_Ah_k1,delta_capacity_Ah \
  --split-views condition_fold,temperature_holdout_fold,c_rate_holdout_fold,profile_holdout_fold,voltage_window_holdout_fold \
  --max-epochs 150 \
  --patience 20 \
  --batch-size 64 \
  --device cuda
```

The full gate produced:

| Item | Result |
|---|---:|
| Metric rows | 144 |
| Prediction rows | 124,380 |
| Training-history rows | 5,134 |
| Selected cells | 228 |
| Selected parameter sets | 76 |

## Results

| Comparison | Status | Evidence |
|---|---|---|
| True sequence vs shuffled | not supported | mean gain `0.0161874`, p05 `-0.0116749`, positive rows `22/48` |
| True sequence vs aggregate-event HGB | not supported | mean gain `-0.405717`, p05 `-0.711488`, positive rows `0/96` |
| True sequence vs timestamp-stress HGB | not supported | mean gain `-0.419318`, p05 `-0.758173`, positive rows `6/88` |
| C-rate `delta_capacity_Ah` | not supported | positive rows `0/10`, mean gain `-0.435394`, p05 `-0.578266` |

The strongest architecture signal is only that some true-order rows beat their
own shuffled controls. That is insufficient because the charter H7 gate requires
true histories to beat shuffled controls and strong aggregate/stress baselines.
The CNN/TCN/CNN-LSTM candidates do not beat those stronger references.

## Figures

The full CUDA run generated actual SVG result figures:

- `reports/baselines/neural_sequence_gate/figures/neural_sequence_gain_matrix.svg`
- `reports/baselines/neural_sequence_gate/figures/true_vs_shuffled_by_split.svg`
- `reports/baselines/neural_sequence_gate/figures/c_rate_delta_leaderboard.svg`
- `reports/baselines/neural_sequence_gate/figures/condition_error_hotspots.svg`
- `reports/baselines/neural_sequence_gate/figures/training_curves.svg`
- `reports/baselines/neural_sequence_gate/figures/sequence_sampling_coverage.svg`
- `reports/baselines/neural_sequence_gate/figures/claim_readiness_summary.svg`

Figure QA confirms all seven SVGs exist, are nonempty, and have source CSVs.

## Decision

Milestone 9 is complete and negative for neural sequence architecture readiness.
The v2 sequence tensor product is valid for diagnostics, and CUDA neural rows
ran, but the architecture gate fails the required controls.

Current claim posture:

- v2 event tensor coverage and leakage QA: supported for diagnostics.
- CNN/TCN/CNN-LSTM sequence value: not supported.
- Neural sequence next-gate readiness: blocked.
- CBAT prototype readiness: blocked.
- Policy ranking, calibrated risk, causal claims, and broad multimodal claims:
  blocked.

The result does not mean neural models can never help this dataset. It means
this predeclared, stronger fixed-length event-sequence architecture gate does
not justify opening CBAT from the current evidence.
