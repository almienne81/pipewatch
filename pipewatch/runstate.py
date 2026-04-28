"""Tracks the current running state of a pipeline job."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class RunStateError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class RunState:
    job: str
    pid: int
    started_at: datetime
    status: str = "running"  # running | done | failed
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "pid": self.pid,
            "started_at": self.started_at.isoformat(),
            "status": self.status,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunState":
        try:
            return cls(
                job=data["job"],
                pid=int(data["pid"]),
                started_at=datetime.fromisoformat(data["started_at"]),
                status=data.get("status", "running"),
                note=data.get("note", ""),
            )
        except KeyError as exc:
            raise RunStateError(f"Missing field in run state: {exc}") from exc


class RunStateStore:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def save(self, state: RunState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state.to_dict(), indent=2))

    def load(self) -> Optional[RunState]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text())
            return RunState.from_dict(data)
        except (json.JSONDecodeError, RunStateError):
            return None

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()

    def is_running(self) -> bool:
        state = self.load()
        if state is None or state.status != "running":
            return False
        try:
            os.kill(state.pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False


def create_state(job: str) -> RunState:
    return RunState(
        job=job,
        pid=os.getpid(),
        started_at=datetime.now(timezone.utc),
    )
