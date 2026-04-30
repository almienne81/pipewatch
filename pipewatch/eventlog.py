"""Structured event log for recording named pipeline events with metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EventEntry:
    job: str
    event: str
    timestamp: datetime
    level: str = "info"
    message: str = ""
    meta: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "meta": dict(self.meta),
        }

    @staticmethod
    def from_dict(d: dict) -> "EventEntry":
        return EventEntry(
            job=d["job"],
            event=d["event"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            level=d.get("level", "info"),
            message=d.get("message", ""),
            meta=d.get("meta", {}),
        )


class EventLog:
    LEVELS = ("debug", "info", "warning", "error")

    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> List[dict]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            return json.load(fh)

    def _save(self, records: List[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(records, fh, indent=2)

    def record(
        self,
        job: str,
        event: str,
        *,
        level: str = "info",
        message: str = "",
        meta: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> EventEntry:
        if level not in self.LEVELS:
            raise ValueError(f"Invalid level {level!r}; choose from {self.LEVELS}")
        entry = EventEntry(
            job=job,
            event=event,
            timestamp=timestamp or datetime.now(timezone.utc),
            level=level,
            message=message,
            meta=meta or {},
        )
        records = self._load()
        records.append(entry.to_dict())
        self._save(records)
        return entry

    def all(self) -> List[EventEntry]:
        return [EventEntry.from_dict(r) for r in self._load()]

    def for_job(self, job: str) -> List[EventEntry]:
        return [e for e in self.all() if e.job == job]

    def by_level(self, level: str) -> List[EventEntry]:
        return [e for e in self.all() if e.level == level]

    def clear(self) -> None:
        self._save([])
