"""Step-level logging for pipeline jobs.

Tracks individual named steps within a pipeline run, recording
start/end times, status, and optional metadata.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StepEntry:
    job: str
    step: str
    status: str  # "ok" | "fail" | "skip"
    started_at: datetime
    ended_at: datetime
    note: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def duration_seconds(self) -> float:
        return (self.ended_at - self.started_at).total_seconds()

    def succeeded(self) -> bool:
        return self.status == "ok"


def to_dict(entry: StepEntry) -> Dict[str, Any]:
    return {
        "job": entry.job,
        "step": entry.step,
        "status": entry.status,
        "started_at": entry.started_at.isoformat(),
        "ended_at": entry.ended_at.isoformat(),
        "note": entry.note,
        "meta": entry.meta,
    }


def from_dict(data: Dict[str, Any]) -> StepEntry:
    return StepEntry(
        job=data["job"],
        step=data["step"],
        status=data["status"],
        started_at=datetime.fromisoformat(data["started_at"]),
        ended_at=datetime.fromisoformat(data["ended_at"]),
        note=data.get("note", ""),
        meta=data.get("meta", {}),
    )


class StepLog:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _load(self) -> List[Dict[str, Any]]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text())

    def _save(self, rows: List[Dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(rows, indent=2))

    def record(
        self,
        job: str,
        step: str,
        status: str,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        note: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> StepEntry:
        now = _utcnow()
        entry = StepEntry(
            job=job,
            step=step,
            status=status,
            started_at=started_at or now,
            ended_at=ended_at or now,
            note=note,
            meta=meta or {},
        )
        rows = self._load()
        rows.append(to_dict(entry))
        self._save(rows)
        return entry

    def all(self) -> List[StepEntry]:
        return [from_dict(r) for r in self._load()]

    def for_job(self, job: str) -> List[StepEntry]:
        return [e for e in self.all() if e.job == job]

    def latest(self, job: str, step: str) -> Optional[StepEntry]:
        matches = [e for e in self.all() if e.job == job and e.step == step]
        return matches[-1] if matches else None

    def clear(self) -> None:
        self._save([])
