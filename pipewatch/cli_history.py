"""CLI sub-commands for run history management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from pipewatch.history import History
from pipewatch.report import format_summary, print_history


def _resolve_path(path_str: Optional[str]) -> Optional[Path]:
    return Path(path_str) if path_str else None


def cmd_history_show(args: argparse.Namespace) -> int:
    path = _resolve_path(getattr(args, "history_path", None))
    print_history(n=args.limit, history_path=path)
    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    path = _resolve_path(getattr(args, "history_path", None))
    history = History(path)
    count = len(history.all())
    history.clear()
    print(f"Cleared {count} history entries.")
    return 0


def cmd_history_stats(args: argparse.Namespace) -> int:
    path = _resolve_path(getattr(args, "history_path", None))
    entries = History(path).all()
    if not entries:
        print("No history recorded yet.")
        return 0
    total = len(entries)
    passed = sum(1 for e in entries if e.succeeded)
    durations = [e.duration_seconds for e in entries]
    avg_dur = sum(durations) / total
    print(f"Total runs   : {total}")
    print(f"Succeeded    : {passed}")
    print(f"Failed       : {total - passed}")
    print(f"Avg duration : {avg_dur:.2f}s")
    print(f"Min duration : {min(durations):.2f}s")
    print(f"Max duration : {max(durations):.2f}s")
    return 0


def build_history_parser(subparsers) -> None:
    hist = subparsers.add_parser("history", help="Manage run history")
    hist.add_argument(
        "--history-path", metavar="PATH", help="Override default history file path"
    )
    hist_sub = hist.add_subparsers(dest="history_cmd", required=True)

    show_p = hist_sub.add_parser("show", help="Print recent run history")
    show_p.add_argument("-n", "--limit", type=int, default=20, help="Number of entries")
    show_p.set_defaults(func=cmd_history_show)

    clear_p = hist_sub.add_parser("clear", help="Delete all history entries")
    clear_p.set_defaults(func=cmd_history_clear)

    stats_p = hist_sub.add_parser("stats", help="Show aggregate run statistics")
    stats_p.set_defaults(func=cmd_history_stats)
