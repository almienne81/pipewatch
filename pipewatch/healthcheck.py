"""Health check module for pipewatch pipelines.

Provides a simple way to evaluate pipeline health based on recent run history
and configurable thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class HealthThresholds:
    """Configurable thresholds for health evaluation."""

    min_success_rate: float = 0.8   # 0.0 – 1.0
    max_consecutive_failures: int = 3
    min_runs: int = 1

    def __post_init__(self) -> None:
        if not (0.0 <= self.min_success_rate <= 1.0):
            raise ValueError("min_success_rate must be between 0.0 and 1.0")
        if self.max_consecutive_failures < 1:
            raise ValueError("max_consecutive_failures must be >= 1")
        if self.min_runs < 1:
            raise ValueError("min_runs must be >= 1")


@dataclass(frozen=True)
class HealthReport:
    """Result of a health evaluation."""

    healthy: bool
    total_runs: int
    success_rate: Optional[float]
    consecutive_failures: int
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "total_runs": self.total_runs,
            "success_rate": self.success_rate,
            "consecutive_failures": self.consecutive_failures,
            "reasons": list(self.reasons),
        }


def _consecutive_failures(outcomes: list[bool]) -> int:
    """Count trailing consecutive False values in *outcomes*."""
    count = 0
    for outcome in reversed(outcomes):
        if not outcome:
            count += 1
        else:
            break
    return count


def evaluate_health(
    outcomes: list[bool],
    thresholds: Optional[HealthThresholds] = None,
) -> HealthReport:
    """Evaluate pipeline health from a list of boolean run outcomes.

    Parameters
    ----------
    outcomes:
        Ordered list of run outcomes (True = success, False = failure),
        oldest first.
    thresholds:
        Thresholds to apply.  Defaults to :class:`HealthThresholds` defaults.
    """
    if thresholds is None:
        thresholds = HealthThresholds()

    total = len(outcomes)
    reasons: list[str] = []

    if total < thresholds.min_runs:
        return HealthReport(
            healthy=False,
            total_runs=total,
            success_rate=None,
            consecutive_failures=0,
            reasons=[f"insufficient runs: {total} < {thresholds.min_runs}"],
        )

    rate = sum(outcomes) / total
    consec = _consecutive_failures(outcomes)

    if rate < thresholds.min_success_rate:
        reasons.append(
            f"success rate {rate:.0%} below threshold {thresholds.min_success_rate:.0%}"
        )
    if consec >= thresholds.max_consecutive_failures:
        reasons.append(
            f"{consec} consecutive failures >= threshold {thresholds.max_consecutive_failures}"
        )

    return HealthReport(
        healthy=len(reasons) == 0,
        total_runs=total,
        success_rate=rate,
        consecutive_failures=consec,
        reasons=reasons,
    )
