# Hypothesis Provisional Guard

This note prevents smoke or pilot hypothesis outputs from being promoted to final report claims.

## Authoritative sources

When final H1/H2/H3 conclusions are needed, use the locked full-campaign outputs:

- `results/tables/hypothesis_summary.md`
- `results/raw/campaign_20260404_140330_266/`

Those files contain the campaign-level hypothesis decisions that should drive the headline findings in `progress_report.tex`.

## Provisional sources

The following outputs are useful for debugging, sanity checks, or pipeline validation, but they must not override the final campaign when both are available:

- `tests/_alloc_smoke/`
- `results/pilot_20260404/`
- `results/baselines_20260404/pressure_pinned/`
- `results/processed/hypothesis_evaluation.*` when it reflects a smoke or pilot bundle rather than the final aggregate

## Rule of use

1. If the final campaign outputs exist, cite them first and treat them as the source of truth for H1/H2/H3.
2. Use smoke or pilot results only as context, implementation checks, or provisional diagnostics.
3. If a document mentions a provisional hypothesis outcome, it must label that outcome as provisional and should not present it as the headline finding.

## Current locked outcomes

At the time of this note, the locked final campaign records these outcomes:

- H1: `Supported`
- H2: `Supported`
- H3: `Not supported`

The report should reflect that set of decisions, and any earlier smoke/pilot table should be treated as superseded for headline claims.
