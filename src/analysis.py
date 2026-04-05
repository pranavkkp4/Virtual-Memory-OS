"""
Data Analysis and Statistical Testing
=====================================

Provides functions for:
- Statistical analysis of experiment results
- Fairness metrics calculation (Jain's index, variance)
- Slowdown calculations
- Hypothesis testing
"""

import csv
from typing import Dict, List

import numpy as np
from scipy import stats


def calculate_jains_fairness(values: List[float]) -> float:
    """
    Calculate Jain's fairness index.

    J = (sum(x_i))^2 / (n * sum(x_i^2))
    """
    if not values:
        return 1.0

    sum_x = float(sum(values))
    sum_x2 = float(sum(x ** 2 for x in values))
    n = len(values)

    if sum_x2 == 0:
        return 1.0

    return (sum_x ** 2) / (n * sum_x2)


def calculate_variance(values: List[float]) -> float:
    """Calculate variance of values with safe handling for tiny samples."""
    if len(values) < 2:
        return 0.0
    return float(np.var(values, ddof=1))


def calculate_slowdown(shared_time: float, isolated_time: float) -> float:
    """Calculate slowdown as shared runtime divided by isolated runtime."""
    if isolated_time == 0:
        return 1.0
    return shared_time / isolated_time


def _extract_fairness_values(process_metrics: Dict[int, Dict]) -> Dict[str, List[float]]:
    """Choose the best available fairness basis from per-process metrics."""
    def _collect(metric_name: str) -> List[float]:
        values: List[float] = []
        for metrics in process_metrics.values():
            if not isinstance(metrics, dict):
                continue

            value = metrics.get(metric_name)
            if isinstance(value, dict) and 'mean' in value:
                value = value['mean']

            if isinstance(value, (int, float, np.floating)):
                values.append(float(value))
        return values

    for basis in ('slowdown', 'page_fault_rate', 'page_faults', 'estimated_page_faults'):
        values = _collect(basis)
        if values:
            return {'basis': basis, 'values': values}

    return {'basis': 'none', 'values': []}


def calculate_fairness_metrics(process_metrics: Dict[int, Dict]) -> Dict:
    """
    Calculate fairness metrics for multiple processes.

    Slowdown is preferred when present. Otherwise the function falls back to
    page-fault-rate or page-fault-count proxies.
    """
    extracted = _extract_fairness_values(process_metrics)
    basis = extracted['basis']
    values = extracted['values']

    if not values:
        return {}

    if basis == 'slowdown':
        performance_values = [1.0 / max(value, 1e-10) for value in values]
    else:
        performance_values = [1.0 / (value + 1e-10) for value in values]

    mean_value = float(np.mean(values))
    std_value = float(np.std(values))

    return {
        'basis': basis,
        'jains_index': calculate_jains_fairness(performance_values),
        'variance': calculate_variance(values),
        'cv': (std_value / mean_value) if mean_value > 0 else 0.0,
        'max_ratio': (max(values) / min(values)) if min(values) > 0 else 1.0,
        'mean': mean_value,
        'std': std_value,
        'min': float(min(values)),
        'max': float(max(values))
    }


def perform_t_test(sample1: List[float], sample2: List[float], alpha: float = 0.05) -> Dict:
    """Perform Welch's two-sample t-test."""
    t_stat, p_value = stats.ttest_ind(sample1, sample2, equal_var=False)

    mean1, mean2 = float(np.mean(sample1)), float(np.mean(sample2))
    std1, std2 = float(np.std(sample1, ddof=1)), float(np.std(sample2, ddof=1))
    n1, n2 = len(sample1), len(sample2)

    se = np.sqrt(std1 ** 2 / n1 + std2 ** 2 / n2)
    df = (std1 ** 2 / n1 + std2 ** 2 / n2) ** 2 / (
        ((std1 ** 2 / n1) ** 2 / (n1 - 1)) + ((std2 ** 2 / n2) ** 2 / (n2 - 1))
    )

    t_crit = stats.t.ppf(1 - alpha / 2, df)
    diff = mean1 - mean2
    ci_lower = diff - t_crit * se
    ci_upper = diff + t_crit * se

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': bool(p_value < alpha),
        'mean1': mean1,
        'mean2': mean2,
        'difference': float(diff),
        'percent_difference': float((diff / mean2 * 100) if mean2 != 0 else 0.0),
        'ci_95': (float(ci_lower), float(ci_upper)),
        'alpha': alpha
    }


def perform_paired_t_test(before: List[float], after: List[float], alpha: float = 0.05) -> Dict:
    """Perform a paired t-test for before/after comparisons."""
    differences = [a - b for a, b in zip(after, before)]
    t_stat, p_value = stats.ttest_rel(after, before)

    mean_diff = float(np.mean(differences))
    std_diff = float(np.std(differences, ddof=1)) if len(differences) > 1 else 0.0
    se = (std_diff / np.sqrt(len(differences))) if differences else 0.0
    t_crit = stats.t.ppf(1 - alpha / 2, len(differences) - 1) if len(differences) > 1 else 0.0
    ci_lower = mean_diff - t_crit * se
    ci_upper = mean_diff + t_crit * se

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': bool(p_value < alpha),
        'mean_difference': mean_diff,
        'std_difference': std_diff,
        'ci_95': (float(ci_lower), float(ci_upper)),
        'percent_change': float((mean_diff / np.mean(before) * 100) if np.mean(before) != 0 else 0.0)
    }


