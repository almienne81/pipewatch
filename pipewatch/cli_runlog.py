"""CLI subcommands for inspecting run logs."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.runlog import RunLog

_DEFAULT_PATH = Path(".pipewatch") / "runlog.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "log_file", None) or _DEFAULT_PATH)


def cmd_runlog_list(args: argparse.Namespace) -> None:
    log = RunLog(_resolve_path(args))
    entries = log.all()
    if not entries:
        print("No run log entries found.")
        return
    for e in entries:
        status = "OK" if e.succeeded else "FAIL"
        dur = f"{e.duration_seconds:.1f}s" if e.duration_seconds is not None else "?"
        print(f"[{status}] {e.run_id[:8]}  {e.command!r}  duration={dur}")


def cmd_runlog_show(args: argparse.Namespace) -> None:
    log = RunLog(_resolve_path(args))
    entry = log.get(args.run_id)
    if entry is None:
        print(f"No entry found for run_id: {args.run_id}")
        return
    print(f"run_id    : {entry.run_id}")
    print(f"command   : {entry.command}")
    print(f"exit_code : {entry.exit_code}")
    print(f"duration  : {entry.duration_seconds}s")
    print(f"tags      : {entry.tags}")
    if entry.stdout:
        print("--- stdout ---")
        print(entry.stdout)
    if entry.stderr:
        print("--- stderr ---")
        print(entry.stderr)


def cmd_runlog_clear(args: argparse.Namespace) -> None:
    log = RunLog(_resolve_path(args))
    log.clear()
    print("Run log cleared.")


def build_runlog_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("runlog", help="Inspect per-run logs")
    p.add_argument("--log-file", metavar="PATH", help="Path to run log JSON file")
    sub = p.add_subparsers(dest="runlog_cmd", required=True)

    sub.add_parser("list", help="List all run log entries").set_defaults(
        func=cmd_runlog_list
    )

    show_p = sub.add_parser("show", help="Show details for a specific run")
    show_p.add_argument("run_id", help="Run ID (or prefix) to display")
    show_p.set_defaults(func=cmd_runlog_show)

    sub.add_parser("clear", help="Clear all run log entries").set_defaults(
        func=cmd_runlog_clear
    )
