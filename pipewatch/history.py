"""Persistent run history storage for pipewatch."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path.home() / ".pipewatch" / "history.json"


@dataclass
class HistoryEntry:
    command: str
    exit_code: int
    duration_seconds: float
    timestamp: str
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(**data)


class History:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_HISTORY_PATH

    def _load(self) -> List[dict]:
        if not self.path.exists():
            return []
        with self.path.open() as fh:
            return json.load(fh)

    def _save(self, entries: List[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as fh:
            json.dump(entries, fh, indent=2)

    def append(self, entry: HistoryEntry) -> None:
        entries = self._load()
        entries.append(entry.to_dict())
        self._save(entries)

    def all(self) -> List[HistoryEntry]:
        return [HistoryEntry.from_dict(d) for d in self._load()]

    def last(self, n: int = 10) -> List[HistoryEntry]:
        return self.all()[-n:]

    def clear(self) -> None:
        self._save([])


def record_run(
    command: str,
    exit_code: int,
    duration_seconds: float,
    stdout_tail: str = "",
    stderr_tail: str = "",
    history_path: Optional[Path] = None,
) -> HistoryEntry:
    entry = HistoryEntry(
        command=command,
        exit_code=exit_code,
        duration_seconds=round(duration_seconds, 3),
        timestamp=datetime.utcnow().isoformat(),
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
    )
    History(history_path).append(entry)
    return entry
