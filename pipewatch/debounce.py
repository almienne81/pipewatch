"""Debounce: suppress repeated alerts until a quiet period has elapsed."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class DebounceError(ValueError):
    """Raised when debounce configuration is invalid."""


@dataclass
class DebounceState:
    last_trigger: float  # epoch seconds
    count: int = 1

    def to_dict(self) -> dict:
        return {"last_trigger": self.last_trigger, "count": self.count}

    @classmethod
    def from_dict(cls, data: dict) -> "DebounceState":
        return cls(last_trigger=float(data["last_trigger"]), count=int(data.get("count", 1)))


@dataclass
class Debounce:
    """Suppress a notification key until *quiet_seconds* have passed with no new triggers."""

    quiet_seconds: float
    state_file: Path
    _state: Dict[str, DebounceState] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.quiet_seconds <= 0:
            raise DebounceError("quiet_seconds must be positive")
        self.state_file = Path(self.state_file)
        self._load()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.state_file.exists():
            raw = json.loads(self.state_file.read_text())
            self._state = {k: DebounceState.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({k: v.to_dict() for k, v in self._state.items()}))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def trigger(self, key: str, *, now: Optional[float] = None) -> bool:
        """Record a trigger for *key*.

        Returns ``True`` if the notification should be **sent** (first trigger
        or quiet period has elapsed since the last one), ``False`` if it should
        be suppressed.
        """
        ts = now if now is not None else time.time()
        entry = self._state.get(key)

        if entry is None or (ts - entry.last_trigger) >= self.quiet_seconds:
            self._state[key] = DebounceState(last_trigger=ts, count=1)
            self._save()
            return True

        # within quiet window — bump count, suppress
        entry.last_trigger = ts
        entry.count += 1
        self._save()
        return False

    def reset(self, key: str) -> None:
        """Manually clear the debounce state for *key*."""
        self._state.pop(key, None)
        self._save()

    def state_for(self, key: str) -> Optional[DebounceState]:
        return self._state.get(key)
