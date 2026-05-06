"""Trendline: simple linear trend detection over a sequence of durations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class TrendlineError(Exception):
    """Raised for invalid trendline configuration or input."""


@dataclass
class TrendlinePolicy:
    min_samples: int = 5
    slope_warn_threshold: float = 0.1   # seconds per run
    slope_fail_threshold: float = 0.5   # seconds per run

    def __post_init__(self) -> None:
        if self.min_samples < 2:
            raise TrendlineError("min_samples must be >= 2")
        if self.slope_warn_threshold < 0:
            raise TrendlineError("slope_warn_threshold must be >= 0")
        if self.slope_fail_threshold < self.slope_warn_threshold:
            raise TrendlineError(
                "slope_fail_threshold must be >= slope_warn_threshold"
            )

    def to_dict(self) -> dict:
        return {
            "min_samples": self.min_samples,
            "slope_warn_threshold": self.slope_warn_threshold,
            "slope_fail_threshold": self.slope_fail_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrendlinePolicy":
        return cls(
            min_samples=data.get("min_samples", 5),
            slope_warn_threshold=data.get("slope_warn_threshold", 0.1),
            slope_fail_threshold=data.get("slope_fail_threshold", 0.5),
        )


@dataclass
class TrendResult:
    slope: float
    intercept: float
    n: int
    status: str  # "ok", "warn", "fail", "insufficient_data"

    def to_dict(self) -> dict:
        return {
            "slope": self.slope,
            "intercept": self.intercept,
            "n": self.n,
            "status": self.status,
        }


def compute_trend(durations: List[float], policy: TrendlinePolicy) -> TrendResult:
    """Fit a least-squares line to *durations* and classify the slope."""
    n = len(durations)
    if n < policy.min_samples:
        return TrendResult(slope=0.0, intercept=0.0, n=n, status="insufficient_data")

    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(durations) / n

    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, durations))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den != 0 else 0.0
    intercept = mean_y - slope * mean_x

    if slope >= policy.slope_fail_threshold:
        status = "fail"
    elif slope >= policy.slope_warn_threshold:
        status = "warn"
    else:
        status = "ok"

    return TrendResult(slope=slope, intercept=intercept, n=n, status=status)
