"""
Experiment runners for the virtual memory research project.

This module supports both synthetic workloads and trace-driven workloads.
It records wall-clock runtimes for single-process and multi-process replay
using ``time.perf_counter_ns()`` through ``runtime_measurement`` helpers.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from tqdm import tqdm

try:
    from .analysis import calculate_fairness_metrics
    from .frame_allocation import ProportionalAllocation, get_allocation_policy
    from .page_replacement import get_algorithm
    from .runtime_measurement import build_runtime_record, measure_once
    from .trace_loader import load_trace_csv
    from .trace_normalizer import TraceEvent
    from .workload_generator import (
        MultiProcessWorkloadGenerator,
        WorkloadConfig,
        WorkloadGenerator,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from analysis import calculate_fairness_metrics
    from frame_allocation import ProportionalAllocation, get_allocation_policy
    from page_replacement import get_algorithm
    from runtime_measurement import build_runtime_record, measure_once
    from trace_loader import load_trace_csv
    from trace_normalizer import TraceEvent
    from workload_generator import MultiProcessWorkloadGenerator, WorkloadConfig, WorkloadGenerator


AccessEvent = Tuple[int, int, bool]


def _mean_std_ci(values: Sequence[float]) -> Dict[str, float | tuple[float, float]]:
    """Return mean/std and a simple 95% CI payload."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "ci_95": (0.0, 0.0)}

    values_array = np.asarray(values, dtype=float)
    mean_value = float(np.mean(values_array))
    std_value = float(np.std(values_array))
    ci_radius = 1.96 * std_value / np.sqrt(len(values_array))
    return {
        "mean": mean_value,
        "std": std_value,
        "ci_95": (float(mean_value - ci_radius), float(mean_value + ci_radius)),
    }


def _estimate_wss_from_trace(trace: Sequence[AccessEvent], window_size: int = 1000) -> int:
    """Estimate working set size from a page-access trace."""
    if not trace:
        return 0

    if len(trace) <= window_size:
        return len({page_id for page_id, _, _ in trace})

    max_wss = 0
    for index in range(len(trace) - window_size + 1):
        window = trace[index : index + window_size]
        unique_pages = len({page_id for page_id, _, _ in window})
        max_wss = max(max_wss, unique_pages)
    return max_wss


def canonical_trace_to_access_trace(events: Sequence[TraceEvent]) -> List[AccessEvent]:
    """Drop timestamps from canonical trace events for replay."""
    return [(page_id, process_id, is_write) for _, process_id, page_id, is_write in events]


def canonical_trace_to_process_traces(events: Sequence[TraceEvent]) -> Dict[int, List[AccessEvent]]:
    """Split canonical trace events into per-process replay traces."""
    process_traces: Dict[int, List[AccessEvent]] = defaultdict(list)
    for _, process_id, page_id, is_write in events:
        process_traces[process_id].append((page_id, process_id, is_write))
    return {pid: list(trace) for pid, trace in process_traces.items()}


@dataclass
class ExperimentConfig:
    """Configuration for a single-process experiment."""

    name: str
    algorithm: str
    allocation_policy: str
    num_frames: int
    workload_config: WorkloadConfig
    num_trials: int = 10
    output_dir: str = "results"
    warmup_runs: int = 1
    workload_name: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "algorithm": self.algorithm,
            "allocation_policy": self.allocation_policy,
            "num_frames": self.num_frames,
            "workload_type": self.workload_config.workload_type.value,
            "workload_name": self.workload_name or self.workload_config.workload_type.value,
            "num_pages": self.workload_config.num_pages,
            "num_accesses": self.workload_config.num_accesses,
            "num_trials": self.num_trials,
            "warmup_runs": self.warmup_runs,
        }


