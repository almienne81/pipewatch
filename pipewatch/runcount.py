"""Track cumulative run counts per job across sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


class RunCountError(Exception):
    """Raised when RunCount operations fail."""


@dataclass
class RunCountEntry:
    job: str
    total: int
    successes: int
    failures: int

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "total": self.total,
            "successes": self.successes,
            "failures": self.failures,
        }

    @staticmethod
    def from_dict(d: dict) -> "RunCountEntry":
        return RunCountEntry(
            job=d["job"],
            total=d["total"],
            successes=d["successes"],
            failures=d["failures"],
        )

    @property
    def success_rate(self) -> Optional[float]:
        if self.total == 0:
            return None
        return self.successes / self.total


class RunCount:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: Dict[str, RunCountEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {
                k: RunCountEntry.from_dict(v) for k, v in raw.items()
            }

    def _save(self) -> None:
        self._path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2)
        )

    def get(self, job: str) -> Optional[RunCountEntry]:
        return self._data.get(job)

    def record(self, job: str, *, success: bool) -> RunCountEntry:
        if not job:
            raise RunCountError("job name must not be empty")
        entry = self._data.get(
            job, RunCountEntry(job=job, total=0, successes=0, failures=0)
        )
        entry = RunCountEntry(
            job=job,
            total=entry.total + 1,
            successes=entry.successes + (1 if success else 0),
            failures=entry.failures + (0 if success else 1),
        )
        self._data[job] = entry
        self._save()
        return entry

    def reset(self, job: str) -> None:
        self._data.pop(job, None)
        self._save()

    def all(self) -> List[RunCountEntry]:
        return list(self._data.values())
