"""Tests for pipewatch.lockfile."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from pipewatch.lockfile import LockError, LockFile, _pid_alive, _read_pid


@pytest.fixture()
def lock_path(tmp_path: Path) -> Path:
    return tmp_path / "test.lock"


# ---------------------------------------------------------------------------
# Basic acquire / release
# ---------------------------------------------------------------------------

def test_acquire_creates_file(lock_path: Path) -> None:
    lock = LockFile(path=lock_path)
    lock.acquire()
    assert lock_path.exists()
    lock.release()


def test_release_removes_file(lock_path: Path) -> None:
    lock = LockFile(path=lock_path)
    lock.acquire()
    lock.release()
    assert not lock_path.exists()


def test_lock_file_contains_pid(lock_path: Path) -> None:
    lock = LockFile(path=lock_path)
    lock.acquire()
    assert _read_pid(lock_path) == os.getpid()
    lock.release()


def test_context_manager_releases_on_exit(lock_path: Path) -> None:
    with LockFile(path=lock_path):
        assert lock_path.exists()
    assert not lock_path.exists()


# ---------------------------------------------------------------------------
# Stale lock handling
# ---------------------------------------------------------------------------

def test_stale_lock_is_overridden(lock_path: Path) -> None:
    # Write a PID that definitely does not exist.
    lock_path.write_text("999999999")
    lock = LockFile(path=lock_path)
    lock.acquire()  # Should succeed by clearing stale lock.
    assert _read_pid(lock_path) == os.getpid()
    lock.release()


# ---------------------------------------------------------------------------
# Contention / timeout
# ---------------------------------------------------------------------------

def test_acquire_raises_when_locked_by_active_pid(lock_path: Path) -> None:
    # Simulate a live owner by using our own PID (we are alive).
    lock_path.write_text(str(os.getpid()))
    # A second LockFile instance with the same path should fail immediately.
    other = LockFile(path=lock_path, pid=os.getpid() + 1)
    with pytest.raises(LockError, match="Lock"):
        other.acquire(timeout=0.0)
    lock_path.unlink(missing_ok=True)


def test_is_locked_reflects_state(lock_path: Path) -> None:
    lock = LockFile(path=lock_path)
    assert not lock.is_locked
    lock.acquire()
    assert lock.is_locked
    lock.release()
    assert not lock.is_locked


def test_owner_pid_returns_none_when_no_file(lock_path: Path) -> None:
    lock = LockFile(path=lock_path)
    assert lock.owner_pid() is None


# ---------------------------------------------------------------------------
# _pid_alive helper
# ---------------------------------------------------------------------------

def test_pid_alive_current_process() -> None:
    assert _pid_alive(os.getpid()) is True


def test_pid_alive_nonexistent_pid() -> None:
    assert _pid_alive(999999999) is False
