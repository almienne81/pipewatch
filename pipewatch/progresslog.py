"""Progress logging for long-running pipeline steps."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ProgressEntry:
    job: str
    step: str
    pct: float          # 0.0 – 100.0
    message: str
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "step": self.step,
            "pct": round(self.pct, 2),
            "message": self.message,
            "ts": self.ts,
        }

    @staticmethod
    def from_dict(d: dict) -> "ProgressEntry":
        return ProgressEntry(
            job=d["job"],
            step=d["step"],
            pct=float(d["pct"]),
            message=d["message"],
            ts=float(d["ts"]),
        )


class ProgressLog:
    """Append-only progress log backed by a JSONL file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("")

    def record(self, job: str, step: str, pct: float, message: str = "") -> ProgressEntry:
        if not (0.0 <= pct <= 100.0):
            raise ValueError(f"pct must be 0–100, got {pct}")
        entry = ProgressEntry(job=job, step=step, pct=pct, message=message)
        with self._path.open("a") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def entries(self, job: Optional[str] = None) -> List[ProgressEntry]:
        results = []
        for line in self._path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            e = ProgressEntry.from_dict(json.loads(line))
            if job is None or e.job == job:
                results.append(e)
        return results

    def latest(self, job: str) -> Optional[ProgressEntry]:
        hits = self.entries(job=job)
        return hits[-1] if hits else None

    def clear(self) -> None:
        self._path.write_text("")
