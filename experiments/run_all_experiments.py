#!/usr/bin/env python3
"""
Main experiment runner for the Virtual Memory project.

This script now supports:
- fixed synthetic experiment matrices
- trace-driven experiments routed through the same runner
- wall-clock isolation/shared runtime logging
- environment metadata capture
- hypothesis evaluation exports
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis import generate_summary_report
from environment_capture import write_run_environment
from experiment_runner import (
    ExperimentConfig,
    ExperimentRunner,
    MultiProcessExperimentRunner,
)
from hypothesis_evaluator import evaluate_h1, evaluate_h2, evaluate_h3, evaluation_table
from trace_loader import load_trace_csv
from workload_generator import PREDEFINED_WORKLOADS, WorkloadConfig, WorkloadGenerator, WorkloadType
from visualization import generate_all_plots


FINAL_ALGORITHMS = ["FIFO", "LRU", "NRU", "SecondChance", "WSClock"]
FINAL_ALLOCATIONS = ["GlobalAllocation", "LocalAllocation", "ProportionalAllocation"]
FINAL_SYNTHETIC_WORKLOADS = ["high_locality", "streaming", "mixed", "thrashing"]
FINAL_TRACE_WORKLOAD = "trace-driven"
FINAL_MEMORY_SCALES = [0.8, 1.0, 1.2, 1.5]
FINAL_PROCESS_COUNTS = [2, 4, 8]
DEFAULT_REPETITIONS = 10

ALL_ALGORITHMS = FINAL_ALGORITHMS
ALL_ALLOCATIONS = FINAL_ALLOCATIONS

FINAL_EXPERIMENT_MATRIX = {
    "algorithms": FINAL_ALGORITHMS,
    "allocations": FINAL_ALLOCATIONS,
    "synthetic_workloads": FINAL_SYNTHETIC_WORKLOADS,
    "trace_workload": FINAL_TRACE_WORKLOAD,
    "memory_levels_x_wss": FINAL_MEMORY_SCALES,
    "repetitions": DEFAULT_REPETITIONS,
    "process_counts": FINAL_PROCESS_COUNTS,
    "notes": [
        "Trace-driven runs are kept as a separate family so they can use the checked-in trace files and their native process counts.",
    ],
}

MINIMUM_REAL_RESULTS_MATRIX = {
    "algorithms": ["FIFO", "LRU", "WSClock"],
    "allocations": ["GlobalAllocation", "LocalAllocation"],
    "synthetic_workloads": ["high_locality", "mixed"],
    "trace_workloads": "all",
    "memory_scales": FINAL_MEMORY_SCALES,
    "repetitions": DEFAULT_REPETITIONS,
    "process_counts": [2, 4],
}


def clone_config(config: WorkloadConfig, **updates) -> WorkloadConfig:
    """Create a modified copy of a workload config."""
    return replace(config, **updates)


def default_trace_files() -> List[Path]:
    """Return checked-in trace files from workloads/traces."""
    trace_dir = Path(__file__).parent.parent / "workloads" / "traces"
    if not trace_dir.exists():
        return []
    return sorted(trace_dir.glob("*.csv"))


def resolve_trace_files(trace_files: Optional[Sequence[str]] = None) -> List[Path]:
    """Return trace paths after validating user-provided inputs."""
    if trace_files:
        selected_trace_files = [Path(trace_file) for trace_file in trace_files]
    else:
        selected_trace_files = default_trace_files()

    missing = [str(path) for path in selected_trace_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"trace file not found: {', '.join(missing)}")
    return selected_trace_files


def ensure_output_dirs(output_dir: Path) -> Dict[str, Path]:
    """Create the results bundle directories."""
    directories = {
        "root": output_dir,
        "raw": output_dir / "raw",
        "processed": output_dir / "processed",
        "figures": output_dir / "figures",
        "tables": output_dir / "tables",
        "metadata": output_dir / "metadata",
        "demo": output_dir / "demo",
    }
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)
    return directories


def build_process_workloads(workload_name: str, process_count: int) -> Dict[int, WorkloadConfig]:
    """Build a reproducible synthetic workload mix for the requested family."""
    process_workloads: Dict[int, WorkloadConfig] = {}

    for pid in range(process_count):
        if workload_name == "high_locality":
            process_workloads[pid] = WorkloadConfig(
                workload_type=WorkloadType.HIGH_LOCALITY,
                num_pages=80 + pid * 10,
                num_accesses=1500,
                working_set_size=18 + pid,
                locality_probability=max(0.82, 0.93 - pid * 0.01),
            )
        elif workload_name == "streaming":
            process_workloads[pid] = WorkloadConfig(
                workload_type=WorkloadType.STREAMING,
                num_pages=160 + pid * 20,
                num_accesses=1500,
                sequential_probability=max(0.70, 0.92 - pid * 0.02),
            )
        elif workload_name == "loop":
            process_workloads[pid] = WorkloadConfig(
                workload_type=WorkloadType.LOOP,
                num_pages=90 + pid * 8,
                num_accesses=1500,
                loop_iterations=10 + (pid % 4),
            )
        elif workload_name == "thrashing":
            process_workloads[pid] = WorkloadConfig(
                workload_type=WorkloadType.THRASHING,
                num_pages=120 + pid * 15,
                num_accesses=1500,
            )
        elif workload_name == "mixed":
            cycle = [
                WorkloadType.HIGH_LOCALITY,
                WorkloadType.STREAMING,
                WorkloadType.RANDOM,
                WorkloadType.LOOP,
            ]
            selected = cycle[pid % len(cycle)]
            process_workloads[pid] = WorkloadConfig(
                workload_type=selected,
                num_pages=100 + pid * 12,
                num_accesses=1500,
                working_set_size=16 + (pid % 5),
                locality_probability=0.88,
                sequential_probability=0.85,
                loop_iterations=10,
            )
        else:
            raise ValueError(f"Unknown workload family: {workload_name}")

    return process_workloads


def estimate_aggregate_wss(process_workloads: Dict[int, WorkloadConfig]) -> int:
    """Estimate aggregate working-set size for a synthetic workload mix."""
    total = 0
    for config in process_workloads.values():
        total += WorkloadGenerator(config).estimate_working_set_size()
    return max(total, 1)


def estimate_trace_aggregate_wss(trace_file: str | Path) -> int:
    """Estimate aggregate WSS for a trace-driven workload."""
    events = load_trace_csv(trace_file)
    per_process_pages: Dict[int, set[int]] = {}
    for _, process_id, page_id, _ in events:
        per_process_pages.setdefault(process_id, set()).add(page_id)
    return max(sum(len(pages) for pages in per_process_pages.values()), 1)


def frame_counts_from_wss(
    aggregate_wss: int,
    process_count: int,
    memory_scales: Sequence[float] = FINAL_MEMORY_SCALES,
) -> List[int]:
    """Translate WSS and memory scales into runnable frame counts."""
    minimum_frames = max(2 * process_count, 4)
    counts = {
        max(minimum_frames, int(round(scale * aggregate_wss)))
        for scale in memory_scales
    }
    return sorted(counts)


def result_mean(result: Dict, *path: str) -> Optional[float]:
    """Fetch a nested mean value from a result payload."""
    current = result
    for key in path:
        if key not in current:
            return None
        current = current[key]
    if isinstance(current, dict) and "mean" in current:
        return float(current["mean"])
    if isinstance(current, (int, float)):
        return float(current)
    return None


def result_config(result: Dict) -> Dict:
    """Convenience wrapper for result config payloads."""
    return result.get("config", {})


def _write_csv(path: Path, rows: List[Dict[str, object]]):
    """Write a list of dictionaries to CSV."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown_table(path: Path, rows: List[Dict[str, object]]):
    """Write a simple markdown table."""
    if not rows:
        return
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_runtime_logs(results_list: Sequence[Dict], raw_dir: Path):
    """Export shared/isolation runtime logs from all trial results."""
    shared_rows: List[Dict[str, object]] = []
    isolation_rows: List[Dict[str, object]] = []
    single_rows: List[Dict[str, object]] = []

    for result in results_list:
        for trial in result.get("trial_results", []):
            for record in trial.get("runtime_records", []):
                mode = record.get("mode")
                if mode == "isolation":
                    isolation_rows.append(record)
                elif mode in {"shared", "shared_total"}:
                    shared_rows.append(record)
                else:
                    single_rows.append(record)

    _write_csv(raw_dir / "shared_results.csv", shared_rows)
    _write_csv(raw_dir / "isolation_results.csv", isolation_rows)
    if single_rows:
        _write_csv(raw_dir / "single_results.csv", single_rows)


