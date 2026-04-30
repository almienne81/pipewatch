"""CLI commands for step-level log inspection."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.steplog import StepLog


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file)


def cmd_steplog_list(args: argparse.Namespace) -> None:
    log = StepLog(_resolve_path(args))
    entries = log.for_job(args.job) if args.job else log.all()
    if not entries:
        print("No step entries found.")
        return
    for e in entries:
        symbol = "✓" if e.succeeded() else ("–" if e.status == "skip" else "✗")
        dur = f"{e.duration_seconds():.2f}s"
        note = f"  {e.note}" if e.note else ""
        print(f"[{symbol}] {e.job}/{e.step}  {e.status}  {dur}{note}")


def cmd_steplog_latest(args: argparse.Namespace) -> None:
    log = StepLog(_resolve_path(args))
    entry = log.latest(args.job, args.step)
    if entry is None:
        print(f"No entry found for job={args.job!r} step={args.step!r}")
        return
    symbol = "✓" if entry.succeeded() else "✗"
    print(f"[{symbol}] {entry.job}/{entry.step}")
    print(f"  status   : {entry.status}")
    print(f"  started  : {entry.started_at.isoformat()}")
    print(f"  ended    : {entry.ended_at.isoformat()}")
    print(f"  duration : {entry.duration_seconds():.2f}s")
    if entry.note:
        print(f"  note     : {entry.note}")
    if entry.meta:
        print(f"  meta     : {entry.meta}")


def cmd_steplog_clear(args: argparse.Namespace) -> None:
    log = StepLog(_resolve_path(args))
    log.clear()
    print("Step log cleared.")


def build_steplog_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("steplog", help="Inspect step-level run log")
    p.add_argument("--file", default=".pipewatch_steplog.json", help="Path to step log file")
    sub = p.add_subparsers(dest="steplog_cmd")

    ls = sub.add_parser("list", help="List step entries")
    ls.add_argument("--job", default=None, help="Filter by job name")
    ls.set_defaults(func=cmd_steplog_list)

    lat = sub.add_parser("latest", help="Show latest entry for a step")
    lat.add_argument("job", help="Job name")
    lat.add_argument("step", help="Step name")
    lat.set_defaults(func=cmd_steplog_latest)

    clr = sub.add_parser("clear", help="Clear all step entries")
    clr.set_defaults(func=cmd_steplog_clear)
