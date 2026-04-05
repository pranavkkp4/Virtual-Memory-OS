#!/usr/bin/env python3
"""Build the final headline figures for the virtual memory report."""

from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SRC_DIR = REPO_ROOT / "src"
for candidate in (SCRIPTS_DIR, SRC_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from build_report_tables import (  # type: ignore
    CANONICAL_CAMPAIGN_ROOT,
    OUTPUT_FIGURES,
    _as_float,
    _display_workload,
    _format_value,
    _is_demo_or_smoke_record,
    _policy_label,
    assign_pressure_ranks,
    build_hypothesis_results,
    load_result_records,
)


plt.style.use("seaborn-v0_8-whitegrid")


def _save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _metric_sort_value(record: Dict[str, object], metric: str, *, default: float) -> float:
    value = _as_float(record.get(metric))
    return value if value is not None else default


def _pressure_summary(records: Sequence[Dict[str, object]], metric: str) -> Dict[str, Dict[int, Tuple[float, float]]]:
    summary: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if _is_demo_or_smoke_record(record):
            continue
        if str(record.get("workload_kind") or "") != "synthetic":
            continue
        policy = str(record.get("allocation_policy") or "")
        rank = record.get("pressure_rank")
        value = _as_float(record.get(metric))
        if not policy or rank is None or value is None:
            continue
        summary[policy][int(rank)].append(value)

    final: Dict[str, Dict[int, Tuple[float, float]]] = {}
    for policy, ranks in summary.items():
        final[policy] = {}
        for rank, values in ranks.items():
            final[policy][rank] = (
                float(statistics.mean(values)),
                float(statistics.stdev(values)) if len(values) > 1 else 0.0,
            )
    return final


def _policy_algorithm_summary(records: Sequence[Dict[str, object]], metric: str) -> Dict[str, Dict[str, Tuple[float, float]]]:
    summary: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if _is_demo_or_smoke_record(record):
            continue
        if str(record.get("workload_kind") or "") != "synthetic":
            continue
        policy = str(record.get("allocation_policy") or "")
        algorithm = str(record.get("algorithm") or "")
        value = _as_float(record.get(metric))
        if not policy or not algorithm or value is None:
            continue
        summary[policy][algorithm].append(value)

    final: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for policy, algorithms in summary.items():
        final[policy] = {}
        for algorithm, values in algorithms.items():
            final[policy][algorithm] = (
                float(statistics.mean(values)),
                float(statistics.stdev(values)) if len(values) > 1 else 0.0,
            )
    return final


def _choose_best(records: Sequence[Dict[str, object]], metric: str, *, higher_is_better: bool) -> Optional[Dict[str, object]]:
    valid = [record for record in records if _as_float(record.get(metric)) is not None]
    if not valid:
        return None
    if higher_is_better:
        return max(valid, key=lambda record: _metric_sort_value(record, metric, default=float("-inf")))
    return min(valid, key=lambda record: _metric_sort_value(record, metric, default=float("inf")))


def plot_page_faults_vs_memory_pressure(records: Sequence[Dict[str, object]], out_path: Path) -> None:
    summary = _pressure_summary(records, "page_faults_mean")
    if not summary:
        return

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    colors = {"GlobalAllocation": "#2B6CB0", "LocalAllocation": "#C05621", "ProportionalAllocation": "#6B46C1"}
    all_ranks = sorted({rank for ranks in summary.values() for rank in ranks})
    for policy, ranks in sorted(summary.items()):
        xs = sorted(ranks)
        means = [ranks[rank][0] for rank in xs]
        stds = [ranks[rank][1] for rank in xs]
        ax.errorbar(
            xs,
            means,
            yerr=stds,
            marker="o",
            linewidth=2,
            capsize=3,
            label=policy.replace("Allocation", ""),
            color=colors.get(policy, None),
        )

    ax.set_title("Page faults vs memory pressure")
    ax.set_xlabel("Pressure level within each workload family")
    ax.set_ylabel("Mean page faults")
    ax.set_xticks(all_ranks)
    ax.set_xticklabels([f"P{rank}" for rank in all_ranks])
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.3)
    ax.text(0.01, -0.18, "Lower pressure ranks mean fewer frames. Levels are ordered within each workload family.", transform=ax.transAxes, fontsize=9)
    _save_figure(fig, out_path)


