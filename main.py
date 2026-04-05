#!/usr/bin/env python3
"""
Virtual Memory Project - Main Entry Point
=========================================

Provides a simple command-line interface for running simulations
and experiments.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for direct script execution.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from analysis import generate_summary_report
from page_replacement import get_algorithm
from workload_generator import PREDEFINED_WORKLOADS, WorkloadGenerator


def run_simulation(args):
    """Run a single simulation."""
    print(f"\nRunning simulation with {args.algorithm} algorithm")
    print(f"Frames: {args.frames}")
    print(f"Workload: {args.workload}\n")

    config = PREDEFINED_WORKLOADS.get(args.workload)
    if config is None:
        print(f"Unknown workload: {args.workload}")
        print(f"Available: {list(PREDEFINED_WORKLOADS.keys())}")
        return

    trace = WorkloadGenerator(config).generate()
    algorithm = get_algorithm(args.algorithm, args.frames)

    for page_id, process_id, is_write in trace:
        algorithm.access_page(page_id, process_id, is_write)

    stats = algorithm.get_stats()
    print("\n" + "=" * 50)
    print("SIMULATION RESULTS")
    print("=" * 50)
    print(f"Total Accesses:    {len(trace):,}")
    print(f"Page Faults:       {stats['page_faults']:,}")
    print(f"Page Fault Rate:   {stats['page_faults'] / len(trace) * 100:.2f}%")
    print(f"Replacements:      {stats['page_replacements']:,}")
    print(f"Disk Reads:        {stats['disk_reads']:,}")
    print(f"Disk Writes:       {stats['disk_writes']:,}")
    print(f"Total Disk I/O:    {stats['total_disk_io']:,}")
    print("=" * 50)


def run_experiment(args):
    """Run experiment suites."""
    print("\nRunning experiments...")

    import experiments.run_all_experiments as exp

    experiment_runners = {
        "single": exp.run_single_process_experiments,
        "allocation": exp.run_allocation_policy_comparison,
        "pressure": exp.run_memory_pressure_experiments,
        "fairness": exp.run_fairness_focused_experiments,
        "thrashing": exp.run_thrashing_experiments,
        "trace": exp.run_trace_driven_experiments,
    }

    if args.final:
        exp.run_final_experiment_matrix(args.output, trace_files=args.trace_file)
    elif args.type == "all":
        for runner in experiment_runners.values():
            if runner is exp.run_trace_driven_experiments:
                runner(args.output, trace_files=args.trace_file)
            else:
                runner(args.output)
    else:
        runner = experiment_runners.get(args.type)
        if runner is None:
            print(f"Unknown experiment type: {args.type}")
            return
        if runner is exp.run_trace_driven_experiments:
            runner(args.output, trace_files=args.trace_file)
        else:
            runner(args.output)

    print(f"\nResults saved to: {args.output}")


def analyze_results(args):
    """Analyze existing JSON results."""
    results_dir = Path(args.input)

    if not results_dir.exists():
        print(f"Results directory not found: {args.input}")
        return

    print(f"\nAnalyzing results in: {args.input}\n")

    all_results = []
    for json_file in results_dir.glob("*.json"):
        with open(json_file, encoding="utf-8") as handle:
            results = json.load(handle)
        all_results.append(results)

        print(f"File: {json_file.name}")
        metric_group = results.get("system", results)
        for metric, stats in metric_group.items():
            if isinstance(stats, dict) and "mean" in stats:
                print(f"  {metric}: {stats['mean']:.2f} +/- {stats['std']:.2f}")
        print()

    if all_results:
        report_path = results_dir / "summary_report.txt"
        generate_summary_report(all_results, str(report_path))
        print(f"Summary report: {report_path}")


def generate_visualizations(args):
    """Generate plots from existing results."""
    from visualization import generate_all_plots

    print(f"\nGenerating visualizations from: {args.input}")
    print(f"Output directory: {args.output}\n")

    generate_all_plots(args.input, args.output)


def build_parser():
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Virtual Memory Project - Main Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py simulate --algorithm LRU --frames 50 --workload small_locality
  python main.py experiment --type all --output my_results
  python main.py analyze --input results
  python main.py visualize --input results --output figures
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    sim_parser = subparsers.add_parser("simulate", help="Run a single simulation")
    sim_parser.add_argument(
        "--algorithm",
        "-a",
        default="LRU",
        choices=["FIFO", "LRU", "NRU", "SecondChance", "WSClock"],
        help="Page replacement algorithm",
    )
    sim_parser.add_argument("--frames", "-f", type=int, default=50, help="Number of frames")
    sim_parser.add_argument(
        "--workload",
        "-w",
        default="small_locality",
        choices=list(PREDEFINED_WORKLOADS.keys()),
        help="Workload type",
    )

    exp_parser = subparsers.add_parser("experiment", help="Run experiments")
    exp_parser.add_argument(
        "--type",
        "-t",
        default="all",
        choices=["all", "single", "allocation", "pressure", "fairness", "thrashing", "trace"],
        help="Experiment type",
    )
    exp_parser.add_argument("--output", "-o", default="results", help="Output directory")
    exp_parser.add_argument(
        "--trace-file",
        action="append",
        help="Trace CSV file to use for trace-driven experiments. May be repeated.",
    )
    exp_parser.add_argument(
        "--final",
        action="store_true",
        help="Run the fixed final experiment matrix.",
    )

    ana_parser = subparsers.add_parser("analyze", help="Analyze results")
    ana_parser.add_argument("--input", "-i", default="results", help="Input directory with results")

    viz_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    viz_parser.add_argument("--input", "-i", default="results", help="Input directory with results")
    viz_parser.add_argument(
        "--output", "-o", default="results/figures", help="Output directory for figures"
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "simulate": run_simulation,
        "experiment": run_experiment,
        "analyze": analyze_results,
        "visualize": generate_visualizations,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
