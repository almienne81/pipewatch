"""Tombstone — record permanent end-of-life markers for pipeline jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class TombstoneError(Exception):
    """Raised when a tombstone operation fails."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TombstoneEntry:
    job: str
    reason: str
    retired_at: datetime
    retired_by: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "reason": self.reason,
            "retired_at": self.retired_at.isoformat(),
            "retired_by": self.retired_by,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TombstoneEntry":
        return cls(
            job=data["job"],
            reason=data["reason"],
            retired_at=datetime.fromisoformat(data["retired_at"]),
            retired_by=data.get("retired_by", ""),
            note=data.get("note", ""),
        )


class Tombstone:
    """Persistent store for retired pipeline job markers."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def _load(self) -> List[TombstoneEntry]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            raw = json.load(fh)
        return [TombstoneEntry.from_dict(r) for r in raw]

    def _save(self, entries: List[TombstoneEntry]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump([e.to_dict() for e in entries], fh, indent=2)

    def retire(self, job: str, reason: str, retired_by: str = "", note: str = "") -> TombstoneEntry:
        if not job:
            raise TombstoneError("job name must not be empty")
        if not reason:
            raise TombstoneError("reason must not be empty")
        entries = self._load()
        if any(e.job == job for e in entries):
            raise TombstoneError(f"job '{job}' is already retired")
        entry = TombstoneEntry(job=job, reason=reason, retired_at=_utcnow(),
                               retired_by=retired_by, note=note)
        entries.append(entry)
        self._save(entries)
        return entry

    def get(self, job: str) -> Optional[TombstoneEntry]:
        return next((e for e in self._load() if e.job == job), None)

    def is_retired(self, job: str) -> bool:
        return self.get(job) is not None

    def all(self) -> List[TombstoneEntry]:
        return self._load()

    def remove(self, job: str) -> bool:
        entries = self._load()
        new = [e for e in entries if e.job != job]
        if len(new) == len(entries):
            return False
        self._save(new)
        return True

    def clear(self) -> int:
        entries = self._load()
        self._save([])
        return len(entries)
