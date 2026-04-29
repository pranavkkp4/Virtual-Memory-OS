#!/usr/bin/env python3
"""Verify and rebuild the final report-facing artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PROCESSED_FILES = [
    REPO_ROOT / "results" / "processed" / "final_aggregate_results.csv",
    REPO_ROOT / "results" / "processed" / "final_aggregate_results.json",
    REPO_ROOT / "results" / "processed" / "slowdown_metrics.csv",
    REPO_ROOT / "results" / "processed" / "hypothesis_evaluation.csv",
    REPO_ROOT / "results" / "processed" / "hypothesis_evaluation.md",
    REPO_ROOT / "results" / "processed" / "validation_report.json",
    REPO_ROOT / "results" / "processed" / "validation_issues.csv",
]

REPORT_TABLE_SCRIPT = REPO_ROOT / "scripts" / "build_report_tables.py"
REPORT_FIGURE_SCRIPT = REPO_ROOT / "scripts" / "build_report_figures.py"
HYPOTHESIS_SUMMARY_MD = REPO_ROOT / "results" / "tables" / "hypothesis_summary.md"
FINAL_DEMO_BUNDLE = REPO_ROOT / "results" / "demo" / "final_bundle"
SOURCE_BEST_POLICY_TABLE = REPO_ROOT / "results" / "tables" / "best_policy_by_workload.csv"
BUNDLE_BEST_POLICY_TABLE = FINAL_DEMO_BUNDLE / "tables" / "best_policy_by_workload.csv"
BUNDLE_MANIFEST = FINAL_DEMO_BUNDLE / "metadata" / "bundle_manifest.json"


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def _missing_or_empty(paths: Iterable[Path]) -> List[Path]:
    return [path for path in paths if not path.is_file() or path.stat().st_size == 0]


def check_required_processed_files() -> CheckResult:
    missing = _missing_or_empty(REQUIRED_PROCESSED_FILES)
    if missing:
        detail = "missing or empty: " + ", ".join(_relative(path) for path in missing)
        return CheckResult("required processed files", False, detail)
    return CheckResult("required processed files", True, f"{len(REQUIRED_PROCESSED_FILES)} files present")


def run_builder(script: Path) -> CheckResult:
    if not script.is_file():
        return CheckResult(_relative(script), False, "script not found")

    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    name = _relative(script)
    if completed.returncode == 0:
        return CheckResult(name, True, "completed")

    output = (completed.stderr or completed.stdout or "").strip()
    if output:
        output = output.splitlines()[-1]
    else:
        output = f"exit code {completed.returncode}"
    return CheckResult(name, False, output)


def check_hypothesis_summary() -> CheckResult:
    if HYPOTHESIS_SUMMARY_MD.is_file() and HYPOTHESIS_SUMMARY_MD.stat().st_size > 0:
        return CheckResult("hypothesis summary table", True, _relative(HYPOTHESIS_SUMMARY_MD))
    return CheckResult("hypothesis summary table", False, f"missing or empty: {_relative(HYPOTHESIS_SUMMARY_MD)}")


def check_final_demo_bundle() -> CheckResult:
    if not FINAL_DEMO_BUNDLE.is_dir():
        return CheckResult("final demo bundle", False, f"directory not found: {_relative(FINAL_DEMO_BUNDLE)}")

    files = [path for path in FINAL_DEMO_BUNDLE.rglob("*") if path.is_file() and path.stat().st_size > 0]
    if not files:
        return CheckResult("final demo bundle", False, f"no non-empty files under {_relative(FINAL_DEMO_BUNDLE)}")

    return CheckResult("final demo bundle", True, f"{len(files)} non-empty files under {_relative(FINAL_DEMO_BUNDLE)}")


def check_demo_bundle_matches_final_outputs() -> CheckResult:
    if not SOURCE_BEST_POLICY_TABLE.is_file():
        return CheckResult("demo bundle table sync", False, f"source table missing: {_relative(SOURCE_BEST_POLICY_TABLE)}")
    if not BUNDLE_BEST_POLICY_TABLE.is_file():
        return CheckResult("demo bundle table sync", False, f"bundle table missing: {_relative(BUNDLE_BEST_POLICY_TABLE)}")
    if SOURCE_BEST_POLICY_TABLE.read_bytes() != BUNDLE_BEST_POLICY_TABLE.read_bytes():
        return CheckResult(
            "demo bundle table sync",
            False,
            f"{_relative(BUNDLE_BEST_POLICY_TABLE)} differs from {_relative(SOURCE_BEST_POLICY_TABLE)}",
        )
    return CheckResult("demo bundle table sync", True, "best_policy_by_workload.csv matches final table")


def check_demo_manifest() -> CheckResult:
    if not BUNDLE_MANIFEST.is_file() or BUNDLE_MANIFEST.stat().st_size == 0:
        return CheckResult("demo bundle manifest", False, f"missing or empty: {_relative(BUNDLE_MANIFEST)}")

    try:
        data = json.loads(BUNDLE_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult("demo bundle manifest", False, f"invalid JSON: {exc}")

    files = set(data.get("files", []))
    manifest_rel = "metadata/bundle_manifest.json"
    if manifest_rel not in files:
        return CheckResult("demo bundle manifest", False, f"manifest omits {manifest_rel}")

    return CheckResult("demo bundle manifest", True, f"{len(files)} manifest entries")


def print_summary(results: Iterable[CheckResult]) -> bool:
    result_list = list(results)
    for result in result_list:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    passed = sum(1 for result in result_list if result.passed)
    failed = len(result_list) - passed
    overall = failed == 0
    print(f"Summary: {'PASS' if overall else 'FAIL'} ({passed} passed, {failed} failed)")
    return overall


def main() -> int:
    results = [
        check_required_processed_files(),
        run_builder(REPORT_TABLE_SCRIPT),
        run_builder(REPORT_FIGURE_SCRIPT),
        check_hypothesis_summary(),
        check_final_demo_bundle(),
        check_demo_bundle_matches_final_outputs(),
        check_demo_manifest(),
    ]
    return 0 if print_summary(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
