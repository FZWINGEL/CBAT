# PULSE-Capacity Coupling Diagnostics

Capacity report: `reports/baselines/capacity_hgb50_focused_report.json`
Capacity predictions: `data/processed/capacity_hgb50_focused_predictions.parquet`
Coupling table: `data/interim/capacity_pulse_coupling_table.parquet`

| Scope | Target | Residual | n | Pearson | Spearman |
|---|---|---|---:|---:|---:|
| `all` | `capacity_Ah_k1` | `capacity_residual` | 81072 | 0.527621 | 0.18772 |
| `all` | `capacity_Ah_k1` | `capacity_abs_residual` | 81072 | 0.559997 | 0.236657 |
| `all` | `delta_capacity_Ah` | `capacity_residual` | 81072 | 0.494999 | 0.112291 |
| `all` | `delta_capacity_Ah` | `capacity_abs_residual` | 81072 | 0.604807 | 0.30491 |
| `c_rate` | `capacity_Ah_k1` | `capacity_residual` | 1144 | 0.87957 | 0.654365 |
| `c_rate` | `capacity_Ah_k1` | `capacity_abs_residual` | 1144 | 0.894547 | 0.664034 |
| `c_rate` | `delta_capacity_Ah` | `capacity_residual` | 1144 | 0.775666 | 0.548799 |
| `c_rate` | `delta_capacity_Ah` | `capacity_abs_residual` | 1144 | 0.822463 | 0.639033 |
| `cold_c_rate` | `capacity_Ah_k1` | `capacity_residual` | 352 | 0.867846 | 0.811447 |
| `cold_c_rate` | `capacity_Ah_k1` | `capacity_abs_residual` | 352 | 0.877023 | 0.824406 |
| `cold_c_rate` | `delta_capacity_Ah` | `capacity_residual` | 352 | 0.721839 | 0.658572 |
| `cold_c_rate` | `delta_capacity_Ah` | `capacity_abs_residual` | 352 | 0.769408 | 0.72349 |

This is a scalar diagnostic report. It does not authorize capacity+PULSE multimodal claims.
