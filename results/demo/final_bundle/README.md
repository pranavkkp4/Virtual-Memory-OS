# Final Demo Bundle

This bundle is a compact snapshot built from the real benchmark outputs already checked into the repository, plus one clearly labeled synthetic locality counterpart for context.

## Contents

- `raw/sample_trace.csv`: a small real trace used by the trace-driven benchmark path.
- `raw/synthetic_locality_demo.csv`: a clearly labeled synthetic counterpart for a tiny locality-focused example.
- `raw/shared_results.csv` and `raw/isolation_results.csv`: the measured wall-clock runtime logs.
- `processed/slowdown_metrics.csv`: per-process slowdown and page-fault metrics.
- `tables/best_policy_by_workload.csv`: the example result table shown in the demo.
- `tables/example_result_table.md`: a readable markdown rendering of the same table.
- `figures/fairness_comparison.png`: the fairness figure for the final demo.
- `figures/page_fault_comparison.png`: the page-fault comparison figure for the final demo.

## Reproduce

1. Install dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Regenerate the real benchmark outputs if needed.

   ```powershell
   python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
   ```

3. Rebuild this bundle from those outputs.

   ```powershell
   python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle
   ```

4. Open the copied figures and tables in `results\demo\final_bundle`.

The bundle is intentionally small so it can be inspected quickly during grading or a live demo.
