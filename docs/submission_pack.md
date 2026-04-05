# Submission Pack Manifest

Concise inventory for the submission/demo package. Paths below are the current repo locations unless marked `PENDING`.

## Report Package

- Report source: `progress_report.tex`
- Bibliography source: `progress_report.bib`
- PDF target: `progress_report.pdf` (PENDING, not checked in yet)

## Processed Results

- Final aggregate data: `results/processed/final_aggregate_results.csv`
- Final aggregate data: `results/processed/final_aggregate_results.json`
- Slowdown summary: `results/processed/slowdown_metrics.csv`
- Hypothesis evaluation: `results/processed/hypothesis_evaluation.csv`
- Hypothesis notes: `results/processed/hypothesis_evaluation.md`
- Validation bundle: `results/processed/validation_report.json`
- Validation issues: `results/processed/validation_issues.csv`

## Key Figures

- `results/figures/fairness_comparison.png`
- `results/figures/page_fault_comparison.png`
- `results/figures/summary_figure.png`
- `results/figures/hypothesis_summary.png`
- `results/figures/worst_case_slowdown_vs_policy.png`
- `results/figures/jains_fairness_vs_policy.png`
- `results/figures/page_faults_vs_memory_pressure.png`
- `results/figures/slowdown_variance_vs_memory_pressure.png`
- `results/figures/trace_driven_comparison.png`

## Key Tables

- `results/tables/best_policy_by_workload.csv`
- `results/tables/best_policy_by_workload.md`
- `results/tables/hypothesis_summary.csv`
- `results/tables/hypothesis_summary.md`

## Final Demo Bundle

- Bundle root: `results/demo/final_bundle/`
- Bundle README: `results/demo/final_bundle/README.md`
- Bundle manifest: `results/demo/final_bundle/metadata/bundle_manifest.json`
- Bundle raw inputs: `results/demo/final_bundle/raw/sample_trace.csv`, `results/demo/final_bundle/raw/shared_results.csv`, `results/demo/final_bundle/raw/isolation_results.csv`
- Bundle processed output: `results/demo/final_bundle/processed/slowdown_metrics.csv`
- Bundle tables: `results/demo/final_bundle/tables/best_policy_by_workload.csv`, `results/demo/final_bundle/tables/example_result_table.md`
- Bundle figures: `results/demo/final_bundle/figures/fairness_comparison.png`, `results/demo/final_bundle/figures/page_fault_comparison.png`

## Reproduction Note

1. Install dependencies with `python -m pip install -r requirements.txt`.
2. Rebuild the report inputs if needed with `python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results`.
3. Rebuild the demo package with `python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle`.
4. Build the report PDF from `progress_report.tex` once the LaTeX toolchain is available `PENDING`.
