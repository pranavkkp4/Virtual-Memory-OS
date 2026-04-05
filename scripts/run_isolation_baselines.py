#!/usr/bin/env python3
"""Run reproducible isolated-runtime baselines and summarize their stability."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, Iterable, List, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "results" / "baselines_20260404"
DEFAULT_TRACE_FILE = REPO_ROOT / "workloads" / "traces" / "sample_trace.csv"
DEFAULT_REPETITIONS = 8
STABILITY_CV_THRESHOLD = 0.10
TIGHT_CV_THRESHOLD = 0.05


@dataclass(frozen=True)
class BaselineProfile:
    """Single benchmark session to run under a specific control wrapper."""

    name: str
    wrapper: str
    benchmark_args: Sequence[str]
    results_subdir: str
    pinned_cores: Sequence[int] = ()


def _powershell_exe() -> str:
    for candidate in ("powershell", "powershell.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Unable to locate PowerShell for benchmark orchestration.")


def _shell_exe() -> str:
    if os.name == "nt":
        return _powershell_exe()
    for candidate in ("bash", "sh"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("Unable to locate a shell for benchmark orchestration.")


def _build_wrapper_command(profile: BaselineProfile, output_root: Path) -> List[str]:
    session_dir_rel = Path("results") / "baselines_20260404" / profile.results_subdir
    benchmark_args = list(profile.benchmark_args) + ["--output-dir", str(session_dir_rel)]

    if os.name == "nt":
        wrapper_name = "run_pinned.ps1" if profile.wrapper == "pinned" else "run_quiet_benchmark.ps1"
        wrapper = REPO_ROOT / "scripts" / wrapper_name
        wrapper_bits = [f"& '{wrapper}'"]
        if profile.wrapper == "pinned":
            cores = ",".join(str(core) for core in (profile.pinned_cores or (2,)))
            wrapper_bits.extend(["-Cores", cores])
        wrapper_bits.extend(
            [
                "-ResultsDir",
                f"'{str(session_dir_rel)}'",
                "-BenchmarkArgs",
                ",".join(f"'{arg}'" for arg in benchmark_args),
            ]
        )
        command = [
            _powershell_exe(),
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            " ".join(wrapper_bits),
        ]
    else:
        wrapper_name = "run_pinned.sh" if profile.wrapper == "pinned" else "run_quiet_benchmark.sh"
        wrapper = REPO_ROOT / "scripts" / wrapper_name
        command = [
            _shell_exe(),
            str(wrapper),
            *benchmark_args,
        ]

    return command


def _run_profile(profile: BaselineProfile, output_root: Path) -> None:
    command = _build_wrapper_command(profile, output_root)
    print(f"Running baseline profile: {profile.name}")
    print("  " + " ".join(command))
    env = os.environ.copy()
    if os.name != "nt":
        env["RESULTS_DIR"] = str(Path("results") / "baselines_20260404" / profile.results_subdir)
    subprocess.run(command, cwd=REPO_ROOT, check=True, env=env)


def _read_runtime_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _group_isolation_rows(rows: Iterable[Dict[str, str]]) -> Dict[tuple, List[float]]:
    grouped: Dict[tuple, List[float]] = defaultdict(list)
    for row in rows:
        if row.get("mode") != "isolation":
            continue
        key = (
            row.get("workload_name", ""),
            row.get("algorithm", ""),
            row.get("allocation_policy", ""),
            _int_or_none(row.get("memory_frames")),
            _int_or_none(row.get("process_id")),
        )
        duration_ns = _float_or_none(row.get("duration_ns"))
        if duration_ns is not None:
            grouped[key].append(duration_ns)
    return grouped


def _summarize_groups(grouped: Dict[tuple, List[float]], *, profile: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for (workload_name, algorithm, allocation_policy, memory_frames, process_id), durations in sorted(grouped.items()):
        if not durations:
            continue
        group_mean = mean(durations)
        group_std = stdev(durations) if len(durations) > 1 else 0.0
        cv = (group_std / group_mean) if group_mean else 0.0
        rows.append(
            {
                "profile": profile,
                "workload_name": workload_name,
                "algorithm": algorithm,
                "allocation_policy": allocation_policy,
                "memory_frames": memory_frames,
                "process_id": process_id,
                "trials": len(durations),
                "mean_ns": round(group_mean, 2),
                "median_ns": round(median(durations), 2),
                "std_ns": round(group_std, 2),
                "cv": round(cv, 6),
                "min_ns": min(durations),
                "max_ns": max(durations),
                "range_ns": max(durations) - min(durations),
            }
        )
    return rows


def _write_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _load_profile_summary(profile_dir: Path, profile_name: str) -> List[Dict[str, object]]:
    rows = _read_runtime_rows(profile_dir / "raw" / "isolation_results.csv")
    grouped = _group_isolation_rows(rows)
    return _summarize_groups(grouped, profile=profile_name)


def _collect_summary_rows(output_root: Path, profiles: Sequence[BaselineProfile]) -> List[Dict[str, object]]:
    summary_rows: List[Dict[str, object]] = []
    for profile in profiles:
        profile_dir = output_root / profile.results_subdir
        summary_rows.extend(_load_profile_summary(profile_dir, profile.name))
    return summary_rows


def _classify_stability(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    if not rows:
        return {
            "group_count": 0,
            "stable_groups": 0,
            "review_groups": 0,
            "unstable_groups": 0,
            "median_cv": 0.0,
            "mean_cv": 0.0,
            "max_cv": 0.0,
            "profiles": {},
            "verdict": "No isolation rows were produced.",
        }

    cvs = [float(row["cv"]) for row in rows]
    profiles: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        profiles[str(row["profile"])].append(float(row["cv"]))

    profile_summary: Dict[str, Dict[str, object]] = {}
    for profile, profile_cvs in profiles.items():
        profile_summary[profile] = {
            "group_count": len(profile_cvs),
            "stable_groups": sum(1 for cv in profile_cvs if cv <= TIGHT_CV_THRESHOLD),
            "review_groups": sum(1 for cv in profile_cvs if TIGHT_CV_THRESHOLD < cv <= STABILITY_CV_THRESHOLD),
            "unstable_groups": sum(1 for cv in profile_cvs if cv > STABILITY_CV_THRESHOLD),
            "median_cv": round(median(profile_cvs), 6),
            "mean_cv": round(mean(profile_cvs), 6),
            "max_cv": round(max(profile_cvs), 6),
        }

    stable_groups = sum(1 for cv in cvs if cv <= TIGHT_CV_THRESHOLD)
    review_groups = sum(1 for cv in cvs if TIGHT_CV_THRESHOLD < cv <= STABILITY_CV_THRESHOLD)
    unstable_groups = sum(1 for cv in cvs if cv > STABILITY_CV_THRESHOLD)
    if unstable_groups == 0:
        verdict = "The isolated baselines look stable enough to trust slowdown."
    elif stable_groups >= unstable_groups:
        verdict = "The isolated baselines are usable, but slowdown should be treated as directional rather than exact."
    else:
        verdict = "The isolated baselines are noisy enough that slowdown should be treated cautiously."
    return {
        "group_count": len(rows),
        "stable_groups": stable_groups,
        "review_groups": review_groups,
        "unstable_groups": unstable_groups,
        "median_cv": round(median(cvs), 6),
        "mean_cv": round(mean(cvs), 6),
        "max_cv": round(max(cvs), 6),
        "profiles": profile_summary,
        "verdict": verdict,
    }


def _build_manifest(output_root: Path, profiles: Sequence[BaselineProfile], repetitions: int) -> Dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_root": str(output_root),
        "repetitions": repetitions,
        "stability_threshold_cv": STABILITY_CV_THRESHOLD,
        "tight_threshold_cv": TIGHT_CV_THRESHOLD,
        "profiles": [
            {
                "name": profile.name,
                "wrapper": profile.wrapper,
                "results_subdir": profile.results_subdir,
                "benchmark_args": list(profile.benchmark_args),
                "pinned_cores": list(profile.pinned_cores),
            }
            for profile in profiles
        ],
    }


def _write_summary_markdown(path: Path, manifest: Dict[str, object], rows: Sequence[Dict[str, object]], stability: Dict[str, object]) -> None:
    lines = [
        "# Isolation Stability Baseline",
        "",
        f"Generated from `{manifest['output_root']}` with `{manifest['repetitions']}` repetitions per configuration.",
        "",
        "Reproduce with:",
        "",
        "```powershell",
        "python scripts\\run_isolation_baselines.py",
        "```",
        "",
        "## Run Recipe",
        "",
    ]
    for profile in manifest["profiles"]:
        args = " ".join(profile["benchmark_args"])
        cores = f" cores={profile['pinned_cores']}" if profile["pinned_cores"] else ""
        lines.append(f"- `{profile['name']}` via `{profile['wrapper']}`{cores}: `{args}`")
    lines.extend(
        [
            "",
            "## Stability Verdict",
            "",
            f"- Group count: `{stability['group_count']}`",
            f"- Stable groups (`cv` <= {TIGHT_CV_THRESHOLD:.2f}): `{stability['stable_groups']}`",
            f"- Review groups (`{TIGHT_CV_THRESHOLD:.2f}` < `cv` <= {STABILITY_CV_THRESHOLD:.2f}): `{stability['review_groups']}`",
            f"- Unstable groups (`cv` > {STABILITY_CV_THRESHOLD:.2f}): `{stability['unstable_groups']}`",
            f"- Median `cv`: `{stability['median_cv']}`",
            f"- Mean `cv`: `{stability.get('mean_cv', 0.0)}`",
            f"- Max `cv`: `{stability['max_cv']}`",
            "",
            f"Verdict: {stability['verdict']}",
            "",
            "## Profile Breakdown",
            "",
            "| profile | groups | stable | review | unstable | median cv | mean cv | max cv |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for profile_name, stats in stability.get("profiles", {}).items():
        lines.append(
            "| {profile} | {group_count} | {stable_groups} | {review_groups} | {unstable_groups} | {median_cv} | {mean_cv} | {max_cv} |".format(
                profile=profile_name,
                **stats,
            )
        )
    lines.extend(
        [
            "",
            "## Sampled Groups",
            "",
            "| profile | workload | algorithm | allocation | frames | pid | trials | mean ns | std ns | cv |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {profile} | {workload_name} | {algorithm} | {allocation_policy} | {memory_frames} | {process_id} | {trials} | {mean_ns} | {std_ns} | {cv} |".format(
                **row
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_profiles(repetitions: int, trace_file: Path) -> List[BaselineProfile]:
    return [
        BaselineProfile(
            name="pressure_pinned",
            wrapper="pinned",
            benchmark_args=[
                "--experiment",
                "pressure",
                "--repetitions",
                str(repetitions),
            ],
            results_subdir="pressure_pinned",
            pinned_cores=(2,),
        ),
        BaselineProfile(
            name="trace_quiet",
            wrapper="quiet",
            benchmark_args=[
                "--experiment",
                "trace",
                "--trace-file",
                str(Path("workloads") / "traces" / trace_file.name),
                "--repetitions",
                str(repetitions),
            ],
            results_subdir="trace_quiet",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and summarize isolated runtime baselines.")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory where the baseline bundle should be written.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help="Number of repetitions per configuration inside each profile.",
    )
    parser.add_argument(
        "--trace-file",
        default=str(DEFAULT_TRACE_FILE),
        help="Trace file used by the trace-driven baseline profile.",
    )
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    profiles = build_profiles(args.repetitions, Path(args.trace_file).resolve())
    for profile in profiles:
        _run_profile(profile, output_root)

    summary_rows = _collect_summary_rows(output_root, profiles)
    stability = _classify_stability(summary_rows)
    manifest = _build_manifest(output_root, profiles, args.repetitions)

    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_csv(output_root / "baseline_stability_summary.csv", summary_rows)
    _write_summary_markdown(output_root / "baseline_stability_summary.md", manifest, summary_rows, stability)

    docs_path = REPO_ROOT / "docs" / "isolation_stability.md"
    _write_summary_markdown(docs_path, manifest, summary_rows, stability)

    print("\nBaseline run complete.")
    print(f"Summary CSV: {output_root / 'baseline_stability_summary.csv'}")
    print(f"Summary MD: {output_root / 'baseline_stability_summary.md'}")
    print(f"Docs note: {docs_path}")
    print(stability["verdict"])


if __name__ == "__main__":
    main()
