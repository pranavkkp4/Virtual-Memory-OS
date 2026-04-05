# Figure and Table Manifest

This manifest documents the compact, report-ready outputs built for Task 7.
The builders prefer the richest available aggregated artifacts under `results/`
and fall back to the processed CSV exports when needed.

## Build Inputs

- `results/**/multiproc_*.json` and `results/**/trace_*.json` summaries when present.
- `results/processed/slowdown_metrics.csv` and any mirrored `slowdown_metrics.csv`
  files under the pilot bundles.

## Figure Outputs

- `results/figures/page_faults_vs_memory_pressure.png`
- `results/figures/worst_case_slowdown_vs_policy.png`
- `results/figures/jains_fairness_vs_policy.png`
- `results/figures/slowdown_variance_vs_memory_pressure.png`
- `results/figures/trace_driven_comparison.png`
- `results/figures/hypothesis_summary.png`

## Table Outputs

- `results/tables/best_policy_by_workload.csv`
- `results/tables/best_policy_by_workload.md`
- `results/tables/hypothesis_summary.csv`
- `results/tables/hypothesis_summary.md`

## Assumptions

- Memory pressure is represented by the ordered pressure points within each
  workload family. When `memory_ratio_to_wss` is available in a JSON summary,
  the builders use it directly; otherwise they fall back to the frame-count
  ordering in the aggregated CSV data.
- Hypothesis evaluation uses the same H1-H3 logic already defined in
  `src/hypothesis_evaluator.py`, with representative 4-process slices for H1
  and H2 and the mixed-workload 4-process slice for H3.
- The trace-driven comparison figure compares the best policy for each metric
  within each workload, so the trace workload appears alongside the synthetic
  workloads in the same compact view.
- The final bundle is intentionally compact rather than exhaustive. It is meant
  to surface the headline results for the report, not to replace the full raw
  experiment archive.
