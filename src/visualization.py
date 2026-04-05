"""
Visualization Tools for Virtual Memory Experiments
==================================================

Creates plots and charts for:
- Page fault curves
- Performance comparisons
- Fairness metrics
- Slowdown distributions
"""

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


def _get_metric_stats(results: Dict, metric: str) -> Dict[str, float]:
    """Read a metric from either single-process or multi-process result shapes."""
    if 'system' in results and metric in results['system']:
        return results['system'][metric]
    if metric in results and isinstance(results[metric], dict) and 'mean' in results[metric]:
        return results[metric]
    return {'mean': 0.0, 'std': 0.0}


def _get_fairness_value(results: Dict, metric: str) -> float:
    """Read a fairness metric from either scalar or mean/std result shapes."""
    fairness = results.get('fairness_metrics', {})
    value = fairness.get(metric, 0.0)
    if isinstance(value, dict) and 'mean' in value:
        return float(value['mean'])
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def plot_page_fault_curve(
    results_list: List[Dict],
    labels: List[str],
    output_file: str = "page_fault_comparison.png"
):
    """Plot page fault comparison across configurations."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(labels))
    means = [_get_metric_stats(results, 'page_faults')['mean'] for results in results_list]
    stds = [_get_metric_stats(results, 'page_faults')['std'] for results in results_list]

    ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7)
    ax.set_xlabel('Configuration')
    ax.set_ylabel('Page Faults')
    ax.set_title('Page Fault Comparison (Mean +/- Std)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to: {output_file}")


def plot_fairness_comparison(
    results_list: List[Dict],
    labels: List[str],
    output_file: str = "fairness_comparison.png"
):
    """Plot Jain's index and fairness variance."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    x = np.arange(len(labels))
    jains_indices = [_get_fairness_value(results, 'jains_index') for results in results_list]
    variances = [_get_fairness_value(results, 'variance') for results in results_list]

    axes[0].bar(x, jains_indices, alpha=0.7, color='green')
    axes[0].set_xlabel('Configuration')
    axes[0].set_ylabel("Jain's Fairness Index")
    axes[0].set_title('Fairness Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=45, ha='right')
    axes[0].set_ylim([0, 1])
    axes[0].grid(axis='y', alpha=0.3)

    axes[1].bar(x, variances, alpha=0.7, color='orange')
    axes[1].set_xlabel('Configuration')
    axes[1].set_ylabel('Variance')
    axes[1].set_title('Variance Comparison (Lower is Better)')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=45, ha='right')
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to: {output_file}")


