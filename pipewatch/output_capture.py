"""Capture stdout/stderr from subprocesses and store structured output."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class CapturedOutput:
    command: str
    stdout: str
    stderr: str
    returncode: int
    started_at: datetime
    finished_at: datetime
    truncated: bool = False

    def succeeded(self) -> bool:
        return self.returncode == 0

    def combined(self) -> str:
        parts = []
        if self.stdout.strip():
            parts.append(self.stdout)
        if self.stderr.strip():
            parts.append(self.stderr)
        return "\n".join(parts)

    def tail(self, lines: int = 20) -> str:
        """Return the last *lines* lines of combined output."""
        all_lines = self.combined().splitlines()
        return "\n".join(all_lines[-lines:])

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "truncated": self.truncated,
        }


MAX_OUTPUT_BYTES = 256 * 1024  # 256 KB per stream


def capture(
    command: List[str],
    *,
    timeout: Optional[float] = None,
    max_bytes: int = MAX_OUTPUT_BYTES,
    env: Optional[dict] = None,
    cwd: Optional[str] = None,
) -> CapturedOutput:
    """Run *command* and return a :class:`CapturedOutput` with results."""
    started_at = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout,
            env=env,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as exc:
        finished_at = datetime.now(timezone.utc)
        raw_out = (exc.stdout or b"").decode("utf-8", errors="replace")
        raw_err = (exc.stderr or b"").decode("utf-8", errors="replace")
        return CapturedOutput(
            command=" ".join(command),
            stdout=raw_out[:max_bytes],
            stderr=raw_err[:max_bytes],
            returncode=-1,
            started_at=started_at,
            finished_at=finished_at,
            truncated=False,
        )

    finished_at = datetime.now(timezone.utc)
    raw_out = result.stdout.decode("utf-8", errors="replace")
    raw_err = result.stderr.decode("utf-8", errors="replace")
    truncated = len(result.stdout) > max_bytes or len(result.stderr) > max_bytes
    return CapturedOutput(
        command=" ".join(command),
        stdout=raw_out[:max_bytes],
        stderr=raw_err[:max_bytes],
        returncode=result.returncode,
        started_at=started_at,
        finished_at=finished_at,
        truncated=truncated,
    )
