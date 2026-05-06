"""Scoreboard — tracks and ranks pipeline jobs by success rate and run count."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class ScoreboardError(Exception):
    """Raised when scoreboard operations fail."""


@dataclass
class ScoreEntry:
    job: str
    runs: int
    successes: int

    @property
    def failures(self) -> int:
        return self.runs - self.successes

    @property
    def success_rate(self) -> Optional[float]:
        if self.runs == 0:
            return None
        return self.successes / self.runs

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "runs": self.runs,
            "successes": self.successes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreEntry":
        return cls(
            job=data["job"],
            runs=int(data["runs"]),
            successes=int(data["successes"]),
        )


class Scoreboard:
    """Persistent scoreboard that accumulates per-job run outcomes."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._entries: dict[str, ScoreEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._entries = {
                item["job"]: ScoreEntry.from_dict(item) for item in raw
            }

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([e.to_dict() for e in self._entries.values()], indent=2)
        )

    def record(self, job: str, success: bool) -> ScoreEntry:
        if not job:
            raise ScoreboardError("job name must not be empty")
        entry = self._entries.get(job, ScoreEntry(job=job, runs=0, successes=0))
        entry = ScoreEntry(
            job=job,
            runs=entry.runs + 1,
            successes=entry.successes + (1 if success else 0),
        )
        self._entries[job] = entry
        self._save()
        return entry

    def get(self, job: str) -> Optional[ScoreEntry]:
        return self._entries.get(job)

    def all(self) -> List[ScoreEntry]:
        return list(self._entries.values())

    def ranked(self, by: str = "success_rate") -> List[ScoreEntry]:
        """Return entries sorted descending by 'success_rate' or 'runs'."""
        if by not in ("success_rate", "runs"):
            raise ScoreboardError(f"unknown ranking key: {by!r}")
        return sorted(
            self._entries.values(),
            key=lambda e: (getattr(e, by) or 0.0),
            reverse=True,
        )

    def clear(self) -> None:
        self._entries = {}
        self._save()
