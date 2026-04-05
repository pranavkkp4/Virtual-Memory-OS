"""Tests for trace ingestion and normalization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from trace_loader import TraceFormatError, load_trace_csv, load_trace_text
from trace_normalizer import address_to_page, normalize_trace_tuples, validate_trace


class TestTraceNormalization(unittest.TestCase):
    def test_address_to_page(self):
        self.assertEqual(address_to_page(0), 0)
        self.assertEqual(address_to_page(4095), 0)
        self.assertEqual(address_to_page(4096), 1)
        self.assertEqual(address_to_page(8192, page_size=2048), 4)

    def test_validate_trace(self):
        events = [(2, 1, 9, 0), (0, 0, 1, 1)]
        validated = validate_trace(events)
        self.assertEqual(validated, [(0, 0, 1, True), (2, 1, 9, False)])

    def test_invalid_event_rejected(self):
        with self.assertRaises(TraceFormatError):
            validate_trace([(0, -1, 1, True)])

    def test_legacy_tuple_rows(self):
        rows = [(3, 2, 1), (1, 2, 0)]
        normalized = normalize_trace_tuples(rows)
        self.assertEqual(normalized, [(0, 2, 3, True), (1, 2, 1, False)])


class TestTraceLoader(unittest.TestCase):
    def test_load_sample_trace_from_repo(self):
        trace_path = Path(__file__).resolve().parent.parent / "workloads" / "traces" / "sample_trace.csv"
        events = load_trace_csv(trace_path, page_size=4096)

        self.assertEqual(len(events), 8)
        self.assertEqual(events[0], (0, 0, 0, False))
        self.assertEqual(events[2], (2, 1, 1, True))
        self.assertEqual(events[-1], (7, 1, 3, False))

    def test_unsorted_header_trace_is_sorted(self):
        csv_text = """timestamp,process_id,address,is_write
        20,1,0x2000,1
        10,0,0x1000,0
        15,0,0x0000,1
        """

        events = load_trace_text(csv_text, page_size=4096)
        self.assertEqual(events, [(10, 0, 1, False), (15, 0, 0, True), (20, 1, 2, True)])

    def test_missing_page_or_address_rejected(self):
        csv_text = """timestamp,process_id,is_write
        0,0,1
        """

        with self.assertRaises(TraceFormatError):
            load_trace_text(csv_text)


if __name__ == "__main__":
    unittest.main()
