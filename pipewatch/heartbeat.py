"""Heartbeat tracker for long-running pipeline jobs.

Records periodic "still alive" pings for a named job and exposes
helpers to check whether a job has gone silent.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class HeartbeatEntry:
    job: str
    timestamp: float  # epoch seconds
    note: str = ""

    def to_dict(self) -> Dict:
        return {"job": self.job, "timestamp": self.timestamp, "note": self.note}

    @classmethod
    def from_dict(cls, data: Dict) -> "HeartbeatEntry":
        return cls(
            job=data["job"],
            timestamp=float(data["timestamp"]),
            note=data.get("note", ""),
        )


@dataclass
class Heartbeat:
    path: Path
    _entries: List[HeartbeatEntry] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._load()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._entries = [HeartbeatEntry.from_dict(r) for r in raw]
        else:
            self._entries = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def ping(self, job: str, note: str = "") -> HeartbeatEntry:
        """Record a heartbeat for *job* at the current wall-clock time."""
        entry = HeartbeatEntry(job=job, timestamp=time.time(), note=note)
        self._entries.append(entry)
        self._save()
        return entry

    def last(self, job: str) -> Optional[HeartbeatEntry]:
        """Return the most recent heartbeat for *job*, or None."""
        matches = [e for e in self._entries if e.job == job]
        return matches[-1] if matches else None

    def is_stale(self, job: str, max_age_seconds: float) -> bool:
        """Return True if no heartbeat has been seen within *max_age_seconds*."""
        entry = self.last(job)
        if entry is None:
            return True
        return (time.time() - entry.timestamp) > max_age_seconds

    def all_entries(self, job: Optional[str] = None) -> List[HeartbeatEntry]:
        if job is None:
            return list(self._entries)
        return [e for e in self._entries if e.job == job]

    def clear(self, job: Optional[str] = None) -> None:
        if job is None:
            self._entries = []
        else:
            self._entries = [e for e in self._entries if e.job != job]
        self._save()
