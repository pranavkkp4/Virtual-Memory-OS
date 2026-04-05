# Pilot Pipeline Check

Date: 2026-04-04

## What I Ran

- Trace-driven pilot via the existing wrapper:
  - `scripts/run_quiet_benchmark.ps1`
  - `--experiment trace --trace-file workloads\traces\sample_trace.csv --repetitions 2 --output-dir results/pilot_20260404/trace_wrapped_pilot`
- Synthetic mixed-workload pilot:
  - `workload_labels=['mixed']`
  - `algorithms=['LRU', 'WSClock']`
  - `allocations=['GlobalAllocation', 'LocalAllocation']`
  - `process_counts=[4]`
  - `memory_scales=[1.0]`
  - `num_trials=2`
  - output: `results/pilot_20260404/synthetic_mixed`

## What Was Produced

- Raw result JSONs for both pilots.
- `raw/shared_results.csv` and `raw/isolation_results.csv` for both pilots.
- `processed/slowdown_metrics.csv` for both pilots.
- `tables/best_policy_by_workload.csv` for both pilots.
- Figures in `figures/` for both pilots.
- Wrapper metadata and run logs for the trace pilot in `results/pilot_20260404/trace_wrapped_pilot/metadata/`.

## Notes

- The wrapper-based trace run is the successful retry that includes `--output-dir results/pilot_20260404/trace_wrapped_pilot`.
- The small pilot matrix did not emit `processed/hypothesis_evaluation.csv` or `tables/hypothesis_evaluation.md`; the H1/H2/H3 summary is only written when the sampled results satisfy the evaluator's conditions.
- No core pipeline code was changed.
