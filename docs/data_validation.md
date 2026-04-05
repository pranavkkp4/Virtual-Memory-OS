# Data Validation

This project now treats benchmark validation and aggregation as a first-class
part of the results workflow.

## What gets scanned

By default, the scripts scan:

- `results/raw/`
- `tests/`

That covers both fresh benchmark runs and the checked-in smoke bundles used to
exercise the pipeline.

## Validation checks

`scripts/validate_results.py` checks each benchmark JSON for:

- Missing `trial_results`
- Missing shared/isolation runtime pairs
- Missing `shared_total` records for multi-process runs
- Mismatched access totals or page-fault totals
- Malformed trace runs, including missing `trace_file` or `trace_name`
- Empty fairness payloads on individual trials
- Duplicate result files and duplicate config groups
- Obvious host-noise outliers in trial runtime samples
- Wrapper failures in `results/metadata/**` and `tests/**/metadata/**`

The validator writes a structured report to:

- `results/processed/validation_report.json`
- `results/processed/validation_issues.csv`
- `results/processed/validation_sources.csv`

## Aggregation outputs

`scripts/aggregate_final_results.py` pools all validated trial data and writes:

- `results/processed/final_aggregate_results.csv`
- `results/processed/final_aggregate_results.json`
- `results/processed/trial_level_results.csv`
- `results/processed/hypothesis_evaluation.csv`
- `results/processed/hypothesis_evaluation.md`

The aggregated tables include:

- Means, medians, standard deviations, and 95% confidence intervals
- Page-fault totals and page-fault-rate summaries
- Slowdown summaries for both system-level and per-process metrics
- Fairness metrics, including Jain’s index, variance, CV, and max ratio
- H1/H2/H3 outcomes, or `Not evaluated` if the required configurations are
  not present

## Usage

```powershell
python scripts\validate_results.py
python scripts\aggregate_final_results.py
```

Both scripts accept repeated `--source` arguments if you want to point them at
other result directories.

