"""Sparkline renderer for compact time-series visualisation in the CLI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

_BLOCKS = " ▁▂▃▄▅▆▇█"


class SparklineError(ValueError):
    """Raised when sparkline input is invalid."""


@dataclass(frozen=True)
class SparklinePolicy:
    """Configuration for sparkline rendering."""

    width: int = 20
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if self.width < 1:
            raise SparklineError("width must be at least 1")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value >= self.max_value
        ):
            raise SparklineError("min_value must be less than max_value")

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "min_value": self.min_value,
            "max_value": self.max_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SparklinePolicy":
        return cls(
            width=int(data.get("width", 20)),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
        )


def render(values: Sequence[float], policy: SparklinePolicy | None = None) -> str:
    """Return a sparkline string for *values*.

    An empty sequence returns an empty string.  Values are sampled or
    truncated to *policy.width* characters.
    """
    if policy is None:
        policy = SparklinePolicy()

    if not values:
        return ""

    # Downsample / truncate to requested width
    samples = list(values[-policy.width :])

    lo = policy.min_value if policy.min_value is not None else min(samples)
    hi = policy.max_value if policy.max_value is not None else max(samples)

    span = hi - lo
    n = len(_BLOCKS) - 1  # number of non-empty block levels

    chars: list[str] = []
    for v in samples:
        if span == 0:
            idx = n // 2
        else:
            idx = round((max(lo, min(hi, v)) - lo) / span * n)
        chars.append(_BLOCKS[idx])

    return "".join(chars)


def success_rate_sparkline(
    outcomes: Sequence[bool], policy: SparklinePolicy | None = None
) -> str:
    """Convenience wrapper: render a sparkline for a boolean outcome series."""
    return render([1.0 if ok else 0.0 for ok in outcomes], policy)
