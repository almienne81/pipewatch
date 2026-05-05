"""Quota tracking: enforce per-job run count limits within a rolling window."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


class QuotaError(Exception):
    """Raised when quota configuration or state is invalid."""


@dataclass
class QuotaPolicy:
    max_runs: int
    window_seconds: int

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise QuotaError("max_runs must be >= 1")
        if self.window_seconds < 1:
            raise QuotaError("window_seconds must be >= 1")

    def to_dict(self) -> dict:
        return {"max_runs": self.max_runs, "window_seconds": self.window_seconds}

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaPolicy":
        return cls(
            max_runs=int(data["max_runs"]),
            window_seconds=int(data["window_seconds"]),
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QuotaState:
    job: str
    timestamps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"job": self.job, "timestamps": list(self.timestamps)}

    @classmethod
    def from_dict(cls, data: dict) -> "QuotaState":
        return cls(job=data["job"], timestamps=list(data.get("timestamps", [])))


class Quota:
    """Persisted per-job run quota enforcer."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: dict = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2))

    def _prune(self, job: str, window_seconds: int) -> List[str]:
        now = _utcnow().timestamp()
        cutoff = now - window_seconds
        kept = [
            ts for ts in self._data.get(job, {}).get("timestamps", [])
            if datetime.fromisoformat(ts).timestamp() >= cutoff
        ]
        return kept

    def is_exceeded(self, job: str, policy: QuotaPolicy) -> bool:
        """Return True if the job has reached its run quota."""
        recent = self._prune(job, policy.window_seconds)
        return len(recent) >= policy.max_runs

    def record(self, job: str, policy: QuotaPolicy) -> None:
        """Record a run for *job*, pruning stale timestamps first."""
        recent = self._prune(job, policy.window_seconds)
        recent.append(_utcnow().isoformat())
        self._data[job] = QuotaState(job=job, timestamps=recent).to_dict()
        self._save()

    def remaining(self, job: str, policy: QuotaPolicy) -> int:
        """Return how many runs are still allowed within the current window."""
        recent = self._prune(job, policy.window_seconds)
        return max(0, policy.max_runs - len(recent))

    def reset(self, job: str) -> None:
        """Clear quota state for *job*."""
        self._data.pop(job, None)
        self._save()
