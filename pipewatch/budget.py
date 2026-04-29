"""Runtime budget tracking — warn or fail when a job exceeds a time budget."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


class BudgetError(ValueError):
    """Raised when a budget configuration is invalid."""


@dataclass
class BudgetPolicy:
    """Defines a soft (warn) and hard (fail) time budget in seconds."""

    warn_seconds: Optional[float] = None
    fail_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        for attr in ("warn_seconds", "fail_seconds"):
            val = getattr(self, attr)
            if val is not None and val <= 0:
                raise BudgetError(f"{attr} must be a positive number, got {val!r}")
        if (
            self.warn_seconds is not None
            and self.fail_seconds is not None
            and self.warn_seconds >= self.fail_seconds
        ):
            raise BudgetError(
                "warn_seconds must be less than fail_seconds"
            )

    def to_dict(self) -> dict:
        return {"warn_seconds": self.warn_seconds, "fail_seconds": self.fail_seconds}

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetPolicy":
        return cls(
            warn_seconds=data.get("warn_seconds"),
            fail_seconds=data.get("fail_seconds"),
        )


@dataclass
class BudgetResult:
    """Outcome of checking elapsed time against a budget."""

    elapsed: float
    warned: bool = False
    failed: bool = False
    message: str = ""


def check_budget(policy: BudgetPolicy, elapsed: float) -> BudgetResult:
    """Return a BudgetResult describing whether the budget was exceeded."""
    result = BudgetResult(elapsed=elapsed)
    if policy.fail_seconds is not None and elapsed >= policy.fail_seconds:
        result.failed = True
        result.message = (
            f"Job exceeded hard budget: {elapsed:.1f}s >= {policy.fail_seconds:.1f}s"
        )
    elif policy.warn_seconds is not None and elapsed >= policy.warn_seconds:
        result.warned = True
        result.message = (
            f"Job exceeded soft budget: {elapsed:.1f}s >= {policy.warn_seconds:.1f}s"
        )
    return result
