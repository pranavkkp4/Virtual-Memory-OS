# Report Past-Tense Pass

Snapshot date: 2026-04-04.

Scope: This pass only edited `progress_report.tex` (per Task 11 ownership). No other files were modified.

## What Changed

- Rewrote remaining plan/intent phrasing into completed-study language where the report already points at locked artifacts and executed runs (examples: "we want to" -> "we studied", "we continue to" -> "we organized", "we expect" -> "we expected", "will" -> "would").
- Shifted the RQ/Hypotheses framing to past-tense hypothesis statements (with evaluation still reported in the existing Hypothesis Evaluation section).
- Recast methods wording (experimental design, performance measures, and controls) to reflect what was used in the executed campaigns rather than what was planned.
- Renamed forward-looking sections to match a completed-study narrative (`Current Progress` -> `Completed Work`, `Remaining Work` -> `Limitations and Future Work`).

## Intentionally Qualified Or Present-Tense

Some language remains qualified (or in present tense) on purpose to stay honest and avoid implying evidence that is not locked by the checked-in artifacts:

- Slowdown-based fairness measurements are still described as noise-sensitive. The report continues to caution interpretation because the baseline stability artifacts show non-trivial runtime noise even under pinned-core execution.
- The "Limitations and Future Work" section stays explicitly forward-looking (using "would strengthen", "future work includes", etc.), because those items are extensions rather than executed evidence.
- A few repository facts are written in present tense (for example, what the repository contains and where artifacts live), because those statements describe the state of the checked-in code and `results/` tree rather than an experiment outcome.

## Quick Self-Check

After the edits, `progress_report.tex` contains no instances of the following plan-forward markers:

- "we will", "we want to", "we continue to", "next steps", "is leading", "currently depends", "already support".
