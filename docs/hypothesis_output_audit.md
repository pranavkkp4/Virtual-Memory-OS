# Hypothesis Output Audit

Snapshot date: 2026-04-04.

## Gate Check

The final hypothesis-evaluation artifacts are present and coherent:

- `results/processed/hypothesis_evaluation.csv`
- `results/tables/hypothesis_summary.md`
- `results/processed/hypothesis_evaluation.md`

The CSV is the source of truth, and the two markdown tables match it on the
final H1/H2/H3 decisions and the underlying summary metrics.

## Manual Review Comparison

The manual review in `docs/hypothesis_manual_review.md` agrees with the final
evaluator output:

- H1: `Supported`
- H2: `Supported`
- H3: `Not supported`

There is no verdict mismatch between the manual review and the final evaluator
artifact. The only difference is provenance: the manual review was explicitly
marked provisional and referenced the smaller `_alloc_smoke` bundle, while the
final artifacts are written from `results/processed/`.

## Coherence Notes

- H1 shows a small page-fault reduction with a large worst-case slowdown
  increase, which supports the tradeoff described in the review.
- H2 shows a large rise in slowdown variance, matching the supported verdict.
- H3 shows higher worst-case slowdown in the comparison condition, so the
  fairness hypothesis remains not supported.

## Conclusion

The gate passes. No fix to the numeric evaluation was needed; the remaining
work was to document the final artifact state clearly and keep the summary table
aligned with the processed CSV.
