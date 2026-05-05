"""SLA budget tracking: monitors how much error budget remains within a rolling window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


class SLABudgetError(Exception):
    """Raised when SLA budget configuration is invalid."""


@dataclass
class SLABudgetPolicy:
    target_success_rate: float = 0.99  # e.g. 0.99 = 99%
    window_seconds: int = 86400  # rolling window, default 24 h

    def __post_init__(self) -> None:
        if not (0.0 < self.target_success_rate <= 1.0):
            raise SLABudgetError(
                f"target_success_rate must be in (0, 1], got {self.target_success_rate}"
            )
        if self.window_seconds <= 0:
            raise SLABudgetError(
                f"window_seconds must be positive, got {self.window_seconds}"
            )

    def to_dict(self) -> dict:
        return {
            "target_success_rate": self.target_success_rate,
            "window_seconds": self.window_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SLABudgetPolicy":
        return cls(
            target_success_rate=float(data.get("target_success_rate", 0.99)),
            window_seconds=int(data.get("window_seconds", 86400)),
        )


@dataclass
class SLABudgetReport:
    total_runs: int
    successful_runs: int
    failed_runs: int
    actual_success_rate: Optional[float]  # None when no runs
    error_budget_remaining: Optional[float]  # fraction of budget left, None when no runs
    exhausted: bool
    policy: SLABudgetPolicy

    def to_dict(self) -> dict:
        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "actual_success_rate": self.actual_success_rate,
            "error_budget_remaining": self.error_budget_remaining,
            "exhausted": self.exhausted,
            "policy": self.policy.to_dict(),
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def evaluate_budget(
    outcomes: List[tuple],  # list of (timestamp: datetime, success: bool)
    policy: SLABudgetPolicy,
    now: Optional[datetime] = None,
) -> SLABudgetReport:
    """Evaluate SLA budget against a list of (timestamp, success) outcome tuples."""
    if now is None:
        now = _utcnow()

    cutoff = now.timestamp() - policy.window_seconds
    recent = [(ts, ok) for ts, ok in outcomes if ts.timestamp() >= cutoff]

    total = len(recent)
    successes = sum(1 for _, ok in recent if ok)
    failures = total - successes

    if total == 0:
        return SLABudgetReport(
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            actual_success_rate=None,
            error_budget_remaining=None,
            exhausted=False,
            policy=policy,
        )

    actual_rate = successes / total
    # allowed_failures = total * (1 - target); budget_remaining = allowed - actual_failures
    allowed_failures = total * (1.0 - policy.target_success_rate)
    budget_remaining = max(0.0, allowed_failures - failures) / max(allowed_failures, 1e-9)
    exhausted = failures > allowed_failures

    return SLABudgetReport(
        total_runs=total,
        successful_runs=successes,
        failed_runs=failures,
        actual_success_rate=round(actual_rate, 6),
        error_budget_remaining=round(budget_remaining, 6),
        exhausted=exhausted,
        policy=policy,
    )
