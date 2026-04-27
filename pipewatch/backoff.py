"""Exponential backoff calculator for retry delays."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


class BackoffError(ValueError):
    """Raised when backoff parameters are invalid."""


@dataclass(frozen=True)
class BackoffPolicy:
    """Defines an exponential backoff strategy."""

    base_seconds: float = 1.0
    multiplier: float = 2.0
    max_seconds: float = 300.0
    jitter: bool = False

    def __post_init__(self) -> None:
        if self.base_seconds <= 0:
            raise BackoffError("base_seconds must be positive")
        if self.multiplier < 1.0:
            raise BackoffError("multiplier must be >= 1.0")
        if self.max_seconds < self.base_seconds:
            raise BackoffError("max_seconds must be >= base_seconds")

    def delay(self, attempt: int) -> float:
        """Return the delay in seconds for the given attempt number (0-indexed)."""
        if attempt < 0:
            raise BackoffError("attempt must be >= 0")
        raw = self.base_seconds * (self.multiplier ** attempt)
        capped = min(raw, self.max_seconds)
        if self.jitter:
            import random
            capped = random.uniform(0.0, capped)
        return capped

    def delays(self, attempts: int) -> list[float]:
        """Return a list of delays for *attempts* retry steps."""
        return [self.delay(i) for i in range(attempts)]

    def to_dict(self) -> dict:
        return {
            "base_seconds": self.base_seconds,
            "multiplier": self.multiplier,
            "max_seconds": self.max_seconds,
            "jitter": self.jitter,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackoffPolicy":
        return cls(
            base_seconds=float(data.get("base_seconds", 1.0)),
            multiplier=float(data.get("multiplier", 2.0)),
            max_seconds=float(data.get("max_seconds", 300.0)),
            jitter=bool(data.get("jitter", False)),
        )


def format_delay(seconds: float) -> str:
    """Return a human-readable delay string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"
