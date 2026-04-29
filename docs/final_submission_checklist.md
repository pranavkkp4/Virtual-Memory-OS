# Final Submission Checklist

Use this file as the last gate before submitting the Virtual Memory final
report. The canonical campaign is locked; rebuild only report-facing tables,
figures, and the demo bundle unless a verified data defect requires a coordinated
refresh.

## Report Source

- Report source: `progress_report.tex`
- Bibliography source: `progress_report.bib`
- PDF target: `progress_report.pdf`
- Format target: IEEE conference, 10 pages or less

## Canonical Results

- Raw campaign: `results/raw/campaign_20260404_140330_266`
- Final aggregate CSV: `results/processed/final_aggregate_results.csv`
- Final hypothesis CSV: `results/processed/hypothesis_evaluation.csv`
- Validation report: `results/processed/validation_report.json`
- Demo bundle: `results/demo/final_bundle`

## Figures Used In The Report

- `results/figures/page_faults_vs_memory_pressure.png`
- `results/figures/trace_driven_comparison.png`
- `results/figures/worst_case_slowdown_vs_policy.png`
- `results/figures/jains_fairness_vs_policy.png`

## Tables Used In The Report

- Matrix scope table in `progress_report.tex`
- `results/tables/best_policy_by_workload.csv`
- `results/tables/best_policy_by_workload.md`
- `results/tables/hypothesis_summary.csv`
- `results/tables/hypothesis_summary.md`

## Rerun Commands

```powershell
python -m unittest discover -s tests -v
python main.py --help
python experiments/run_all_experiments.py --help
python experiments/run_all_experiments.py --experiment allocation --repetitions 2 --output-dir tests/_alloc_smoke
python results/demo/generate_demo_bundle.py --output-dir tests/_demo_bundle_smoke
powershell -ExecutionPolicy Bypass -File .\scripts\run_quiet_benchmark.ps1 -BenchmarkArgs '--experiment','allocation','--repetitions','2','--output-dir','tests\_quiet_wrapper_smoke'
python results/demo/generate_demo_bundle.py --output-dir results/demo/final_bundle
python scripts/build_final_report_artifacts.py
```

## Validation Pass Status

- Unit test discovery: PASS on 2026-04-29.
- `main.py --help`: PASS on 2026-04-29.
- `experiments/run_all_experiments.py --help`: PASS on 2026-04-29.
- Allocation smoke run: PASS on 2026-04-29; outputs written under `tests/_alloc_smoke`.
- Demo bundle smoke run: PASS on 2026-04-29; outputs written under `tests/_demo_bundle_smoke`.
- Windows quiet-wrapper smoke run: PASS on 2026-04-29 after wrapper argument normalization; metadata and logs written under `tests/_quiet_wrapper_smoke/metadata`.
- Final demo bundle refresh: PASS on 2026-04-29; copied table now matches `results/tables/best_policy_by_workload.csv`.
- Artifact gate: run `python scripts/build_final_report_artifacts.py`; expected final line is `Summary: PASS`.

## Final Gate

- [ ] `progress_report.tex` uses final-report language, not progress-report language.
- [ ] H1/H2/H3 statuses match `results/processed/hypothesis_evaluation.csv`.
- [ ] Report tables match final generated tables.
- [ ] Report figures exist under `results/figures`.
- [ ] Demo bundle table matches the final table.
- [ ] `progress_report.pdf` compiles after report edits.
