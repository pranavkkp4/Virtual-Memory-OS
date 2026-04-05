# Technical Report Draft

## Status

This file is a project draft, not a final results paper. It has been corrected to reflect the current repository state rather than placeholder findings.

## Implemented System

### Replacement algorithms

- FIFO
- LRU
- NRU
- Second Chance
- WSClock

### Allocation policies

- Global allocation
- Local allocation
- Proportional allocation

### Workloads

- High locality
- Streaming
- Random
- Mixed
- Loop
- Thrashing

### Automation and analysis

- Single-process repeated trials
- Multi-process experiment runner
- Working-set estimation for synthetic workloads
- Fairness metrics based on per-process outputs
- Plot generation from saved JSON results

## What the Repository Supports Today

- Comparing replacement algorithms on controlled synthetic traces
- Comparing global and local allocation under shared pressure
- Sweeping frame counts around estimated working-set sizes
- Exporting result summaries and figures

## What Is Still Incomplete

- Runtime slowdown measured against isolated baselines
- Throughput as a first-class reported metric
- Real-trace ingestion and processing pipeline
- Automated methodological controls such as CPU affinity and isolated VM execution
- Final statistical interpretation for the three research questions

## Current Research Alignment

### RQ1

The repository can compare total page faults across algorithm and allocation combinations. It cannot yet make a strong claim about fairness-vs-efficiency using slowdown because slowdown instrumentation is still missing.

### RQ2

The memory-pressure sweep infrastructure exists. The threshold study is partially supported through frame-count sweeps and working-set estimation, but the fairness side is still based on proxy metrics rather than runtime slowdown.

### RQ3

The repo can compare simple and history-based policies on heterogeneous synthetic workloads. The current evidence is suitable for preliminary page-fault and fairness-proxy analysis, not final hypothesis testing.

## Recommended Next Steps

1. Add isolated-baseline runs and compute slowdown explicitly.
2. Add throughput and wall-clock reporting to experiment output.
3. Add real traces and document their preprocessing path.
4. Record environment controls used for each experiment batch.
5. Replace draft prose with measured results after experiments complete.
