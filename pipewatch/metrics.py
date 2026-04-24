"""Runtime metrics collection for monitored pipeline jobs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Metrics:
    """Captured runtime metrics for a single pipeline run."""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    exit_code: Optional[int] = None
    stdout_lines: int = 0
    stderr_lines: int = 0

    def stop(self) -> None:
        """Record the end time of the run."""
        self.end_time = time.time()

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Return elapsed wall-clock seconds, or None if not yet stopped."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def elapsed_human(self) -> str:
        """Return a human-readable elapsed time string."""
        secs = self.elapsed_seconds
        if secs is None:
            return "running"
        if secs < 60:
            return f"{secs:.1f}s"
        minutes, seconds = divmod(int(secs), 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def to_dict(self) -> dict:
        """Serialize metrics to a plain dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": self.elapsed_seconds,
            "peak_memory_mb": self.peak_memory_mb,
            "exit_code": self.exit_code,
            "stdout_lines": self.stdout_lines,
            "stderr_lines": self.stderr_lines,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Metrics":
        """Deserialize metrics from a plain dictionary."""
        m = cls(start_time=data.get("start_time", 0.0))
        m.end_time = data.get("end_time")
        m.peak_memory_mb = data.get("peak_memory_mb")
        m.exit_code = data.get("exit_code")
        m.stdout_lines = data.get("stdout_lines", 0)
        m.stderr_lines = data.get("stderr_lines", 0)
        return m


def collect(exit_code: int, stdout: str, stderr: str, start: float) -> Metrics:
    """Build a completed Metrics object from run outputs."""
    m = Metrics(start_time=start)
    m.stop()
    m.exit_code = exit_code
    m.stdout_lines = stdout.count("\n") + (1 if stdout and not stdout.endswith("\n") else 0)
    m.stderr_lines = stderr.count("\n") + (1 if stderr and not stderr.endswith("\n") else 0)
    return m
