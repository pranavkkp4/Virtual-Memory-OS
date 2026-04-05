"""Integration tests for trace-driven experiment plumbing."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from experiment_runner import MultiProcessExperimentRunner


class TestTracePipeline(unittest.TestCase):
    """Verify the shared trace-driven path records runtime and slowdown data."""

    def test_trace_runner_records_runtime_and_slowdown(self):
        trace_file = (
            Path(__file__).resolve().parent.parent
            / "workloads"
            / "traces"
            / "sample_trace.csv"
        )

        runner = MultiProcessExperimentRunner(
            algorithm="LRU",
            allocation_policy="GlobalAllocation",
            total_frames=4,
            trace_file=str(trace_file),
            num_trials=1,
            warmup_runs=0,
            workload_label="trace",
        )
        result = runner.run()

        self.assertEqual(result["config"]["workload_kind"], "trace")
        self.assertEqual(result["config"]["trace_name"], "sample_trace")
        self.assertIn("fairness_metrics", result)
        self.assertEqual(result["fairness_metrics"]["basis"], "slowdown")

        trial = result["trial_results"][0]
        self.assertGreater(trial["runtime_ms"], 0.0)
        self.assertGreater(len(trial["runtime_records"]), 0)

        for process_metrics in trial["per_process"].values():
            self.assertIn("shared_runtime_ms", process_metrics)
            self.assertIn("isolated_runtime_ms", process_metrics)
            self.assertIn("slowdown", process_metrics)
            self.assertGreaterEqual(process_metrics["slowdown"], 0.0)


if __name__ == "__main__":
    unittest.main()
