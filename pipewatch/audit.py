"""Audit log: records significant pipeline lifecycle events to a JSONL file."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEvent:
    job: str
    event: str  # e.g. "start", "success", "failure", "retry", "alert_sent"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[str] = None
    exit_code: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "exit_code": self.exit_code,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditEvent":
        return AuditEvent(
            job=d["job"],
            event=d["event"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            details=d.get("details"),
            exit_code=d.get("exit_code"),
        )


class Audit:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def record(self, event: AuditEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict()) + "\n")

    def all(self) -> List[AuditEvent]:
        if not self._path.exists():
            return []
        events: List[AuditEvent] = []
        with self._path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(AuditEvent.from_dict(json.loads(line)))
        return events

    def for_job(self, job: str) -> List[AuditEvent]:
        return [e for e in self.all() if e.job == job]

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
