"""Flap detection — identifies rapidly alternating success/failure patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class FlapError(ValueError):
    """Raised when flap detection configuration is invalid."""


@dataclass(frozen=True)
class FlapPolicy:
    """Policy controlling when a job is considered to be flapping."""

    window: int = 10  # number of recent outcomes to inspect
    min_flips: int = 4  # minimum alternations required to flag as flapping

    def __post_init__(self) -> None:
        if self.window < 2:
            raise FlapError("window must be at least 2")
        if self.min_flips < 2:
            raise FlapError("min_flips must be at least 2")
        if self.min_flips >= self.window:
            raise FlapError("min_flips must be less than window")

    def to_dict(self) -> dict:
        return {"window": self.window, "min_flips": self.min_flips}

    @classmethod
    def from_dict(cls, data: dict) -> "FlapPolicy":
        return cls(
            window=int(data.get("window", 10)),
            min_flips=int(data.get("min_flips", 4)),
        )


@dataclass(frozen=True)
class FlapResult:
    """Result of a flap detection check."""

    is_flapping: bool
    flips: int
    window_size: int
    outcomes: List[bool] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_flapping": self.is_flapping,
            "flips": self.flips,
            "window_size": self.window_size,
            "outcomes": self.outcomes,
        }


def count_flips(outcomes: List[bool]) -> int:
    """Count the number of times the outcome alternates in a sequence."""
    if len(outcomes) < 2:
        return 0
    return sum(
        1 for i in range(1, len(outcomes)) if outcomes[i] != outcomes[i - 1]
    )


def detect_flap(
    outcomes: List[bool],
    policy: Optional[FlapPolicy] = None,
) -> FlapResult:
    """Detect whether a job is flapping based on recent outcomes.

    Args:
        outcomes: Ordered list of boolean outcomes (True = success).
        policy: Flap detection policy; defaults to FlapPolicy().

    Returns:
        FlapResult describing whether flapping was detected.
    """
    if policy is None:
        policy = FlapPolicy()

    window = outcomes[-policy.window :]
    flips = count_flips(window)
    is_flapping = flips >= policy.min_flips

    return FlapResult(
        is_flapping=is_flapping,
        flips=flips,
        window_size=len(window),
        outcomes=list(window),
    )
