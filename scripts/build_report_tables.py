#!/usr/bin/env python3
"""Build compact, report-ready tables for the final virtual memory report."""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CAMPAIGN_ROOT = REPO_ROOT / "results" / "raw" / "campaign_20260404_140330_266"
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hypothesis_evaluator import evaluate_h1, evaluate_h2, evaluate_h3


OUTPUT_FIGURES = REPO_ROOT / "results" / "figures"
OUTPUT_TABLES = REPO_ROOT / "results" / "tables"


def _as_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    if isinstance(value, dict):
        for key in ("mean", "value", "std"):
            nested = value.get(key)
            if isinstance(nested, (int, float)):
                return float(nested)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unwrap_metric(metric: object) -> Tuple[Optional[float], Optional[float]]:
    if isinstance(metric, dict):
        return _as_float(metric.get("mean")), _as_float(metric.get("std"))
    return _as_float(metric), None


def _format_value(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        magnitude = abs(value)
        if magnitude >= 1000:
            text = f"{value:.1f}"
        elif magnitude >= 100:
            text = f"{value:.2f}"
        elif magnitude >= 1:
            text = f"{value:.3f}"
        elif magnitude >= 0.01:
            text = f"{value:.4f}"
        else:
            text = f"{value:.6f}"
        return text.rstrip("0").rstrip(".") if "." in text else text
    return str(value)


def _display_workload(record: Dict[str, object]) -> str:
    trace_name = str(record.get("trace_name") or "").strip()
    workload_label = str(record.get("workload_label") or "").strip()
    if trace_name:
        return f"trace: {trace_name}"
    return workload_label or "unknown"


def _policy_label(record: Dict[str, object]) -> str:
    return f"{record.get('algorithm', '')} + {record.get('allocation_policy', '')}".strip()


def _metric_sort_value(record: Dict[str, object], metric: str, *, default: float) -> float:
    value = _as_float(record.get(metric))
    return value if value is not None else default


def _is_demo_or_smoke_record(record: Dict[str, object]) -> bool:
    source_path = str(record.get("source_path") or "").lower().replace("/", "\\")
    trace_name = str(record.get("trace_name") or "").strip().lower()
    if trace_name.startswith("demo"):
        return True
    if "tests\\" in source_path or "\\tests\\" in source_path:
        return True
    if "pilot_" in source_path or "\\pilot_" in source_path:
        return True
    if "demo_bundle_smoke" in source_path or "\\demo\\" in source_path:
        return True
    return False


def _jains_from_slowdowns(values: Sequence[float]) -> float:
    if not values:
        return 1.0
    perf = [1.0 / max(value, 1e-10) for value in values]
    total = sum(perf)
    if total == 0:
        return 1.0
    return (total * total) / (len(perf) * sum(value * value for value in perf))


def _extract_common_fields(payload: Dict[str, object], *, source: str) -> Dict[str, object]:
    config = payload.get("config", {}) if isinstance(payload.get("config"), dict) else {}
    system = payload.get("system", {}) if isinstance(payload.get("system"), dict) else {}
    fairness = payload.get("fairness_metrics", {}) if isinstance(payload.get("fairness_metrics"), dict) else {}

    page_faults, page_faults_std = _unwrap_metric(system.get("page_faults"))
    worst_slowdown, worst_slowdown_std = _unwrap_metric(system.get("worst_case_slowdown"))
    mean_slowdown, mean_slowdown_std = _unwrap_metric(system.get("mean_slowdown"))
    throughput, throughput_std = _unwrap_metric(system.get("throughput"))
    runtime_ms, runtime_ms_std = _unwrap_metric(system.get("runtime_ms"))

    jains_index, jains_std = _unwrap_metric(fairness.get("jains_index"))
    variance, variance_std = _unwrap_metric(fairness.get("variance"))
    cv, cv_std = _unwrap_metric(fairness.get("cv"))
    max_ratio, max_ratio_std = _unwrap_metric(fairness.get("max_ratio"))

    workload_label = str(config.get("workload_label") or payload.get("workload_label") or "").strip()
    workload_kind = str(config.get("workload_kind") or payload.get("workload_kind") or "").strip()
    trace_name = str(config.get("trace_name") or payload.get("trace_name") or "").strip()
    if not workload_kind:
        workload_kind = "trace" if trace_name else "synthetic"

    return {
        "source": source,
        "source_path": str(payload.get("source_path", "")),
        "workload_label": workload_label,
        "workload_kind": workload_kind,
        "trace_name": trace_name,
        "algorithm": str(config.get("algorithm") or "").strip(),
        "allocation_policy": str(config.get("allocation_policy") or "").strip(),
        "process_count": _as_float(config.get("process_count") or payload.get("process_count")),
        "total_frames": _as_float(config.get("total_frames") or config.get("num_frames") or payload.get("total_frames")),
        "memory_ratio_to_wss": _as_float(payload.get("memory_ratio_to_wss") or config.get("memory_ratio_to_wss")),
        "page_faults_mean": page_faults,
        "page_faults_std": page_faults_std,
        "worst_case_slowdown_mean": worst_slowdown,
        "worst_case_slowdown_std": worst_slowdown_std,
        "mean_slowdown_mean": mean_slowdown,
        "mean_slowdown_std": mean_slowdown_std,
        "throughput_mean": throughput,
        "throughput_std": throughput_std,
        "runtime_ms_mean": runtime_ms,
        "runtime_ms_std": runtime_ms_std,
        "jains_index_mean": jains_index,
        "jains_index_std": jains_std,
        "slowdown_variance_mean": variance,
        "slowdown_variance_std": variance_std,
        "fairness_cv_mean": cv,
        "fairness_cv_std": cv_std,
        "fairness_max_ratio_mean": max_ratio,
        "fairness_max_ratio_std": max_ratio_std,
    }


def _load_json_summary(path: Path) -> Optional[Dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict) or "config" not in payload or "system" not in payload:
        return None

    payload["source_path"] = str(path.relative_to(REPO_ROOT))
    return _extract_common_fields(payload, source="json")


def _load_csv_trial_summaries(path: Path) -> List[Dict[str, object]]:
    trial_rows: Dict[Tuple[object, ...], List[Dict[str, object]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            trial_key = (
                row.get("workload_label", ""),
                row.get("workload_kind", ""),
                row.get("trace_name", ""),
                row.get("algorithm", ""),
                row.get("allocation_policy", ""),
                row.get("memory_frames", ""),
                row.get("repetition_id", ""),
            )
            trial_rows[trial_key].append(row)

    trial_summaries: List[Dict[str, object]] = []
    for trial_key, rows in trial_rows.items():
        faults: List[float] = []
        slowdowns: List[float] = []
        for row in rows:
            fault = _as_float(row.get("page_faults"))
            slowdown = _as_float(row.get("slowdown"))
            if fault is not None:
                faults.append(fault)
            if slowdown is not None:
                slowdowns.append(slowdown)

        trial_summaries.append(
            {
                "workload_label": trial_key[0],
                "workload_kind": trial_key[1] or "synthetic",
                "trace_name": trial_key[2],
                "algorithm": trial_key[3],
                "allocation_policy": trial_key[4],
                "process_count": float(len(rows)),
                "total_frames": _as_float(trial_key[5]),
                "page_faults_mean": float(sum(faults)) if faults else None,
                "worst_case_slowdown_mean": max(slowdowns) if slowdowns else None,
                "mean_slowdown_mean": float(statistics.mean(slowdowns)) if slowdowns else None,
                "jains_index_mean": _jains_from_slowdowns(slowdowns),
                "slowdown_variance_mean": float(statistics.variance(slowdowns)) if len(slowdowns) > 1 else 0.0,
            }
        )

    config_groups: Dict[Tuple[object, ...], List[Dict[str, object]]] = defaultdict(list)
    for trial in trial_summaries:
        config_key = (
            trial["workload_label"],
            trial["workload_kind"],
            trial["trace_name"],
            trial["algorithm"],
            trial["allocation_policy"],
            trial["total_frames"],
        )
        config_groups[config_key].append(trial)

    summaries: List[Dict[str, object]] = []
    for config_key, trials in config_groups.items():
        page_faults = [trial["page_faults_mean"] for trial in trials if trial.get("page_faults_mean") is not None]
        slowdowns = [trial["worst_case_slowdown_mean"] for trial in trials if trial.get("worst_case_slowdown_mean") is not None]
        mean_slowdowns = [trial["mean_slowdown_mean"] for trial in trials if trial.get("mean_slowdown_mean") is not None]
        jains = [trial["jains_index_mean"] for trial in trials if trial.get("jains_index_mean") is not None]
        variances = [trial["slowdown_variance_mean"] for trial in trials if trial.get("slowdown_variance_mean") is not None]

        summaries.append(
            {
                "source": "csv",
                "source_path": str(path.relative_to(REPO_ROOT)),
                "workload_label": config_key[0],
                "workload_kind": config_key[1],
                "trace_name": config_key[2],
                "algorithm": config_key[3],
                "allocation_policy": config_key[4],
                "process_count": float(statistics.mean([trial["process_count"] for trial in trials])) if trials else None,
                "total_frames": _as_float(config_key[5]),
                "memory_ratio_to_wss": None,
                "page_faults_mean": float(statistics.mean(page_faults)) if page_faults else None,
                "page_faults_std": float(statistics.stdev(page_faults)) if len(page_faults) > 1 else 0.0,
                "worst_case_slowdown_mean": float(statistics.mean(slowdowns)) if slowdowns else None,
                "worst_case_slowdown_std": float(statistics.stdev(slowdowns)) if len(slowdowns) > 1 else 0.0,
                "mean_slowdown_mean": float(statistics.mean(mean_slowdowns)) if mean_slowdowns else None,
                "jains_index_mean": float(statistics.mean(jains)) if jains else None,
                "slowdown_variance_mean": float(statistics.mean(variances)) if variances else None,
            }
        )

    return summaries


def load_result_records(results_root: Path = CANONICAL_CAMPAIGN_ROOT) -> List[Dict[str, object]]:
    """Load the best available result summaries from JSON and CSV exports."""
    records: Dict[Tuple[object, ...], Dict[str, object]] = {}

    for json_path in sorted(results_root.rglob("*.json")):
        if "metadata" in json_path.parts or json_path.name.startswith("run_environment"):
            continue
        record = _load_json_summary(json_path)
        if not record:
            continue
        if _is_demo_or_smoke_record(record):
            continue
        key = (
            record.get("workload_label"),
            record.get("workload_kind"),
            record.get("trace_name"),
            record.get("algorithm"),
            record.get("allocation_policy"),
            record.get("process_count"),
            record.get("total_frames"),
        )
        records[key] = record

    for csv_path in sorted(results_root.rglob("slowdown_metrics.csv")):
        for record in _load_csv_trial_summaries(csv_path):
            if _is_demo_or_smoke_record(record):
                continue
            key = (
                record.get("workload_label"),
                record.get("workload_kind"),
                record.get("trace_name"),
                record.get("algorithm"),
                record.get("allocation_policy"),
                record.get("process_count"),
                record.get("total_frames"),
            )
            records.setdefault(key, record)

    return list(records.values())


def assign_pressure_ranks(records: Sequence[Dict[str, object]]) -> None:
    """Assign a rank to each memory-pressure point within a workload family."""
    grouped_values: Dict[Tuple[object, ...], List[Tuple[float, Dict[str, object]]]] = defaultdict(list)

    for record in records:
        family_key = (
            record.get("workload_label"),
            record.get("workload_kind"),
            record.get("trace_name"),
            record.get("process_count"),
        )
        sort_value = record.get("memory_ratio_to_wss")
        if sort_value is None:
            sort_value = record.get("total_frames")
        if sort_value is None:
            continue
        try:
            grouped_values[family_key].append((float(sort_value), record))
        except (TypeError, ValueError):
            continue

    for values in grouped_values.values():
        ordered = sorted({value for value, _ in values})
        rank_map = {value: index + 1 for index, value in enumerate(ordered)}
        for value, record in values:
            record["pressure_rank"] = rank_map[value]
            record["pressure_count"] = len(ordered)
            record["pressure_value"] = value


def _preferred_workloads(records: Sequence[Dict[str, object]]) -> List[Tuple[str, str]]:
    ordered: List[Tuple[str, str]] = []
    for record in records:
        key = (_display_workload(record), str(record.get("workload_kind") or ""))
        if key not in ordered:
            ordered.append(key)
    return ordered


def _best_record(records: Sequence[Dict[str, object]], *, metric: str, higher_is_better: bool) -> Optional[Dict[str, object]]:
    valid = [record for record in records if _as_float(record.get(metric)) is not None]
    if not valid:
        return None
    if higher_is_better:
        return max(valid, key=lambda record: _metric_sort_value(record, metric, default=float("-inf")))
    return min(valid, key=lambda record: _metric_sort_value(record, metric, default=float("inf")))


def build_best_policy_rows(records: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for workload, kind in _preferred_workloads(records):
        workload_records = [record for record in records if _display_workload(record) == workload and str(record.get("workload_kind") or "") == kind]
        if not workload_records:
            continue

        best_faults = _best_record(workload_records, metric="page_faults_mean", higher_is_better=False)
        best_slowdown = _best_record(workload_records, metric="worst_case_slowdown_mean", higher_is_better=False)
        best_fairness = _best_record(workload_records, metric="jains_index_mean", higher_is_better=True)

        rows.append(
            {
                "workload": workload,
                "kind": kind,
                "lowest_page_faults": _policy_label(best_faults) if best_faults else "",
                "lowest_page_faults_value": _as_float(best_faults.get("page_faults_mean")) if best_faults else None,
                "lowest_worst_slowdown": _policy_label(best_slowdown) if best_slowdown else "",
                "lowest_worst_slowdown_value": _as_float(best_slowdown.get("worst_case_slowdown_mean")) if best_slowdown else None,
                "highest_jains_index": _policy_label(best_fairness) if best_fairness else "",
                "highest_jains_index_value": _as_float(best_fairness.get("jains_index_mean")) if best_fairness else None,
            }
        )

    return rows


def _select_matching_record(
    records: Sequence[Dict[str, object]],
    *,
    workload_label: str,
    workload_kind: str,
    algorithm: str,
    allocation_policy: str,
    process_count: Optional[int],
    target_ratio: float,
) -> Optional[Dict[str, object]]:
    candidates = []
    target_rank = {0.8: 1, 1.0: 2, 1.2: 3, 1.5: 4}.get(round(target_ratio, 1), 2)

    for record in records:
        if record.get("workload_label") != workload_label:
            continue
        if str(record.get("workload_kind") or "") != workload_kind:
            continue
        if record.get("algorithm") != algorithm:
            continue
        if record.get("allocation_policy") != allocation_policy:
            continue
        if process_count is not None and int(record.get("process_count") or -1) != process_count:
            continue

        ratio = record.get("memory_ratio_to_wss")
        rank = record.get("pressure_rank")
        if ratio is not None:
            candidates.append((abs(float(ratio) - target_ratio), 0, record))
        elif rank is not None:
            candidates.append((abs(int(rank) - target_rank), 1, record))
        else:
            candidates.append((float("inf"), 2, record))

    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            _metric_sort_value(item[2], "total_frames", default=float("inf")),
        )
    )
    return candidates[0][2]


def build_hypothesis_results(records: Sequence[Dict[str, object]]):
    results = []

    h1_global = _select_matching_record(
        records,
        workload_label="high_locality",
        workload_kind="synthetic",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_ratio=1.2,
    )
    h1_local = _select_matching_record(
        records,
        workload_label="high_locality",
        workload_kind="synthetic",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_ratio=1.2,
    )
    if h1_global and h1_local:
        results.append(
            evaluate_h1(
                high_locality_condition="High locality, 4 processes, near 1.2x WSS",
                lru_global_faults=_as_float(h1_global.get("page_faults_mean")) or 0.0,
                lru_local_faults=_as_float(h1_local.get("page_faults_mean")) or 0.0,
                lru_global_worst_slowdown=_as_float(h1_global.get("worst_case_slowdown_mean")) or 0.0,
                lru_local_worst_slowdown=_as_float(h1_local.get("worst_case_slowdown_mean")) or 0.0,
            )
        )

    h2_global = _select_matching_record(
        records,
        workload_label="high_locality",
        workload_kind="synthetic",
        algorithm="LRU",
        allocation_policy="GlobalAllocation",
        process_count=4,
        target_ratio=1.0,
    )
    h2_local = _select_matching_record(
        records,
        workload_label="high_locality",
        workload_kind="synthetic",
        algorithm="LRU",
        allocation_policy="LocalAllocation",
        process_count=4,
        target_ratio=1.0,
    )
    if h2_global and h2_local:
        results.append(
            evaluate_h2(
                memory_pressure_condition="Near the aggregate WSS boundary, 4 processes",
                global_slowdown_variance=_as_float(h2_global.get("slowdown_variance_mean")) or 0.0,
                local_slowdown_variance=_as_float(h2_local.get("slowdown_variance_mean")) or 0.0,
            )
        )

    simple_candidates = []
    for algorithm in ("FIFO", "NRU"):
        candidate = _select_matching_record(
            records,
            workload_label="mixed",
            workload_kind="synthetic",
            algorithm=algorithm,
            allocation_policy="LocalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        if candidate:
            simple_candidates.append(candidate)

    advanced_candidates = []
    for algorithm in ("LRU", "WSClock"):
        candidate = _select_matching_record(
            records,
            workload_label="mixed",
            workload_kind="synthetic",
            algorithm=algorithm,
            allocation_policy="GlobalAllocation",
            process_count=4,
            target_ratio=1.0,
        )
        if candidate:
            advanced_candidates.append(candidate)

    if simple_candidates and advanced_candidates:
        simple_local = min(simple_candidates, key=lambda record: _metric_sort_value(record, "worst_case_slowdown_mean", default=float("inf")))
        advanced_global = min(advanced_candidates, key=lambda record: _metric_sort_value(record, "worst_case_slowdown_mean", default=float("inf")))
        results.append(
            evaluate_h3(
                heterogeneous_workload_condition="Mixed workload, 4 processes, near aggregate WSS",
                simple_local_worst_slowdown=_as_float(simple_local.get("worst_case_slowdown_mean")) or 0.0,
                advanced_global_worst_slowdown=_as_float(advanced_global.get("worst_case_slowdown_mean")) or 0.0,
                simple_local_faults=_as_float(simple_local.get("page_faults_mean")),
                advanced_global_faults=_as_float(advanced_global.get("page_faults_mean")),
            )
        )

    return results


def _write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def _write_markdown_table(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    if not rows:
        return
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_format_value(row.get(header, "")) for header in headers) + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_tables(results_root: Path = CANONICAL_CAMPAIGN_ROOT) -> Dict[str, Path]:
    records = load_result_records(results_root)
    if not records:
        raise RuntimeError(f"No usable result records found under {results_root}")

    assign_pressure_ranks(records)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)

    best_policy_rows = build_best_policy_rows(records)
    hypothesis_results = build_hypothesis_results(records)
    hypothesis_rows = [{key: value for key, value in result.to_csv_row().items() if key != "rules"} for result in hypothesis_results]

    best_policy_csv = OUTPUT_TABLES / "best_policy_by_workload.csv"
    best_policy_md = OUTPUT_TABLES / "best_policy_by_workload.md"
    hypothesis_csv = OUTPUT_TABLES / "hypothesis_summary.csv"
    hypothesis_md = OUTPUT_TABLES / "hypothesis_summary.md"

    _write_csv(best_policy_csv, best_policy_rows)
    _write_markdown_table(best_policy_md, best_policy_rows)
    _write_csv(hypothesis_csv, hypothesis_rows)
    _write_markdown_table(hypothesis_md, hypothesis_rows)

    return {
        "best_policy_csv": best_policy_csv,
        "best_policy_md": best_policy_md,
        "hypothesis_csv": hypothesis_csv,
        "hypothesis_md": hypothesis_md,
    }


def main() -> None:
    paths = build_tables()
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
