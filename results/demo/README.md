# Demo Bundle

This directory contains the checked-in packaging script for the final demo bundle.

## What it does

- Copies a small real trace into the demo bundle.
- Copies a clearly labeled synthetic locality counterpart alongside the real trace.
- Copies the real runtime logs, slowdown metrics, and summary table already produced by the benchmark runs.
- Copies the two final figures used in the demo: fairness and page faults.
- Writes a bundle README and a small manifest so the package is easy to inspect.

## Build the bundle

```powershell
python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle
```

## Rebuild the source outputs first, if needed

```powershell
python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
```

## Bundle contents

- `results\demo\final_bundle\README.md`
- `results\demo\final_bundle\raw\sample_trace.csv`
- `results\demo\final_bundle\raw\synthetic_locality_demo.csv`
- `results\demo\final_bundle\raw\shared_results.csv`
- `results\demo\final_bundle\raw\isolation_results.csv`
- `results\demo\final_bundle\processed\slowdown_metrics.csv`
- `results\demo\final_bundle\tables\best_policy_by_workload.csv`
- `results\demo\final_bundle\tables\example_result_table.md`
- `results\demo\final_bundle\figures\fairness_comparison.png`
- `results\demo\final_bundle\figures\page_fault_comparison.png`
