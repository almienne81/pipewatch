"""Suppress repeated alerts for a job within a configurable window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class SuppressError(Exception):
    """Raised when suppress configuration is invalid."""


@dataclass
class SuppressEntry:
    job: str
    suppressed_until: float  # Unix timestamp
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "suppressed_until": self.suppressed_until,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SuppressEntry":
        return cls(
            job=data["job"],
            suppressed_until=float(data["suppressed_until"]),
            reason=data.get("reason", ""),
        )


@dataclass
class Suppress:
    """Persist and check per-job alert suppression windows."""

    path: Path
    _state: Dict[str, SuppressEntry] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._state = {
                k: SuppressEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._state.items()}, indent=2)
        )

    def is_suppressed(self, job: str) -> bool:
        """Return True if the job is currently suppressed."""
        entry = self._state.get(job)
        if entry is None:
            return False
        return time.time() < entry.suppressed_until

    def suppress(self, job: str, duration_seconds: float, reason: str = "") -> SuppressEntry:
        """Suppress alerts for *job* for *duration_seconds* seconds."""
        if duration_seconds <= 0:
            raise SuppressError("duration_seconds must be positive")
        if not job:
            raise SuppressError("job name must not be empty")
        entry = SuppressEntry(
            job=job,
            suppressed_until=time.time() + duration_seconds,
            reason=reason,
        )
        self._state[job] = entry
        self._save()
        return entry

    def release(self, job: str) -> bool:
        """Remove suppression for *job*. Returns True if an entry existed."""
        if job in self._state:
            del self._state[job]
            self._save()
            return True
        return False

    def all_entries(self) -> list:
        """Return all SuppressEntry objects, active or expired."""
        return list(self._state.values())

    def active_entries(self) -> list:
        """Return only currently active (non-expired) entries."""
        now = time.time()
        return [e for e in self._state.values() if now < e.suppressed_until]
