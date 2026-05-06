"""CLI commands for the replay buffer."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.replaybuffer import ReplayBuffer

_DEFAULT = Path(".pipewatch") / "replay.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT)


def cmd_replay_list(args: argparse.Namespace) -> None:
    buf = ReplayBuffer(_resolve_path(args))
    entries = buf.for_job(args.job) if getattr(args, "job", None) else buf.all()
    if not entries:
        print("No entries.")
        return
    for e in entries:
        status = "✓" if e.outcome == "success" else "✗"
        print(f"{status} [{e.timestamp}] {e.job}  exit={e.exit_code}  {e.note}".rstrip())


def cmd_replay_latest(args: argparse.Namespace) -> None:
    buf = ReplayBuffer(_resolve_path(args))
    entry = buf.latest(args.job)
    if entry is None:
        print(f"No entries for job '{args.job}'.")
        return
    print(f"outcome : {entry.outcome}")
    print(f"exit    : {entry.exit_code}")
    print(f"time    : {entry.timestamp}")
    if entry.note:
        print(f"note    : {entry.note}")


def cmd_replay_clear(args: argparse.Namespace) -> None:
    buf = ReplayBuffer(_resolve_path(args))
    buf.clear()
    print("Replay buffer cleared.")


def build_replay_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("replay", help="Manage the replay buffer")
    p.add_argument("--file", metavar="PATH", help="Buffer file (default: .pipewatch/replay.json)")
    p.add_argument("--capacity", type=int, default=50, help="Max entries to keep")
    s = p.add_subparsers(dest="replay_cmd", required=True)

    ls = s.add_parser("list", help="List buffered entries")
    ls.add_argument("--job", metavar="NAME", help="Filter by job name")
    ls.set_defaults(func=cmd_replay_list)

    lat = s.add_parser("latest", help="Show latest entry for a job")
    lat.add_argument("job", metavar="JOB")
    lat.set_defaults(func=cmd_replay_latest)

    cl = s.add_parser("clear", help="Clear all entries")
    cl.set_defaults(func=cmd_replay_clear)

    return p
