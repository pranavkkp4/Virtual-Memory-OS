"""Tests for hypothesis evaluation."""

import unittest

from src.hypothesis_evaluator import (
    MetricRule,
    evaluate_h1,
    evaluate_h2,
    evaluate_h3,
    evaluation_table,
    summarize_outcomes,
)


class TestMetricRule(unittest.TestCase):
    def test_increase_threshold_supported(self):
        rule = MetricRule(
            metric="variance",
            baseline_label="Local",
            comparison_label="Global",
            baseline_value=100.0,
            comparison_value=117.0,
            threshold_percent=15.0,
            expected_direction="increase",
        )
        self.assertAlmostEqual(rule.percent_change(), 17.0)
        self.assertTrue(rule.direction_ok())
        self.assertTrue(rule.threshold_met())
        self.assertEqual(rule.outcome(), "Supported")

    def test_increase_threshold_partial(self):
        rule = MetricRule(
            metric="variance",
            baseline_label="Local",
            comparison_label="Global",
            baseline_value=100.0,
            comparison_value=110.0,
            threshold_percent=15.0,
            expected_direction="increase",
        )
        self.assertEqual(rule.outcome(), "Partially supported")

    def test_wrong_direction_not_supported(self):
        rule = MetricRule(
            metric="variance",
            baseline_label="Local",
            comparison_label="Global",
            baseline_value=100.0,
            comparison_value=90.0,
            threshold_percent=15.0,
            expected_direction="increase",
        )
        self.assertEqual(rule.outcome(), "Not supported")


class TestHypothesisEvaluation(unittest.TestCase):
    def test_h1_supported(self):
        result = evaluate_h1(
            high_locality_condition="high locality at 1.2x WSS",
            lru_global_faults=880.0,
            lru_local_faults=1000.0,
            lru_global_worst_slowdown=1.34,
            lru_local_worst_slowdown=1.00,
        )
        self.assertEqual(result.outcome(), "Supported")

        row = result.to_csv_row()
        self.assertEqual(row["hypothesis"], "H1")
        self.assertEqual(row["outcome"], "Supported")
        self.assertIn("page_faults", row["rules_summary"])

    def test_h1_partial_when_slowdown_below_threshold(self):
        result = evaluate_h1(
            high_locality_condition="high locality at 1.2x WSS",
            lru_global_faults=880.0,
            lru_local_faults=1000.0,
            lru_global_worst_slowdown=1.20,
            lru_local_worst_slowdown=1.00,
        )
        self.assertEqual(result.outcome(), "Partially supported")

    def test_h2_supported(self):
        result = evaluate_h2(
            memory_pressure_condition="near WSS boundary",
            global_slowdown_variance=117.0,
            local_slowdown_variance=100.0,
        )
        self.assertEqual(result.outcome(), "Supported")

    def test_h3_partial_and_contextual_fault_note(self):
        result = evaluate_h3(
            heterogeneous_workload_condition="mixed workloads",
            simple_local_worst_slowdown=1.134,
            advanced_global_worst_slowdown=1.30,
            simple_local_faults=1200.0,
            advanced_global_faults=1100.0,
        )
        self.assertEqual(result.outcome(), "Partially supported")

        row = result.to_csv_row()
        self.assertEqual(row["hypothesis"], "H3")
        self.assertEqual(row["rule_count"], 2)
        self.assertIn("worst_slowdown", row["rules_summary"])

    def test_table_and_summary_helpers(self):
        h1 = evaluate_h1(
            high_locality_condition="high locality at 1.2x WSS",
            lru_global_faults=880.0,
            lru_local_faults=1000.0,
            lru_global_worst_slowdown=1.34,
            lru_local_worst_slowdown=1.00,
        )
        h2 = evaluate_h2(
            memory_pressure_condition="near WSS boundary",
            global_slowdown_variance=117.0,
            local_slowdown_variance=100.0,
        )
        h3 = evaluate_h3(
            heterogeneous_workload_condition="mixed workloads",
            simple_local_worst_slowdown=1.134,
            advanced_global_worst_slowdown=1.30,
        )

        table = evaluation_table([h1, h2, h3])
        self.assertEqual([row["hypothesis"] for row in table], ["H1", "H2", "H3"])

        summary = summarize_outcomes([h1, h2, h3])
        self.assertEqual(summary["Supported"], 2)
        self.assertEqual(summary["Partially supported"], 1)
        self.assertEqual(summary["Not supported"], 0)


if __name__ == "__main__":
    unittest.main()
