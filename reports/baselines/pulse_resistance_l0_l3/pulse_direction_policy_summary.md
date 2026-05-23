# PULSE Direction Policy Summary

Direction-specific target extraction is diagnostic for Milestone 0.7.2.

| Direction | Status | C-rate condition mean MAE | Interpretation |
|---|---|---:|---|
| `mean` | `passed` | 0.0018584237602246756 | canonical target |
| `charge` | `passed` | 0.0018584237602246756 | same as mean for current RT/50 extraction |
| `discharge` | `missing` | NA | No comparison row. |

Decision: keep `mean` as canonical direction handling. In the current RT/50 context, `mean` and `charge` are equivalent in the generated target table, while discharge has no finite adjacent RT/50 interval deltas. Direction-specific claims remain blocked.
