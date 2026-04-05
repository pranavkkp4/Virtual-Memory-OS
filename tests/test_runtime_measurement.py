"""Tests for runtime measurement helpers."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import runtime_measurement as rm


class TestRuntimeMeasurement(unittest.TestCase):
    def test_measure_repeated_discards_warmups(self):
        calls = []
        counter = {"value": 0}

        def fake_perf_counter_ns():
            counter["value"] += 10
            return counter["value"]

        def target():
            calls.append(len(calls))
            return "ok"

        original_perf_counter_ns = rm.perf_counter_ns
        rm.perf_counter_ns = fake_perf_counter_ns
        try:
            summary = rm.measure_repeated(target, repeats=3, warmup_runs=2, label="demo")
        finally:
            rm.perf_counter_ns = original_perf_counter_ns

        self.assertEqual(len(calls), 5)
        self.assertEqual(summary.warmup_runs, 2)
        self.assertEqual(summary.measured_runs, 3)
        self.assertEqual(summary.durations_ns, [10, 10, 10])

    def test_summary_median_and_serialization(self):
        summary = rm.RuntimeSummary(
            label="sample",
            warmup_runs=1,
            measured_runs=4,
            durations_ns=[40, 10, 30, 20],
            metadata={"algorithm": "LRU"},
        )

        payload = summary.to_dict()
        self.assertEqual(payload["median_ns"], 25)
        self.assertEqual(payload["mean_ns"], 25.0)
        self.assertEqual(payload["durations_ms"], [4e-05, 1e-05, 3e-05, 2e-05])
        json.dumps(payload)

    def test_runtime_record_and_summary_records(self):
        record1 = rm.build_runtime_record(
            mode="isolation",
            process_id=1,
            workload_name="trace_a",
            algorithm="LRU",
            allocation_policy="LocalAllocation",
            memory_frames=50,
            repetition_id=0,
            duration_ns=1234567,
            metadata={"host": "test"},
        )
        record2 = rm.build_runtime_record(
            mode="shared",
            process_id=1,
            workload_name="trace_a",
            algorithm="LRU",
            allocation_policy="LocalAllocation",
            memory_frames=50,
            repetition_id=1,
            duration_ns=7654321,
        )

        self.assertEqual(record1.to_dict()["duration_ms"], 1.234567)
        summary = rm.summarize_records([record1, record2])
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["median_ns"], 4444444)
        json.dumps(summary)

    def test_invalid_repeat_configuration(self):
        with self.assertRaises(ValueError):
            rm.measure_repeated(lambda: None, repeats=0)

        with self.assertRaises(ValueError):
            rm.measure_repeated(lambda: None, warmup_runs=-1)


if __name__ == "__main__":
    unittest.main()
