"""Replay buffer — stores the last N run outcomes for a job and replays them."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ReplayBufferError(Exception):
    """Raised when the replay buffer is used incorrectly."""


@dataclass
class ReplayEntry:
    job: str
    outcome: str          # "success" | "failure"
    exit_code: int
    timestamp: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "outcome": self.outcome,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReplayEntry":
        return cls(
            job=d["job"],
            outcome=d["outcome"],
            exit_code=d["exit_code"],
            timestamp=d["timestamp"],
            note=d.get("note", ""),
        )


@dataclass
class ReplayBuffer:
    path: Path
    capacity: int = 50
    _entries: List[ReplayEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ReplayBufferError("capacity must be >= 1")
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._entries = [ReplayEntry.from_dict(r) for r in raw]
        else:
            self._entries = []

    def _save(self) -> None:
        self.path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    # ------------------------------------------------------------------
    def push(self, entry: ReplayEntry) -> ReplayEntry:
        """Append *entry*, evicting the oldest when capacity is exceeded."""
        if not entry.job:
            raise ReplayBufferError("job must not be empty")
        self._entries.append(entry)
        if len(self._entries) > self.capacity:
            self._entries = self._entries[-self.capacity:]
        self._save()
        return entry

    def all(self) -> List[ReplayEntry]:
        return list(self._entries)

    def for_job(self, job: str) -> List[ReplayEntry]:
        return [e for e in self._entries if e.job == job]

    def latest(self, job: str) -> Optional[ReplayEntry]:
        entries = self.for_job(job)
        return entries[-1] if entries else None

    def clear(self) -> None:
        self._entries = []
        self._save()
