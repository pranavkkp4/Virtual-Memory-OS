# Carver Output Audit

Scope: final publication set for Task 7, checked against the required minimal
set of figures and tables.

## Required Set Check

The required semantic outputs are present in `results/`:

- `results/figures/page_faults_vs_memory_pressure.png`
- `results/figures/worst_case_slowdown_vs_policy.png`
- `results/figures/jains_fairness_vs_policy.png`
- `results/figures/slowdown_variance_vs_memory_pressure.png`
- `results/figures/trace_driven_comparison.png`
- `results/tables/best_policy_by_workload.csv`
- `results/tables/best_policy_by_workload.md`
- `results/tables/hypothesis_summary.csv`
- `results/tables/hypothesis_summary.md`

## Extra / Nonessential Outputs

`results/figures` contains additional plot files that are not part of the
required minimal publication set:

- `results/figures/page_fault_comparison.png`
- `results/figures/fairness_comparison.png`
- `results/figures/summary_figure.png`
- `results/figures/hypothesis_summary.png`

These look like legacy, alternate-name, or convenience exports rather than
required publication artifacts. They are safe to treat as nonessential unless
the report build explicitly references them.

## Gaps

No missing required figure/table categories were found. The only audit issue is
that the figure directory is not minimal because it retains the extra files
listed above.

## Bottom Line

The final output set is functionally complete for the required publication
bundle, but it is not exactly minimal because `results/figures` includes four
nonessential extras alongside the five required figures.
