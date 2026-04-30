"""Sliding time-window aggregation for pipeline run outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class WindowError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


@dataclass
class WindowResult:
    window_seconds: int
    total: int
    successes: int
    failures: int
    success_rate: Optional[float]  # None when total == 0
    oldest_ts: Optional[datetime]
    newest_ts: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "window_seconds": self.window_seconds,
            "total": self.total,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": self.success_rate,
            "oldest_ts": self.oldest_ts.isoformat() if self.oldest_ts else None,
            "newest_ts": self.newest_ts.isoformat() if self.newest_ts else None,
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_window(
    outcomes: List[dict],
    window_seconds: int,
    *,
    now: Optional[datetime] = None,
) -> WindowResult:
    """Aggregate outcomes that fall within the trailing *window_seconds*.

    Each element of *outcomes* must have:
      - ``timestamp`` (ISO-8601 str or datetime)
      - ``success`` (bool)

    Raises ``WindowError`` for non-positive *window_seconds*.
    """
    if window_seconds <= 0:
        raise WindowError(f"window_seconds must be positive, got {window_seconds}")

    reference = now or _utcnow()
    cutoff = reference - timedelta(seconds=window_seconds)

    in_window: List[dict] = []
    for entry in outcomes:
        ts = entry["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            in_window.append({**entry, "_ts": ts})

    total = len(in_window)
    successes = sum(1 for e in in_window if e["success"])
    failures = total - successes
    success_rate = (successes / total) if total > 0 else None

    timestamps = [e["_ts"] for e in in_window]
    oldest = min(timestamps) if timestamps else None
    newest = max(timestamps) if timestamps else None

    return WindowResult(
        window_seconds=window_seconds,
        total=total,
        successes=successes,
        failures=failures,
        success_rate=success_rate,
        oldest_ts=oldest,
        newest_ts=newest,
    )