def analyze_experiment_results(results: Dict) -> Dict:
    """Analyze experiment results and compute system and fairness metrics."""
    analysis = {
        'system_metrics': {},
        'fairness_metrics': {},
        'hypothesis_tests': {}
    }

    if 'system' in results:
        system_metrics = results['system']
    else:
        system_metrics = {
            key: value
            for key, value in results.items()
            if isinstance(value, dict) and 'mean' in value
        }

    for metric, values in system_metrics.items():
        if isinstance(values, dict) and 'mean' in values:
            analysis['system_metrics'][metric] = values

    if 'per_process' in results:
        analysis['fairness_metrics'] = calculate_fairness_metrics(results['per_process'])

    return analysis


def compare_policies(policy1_results: Dict, policy2_results: Dict, metric: str = 'page_faults') -> Dict:
    """Compare two policies using trial-level system metrics."""
    trials1 = [t['system_total'][metric] for t in policy1_results['trial_results']]
    trials2 = [t['system_total'][metric] for t in policy2_results['trial_results']]

    test_result = perform_t_test(trials1, trials2)
    return {
        'metric': metric,
        'policy1_mean': test_result['mean1'],
        'policy2_mean': test_result['mean2'],
        'difference': test_result['difference'],
        'percent_difference': test_result['percent_difference'],
        'p_value': test_result['p_value'],
        'significant': test_result['significant'],
        'ci_95': test_result['ci_95']
    }


def generate_summary_report(results_list: List[Dict], output_file: str = "summary_report.txt"):
    """Generate a text summary report for a mixed set of experiments."""
    with open(output_file, 'w', encoding='utf-8') as handle:
        handle.write("=" * 80 + "\n")
        handle.write("VIRTUAL MEMORY EXPERIMENT SUMMARY REPORT\n")
        handle.write("=" * 80 + "\n\n")

        for index, results in enumerate(results_list, start=1):
            handle.write(f"Experiment {index}\n")
            handle.write("-" * 40 + "\n")

            if 'config' in results:
                config = results['config']
                handle.write(f"Name: {config.get('name', 'N/A')}\n")
                handle.write(f"Algorithm: {config.get('algorithm', 'N/A')}\n")
                handle.write(f"Allocation: {config.get('allocation_policy', 'N/A')}\n")
                handle.write(f"Frames: {config.get('num_frames', 'N/A')}\n")

            if 'system' in results:
                system_metrics = results['system']
            else:
                system_metrics = {
                    key: value
                    for key, value in results.items()
                    if isinstance(value, dict) and 'mean' in value
                }

            if system_metrics:
                handle.write("\nSystem Metrics:\n")
                for metric, metric_stats in system_metrics.items():
                    if isinstance(metric_stats, dict) and 'mean' in metric_stats:
                        handle.write(
                            f"  {metric}: {metric_stats['mean']:.2f} +/- {metric_stats['std']:.2f}\n"
                        )

            fairness_metrics = results.get('fairness_metrics')
            if fairness_metrics:
                handle.write("\nFairness Metrics:\n")
                for key, value in fairness_metrics.items():
                    if isinstance(value, float):
                        handle.write(f"  {key}: {value:.4f}\n")
                    else:
                        handle.write(f"  {key}: {value}\n")

            handle.write("\n")

        handle.write("=" * 80 + "\n")
        handle.write("END OF REPORT\n")
        handle.write("=" * 80 + "\n")

    print(f"Summary report saved to: {output_file}")


def export_results_csv(results: Dict, filename: str):
    """Export trial results to CSV for either single- or multi-process runs."""
    with open(filename, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)

        if not results.get('trial_results'):
            writer.writerow(['message'])
            writer.writerow(['No trial results available'])
            return

        sample_trial = results['trial_results'][0]
        if 'system_total' in sample_trial:
            writer.writerow([
                'Trial',
                'Page Faults',
                'Replacements',
                'Disk Reads',
                'Disk Writes',
                'Total Disk IO'
            ])
            for trial in results['trial_results']:
                writer.writerow([
                    trial['trial'],
                    trial['system_total']['page_faults'],
                    trial['system_total']['page_replacements'],
                    trial['system_total']['disk_reads'],
                    trial['system_total']['disk_writes'],
                    trial['system_total']['total_disk_io']
                ])
        else:
            writer.writerow([
                'Trial',
                'Page Faults',
                'Replacements',
                'Disk Reads',
                'Disk Writes',
                'Total Disk IO',
                'Page Fault Rate',
                'Throughput'
            ])
            for trial in results['trial_results']:
                writer.writerow([
                    trial['trial'],
                    trial['page_faults'],
                    trial['page_replacements'],
                    trial['disk_reads'],
                    trial['disk_writes'],
                    trial['total_disk_io'],
                    trial['page_fault_rate'],
                    trial.get('throughput', 0.0)
                ])

    print(f"CSV exported to: {filename}")
