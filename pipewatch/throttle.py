"""Rate-limiting / throttle guard for notifications.

Prevents alert fatigue by suppressing duplicate notifications
for the same pipeline within a configurable cooldown window.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes


@dataclass
class ThrottleState:
    """Persisted state for a single pipeline key."""

    last_notified_at: float  # Unix timestamp
    count: int = 1


@dataclass
class Throttle:
    """Manages per-pipeline notification throttling."""

    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    state_path: Optional[Path] = None
    _state: Dict[str, ThrottleState] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.state_path is not None:
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_suppressed(self, key: str, now: Optional[float] = None) -> bool:
        """Return True if a notification for *key* should be suppressed."""
        ts = now if now is not None else time.time()
        entry = self._state.get(key)
        if entry is None:
            return False
        return (ts - entry.last_notified_at) < self.cooldown_seconds

    def record(self, key: str, now: Optional[float] = None) -> None:
        """Record that a notification was sent for *key*."""
        ts = now if now is not None else time.time()
        existing = self._state.get(key)
        count = (existing.count + 1) if existing else 1
        self._state[key] = ThrottleState(last_notified_at=ts, count=count)
        if self.state_path is not None:
            self._save()

    def reset(self, key: str) -> None:
        """Remove throttle state for *key* (e.g. after a successful run)."""
        self._state.pop(key, None)
        if self.state_path is not None:
            self._save()

    def state_for(self, key: str) -> Optional[ThrottleState]:
        return self._state.get(key)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        assert self.state_path is not None
        if not self.state_path.exists():
            return
        raw: dict = json.loads(self.state_path.read_text())
        self._state = {
            k: ThrottleState(**v) for k, v in raw.items()
        }

    def _save(self) -> None:
        assert self.state_path is not None
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            k: {"last_notified_at": v.last_notified_at, "count": v.count}
            for k, v in self._state.items()
        }
        self.state_path.write_text(json.dumps(payload, indent=2))
