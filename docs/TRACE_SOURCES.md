# Trace Sources

This repository keeps a small, final trace set in `workloads/traces/` for
sanity checks and trace-driven report runs. The set is intentionally tiny so it
can stay in-repo and be replayed quickly.

## Shared Assumptions

- Page size for normalization: `4096` bytes.
- Address-to-page conversion: `page_id = address // 4096`.
- All trace files are CSV with the canonical columns
  `timestamp,process_id,address,is_write`.
- The loader treats comments as metadata and ignores them during parsing.
- Timestamps are zero-based and sorted before replay.
- Process IDs are stable, small integers assigned per file to reflect the
  intended workload roles.

## Catalog

| File | Role | Source / provenance | PID assignment | Cleanup / normalization |
| --- | --- | --- | --- | --- |
| `workloads/traces/sample_trace.csv` | Demo sanity fixture | Pre-existing repo sample used by loader tests and quickstart examples. It is kept as the smallest mixed demo. | `0` = first stream, `1` = second stream. | Kept as-is except for the canonical CSV header/comments already present; addresses are normalized with `4096`-byte pages. |
| `workloads/traces/demo_locality.csv` | Demo sanity fixture | Hand-curated from the high-locality archetype in `src/workload_generator.py` and trimmed to 8 events. | `0` = hot locality stream, `1` = companion hot stream. | Reduced to a minimal in-repo smoke trace, timestamps reset to `0..7`, and addresses chosen so pages remain stable under `address // 4096`. |
| `workloads/traces/report_locality_heavy.csv` | Report trace | Hand-built from the high-locality workload archetype, with two processes repeatedly touching a small hot set. | `0` = locality-heavy process, `1` = second locality-heavy process. | Trimmed to 16 events, kept only the canonical columns, and normalized to `4096`-byte page boundaries with a few intra-page offsets. |
| `workloads/traces/report_streaming_sequential.csv` | Report trace | Hand-built from the streaming archetype and compressed into two sequential scans. | `0` = first scanner, `1` = second scanner. | Trimmed to 16 events, timestamps made contiguous, and page addresses laid out as a sequential walk with a small write mix. |
| `workloads/traces/report_mixed_heterogeneous.csv` | Report trace | Hand-built from the mixed archetype to preserve locality, streaming, and loop-like reuse in one trace. | `0` = locality phase, `1` = streaming phase, `2` = loop / reuse phase. | Collapsed to 18 events, reordered into a readable interleave, and stripped to one canonical CSV per event stream. |
| `workloads/traces/report_thrashing_pressure.csv` | Report trace | Hand-built from the thrashing archetype, with two competing streams that exceed a small frame budget. | `0` = first pressure stream, `1` = second pressure stream. | Trimmed to 20 events, kept the repeated 5-page cycles, and used small intra-page offsets so the trace still normalizes cleanly to page IDs. |

## Notes

- No trace in this directory depends on external capture or large raw dumps.
- The report traces are deliberately small enough to remain readable in code
  review and stable in version control.
- If you replay these traces with a different page size, the page IDs will
  change for address-based rows; the documentation and report assumptions use
  `4096` bytes throughout.
