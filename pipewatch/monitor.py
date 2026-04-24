"""Process monitor for long-running pipeline jobs."""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pipewatch.config import Config
from pipewatch.notifier import notify


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime
    finished_at: datetime

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def summary(self) -> str:
        status = "SUCCESS" if self.succeeded else f"FAILED (exit {self.returncode})"
        return (
            f"[pipewatch] {status} — `{self.command}`\n"
            f"Duration: {self.duration_seconds:.1f}s | "
            f"Started: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )


def run_and_monitor(
    command: str,
    config: Config,
    timeout: Optional[float] = None,
    notify_on_success: bool = False,
) -> RunResult:
    """Run *command* in a shell, stream output, and alert via configured channels.

    Args:
        command: Shell command string to execute.
        config: Loaded pipewatch Config.
        timeout: Optional timeout in seconds; raises subprocess.TimeoutExpired.
        notify_on_success: If True, send a notification even on success.

    Returns:
        A RunResult describing the completed process.
    """
    started_at = datetime.utcnow()
    start_time = time.monotonic()

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    with subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as proc:
        try:
            raw_stdout, raw_stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raw_stdout, raw_stderr = proc.communicate()
            raise

        stdout_lines = raw_stdout.splitlines()
        stderr_lines = raw_stderr.splitlines()

    duration = time.monotonic() - start_time
    finished_at = datetime.utcnow()

    result = RunResult(
        command=command,
        returncode=proc.returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
        duration_seconds=duration,
        started_at=started_at,
        finished_at=finished_at,
    )

    if not result.succeeded or notify_on_success:
        notify(result.summary(), config)

    return result
