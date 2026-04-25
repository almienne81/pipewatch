"""Rate limiting for pipeline notifications — caps how many alerts can
be sent within a rolling time window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class RateLimitError(Exception):
    """Raised when rate-limit configuration is invalid."""


@dataclass
class RateLimitPolicy:
    """Defines the maximum number of notifications allowed within *window_seconds*."""

    max_alerts: int = 5
    window_seconds: int = 3600  # 1 hour

    def __post_init__(self) -> None:
        if self.max_alerts < 1:
            raise RateLimitError("max_alerts must be >= 1")
        if self.window_seconds < 1:
            raise RateLimitError("window_seconds must be >= 1")

    def to_dict(self) -> dict:
        return {"max_alerts": self.max_alerts, "window_seconds": self.window_seconds}

    @classmethod
    def from_dict(cls, data: dict) -> "RateLimitPolicy":
        return cls(
            max_alerts=int(data.get("max_alerts", 5)),
            window_seconds=int(data.get("window_seconds", 3600)),
        )


@dataclass
class RateLimiter:
    """Tracks alert timestamps for a given key and enforces a RateLimitPolicy."""

    policy: RateLimitPolicy
    state_path: Path
    _timestamps: List[float] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, key: str, now: Optional[float] = None) -> bool:
        """Return True if a new alert for *key* is within the rate limit."""
        now = now or time.time()
        self._prune(key, now)
        timestamps = self._timestamps_for(key)
        return len(timestamps) < self.policy.max_alerts

    def record(self, key: str, now: Optional[float] = None) -> None:
        """Record that an alert was sent for *key* at *now*."""
        now = now or time.time()
        state = self._load_raw()
        state.setdefault(key, [])
        state[key].append(now)
        self._save_raw(state)
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _timestamps_for(self, key: str) -> List[float]:
        state = self._load_raw()
        return state.get(key, [])

    def _prune(self, key: str, now: float) -> None:
        state = self._load_raw()
        cutoff = now - self.policy.window_seconds
        state[key] = [t for t in state.get(key, []) if t >= cutoff]
        self._save_raw(state)
        self._load()

    def _load(self) -> None:
        self._timestamps = []

    def _load_raw(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_raw(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state))
