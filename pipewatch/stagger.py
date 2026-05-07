"""Stagger: distribute job start times to avoid thundering-herd."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


class StaggerError(Exception):
    """Raised when stagger configuration is invalid."""


@dataclass
class StaggerPolicy:
    """Policy controlling how jobs are staggered across a time window."""

    window_seconds: float = 60.0
    slots: int = 1
    offset_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise StaggerError("window_seconds must be positive")
        if self.slots < 1:
            raise StaggerError("slots must be at least 1")
        if self.offset_seconds < 0:
            raise StaggerError("offset_seconds must be non-negative")

    def to_dict(self) -> dict:
        return {
            "window_seconds": self.window_seconds,
            "slots": self.slots,
            "offset_seconds": self.offset_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StaggerPolicy":
        return cls(
            window_seconds=float(data.get("window_seconds", 60.0)),
            slots=int(data.get("slots", 1)),
            offset_seconds=float(data.get("offset_seconds", 0.0)),
        )


def slot_delay(policy: StaggerPolicy, slot_index: int) -> float:
    """Return the delay in seconds for a given slot index (0-based)."""
    if slot_index < 0 or slot_index >= policy.slots:
        raise StaggerError(
            f"slot_index {slot_index} out of range [0, {policy.slots - 1}]"
        )
    step = policy.window_seconds / policy.slots
    return policy.offset_seconds + step * slot_index


def all_delays(policy: StaggerPolicy) -> List[float]:
    """Return the list of delays for every slot."""
    return [slot_delay(policy, i) for i in range(policy.slots)]


def slot_for_job(policy: StaggerPolicy, job_name: str) -> int:
    """Deterministically assign a slot index to a job name via hash."""
    return abs(hash(job_name)) % policy.slots


def delay_for_job(policy: StaggerPolicy, job_name: str) -> float:
    """Return the stagger delay in seconds for a named job."""
    return slot_delay(policy, slot_for_job(policy, job_name))
