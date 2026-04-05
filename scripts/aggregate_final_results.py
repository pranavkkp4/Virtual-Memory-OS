#!/usr/bin/env python3
"""Aggregate validated benchmark outputs into submission-ready processed tables."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hypothesis_evaluator import evaluation_table, evaluate_h1, evaluate_h2, evaluate_h3  # noqa: E402

from validate_results import (  # noqa: E402
    ValidatedSource,
    discover_candidate_files,
    load_sources,
    summarize_values,
    validate_sources,
    write_validation_outputs,
)

DEFAULT_CANONICAL_SOURCE = Path("results/raw/campaign_20260404_140330_266")


def _numeric_mean(value: Any) -> Optional[float]:
    if isinstance(value, dict):
        candidate = value.get("mean")
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            return float(candidate)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def result_mean(result: Dict[str, Any], *path: str) -> Optional[float]:
    current: Any = result
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return _numeric_mean(current)


def result_config(result: Dict[str, Any]) -> Dict[str, Any]:
    config = result.get("config")
    return config if isinstance(config, dict) else {}


def _flatten_summary(prefix: str, stats: Dict[str, Any]) -> Dict[str, Any]:
    return {
        f"{prefix}_count": stats.get("count", 0),
        f"{prefix}_sum": stats.get("sum", 0.0),
        f"{prefix}_mean": stats.get("mean", 0.0),
        f"{prefix}_median": stats.get("median", 0.0),
        f"{prefix}_std": stats.get("std", 0.0),
        f"{prefix}_ci_low": stats.get("ci_low", 0.0),
        f"{prefix}_ci_high": stats.get("ci_high", 0.0),
        f"{prefix}_min": stats.get("min", 0.0),
        f"{prefix}_max": stats.get("max", 0.0),
    }


def _maybe(value: Any, fallback: Any = "") -> Any:
    return fallback if value in (None, "") else value


def _config_label(config: Dict[str, Any]) -> str:
    parts = [
        str(_maybe(config.get("workload_kind"))),
        str(_maybe(config.get("workload_label"))),
        str(_maybe(config.get("trace_name"))),
        str(_maybe(config.get("algorithm"))),
        str(_maybe(config.get("allocation_policy"))),
        f"f{config.get('total_frames')}" if config.get("total_frames") is not None else "",
        f"p{config.get('process_count')}" if config.get("process_count") is not None else "",
    ]
    return " | ".join(part for part in parts if part and part != "")


def _safe_float(value: Any) -> Optional[float]:
    if isinstance(value, dict):
        value = value.get("mean")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        return float(value)
    return None


def _trial_page_fault_rate(trial: Dict[str, Any]) -> Optional[float]:
    if "page_fault_rate" in trial:
        return _safe_float(trial.get("page_fault_rate"))

    accesses = _safe_float(trial.get("total_accesses"))
    if accesses in (None, 0.0):
        return None

    faults = _safe_float(trial.get("page_faults"))
    if faults is None and isinstance(trial.get("system_total"), dict):
        faults = _safe_float(trial["system_total"].get("page_faults"))
    if faults is None:
        return None
    return faults / accesses


def _trial_rows(sources: Sequence[ValidatedSource]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for source in sources:
        if source.is_duplicate_digest:
            continue
        config = source.config
        trials = source.payload.get("trial_results")
        if not isinstance(trials, list):
            continue
        for trial_index, trial in enumerate(trials):
            if not isinstance(trial, dict):
                continue
            per_process = trial.get("per_process") if isinstance(trial.get("per_process"), dict) else {}
            slowdown_values = [
                _safe_float(metrics.get("slowdown"))
                for metrics in per_process.values()
                if isinstance(metrics, dict)
            ]
            slowdown_values = [value for value in slowdown_values if value is not None]
            fairness = trial.get("fairness_metrics") if isinstance(trial.get("fairness_metrics"), dict) else {}
            row = {
                "source_file": str(source.path),
                "trial": trial.get("trial", trial_index),
                "workload_kind": _maybe(config.get("workload_kind")),
                "workload_label": _maybe(config.get("workload_label")),
                "trace_name": _maybe(config.get("trace_name")),
                "algorithm": _maybe(config.get("algorithm")),
                "allocation_policy": _maybe(config.get("allocation_policy")),
                "total_frames": _maybe(config.get("total_frames")),
                "process_count": _maybe(config.get("process_count")),
                "page_faults": _safe_float(trial.get("page_faults"))
                if "page_faults" in trial
                else _safe_float(trial.get("system_total", {}).get("page_faults") if isinstance(trial.get("system_total"), dict) else None),
                "page_replacements": _safe_float(trial.get("system_total", {}).get("page_replacements") if isinstance(trial.get("system_total"), dict) else None),
                "disk_reads": _safe_float(trial.get("system_total", {}).get("disk_reads") if isinstance(trial.get("system_total"), dict) else None),
                "disk_writes": _safe_float(trial.get("system_total", {}).get("disk_writes") if isinstance(trial.get("system_total"), dict) else None),
                "total_disk_io": _safe_float(trial.get("system_total", {}).get("total_disk_io") if isinstance(trial.get("system_total"), dict) else None),
                "page_fault_rate": _trial_page_fault_rate(trial),
                "runtime_ms": _safe_float(trial.get("runtime_ms"))
                if "runtime_ms" in trial
                else (_safe_float(trial.get("simulation_time")) * 1000.0 if _safe_float(trial.get("simulation_time")) is not None else None),
                "throughput": _safe_float(trial.get("throughput")),
                "worst_case_slowdown": _safe_float(trial.get("worst_case_slowdown")),
                "mean_slowdown": _safe_float(trial.get("mean_slowdown")),
                "aggregate_wss": _safe_float(trial.get("aggregate_wss")),
                "memory_ratio_to_wss": _safe_float(trial.get("memory_ratio_to_wss")),
                "slowdown_mean": summarize_values(slowdown_values).get("mean", 0.0),
                "slowdown_median": summarize_values(slowdown_values).get("median", 0.0),
                "fairness_jains_index": _safe_float(fairness.get("jains_index")),
                "fairness_variance": _safe_float(fairness.get("variance")),
                "fairness_cv": _safe_float(fairness.get("cv")),
                "fairness_max_ratio": _safe_float(fairness.get("max_ratio")),
                "fairness_mean": _safe_float(fairness.get("mean")),
                "fairness_std": _safe_float(fairness.get("std")),
                "fairness_min": _safe_float(fairness.get("min")),
                "fairness_max": _safe_float(fairness.get("max")),
                "outlier_flag": False,
            }
            rows.append(row)
    return rows


def _group_sources(sources: Sequence[ValidatedSource]) -> Dict[Tuple[Any, ...], List[ValidatedSource]]:
    grouped: Dict[Tuple[Any, ...], List[ValidatedSource]] = defaultdict(list)
    for source in sources:
        if source.is_duplicate_digest:
            continue
        grouped[source.config_key].append(source)
    return grouped


def _group_summary(sources: Sequence[ValidatedSource]) -> Dict[str, Any]:
    config = dict(sources[0].config)
    trial_rows = _trial_rows(sources)

    metric_names = [
        "page_faults",
        "page_replacements",
        "disk_reads",
        "disk_writes",
        "total_disk_io",
        "page_fault_rate",
        "runtime_ms",
        "throughput",
        "worst_case_slowdown",
        "mean_slowdown",
        "aggregate_wss",
        "memory_ratio_to_wss",
        "slowdown_mean",
        "slowdown_median",
        "fairness_jains_index",
        "fairness_variance",
        "fairness_cv",
        "fairness_max_ratio",
        "fairness_mean",
        "fairness_std",
        "fairness_min",
        "fairness_max",
    ]

    summary: Dict[str, Any] = {
        "config_label": _config_label(config),
        "source_file_count": len(sources),
        "source_files": "; ".join(str(source.path) for source in sources),
        "source_digests": "; ".join(source.digest for source in sources),
        "trial_count": len(trial_rows),
        "duplicate_config_group": len(sources) > 1,
        "workload_kind": _maybe(config.get("workload_kind")),
        "workload_label": _maybe(config.get("workload_label")),
        "trace_name": _maybe(config.get("trace_name")),
        "algorithm": _maybe(config.get("algorithm")),
        "allocation_policy": _maybe(config.get("allocation_policy")),
        "total_frames": _maybe(config.get("total_frames")),
        "process_count": _maybe(config.get("process_count")),
        "page_fault_total": 0.0,
        "page_fault_rate_mean": 0.0,
        "page_fault_rate_median": 0.0,
        "page_fault_rate_std": 0.0,
        "page_fault_rate_ci_low": 0.0,
        "page_fault_rate_ci_high": 0.0,
        "validation_issue_count": sum(len(source.issues) for source in sources),
        "outlier_trial_count": 0,
    }

    for metric in metric_names:
        values = [row[metric] for row in trial_rows if row.get(metric) is not None]
        stats = summarize_values(values)
        summary.update(_flatten_summary(metric, stats))

    for metric in ("aggregate_wss", "memory_ratio_to_wss"):
        values = [row[metric] for row in trial_rows if row.get(metric) is not None]
        stats = summarize_values(values)
        summary.update(_flatten_summary(metric, stats))

    outlier_trial_count = 0
    for source in sources:
        for issue in source.issues:
            if issue.startswith("host_noise_outlier_trial_"):
                outlier_trial_count += 1
    summary["outlier_trial_count"] = outlier_trial_count

    return summary


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_markdown_table(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    if not rows:
        return
    lines = [
        "| " + " | ".join(fieldnames) + " |",
        "| " + " | ".join("---" for _ in fieldnames) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fieldnames) + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_group_results(group_summaries: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result_rows: List[Dict[str, Any]] = []
    for summary in group_summaries:
        result_rows.append(
            {
                "config": {
                    "algorithm": summary.get("algorithm"),
                    "allocation_policy": summary.get("allocation_policy"),
                    "total_frames": summary.get("total_frames"),
                    "process_count": summary.get("process_count"),
                    "workload_kind": summary.get("workload_kind"),
                    "workload_label": summary.get("workload_label"),
                    "trace_name": summary.get("trace_name"),
                },
                "system": {
                    "page_faults": {"mean": summary.get("page_faults_mean", 0.0)},
                    "page_replacements": {"mean": summary.get("page_replacements_mean", 0.0)},
                    "disk_reads": {"mean": summary.get("disk_reads_mean", 0.0)},
                    "disk_writes": {"mean": summary.get("disk_writes_mean", 0.0)},
                    "total_disk_io": {"mean": summary.get("total_disk_io_mean", 0.0)},
                    "runtime_ms": {"mean": summary.get("runtime_ms_mean", 0.0)},
                    "throughput": {"mean": summary.get("throughput_mean", 0.0)},
                    "worst_case_slowdown": {"mean": summary.get("worst_case_slowdown_mean", 0.0)},
                    "mean_slowdown": {"mean": summary.get("mean_slowdown_mean", 0.0)},
                },
                "fairness_metrics": {
                    "jains_index": {"mean": summary.get("fairness_jains_index_mean", 0.0)},
                    "variance": {"mean": summary.get("fairness_variance_mean", 0.0)},
                    "cv": {"mean": summary.get("fairness_cv_mean", 0.0)},
                    "max_ratio": {"mean": summary.get("fairness_max_ratio_mean", 0.0)},
                    "mean": {"mean": summary.get("fairness_mean_mean", 0.0)},
                    "std": {"mean": summary.get("fairness_std_mean", 0.0)},
                    "min": {"mean": summary.get("fairness_min_mean", 0.0)},
                    "max": {"mean": summary.get("fairness_max_mean", 0.0)},
                },
                "aggregate_wss": {"mean": summary.get("aggregate_wss_mean", 0.0)},
                "memory_ratio_to_wss": {"mean": summary.get("memory_ratio_to_wss_mean", 0.0)},
            }
        )
    return result_rows


def _find_matching_result(
    results_list: Sequence[Dict[str, Any]],
    *,
    workload_label: str,
    algorithm: str,
    allocation_policy: str,
    process_count: Optional[int],
    target_memory_ratio: float,
) -> Optional[Dict[str, Any]]:
    candidates: List[Tuple[float, Dict[str, Any]]] = []
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
    results_list: Sequence[Dict[str, Any]],
    *,
    workload_label: str,
    algorithms: Sequence[str],
    allocation_policy: str,
    process_count: int,
    target_memory_ratio: float,
) -> Optional[Dict[str, Any]]:
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


def _placeholder_hypothesis_row(hypothesis: str, condition: str) -> Dict[str, Any]:
    return {
        "hypothesis": hypothesis,
        "test_condition": condition,
        "outcome": "Not evaluated",
        "rules": [],
        "main_metric": "",
        "main_baseline_value": "",
        "main_comparison_value": "",
        "main_percent_change": "",
        "main_threshold_percent": "",
        "rules_summary": "",
        "rule_count": 0,
    }


def _build_hypothesis_rows(group_results: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    h1_condition = "High locality, 4 processes, near 1.2x aggregate WSS"
    h1_global = _find_matching_result(
        group_results,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.2,
    )
    h1_local = _find_matching_result(
        group_results,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.2,
    )
    if h1_global and h1_local:
        rows.extend(
            evaluation_table(
                [
                    evaluate_h1(
                        high_locality_condition=h1_condition,
                        lru_global_faults=result_mean(h1_global, "system", "page_faults") or 0.0,
                        lru_local_faults=result_mean(h1_local, "system", "page_faults") or 0.0,
                        lru_global_worst_slowdown=result_mean(h1_global, "system", "worst_case_slowdown") or 0.0,
                        lru_local_worst_slowdown=result_mean(h1_local, "system", "worst_case_slowdown") or 0.0,
                    )
                ]
            )
        )
    else:
        rows.append(_placeholder_hypothesis_row("H1", h1_condition))

    h2_condition = "Near the aggregate WSS boundary, 4 processes"
    h2_global = _find_matching_result(
        group_results,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    h2_local = _find_matching_result(
        group_results,
        workload_label="high_locality",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    if h2_global and h2_local:
        rows.extend(
            evaluation_table(
                [
                    evaluate_h2(
                        memory_pressure_condition=h2_condition,
                        global_slowdown_variance=result_mean(h2_global, "fairness_metrics", "variance") or 0.0,
                        local_slowdown_variance=result_mean(h2_local, "fairness_metrics", "variance") or 0.0,
                    )
                ]
            )
        )
    else:
        rows.append(_placeholder_hypothesis_row("H2", h2_condition))

    h3_condition = "Mixed workload, 4 processes, near aggregate WSS"
    simple_local = _best_family_result(
        group_results,
        workload_label="mixed",
        algorithms=["FIFO", "NRU"],
        allocation_policy="LocalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    advanced_global = _best_family_result(
        group_results,
        workload_label="mixed",
        algorithms=["LRU", "WSClock"],
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_memory_ratio=1.0,
    )
    if simple_local and advanced_global:
        rows.extend(
            evaluation_table(
                [
                    evaluate_h3(
                        heterogeneous_workload_condition=h3_condition,
                        simple_local_worst_slowdown=result_mean(simple_local, "system", "worst_case_slowdown") or 0.0,
                        advanced_global_worst_slowdown=result_mean(advanced_global, "system", "worst_case_slowdown") or 0.0,
                        simple_local_faults=result_mean(simple_local, "system", "page_faults"),
                        advanced_global_faults=result_mean(advanced_global, "system", "page_faults"),
                    )
                ]
            )
        )
    else:
        rows.append(_placeholder_hypothesis_row("H3", h3_condition))

    return rows


def aggregate_results(sources: Sequence[ValidatedSource]) -> Dict[str, Any]:
    grouped = _group_sources(sources)
    group_summaries = [_group_summary(group) for group in grouped.values()]
    group_summaries.sort(key=lambda row: (str(row.get("workload_label")), str(row.get("algorithm")), str(row.get("allocation_policy")), str(row.get("total_frames"))))

    trial_rows = _trial_rows(sources)
    hypothesis_rows = _build_hypothesis_rows(_build_group_results(group_summaries))

    report = {
        "group_count": len(group_summaries),
        "trial_row_count": len(trial_rows),
        "config_summaries": group_summaries,
        "trial_rows": trial_rows,
        "hypothesis_rows": hypothesis_rows,
    }
    return report


def write_aggregate_outputs(report: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "final_aggregate_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    config_rows = report.get("config_summaries", [])
    if config_rows:
        config_fields = [
            "config_label",
            "workload_kind",
            "workload_label",
            "trace_name",
            "algorithm",
            "allocation_policy",
            "total_frames",
            "process_count",
            "source_file_count",
            "trial_count",
            "page_fault_total",
            "page_fault_rate_mean",
            "page_fault_rate_median",
            "page_fault_rate_std",
            "page_fault_rate_ci_low",
            "page_fault_rate_ci_high",
            "page_faults_mean",
            "page_faults_median",
            "page_faults_std",
            "page_faults_ci_low",
            "page_faults_ci_high",
            "page_faults_sum",
            "page_replacements_mean",
            "disk_reads_mean",
            "disk_writes_mean",
            "total_disk_io_mean",
            "runtime_ms_mean",
            "throughput_mean",
            "worst_case_slowdown_mean",
            "mean_slowdown_mean",
            "aggregate_wss_mean",
            "aggregate_wss_median",
            "aggregate_wss_std",
            "aggregate_wss_ci_low",
            "aggregate_wss_ci_high",
            "aggregate_wss_sum",
            "memory_ratio_to_wss_mean",
            "memory_ratio_to_wss_median",
            "memory_ratio_to_wss_std",
            "memory_ratio_to_wss_ci_low",
            "memory_ratio_to_wss_ci_high",
            "memory_ratio_to_wss_sum",
            "fairness_jains_index_mean",
            "fairness_variance_mean",
            "fairness_cv_mean",
            "fairness_max_ratio_mean",
            "fairness_mean_mean",
            "fairness_std_mean",
            "fairness_min_mean",
            "fairness_max_mean",
            "outlier_trial_count",
            "validation_issue_count",
            "source_files",
        ]
        _write_csv(output_dir / "final_aggregate_results.csv", config_rows, config_fields)

    trial_rows = report.get("trial_rows", [])
    if trial_rows:
        trial_fields = [
            "source_file",
            "trial",
            "workload_kind",
            "workload_label",
            "trace_name",
            "algorithm",
            "allocation_policy",
            "total_frames",
            "process_count",
            "page_faults",
            "page_replacements",
            "disk_reads",
            "disk_writes",
            "total_disk_io",
            "page_fault_rate",
            "runtime_ms",
            "throughput",
            "worst_case_slowdown",
            "mean_slowdown",
            "aggregate_wss",
            "memory_ratio_to_wss",
            "slowdown_mean",
            "slowdown_median",
            "fairness_jains_index",
            "fairness_variance",
            "fairness_cv",
            "fairness_max_ratio",
            "fairness_mean",
            "fairness_std",
            "fairness_min",
            "fairness_max",
            "outlier_flag",
        ]
        _write_csv(output_dir / "trial_level_results.csv", trial_rows, trial_fields)

    hypothesis_rows = report.get("hypothesis_rows", [])
    if hypothesis_rows:
        hypothesis_fields = [
            "hypothesis",
            "test_condition",
            "outcome",
            "main_metric",
            "main_baseline_value",
            "main_comparison_value",
            "main_percent_change",
            "main_threshold_percent",
            "rules_summary",
            "rule_count",
        ]
        _write_csv(output_dir / "hypothesis_evaluation.csv", hypothesis_rows, hypothesis_fields)
        _write_markdown_table(output_dir / "hypothesis_evaluation.md", hypothesis_rows, hypothesis_fields)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate benchmark result bundles.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Root directory to scan for benchmark JSON files. May be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/processed",
        help="Directory to write processed outputs.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Also scan the tests/ tree. Disabled by default so the canonical outputs stay clean.",
    )
    args = parser.parse_args()

    roots = [Path(item) for item in args.source] if args.source else [DEFAULT_CANONICAL_SOURCE]
    if args.include_tests and Path("tests") not in roots:
        roots.append(Path("tests"))
    candidates = discover_candidate_files(roots)
    sources = load_sources(candidates)
    wrapper_roots = [Path("results")]
    if args.include_tests:
        wrapper_roots.append(Path("tests"))
    validation = validate_sources(sources, wrapper_roots=wrapper_roots)
    write_validation_outputs(validation, Path(args.output_dir))
    report = aggregate_results(sources)
    write_aggregate_outputs(report, Path(args.output_dir))

    print(f"Aggregated {report['group_count']} config groups from {len(sources)} benchmark files.")
    print(f"Trial rows: {report['trial_row_count']}")
    print(f"Hypothesis table: {Path(args.output_dir) / 'hypothesis_evaluation.csv'}")


if __name__ == "__main__":
    main()
