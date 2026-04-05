# Final Experiment Matrix

This document freezes the study matrix used by `experiments/run_all_experiments.py`.
It is the source of truth for the final paper-sized sweep.

## Frozen Settings

- Algorithms: `FIFO`, `LRU`, `NRU`, `SecondChance`, `WSClock`
- Allocation policies: `GlobalAllocation`, `LocalAllocation`, `ProportionalAllocation`
- Synthetic workloads: `high_locality`, `streaming`, `mixed`, `thrashing`
- Memory levels: `0.8x`, `1.0x`, `1.2x`, `1.5x` aggregate WSS
- Repetitions: `10`
- Process counts: `2`, `4`, `8`
- Trace-driven family: enabled as a separate run family through the same runner

## Matrix Shape

The frozen synthetic matrix is:

- `5` algorithms
- `3` allocation policies
- `4` synthetic workloads
- `4` memory levels
- `3` process counts
- `10` repetitions

That gives `5 x 3 x 4 x 4 x 3 x 10 = 7,200` synthetic trial combinations before any per-trial runtime sampling.

Trace-driven runs are kept on purpose, but they are not forced into the synthetic process-count grid. They use the checked-in trace files and whatever process counts those traces encode, which keeps the trace study faithful to the source data.

## CLI Contract

Use the final matrix with:

```powershell
python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
```

The `--final` flag always uses the frozen matrix above. The `--trace-file` option may be repeated to add more trace inputs, and trace-driven runs retain the `trace-driven` workload label in exported results and reports.

## Notes

- The synthetic portion intentionally stops at `thrashing` so the final matrix stays aligned with the final study plan.
- The trace-driven family is preserved for rigor and should not be trimmed unless the trace set itself changes.
