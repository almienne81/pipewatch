"""Staleness detection — flags jobs that have not run within an expected interval."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class StalenessError(Exception):
    """Raised for invalid staleness configuration or state."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StalenessPolicy:
    """Configuration for staleness detection."""

    max_age_seconds: float
    warn_age_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.max_age_seconds <= 0:
            raise StalenessError("max_age_seconds must be positive")
        if self.warn_age_seconds is not None:
            if self.warn_age_seconds <= 0:
                raise StalenessError("warn_age_seconds must be positive")
            if self.warn_age_seconds >= self.max_age_seconds:
                raise StalenessError("warn_age_seconds must be less than max_age_seconds")

    def to_dict(self) -> dict:
        return {"max_age_seconds": self.max_age_seconds, "warn_age_seconds": self.warn_age_seconds}

    @classmethod
    def from_dict(cls, data: dict) -> "StalenessPolicy":
        return cls(
            max_age_seconds=float(data["max_age_seconds"]),
            warn_age_seconds=float(data["warn_age_seconds"]) if data.get("warn_age_seconds") is not None else None,
        )


@dataclass
class StalenessEntry:
    job: str
    last_seen: datetime

    def to_dict(self) -> dict:
        return {"job": self.job, "last_seen": self.last_seen.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> "StalenessEntry":
        return cls(job=data["job"], last_seen=datetime.fromisoformat(data["last_seen"]))


@dataclass
class StalenessTracker:
    path: Path
    _entries: dict = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._entries = {k: StalenessEntry.from_dict(v) for k, v in raw.items()}
        else:
            self._entries = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2))

    def ping(self, job: str) -> StalenessEntry:
        if not job:
            raise StalenessError("job name must not be empty")
        entry = StalenessEntry(job=job, last_seen=_utcnow())
        self._entries[job] = entry
        self._save()
        return entry

    def check(self, job: str, policy: StalenessPolicy) -> str:
        """Return 'ok', 'warn', or 'stale'."""
        entry = self._entries.get(job)
        if entry is None:
            return "stale"
        age = (_utcnow() - entry.last_seen).total_seconds()
        if age >= policy.max_age_seconds:
            return "stale"
        if policy.warn_age_seconds is not None and age >= policy.warn_age_seconds:
            return "warn"
        return "ok"

    def get(self, job: str) -> Optional[StalenessEntry]:
        return self._entries.get(job)

    def all_entries(self) -> List[StalenessEntry]:
        return list(self._entries.values())

    def clear(self, job: str) -> None:
        self._entries.pop(job, None)
        self._save()
