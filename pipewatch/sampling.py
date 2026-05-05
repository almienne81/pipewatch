"""Sampling policy for selectively recording pipeline runs."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


class SamplingError(ValueError):
    """Raised when a sampling policy is misconfigured."""


@dataclass
class SamplingPolicy:
    """Defines how frequently pipeline events should be sampled.

    Attributes:
        rate: Probability in [0.0, 1.0] that a given event is kept.
        seed: Optional RNG seed for deterministic behaviour in tests.
    """

    rate: float = 1.0
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not (0.0 <= self.rate <= 1.0):
            raise SamplingError(
                f"rate must be between 0.0 and 1.0, got {self.rate}"
            )
        self._rng = random.Random(self.seed)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def should_sample(self) -> bool:
        """Return True if this event should be recorded."""
        if self.rate == 1.0:
            return True
        if self.rate == 0.0:
            return False
        return self._rng.random() < self.rate

    def to_dict(self) -> dict:
        return {"rate": self.rate, "seed": self.seed}

    @classmethod
    def from_dict(cls, data: dict) -> "SamplingPolicy":
        return cls(
            rate=float(data.get("rate", 1.0)),
            seed=data.get("seed"),
        )


def sample_filter(policy: SamplingPolicy, items: list) -> list:
    """Return a subset of *items* according to *policy*.

    Each item is independently kept with probability ``policy.rate``.
    """
    if policy.rate == 1.0:
        return list(items)
    if policy.rate == 0.0:
        return []
    return [item for item in items if policy.should_sample()]
