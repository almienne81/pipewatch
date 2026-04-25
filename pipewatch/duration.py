"""Human-readable duration parsing and formatting utilities."""

from __future__ import annotations

import re
from typing import Union


class DurationError(ValueError):
    """Raised when a duration string cannot be parsed."""


# Mapping of unit suffixes to seconds
_UNIT_SECONDS: dict[str, int] = {
    "s": 1,
    "sec": 1,
    "secs": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hr": 3600,
    "hrs": 3600,
    "hour": 3600,
    "hours": 3600,
    "d": 86400,
    "day": 86400,
    "days": 86400,
}

_PATTERN = re.compile(
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[a-zA-Z]+)"
)


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string into seconds.

    Examples::

        parse_duration("5m")      # 300.0
        parse_duration("1.5 hours")  # 5400.0
        parse_duration("90s")     # 90.0

    Raises:
        DurationError: If the string cannot be parsed or the unit is unknown.
    """
    text = text.strip()
    match = _PATTERN.fullmatch(text)
    if not match:
        raise DurationError(
            f"Cannot parse duration {text!r}. "
            "Expected format like '5m', '2 hours', '30s'."
        )
    value = float(match.group("value"))
    unit = match.group("unit").lower()
    if unit not in _UNIT_SECONDS:
        raise DurationError(
            f"Unknown time unit {unit!r} in {text!r}. "
            f"Supported units: {sorted(set(_UNIT_SECONDS.values()))}"
        )
    return value * _UNIT_SECONDS[unit]


def format_duration(seconds: Union[int, float]) -> str:
    """Format a number of seconds into a compact human-readable string.

    Examples::

        format_duration(90)    # '1m 30s'
        format_duration(3661)  # '1h 1m 1s'
        format_duration(45)    # '45s'
    """
    seconds = int(seconds)
    if seconds < 0:
        raise DurationError("Duration must be non-negative.")

    parts: list[str] = []
    for label, unit in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if seconds >= unit:
            parts.append(f"{seconds // unit}{label}")
            seconds %= unit
    return " ".join(parts) if parts else "0s"
