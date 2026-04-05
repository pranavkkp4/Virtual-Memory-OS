"""Helpers for recording the benchmark environment."""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _read_git_commit(root: Path) -> Optional[str]:
    """Best-effort lookup of the current git commit."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _load_average() -> Optional[list[float]]:
    """Return a best-effort host load snapshot."""
    try:
        load = os.getloadavg()
    except (AttributeError, OSError):
        return None
    return [float(value) for value in load]


def capture_run_environment(root: str | Path, *, pinned_cores: Optional[str] = None) -> Dict[str, Any]:
    """Capture lightweight metadata for a benchmark session."""
    project_root = Path(root).resolve()
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "hardware": {
            "cpu_count": os.cpu_count(),
            "load_average": _load_average(),
        },
        "project_root": str(project_root),
        "git_commit": _read_git_commit(project_root),
        "pinned_cores": pinned_cores or os.environ.get("VM_PINNED_CORES"),
        "benchmark_env": {
            "quiet_mode": os.environ.get("VM_QUIET_BENCHMARK"),
            "session_label": os.environ.get("VM_BENCHMARK_LABEL"),
        },
    }


def write_run_environment(
    output_path: str | Path,
    root: str | Path,
    *,
    pinned_cores: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture and persist benchmark metadata as JSON."""
    payload = capture_run_environment(root, pinned_cores=pinned_cores)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload
