"""Timeout enforcement for pipeline commands."""

from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Optional


class TimeoutError(Exception):  # noqa: A001
    """Raised when a pipeline command exceeds its allowed duration."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        super().__init__(f"Command timed out after {seconds:.1f}s")


@dataclass
class TimeoutPolicy:
    """Describes how long a command is allowed to run."""

    seconds: Optional[float] = None
    kill_on_timeout: bool = True

    def is_enabled(self) -> bool:
        return self.seconds is not None and self.seconds > 0

    def to_dict(self) -> dict:
        return {
            "seconds": self.seconds,
            "kill_on_timeout": self.kill_on_timeout,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeoutPolicy":
        return cls(
            seconds=data.get("seconds"),
            kill_on_timeout=data.get("kill_on_timeout", True),
        )


class _TimeoutContext:
    """Context manager that raises TimeoutError after *seconds*."""

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def _handler(self, signum: int, frame: object) -> None:  # noqa: ARG002
        raise TimeoutError(self._seconds)

    def __enter__(self) -> "_TimeoutContext":
        signal.signal(signal.SIGALRM, self._handler)
        signal.alarm(int(self._seconds) or 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        signal.alarm(0)
        return False


def enforce(policy: TimeoutPolicy, fn, *args, **kwargs):
    """Call *fn* with *args*/*kwargs*, enforcing *policy* timeout.

    Returns the function's return value.  Raises ``TimeoutError`` if the
    deadline is exceeded.
    """
    if not policy.is_enabled():
        return fn(*args, **kwargs)

    with _TimeoutContext(policy.seconds):
        return fn(*args, **kwargs)
