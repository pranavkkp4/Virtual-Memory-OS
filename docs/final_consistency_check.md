# Final Consistency Check

Snapshot date: 2026-04-04.

## Summary

- `results/tables/hypothesis_summary.csv` was stale and is now aligned with `results/processed/hypothesis_evaluation.csv`.
- The hypothesis markdown table already matched the processed hypothesis CSV.
- The final demo bundle script uses the final outputs under `results/` and defaults to `results/demo/final_bundle`.
- The README, quickstart guide, and results bundle guide now point at the final demo bundle path instead of the older `results\demo_bundle` location.
- The remaining mismatch is out of scope for this task: `progress_report.tex` still quotes the older H1/H2/H3 numbers that do not match `results/processed/final_aggregate_results.csv`.

## Checks

- Report numbers vs `results/processed/final_aggregate_results.csv`: fail, but unchanged in this task. The report currently carries the older hypothesis values, so it is not yet numerically synchronized with the final aggregate CSV.
- Hypothesis table vs `results/processed/hypothesis_evaluation.csv`: pass after resyncing `results/tables/hypothesis_summary.csv`.
- Figures vs tables: pass by construction. `scripts/build_report_figures.py` and `scripts/build_report_tables.py` both derive their outputs from the same loaded result records and the same hypothesis evaluation helper.
- Demo bundle source: pass. `results/demo/generate_demo_bundle.py` copies the final shared/isolation logs, `results/processed/slowdown_metrics.csv`, `results/tables/best_policy_by_workload.csv`, and the final figures from `results/figures/`.
- README/Quickstart/Results Bundle demo command: pass. The documented output path now points at `results\demo\final_bundle` in all three docs.

## Notes

- I did not change `progress_report.tex` or any out-of-scope files.
- The one narrow fix within scope was to refresh `results/tables/hypothesis_summary.csv` so it matches the processed hypothesis evaluation exactly.
