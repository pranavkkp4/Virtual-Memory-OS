# Full Benchmark Campaign Log (Task 5 Ownership)

This log is the authoritative record for the benchmark campaign runs executed for the frozen final matrix.

## Campaign

- Campaign ID: `campaign_20260404_140330_266`
- Started (America/Denver): `2026-04-04`
- Runner: `experiments/run_all_experiments.py`
- Matrix source: `FINAL_EXPERIMENT_MATRIX` in `experiments/run_all_experiments.py`

### Frozen Final Matrix (As Implemented)

- Algorithms: FIFO, LRU, NRU, SecondChance, WSClock
- Allocation policies: GlobalAllocation, LocalAllocation, ProportionalAllocation
- Synthetic workload families: high_locality, streaming, mixed, thrashing
- Memory levels: 0.8, 1.0, 1.2, 1.5 (x aggregate WSS)
- Process counts: 2, 4, 8
- Repetitions: 10
- Trace-driven workloads: checked-in CSV traces under `workloads/traces/*.csv`

### Output Convention

- Batch outputs go under: `results/raw/campaign_20260404_140330_266/<batch_id>/`
- Batch metadata/manifests go under: `results/metadata/campaign_20260404_140330_266/<batch_id>/`
- Each batch is run in its own fresh directory to avoid overwriting earlier results.

## Batches

Planned workload-family batches:

- `synthetic_high_locality`
- `synthetic_streaming`
- `synthetic_mixed`
- `synthetic_thrashing`
- `trace_all_checked_in`

## Run Log

### 2026-04-04

- Started `synthetic_high_locality` (run id `20260404_140413_212`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_high_locality/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_high_locality/`
- Note: run id `20260404_140413_212` failed immediately (PowerShell `Start-Process` argument splitting caused a `python -c` SyntaxError). Retrying with direct invocation.
- Started `synthetic_high_locality` retry (run id `20260404_140516_666`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_high_locality/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_high_locality/`
- Note: run id `20260404_140516_666` failed immediately (bad quoting around raw-string path inside the `python -c` snippet). Retrying.
- Started `synthetic_high_locality` retry 2 (run id `20260404_140600_757`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_high_locality/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_high_locality/`
- Note: run id `20260404_140600_757` failed immediately (Windows argv parsing stripped quotes inside the embedded `-c` snippet). Switching to passing `output_dir` as `sys.argv[1]` instead of embedding it.
- Started `synthetic_high_locality` retry 3 (run id `20260404_140704_592`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_high_locality/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_high_locality/`
- Completed `synthetic_high_locality` (run id `20260404_140704_592`)
  - Start: `2026-04-04T14:07:33-06:00`
  - End: `2026-04-04T14:10:58-06:00`
  - Result JSONs: 180 (`multiproc_high_locality_..._p{2,4,8}_f{...}.json`)
  - Manifest: `results/metadata/campaign_20260404_140330_266/synthetic_high_locality/manifest_20260404_140704_592.json`
- Started `synthetic_streaming` (run id `20260404_141124_263`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_streaming/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_streaming/`
- Completed `synthetic_streaming` (run id `20260404_141124_263`)
  - Start: `2026-04-04T14:11:49-06:00`
  - End: `2026-04-04T14:15:19-06:00`
  - Result JSONs: 180
  - Manifest: `results/metadata/campaign_20260404_140330_266/synthetic_streaming/manifest_20260404_141124_263.json`
- Started `synthetic_mixed` (run id `20260404_141538_872`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_mixed/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_mixed/`
- Completed `synthetic_mixed` (run id `20260404_141538_872`)
  - Start: `2026-04-04T14:16:04-06:00`
  - End: `2026-04-04T14:19:33-06:00`
  - Result JSONs: 180
  - Manifest: `results/metadata/campaign_20260404_140330_266/synthetic_mixed/manifest_20260404_141538_872.json`
- Started `synthetic_thrashing` (run id `20260404_141948_306`)
  - Outputs: `results/raw/campaign_20260404_140330_266/synthetic_thrashing/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/synthetic_thrashing/`
- Completed `synthetic_thrashing` (run id `20260404_141948_306`)
  - Start: `2026-04-04T14:20:11-06:00`
  - End: `2026-04-04T14:24:05-06:00`
  - Result JSONs: 180
  - Manifest: `results/metadata/campaign_20260404_140330_266/synthetic_thrashing/manifest_20260404_141948_306.json`
- Started `trace_all_checked_in` (run id `20260404_142423_554`)
  - Outputs: `results/raw/campaign_20260404_140330_266/trace_all_checked_in/`
  - Metadata: `results/metadata/campaign_20260404_140330_266/trace_all_checked_in/`
- Completed `trace_all_checked_in` (run id `20260404_142423_554`)
  - Start: `2026-04-04T14:24:53-06:00`
  - End: `2026-04-04T14:25:13-06:00`
  - Result JSONs: 300 (`trace_<trace>_<algorithm>_<allocation>_f<frames>.json`)
  - Manifest: `results/metadata/campaign_20260404_140330_266/trace_all_checked_in/manifest_20260404_142423_554.json`

- Status: all planned workload-family batches for the frozen final matrix completed for campaign `campaign_20260404_140330_266`.
