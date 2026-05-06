"""Concurrency limiter — cap the number of simultaneous pipeline runs."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ConcurrencyError(Exception):
    """Raised when a concurrency limit is violated."""


@dataclass
class ConcurrencyPolicy:
    max_concurrent: int = 1
    timeout_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.max_concurrent < 1:
            raise ConcurrencyError(
                f"max_concurrent must be >= 1, got {self.max_concurrent}"
            )
        if self.timeout_seconds is not None and self.timeout_seconds < 0:
            raise ConcurrencyError(
                f"timeout_seconds must be >= 0, got {self.timeout_seconds}"
            )

    def to_dict(self) -> dict:
        return {
            "max_concurrent": self.max_concurrent,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConcurrencyPolicy":
        return cls(
            max_concurrent=int(data.get("max_concurrent", 1)),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass
class ConcurrencySlot:
    pid: int
    job: str
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"pid": self.pid, "job": self.job, "started_at": self.started_at}

    @classmethod
    def from_dict(cls, data: dict) -> "ConcurrencySlot":
        return cls(
            pid=int(data["pid"]),
            job=str(data["job"]),
            started_at=float(data["started_at"]),
        )


class ConcurrencyLimiter:
    """File-backed concurrency limiter."""

    def __init__(self, path: Path, policy: ConcurrencyPolicy) -> None:
        self._path = path
        self._policy = policy

    def _load(self) -> List[ConcurrencySlot]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text())
            return [ConcurrencySlot.from_dict(s) for s in raw]
        except (json.JSONDecodeError, KeyError):
            return []

    def _save(self, slots: List[ConcurrencySlot]) -> None:
        self._path.write_text(json.dumps([s.to_dict() for s in slots], indent=2))

    def _live_slots(self, slots: List[ConcurrencySlot]) -> List[ConcurrencySlot]:
        """Remove slots whose process is no longer running."""
        live = []
        for slot in slots:
            try:
                os.kill(slot.pid, 0)
                live.append(slot)
            except (ProcessLookupError, PermissionError):
                pass
        return live

    def acquire(self, job: str) -> ConcurrencySlot:
        """Acquire a slot or raise ConcurrencyError."""
        slots = self._live_slots(self._load())
        if len(slots) >= self._policy.max_concurrent:
            raise ConcurrencyError(
                f"Concurrency limit {self._policy.max_concurrent} reached "
                f"({len(slots)} active slots)."
            )
        slot = ConcurrencySlot(pid=os.getpid(), job=job)
        slots.append(slot)
        self._save(slots)
        return slot

    def release(self, slot: ConcurrencySlot) -> None:
        """Release a previously acquired slot."""
        slots = self._live_slots(self._load())
        slots = [s for s in slots if not (s.pid == slot.pid and s.job == slot.job)]
        self._save(slots)

    def active_slots(self) -> List[ConcurrencySlot]:
        slots = self._live_slots(self._load())
        self._save(slots)
        return slots

    def clear(self) -> None:
        self._save([])
