"""CSV trace ingestion for the virtual memory project."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

try:
    from .trace_normalizer import (
        TraceEvent,
        TraceFormatError,
        normalize_trace_rows,
        normalize_trace_tuples,
        validate_trace,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from trace_normalizer import (
        TraceEvent,
        TraceFormatError,
        normalize_trace_rows,
        normalize_trace_tuples,
        validate_trace,
    )


def _is_header_row(row: Sequence[str]) -> bool:
    """Detect whether the first non-comment row is a header."""
    normalized = {cell.strip().lower() for cell in row}
    return any(
        token in normalized
        for token in {
            "timestamp",
            "time",
            "ts",
            "process_id",
            "pid",
            "page_id",
            "page",
            "address",
            "virtual_address",
            "is_write",
            "write",
            "access_type",
            "op",
            "operation",
        }
    )


def _read_data_rows(path: Path) -> List[List[str]]:
    """Read non-comment CSV rows."""
    rows: List[List[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            rows.append(next(csv.reader([raw_line])))
    return rows


def _rows_to_dicts(header: Sequence[str], rows: Iterable[Sequence[str]]) -> List[Dict[str, Any]]:
    """Convert header-based CSV rows into dictionaries."""
    normalized_header = [key.strip().lower() for key in header]
    dict_rows: List[Dict[str, Any]] = []
    for row in rows:
        record: Dict[str, Any] = {}
        for index, key in enumerate(normalized_header):
            if index < len(row):
                record[key] = row[index].strip()
        dict_rows.append(record)
    return dict_rows


def load_trace_csv(
    path: str | Path,
    *,
    page_size: int = 4096,
    default_process_id: int = 0,
    sort_by_timestamp: bool = True,
) -> List[TraceEvent]:
    """Load a CSV trace and return canonical (timestamp, process_id, page_id, is_write) tuples."""
    trace_path = Path(path)
    if not trace_path.exists():
        raise FileNotFoundError(trace_path)

    rows = _read_data_rows(trace_path)
    if not rows:
        return []

    first_row = rows[0]
    if _is_header_row(first_row):
        header = [cell.strip() for cell in first_row]
        dict_rows = _rows_to_dicts(header, rows[1:])
        events = normalize_trace_rows(
            dict_rows,
            page_size=page_size,
            default_process_id=default_process_id,
            sort_by_timestamp=sort_by_timestamp,
        )
    else:
        events = normalize_trace_tuples(
            rows,
            page_size=page_size,
            default_process_id=default_process_id,
            sort_by_timestamp=sort_by_timestamp,
        )

    return validate_trace(events)


def load_trace_text(
    csv_text: str,
    *,
    page_size: int = 4096,
    default_process_id: int = 0,
    sort_by_timestamp: bool = True,
) -> List[TraceEvent]:
    """Load trace data from an in-memory CSV string."""
    rows: List[List[str]] = []
    for raw_line in csv_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append(next(csv.reader([raw_line])))

    if not rows:
        return []

    first_row = rows[0]
    if _is_header_row(first_row):
        dict_rows = _rows_to_dicts(first_row, rows[1:])
        events = normalize_trace_rows(
            dict_rows,
            page_size=page_size,
            default_process_id=default_process_id,
            sort_by_timestamp=sort_by_timestamp,
        )
    else:
        events = normalize_trace_tuples(
            rows,
            page_size=page_size,
            default_process_id=default_process_id,
            sort_by_timestamp=sort_by_timestamp,
        )

    return validate_trace(events)


__all__ = [
    "TraceEvent",
    "TraceFormatError",
    "load_trace_csv",
    "load_trace_text",
]
