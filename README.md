# Virtual Memory Replacement & Allocation

Research codebase for comparing page replacement algorithms and frame allocation policies under memory pressure.

## Team

- Pranav Kumar Kaliaperumal (110042133)
- Akanksha Gutal (111860280)
- Spandana Erukulla (111447474)

## Scope

The project studies how replacement policy and frame allocation interact in multiprogrammed systems. The current repository supports:

- Page replacement algorithms: `FIFO`, `LRU`, `NRU`, `SecondChance`, `WSClock`
- Allocation policies: `GlobalAllocation`, `LocalAllocation`, `ProportionalAllocation`
- Synthetic workloads: high locality, streaming, random, mixed, loop, thrashing
- Trace-driven experiments routed through the same main runner as synthetic workloads
- Measured wall-clock slowdown from shared vs isolated replay timing
- Experiment automation for single-process and multi-process runs
- Summary analysis, hypothesis evaluation, and plot generation
- Benchmark-control wrappers for pinned and quiet benchmark sessions

## Repository Layout

```text
Virtual Memory/
|-- docs/
|   |-- QUICKSTART.md
|   |-- RESULTS_BUNDLE.md
|   `-- TRACE_FORMAT.md
|-- experiments/
|   `-- run_all_experiments.py
|-- results/
|   |-- raw/
|   |-- processed/
|   |-- figures/
|   |-- tables/
|   `-- demo/
|-- scripts/
|   |-- run_pinned.ps1
|   |-- run_quiet_benchmark.ps1
|   |-- run_pinned.sh
|   `-- run_quiet_benchmark.sh
|-- src/
|   |-- analysis.py
|   |-- environment_capture.py
|   |-- experiment_runner.py
|   |-- frame_allocation.py
|   |-- hypothesis_evaluator.py
|   |-- page_replacement.py
|   |-- runtime_measurement.py
|   |-- trace_loader.py
|   |-- trace_normalizer.py
|   |-- visualization.py
|   `-- workload_generator.py
|-- tests/
|   |-- test_page_replacement.py
|   |-- test_project_setup.py
|   |-- test_runtime_measurement.py
|   |-- test_trace_loader.py
|   `-- test_trace_pipeline.py
|-- workloads/
|   `-- traces/
|-- main.py
|-- progress_report.bib
|-- progress_report.tex
`-- requirements.txt
```

The checked-in `results\` directories hold the submission-ready bundle layout, and the runner fills them with JSON, CSV, figures, and hypothesis tables.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Validation

```powershell
python -m unittest discover -s tests -v
python main.py --help
python experiments\run_all_experiments.py --help
```

## Usage

Run a single simulation:

```powershell
python main.py simulate --algorithm LRU --frames 50 --workload small_locality
```

Run one experiment family:

```powershell
python main.py experiment --type allocation --output results
python main.py experiment --type trace --trace-file workloads\traces\sample_trace.csv --output results
```

Run the fixed paper-sized matrix directly:

```powershell
python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
```

Run the lightweight checked-in demo bundle:

```powershell
python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle
```

Run benchmark wrappers with metadata capture:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_pinned.ps1 -Cores 2 -BenchmarkArgs '--experiment','trace','--trace-file','workloads\traces\sample_trace.csv','--repetitions','2'
powershell -ExecutionPolicy Bypass -File scripts\run_quiet_benchmark.ps1 -BenchmarkArgs '--experiment','allocation','--repetitions','2'
```

Analyze saved results:

```powershell
python main.py analyze --input results
python main.py visualize --input results --output results\figures
```

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [Results Bundle Guide](docs/RESULTS_BUNDLE.md)
- [Trace Format](docs/TRACE_FORMAT.md)
- [Progress Report LaTeX](progress_report.tex)
