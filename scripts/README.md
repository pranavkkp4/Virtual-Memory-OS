# Benchmark Wrappers

These scripts run the existing experiment driver with lightweight benchmark controls and metadata capture.

## Files

- `run_pinned.ps1`: Windows PowerShell wrapper that pins the Python process to one or more CPU cores.
- `run_quiet_benchmark.ps1`: Windows PowerShell wrapper that lowers process priority and captures metadata.
- `run_pinned.sh`: bash wrapper that uses `taskset` when available.
- `run_quiet_benchmark.sh`: bash wrapper that uses `nice` and `ionice` when available.

## Defaults

If you run a wrapper with no extra arguments, it executes:

```text
python experiments/run_all_experiments.py --experiment all
```

You can pass through any additional experiment arguments after the wrapper name.

## Metadata Output

Each run writes two artifacts into `results/metadata/`:

- `run_environment_<timestamp>.json`
- `run_output_<timestamp>.log`

The metadata JSON is intended to capture:

- `timestamp`
- `mode` (`pinned` or `quiet`)
- `repo_root`
- `results_dir`
- `python_executable`
- `python_version`
- `git_commit`
- `benchmark_args`
- `command`

Pinned runs also record:

- `pinned_cores`
- `processor_affinity_mask` on Windows

Quiet runs also record:

- `process_priority`

## Examples

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_pinned.ps1 -Cores 2,3 -BenchmarkArgs '--experiment', 'fairness'
powershell -ExecutionPolicy Bypass -File .\scripts\run_quiet_benchmark.ps1 -BenchmarkArgs '--experiment', 'trace', '--trace-file', 'workloads\traces\sample_trace.csv', '--repetitions', '2'
```

bash:

```bash
./scripts/run_pinned.sh --experiment fairness
./scripts/run_quiet_benchmark.sh --experiment trace
```

## Notes

- These wrappers do not change the simulation code.
- They are meant to standardize benchmark invocation, capture session metadata, and make later analysis easier.
- If `taskset`, `nice`, or `ionice` are unavailable, the bash wrappers fall back to a normal launch.
