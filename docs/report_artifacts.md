# Report Artifacts and Reproducibility (Task 9)

This note records the concrete outputs that back the claims in
`progress_report.tex`, and how to regenerate them.

Snapshot date: 2026-04-04 (America/Denver).

## What Was Actually Executed

The repository already contains generated result bundles under `results/` that
were produced by the experiment runners and wrapper scripts. The LaTeX report
only claims results that can be traced to files listed below.

## Primary Bundle: `results/`

Trace-driven matrix (sample trace, 60 configurations):

- `results/trace_sample_trace_*.json`
  - 5 algorithms x 3 allocation policies x 4 frame counts (`f4,f5,f6,f8`)
  - These JSON files currently include system-level aggregates but may omit some
    metadata fields inside the JSON (labels can be recovered from the filename
    and from the raw CSV logs).
- `results/summary_report.txt`
  - Aggregated text report across all discovered `results/*.json`.
- `results/raw/shared_results.csv`
  - Wall-clock timings for shared (multiprogrammed) runs, including per-process
    and per-run totals.
- `results/raw/isolation_results.csv`
  - Wall-clock timings for isolated per-process baseline runs.
- `results/processed/slowdown_metrics.csv`
  - Per-process slowdown computed as `t_shared_ms / t_isolated_ms`, with page
    fault counters where available.
- `results/tables/best_policy_by_workload.csv`
  - “Best policy” pick per workload for (a) lowest faults, (b) lowest worst
    slowdown, (c) highest Jain's index.
- `results/figures/summary_figure.png`
- `results/figures/page_fault_comparison.png`
- `results/figures/fairness_comparison.png`
- `results/metadata/run_environment*.json`, `results/metadata/run_output_*.log`
  - Environment snapshots and runner logs captured during generation.

## Pilot Bundle: `results/pilot_20260404/synthetic_mixed/`

This directory contains a small synthetic workload pilot that produces more
variable page-fault and slowdown behavior than the tiny sample trace.

- `results/pilot_20260404/synthetic_mixed/summary_report.txt`
- `results/pilot_20260404/synthetic_mixed/processed/slowdown_metrics.csv`
- `results/pilot_20260404/synthetic_mixed/figures/*.png`
- `results/pilot_20260404/synthetic_mixed/tables/best_policy_by_workload.csv`

## Pinned Baselines + Hypothesis Checks: `results/baselines_20260404/`

This bundle captures (a) wrapper configuration, (b) isolation stability
statistics, and (c) a pinned high-locality pressure run used for automated
hypothesis checks.

- `results/baselines_20260404/manifest.json`
  - Declares wrapper profiles, repetitions (`8`), and stability thresholds.
- `results/baselines_20260404/baseline_stability_summary.md`
- `results/baselines_20260404/baseline_stability_summary.csv`
  - Isolation baseline CV statistics grouped by configuration.
- `results/baselines_20260404/pressure_pinned/summary_report.txt`
- `results/baselines_20260404/pressure_pinned/processed/slowdown_metrics.csv`
- `results/baselines_20260404/pressure_pinned/processed/hypothesis_evaluation.csv`
- `results/baselines_20260404/pressure_pinned/tables/hypothesis_evaluation.md`
- `results/baselines_20260404/pressure_pinned/tables/best_policy_by_workload.csv`
- `results/baselines_20260404/pressure_pinned/metadata/run_environment*.json`
  and `run_output_*.log`

## Reproducing The Artifacts

From the repository root:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Re-run the trace-driven matrix and regenerate analysis outputs:

```powershell
python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
python main.py analyze --input results
python main.py visualize --input results --output results\figures
```

Run wrapper scripts (metadata capture, optional core pinning):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_pinned.ps1 -Cores 2 -BenchmarkArgs '--experiment','pressure','--repetitions','8'
powershell -ExecutionPolicy Bypass -File scripts\run_quiet_benchmark.ps1 -BenchmarkArgs '--experiment','trace','--trace-file','workloads\traces\sample_trace.csv','--repetitions','8'
```

## Known Limitations (Honest Notes)

- The checked-in `sample_trace.csv` is intentionally small and should be treated
  as a pipeline validation, not as a definitive performance ranking between
  algorithms.
- Runtime-based slowdown can be noisy at millisecond-scale durations. The
  baseline stability report quantifies that noise (CV distribution) even under
  pinned-core execution.
- Some JSON result artifacts may omit metadata fields (algorithm/allocation/frames)
  inside the JSON payload; current labeling can be reconstructed from filenames
  and from `results/raw/*.csv`.

