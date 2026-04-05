# Preliminary Hypothesis Language Pass (Task 4 Ownership)

Date: April 4, 2026

This note records the progress-report-safe language conventions we use when describing H1/H2/H3 in the report. The goal is to keep conclusions aligned with the current evidence in the repository outputs while avoiding overstatement (progress-stage results are not final, and slowdown-based fairness signals are noisy).

## Conventions We Use

- Prefer progress-stage framing: "in this snapshot", "current campaign snapshot", "so far", "at this progress stage".
- Prefer epistemically cautious verbs: "suggests", "indicates", "is consistent with", "appears to".
- When the automated evaluator reports "supported", translate to: "preliminary benchmarking currently suggests support for Hx" (not "Hx is proven" or "Hx is confirmed").
- When the automated evaluator reports "not supported", translate to: "Hx is not currently supported by the progress-stage results" (not "Hx is false").
- Keep the evidence concrete: retain the numeric deltas/threshold checks, but avoid causal language that exceeds what the data directly shows.

## H1/H2/H3 Report Wording Pattern

These are the canonical templates used in `progress_report.tex`:

- H1: "Preliminary benchmarking on the current campaign snapshot currently suggests support for H1 ..."
- H2: "Current campaign results indicate that H2 is likely to hold (in this snapshot) ..."
- H3: "H3 is not currently supported by these progress-stage results ..."

## Common Phrases To Avoid

- "proves", "confirms", "demonstrates conclusively"
- "shows that Hx is true" (without qualifiers)
- "Hx is false" (when the current state is simply lack of support under current conditions)

