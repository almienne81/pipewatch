"""Lockfile support to prevent overlapping pipeline runs."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


@dataclass
class LockFile:
    path: Path
    pid: int = field(default_factory=os.getpid)
    _acquired: bool = field(default=False, init=False, repr=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire(self, timeout: float = 0.0) -> None:
        """Acquire the lock, waiting up to *timeout* seconds.

        Raises LockError if the lock is held by another process after
        the timeout expires.
        """
        deadline = time.monotonic() + timeout
        while True:
            if not self.path.exists():
                self._write()
                self._acquired = True
                return
            existing = _read_pid(self.path)
            if existing is not None and not _pid_alive(existing):
                # Stale lock — remove and retry immediately.
                self.path.unlink(missing_ok=True)
                continue
            if time.monotonic() >= deadline:
                raise LockError(
                    f"Lock '{self.path}' is held by PID {existing}."
                )
            time.sleep(0.05)

    def release(self) -> None:
        """Release the lock if we own it."""
        if self._acquired:
            self.path.unlink(missing_ok=True)
            self._acquired = False

    @property
    def is_locked(self) -> bool:
        """Return True if the lock file currently exists on disk."""
        return self.path.exists()

    def owner_pid(self) -> Optional[int]:
        """Return the PID stored in the lock file, or None."""
        return _read_pid(self.path)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "LockFile":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(self.pid))


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _read_pid(path: Path) -> Optional[int]:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
