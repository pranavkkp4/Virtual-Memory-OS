"""Regression tests for CLI, trace, workload, and analysis edge cases."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import main
from experiments.run_all_experiments import resolve_trace_files
from page_replacement import FIFO
from scripts.validate_results import _trial_process_ids
from src.analysis import perform_t_test
from trace_loader import load_trace_text
from workload_generator import (
    MultiProcessWorkloadGenerator,
    WorkloadConfig,
    WorkloadGenerator,
    WorkloadType,
)


class TestActionableRegressions(unittest.TestCase):
    def test_validate_results_accepts_numeric_string_process_ids(self):
        process_ids = _trial_process_ids({"0": {}, "1": {}, "worker": {}})
        self.assertEqual(process_ids, [0, 1])

    def test_frames_must_be_positive(self):
        parser = main.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["simulate", "--frames", "0"])
        with self.assertRaises(ValueError):
            FIFO(0)

    def test_missing_trace_paths_are_validated(self):
        with self.assertRaises(FileNotFoundError):
            resolve_trace_files(["missing_trace_file.csv"])

    def test_trace_headers_are_case_insensitive(self):
        csv_text = """Timestamp,Process_ID,Address,Is_Write
        2,1,0x2000,1
        1,0,0x1000,0
        """
        events = load_trace_text(csv_text, page_size=4096)
        self.assertEqual(events, [(1, 0, 1, False), (2, 1, 2, True)])

    def test_mixed_workload_emits_exact_requested_count(self):
        config = WorkloadConfig(
            workload_type=WorkloadType.MIXED,
            num_pages=20,
            num_accesses=11,
            working_set_size=5,
            seed=7,
        )
        self.assertEqual(len(WorkloadGenerator(config).generate()), 11)

    def test_high_locality_pages_stay_in_range_when_wss_exceeds_pages(self):
        config = WorkloadConfig(
            workload_type=WorkloadType.HIGH_LOCALITY,
            num_pages=3,
            num_accesses=100,
            working_set_size=10,
            seed=1,
        )
        pages = [page_id for page_id, _, _ in WorkloadGenerator(config).generate()]
        self.assertTrue(all(0 <= page_id < config.num_pages for page_id in pages))

    def test_workload_generator_seed_does_not_touch_global_random_state(self):
        config_a = WorkloadConfig(
            workload_type=WorkloadType.RANDOM,
            num_pages=10,
            num_accesses=20,
            seed=123,
        )
        config_b = WorkloadConfig(
            workload_type=WorkloadType.RANDOM,
            num_pages=10,
            num_accesses=20,
            seed=999,
        )

        generator_a = WorkloadGenerator(config_a)
        generator_b = WorkloadGenerator(config_b)
        generator_b.generate()

        self.assertEqual(generator_a.generate(), WorkloadGenerator(config_a).generate())

    def test_multiprocess_generator_keeps_process_seeds_isolated(self):
        process_zero = WorkloadConfig(
            workload_type=WorkloadType.RANDOM,
            num_pages=10,
            num_accesses=20,
            seed=0,
        )
        process_one = WorkloadConfig(
            workload_type=WorkloadType.RANDOM,
            num_pages=10,
            num_accesses=20,
            seed=999,
        )

        expected_process_zero_trace = WorkloadGenerator(process_zero).generate()
        generator = MultiProcessWorkloadGenerator({0: process_zero, 1: process_one})
        generator.generate(interleave="round_robin")

        self.assertEqual(generator.last_process_traces[0], expected_process_zero_trace)

    def test_t_test_handles_insufficient_samples(self):
        result = perform_t_test([1.0], [2.0])
        self.assertFalse(result["significant"])
        self.assertTrue(result["insufficient_samples"])
        self.assertEqual(result["mean1"], 1.0)
        self.assertEqual(result["mean2"], 2.0)


if __name__ == "__main__":
    unittest.main()