class ExperimentRunner:
    """Runs repeated single-process simulations."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.results: Dict = {}

    def _replay_trace(self, trace: Sequence[AccessEvent]) -> Dict:
        algorithm = get_algorithm(self.config.algorithm, self.config.num_frames)
        for page_id, process_id, is_write in trace:
            algorithm.access_page(page_id, process_id, is_write)
        return algorithm.get_stats()

    def run_single_trial(self, trial_num: int = 0) -> Dict:
        workload_config = self.config.workload_config
        workload_config.seed = trial_num

        trace = WorkloadGenerator(workload_config).generate()

        for _ in range(self.config.warmup_runs):
            self._replay_trace(trace)

        stats, duration_ns = measure_once(self._replay_trace, trace)
        duration_s = duration_ns / 1_000_000_000 if duration_ns else 0.0

        stats["trial"] = trial_num
        stats["runtime_ns"] = duration_ns
        stats["runtime_ms"] = duration_ns / 1_000_000
        stats["total_accesses"] = len(trace)
        stats["page_fault_rate"] = stats["page_faults"] / len(trace) if trace else 0.0
        stats["throughput"] = (len(trace) / duration_s) if duration_s > 0 else 0.0
        stats["runtime_records"] = [
            build_runtime_record(
                mode="single",
                process_id=0,
                workload_name=self.config.workload_name
                or self.config.workload_config.workload_type.value,
                algorithm=self.config.algorithm,
                allocation_policy=self.config.allocation_policy,
                memory_frames=self.config.num_frames,
                repetition_id=trial_num,
                duration_ns=duration_ns,
                metadata={"trace_kind": "synthetic"},
            ).to_dict()
        ]
        return stats

    def run(self) -> Dict:
        print(f"Running experiment: {self.config.name}")
        print(f"  Algorithm: {self.config.algorithm}")
        print(f"  Allocation: {self.config.allocation_policy}")
        print(f"  Frames: {self.config.num_frames}")
        print(f"  Trials: {self.config.num_trials}")

        trial_results = []
        for trial in tqdm(range(self.config.num_trials), desc="Trials"):
            trial_results.append(self.run_single_trial(trial))

        aggregated = self._aggregate_results(trial_results)
        aggregated["config"] = self.config.to_dict()
        aggregated["trial_results"] = trial_results
        self.results = aggregated
        return aggregated

    def _aggregate_results(self, trial_results: List[Dict]) -> Dict:
        metrics = [
            "page_faults",
            "page_replacements",
            "disk_reads",
            "disk_writes",
            "total_disk_io",
            "page_fault_rate",
            "throughput",
            "runtime_ms",
        ]

        aggregated: Dict[str, Dict] = {}
        for metric in metrics:
            values = [float(result[metric]) for result in trial_results]
            metric_stats = _mean_std_ci(values)
            metric_stats["min"] = float(np.min(values))
            metric_stats["max"] = float(np.max(values))
            metric_stats["median"] = float(np.median(values))
            aggregated[metric] = metric_stats
        return aggregated

    def save_results(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = self.config.output_dir

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = f"{self.config.name}_{self.config.algorithm}_{self.config.allocation_policy}.json"
        filepath = Path(output_dir) / filename

        with filepath.open("w", encoding="utf-8") as handle:
            json.dump(self.results, handle, indent=2)
        print(f"Results saved to: {filepath}")


class MultiProcessExperimentRunner:
    """Runs repeated multi-process simulations for synthetic or trace-driven workloads."""

    def __init__(
        self,
        algorithm: str,
        allocation_policy: str,
        total_frames: int,
        process_workloads: Optional[Dict[int, WorkloadConfig]] = None,
        *,
        trace_events: Optional[Sequence[TraceEvent]] = None,
        trace_file: Optional[str] = None,
        trace_name: Optional[str] = None,
        workload_label: Optional[str] = None,
        interleave: str = "random",
        num_trials: int = 10,
        warmup_runs: int = 1,
        page_size: int = 4096,
    ):
        self.algorithm = algorithm
        self.allocation_policy = allocation_policy
        self.total_frames = total_frames
        self.process_workloads = process_workloads or {}
        self.trace_file = trace_file
        self.trace_name = trace_name or (Path(trace_file).stem if trace_file else "trace")
        self.workload_label = workload_label or (self.trace_name if trace_file or trace_events else "synthetic")
        self.interleave = interleave
        self.num_trials = num_trials
        self.warmup_runs = warmup_runs
        self.page_size = page_size
        self.results: Optional[Dict] = None

        if trace_events is not None:
            self.trace_events = list(trace_events)
        elif trace_file is not None:
            self.trace_events = load_trace_csv(trace_file, page_size=page_size)
        else:
            self.trace_events = []

        if not self.process_workloads and not self.trace_events:
            raise ValueError("Provide synthetic process_workloads or trace_events/trace_file")

    def _config_summary(self) -> Dict:
        """Return a serialization-friendly experiment summary."""
        return {
            "algorithm": self.algorithm,
            "allocation_policy": self.allocation_policy,
            "total_frames": self.total_frames,
            "num_trials": self.num_trials,
            "warmup_runs": self.warmup_runs,
            "interleave": self.interleave,
            "workload_kind": "trace" if self.trace_events else "synthetic",
            "workload_label": self.workload_label,
            "trace_file": self.trace_file,
            "trace_name": self.trace_name if self.trace_events else None,
            "process_count": len(self.process_workloads) if self.process_workloads else len(canonical_trace_to_process_traces(self.trace_events)),
        }

    def _prepare_synthetic_trial(
        self, trial_num: int
    ) -> tuple[List[AccessEvent], Dict[int, List[AccessEvent]], Dict[int, int], Dict[int, str]]:
        for pid, config in self.process_workloads.items():
            config.seed = trial_num + pid * 1000

        generator = MultiProcessWorkloadGenerator(self.process_workloads)
        interleaved_trace = generator.generate(interleave=self.interleave)
        process_traces = generator.last_process_traces
        working_sets = generator.estimate_aggregate_wss()
        process_names = {
            pid: config.workload_type.value for pid, config in self.process_workloads.items()
        }
        return interleaved_trace, process_traces, working_sets, process_names

    def _prepare_trace_trial(
        self,
    ) -> tuple[List[AccessEvent], Dict[int, List[AccessEvent]], Dict[int, int], Dict[int, str]]:
        process_traces = canonical_trace_to_process_traces(self.trace_events)
        interleaved_trace = canonical_trace_to_access_trace(self.trace_events)
        working_sets = {
            pid: _estimate_wss_from_trace(trace)
            for pid, trace in process_traces.items()
        }
        process_names = {pid: self.trace_name for pid in process_traces}
        return interleaved_trace, process_traces, working_sets, process_names

    def _prepare_trial(
        self, trial_num: int
    ) -> tuple[List[AccessEvent], Dict[int, List[AccessEvent]], Dict[int, int], Dict[int, str]]:
        if self.trace_events:
            return self._prepare_trace_trial()
        return self._prepare_synthetic_trial(trial_num)

    def _create_policy(self, process_ids: Sequence[int], working_sets: Dict[int, int]):
        policy = get_allocation_policy(
            self.allocation_policy,
            self.total_frames,
            self.algorithm,
        )

        if self.allocation_policy == "GlobalAllocation":
            for pid in process_ids:
                policy.add_process(pid)
            return policy

        if isinstance(policy, ProportionalAllocation):
            allocation = policy.allocate_frames_proportional(working_sets)
        else:
            allocation = policy.allocate_frames(list(process_ids))

        for pid in process_ids:
            policy.add_process(pid, allocation[pid])
        return policy

    def _replay_shared_trace(
        self,
        trace: Sequence[AccessEvent],
        working_sets: Dict[int, int],
        *,
        collect_timings: bool,
    ) -> tuple[Dict, int, Dict[int, int]]:
        process_ids = sorted({process_id for _, process_id, _ in trace})
        policy = self._create_policy(process_ids, working_sets)

        per_process_runtime_ns: Dict[int, int] = defaultdict(int)

        def run_trace() -> Dict:
            if collect_timings:
                from time import perf_counter_ns

                for page_id, process_id, is_write in trace:
                    started = perf_counter_ns()
                    policy.access_page(process_id, page_id, is_write)
                    per_process_runtime_ns[process_id] += perf_counter_ns() - started
            else:
                for page_id, process_id, is_write in trace:
                    policy.access_page(process_id, page_id, is_write)
            return policy.get_all_stats()

        stats, duration_ns = measure_once(run_trace)
        return stats, duration_ns, dict(per_process_runtime_ns)

    def _measure_isolated_replay(
        self,
        process_id: int,
        trace: Sequence[AccessEvent],
    ) -> tuple[Dict, int]:
        def run_isolated() -> Dict:
            algorithm = get_algorithm(self.algorithm, self.total_frames)
            for page_id, _, is_write in trace:
                algorithm.access_page(page_id, process_id, is_write)
            return algorithm.get_stats()

        for _ in range(self.warmup_runs):
            run_isolated()

        stats, duration_ns = measure_once(run_isolated)
        return stats, duration_ns

    def run_single_trial(self, trial_num: int = 0) -> Dict:
        trace, process_traces, working_sets, process_names = self._prepare_trial(trial_num)
        access_counts = {pid: len(proc_trace) for pid, proc_trace in process_traces.items()}

        for _ in range(self.warmup_runs):
            self._replay_shared_trace(trace, working_sets, collect_timings=False)

        stats, duration_ns, per_process_runtime_ns = self._replay_shared_trace(
            trace,
            working_sets,
            collect_timings=True,
        )
        duration_s = duration_ns / 1_000_000_000 if duration_ns else 0.0

        stats["trial"] = trial_num
        stats["runtime_ns"] = duration_ns
        stats["runtime_ms"] = duration_ns / 1_000_000
        stats["total_accesses"] = len(trace)
        stats["throughput"] = (len(trace) / duration_s) if duration_s > 0 else 0.0

        runtime_records = [
            build_runtime_record(
                mode="shared_total",
                process_id=None,
                workload_name=self.workload_label,
                algorithm=self.algorithm,
                allocation_policy=self.allocation_policy,
                memory_frames=self.total_frames,
                repetition_id=trial_num,
                duration_ns=duration_ns,
                metadata={"interleave": self.interleave},
            ).to_dict()
        ]

        slowdowns = []
        for pid, proc_stats in stats["per_process"].items():
            accesses = access_counts.get(pid, 0)
            page_faults = proc_stats.get("page_faults", 0)
            proc_stats["accesses"] = accesses
            proc_stats["page_fault_rate"] = (page_faults / accesses) if accesses else 0.0

            isolated_stats, isolated_duration_ns = self._measure_isolated_replay(pid, process_traces[pid])
            shared_duration_ns = per_process_runtime_ns.get(pid, 0)

            proc_stats["isolated_page_faults"] = isolated_stats["page_faults"]
            proc_stats["isolated_runtime_ns"] = isolated_duration_ns
            proc_stats["isolated_runtime_ms"] = isolated_duration_ns / 1_000_000
            proc_stats["shared_runtime_ns"] = shared_duration_ns
            proc_stats["shared_runtime_ms"] = shared_duration_ns / 1_000_000
            proc_stats["slowdown"] = (
                shared_duration_ns / isolated_duration_ns if isolated_duration_ns else 1.0
            )
            slowdowns.append(proc_stats["slowdown"])

            workload_name = process_names.get(pid, str(pid))
            runtime_records.append(
                build_runtime_record(
                    mode="shared",
                    process_id=pid,
                    workload_name=workload_name,
                    algorithm=self.algorithm,
                    allocation_policy=self.allocation_policy,
                    memory_frames=self.total_frames,
                    repetition_id=trial_num,
                    duration_ns=shared_duration_ns,
                    metadata={"interleave": self.interleave},
                ).to_dict()
            )
            runtime_records.append(
                build_runtime_record(
                    mode="isolation",
                    process_id=pid,
                    workload_name=workload_name,
                    algorithm=self.algorithm,
                    allocation_policy=self.allocation_policy,
                    memory_frames=self.total_frames,
                    repetition_id=trial_num,
                    duration_ns=isolated_duration_ns,
                    metadata={"trace_kind": "trace" if self.trace_events else "synthetic"},
                ).to_dict()
            )

        stats["working_set_sizes"] = working_sets
        stats["aggregate_wss"] = sum(working_sets.values())
        stats["memory_ratio_to_wss"] = (
            self.total_frames / stats["aggregate_wss"] if stats["aggregate_wss"] else None
        )
        stats["worst_case_slowdown"] = max(slowdowns) if slowdowns else 0.0
        stats["mean_slowdown"] = float(np.mean(slowdowns)) if slowdowns else 0.0
        stats["fairness_metrics"] = calculate_fairness_metrics(stats["per_process"])
        stats["runtime_records"] = runtime_records
        stats["workload_kind"] = "trace" if self.trace_events else "synthetic"
        stats["workload_label"] = self.workload_label
        stats["trace_name"] = self.trace_name if self.trace_events else None
        return stats

    def run(self) -> Dict:
        print("Running multi-process experiment")
        print(f"  Algorithm: {self.algorithm}")
        print(f"  Allocation: {self.allocation_policy}")
        print(f"  Total Frames: {self.total_frames}")
        if self.trace_events:
            print(f"  Trace: {self.trace_name}")
        else:
            print(f"  Processes: {list(self.process_workloads.keys())}")

        trial_results = []
        for trial in tqdm(range(self.num_trials), desc="Trials"):
            trial_results.append(self.run_single_trial(trial))

        aggregated = self._aggregate_multi_process_results(trial_results)
        aggregated["config"] = self._config_summary()
        aggregated["trial_results"] = trial_results
        self.results = aggregated
        return aggregated

    def _aggregate_multi_process_results(self, trial_results: List[Dict]) -> Dict:
        aggregated = {
            "system": {},
            "per_process": {},
        }

        system_metrics = [
            "page_faults",
            "page_replacements",
            "disk_reads",
            "disk_writes",
            "total_disk_io",
            "throughput",
            "runtime_ms",
            "worst_case_slowdown",
            "mean_slowdown",
        ]

        for metric in system_metrics:
            if metric in {"throughput", "runtime_ms", "worst_case_slowdown", "mean_slowdown"}:
                values = [float(result[metric]) for result in trial_results]
            else:
                values = [float(result["system_total"][metric]) for result in trial_results]
            aggregated["system"][metric] = _mean_std_ci(values)

        process_ids = list(trial_results[0]["per_process"].keys())
        for pid in process_ids:
            aggregated["per_process"][pid] = {}
            for metric in [
                "accesses",
                "page_faults",
                "page_fault_rate",
                "shared_runtime_ms",
                "isolated_runtime_ms",
                "slowdown",
            ]:
                values = [float(result["per_process"][pid].get(metric, 0.0)) for result in trial_results]
                aggregated["per_process"][pid][metric] = _mean_std_ci(values)

        fairness_trials = [result.get("fairness_metrics", {}) for result in trial_results]
        aggregated["fairness_metrics"] = {}
        for metric in ["jains_index", "variance", "cv", "max_ratio", "mean", "std", "min", "max"]:
            values = [float(metrics[metric]) for metrics in fairness_trials if metric in metrics]
            if values:
                aggregated["fairness_metrics"][metric] = _mean_std_ci(values)

        if fairness_trials:
            bases = [metrics.get("basis") for metrics in fairness_trials if metrics.get("basis")]
            if bases:
                aggregated["fairness_metrics"]["basis"] = bases[0]

        aggregate_wss_values = [float(result["aggregate_wss"]) for result in trial_results]
        aggregated["aggregate_wss"] = _mean_std_ci(aggregate_wss_values)

        ratio_values = [
            float(result["memory_ratio_to_wss"])
            for result in trial_results
            if result["memory_ratio_to_wss"] is not None
        ]
        aggregated["memory_ratio_to_wss"] = _mean_std_ci(ratio_values) if ratio_values else {}
        aggregated["workload_kind"] = trial_results[0].get("workload_kind", "synthetic")
        aggregated["workload_label"] = trial_results[0].get("workload_label")
        aggregated["trace_name"] = trial_results[0].get("trace_name")
        return aggregated

    def save_results(self, output_dir: str = "results"):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        if self.trace_events:
            filename = (
                f"trace_{self.trace_name}_{self.algorithm}_{self.allocation_policy}"
                f"_f{self.total_frames}.json"
            )
        else:
            filename = (
                f"multiproc_{self.workload_label}_{self.algorithm}_{self.allocation_policy}"
                f"_p{self._config_summary()['process_count']}_f{self.total_frames}.json"
            )
        filepath = Path(output_dir) / filename

        with filepath.open("w", encoding="utf-8") as handle:
            json.dump(self.results, handle, indent=2)
        print(f"Results saved to: {filepath}")


def run_experiment_suite(configs: Iterable[ExperimentConfig], output_dir: str = "results") -> List[Dict]:
    """Run a list of single-process experiment configs."""
    all_results = []
    for config in configs:
        runner = ExperimentRunner(config)
        results = runner.run()
        runner.save_results(output_dir)
        all_results.append(results)
    return all_results
