#!/usr/bin/env python3
"""Validate benchmark result bundles and emit a structured audit report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

ALGORITHMS = ["FIFO", "LRU", "NRU", "SecondChance", "WSClock"]
ALLOCATIONS = ["GlobalAllocation", "LocalAllocation", "ProportionalAllocation"]
DEFAULT_CANONICAL_SOURCE = Path("results/raw/campaign_20260404_140330_266")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _as_float(value: Any) -> Optional[float]:
    if _is_number(value):
        return float(value)
    if isinstance(value, dict):
        for key in ("mean", "value"):
            inner = value.get(key)
            if _is_number(inner):
                return float(inner)
    return None


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Optional[dict]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _find_known_suffix(body: str) -> Optional[Tuple[str, str, str]]:
    for allocation in ALLOCATIONS:
        alloc_suffix = f"_{allocation}"
        if not body.endswith(alloc_suffix):
            continue
        before_alloc = body[: -len(alloc_suffix)]
        for algorithm in ALGORITHMS:
            algo_suffix = f"_{algorithm}"
            if before_alloc.endswith(algo_suffix):
                prefix = before_alloc[: -len(algo_suffix)]
                return prefix, algorithm, allocation
    return None


def infer_config_from_name(path: Path) -> Dict[str, Any]:
    """Infer a best-effort configuration from a benchmark filename."""
    stem = path.stem
    inferred: Dict[str, Any] = {
        "source_file": str(path),
        "source_stem": stem,
    }

    for prefix, workload_kind in (("trace_", "trace"), ("multiproc_", "synthetic"), ("single_", "single")):
        if not stem.startswith(prefix):
            continue

        remainder = stem[len(prefix) :]
        frames_match = re.search(r"_f(?P<frames>\d+)$", remainder)
        process_match = re.search(r"_p(?P<processes>\d+)(?:_f\d+)?$", remainder)
        if frames_match:
            inferred["total_frames"] = int(frames_match.group("frames"))
            remainder = remainder[: frames_match.start()]
        if process_match:
            inferred["process_count"] = int(process_match.group("processes"))
            remainder = remainder[: process_match.start()]

        known = _find_known_suffix(remainder)
        if known:
            prefix_value, algorithm, allocation = known
            inferred["algorithm"] = algorithm
            inferred["allocation_policy"] = allocation
            if workload_kind == "trace":
                inferred["trace_name"] = prefix_value
                inferred["workload_label"] = "trace"
            elif prefix_value:
                inferred["workload_label"] = prefix_value
            else:
                inferred["workload_label"] = "synthetic"
            inferred["workload_kind"] = workload_kind
        else:
            inferred["workload_kind"] = workload_kind
        return inferred

    return inferred


def infer_total_frames(payload: Dict[str, Any], config: Dict[str, Any]) -> Optional[int]:
    for key in ("total_frames", "num_frames"):
        value = _as_int(config.get(key)) if key in config else None
        if value is not None:
            return value

    filename_value = _as_int(config.get("total_frames"))
    if filename_value is not None:
        return filename_value

    ratio = _as_float(payload.get("memory_ratio_to_wss"))
    wss = _as_float(payload.get("aggregate_wss"))
    if ratio is None or wss is None:
        return None
    frames = int(round(ratio * wss))
    return frames if frames > 0 else None


def infer_process_count(payload: Dict[str, Any], config: Dict[str, Any]) -> Optional[int]:
    value = _as_int(config.get("process_count"))
    if value is not None:
        return value
    trial_results = payload.get("trial_results")
    if isinstance(trial_results, list) and trial_results:
        first = trial_results[0]
        per_process = first.get("per_process")
        if isinstance(per_process, dict) and per_process:
            return len(per_process)
    per_process = payload.get("per_process")
    if isinstance(per_process, dict) and per_process:
        return len(per_process)
    return None


def infer_workload_fields(payload: Dict[str, Any], config: Dict[str, Any], path: Path) -> Dict[str, Any]:
    inferred = infer_config_from_name(path)
    merged: Dict[str, Any] = dict(inferred)
    merged.update({k: v for k, v in config.items() if v not in (None, "")})

    if "workload_kind" not in merged:
        merged["workload_kind"] = "trace" if merged.get("trace_file") or path.stem.startswith("trace_") else "synthetic"
    if "workload_label" not in merged:
        merged["workload_label"] = payload.get("workload_label") or merged.get("trace_name") or merged["workload_kind"]

    total_frames = infer_total_frames(payload, merged)
    if total_frames is not None:
        merged["total_frames"] = total_frames

    process_count = infer_process_count(payload, merged)
    if process_count is not None:
        merged["process_count"] = process_count

    if "trace_name" not in merged and path.stem.startswith("trace_"):
        remainder = path.stem[len("trace_") :]
        known = _find_known_suffix(remainder)
        if known:
            prefix_value, _, _ = known
            merged["trace_name"] = prefix_value

    return merged


def _normalize_runtime_field(value: Any) -> Optional[float]:
    if _is_number(value):
        return float(value)
    if isinstance(value, dict):
        for key in ("mean", "value"):
            nested = value.get(key)
            if _is_number(nested):
                return float(nested)
    return None


def _count_runtime_modes(runtime_records: Any) -> Dict[str, int]:
    counts = {"shared": 0, "isolation": 0, "shared_total": 0, "single": 0}
    if not isinstance(runtime_records, list):
        return counts
    for record in runtime_records:
        if not isinstance(record, dict):
            continue
        mode = record.get("mode")
        if mode in counts:
            counts[mode] += 1
    return counts


def _trial_process_ids(per_process: Any) -> List[int]:
    if not isinstance(per_process, dict):
        return []
    process_ids: List[int] = []
    for key in per_process:
        pid = _as_int(key)
        if pid is not None:
            process_ids.append(pid)
    return sorted(process_ids)


def _trial_metric_value(trial: Dict[str, Any], key: str) -> Optional[float]:
    if key in trial:
        return _as_float(trial.get(key))
    if key == "runtime_ms" and _is_number(trial.get("simulation_time")):
        return float(trial["simulation_time"]) * 1000.0
    if key == "page_faults" and isinstance(trial.get("system_total"), dict):
        return _as_float(trial["system_total"].get("page_faults"))
    return None


def _extract_trial_summary(trial: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    system_total = trial.get("system_total") if isinstance(trial.get("system_total"), dict) else {}
    per_process = trial.get("per_process") if isinstance(trial.get("per_process"), dict) else {}

    summary["trial"] = trial.get("trial")
    summary["runtime_ms"] = _trial_metric_value(trial, "runtime_ms")
    summary["throughput"] = _trial_metric_value(trial, "throughput")
    summary["total_accesses"] = _as_float(trial.get("total_accesses"))
    summary["page_faults"] = _as_float(system_total.get("page_faults"))
    summary["page_replacements"] = _as_float(system_total.get("page_replacements"))
    summary["disk_reads"] = _as_float(system_total.get("disk_reads"))
    summary["disk_writes"] = _as_float(system_total.get("disk_writes"))
    summary["total_disk_io"] = _as_float(system_total.get("total_disk_io"))
    summary["worst_case_slowdown"] = _trial_metric_value(trial, "worst_case_slowdown")
    summary["mean_slowdown"] = _trial_metric_value(trial, "mean_slowdown")
    summary["aggregate_wss"] = _as_float(trial.get("aggregate_wss"))
    summary["memory_ratio_to_wss"] = _as_float(trial.get("memory_ratio_to_wss"))
    summary["per_process_count"] = len(per_process)

    fairness = trial.get("fairness_metrics") if isinstance(trial.get("fairness_metrics"), dict) else {}
    for metric in ("jains_index", "variance", "cv", "max_ratio", "mean", "std", "min", "max"):
        summary[f"fairness_{metric}"] = _as_float(fairness.get(metric))

    slowdown_values: List[float] = []
    shared_missing = 0
    isolated_missing = 0
    malformed_processes = 0
    for pid, metrics in per_process.items():
        if not isinstance(metrics, dict):
            malformed_processes += 1
            continue
        slowdown = _as_float(metrics.get("slowdown"))
        if slowdown is not None:
            slowdown_values.append(slowdown)
        if _normalize_runtime_field(metrics.get("shared_runtime_ms")) is None and _normalize_runtime_field(metrics.get("shared_runtime")) is None:
            shared_missing += 1
        if _normalize_runtime_field(metrics.get("isolated_runtime_ms")) is None and _normalize_runtime_field(metrics.get("isolated_runtime")) is None:
            isolated_missing += 1
    summary["per_process_slowdowns"] = slowdown_values
    summary["shared_missing"] = shared_missing
    summary["isolated_missing"] = isolated_missing
    summary["malformed_processes"] = malformed_processes
    summary["runtime_record_modes"] = _count_runtime_modes(trial.get("runtime_records"))

    return summary


def _ci95(values: Sequence[float]) -> Tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        value = float(values[0])
        return (value, value)
    mean_value = statistics.mean(values)
    std_value = statistics.pstdev(values)
    radius = 1.96 * std_value / math.sqrt(len(values))
    return (float(mean_value - radius), float(mean_value + radius))


def summarize_values(values: Sequence[float]) -> Dict[str, Any]:
    clean = [float(value) for value in values if _is_number(value)]
    if not clean:
        return {
            "count": 0,
            "sum": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    mean_value = statistics.mean(clean)
    return {
        "count": len(clean),
        "sum": float(sum(clean)),
        "mean": float(mean_value),
        "median": float(statistics.median(clean)),
        "std": float(statistics.pstdev(clean)) if len(clean) > 1 else 0.0,
        "ci_low": _ci95(clean)[0],
        "ci_high": _ci95(clean)[1],
        "min": float(min(clean)),
        "max": float(max(clean)),
    }


def _robust_outlier_indices(values: Sequence[float]) -> List[int]:
    clean = [float(value) for value in values if _is_number(value)]
    if len(clean) < 4:
        return []

    median_value = statistics.median(clean)
    deviations = [abs(value - median_value) for value in clean]
    mad = statistics.median(deviations)
    if mad > 0:
        threshold = 3.5 * 1.4826 * mad
        return [index for index, value in enumerate(clean) if abs(value - median_value) > threshold]

    sorted_values = sorted(clean)
    q1 = statistics.median(sorted_values[: len(sorted_values) // 2])
    q3 = statistics.median(sorted_values[(len(sorted_values) + 1) // 2 :])
    iqr = q3 - q1
    if iqr <= 0:
        return []
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [index for index, value in enumerate(clean) if value < lower or value > upper]


def _payload_kind(payload: Dict[str, Any]) -> str:
    if "trial_results" in payload or "system" in payload:
        return "benchmark"
    if "timestamp" in payload and "command" in payload:
        return "metadata"
    return "unknown"


def _is_demo_like_source(path: Path, payload: Dict[str, Any], config: Dict[str, Any]) -> bool:
    source_text = str(path).lower().replace("/", "\\")
    trace_name = str(config.get("trace_name") or payload.get("trace_name") or "").strip().lower()
    if trace_name.startswith("demo"):
        return True
    if "tests\\" in source_text or "\\tests\\" in source_text:
        return True
    if "pilot_" in source_text or "\\pilot_" in source_text:
        return True
    if "demo_bundle_smoke" in source_text or "\\demo\\" in source_text:
        return True
    return False


def _file_stem_key(path: Path) -> str:
    return path.stem.lower()


@dataclass
class ValidatedSource:
    path: Path
    digest: str
    payload: Dict[str, Any]
    config: Dict[str, Any]
    kind: str
    issues: List[str] = field(default_factory=list)
    trial_summaries: List[Dict[str, Any]] = field(default_factory=list)
    is_duplicate_digest: bool = False

    @property
    def config_key(self) -> Tuple[Any, ...]:
        return (
            self.config.get("workload_kind"),
            self.config.get("workload_label"),
            self.config.get("trace_name"),
            self.config.get("algorithm"),
            self.config.get("allocation_policy"),
            self.config.get("total_frames"),
            self.config.get("process_count"),
        )

    @property
    def is_benchmark(self) -> bool:
        return self.kind == "benchmark"


def _validate_trial(trial: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    summary = _extract_trial_summary(trial)
    per_process = trial.get("per_process") if isinstance(trial.get("per_process"), dict) else {}

    if not per_process:
        issues.append("missing_per_process_metrics")
        return issues, summary

    process_ids = _trial_process_ids(per_process)
    expected_total = summary.get("total_accesses")
    if expected_total is not None:
        access_total = 0.0
        fault_total = 0.0
        for pid, metrics in per_process.items():
            if not isinstance(metrics, dict):
                continue
            access_value = _as_float(metrics.get("accesses"))
            fault_value = _as_float(metrics.get("page_faults"))
            if access_value is not None:
                access_total += access_value
            if fault_value is not None:
                fault_total += fault_value
        if abs(access_total - float(expected_total)) > 0.01:
            issues.append("access_total_mismatch")
        if summary.get("page_faults") is not None and abs(fault_total - float(summary["page_faults"])) > 0.01:
            issues.append("page_fault_total_mismatch")

    runtime_modes = summary["runtime_record_modes"]
    if runtime_modes["shared"] != len(process_ids):
        issues.append("missing_shared_runtime_records")
    if runtime_modes["isolation"] != len(process_ids):
        issues.append("missing_isolation_runtime_records")
    if process_ids and runtime_modes["shared_total"] == 0:
        issues.append("missing_shared_total_runtime_record")

    for pid, metrics in per_process.items():
        if not isinstance(metrics, dict):
            issues.append(f"malformed_process_{pid}")
            continue
        if _as_float(metrics.get("slowdown")) is None:
            issues.append(f"missing_slowdown_process_{pid}")
        if _normalize_runtime_field(metrics.get("shared_runtime_ms")) is None and _normalize_runtime_field(metrics.get("shared_runtime")) is None:
            issues.append(f"missing_shared_runtime_process_{pid}")
        if _normalize_runtime_field(metrics.get("isolated_runtime_ms")) is None and _normalize_runtime_field(metrics.get("isolated_runtime")) is None:
            issues.append(f"missing_isolated_runtime_process_{pid}")

    workload_kind = config.get("workload_kind")
    if workload_kind == "trace" or str(config.get("trace_file") or "").lower().endswith(".csv"):
        if not config.get("trace_name"):
            issues.append("missing_trace_name")
        if not config.get("trace_file"):
            issues.append("missing_trace_file")
        if config.get("interleave") not in (None, "trace-order"):
            issues.append("unexpected_trace_interleave")
        if not runtime_modes["shared_total"]:
            issues.append("malformed_trace_runtime_records")

    if not trial.get("fairness_metrics"):
        issues.append("empty_trial_fairness_metrics")

    return issues, summary


def _has_hypothesis_data(
    source: ValidatedSource,
    *,
    workload_label: str,
    algorithm: str,
    allocation_policy: str,
    process_count: int,
    target_ratio: Optional[float] = None,
    tolerance: float = 0.25,
) -> bool:
    config = source.config
    if config.get("workload_label") != workload_label:
        return False
    if config.get("algorithm") != algorithm:
        return False
    if config.get("allocation_policy") != allocation_policy:
        return False
    if _as_int(config.get("process_count")) != process_count:
        return False
    ratio = _as_float(source.payload.get("memory_ratio_to_wss"))
    if ratio is None:
        return False
    if target_ratio is None:
        return True
    return abs(ratio - target_ratio) <= tolerance


def load_sources(paths: Sequence[Path]) -> List[ValidatedSource]:
    sources: List[ValidatedSource] = []
    for path in paths:
        payload = _load_json(path)
        if payload is None:
            continue
        kind = _payload_kind(payload)
        if kind != "benchmark":
            continue
        config = infer_workload_fields(payload, payload.get("config", {}) if isinstance(payload.get("config"), dict) else {}, path)
        if _is_demo_like_source(path, payload, config):
            continue
        sources.append(
            ValidatedSource(
                path=path,
                digest=_sha256(path),
                payload=payload,
                config=config,
                kind=kind,
            )
        )
    return sources


def discover_candidate_files(roots: Sequence[Path]) -> List[Path]:
    candidates: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if "processed" in {part.lower() for part in path.parts}:
                continue
            candidates.append(path)
    return sorted(candidates)


def scan_wrapper_logs(roots: Sequence[Path]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for metadata_dir in root.rglob("metadata"):
            if not metadata_dir.is_dir():
                continue
            for env_path in metadata_dir.glob("run_environment_*.json"):
                payload = _load_json(env_path)
                if not isinstance(payload, dict):
                    continue
                command = payload.get("command")
                benchmark_args = payload.get("benchmark_args")
                command_text = " ".join(map(str, command)) if isinstance(command, list) else ""
                args_text = " ".join(map(str, benchmark_args)) if isinstance(benchmark_args, list) else ""
                is_help_run = "--help" in command_text or "--help" in args_text or " -h" in command_text or " -h" in args_text

                stem = env_path.stem.replace("run_environment_", "run_output_")
                log_path = metadata_dir / f"{stem}.log"
                stdout_path = metadata_dir / f"{stem}.stdout.log"
                stderr_path = metadata_dir / f"{stem}.stderr.log"

                stderr_text = stderr_path.read_text(encoding="utf-8", errors="ignore") if stderr_path.exists() else ""
                log_text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
                stdout_text = stdout_path.read_text(encoding="utf-8", errors="ignore") if stdout_path.exists() else ""

                status = "ok"
                details: List[str] = []
                if not is_help_run:
                    if stderr_text.strip():
                        status = "failed"
                        details.append("stderr_not_empty")
                    if "Traceback" in log_text or "Traceback" in stdout_text or "Traceback" in stderr_text:
                        status = "failed"
                        details.append("traceback_detected")
                    if "Benchmark run failed" in log_text or "Benchmark run failed" in stdout_text:
                        status = "failed"
                        details.append("wrapper_failure_message")
                    if not log_text.strip():
                        status = "warning"
                        details.append("missing_output_log")
                rows.append(
                    {
                        "metadata_file": str(env_path),
                        "mode": payload.get("mode"),
                        "command": command_text,
                        "status": status,
                        "details": "; ".join(details),
                    }
                )
    return rows


def validate_sources(
    sources: Sequence[ValidatedSource],
    *,
    wrapper_roots: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    digest_map: Dict[str, ValidatedSource] = {}
    config_groups: Dict[Tuple[Any, ...], List[ValidatedSource]] = {}
    issue_rows: List[Dict[str, Any]] = []
    valid_sources: List[ValidatedSource] = []

    for source in sources:
        if source.digest in digest_map:
            source.is_duplicate_digest = True
            source.issues.append("duplicate_file_digest")
        else:
            digest_map[source.digest] = source
            valid_sources.append(source)

        config_groups.setdefault(source.config_key, []).append(source)

        trials = source.payload.get("trial_results")
        if not isinstance(trials, list) or not trials:
            source.issues.append("missing_trial_results")
            continue

        for trial_index, trial in enumerate(trials):
            if not isinstance(trial, dict):
                source.issues.append(f"malformed_trial_{trial_index}")
                continue
            trial_issues, trial_summary = _validate_trial(trial, source.config)
            source.trial_summaries.append(trial_summary)
            for issue in trial_issues:
                source.issues.append(issue)
                issue_rows.append(
                    {
                        "source_file": str(source.path),
                        "trial": trial.get("trial", trial_index),
                        "issue": issue,
                    }
                )

        runtime_ms_values = [summary["runtime_ms"] for summary in source.trial_summaries if summary.get("runtime_ms") is not None]
        if runtime_ms_values:
            for index in _robust_outlier_indices(runtime_ms_values):
                source.issues.append(f"host_noise_outlier_trial_{index}")
                issue_rows.append(
                    {
                        "source_file": str(source.path),
                        "trial": source.trial_summaries[index].get("trial", index),
                        "issue": "host_noise_outlier",
                    }
                )

    duplicate_configs = {
        " | ".join("" if part is None else str(part) for part in key): [str(item.path) for item in group]
        for key, group in config_groups.items()
        if len(group) > 1
    }

    h1_ready = any(
        _has_hypothesis_data(
            source,
            workload_label="high_locality",
            algorithm="LRU",
            allocation_policy="GlobalAllocation",
            process_count=4,
            target_ratio=1.2,
        )
        for source in valid_sources
    ) and any(
        _has_hypothesis_data(
            source,
            workload_label="high_locality",
            algorithm="LRU",
            allocation_policy="LocalAllocation",
            process_count=4,
            target_ratio=1.2,
        )
        for source in valid_sources
    )
    h2_ready = any(
        _has_hypothesis_data(
            source,
            workload_label="high_locality",
            algorithm="LRU",
            allocation_policy="GlobalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        for source in valid_sources
    ) and any(
        _has_hypothesis_data(
            source,
            workload_label="high_locality",
            algorithm="LRU",
            allocation_policy="LocalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        for source in valid_sources
    )
    h3_ready = any(
        _has_hypothesis_data(
            source,
            workload_label="mixed",
            algorithm=algorithm,
            allocation_policy="LocalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        for source in valid_sources
        for algorithm in ("FIFO", "NRU")
    ) and any(
        _has_hypothesis_data(
            source,
            workload_label="mixed",
            algorithm=algorithm,
            allocation_policy="GlobalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        for source in valid_sources
        for algorithm in ("LRU", "WSClock")
    )
    empty_hypothesis = not (h1_ready or h2_ready or h3_ready)

    summary = {
        "source_count": len(sources),
        "valid_source_count": len(valid_sources),
        "duplicate_file_count": sum(1 for source in sources if source.is_duplicate_digest),
        "duplicate_config_count": len(duplicate_configs),
        "duplicate_configs": duplicate_configs,
        "issue_count": len(issue_rows),
        "issue_rows": issue_rows,
        "wrapper_runs": scan_wrapper_logs(list(wrapper_roots) if wrapper_roots is not None else [Path("results")]),
        "empty_hypothesis_evaluations": empty_hypothesis,
        "sources": [
            {
                "source_file": str(source.path),
                "digest": source.digest,
                "kind": source.kind,
                "config": source.config,
                "issues": source.issues,
                "is_duplicate_digest": source.is_duplicate_digest,
                "trial_count": len(source.trial_summaries),
            }
            for source in sources
        ],
    }
    summary["wrapper_failure_count"] = sum(1 for row in summary["wrapper_runs"] if row["status"] == "failed")
    summary["wrapper_warning_count"] = sum(1 for row in summary["wrapper_runs"] if row["status"] == "warning")
    summary["wrapper_help_runs"] = sum(1 for row in summary["wrapper_runs"] if "--help" in row.get("command", ""))
    return summary


def write_validation_outputs(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    issue_rows = report.get("issue_rows", [])
    if issue_rows:
        with (output_dir / "validation_issues.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source_file", "trial", "issue"])
            writer.writeheader()
            writer.writerows(issue_rows)

    source_rows = report.get("sources", [])
    if source_rows:
        with (output_dir / "validation_sources.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["source_file", "kind", "trial_count", "is_duplicate_digest", "issues"],
            )
            writer.writeheader()
            for row in source_rows:
                writer.writerow(
                    {
                        "source_file": row["source_file"],
                        "kind": row["kind"],
                        "trial_count": row["trial_count"],
                        "is_duplicate_digest": row["is_duplicate_digest"],
                        "issues": "; ".join(row["issues"]),
                    }
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate benchmark result bundles.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Root directory to scan for benchmark JSON files. May be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/processed",
        help="Directory to write validation outputs.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also scan the tests/ tree. Disabled by default so canonical validation stays clean.",
    )
    args = parser.parse_args()

    sources = [Path(item) for item in args.source] if args.source else [DEFAULT_CANONICAL_SOURCE]
    if args.include_tests and Path("tests") not in sources:
        sources.append(Path("tests"))
    candidates = discover_candidate_files(sources)
    validated_sources = load_sources(candidates)
    wrapper_roots = [Path("results")]
    if args.include_tests:
        wrapper_roots.append(Path("tests"))
    report = validate_sources(validated_sources, wrapper_roots=wrapper_roots)
    write_validation_outputs(report, Path(args.output_dir))

    print(f"Validated {report['valid_source_count']} benchmark files.")
    print(f"Duplicate configs: {report['duplicate_config_count']}")
    print(f"Wrapper failures: {report['wrapper_failure_count']}")
    print(f"Validation report: {Path(args.output_dir) / 'validation_report.json'}")


if __name__ == "__main__":
    main()
