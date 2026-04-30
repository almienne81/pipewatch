"""CLI commands for inspecting the structured event log."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.eventlog import EventLog

_DEFAULT_PATH = Path(".pipewatch") / "events.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_eventlog_list(args: argparse.Namespace) -> None:
    log = EventLog(_resolve_path(args))
    entries = log.for_job(args.job) if args.job else log.all()
    if args.level:
        entries = [e for e in entries if e.level == args.level]
    if not entries:
        print("No events found.")
        return
    for e in entries:
        ts = e.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        meta_str = " " + str(e.meta) if e.meta else ""
        print(f"[{ts}] [{e.level.upper():7}] {e.job} / {e.event}  {e.message}{meta_str}")


def cmd_eventlog_record(args: argparse.Namespace) -> None:
    log = EventLog(_resolve_path(args))
    entry = log.record(
        job=args.job,
        event=args.event,
        level=args.level,
        message=args.message or "",
    )
    print(f"Recorded: [{entry.level}] {entry.job}/{entry.event}")


def cmd_eventlog_clear(args: argparse.Namespace) -> None:
    log = EventLog(_resolve_path(args))
    log.clear()
    print("Event log cleared.")


def build_eventlog_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("eventlog", help="Manage structured event log")
    p.add_argument("--file", default=None, help="Path to event log file")
    sub = p.add_subparsers(dest="eventlog_cmd", required=True)

    ls = sub.add_parser("list", help="List events")
    ls.add_argument("--job", default=None, help="Filter by job name")
    ls.add_argument("--level", default=None, choices=EventLog.LEVELS, help="Filter by level")
    ls.set_defaults(func=cmd_eventlog_list)

    rec = sub.add_parser("record", help="Record a new event")
    rec.add_argument("job", help="Job name")
    rec.add_argument("event", help="Event name")
    rec.add_argument("--level", default="info", choices=EventLog.LEVELS)
    rec.add_argument("--message", default="", help="Optional message")
    rec.set_defaults(func=cmd_eventlog_record)

    cl = sub.add_parser("clear", help="Clear all events")
    cl.set_defaults(func=cmd_eventlog_clear)
