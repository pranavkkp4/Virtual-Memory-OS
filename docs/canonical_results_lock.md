# Canonical Results Lock

This document freezes the canonical final results for the Virtual Memory project. The files listed below are the source of truth for the final campaign and should be treated as locked artifacts, not as routine regeneration targets.

## Canonical Artifacts

- `results/raw/campaign_20260404_140330_266`
- `results/processed/final_aggregate_results.csv`
- `results/processed/hypothesis_evaluation.csv`
- `results/processed/validation_report.json`

## Lock Policy

- These artifacts are canonical because they represent the final validated outputs used for reporting and downstream documentation.
- Do not regenerate, rewrite, or replace them during normal cleanup, refactoring, or experiment reruns.
- If other work in the repository updates adjacent code or documentation, preserve these files unchanged unless the change is explicitly about a defect in the locked results.

## Why They Are Frozen

- The final campaign has already been validated and summarized for submission-facing use.
- Regenerating the outputs risks introducing drift between the documented results, the processed summaries, and the raw campaign evidence.
- Freezing the canonical set keeps the report, tables, and validation narrative aligned with one stable reference point.

## Exceptions

- Regeneration is allowed only if a real defect is found in the canonical outputs, such as a verified data processing bug, a validation error, or a reproducible mismatch between the raw campaign and the processed summaries.
- If regeneration is required, document the defect first, replace the canonical artifacts together as a single coordinated update, and update this lock file to describe the new frozen source of truth.
- Cosmetic changes, formatting changes, or convenience reruns are not sufficient reasons to refresh the canonical artifacts.

## Operational Note

Any scripts or workflows that produce these results should point to this lock document as the authoritative reference for what counts as final.
