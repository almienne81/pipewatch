"""Rolling window statistics for pipeline run durations and outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Sequence


class RollingError(ValueError):
    """Raised when rolling window parameters are invalid."""


@dataclass(frozen=True)
class RollingWindow:
    """Configuration for a rolling statistics window."""

    size: int = 10

    def __post_init__(self) -> None:
        if self.size < 1:
            raise RollingError(f"size must be >= 1, got {self.size}")

    def to_dict(self) -> dict:
        return {"size": self.size}

    @classmethod
    def from_dict(cls, data: dict) -> "RollingWindow":
        return cls(size=int(data.get("size", 10)))


@dataclass
class RollingStats:
    """Computed statistics over a rolling window of durations."""

    count: int
    mean: Optional[float]
    minimum: Optional[float]
    maximum: Optional[float]
    p50: Optional[float]
    p95: Optional[float]

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "mean": self.mean,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "p50": self.p50,
            "p95": self.p95,
        }


def compute_rolling(durations: Sequence[float], window: RollingWindow) -> RollingStats:
    """Compute rolling statistics from the most recent *window.size* durations."""
    recent = list(durations)[-window.size :]
    if not recent:
        return RollingStats(
            count=0,
            mean=None,
            minimum=None,
            maximum=None,
            p50=None,
            p95=None,
        )
    sorted_vals = sorted(recent)
    n = len(sorted_vals)

    def _percentile(p: float) -> float:
        idx = (p / 100) * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        frac = idx - lo
        return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])

    return RollingStats(
        count=n,
        mean=sum(sorted_vals) / n,
        minimum=sorted_vals[0],
        maximum=sorted_vals[-1],
        p50=_percentile(50),
        p95=_percentile(95),
    )
