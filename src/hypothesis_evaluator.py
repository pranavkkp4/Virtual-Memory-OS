"""
Hypothesis evaluation for the virtual memory project.

This module converts measured experiment summaries into explicit
Supported / Partially supported / Not supported decisions for H1-H3.
It is intentionally self-contained so it can be used from reports,
CSV exports, or downstream scripts without depending on the analysis
or experiment runner modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Literal, Optional

OutcomeLabel = Literal["Supported", "Partially supported", "Not supported"]
Direction = Literal["increase", "decrease"]
RuleKind = Literal["primary", "context"]


def _safe_percent_change(baseline: float, comparison: float) -> Optional[float]:
    """Return percent change from baseline to comparison, or None if undefined."""
    if baseline == 0:
        if comparison == 0:
            return 0.0
        return None
    return ((comparison - baseline) / baseline) * 100.0


def _safe_percent_difference(baseline: float, comparison: float) -> Optional[float]:
    """Return percent improvement relative to baseline for lower-is-better metrics."""
    if baseline == 0:
        if comparison == 0:
            return 0.0
        return None
    return ((baseline - comparison) / baseline) * 100.0


@dataclass(frozen=True)
class MetricRule:
    """One metric-level rule used to evaluate a hypothesis."""

    metric: str
    baseline_label: str
    comparison_label: str
    baseline_value: float
    comparison_value: float
    threshold_percent: float
    expected_direction: Direction
    kind: RuleKind = "primary"
    note: str = ""

    def percent_change(self) -> Optional[float]:
        return _safe_percent_change(self.baseline_value, self.comparison_value)

    def percent_improvement(self) -> Optional[float]:
        return _safe_percent_difference(self.baseline_value, self.comparison_value)

    def direction_ok(self) -> Optional[bool]:
        change = self.percent_change()
        if change is None:
            return None
        if self.expected_direction == "increase":
            return change > 0
        return change < 0

    def threshold_met(self) -> Optional[bool]:
        change = self.percent_change()
        if change is None:
            return None
        magnitude = abs(change)
        return magnitude >= self.threshold_percent

    def outcome(self) -> OutcomeLabel:
        direction = self.direction_ok()
        threshold = self.threshold_met()
        if direction is False or threshold is False:
            if direction is False:
                return "Not supported"
            return "Partially supported"
        if direction is None or threshold is None:
            return "Not supported"
        if direction and threshold:
            return "Supported"
        if direction:
            return "Partially supported"
        return "Not supported"

    def to_row(self) -> Dict[str, object]:
        change = self.percent_change()
        improvement = self.percent_improvement()
        return {
            "metric": self.metric,
            "baseline_label": self.baseline_label,
            "comparison_label": self.comparison_label,
            "baseline_value": self.baseline_value,
            "comparison_value": self.comparison_value,
            "percent_change": change,
            "percent_improvement": improvement,
            "threshold_percent": self.threshold_percent,
            "expected_direction": self.expected_direction,
            "direction_ok": self.direction_ok(),
            "threshold_met": self.threshold_met(),
            "outcome": self.outcome(),
            "kind": self.kind,
            "note": self.note,
        }


@dataclass(frozen=True)
class HypothesisResult:
    """Aggregate outcome for a hypothesis."""

    hypothesis: str
    test_condition: str
    rules: List[MetricRule] = field(default_factory=list)

    def primary_rules(self) -> List[MetricRule]:
        return [rule for rule in self.rules if rule.kind == "primary"]

    def contextual_rules(self) -> List[MetricRule]:
        return [rule for rule in self.rules if rule.kind != "primary"]

    def outcome(self) -> OutcomeLabel:
        primary_rules = self.primary_rules()
        if not primary_rules:
            return "Not supported"

        direction_states = [rule.direction_ok() for rule in primary_rules]
        threshold_states = [rule.threshold_met() for rule in primary_rules]

        if any(state is False for state in direction_states):
            return "Not supported"
        if any(state is None for state in direction_states + threshold_states):
            return "Not supported"

        if all(direction_states) and all(threshold_states):
            return "Supported"
        if all(direction_states):
            return "Partially supported"
        return "Not supported"

    def to_dict(self) -> Dict[str, object]:
        primary = self.primary_rules()
        main_rule = primary[0] if primary else None
        return {
            "hypothesis": self.hypothesis,
            "test_condition": self.test_condition,
            "outcome": self.outcome(),
            "rules": [rule.to_row() for rule in self.rules],
            "main_metric": main_rule.metric if main_rule else "",
            "main_baseline_value": main_rule.baseline_value if main_rule else None,
            "main_comparison_value": main_rule.comparison_value if main_rule else None,
            "main_percent_change": main_rule.percent_change() if main_rule else None,
            "main_threshold_percent": main_rule.threshold_percent if main_rule else None,
        }

    def to_csv_row(self) -> Dict[str, object]:
        """Flattened row suitable for CSV or table export."""
        data = self.to_dict()
        rule_parts = []
        for rule in self.rules:
            change = rule.percent_change()
            pct = "n/a" if change is None else f"{change:.2f}%"
            rule_parts.append(f"{rule.metric}:{pct}")

        data["rules_summary"] = "; ".join(rule_parts)
        data["rule_count"] = len(self.rules)
        return data


def evaluate_hypothesis(
    hypothesis: str,
    test_condition: str,
    rules: Iterable[MetricRule],
) -> HypothesisResult:
    """Evaluate a hypothesis from a collection of metric rules."""
    return HypothesisResult(
        hypothesis=hypothesis,
        test_condition=test_condition,
        rules=list(rules),
    )


def evaluate_h1(
    *,
    high_locality_condition: str,
    lru_global_faults: float,
    lru_local_faults: float,
    lru_global_worst_slowdown: float,
    lru_local_worst_slowdown: float,
    slowdown_threshold_percent: float = 30.0,
) -> HypothesisResult:
    """Evaluate H1 using fault reduction and slowdown increase rules."""
    rules = [
        MetricRule(
            metric="page_faults",
            baseline_label="LRU+Local",
            comparison_label="LRU+Global",
            baseline_value=lru_local_faults,
            comparison_value=lru_global_faults,
            threshold_percent=0.0,
            expected_direction="decrease",
            kind="primary",
            note="Global allocation should lower total faults",
        ),
        MetricRule(
            metric="worst_slowdown",
            baseline_label="LRU+Local",
            comparison_label="LRU+Global",
            baseline_value=lru_local_worst_slowdown,
            comparison_value=lru_global_worst_slowdown,
            threshold_percent=slowdown_threshold_percent,
            expected_direction="increase",
            kind="primary",
            note="Global allocation may slow down the worst process",
        ),
    ]
    return evaluate_hypothesis("H1", high_locality_condition, rules)


def evaluate_h2(
    *,
    memory_pressure_condition: str,
    global_slowdown_variance: float,
    local_slowdown_variance: float,
    variance_threshold_percent: float = 15.0,
) -> HypothesisResult:
    """Evaluate H2 using slowdown variance under global vs local allocation."""
    rules = [
        MetricRule(
            metric="slowdown_variance",
            baseline_label="Local",
            comparison_label="Global",
            baseline_value=local_slowdown_variance,
            comparison_value=global_slowdown_variance,
            threshold_percent=variance_threshold_percent,
            expected_direction="increase",
            kind="primary",
            note="Global allocation should increase slowdown variance near the WSS boundary",
        )
    ]
    return evaluate_hypothesis("H2", memory_pressure_condition, rules)


def evaluate_h3(
    *,
    heterogeneous_workload_condition: str,
    simple_local_worst_slowdown: float,
    advanced_global_worst_slowdown: float,
    slowdown_threshold_percent: float = 15.0,
    simple_local_faults: Optional[float] = None,
    advanced_global_faults: Optional[float] = None,
) -> HypothesisResult:
    """Evaluate H3 using worst-case slowdown reduction for simple/local policies."""
    rules = [
        MetricRule(
            metric="worst_slowdown",
            baseline_label="LRU/WSClock+Global",
            comparison_label="FIFO/NRU+Local",
            baseline_value=advanced_global_worst_slowdown,
            comparison_value=simple_local_worst_slowdown,
            threshold_percent=slowdown_threshold_percent,
            expected_direction="decrease",
            kind="primary",
            note="Simple local policies should reduce worst-case slowdown",
        )
    ]

    if simple_local_faults is not None and advanced_global_faults is not None:
        rules.append(
            MetricRule(
                metric="page_faults",
                baseline_label="FIFO/NRU+Local",
                comparison_label="LRU/WSClock+Global",
                baseline_value=simple_local_faults,
                comparison_value=advanced_global_faults,
                threshold_percent=0.0,
                expected_direction="increase",
                kind="context",
                note="Higher faults are acceptable if fairness improves",
            )
        )

    return evaluate_hypothesis("H3", heterogeneous_workload_condition, rules)


def evaluation_table(results: Iterable[HypothesisResult]) -> List[Dict[str, object]]:
    """Return CSV/table-friendly rows for a collection of results."""
    return [result.to_csv_row() for result in results]


def summarize_outcomes(results: Iterable[HypothesisResult]) -> Dict[str, int]:
    """Count the number of outcomes by label."""
    summary = {
        "Supported": 0,
        "Partially supported": 0,
        "Not supported": 0,
    }
    for result in results:
        summary[result.outcome()] += 1
    return summary
