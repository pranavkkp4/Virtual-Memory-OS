"""Helpers for measuring wall-clock runtime in repeatable experiment runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean, median
from time import perf_counter_ns, sleep
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional


@dataclass(slots=True)
class RuntimeRecord:
    """Serialization-friendly record for a single runtime observation."""

    mode: str
    process_id: Optional[int]
    workload_name: str
    algorithm: str
    allocation_policy: str
    memory_frames: Optional[int]
    repetition_id: int
    duration_ns: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a JSON-serializable dictionary."""
        data = asdict(self)
        data["duration_ms"] = self.duration_ns / 1_000_000
        return data


@dataclass(slots=True)
class RuntimeSummary:
    """Aggregate timing statistics for repeated measurements."""

    label: str
    warmup_runs: int
    measured_runs: int
    durations_ns: List[int]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def median_ns(self) -> int:
        return int(median(self.durations_ns)) if self.durations_ns else 0

    @property
    def mean_ns(self) -> float:
        return float(mean(self.durations_ns)) if self.durations_ns else 0.0

    @property
    def min_ns(self) -> int:
        return min(self.durations_ns) if self.durations_ns else 0

    @property
    def max_ns(self) -> int:
        return max(self.durations_ns) if self.durations_ns else 0

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable summary payload."""
        return {
            "label": self.label,
            "warmup_runs": self.warmup_runs,
            "measured_runs": self.measured_runs,
            "durations_ns": list(self.durations_ns),
            "median_ns": self.median_ns,
            "mean_ns": self.mean_ns,
            "min_ns": self.min_ns,
            "max_ns": self.max_ns,
            "metadata": dict(self.metadata),
            "durations_ms": [duration / 1_000_000 for duration in self.durations_ns],
            "median_ms": self.median_ns / 1_000_000,
            "mean_ms": self.mean_ns / 1_000_000 if self.durations_ns else 0.0,
        }


def measure_once(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, int]:
    """Measure a single wall-clock call using perf_counter_ns."""
    started = perf_counter_ns()
    result = func(*args, **kwargs)
    elapsed = perf_counter_ns() - started
    return result, elapsed


def measure_repeated(
    func: Callable[..., Any],
    *args: Any,
    repeats: int = 10,
    warmup_runs: int = 1,
    label: str = "runtime",
    metadata: Optional[Mapping[str, Any]] = None,
    repeat_delay_s: float = 0.0,
    **kwargs: Any,
) -> RuntimeSummary:
    """
    Measure a callable repeatedly, discarding warmup runs.

    The return value of `func` is ignored after each run; this helper focuses on
    the timing distribution only.
    """
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if warmup_runs < 0:
        raise ValueError("warmup_runs cannot be negative")

    for _ in range(warmup_runs):
        func(*args, **kwargs)
        if repeat_delay_s > 0:
            sleep(repeat_delay_s)

    durations_ns: List[int] = []
    for _ in range(repeats):
        _, elapsed = measure_once(func, *args, **kwargs)
        durations_ns.append(elapsed)
        if repeat_delay_s > 0:
            sleep(repeat_delay_s)

    return RuntimeSummary(
        label=label,
        warmup_runs=warmup_runs,
        measured_runs=repeats,
        durations_ns=durations_ns,
        metadata=dict(metadata or {}),
    )


def build_runtime_record(
    *,
    mode: str,
    process_id: Optional[int],
    workload_name: str,
    algorithm: str,
    allocation_policy: str,
    memory_frames: Optional[int],
    repetition_id: int,
    duration_ns: int,
    metadata: Optional[Mapping[str, Any]] = None,
) -> RuntimeRecord:
    """Create a canonical runtime log record."""
    return RuntimeRecord(
        mode=mode,
        process_id=process_id,
        workload_name=workload_name,
        algorithm=algorithm,
        allocation_policy=allocation_policy,
        memory_frames=memory_frames,
        repetition_id=repetition_id,
        duration_ns=duration_ns,
        metadata=dict(metadata or {}),
    )


def summarize_records(records: Iterable[RuntimeRecord]) -> Dict[str, Any]:
    """Summarize a list of runtime records in a serialization-friendly form."""
    records_list = list(records)
    durations_ns = [record.duration_ns for record in records_list]
    if not durations_ns:
        return {
            "count": 0,
            "median_ns": 0,
            "mean_ns": 0.0,
            "min_ns": 0,
            "max_ns": 0,
            "records": [],
        }

    return {
        "count": len(records_list),
        "median_ns": int(median(durations_ns)),
        "mean_ns": float(mean(durations_ns)),
        "min_ns": min(durations_ns),
        "max_ns": max(durations_ns),
        "records": [record.to_dict() for record in records_list],
    }
