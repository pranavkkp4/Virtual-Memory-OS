"""Utilities for normalizing memory access traces.

The canonical internal representation is:
    (timestamp, process_id, page_id, is_write)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple


TraceEvent = Tuple[int, int, int, bool]


class TraceFormatError(ValueError):
    """Raised when a trace row cannot be normalized."""


@dataclass(frozen=True)
class NormalizedTrace:
    """A small helper wrapper for canonical trace events."""

    timestamp: int
    process_id: int
    page_id: int
    is_write: bool

    def as_tuple(self) -> TraceEvent:
        return (self.timestamp, self.process_id, self.page_id, self.is_write)


def address_to_page(address: int, page_size: int = 4096) -> int:
    """Convert a byte address to a page number."""
    if page_size <= 0:
        raise TraceFormatError("page_size must be greater than zero")
    if address < 0:
        raise TraceFormatError("address must be non-negative")
    return address // page_size


def parse_int(value: Any, field_name: str) -> int:
    """Parse an integer-like value, including hex strings."""
    if isinstance(value, bool):
        raise TraceFormatError(f"{field_name} must be an integer, not bool")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise TraceFormatError(f"{field_name} cannot be empty")
        try:
            return int(text, 0)
        except ValueError as exc:
            raise TraceFormatError(f"Invalid integer for {field_name}: {value!r}") from exc
    raise TraceFormatError(f"Invalid integer for {field_name}: {value!r}")


def parse_bool(value: Any, field_name: str = "is_write") -> bool:
    """Parse common boolean encodings used in trace files."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
        raise TraceFormatError(f"{field_name} integer must be 0 or 1")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "t", "yes", "y", "write", "w"}:
            return True
        if normalized in {"0", "false", "f", "no", "n", "read", "r"}:
            return False
    raise TraceFormatError(f"Invalid boolean for {field_name}: {value!r}")


def _extract_page_id(row: Dict[str, Any], page_size: int) -> int:
    """Extract a page id or derive it from an address field."""
    for key in ("page_id", "page", "page number", "vpn"):
        if key in row and row[key] not in (None, ""):
            return parse_int(row[key], "page_id")

    for key in ("address", "virtual_address", "virtual address", "addr"):
        if key in row and row[key] not in (None, ""):
            return address_to_page(parse_int(row[key], key), page_size)

    raise TraceFormatError("trace row must include page_id or address")


def _extract_timestamp(row: Dict[str, Any], fallback: int) -> int:
    """Extract the timestamp or synthesize one from row order."""
    for key in ("timestamp", "time", "ts"):
        if key in row and row[key] not in (None, ""):
            return parse_int(row[key], "timestamp")
    return fallback


def _extract_process_id(row: Dict[str, Any], default_process_id: int) -> int:
    """Extract the process id, defaulting when the trace omits it."""
    for key in ("process_id", "pid", "process", "proc_id"):
        if key in row and row[key] not in (None, ""):
            return parse_int(row[key], "process_id")
    return default_process_id


def normalize_trace_rows(
    rows: Iterable[Dict[str, Any]],
    *,
    page_size: int = 4096,
    default_process_id: int = 0,
    sort_by_timestamp: bool = True,
) -> List[TraceEvent]:
    """Normalize dict-like rows into canonical trace events."""
    normalized: List[TraceEvent] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TraceFormatError("normalize_trace_rows expects dictionaries")

        timestamp = _extract_timestamp(row, index)
        process_id = _extract_process_id(row, default_process_id)
        page_id = _extract_page_id(row, page_size)

        write_value = None
        for key in ("is_write", "write", "iswrite", "access_type", "op", "operation"):
            if key in row and row[key] not in (None, ""):
                write_value = row[key]
                break

        if write_value is None:
            raise TraceFormatError("trace row must include is_write or an equivalent field")

        is_write = parse_bool(write_value)
        normalized.append(NormalizedTrace(timestamp, process_id, page_id, is_write).as_tuple())

    if sort_by_timestamp:
        normalized.sort(key=lambda event: (event[0], event[1], event[2]))

    return normalized


def normalize_trace_tuples(
    rows: Iterable[Sequence[Any]],
    *,
    page_size: int = 4096,
    default_process_id: int = 0,
    sort_by_timestamp: bool = True,
) -> List[TraceEvent]:
    """Normalize tuple/list rows from legacy CSV traces."""
    normalized: List[TraceEvent] = []
    for index, row in enumerate(rows):
        values = list(row)
        if len(values) == 4:
            timestamp = parse_int(values[0], "timestamp")
            process_id = parse_int(values[1], "process_id")
            page_id = parse_int(values[2], "page_id")
            is_write = parse_bool(values[3])
        elif len(values) == 3:
            timestamp = index
            page_id = parse_int(values[0], "page_id")
            process_id = parse_int(values[1], "process_id")
            is_write = parse_bool(values[2])
        elif len(values) == 2:
            timestamp = index
            page_id = parse_int(values[0], "page_id")
            process_id = default_process_id
            is_write = parse_bool(values[1])
        else:
            raise TraceFormatError("legacy trace rows must have 2, 3, or 4 columns")

        if page_id < 0:
            raise TraceFormatError("page_id must be non-negative")
        if process_id < 0:
            raise TraceFormatError("process_id must be non-negative")
        normalized.append(NormalizedTrace(timestamp, process_id, page_id, is_write).as_tuple())

    if sort_by_timestamp:
        normalized.sort(key=lambda event: (event[0], event[1], event[2]))

    return normalized


def validate_trace(events: Iterable[TraceEvent]) -> List[TraceEvent]:
    """Validate canonical trace events and return them as a list."""
    validated: List[TraceEvent] = []
    for event in events:
        if len(event) != 4:
            raise TraceFormatError("canonical trace events must contain four fields")

        timestamp, process_id, page_id, is_write = event
        timestamp = parse_int(timestamp, "timestamp")
        process_id = parse_int(process_id, "process_id")
        page_id = parse_int(page_id, "page_id")
        is_write = parse_bool(is_write)

        if timestamp < 0:
            raise TraceFormatError("timestamp must be non-negative")
        if process_id < 0:
            raise TraceFormatError("process_id must be non-negative")
        if page_id < 0:
            raise TraceFormatError("page_id must be non-negative")

        validated.append((timestamp, process_id, page_id, is_write))

    validated.sort(key=lambda event: (event[0], event[1], event[2]))
    return validated