def export_slowdown_metrics(results_list: Sequence[Dict], processed_dir: Path):
    """Export per-process slowdown metrics to CSV."""
    rows: List[Dict[str, object]] = []
    for result in results_list:
        config = result_config(result)
        for trial in result.get("trial_results", []):
            for process_id, metrics in trial.get("per_process", {}).items():
                rows.append(
                    {
                        "workload_label": trial.get("workload_label") or config.get("workload_label"),
                        "workload_kind": trial.get("workload_kind") or config.get("workload_kind"),
                        "trace_name": trial.get("trace_name") or config.get("trace_name"),
                        "algorithm": config.get("algorithm"),
                        "allocation_policy": config.get("allocation_policy"),
                        "memory_frames": config.get("total_frames") or config.get("num_frames"),
                        "repetition_id": trial.get("trial"),
                        "process_id": process_id,
                        "t_isolated_ms": metrics.get("isolated_runtime_ms"),
                        "t_shared_ms": metrics.get("shared_runtime_ms"),
                        "slowdown": metrics.get("slowdown"),
                        "page_faults": metrics.get("page_faults"),
                        "replacements": metrics.get("page_replacements"),
                        "disk_reads": metrics.get("disk_reads"),
                        "disk_writes": metrics.get("disk_writes"),
                    }
                )
    _write_csv(processed_dir / "slowdown_metrics.csv", rows)


