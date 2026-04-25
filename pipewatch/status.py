"""Pipeline status aggregation — combines recent history, metrics, and tags into a single status snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pipewatch.history import History
from pipewatch.tags import Tags


@dataclass
class PipelineStatus:
    """Aggregated status snapshot for a named pipeline."""

    name: str
    last_run_at: Optional[datetime] = None
    last_exit_code: Optional[int] = None
    last_duration_seconds: Optional[float] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    tags: dict = field(default_factory=dict)

    @property
    def success_rate(self) -> Optional[float]:
        """Return success rate as a value between 0.0 and 1.0, or None if no runs."""
        if self.total_runs == 0:
            return None
        return self.successful_runs / self.total_runs

    @property
    def is_healthy(self) -> bool:
        """Return True when the last run succeeded."""
        return self.last_exit_code == 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_exit_code": self.last_exit_code,
            "last_duration_seconds": self.last_duration_seconds,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": self.success_rate,
            "is_healthy": self.is_healthy,
            "tags": self.tags,
        }


def collect_status(name: str, history: History, tags: Optional[Tags] = None) -> PipelineStatus:
    """Build a PipelineStatus from a History instance and optional Tags."""
    entries = history.all()

    total = len(entries)
    successful = sum(1 for e in entries if e.exit_code == 0)
    failed = total - successful

    last_run_at = None
    last_exit_code = None
    last_duration = None

    if entries:
        latest = entries[-1]
        last_run_at = latest.started_at
        last_exit_code = latest.exit_code
        last_duration = latest.duration_seconds

    tag_dict = dict(tags) if tags is not None else {}

    return PipelineStatus(
        name=name,
        last_run_at=last_run_at,
        last_exit_code=last_exit_code,
        last_duration_seconds=last_duration,
        total_runs=total,
        successful_runs=successful,
        failed_runs=failed,
        tags=tag_dict,
    )
