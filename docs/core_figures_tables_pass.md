# Core Figures and Tables (Submission Set Pass)

Goal: keep the submission centered on a compact core evidence set (3-4 figures, 3-4 tables). Everything else in `results/` is supporting material.

This pass is implemented in `progress_report.tex` via the "Core Tables and Figures (Submission Set)" section.

## Preferred Core Figures (3-4)

- **F1: Page faults vs memory pressure**: `results/figures/page_faults_vs_memory_pressure.png`
  Use: efficiency signal and pressure threshold behavior.
- **F2: Worst-case slowdown vs policy**: `results/figures/worst_case_slowdown_vs_policy.png`
  Use: worst-process fairness cost of policy choices.
- **F3: Jain fairness vs policy**: `results/figures/jains_fairness_vs_policy.png`
  Use: compact fairness summary across policies.
- **F4: Trace-driven comparison**: `results/figures/trace_driven_comparison.png`
  Use: trace-based cross-check against synthetic workload conclusions.

Optional supporting (only if space permits):
- **S1: Slowdown variance vs memory pressure**: `results/figures/slowdown_variance_vs_memory_pressure.png`
  Use: dispersion signal for H2 near the WSS boundary.

## Preferred Core Tables (3-4)

- **T1: Experimental matrix**: `docs/final_experiment_matrix.md`
  Use: factor levels, repetition counts, and what was actually swept.
- **T2: Headline results by workload/policy (best-by-metric picks)**: `results/tables/best_policy_by_workload.md`
  Use: the "what won where" table for quick reading.
- **T3: H1/H2/H3 summary**: `results/tables/hypothesis_summary.md` (source: `results/processed/hypothesis_evaluation.csv`)
  Use: the hypothesis outcomes with the exact deltas used in the report.
- **T4: Compact statistical/fairness summary (submission-condensed)**: derived from `results/processed/final_aggregate_results.csv`
  Use: one-page table focusing on the near-WSS pressure point with mean/std/CI for faults and slowdown plus Jain/variance/CV.

