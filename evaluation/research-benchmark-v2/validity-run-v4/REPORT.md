# GEDAM validity benchmark v2

Labeled cases: 26.

| Arm | Answer recall | False abstention | No-answer FP | Correct abstention | Conflict detection recall |
|---|---:|---:|---:|---:|---:|
| no_memory | 0.000 | 1.000 | 0.000 | 1.000 | 0.0 |
| basic | 0.769 | 0.154 | 0.846 | 0.154 | 0.0 |
| similarity | 0.769 | 0.154 | 0.846 | 0.154 | 0.0 |
| gedam | 0.615 | 0.308 | 0.692 | 0.308 | 1.0 |

This safety suite is reported separately from LoCoMo because LoCoMo does not label stale, no-answer, or contradictory memories.
