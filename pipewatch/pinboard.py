"""pinboard.py — Named key-value pin store for pipeline run metadata.

Allows pipelines to pin arbitrary string values under named keys,
persisted to disk as JSON for inspection and cross-run sharing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class PinboardError(Exception):
    """Raised when a pinboard operation fails."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PinEntry:
    key: str
    value: str
    pinned_at: str

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "pinned_at": self.pinned_at}

    @classmethod
    def from_dict(cls, data: dict) -> "PinEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            pinned_at=data["pinned_at"],
        )


class Pinboard:
    """Persistent named pin store backed by a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._pins: Dict[str, PinEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._pins = {k: PinEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._pins.items()}, indent=2))

    def pin(self, key: str, value: str) -> PinEntry:
        """Set or overwrite a pin."""
        if not key or not key.strip():
            raise PinboardError("Pin key must not be empty.")
        if not isinstance(value, str):
            raise PinboardError("Pin value must be a string.")
        entry = PinEntry(key=key, value=value, pinned_at=_utcnow())
        self._pins[key] = entry
        self._save()
        return entry

    def get(self, key: str) -> Optional[PinEntry]:
        """Return the pin entry for *key*, or None if absent."""
        return self._pins.get(key)

    def remove(self, key: str) -> bool:
        """Remove a pin by key. Returns True if it existed."""
        if key in self._pins:
            del self._pins[key]
            self._save()
            return True
        return False

    def all(self) -> List[PinEntry]:
        """Return all pins sorted by key."""
        return [self._pins[k] for k in sorted(self._pins)]

    def clear(self) -> None:
        """Remove all pins."""
        self._pins.clear()
        self._save()

    def __len__(self) -> int:
        return len(self._pins)
