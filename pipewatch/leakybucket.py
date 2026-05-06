"""Leaky-bucket rate limiter for controlling alert/event emission frequency."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class LeakyBucketError(ValueError):
    """Raised when LeakyBucketPolicy parameters are invalid."""


@dataclass
class LeakyBucketPolicy:
    capacity: float = 10.0      # maximum tokens the bucket can hold
    leak_rate: float = 1.0      # tokens leaked (removed) per second

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise LeakyBucketError("capacity must be positive")
        if self.leak_rate <= 0:
            raise LeakyBucketError("leak_rate must be positive")

    def to_dict(self) -> dict:
        return {"capacity": self.capacity, "leak_rate": self.leak_rate}

    @classmethod
    def from_dict(cls, data: dict) -> "LeakyBucketPolicy":
        return cls(
            capacity=float(data.get("capacity", 10.0)),
            leak_rate=float(data.get("leak_rate", 1.0)),
        )


@dataclass
class _BucketState:
    level: float = 0.0
    last_checked: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"level": self.level, "last_checked": self.last_checked}

    @classmethod
    def from_dict(cls, data: dict) -> "_BucketState":
        return cls(level=float(data["level"]), last_checked=float(data["last_checked"]))


class LeakyBucket:
    """Persistent leaky-bucket rate limiter keyed by job name."""

    def __init__(self, path: Path, policy: LeakyBucketPolicy) -> None:
        self._path = path
        self._policy = policy
        self._states: dict[str, _BucketState] = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._states = {k: _BucketState.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._states.items()}))

    # ------------------------------------------------------------------
    def _leak(self, state: _BucketState, now: Optional[float] = None) -> None:
        """Drain tokens that have leaked since last check."""
        now = now if now is not None else time.time()
        elapsed = max(0.0, now - state.last_checked)
        state.level = max(0.0, state.level - elapsed * self._policy.leak_rate)
        state.last_checked = now

    def allow(self, key: str, cost: float = 1.0, now: Optional[float] = None) -> bool:
        """Return True and consume *cost* tokens if the bucket has room."""
        if not key:
            raise LeakyBucketError("key must not be empty")
        state = self._states.setdefault(key, _BucketState(last_checked=now or time.time()))
        self._leak(state, now)
        if state.level + cost <= self._policy.capacity:
            state.level += cost
            self._save()
            return True
        self._save()
        return False

    def level(self, key: str, now: Optional[float] = None) -> float:
        """Return the current fill level for *key* after leaking."""
        state = self._states.get(key)
        if state is None:
            return 0.0
        self._leak(state, now)
        self._save()
        return state.level

    def reset(self, key: str) -> None:
        """Empty the bucket for *key*."""
        if key in self._states:
            del self._states[key]
            self._save()