def export_best_policy_table(results_list: Sequence[Dict], tables_dir: Path):
    """Export a compact 'best policy per workload' table."""
    grouped: Dict[tuple[str, str], List[Dict]] = {}
    for result in results_list:
        config = result_config(result)
        workload_label = result.get("workload_label") or config.get("workload_label")
        allocation = config.get("allocation_policy")
        algorithm = config.get("algorithm")
        if not workload_label or not algorithm or not allocation:
            continue
        grouped.setdefault((workload_label, config.get("workload_kind", "unknown")), []).append(result)

    rows: List[Dict[str, object]] = []
    for (workload_label, workload_kind), candidates in sorted(grouped.items()):
        best_fault = min(candidates, key=lambda item: result_mean(item, "system", "page_faults") or float("inf"))
        best_slowdown = min(
            candidates,
            key=lambda item: result_mean(item, "system", "worst_case_slowdown") or float("inf"),
        )
        best_fairness = max(
            candidates,
            key=lambda item: result_mean(item, "fairness_metrics", "jains_index") or float("-inf"),
        )
        rows.append(
            {
                "workload": workload_label,
                "kind": workload_kind,
                "lowest_page_faults": f"{result_config(best_fault).get('algorithm')} + {result_config(best_fault).get('allocation_policy')}",
                "lowest_worst_slowdown": f"{result_config(best_slowdown).get('algorithm')} + {result_config(best_slowdown).get('allocation_policy')}",
                "highest_jains_index": f"{result_config(best_fairness).get('algorithm')} + {result_config(best_fairness).get('allocation_policy')}",
            }
        )

    _write_csv(tables_dir / "best_policy_by_workload.csv", rows)