def plot_slowdown_variance_vs_memory_pressure(records: Sequence[Dict[str, object]], out_path: Path) -> None:
    summary = _pressure_summary(records, "slowdown_variance_mean")
    if not summary:
        return

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    colors = {"GlobalAllocation": "#2F855A", "LocalAllocation": "#DD6B20", "ProportionalAllocation": "#805AD5"}
    all_ranks = sorted({rank for ranks in summary.values() for rank in ranks})
    for policy, ranks in sorted(summary.items()):
        xs = sorted(ranks)
        means = [ranks[rank][0] for rank in xs]
        stds = [ranks[rank][1] for rank in xs]
        ax.errorbar(
            xs,
            means,
            yerr=stds,
            marker="o",
            linewidth=2,
            capsize=3,
            label=policy.replace("Allocation", ""),
            color=colors.get(policy, None),
        )

    ax.set_title("Slowdown variance vs memory pressure")
    ax.set_xlabel("Pressure level within each workload family")
    ax.set_ylabel("Mean slowdown variance")
    ax.set_xticks(all_ranks)
    ax.set_xticklabels([f"P{rank}" for rank in all_ranks])
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.3)
    ax.text(0.01, -0.18, "Variance is computed from per-process slowdown when present in the result bundle.", transform=ax.transAxes, fontsize=9)
    _save_figure(fig, out_path)


def plot_metric_vs_policy(records: Sequence[Dict[str, object]], metric: str, title: str, ylabel: str, out_path: Path) -> None:
    summary = _policy_algorithm_summary(records, metric)
    if not summary:
        return

    policies = [policy for policy in ("GlobalAllocation", "LocalAllocation", "ProportionalAllocation") if policy in summary]
    algorithms = sorted({algorithm for policy in summary.values() for algorithm in policy.keys()})

    fig, ax = plt.subplots(figsize=(9.75, 5.75))
    x = np.arange(len(policies))
    width = 0.75 / max(len(algorithms), 1)
    palette = {
        "FIFO": "#2B6CB0",
        "LRU": "#38A169",
        "NRU": "#D69E2E",
        "SecondChance": "#805AD5",
        "WSClock": "#C05621",
    }

    for index, algorithm in enumerate(algorithms):
        offsets = x - 0.375 + width / 2 + index * width
        means = []
        stds = []
        for policy in policies:
            value = summary.get(policy, {}).get(algorithm)
            if value is None:
                means.append(np.nan)
                stds.append(0.0)
            else:
                means.append(value[0])
                stds.append(value[1])
        ax.bar(
            offsets,
            means,
            width=width,
            yerr=stds,
            capsize=3,
            label=algorithm,
            color=palette.get(algorithm, None),
            alpha=0.9,
        )

    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([policy.replace("Allocation", "") for policy in policies])
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.3)
    _save_figure(fig, out_path)


def plot_trace_driven_comparison(records: Sequence[Dict[str, object]], out_path: Path) -> None:
    workload_order: List[Tuple[str, str]] = []
    for record in records:
        if _is_demo_or_smoke_record(record):
            continue
        if str(record.get("workload_kind") or "") not in {"synthetic", "trace"}:
            continue
        pair = (_display_workload(record), str(record.get("workload_kind") or ""))
        if pair not in workload_order:
            workload_order.append(pair)

    selected: Dict[str, Dict[str, object]] = {}
    for workload, kind in workload_order:
        subset = [record for record in records if _display_workload(record) == workload and str(record.get("workload_kind") or "") == kind]
        if not subset:
            continue
        selected[f"{workload}\n({kind})"] = {
            "page_faults": _choose_best(subset, "page_faults_mean", higher_is_better=False),
            "worst_case_slowdown": _choose_best(subset, "worst_case_slowdown_mean", higher_is_better=False),
            "jains_index": _choose_best(subset, "jains_index_mean", higher_is_better=True),
        }

    if not selected:
        return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True)
    metric_specs = [
        ("page_faults", "Page faults", "#2B6CB0", "page_faults_mean"),
        ("worst_case_slowdown", "Worst-case slowdown", "#D69E2E", "worst_case_slowdown_mean"),
        ("jains_index", "Jain's fairness index", "#2F855A", "jains_index_mean"),
    ]

    workloads = list(selected.keys())
    x = np.arange(len(workloads))
    for axis, (metric_key, ylabel, color, value_key) in zip(axes, metric_specs):
        values = []
        labels = []
        for workload in workloads:
            record = selected[workload][metric_key]
            values.append(_as_float(record.get(value_key)) if record else None)
            labels.append(_policy_label(record) if record else "")

        axis.bar(x, values, color=color, alpha=0.88)
        axis.set_title(ylabel)
        axis.set_xticks(x)
        axis.set_xticklabels(workloads, rotation=20, ha="right")
        axis.grid(axis="y", alpha=0.3)
        if metric_key == "jains_index":
            axis.set_ylim(0, 1.05)
        for index, (value, label) in enumerate(zip(values, labels)):
            if value is None:
                continue
            axis.text(index, value, f"{_format_value(value)}\n{label}", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Trace-driven comparison against synthetic workloads", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Metric value")
    fig.text(0.5, 0.01, "Each bar uses the best policy for the metric within that workload.", ha="center", fontsize=9)
    _save_figure(fig, out_path)


