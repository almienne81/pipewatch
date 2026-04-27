"""Structured per-run log capture for pipeline jobs."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class RunLogEntry:
    run_id: str
    command: str
    started_at: float
    finished_at: Optional[float]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    tags: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "command": self.command,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunLogEntry":
        return cls(
            run_id=data["run_id"],
            command=data["command"],
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            exit_code=data.get("exit_code"),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            tags=data.get("tags", {}),
        )

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return self.finished_at - self.started_at


class RunLog:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def _load(self) -> List[dict]:
        if not self._path.exists():
            return []
        with self._path.open() as fh:
            return json.load(fh)

    def _save(self, entries: List[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(entries, fh, indent=2)

    def append(self, entry: RunLogEntry) -> None:
        data = self._load()
        data.append(entry.to_dict())
        self._save(data)

    def all(self) -> List[RunLogEntry]:
        return [RunLogEntry.from_dict(d) for d in self._load()]

    def get(self, run_id: str) -> Optional[RunLogEntry]:
        for entry in self.all():
            if entry.run_id == run_id:
                return entry
        return None

    def clear(self) -> None:
        self._save([])

    def last(self) -> Optional[RunLogEntry]:
        entries = self.all()
        return entries[-1] if entries else None
