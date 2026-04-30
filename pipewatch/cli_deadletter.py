"""CLI commands for inspecting and managing the dead-letter queue."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.deadletter import DeadLetterQueue

_DEFAULT_PATH = Path(".pipewatch") / "deadletter.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_deadletter_list(args: argparse.Namespace) -> None:
    dlq = DeadLetterQueue(_resolve_path(args))
    job = getattr(args, "job", None)
    entries = dlq.for_job(job) if job else dlq.all()
    if not entries:
        print("No dead-letter entries.")
        return
    for e in entries:
        print(f"[{e.timestamp.isoformat()}] job={e.job} attempts={e.attempts} reason={e.reason}")


def cmd_deadletter_clear(args: argparse.Namespace) -> None:
    dlq = DeadLetterQueue(_resolve_path(args))
    job = getattr(args, "job", None)
    removed = dlq.clear(job=job)
    target = f"job '{job}'" if job else "all jobs"
    print(f"Cleared {removed} dead-letter entries for {target}.")


def cmd_deadletter_count(args: argparse.Namespace) -> None:
    dlq = DeadLetterQueue(_resolve_path(args))
    job = getattr(args, "job", None)
    entries = dlq.for_job(job) if job else dlq.all()
    label = f" for job '{job}'" if job else ""
    print(f"{len(entries)} dead-letter entries{label}.")


def build_deadletter_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("deadletter", help="Manage the dead-letter queue")
    p.add_argument("--file", help="Path to dead-letter JSON file")
    cmds = p.add_subparsers(dest="dl_cmd", required=True)

    ls = cmds.add_parser("list", help="List dead-letter entries")
    ls.add_argument("--job", help="Filter by job name")
    ls.set_defaults(func=cmd_deadletter_list)

    cl = cmds.add_parser("clear", help="Clear dead-letter entries")
    cl.add_argument("--job", help="Clear only entries for this job")
    cl.set_defaults(func=cmd_deadletter_clear)

    ct = cmds.add_parser("count", help="Count dead-letter entries")
    ct.add_argument("--job", help="Count only entries for this job")
    ct.set_defaults(func=cmd_deadletter_count)

    return p