def plot_hypothesis_summary(records: Sequence[Dict[str, object]], out_path: Path) -> None:
    hypotheses = build_hypothesis_results(records)
    if not hypotheses:
        return

    summary_colors = {
        "Supported": "#2F855A",
        "Partially supported": "#D69E2E",
        "Not supported": "#C53030",
    }
    rows = [result.to_csv_row() for result in hypotheses]
    labels = [row["hypothesis"] for row in rows]
    outcomes = [row["outcome"] for row in rows]
    percent_changes = [row.get("main_percent_change") for row in rows]
    metric_names = [row.get("main_metric", "") for row in rows]

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    x = np.arange(len(labels))
    colors = [summary_colors.get(outcome, "#718096") for outcome in outcomes]
    ax.bar(x, [1] * len(labels), color=colors, alpha=0.9)
    ax.set_ylim(0, 1.2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_yticks([])
    ax.set_title("Hypothesis summary")

    for index, (outcome, pct, metric) in enumerate(zip(outcomes, percent_changes, metric_names)):
        text = outcome
        if pct is not None:
            text += f"\n{metric}: {pct:+.1f}%"
        ax.text(index, 0.5, text, ha="center", va="center", color="white", fontsize=10, fontweight="bold")

    supported = sum(1 for outcome in outcomes if outcome == "Supported")
    partial = sum(1 for outcome in outcomes if outcome == "Partially supported")
    ax.text(0.01, -0.16, f"Supported: {supported}, partially supported: {partial}, not supported: {len(labels) - supported - partial}.", transform=ax.transAxes, fontsize=9)
    _save_figure(fig, out_path)


def build_figures(results_root: Path = CANONICAL_CAMPAIGN_ROOT) -> Dict[str, Path]:
    records = load_result_records(results_root)
    if not records:
        raise RuntimeError(f"No usable result records found under {results_root}")

    records = [record for record in records if not _is_demo_or_smoke_record(record)]
    assign_pressure_ranks(records)
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

    paths = {
        "page_faults_vs_memory_pressure": OUTPUT_FIGURES / "page_faults_vs_memory_pressure.png",
        "worst_case_slowdown_vs_policy": OUTPUT_FIGURES / "worst_case_slowdown_vs_policy.png",
        "jains_fairness_vs_policy": OUTPUT_FIGURES / "jains_fairness_vs_policy.png",
        "slowdown_variance_vs_memory_pressure": OUTPUT_FIGURES / "slowdown_variance_vs_memory_pressure.png",
        "trace_driven_comparison": OUTPUT_FIGURES / "trace_driven_comparison.png",
        "hypothesis_summary": OUTPUT_FIGURES / "hypothesis_summary.png",
    }

    plot_page_faults_vs_memory_pressure(records, paths["page_faults_vs_memory_pressure"])
    plot_metric_vs_policy(records, "worst_case_slowdown_mean", "Worst-case slowdown vs policy", "Worst-case slowdown", paths["worst_case_slowdown_vs_policy"])
    plot_metric_vs_policy(records, "jains_index_mean", "Jain's fairness index vs policy", "Jain's fairness index", paths["jains_fairness_vs_policy"])
    plot_slowdown_variance_vs_memory_pressure(records, paths["slowdown_variance_vs_memory_pressure"])
    plot_trace_driven_comparison(records, paths["trace_driven_comparison"])
    plot_hypothesis_summary(records, paths["hypothesis_summary"])

    return paths


def main() -> None:
    paths = build_figures()
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
