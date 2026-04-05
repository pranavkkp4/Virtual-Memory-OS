# Integration Order Check

Snapshot date: 2026-04-04.

Checked against the completed repository artifacts in `results/`, `docs/`, and `progress_report.tex`.

## Pass/Fail Checklist

- [x] 1. Isolation baselines are complete and usable.
  - `results/baselines_20260404/manifest.json`
  - `results/baselines_20260404/baseline_stability_summary.md`
  - `results/baselines_20260404/baseline_stability_summary.csv`
  - The baseline stability bundle is present and its summary matches the 8-repetition pinned/quiet runs described in the docs.

- [x] 2. Full campaign outputs are complete.
  - `results/raw/campaign_20260404_140330_266/`
  - `results/metadata/campaign_20260404_140330_266/`
  - The campaign log shows all planned batches completed: `synthetic_high_locality`, `synthetic_streaming`, `synthetic_mixed`, `synthetic_thrashing`, and `trace_all_checked_in`.

- [x] 3. Aggregation artifacts are coherent.
  - `results/processed/final_aggregate_results.csv`
  - `results/processed/final_aggregate_results.json`
  - `results/processed/hypothesis_evaluation.csv`
  - `results/processed/hypothesis_evaluation.md`
  - `results/processed/slowdown_metrics.csv`
  - The CSV/Markdown hypothesis pair agrees on the final H1/H2/H3 outcomes.

- [x] 4. Figures and tables are built from final outputs.
  - `results/figures/page_faults_vs_memory_pressure.png`
  - `results/figures/worst_case_slowdown_vs_policy.png`
  - `results/figures/jains_fairness_vs_policy.png`
  - `results/figures/slowdown_variance_vs_memory_pressure.png`
  - `results/figures/trace_driven_comparison.png`
  - `results/figures/hypothesis_summary.png`
  - `results/tables/best_policy_by_workload.csv`
  - `results/tables/best_policy_by_workload.md`
  - `results/tables/hypothesis_summary.csv`
  - `results/tables/hypothesis_summary.md`
  - These artifacts are present and are the report-facing final set.

- [x] 5. Report rewrite is aligned with final artifacts.
  - `progress_report.tex`
  - The report cites final `results/` outputs, including the baseline bundle, processed hypothesis outputs, and report tables/figures.
  - No provisional `_alloc_smoke`-style bundle is used in the report body.

- [x] 6. Demo bundle is complete.
  - `results/demo/final_bundle/README.md`
  - `results/demo/final_bundle/metadata/bundle_manifest.json`
  - `results/demo/final_bundle/raw/shared_results.csv`
  - `results/demo/final_bundle/raw/isolation_results.csv`
  - `results/demo/final_bundle/processed/slowdown_metrics.csv`
  - `results/demo/final_bundle/tables/best_policy_by_workload.csv`
  - `results/demo/final_bundle/figures/fairness_comparison.png`
  - `results/demo/final_bundle/figures/page_fault_comparison.png`

## Issues

- [ ] Downstream docs still contain an older demo bundle path.
  - `README.md`, `docs/QUICKSTART.md`, and `docs/RESULTS_BUNDLE.md` still reference `results\demo_bundle`.
  - The final package path used everywhere else is `results\demo\final_bundle`.
  - This does not break the bundle itself, but it is a stale reference and should be updated so the docs point at the final output rather than the provisional name.

## Verdict

PASS overall, with one documentation-path cleanup item left open for the demo bundle naming.
