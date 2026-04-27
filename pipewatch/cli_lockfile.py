"""CLI sub-commands for inspecting pipeline lock files."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.lockfile import LockFile, _pid_alive


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.lock_file)


def cmd_lock_status(args: argparse.Namespace) -> None:
    lock = LockFile(path=_resolve_path(args))
    if not lock.is_locked:
        print("No lock file found — pipeline is not running.")
        return
    pid = lock.owner_pid()
    if pid is None:
        print("Lock file exists but could not be read.")
        return
    alive = _pid_alive(pid)
    status = "running" if alive else "stale (process no longer alive)"
    print(f"Lock held by PID {pid} — {status}")
    print(f"Lock file: {lock.path}")


def cmd_lock_clear(args: argparse.Namespace) -> None:
    lock = LockFile(path=_resolve_path(args))
    if not lock.is_locked:
        print("No lock file to clear.")
        return
    lock.path.unlink(missing_ok=True)
    print(f"Lock file removed: {lock.path}")


def build_lockfile_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parent = subparsers.add_parser("lock", help="Manage pipeline lock files.")
    parent.add_argument(
        "--lock-file",
        default=".pipewatch.lock",
        metavar="PATH",
        help="Path to the lock file (default: .pipewatch.lock).",
    )

    sub = parent.add_subparsers(dest="lock_cmd", required=True)

    status_p = sub.add_parser("status", help="Show current lock status.")
    status_p.set_defaults(func=cmd_lock_status)

    clear_p = sub.add_parser("clear", help="Force-remove a stale lock file.")
    clear_p.set_defaults(func=cmd_lock_clear)
