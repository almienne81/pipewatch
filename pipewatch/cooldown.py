"""Cooldown tracker: suppress repeated alerts for the same pipeline key."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class CooldownError(Exception):
    """Raised when the cooldown state file cannot be read or written."""


@dataclass
class CooldownEntry:
    key: str
    last_alerted: float  # Unix timestamp
    alert_count: int = 1

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "last_alerted": self.last_alerted,
            "alert_count": self.alert_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CooldownEntry":
        return cls(
            key=data["key"],
            last_alerted=float(data["last_alerted"]),
            alert_count=int(data.get("alert_count", 1)),
        )


@dataclass
class Cooldown:
    """Persist per-key cooldown state to a JSON file."""

    path: Path
    default_seconds: float = 300.0
    _state: Dict[str, CooldownEntry] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self.path.exists():
            self._state = {}
            return
        try:
            raw = json.loads(self.path.read_text())
            self._state = {k: CooldownEntry.from_dict(v) for k, v in raw.items()}
        except Exception as exc:  # noqa: BLE001
            raise CooldownError(f"Cannot load cooldown state from {self.path}: {exc}") from exc

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({k: v.to_dict() for k, v in self._state.items()}, indent=2))
        except Exception as exc:  # noqa: BLE001
            raise CooldownError(f"Cannot save cooldown state to {self.path}: {exc}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_suppressed(self, key: str, cooldown_seconds: Optional[float] = None) -> bool:
        """Return True if *key* is within its cooldown window."""
        seconds = cooldown_seconds if cooldown_seconds is not None else self.default_seconds
        entry = self._state.get(key)
        if entry is None:
            return False
        return (time.time() - entry.last_alerted) < seconds

    def record(self, key: str) -> CooldownEntry:
        """Record that an alert was just sent for *key*; persist to disk."""
        existing = self._state.get(key)
        count = (existing.alert_count + 1) if existing else 1
        entry = CooldownEntry(key=key, last_alerted=time.time(), alert_count=count)
        self._state[key] = entry
        self._save()
        return entry

    def reset(self, key: str) -> None:
        """Remove cooldown state for *key*."""
        self._state.pop(key, None)
        self._save()

    def all_entries(self) -> list:
        return list(self._state.values())
