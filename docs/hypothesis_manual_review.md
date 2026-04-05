# Manual H1/H2/H3 Review

Scope: this review is based on the currently available processed outputs, mainly `tests/_alloc_smoke/processed/hypothesis_evaluation.csv` and its matching table. It is therefore provisional until the full campaign is rerun and aggregated.

## H1
- Compared `LRU+Local` vs `LRU+Global` for the high-locality, 4-process case near `1.2x` aggregate working-set size.
- The threshold logic looks correct: page faults require a decrease with a `0%` threshold, while worst-case slowdown requires an increase with a `30%` threshold.
- The data matches the label: page faults changed from `329.0` to `328.5` (`-0.15%`), and worst-case slowdown changed from `1.59` to `2.60` (`+63.11%`).
- Interpretation: global allocation barely improved total faults, but it clearly increased tail slowdown, so the expected tradeoff showed up.
- Verdict: `Supported`, and the direction/outcome are consistent with the measured values.

## H2
- Compared local vs global allocation at the aggregate working-set boundary with 4 processes.
- The threshold logic looks correct: slowdown variance is expected to increase, with a `15%` minimum change required.
- The data matches the label: slowdown variance changed from `0.00069` to `0.04174` (`+5925.81%`).
- Interpretation: global allocation appears to have amplified imbalance near the boundary, which is exactly the kind of fairness shift this hypothesis was trying to capture.
- Verdict: `Supported`. The relative jump is enormous, although the baseline variance is very small, so this one should still be treated as campaign-sensitive.

## H3
- Compared `FIFO/NRU+Local` against `LRU/WSClock+Global` for the mixed workload, 4 processes, near aggregate working-set size.
- The threshold logic looks correct: worst-case slowdown is expected to decrease by at least `15%`, with page faults included only as context.
- The data does not match the expectation: worst-case slowdown changed from `2.58` to `3.23` (`+25.45%`), while page faults changed from `1084.5` to `340.5` (`-68.60%`).
- Interpretation: the simple local policies reduced faults, but they hurt the worst process, so the fairness claim did not hold in the current bundle.
- Verdict: `Not supported`. This is the most provisional call because it depends on the full mixed-workload campaign, but the current processed outputs are internally consistent.
