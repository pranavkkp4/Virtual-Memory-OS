# Relevant Results

Source files:
- `results/processed/final_aggregate_results.csv`
- `results/processed/hypothesis_evaluation.csv`
- `results/processed/validation_report.json`
- `results/tables/best_policy_by_workload.csv`

## Campaign Scope

| Metric | Value |
| --- | ---: |
| Valid benchmark groups | 1,005 |
| Trial rows | 10,050 |
| Synthetic aggregate configs | 720 |
| Trace aggregate configs | 285 |
| Duplicate configs | 0 |
| Wrapper failures | 0 |
| Missing shared runtime records | 0 |
| Missing isolation runtime records | 0 |
| Remaining validation warnings | 1,189 host-noise outliers |

## Hypothesis Outcomes

| Hypothesis | Condition | Main comparison | Change | Outcome |
| --- | --- | ---: | ---: | --- |
| H1 | High locality, 4 processes, near 1.2x WSS | 326.2 -> 325.1 page faults | -0.34% | Supported |
| H2 | 4 processes near aggregate WSS boundary | 0.01190 -> 0.01886 slowdown variance | +58.53% | Supported |
| H3 | Mixed workload, 4 processes, near WSS | 2.6449 -> 3.2209 worst slowdown | +21.78% | Not supported |

## Synthetic Workload Winners

| Workload | Lowest page faults | Lowest worst slowdown | Highest Jain's index |
| --- | --- | --- | --- |
| high_locality | FIFO + GlobalAllocation (144.0) | NRU + ProportionalAllocation (1.5105) | SecondChance + LocalAllocation (0.99997) |
| mixed | FIFO + GlobalAllocation (202.7) | NRU + LocalAllocation (1.5054) | FIFO + LocalAllocation (0.99988) |
| streaming | FIFO + GlobalAllocation (340.0) | NRU + LocalAllocation (1.4488) | LRU + ProportionalAllocation (0.99991) |
| thrashing | FIFO + GlobalAllocation (204.0) | NRU + ProportionalAllocation (1.5057) | FIFO + LocalAllocation (0.99987) |

## Trace Workload Winners

| Trace | Lowest page faults | Lowest worst slowdown | Highest Jain's index |
| --- | --- | --- | --- |
| report_locality_heavy | FIFO + GlobalAllocation (4.0) | FIFO + ProportionalAllocation (1.0782) | NRU + GlobalAllocation (0.99867) |
| report_mixed_heterogeneous | FIFO + GlobalAllocation (11.0) | FIFO + ProportionalAllocation (0.9630) | SecondChance + GlobalAllocation (0.99846) |
| report_streaming_sequential | FIFO + GlobalAllocation (16.0) | FIFO + ProportionalAllocation (1.0486) | SecondChance + GlobalAllocation (0.99965) |
| report_thrashing_pressure | FIFO + GlobalAllocation (10.0) | FIFO + ProportionalAllocation (1.0739) | WSClock + LocalAllocation (0.99963) |
| sample_trace | FIFO + GlobalAllocation (5.0) | FIFO + ProportionalAllocation (0.9342) | LRU + LocalAllocation (0.99781) |

## Main Takeaway

FIFO with global allocation most often minimized page faults, but fairness-oriented winners were different. NRU with local or proportional allocation often minimized worst-case slowdown, and local/proportional allocation frequently produced the strongest Jain's fairness results. The final result is that page-fault minimization alone is not enough to select a virtual-memory policy under heterogeneous multiprogrammed workloads.
