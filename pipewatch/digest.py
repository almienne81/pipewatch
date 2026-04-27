"""Periodic digest summarisation for pipeline run history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.history import History, HistoryEntry


@dataclass
class DigestEntry:
    pipeline: str
    total_runs: int
    successes: int
    failures: int
    success_rate: Optional[float]  # 0.0–1.0 or None when no runs
    last_run_at: Optional[str]
    last_status: Optional[str]

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "total_runs": self.total_runs,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": self.success_rate,
            "last_run_at": self.last_run_at,
            "last_status": self.last_status,
        }


@dataclass
class Digest:
    generated_at: str
    window_hours: int
    entries: List[DigestEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "window_hours": self.window_hours,
            "entries": [e.to_dict() for e in self.entries],
        }


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def build_digest(history: History, pipeline: str, window_hours: int = 24) -> Digest:
    """Summarise *history* for *pipeline* over the last *window_hours* hours."""
    now = _utcnow()
    cutoff_ts = now.timestamp() - window_hours * 3600

    entries: List[HistoryEntry] = [
        e for e in history.all() if e.timestamp >= cutoff_ts
    ]

    successes = sum(1 for e in entries if e.exit_code == 0)
    failures = len(entries) - successes
    rate = successes / len(entries) if entries else None

    last: Optional[HistoryEntry] = entries[-1] if entries else None
    last_run_at = (
        datetime.fromtimestamp(last.timestamp, tz=timezone.utc).isoformat()
        if last
        else None
    )
    last_status = ("success" if last.exit_code == 0 else "failure") if last else None

    digest_entry = DigestEntry(
        pipeline=pipeline,
        total_runs=len(entries),
        successes=successes,
        failures=failures,
        success_rate=rate,
        last_run_at=last_run_at,
        last_status=last_status,
    )

    return Digest(
        generated_at=now.isoformat(),
        window_hours=window_hours,
        entries=[digest_entry],
    )


def format_digest(digest: Digest) -> str:
    """Return a human-readable text summary of *digest*."""
    lines = [
        f"Pipeline Digest  (last {digest.window_hours}h)",
        f"Generated: {digest.generated_at}",
        "-" * 44,
    ]
    for e in digest.entries:
        rate_str = f"{e.success_rate * 100:.1f}%" if e.success_rate is not None else "n/a"
        lines.append(f"Pipeline : {e.pipeline}")
        lines.append(f"  Runs   : {e.total_runs}  (✓ {e.successes}  ✗ {e.failures})")
        lines.append(f"  Rate   : {rate_str}")
        lines.append(f"  Last   : {e.last_run_at or 'never'}  [{e.last_status or '-'}]")
    return "\n".join(lines)
