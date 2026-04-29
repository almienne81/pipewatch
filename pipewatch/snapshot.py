"""Pipeline snapshot: capture and persist a point-in-time summary of pipeline state."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SnapshotEntry:
    job: str
    timestamp: float
    status: str  # "ok" | "fail" | "unknown"
    exit_code: Optional[int] = None
    note: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job": self.job,
            "timestamp": self.timestamp,
            "status": self.status,
            "exit_code": self.exit_code,
            "note": self.note,
            "tags": dict(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotEntry":
        return cls(
            job=data["job"],
            timestamp=float(data["timestamp"]),
            status=data["status"],
            exit_code=data.get("exit_code"),
            note=data.get("note", ""),
            tags=data.get("tags", {}),
        )


class Snapshot:
    """Persist the latest snapshot entry per job to a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: Dict[str, SnapshotEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            raw = json.loads(self._path.read_text())
            self._data = {k: SnapshotEntry.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({k: v.to_dict() for k, v in self._data.items()}, indent=2))

    def capture(self, job: str, status: str, exit_code: Optional[int] = None,
                note: str = "", tags: Optional[Dict[str, str]] = None) -> SnapshotEntry:
        entry = SnapshotEntry(
            job=job,
            timestamp=time.time(),
            status=status,
            exit_code=exit_code,
            note=note,
            tags=tags or {},
        )
        self._data[job] = entry
        self._save()
        return entry

    def get(self, job: str) -> Optional[SnapshotEntry]:
        return self._data.get(job)

    def all(self) -> List[SnapshotEntry]:
        return list(self._data.values())

    def clear(self, job: Optional[str] = None) -> None:
        if job is None:
            self._data.clear()
        else:
            self._data.pop(job, None)
        self._save()
