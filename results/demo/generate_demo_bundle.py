#!/usr/bin/env python3
"""Package the final demo bundle from already-generated real outputs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from run_all_experiments import ensure_output_dirs  # type: ignore


SOURCE_FILES = {
    "trace": REPO_ROOT / "workloads" / "traces" / "sample_trace.csv",
    "synthetic_trace": REPO_ROOT / "workloads" / "traces" / "demo_locality.csv",
    "shared_results": REPO_ROOT / "results" / "raw" / "shared_results.csv",
    "isolation_results": REPO_ROOT / "results" / "raw" / "isolation_results.csv",
    "slowdown_metrics": REPO_ROOT / "results" / "processed" / "slowdown_metrics.csv",
    "best_policy_table": REPO_ROOT / "results" / "tables" / "best_policy_by_workload.csv",
    "fairness_figure": REPO_ROOT / "results" / "figures" / "fairness_comparison.png",
    "page_fault_figure": REPO_ROOT / "results" / "figures" / "page_fault_comparison.png",
}


def _copy_file(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing source artifact: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _write_markdown_table(source_csv: Path, destination_md: Path, *, title: str) -> None:
    if not source_csv.exists():
        raise FileNotFoundError(f"Missing source table: {source_csv}")

    with source_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError(f"No rows found in {source_csv}")

    headers = list(rows[0].keys())
    lines = [f"# {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in headers) + " |")

    destination_md.parent.mkdir(parents=True, exist_ok=True)
    destination_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_bundle_readme(destination: Path) -> None:
    readme = f"""# Final Demo Bundle

This bundle is a compact snapshot built from the real benchmark outputs already checked into the repository, plus one clearly labeled synthetic locality counterpart for context.

## Contents

- `raw/sample_trace.csv`: a small real trace used by the trace-driven benchmark path.
- `raw/synthetic_locality_demo.csv`: a clearly labeled synthetic counterpart for a tiny locality-focused example.
- `raw/shared_results.csv` and `raw/isolation_results.csv`: the measured wall-clock runtime logs.
- `processed/slowdown_metrics.csv`: per-process slowdown and page-fault metrics.
- `tables/best_policy_by_workload.csv`: the example result table shown in the demo.
- `tables/example_result_table.md`: a readable markdown rendering of the same table.
- `figures/fairness_comparison.png`: the fairness figure for the final demo.
- `figures/page_fault_comparison.png`: the page-fault comparison figure for the final demo.

## Reproduce

1. Install dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Regenerate the real benchmark outputs if needed.

   ```powershell
   python experiments\\run_all_experiments.py --final --trace-file workloads\\traces\\sample_trace.csv --output-dir results
   ```

3. Rebuild this bundle from those outputs.

   ```powershell
   python results\\demo\\generate_demo_bundle.py --output-dir results\\demo\\final_bundle
   ```

4. Open the copied figures and tables in `results\\demo\\final_bundle`.

The bundle is intentionally small so it can be inspected quickly during grading or a live demo.
"""
    destination.write_text(readme, encoding="utf-8")


def _write_manifest(destination: Path, bundle_root: Path, copied_files: Sequence[Path]) -> None:
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_root": str(bundle_root),
        "files": [str(path.relative_to(bundle_root)).replace("\\", "/") for path in copied_files],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_demo_bundle(output_dir: str | Path) -> Path:
    """Copy the real benchmark outputs into a small submission-ready bundle."""
    output_path = Path(output_dir)
    directories = ensure_output_dirs(output_path)

    copies: list[tuple[Path, Path]] = [
        (SOURCE_FILES["trace"], directories["raw"] / "sample_trace.csv"),
        (SOURCE_FILES["synthetic_trace"], directories["raw"] / "synthetic_locality_demo.csv"),
        (SOURCE_FILES["shared_results"], directories["raw"] / "shared_results.csv"),
        (SOURCE_FILES["isolation_results"], directories["raw"] / "isolation_results.csv"),
        (SOURCE_FILES["slowdown_metrics"], directories["processed"] / "slowdown_metrics.csv"),
        (SOURCE_FILES["best_policy_table"], directories["tables"] / "best_policy_by_workload.csv"),
        (SOURCE_FILES["fairness_figure"], directories["figures"] / "fairness_comparison.png"),
        (SOURCE_FILES["page_fault_figure"], directories["figures"] / "page_fault_comparison.png"),
    ]

    copied_paths: list[Path] = []
    for source, destination in copies:
        _copy_file(source, destination)
        copied_paths.append(destination)

    _write_markdown_table(
        SOURCE_FILES["best_policy_table"],
        directories["tables"] / "example_result_table.md",
        title="Example Result Table",
    )
    copied_paths.append(directories["tables"] / "example_result_table.md")

    _write_bundle_readme(directories["root"] / "README.md")
    copied_paths.append(directories["root"] / "README.md")
    manifest_path = directories["metadata"] / "bundle_manifest.json"
    _write_manifest(manifest_path, directories["root"], copied_paths + [manifest_path])
    copied_paths.append(manifest_path)

    return directories["root"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the final demo bundle from real outputs.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "results" / "demo" / "final_bundle"),
        help="Where to write the demo bundle.",
    )
    args = parser.parse_args()

    output_path = build_demo_bundle(args.output_dir)
    print(f"Demo bundle written to: {output_path}")


if __name__ == "__main__":
    main()