def plot_memory_pressure_analysis(
    frames_range: List[int],
    page_faults: Dict[str, List[float]],
    output_file: str = "memory_pressure.png"
):
    """Plot page faults versus frame count for multiple algorithms."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for algorithm_name, faults in page_faults.items():
        ax.plot(frames_range, faults, marker='o', linewidth=2, label=algorithm_name)

    ax.set_xlabel('Number of Frames')
    ax.set_ylabel('Page Faults')
    ax.set_title('Page Faults vs Memory Size')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to: {output_file}")


def plot_slowdown_distribution(
    process_slowdowns: Dict[int, List[float]],
    output_file: str = "slowdown_distribution.png"
):
    """Plot slowdown distributions across processes."""
    fig, ax = plt.subplots(figsize=(10, 6))

    process_ids = sorted(process_slowdowns.keys())
    data = [process_slowdowns[pid] for pid in process_ids]
    boxplot = ax.boxplot(data, tick_labels=process_ids, patch_artist=True)

    for patch in boxplot['boxes']:
        patch.set_facecolor('lightblue')

    ax.set_xlabel('Process ID')
    ax.set_ylabel('Slowdown')
    ax.set_title('Slowdown Distribution by Process')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to: {output_file}")


def plot_algorithm_comparison_heatmap(
    results_matrix: np.ndarray,
    algorithms: List[str],
    allocations: List[str],
    output_file: str = "algorithm_heatmap.png"
):
    """Create a heatmap comparing algorithms and allocation policies."""
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(results_matrix, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(np.arange(len(allocations)))
    ax.set_yticks(np.arange(len(algorithms)))
    ax.set_xticklabels(allocations)
    ax.set_yticklabels(algorithms)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    for row_index, _ in enumerate(algorithms):
        for column_index, _ in enumerate(allocations):
            ax.text(
                column_index,
                row_index,
                f"{results_matrix[row_index, column_index]:.0f}",
                ha='center',
                va='center',
                color='black'
            )

    ax.set_title('Page Faults: Algorithm vs Allocation Policy')
    fig.colorbar(image, ax=ax, label='Page Faults')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Heatmap saved to: {output_file}")


def plot_confidence_intervals(
    comparisons: List[Dict],
    output_file: str = "confidence_intervals.png"
):
    """Plot confidence intervals for comparison results."""
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = [comparison.get('metric', 'Unknown') for comparison in comparisons]
    y_positions = np.arange(len(labels))

    for index, comparison in enumerate(comparisons):
        mean = comparison['difference']
        ci_lower, ci_upper = comparison['ci_95']
        ax.plot([ci_lower, ci_upper], [index, index], 'b-', linewidth=2)
        ax.plot(mean, index, 'bo', markersize=8)

    ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='No difference')
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Difference (Policy 1 - Policy 2)')
    ax.set_title('95% Confidence Intervals for Policy Comparisons')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to: {output_file}")


def create_summary_figure(
    results_list: List[Dict],
    labels: List[str],
    output_file: str = "summary_figure.png"
):
    """Create a summary figure with key system and fairness metrics."""
    figure = plt.figure(figsize=(14, 10))
    grid = figure.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    x = np.arange(len(labels))

    ax1 = figure.add_subplot(grid[0, :])
    fault_means = [_get_metric_stats(results, 'page_faults')['mean'] for results in results_list]
    fault_stds = [_get_metric_stats(results, 'page_faults')['std'] for results in results_list]
    ax1.bar(x, fault_means, yerr=fault_stds, capsize=5, alpha=0.7, color='steelblue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.set_ylabel('Page Faults')
    ax1.set_title('Page Faults Comparison')
    ax1.grid(axis='y', alpha=0.3)

    ax2 = figure.add_subplot(grid[1, 0])
    disk_means = [_get_metric_stats(results, 'total_disk_io')['mean'] for results in results_list]
    ax2.bar(x, disk_means, alpha=0.7, color='coral')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.set_ylabel('Total Disk I/O')
    ax2.set_title('Disk I/O Comparison')
    ax2.grid(axis='y', alpha=0.3)

    ax3 = figure.add_subplot(grid[1, 1])
    jains = [_get_fairness_value(results, 'jains_index') for results in results_list]
    ax3.bar(x, jains, alpha=0.7, color='green')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, rotation=45, ha='right')
    ax3.set_ylabel("Jain's Index")
    ax3.set_title('Fairness Comparison')
    ax3.set_ylim([0, 1])
    ax3.grid(axis='y', alpha=0.3)

    ax4 = figure.add_subplot(grid[2, 0])
    rates = [_get_metric_stats(results, 'page_fault_rate')['mean'] for results in results_list]
    ax4.bar(x, rates, alpha=0.7, color='purple')
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels, rotation=45, ha='right')
    ax4.set_ylabel('Page Fault Rate')
    ax4.set_title('Page Fault Rate Comparison')
    ax4.grid(axis='y', alpha=0.3)

    ax5 = figure.add_subplot(grid[2, 1])
    variances = [_get_fairness_value(results, 'variance') for results in results_list]
    ax5.bar(x, variances, alpha=0.7, color='orange')
    ax5.set_xticks(x)
    ax5.set_xticklabels(labels, rotation=45, ha='right')
    ax5.set_ylabel('Variance')
    ax5.set_title('Fairness Variance Comparison')
    ax5.grid(axis='y', alpha=0.3)

    plt.suptitle('Virtual Memory Experiment Summary', fontsize=14, fontweight='bold')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Summary figure saved to: {output_file}")


def generate_all_plots(results_dir: str, output_dir: str):
    """Generate all standard plots from result JSON files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results_list: List[Dict] = []
    labels: List[str] = []

    for json_file in Path(results_dir).glob("*.json"):
        with open(json_file, encoding='utf-8') as handle:
            results = json.load(handle)
        results_list.append(results)
        labels.append(json_file.stem.replace('_', '\n'))

    if not results_list:
        print(f"No JSON result files found in: {results_dir}")
        return

    create_summary_figure(
        results_list,
        labels,
        str(Path(output_dir) / "summary_figure.png")
    )
    plot_page_fault_curve(
        results_list,
        labels,
        str(Path(output_dir) / "page_fault_comparison.png")
    )
    plot_fairness_comparison(
        results_list,
        labels,
        str(Path(output_dir) / "fairness_comparison.png")
    )
