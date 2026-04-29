"""CLI commands for the pipeline snapshot feature."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.snapshot import Snapshot

_DEFAULT_PATH = Path(".pipewatch") / "snapshot.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_snapshot_show(args: argparse.Namespace) -> None:
    snap = Snapshot(_resolve_path(args))
    entries = snap.all()
    if not entries:
        print("No snapshots recorded.")
        return
    for e in sorted(entries, key=lambda x: x.job):
        tag_str = ", ".join(f"{k}={v}" for k, v in e.tags.items())
        tag_part = f"  [{tag_str}]" if tag_str else ""
        note_part = f"  {e.note}" if e.note else ""
        print(f"{e.job}  {e.status.upper()}  exit={e.exit_code}{note_part}{tag_part}")


def cmd_snapshot_get(args: argparse.Namespace) -> None:
    snap = Snapshot(_resolve_path(args))
    entry = snap.get(args.job)
    if entry is None:
        print(f"No snapshot found for job: {args.job}")
        return
    print(f"job       : {entry.job}")
    print(f"status    : {entry.status}")
    print(f"exit_code : {entry.exit_code}")
    print(f"note      : {entry.note}")
    print(f"tags      : {entry.tags}")


def cmd_snapshot_clear(args: argparse.Namespace) -> None:
    snap = Snapshot(_resolve_path(args))
    job = getattr(args, "job", None)
    snap.clear(job)
    if job:
        print(f"Cleared snapshot for job: {job}")
    else:
        print("All snapshots cleared.")


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("snapshot", help="Pipeline snapshot commands")
    p.add_argument("--file", help="Path to snapshot file")
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    sub.add_parser("show", help="Show all snapshots").set_defaults(func=cmd_snapshot_show)

    get_p = sub.add_parser("get", help="Get snapshot for a specific job")
    get_p.add_argument("job", help="Job name")
    get_p.set_defaults(func=cmd_snapshot_get)

    clear_p = sub.add_parser("clear", help="Clear snapshots")
    clear_p.add_argument("--job", help="Clear only this job", default=None)
    clear_p.set_defaults(func=cmd_snapshot_clear)