def _find_matching_result(
    results_list: Sequence[Dict],
    *,
    workload_label: str,
    algorithm: str,
    allocation_policy: str,
    process_count: Optional[int],
    target_memory_ratio: float,
) -> Optional[Dict]:
    candidates = []
    for result in results_list:
        config = result_config(result)
        if config.get("workload_label") != workload_label:
            continue
        if config.get("algorithm") != algorithm:
            continue
        if config.get("allocation_policy") != allocation_policy:
            continue
        if process_count is not None and config.get("process_count") != process_count:
            continue
        ratio = result_mean(result, "memory_ratio_to_wss")
        if ratio is None:
            continue
        candidates.append((abs(ratio - target_memory_ratio), result))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _best_family_result(
    results_list: Sequence[Dict],
    *,
    workload_label: str,
    algorithms: Sequence[str],
    allocation_policy: str,
    process_count: int,
    target_memory_ratio: float,
) -> Optional[Dict]:
    candidates = []
    for algorithm in algorithms:
        result = _find_matching_result(
            results_list,
            workload_label=workload_label,
            algorithm=algorithm,
            allocation_policy=allocation_policy,
            process_count=process_count,
            target_memory_ratio=target_memory_ratio,
        )
        if result is not None:
            candidates.append(result)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: result_mean(item, "system", "worst_case_slowdown") or float("inf"),
    )


