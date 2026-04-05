# Integration Checkpoints

Current repo state: 2026-04-04.

## Checkpoint A: Results Locked

**Gate status:** satisfied

The results side looks frozen enough for integration use because the final campaign outputs, aggregated analysis, and publication figures/tables are already checked in.

Evidence:

- `docs/full_campaign_log.md` records that all planned batches for `campaign_20260404_140330_266` completed, including `synthetic_high_locality`, `synthetic_streaming`, `synthetic_mixed`, `synthetic_thrashing`, and `trace_all_checked_in`.
- `results/processed/final_aggregate_results.csv` and `results/processed/final_aggregate_results.json` exist, so the campaign has a consolidated analysis layer rather than only raw runs.
- `results/processed/hypothesis_evaluation.csv` and `results/processed/hypothesis_evaluation.md` exist for the automated hypothesis checks.
- `results/tables/best_policy_by_workload.csv` and `results/tables/hypothesis_summary.csv` exist as report-ready tables.
- `results/figures/summary_figure.png`, `results/figures/page_fault_comparison.png`, `results/figures/fairness_comparison.png`, and the other figure assets are present for the final writeup.

Assessment:

- The repo contains a stable, artifact-backed results bundle.
- The remaining files under `results/` are supporting outputs, not indicators that the core results package is still being reshaped.

## Checkpoint B: Publication Locked

**Gate status:** not satisfied

The publication package is not locked yet because the manuscript is still explicitly framed as a progress report, and there is no final frozen publication artifact in the tree.

Evidence:

- `progress_report.tex` is still the active manuscript source, and its abstract says the results are "reported as progress-stage findings rather than final empirical claims."
- `README.md` links to `progress_report.tex`, not to a final paper, submission PDF, or locked publication bundle.
- The repository does not currently show a finalized publication artifact such as a compiled PDF, a renamed final manuscript, or a dedicated submission directory.

Assessment:

- The writeup is in a good state for continued editing, but it is not yet frozen as a publication deliverable.
- Publication should be considered unlocked until the final manuscript artifact is added and the paper source is no longer treated as a progress-stage report.
