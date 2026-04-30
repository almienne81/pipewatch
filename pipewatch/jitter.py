"""Jitter utilities for randomising retry/backoff delays."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


class JitterError(ValueError):
    """Raised when jitter configuration is invalid."""


@dataclass(frozen=True)
class JitterPolicy:
    """Policy that adds randomised jitter to a base delay.

    Attributes:
        min_factor: Multiplier lower bound (>= 0.0).
        max_factor: Multiplier upper bound (>= min_factor).
        seed: Optional RNG seed for reproducible tests.
    """

    min_factor: float = 0.8
    max_factor: float = 1.2
    seed: Optional[int] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.min_factor < 0.0:
            raise JitterError("min_factor must be >= 0.0")
        if self.max_factor < self.min_factor:
            raise JitterError("max_factor must be >= min_factor")

    # ------------------------------------------------------------------
    def apply(self, base_seconds: float) -> float:
        """Return *base_seconds* multiplied by a random factor in [min, max]."""
        if base_seconds < 0:
            raise JitterError("base_seconds must be >= 0")
        rng = random.Random(self.seed)
        factor = rng.uniform(self.min_factor, self.max_factor)
        return base_seconds * factor

    def to_dict(self) -> dict:
        return {
            "min_factor": self.min_factor,
            "max_factor": self.max_factor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JitterPolicy":
        return cls(
            min_factor=float(data.get("min_factor", 0.8)),
            max_factor=float(data.get("max_factor", 1.2)),
        )


def full_jitter(base_seconds: float, seed: Optional[int] = None) -> float:
    """Uniform jitter in [0, base_seconds] — common AWS pattern."""
    if base_seconds < 0:
        raise JitterError("base_seconds must be >= 0")
    rng = random.Random(seed)
    return rng.uniform(0.0, base_seconds)


def equal_jitter(base_seconds: float, seed: Optional[int] = None) -> float:
    """Half fixed + half random — reduces thundering herd while keeping
    a minimum delay.
    """
    if base_seconds < 0:
        raise JitterError("base_seconds must be >= 0")
    half = base_seconds / 2.0
    rng = random.Random(seed)
    return half + rng.uniform(0.0, half)
