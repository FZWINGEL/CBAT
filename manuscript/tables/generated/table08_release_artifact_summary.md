# Table 8. Release-candidate artifact summary

| Artifact group | Status | Notes |
|---|---|---|
| `benchmark-v0.1-rc1` | validation checkpoint | Tagged at `ff4c8c2`; preserves the pure release-check validation state. |
| `benchmark-v0.1-rc2` | reviewer-facing release candidate | Tagged at `e499b12`; includes release-polish handoff documents. |
| executable release checker | passed | `mbp report check-release-candidate` validates release files, artifacts, claims, and command coverage. |
| tracked reports | included | Audit, baseline, analysis, synthesis, and manuscript artifacts are tracked. |
| generated data products | excluded | Raw data, interim Parquets, split Parquets, and prediction Parquets remain local ignored artifacts. |
| blocked branches | preserved | CBAT, neural/sequence models, DRT/embeddings, policy ranking, detector-knee prediction, risk calibration, and causal claims remain blocked. |

