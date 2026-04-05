# Quick Start

## Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

## Verify the Project Loads

```powershell
python -m unittest discover -s tests -v
python main.py --help
python experiments\run_all_experiments.py --help
```

## Run a Simple Simulation

```powershell
python main.py simulate --algorithm LRU --frames 50 --workload small_locality
```

## Run an Experiment Family

```powershell
python main.py experiment --type single --output results
python main.py experiment --type allocation --output results
python main.py experiment --type pressure --output results
python main.py experiment --type fairness --output results
python main.py experiment --type thrashing --output results
python main.py experiment --type trace --trace-file workloads\traces\sample_trace.csv --output results
```

You can also call the experiment driver directly:

```powershell
python experiments\run_all_experiments.py --experiment allocation --output-dir results
python experiments\run_all_experiments.py --experiment all --include-traces --trace-file workloads\traces\sample_trace.csv --repetitions 2 --output-dir results
python experiments\run_all_experiments.py --final --trace-file workloads\traces\sample_trace.csv --output-dir results
```

## Generate and Inspect Outputs

```powershell
python main.py analyze --input results
python main.py visualize --input results --output results\figures
Get-Content results\summary_report.txt
Get-Content results\processed\hypothesis_evaluation.csv
```

Typical output locations:

- `results\*.json`: raw experiment summaries
- `results\raw\shared_results.csv` and `results\raw\isolation_results.csv`: measured runtime logs
- `results\processed\slowdown_metrics.csv`: per-process shared vs isolated slowdown metrics
- `results\processed\hypothesis_evaluation.csv`: H1/H2/H3 outcome table
- `results\summary_report.txt`: aggregated text summary
- `results\figures\*.png`: generated plots
- `results\tables\*.csv` and `results\tables\*.md`: report-ready tables

## Run Benchmark Wrappers

The repository includes wrappers that record host metadata and benchmark logs.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_pinned.ps1 -Cores 2 -BenchmarkArgs '--experiment','trace','--trace-file','workloads\traces\sample_trace.csv','--repetitions','2'
powershell -ExecutionPolicy Bypass -File scripts\run_quiet_benchmark.ps1 -BenchmarkArgs '--experiment','allocation','--repetitions','2'
```

These wrappers write environment snapshots and logs under `results\metadata\`.

## Run The Checked-In Demo Bundle

```powershell
python results\demo\generate_demo_bundle.py --output-dir results\demo\final_bundle
```

The demo script runs one tiny synthetic family plus one tiny trace-driven family and exports a self-contained bundle with raw logs, slowdown metrics, plots, and report-ready tables. Larger matrices such as `--experiment allocation` or `--final` also emit `results\processed\hypothesis_evaluation.csv` when the H1/H2/H3 comparison conditions are present.

## Minimal Python Example

```python
from src.page_replacement import LRU
from src.workload_generator import WorkloadConfig, WorkloadGenerator, WorkloadType

config = WorkloadConfig(
    workload_type=WorkloadType.HIGH_LOCALITY,
    num_pages=100,
    num_accesses=1000,
    working_set_size=20,
    locality_probability=0.9,
)

trace = WorkloadGenerator(config).generate()
algorithm = LRU(num_frames=25)

for page_id, process_id, is_write in trace:
    algorithm.access_page(page_id, process_id, is_write)

print(algorithm.get_stats())
```

## Notes

- `src.*` imports now work directly from the project root.
- Multi-process experiments now measure wall-clock runtime with `time.perf_counter_ns()`.
- Slowdown is computed from shared replay time divided by isolated replay time for each process.
- Trace CSV files are normalized into `(timestamp, process_id, page_id, is_write)` events before replay.
