"""Checkpoint support for tracking pipeline stage progress."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CheckpointEntry:
    stage: str
    status: str          # "ok" | "failed" | "skipped"
    timestamp: float = field(default_factory=time.time)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "timestamp": self.timestamp,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointEntry":
        return cls(
            stage=data["stage"],
            status=data["status"],
            timestamp=data.get("timestamp", 0.0),
            message=data.get("message", ""),
        )


class Checkpoint:
    """Persists pipeline stage checkpoints to a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: List[CheckpointEntry] = []
        if path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mark(self, stage: str, status: str, message: str = "") -> CheckpointEntry:
        """Record a stage result and persist immediately."""
        if status not in {"ok", "failed", "skipped"}:
            raise ValueError(f"Invalid status: {status!r}")
        entry = CheckpointEntry(stage=stage, status=status, message=message)
        self._entries.append(entry)
        self._save()
        return entry

    def last(self, stage: str) -> Optional[CheckpointEntry]:
        """Return the most recent entry for *stage*, or None."""
        for entry in reversed(self._entries):
            if entry.stage == stage:
                return entry
        return None

    def stages(self) -> List[str]:
        """Return ordered list of unique stage names recorded."""
        seen: Dict[str, None] = {}
        for e in self._entries:
            seen[e.stage] = None
        return list(seen)

    def all(self) -> List[CheckpointEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        if self._path.exists():
            self._path.unlink()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([e.to_dict() for e in self._entries], indent=2)
        )

    def _load(self) -> None:
        data = json.loads(self._path.read_text())
        self._entries = [CheckpointEntry.from_dict(d) for d in data]
