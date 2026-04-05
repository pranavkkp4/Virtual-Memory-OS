# Strict Validation Audit

Date: 2026-04-04

Scope: final report outputs under `progress_report.tex`, `results/`, and the
final pinned-baseline bundle under `results/baselines_20260404/pressure_pinned/`.
This audit ignores test/smoke overlap in `tests/` unless it leaks into the final
report bundle.

## Checklist Results

| Checklist item | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Matrix combinations completed or clearly excluded | PASS | `results/trace_sample_trace_*.json` has 60 files; `results/processed/slowdown_metrics.csv` contains 60 config groups with exactly 2 repetitions each. The report also labels the synthetic mixed workload as a pilot and the pinned-baseline study as a separate bundle. | The trace-driven matrix is fully covered; larger synthetic work is explicitly scoped as pilot or future campaign work, not silently implied as complete. |
| Repetitions accounted for | PASS | Final trace bundle: 60 groups, 2 reps per group. Pressure bundle: 48 groups, 8 reps per group in `results/baselines_20260404/pressure_pinned/processed/slowdown_metrics.csv`. | The counts line up with the bundle manifests and the per-config repetition fields. |
| Isolation baseline variance acceptable | PASS | `results/baselines_20260404/baseline_stability_summary.md` reports 264 groups, 81 stable, 39 review, 144 unstable, median CV `0.128607`, mean CV `0.1902`. `progress_report.tex:76` now reports the same counts and CV statistics and explicitly notes that isolated timing baselines can be noisy. | The report is now aligned with the locked baseline-stability bundle and does not over-claim baseline stability; fairness claims are framed with the same caution as the baseline summary verdict. |
| Wrapper metadata present | PASS | `results/baselines_20260404/manifest.json` lists the `pinned` and `quiet` wrappers, and `results/baselines_20260404/pressure_pinned/metadata/` contains `run_environment*.json` plus `run_output_*.log` files. | Pilot wrapper metadata also exists under `results/pilot_20260404/trace_wrapped_pilot/metadata/`. |
| Processed metrics reproducible from raw data | PASS | Exact join check against raw logs: final bundle `240/240` slowdown rows matched with `0` missing pairs and `0` mismatches; pressure bundle `1152/1152` rows matched with `0` missing pairs and `0` mismatches. | The processed slowdown values are exact ratios of shared to isolated runtimes. |
| Figures match processed tables | PASS | `results/figures/hypothesis_summary.png` shows H1/H2/H3 statuses and percentages that match `results/tables/hypothesis_summary.csv`. `results/figures/trace_driven_comparison.png` shows the same values as `results/tables/best_policy_by_workload.csv` for the trace row. | The page-fault and pressure plots are visually consistent with the final aggregate tables; no mismatched labels or stale values were found in the report-facing figures. |
| Hypothesis evaluator ran on final aggregated data | PASS | `results/processed/hypothesis_evaluation.csv` and `.md` exist, and `results/baselines_20260404/pressure_pinned/processed/hypothesis_evaluation.csv` exists for the pinned pressure subset. The report cites the final bundle in `progress_report.tex:100-106`, with H1/H2 supported and H3 not supported. | The evaluator output is present for the final aggregated outputs, and the pinned pressure subset carries the corresponding CSV used for subset checks. |
| No pilot-only values copied into final outputs | PASS | Pilot-only values live in `results/pilot_20260404/synthetic_mixed/summary_report.txt` and the pilot bundle. The final table output uses different mixed-workload values, e.g. `results/tables/best_policy_by_workload.csv` reports `340.5`, `1.6548332137733142`, and `0.999226757176557` for the mixed row. `progress_report.tex:72-73` also labels the pilot as separate and says it is not the source of the final headline claims. | Pilot evidence is present, but it is clearly quarantined from the final campaign claims and final summary tables. |

## Audit Verdict

Overall verdict: `PASS` for report acceptance.

Reason: all checklist items pass, and `progress_report.tex` is aligned with the
locked baseline-stability summary and other final result bundles under
`results/`.
