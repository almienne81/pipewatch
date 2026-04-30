"""Dead-letter queue for failed pipeline events that could not be delivered."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DeadLetterEntry:
    job: str
    reason: str
    payload: dict
    timestamp: datetime
    attempts: int = 1

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "reason": self.reason,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "attempts": self.attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeadLetterEntry":
        return cls(
            job=data["job"],
            reason=data["reason"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            attempts=data.get("attempts", 1),
        )


class DeadLetterQueue:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def _load(self) -> List[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text())

    def _save(self, entries: List[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(entries, indent=2))

    def push(self, job: str, reason: str, payload: dict) -> DeadLetterEntry:
        """Record a failed delivery event."""
        entry = DeadLetterEntry(
            job=job,
            reason=reason,
            payload=payload,
            timestamp=_utcnow(),
        )
        raw = self._load()
        raw.append(entry.to_dict())
        self._save(raw)
        return entry

    def all(self) -> List[DeadLetterEntry]:
        """Return all dead-letter entries."""
        return [DeadLetterEntry.from_dict(r) for r in self._load()]

    def for_job(self, job: str) -> List[DeadLetterEntry]:
        """Return dead-letter entries for a specific job."""
        return [e for e in self.all() if e.job == job]

    def clear(self, job: Optional[str] = None) -> int:
        """Remove entries. If job is given, only remove entries for that job."""
        raw = self._load()
        if job is None:
            count = len(raw)
            self._save([])
            return count
        kept = [r for r in raw if r["job"] != job]
        removed = len(raw) - len(kept)
        self._save(kept)
        return removed
