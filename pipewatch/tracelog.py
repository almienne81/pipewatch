"""Structured trace log for recording pipeline execution spans."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TraceEntry:
    job: str
    span: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str = "ok"
    meta: dict = field(default_factory=dict)

    def duration_seconds(self) -> Optional[float]:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "span": self.span,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TraceEntry":
        ended_raw = d.get("ended_at")
        return cls(
            job=d["job"],
            span=d["span"],
            started_at=datetime.fromisoformat(d["started_at"]),
            ended_at=datetime.fromisoformat(ended_raw) if ended_raw else None,
            status=d.get("status", "ok"),
            meta=d.get("meta", {}),
        )


class TraceLog:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def _load(self) -> List[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text())

    def _save(self, entries: List[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(entries, indent=2))

    def record(self, job: str, span: str, status: str = "ok", meta: dict | None = None) -> TraceEntry:
        entry = TraceEntry(
            job=job,
            span=span,
            started_at=_utcnow(),
            ended_at=_utcnow(),
            status=status,
            meta=meta or {},
        )
        rows = self._load()
        rows.append(entry.to_dict())
        self._save(rows)
        return entry

    def all(self) -> List[TraceEntry]:
        return [TraceEntry.from_dict(r) for r in self._load()]

    def filter_job(self, job: str) -> List[TraceEntry]:
        return [e for e in self.all() if e.job == job]

    def filter_span(self, span: str) -> List[TraceEntry]:
        return [e for e in self.all() if e.span == span]

    def clear(self) -> None:
        self._save([])
