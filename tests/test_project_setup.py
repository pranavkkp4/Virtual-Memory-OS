"""Project-level regression tests."""

import shutil
import unittest
from pathlib import Path

import main
from src.analysis import analyze_experiment_results, generate_summary_report
from src.frame_allocation import GlobalAllocation, LocalAllocation
from src.visualization import create_summary_figure


class TestProjectSetup(unittest.TestCase):
    """Verify core project setup paths work."""

    def setUp(self):
        self.workspace_tmp = Path(__file__).resolve().parent / "_tmp"
        self.workspace_tmp.mkdir(exist_ok=True)

    def tearDown(self):
        if self.workspace_tmp.exists():
            shutil.rmtree(self.workspace_tmp, ignore_errors=True)

    def test_imports_and_parser(self):
        parser = main.build_parser()
        args = parser.parse_args(["experiment", "--type", "allocation"])
        self.assertEqual(args.command, "experiment")
        self.assertEqual(args.type, "allocation")

        self.assertIsInstance(GlobalAllocation(total_frames=10), GlobalAllocation)
        self.assertIsInstance(LocalAllocation(total_frames=10), LocalAllocation)

    def test_analysis_handles_single_process_schema(self):
        results = {
            "config": {
                "name": "smoke",
                "algorithm": "LRU",
                "allocation_policy": "LocalAllocation",
                "num_frames": 8,
            },
            "page_faults": {"mean": 10.0, "std": 1.0},
            "page_replacements": {"mean": 2.0, "std": 0.5},
            "disk_reads": {"mean": 10.0, "std": 1.0},
            "disk_writes": {"mean": 1.0, "std": 0.2},
            "total_disk_io": {"mean": 11.0, "std": 1.1},
            "page_fault_rate": {"mean": 0.25, "std": 0.01},
            "trial_results": [{"trial": 0, "page_fault_rate": 0.25}],
        }

        analysis = analyze_experiment_results(results)
        self.assertIn("page_faults", analysis["system_metrics"])

        report_dir = self.workspace_tmp / "report"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "summary_report.txt"
        generate_summary_report([results], str(report_path))
        self.assertTrue(report_path.exists())
        self.assertIn("page_faults", report_path.read_text(encoding="utf-8"))

    def test_summary_figure_handles_single_process_schema(self):
        results = {
            "page_faults": {"mean": 10.0, "std": 1.0},
            "total_disk_io": {"mean": 11.0, "std": 1.1},
            "trial_results": [{"trial": 0, "page_fault_rate": 0.25}],
        }

        figure_dir = self.workspace_tmp / "figures"
        figure_dir.mkdir(parents=True, exist_ok=True)
        output_path = figure_dir / "summary.png"
        create_summary_figure([results], ["single"], str(output_path))
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
