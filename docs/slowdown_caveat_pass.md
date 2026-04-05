# Slowdown Caveat Pass (Task 13)

Date: April 4, 2026 (America/Denver)

## Ground Truth

- Slowdown was implemented as isolation/shared wall-clock timing (`t_shared / t_isolated`) and used in the executed runs.
- The isolation baseline stability campaign shows timing baselines have some noise, so exact slowdown point estimates should not be over-interpreted.
- Page-fault trends and pattern-level fairness behavior (e.g., dispersion changes across memory pressure) are more robust than single-run slowdown point estimates.

## What Changed

To make the slowdown caveat explicit and consistent, `progress_report.tex` was updated to include the same one-sentence caveat in the requested places:

- Methodology/measurement: appended to `Slowdown Measurement Method (Exact)`.
- Results discussion: added to the `Executed Results` section opener (Section `sec:results`).
- Conclusion/future-work framing: added in both `Limitations and Future Work` and `Conclusion` so the framing is consistent where the report summarizes and qualifies claims.

Only `progress_report.tex` and this file were modified as part of this pass.

