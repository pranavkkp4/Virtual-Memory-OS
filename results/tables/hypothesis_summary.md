| hypothesis | test_condition | outcome | main_metric | main_baseline_value | main_comparison_value | main_percent_change | main_threshold_percent | rules_summary | rule_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | High locality, 4 processes, near 1.2x WSS | Supported | page_faults | 326.2 | 325.1 | -0.3372 | 0 | page_faults:-0.34%; worst_slowdown:124.05% | 2 |
| H2 | Near the aggregate WSS boundary, 4 processes | Supported | slowdown_variance | 0.0119 | 0.0189 | 58.529 | 15 | slowdown_variance:58.53% | 1 |
| H3 | Mixed workload, 4 processes, near aggregate WSS | Not supported | worst_slowdown | 2.645 | 3.221 | 21.78 | 15 | worst_slowdown:21.78%; page_faults:-69.03% | 2 |
