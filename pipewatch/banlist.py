"""banlist.py — track and enforce a list of banned/blocked job identifiers."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class BanlistError(Exception):
    """Raised when a banlist operation fails."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BanEntry:
    job: str
    reason: str
    banned_at: datetime
    banned_by: str = "system"

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "reason": self.reason,
            "banned_at": self.banned_at.isoformat(),
            "banned_by": self.banned_by,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BanEntry":
        return cls(
            job=d["job"],
            reason=d["reason"],
            banned_at=datetime.fromisoformat(d["banned_at"]),
            banned_by=d.get("banned_by", "system"),
        )


class Banlist:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: List[BanEntry] = self._load()

    def _load(self) -> List[BanEntry]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text())
        return [BanEntry.from_dict(r) for r in raw]

    def _save(self) -> None:
        self._path.write_text(json.dumps([e.to_dict() for e in self._entries], indent=2))

    def ban(self, job: str, reason: str, banned_by: str = "system") -> BanEntry:
        if not job:
            raise BanlistError("job name must not be empty")
        if not reason:
            raise BanlistError("reason must not be empty")
        existing = self.get(job)
        if existing is not None:
            return existing
        entry = BanEntry(job=job, reason=reason, banned_at=_utcnow(), banned_by=banned_by)
        self._entries.append(entry)
        self._save()
        return entry

    def unban(self, job: str) -> bool:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.job != job]
        if len(self._entries) < before:
            self._save()
            return True
        return False

    def is_banned(self, job: str) -> bool:
        return any(e.job == job for e in self._entries)

    def get(self, job: str) -> Optional[BanEntry]:
        for e in self._entries:
            if e.job == job:
                return e
        return None

    def all(self) -> List[BanEntry]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        self._save()
