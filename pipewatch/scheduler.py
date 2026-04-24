"""Simple cron-style schedule checker for pipewatch pipelines."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


CRON_ALIASES = {
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
}


@dataclass
class Schedule:
    """Represents a parsed cron schedule."""

    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str
    raw: str

    def is_due(self, at: Optional[datetime] = None) -> bool:
        """Return True if the schedule matches the given datetime (default: now)."""
        dt = at or datetime.now()
        return (
            _field_matches(self.minute, dt.minute)
            and _field_matches(self.hour, dt.hour)
            and _field_matches(self.day_of_month, dt.day)
            and _field_matches(self.month, dt.month)
            and _field_matches(self.day_of_week, dt.weekday())
        )


def parse_schedule(expr: str) -> Schedule:
    """Parse a cron expression string into a Schedule.

    Raises ValueError for invalid expressions.
    """
    expr = expr.strip()
    expr = CRON_ALIASES.get(expr, expr)

    parts = re.split(r"\s+", expr)
    if len(parts) != 5:
        raise ValueError(
            f"Invalid cron expression {expr!r}: expected 5 fields, got {len(parts)}"
        )
    minute, hour, dom, month, dow = parts
    return Schedule(
        minute=minute,
        hour=hour,
        day_of_month=dom,
        month=month,
        day_of_week=dow,
        raw=expr,
    )


def _field_matches(field: str, value: int) -> bool:
    """Check whether a single cron field matches an integer value."""
    if field == "*":
        return True
    if re.fullmatch(r"\d+", field):
        return int(field) == value
    # */step
    m = re.fullmatch(r"\*/(\d+)", field)
    if m:
        step = int(m.group(1))
        return step > 0 and value % step == 0
    # range a-b
    m = re.fullmatch(r"(\d+)-(\d+)", field)
    if m:
        return int(m.group(1)) <= value <= int(m.group(2))
    # list a,b,c
    if "," in field:
        return any(_field_matches(part, value) for part in field.split(","))
    raise ValueError(f"Unsupported cron field syntax: {field!r}")
