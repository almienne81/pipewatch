"""Correlation ID generation and propagation for pipeline runs."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class CorrelationError(Exception):
    """Raised when correlation ID operations fail."""


@dataclass
class CorrelationEntry:
    correlation_id: str
    job: str
    parent_id: Optional[str]
    created_at: datetime
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "correlation_id": self.correlation_id,
            "job": self.job,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CorrelationEntry":
        return cls(
            correlation_id=data["correlation_id"],
            job=data["job"],
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            note=data.get("note", ""),
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CorrelationStore:
    """Persist and retrieve correlation entries from a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, records: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(records, indent=2))

    def generate(
        self,
        job: str,
        parent_id: Optional[str] = None,
        note: str = "",
    ) -> CorrelationEntry:
        if not job:
            raise CorrelationError("job must not be empty")
        entry = CorrelationEntry(
            correlation_id=str(uuid.uuid4()),
            job=job,
            parent_id=parent_id,
            created_at=_utcnow(),
            note=note,
        )
        records = self._load()
        records.append(entry.to_dict())
        self._save(records)
        return entry

    def list(self, job: Optional[str] = None) -> list[CorrelationEntry]:
        records = self._load()
        entries = [CorrelationEntry.from_dict(r) for r in records]
        if job:
            entries = [e for e in entries if e.job == job]
        return entries

    def get(self, correlation_id: str) -> Optional[CorrelationEntry]:
        for r in self._load():
            if r.get("correlation_id") == correlation_id:
                return CorrelationEntry.from_dict(r)
        return None

    def clear(self) -> None:
        self._save([])
