# Final Demo Bundle

This page documents the submission-ready demo bundle built from the benchmark outputs already present in the repository. The bundle is self-contained for grading or live demo use.

## Bundle Location

The packaged demo lives under `results/demo/final_bundle/`.

## Included Artifacts

- `results/demo/final_bundle/raw/sample_trace.csv`
- `results/demo/final_bundle/raw/synthetic_locality_demo.csv`
- `results/demo/final_bundle/raw/shared_results.csv`
- `results/demo/final_bundle/raw/isolation_results.csv`
- `results/demo/final_bundle/processed/slowdown_metrics.csv`
- `results/demo/final_bundle/tables/best_policy_by_workload.csv`
- `results/demo/final_bundle/tables/example_result_table.md`
- `results/demo/final_bundle/figures/fairness_comparison.png`
- `results/demo/final_bundle/figures/page_fault_comparison.png`
- `results/demo/final_bundle/README.md`

## Why These Files

- The trace is a small real input that drives the trace-based benchmark path.
- The synthetic locality example is a documented counterpart that makes the demo bundle easier to understand without replacing the real trace.
- The runtime CSVs show the actual measured shared and isolated execution times.
- The slowdown CSV captures the per-process benchmark outputs used for analysis.
- The table gives a compact example of the best-policy summary extracted from the real results.
- The fairness and page-fault figures are the final presentation plots for the demo.

## Reproduction

1. Install dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Regenerate the benchmark outputs if you want a fresh run.

   ```powershell
   python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
   ```

3. Rebuild the demo bundle from those outputs.

   ```powershell
   python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle
   ```

4. Review the copied figures and tables in `results/demo/final_bundle/`.

## Notes

- The bundle is intentionally compact so it can be opened quickly during grading or a live demo.
- The final package is sourced from repository outputs rather than synthetic placeholders.
- `results/demo/README.md` contains the same high-level build command for convenience.