def export_hypothesis_summary(results_list: Sequence[Dict], processed_dir: Path, tables_dir: Path):
    """Evaluate H1/H2/H3 from the available result set when enough data exists."""
    evaluations = []

    lru_global_h1 = _find_matching_result(
        results_list,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.2,
    )
    lru_local_h1 = _find_matching_result(
        results_list,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.2,
    )
    if lru_global_h1 and lru_local_h1:
        evaluations.append(
            evaluate_h1(
                high_locality_condition="High locality, 4 processes, near 1.2x aggregate WSS",
                lru_global_faults=result_mean(lru_global_h1, "system", "page_faults") or 0.0,
                lru_local_faults=result_mean(lru_local_h1, "system", "page_faults") or 0.0,
                lru_global_worst_slowdown=result_mean(lru_global_h1, "system", "worst_case_slowdown") or 0.0,
                lru_local_worst_slowdown=result_mean(lru_local_h1, "system", "worst_case_slowdown") or 0.0,
            )
        )

    lru_global_h2 = _find_matching_result(
        results_list,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    lru_local_h2 = _find_matching_result(
        results_list,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    if lru_global_h2 and lru_local_h2:
        evaluations.append(
            evaluate_h2(
                memory_pressure_condition="Near the aggregate WSS boundary, 4 processes",
                global_slowdown_variance=result_mean(lru_global_h2, "fairness_metrics", "variance") or 0.0,
                local_slowdown_variance=result_mean(lru_local_h2, "fairness_metrics", "variance") or 0.0,
            )
        )

    simple_local = _best_family_result(
        results_list,
        workload_label="mixed",
        algorithms=["FIFO", "NRU"],
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    advanced_global = _best_family_result(
        results_list,
        workload_label="mixed",
        algorithms=["LRU", "WSClock"],
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    if simple_local and advanced_global:
        evaluations.append(
            evaluate_h3(
                heterogeneous_workload_condition="Mixed workload, 4 processes, near aggregate WSS",
                simple_local_worst_slowdown=result_mean(simple_local, "system", "worst_case_slowdown") or 0.0,
                advanced_global_worst_slowdown=result_mean(advanced_global, "system", "worst_case_slowdown") or 0.0,
                simple_local_faults=result_mean(simple_local, "system", "page_faults"),
                advanced_global_faults=result_mean(advanced_global, "system", "page_faults"),
            )
        )

    if not evaluations:
        return

    table_rows = evaluation_table(evaluations)
    _write_csv(processed_dir / "hypothesis_evaluation.csv", table_rows)
    _write_markdown_table(tables_dir / "hypothesis_evaluation.md", table_rows)


def attach_configured_fairness(results: Iterable[Dict]):
    """Normalize fairness metrics onto top-level results for downstream exports."""
    for result in results:
        if "fairness_metrics" not in result and "system" in result:
            fairness = result.get("fairness_metrics")
            if fairness:
                result["fairness_metrics"] = fairness


def run_single_process_experiments(output_dir: str = "results", *, num_trials: int = DEFAULT_REPETITIONS):
    """Run single-process experiments across the standard algorithms."""
    print("\n" + "=" * 80)
    print("SINGLE-PROCESS EXPERIMENTS")
    print("=" * 80 + "\n")

    workloads = {
        "high_locality": PREDEFINED_WORKLOADS["small_locality"],
        "streaming": PREDEFINED_WORKLOADS["large_streaming"],
        "mixed": PREDEFINED_WORKLOADS["mixed_heterogeneous"],
    }

    results = []
    for algorithm in ALL_ALGORITHMS:
        for workload_name, workload_config in workloads.items():
            config = ExperimentConfig(
                name=f"single_{algorithm}_{workload_name}",
                algorithm=algorithm,
                allocation_policy="LocalAllocation",
                num_frames=50,
                workload_config=clone_config(workload_config),
                num_trials=num_trials,
                output_dir=output_dir,
                workload_name=workload_name,
            )
            runner = ExperimentRunner(config)
            result = runner.run()
            runner.save_results(output_dir)
            results.append(result)
    return results


def run_synthetic_matrix(
    output_dir: str,
    *,
    workload_labels: Sequence[str],
    algorithms: Sequence[str],
    allocations: Sequence[str],
    process_counts: Sequence[int],
    memory_scales: Sequence[float],
    num_trials: int,
) -> List[Dict]:
    """Run a configurable synthetic multi-process experiment matrix."""
    results: List[Dict] = []
    for workload_label in workload_labels:
        for process_count in process_counts:
            process_workloads = build_process_workloads(workload_label, process_count)
            aggregate_wss = estimate_aggregate_wss(process_workloads)
            for total_frames in frame_counts_from_wss(aggregate_wss, process_count, memory_scales):
                for algorithm in algorithms:
                    for allocation_policy in allocations:
                        print(
                            f"\nRunning synthetic matrix: {workload_label}, {process_count} procs, "
                            f"{algorithm}, {allocation_policy}, frames={total_frames}"
                        )
                        runner = MultiProcessExperimentRunner(
                            algorithm=algorithm,
                            allocation_policy=allocation_policy,
                            total_frames=total_frames,
                            process_workloads=process_workloads,
                            interleave="random",
                            num_trials=num_trials,
                            warmup_runs=1,
                            workload_label=workload_label,
                        )
                        result = runner.run()
                        runner.save_results(output_dir)
                        results.append(result)
    return results


def run_allocation_policy_comparison(output_dir: str = "results", *, num_trials: int = DEFAULT_REPETITIONS):
    """Run a focused global/local/proportional comparison."""
    print("\n" + "=" * 80)
    print("ALLOCATION POLICY COMPARISON")
    print("=" * 80 + "\n")

    return run_synthetic_matrix(
        output_dir,
        workload_labels=["high_locality", "mixed"],
        algorithms=["FIFO", "LRU"],
        allocations=["GlobalAllocation", "LocalAllocation", "ProportionalAllocation"],
        process_counts=[4],
        memory_scales=FINAL_MEMORY_SCALES,
        num_trials=num_trials,
    )


def run_memory_pressure_experiments(output_dir: str = "results", *, num_trials: int = DEFAULT_REPETITIONS):
    """Run memory-pressure experiments near the WSS boundary."""
    print("\n" + "=" * 80)
    print("MEMORY PRESSURE EXPERIMENTS")
    print("=" * 80 + "\n")

    return run_synthetic_matrix(
        output_dir,
        workload_labels=["high_locality"],
        algorithms=["FIFO", "LRU", "WSClock"],
        allocations=["GlobalAllocation", "LocalAllocation"],
        process_counts=[2, 4],
        memory_scales=FINAL_MEMORY_SCALES,
        num_trials=num_trials,
    )


def run_fairness_focused_experiments(output_dir: str = "results", *, num_trials: int = DEFAULT_REPETITIONS):
    """Run mixed-workload fairness experiments."""
    print("\n" + "=" * 80)
    print("FAIRNESS-FOCUSED EXPERIMENTS")
    print("=" * 80 + "\n")

    return run_synthetic_matrix(
        output_dir,
        workload_labels=["mixed"],
        algorithms=["FIFO", "NRU", "LRU", "WSClock"],
        allocations=["LocalAllocation", "GlobalAllocation"],
        process_counts=[4, 8],
        memory_scales=FINAL_MEMORY_SCALES,
        num_trials=num_trials,
    )


def run_thrashing_experiments(output_dir: str = "results", *, num_trials: int = 5):
    """Run thrashing-focused experiments."""
    print("\n" + "=" * 80)
    print("THRASHING EXPERIMENTS")
    print("=" * 80 + "\n")

    return run_synthetic_matrix(
        output_dir,
        workload_labels=["thrashing"],
        algorithms=["FIFO", "LRU", "SecondChance", "WSClock"],
        allocations=["LocalAllocation", "GlobalAllocation"],
        process_counts=[2, 4],
        memory_scales=FINAL_MEMORY_SCALES,
        num_trials=num_trials,
    )


def run_trace_driven_experiments(
    output_dir: str = "results",
    *,
    trace_files: Optional[Sequence[str]] = None,
    algorithms: Sequence[str] = ALL_ALGORITHMS,
    allocations: Sequence[str] = ALL_ALLOCATIONS,
    num_trials: int = DEFAULT_REPETITIONS,
    workload_label: str = FINAL_TRACE_WORKLOAD,
) -> List[Dict]:
    """Run trace-driven experiments through the shared multi-process runner."""
    print("\n" + "=" * 80)
    print("TRACE-DRIVEN EXPERIMENTS")
    print("=" * 80 + "\n")

    selected_trace_files = resolve_trace_files(trace_files)

    results: List[Dict] = []
    for trace_file in selected_trace_files:
        aggregate_wss = estimate_trace_aggregate_wss(trace_file)
        events = load_trace_csv(trace_file)
        process_count = len({event[1] for event in events})
        for total_frames in frame_counts_from_wss(aggregate_wss, process_count, FINAL_MEMORY_SCALES):
            for algorithm in algorithms:
                for allocation_policy in allocations:
                    print(
                        f"\nRunning trace experiment: {trace_file.name}, {algorithm}, "
                        f"{allocation_policy}, frames={total_frames}"
                    )
                    runner = MultiProcessExperimentRunner(
                        algorithm=algorithm,
                        allocation_policy=allocation_policy,
                        total_frames=total_frames,
                        trace_file=str(trace_file),
                        trace_name=trace_file.stem,
                        workload_label=workload_label,
                        interleave="trace-order",
                        num_trials=num_trials,
                        warmup_runs=1,
                    )
                    result = runner.run()
                    runner.save_results(output_dir)
                    results.append(result)
    return results


def run_final_experiment_matrix(
    output_dir: str = "results",
    *,
    trace_files: Optional[Sequence[str]] = None,
) -> List[Dict]:
    """Run the fixed paper-sized matrix from the project plan."""
    print("\n" + "=" * 80)
    print("FINAL EXPERIMENT MATRIX")
    print("=" * 80 + "\n")
    print(json.dumps(FINAL_EXPERIMENT_MATRIX, indent=2))

    results = []
    results.extend(
        run_synthetic_matrix(
            output_dir,
            workload_labels=FINAL_EXPERIMENT_MATRIX["synthetic_workloads"],
            algorithms=FINAL_EXPERIMENT_MATRIX["algorithms"],
            allocations=FINAL_EXPERIMENT_MATRIX["allocations"],
            process_counts=FINAL_EXPERIMENT_MATRIX["process_counts"],
            memory_scales=FINAL_EXPERIMENT_MATRIX["memory_levels_x_wss"],
            num_trials=FINAL_EXPERIMENT_MATRIX["repetitions"],
        )
    )
    results.extend(
        run_trace_driven_experiments(
            output_dir,
            trace_files=trace_files,
            algorithms=FINAL_EXPERIMENT_MATRIX["algorithms"],
            allocations=FINAL_EXPERIMENT_MATRIX["allocations"],
            num_trials=FINAL_EXPERIMENT_MATRIX["repetitions"],
            workload_label=FINAL_EXPERIMENT_MATRIX["trace_workload"],
        )
    )
    return results


def write_all_exports(results: Sequence[Dict], directories: Dict[str, Path]):
    """Write runtime logs, processed metrics, tables, summary report, and figures."""
    export_runtime_logs(results, directories["raw"])
    export_slowdown_metrics(results, directories["processed"])
    export_best_policy_table(results, directories["tables"])
    export_hypothesis_summary(results, directories["processed"], directories["tables"])
    generate_summary_report(list(results), str(directories["root"] / "summary_report.txt"))
    generate_all_plots(str(directories["root"]), str(directories["figures"]))


def main():
    parser = argparse.ArgumentParser(description="Run Virtual Memory Experiments")
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save results (default: results)",
    )
    parser.add_argument(
        "--experiment",
        choices=["all", "single", "allocation", "pressure", "fairness", "thrashing", "trace"],
        default="all",
        help="Which experiment to run (default: all)",
    )
    parser.add_argument(
        "--trace-file",
        action="append",
        help="Trace CSV file to include for trace-driven experiments. May be repeated.",
    )
    parser.add_argument(
        "--include-traces",
        action="store_true",
        help="Include trace-driven experiments when running --experiment all.",
    )
    parser.add_argument(
        "--final",
        action="store_true",
        help=(
            "Run the frozen final matrix: 5 algorithms, 3 allocation policies, "
            "4 synthetic workloads, 4 memory levels (0.8/1.0/1.2/1.5 x WSS), "
            "10 repetitions, 2/4/8 process counts, plus trace-driven runs."
        ),
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help="Override repetitions for non-final experiment families.",
    )
    parser.add_argument(
        "--pinned-cores",
        default=None,
        help="Optional CPU affinity metadata to record alongside the run.",
    )
    args = parser.parse_args()

    if args.final or args.experiment == "trace" or args.trace_file:
        try:
            resolve_trace_files(args.trace_file)
        except FileNotFoundError as exc:
            parser.error(str(exc))

    output_dir = Path(args.output_dir)
    directories = ensure_output_dirs(output_dir)
    write_run_environment(
        directories["metadata"] / "run_environment.json",
        Path(__file__).parent.parent,
        pinned_cores=args.pinned_cores,
    )

    all_results: List[Dict] = []
    if args.final:
        all_results.extend(run_final_experiment_matrix(str(output_dir), trace_files=args.trace_file))
    else:
        if args.experiment in {"all", "single"}:
            all_results.extend(run_single_process_experiments(str(output_dir), num_trials=args.repetitions))
        if args.experiment in {"all", "allocation"}:
            all_results.extend(run_allocation_policy_comparison(str(output_dir), num_trials=args.repetitions))
        if args.experiment in {"all", "pressure"}:
            all_results.extend(run_memory_pressure_experiments(str(output_dir), num_trials=args.repetitions))
        if args.experiment in {"all", "fairness"}:
            all_results.extend(run_fairness_focused_experiments(str(output_dir), num_trials=args.repetitions))
        if args.experiment in {"all", "thrashing"}:
            all_results.extend(run_thrashing_experiments(str(output_dir), num_trials=max(5, min(args.repetitions, 10))))
        if args.experiment == "trace" or (args.experiment == "all" and (args.include_traces or args.trace_file)):
            all_results.extend(
                run_trace_driven_experiments(
                    str(output_dir),
                    trace_files=args.trace_file,
                    num_trials=args.repetitions,
                )
            )

    print("\n" + "=" * 80)
    print("GENERATING REPORTS AND EXPORTS")
    print("=" * 80 + "\n")
    write_all_exports(all_results, directories)

    print("\n" + "=" * 80)
    print("EXPERIMENTS COMPLETED")
    print("=" * 80)
    print(f"\nResults saved to: {directories['root']}")
    print(f"Figures saved to: {directories['figures']}")
    print(f"Summary report: {directories['root'] / 'summary_report.txt'}")
    print(f"Hypothesis evaluation: {directories['processed'] / 'hypothesis_evaluation.csv'}")


if __name__ == "__main__":
    main()
