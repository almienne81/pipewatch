"""Anomaly detection for pipeline run durations using z-score analysis."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


class AnomalyError(Exception):
    """Raised when anomaly detection configuration is invalid."""


@dataclass
class AnomalyPolicy:
    """Policy for z-score based anomaly detection."""

    min_samples: int = 5
    z_threshold: float = 2.5

    def __post_init__(self) -> None:
        if self.min_samples < 2:
            raise AnomalyError("min_samples must be >= 2")
        if self.z_threshold <= 0:
            raise AnomalyError("z_threshold must be positive")

    def to_dict(self) -> dict:
        return {"min_samples": self.min_samples, "z_threshold": self.z_threshold}

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyPolicy":
        return cls(
            min_samples=int(data.get("min_samples", 5)),
            z_threshold=float(data.get("z_threshold", 2.5)),
        )


@dataclass
class AnomalyResult:
    """Result of an anomaly check."""

    value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool
    sufficient_data: bool

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "mean": self.mean,
            "stddev": self.stddev,
            "z_score": self.z_score,
            "is_anomaly": self.is_anomaly,
            "sufficient_data": self.sufficient_data,
        }


def _mean(samples: List[float]) -> float:
    return sum(samples) / len(samples)


def _stddev(samples: List[float], mean: float) -> float:
    variance = sum((x - mean) ** 2 for x in samples) / len(samples)
    return math.sqrt(variance)


def check_anomaly(
    value: float,
    history: List[float],
    policy: Optional[AnomalyPolicy] = None,
) -> AnomalyResult:
    """Check whether *value* is anomalous relative to *history*.

    If there are fewer samples than ``policy.min_samples``, ``sufficient_data``
    is False and ``is_anomaly`` is always False.
    """
    if policy is None:
        policy = AnomalyPolicy()

    if len(history) < policy.min_samples:
        return AnomalyResult(
            value=value,
            mean=0.0,
            stddev=0.0,
            z_score=0.0,
            is_anomaly=False,
            sufficient_data=False,
        )

    mu = _mean(history)
    sigma = _stddev(history, mu)

    if sigma == 0.0:
        z = 0.0
    else:
        z = abs(value - mu) / sigma

    return AnomalyResult(
        value=value,
        mean=mu,
        stddev=sigma,
        z_score=z,
        is_anomaly=z > policy.z_threshold,
        sufficient_data=True,
    )
