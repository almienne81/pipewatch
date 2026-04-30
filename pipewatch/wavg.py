"""Weighted average utilities for pipeline metric aggregation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


class WAvgError(ValueError):
    """Raised when weighted average computation fails."""


@dataclass(frozen=True)
class WeightedSample:
    value: float
    weight: float

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise WAvgError(f"Weight must be non-negative, got {self.weight}")


def weighted_average(samples: Sequence[WeightedSample]) -> float | None:
    """Return the weighted average of *samples*, or None if total weight is zero."""
    if not samples:
        return None
    total_weight = sum(s.weight for s in samples)
    if total_weight == 0.0:
        return None
    return sum(s.value * s.weight for s in samples) / total_weight


def from_pairs(pairs: Iterable[tuple[float, float]]) -> list[WeightedSample]:
    """Build a list of WeightedSample from (value, weight) tuples."""
    return [WeightedSample(value=v, weight=w) for v, w in pairs]


def duration_weighted_average(durations: Sequence[float]) -> float | None:
    """Return the average duration weighted by recency (index + 1).

    More recent entries (later in the list) receive a higher weight.
    Returns None for an empty sequence.
    """
    if not durations:
        return None
    samples = [
        WeightedSample(value=d, weight=float(i + 1))
        for i, d in enumerate(durations)
    ]
    return weighted_average(samples)


def success_rate_trend(outcomes: Sequence[bool], window: int = 10) -> float | None:
    """Return the recency-weighted success rate over the last *window* outcomes.

    Returns None when *outcomes* is empty.
    """
    if not outcomes:
        return None
    recent = list(outcomes)[-window:]
    samples = [
        WeightedSample(value=1.0 if ok else 0.0, weight=float(i + 1))
        for i, ok in enumerate(recent)
    ]
    return weighted_average(samples)
