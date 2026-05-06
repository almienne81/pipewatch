"""Watermark tracking — record and compare high-water-mark values for pipeline metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class WatermarkError(Exception):
    """Raised when watermark operations fail."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WatermarkEntry:
    job: str
    key: str
    value: float
    recorded_at: datetime

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "key": self.key,
            "value": self.value,
            "recorded_at": self.recorded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatermarkEntry":
        return cls(
            job=data["job"],
            key=data["key"],
            value=float(data["value"]),
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
        )


class Watermark:
    """Persist and query high-water-mark values per (job, key) pair."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, WatermarkEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {
                k: WatermarkEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2)
        )

    def _key(self, job: str, key: str) -> str:
        if not job:
            raise WatermarkError("job must not be empty")
        if not key:
            raise WatermarkError("key must not be empty")
        return f"{job}:{key}"

    def update(self, job: str, key: str, value: float) -> WatermarkEntry:
        """Record value only if it exceeds the current watermark."""
        composite = self._key(job, key)
        existing = self._data.get(composite)
        if existing is None or value > existing.value:
            entry = WatermarkEntry(job=job, key=key, value=value, recorded_at=_utcnow())
            self._data[composite] = entry
            self._save()
            return entry
        return existing

    def get(self, job: str, key: str) -> Optional[WatermarkEntry]:
        return self._data.get(self._key(job, key))

    def all(self) -> list[WatermarkEntry]:
        return list(self._data.values())

    def clear(self, job: str, key: str) -> None:
        composite = self._key(job, key)
        if composite in self._data:
            del self._data[composite]
            self._save()

    def clear_all(self) -> None:
        self._data.clear()
        self._save()
