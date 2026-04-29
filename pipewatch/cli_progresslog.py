"""CLI subcommands for progress log inspection."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.progresslog import ProgressLog

_DEFAULT = Path(".pipewatch") / "progress.jsonl"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT)


def cmd_progress_list(args: argparse.Namespace) -> None:
    log = ProgressLog(_resolve_path(args))
    job = getattr(args, "job", None)
    entries = log.entries(job=job)
    if not entries:
        print("No progress entries found.")
        return
    for e in entries:
        bar = int(e.pct / 5)  # 20-char bar
        filled = "#" * bar
        empty = "-" * (20 - bar)
        print(f"[{filled}{empty}] {e.pct:6.2f}%  {e.job}/{e.step}  {e.message}")


def cmd_progress_latest(args: argparse.Namespace) -> None:
    log = ProgressLog(_resolve_path(args))
    job = args.job
    entry = log.latest(job)
    if entry is None:
        print(f"No progress recorded for job '{job}'.")
        return
    print(f"{entry.job}/{entry.step}: {entry.pct:.2f}% — {entry.message}")


def cmd_progress_clear(args: argparse.Namespace) -> None:
    log = ProgressLog(_resolve_path(args))
    log.clear()
    print("Progress log cleared.")


def build_progress_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("progress", help="Inspect pipeline progress log")
    p.add_argument("--file", default=None, help="Path to progress JSONL file")
    sp = p.add_subparsers(dest="progress_cmd", required=True)

    ls = sp.add_parser("list", help="List progress entries")
    ls.add_argument("--job", default=None, help="Filter by job name")
    ls.set_defaults(func=cmd_progress_list)

    lat = sp.add_parser("latest", help="Show latest progress for a job")
    lat.add_argument("job", help="Job name")
    lat.set_defaults(func=cmd_progress_latest)

    clr = sp.add_parser("clear", help="Clear all progress entries")
    clr.set_defaults(func=cmd_progress_clear)

    return p
