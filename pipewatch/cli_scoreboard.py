"""CLI sub-commands for the pipewatch scoreboard."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.scoreboard import Scoreboard

_DEFAULT_PATH = Path(".pipewatch") / "scoreboard.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_scoreboard_list(args: argparse.Namespace) -> None:
    sb = Scoreboard(_resolve_path(args))
    entries = sb.all()
    if not entries:
        print("No entries recorded.")
        return
    by = getattr(args, "sort", "success_rate")
    ranked = sb.ranked(by=by)
    print(f"{'Job':<30} {'Runs':>6} {'OK':>6} {'Fail':>6} {'Rate':>8}")
    print("-" * 60)
    for e in ranked:
        rate = f"{e.success_rate:.1%}" if e.success_rate is not None else "n/a"
        print(f"{e.job:<30} {e.runs:>6} {e.successes:>6} {e.failures:>6} {rate:>8}")


def cmd_scoreboard_record(args: argparse.Namespace) -> None:
    sb = Scoreboard(_resolve_path(args))
    success = args.outcome.lower() in ("ok", "success", "true", "1")
    entry = sb.record(args.job, success)
    rate = f"{entry.success_rate:.1%}" if entry.success_rate is not None else "n/a"
    print(f"Recorded {'OK' if success else 'FAIL'} for {entry.job!r} "
          f"(runs={entry.runs}, rate={rate})")


def cmd_scoreboard_show(args: argparse.Namespace) -> None:
    sb = Scoreboard(_resolve_path(args))
    entry = sb.get(args.job)
    if entry is None:
        print(f"No data for job {args.job!r}.")
        return
    rate = f"{entry.success_rate:.1%}" if entry.success_rate is not None else "n/a"
    print(f"Job      : {entry.job}")
    print(f"Runs     : {entry.runs}")
    print(f"Successes: {entry.successes}")
    print(f"Failures : {entry.failures}")
    print(f"Rate     : {rate}")


def cmd_scoreboard_clear(args: argparse.Namespace) -> None:
    sb = Scoreboard(_resolve_path(args))
    sb.clear()
    print("Scoreboard cleared.")


def build_scoreboard_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("scoreboard", help="Pipeline job scoreboard")
    p.add_argument("--file", default=None, help="Path to scoreboard file")
    sub = p.add_subparsers(dest="scoreboard_cmd", required=True)

    lst = sub.add_parser("list", help="List all jobs ranked by score")
    lst.add_argument("--sort", choices=["success_rate", "runs"],
                     default="success_rate", help="Ranking key")
    lst.set_defaults(func=cmd_scoreboard_list)

    rec = sub.add_parser("record", help="Record a run outcome")
    rec.add_argument("job", help="Job name")
    rec.add_argument("outcome", help="Outcome: ok|fail")
    rec.set_defaults(func=cmd_scoreboard_record)

    shw = sub.add_parser("show", help="Show stats for a single job")
    shw.add_argument("job", help="Job name")
    shw.set_defaults(func=cmd_scoreboard_show)

    clr = sub.add_parser("clear", help="Clear all scoreboard data")
    clr.set_defaults(func=cmd_scoreboard_clear)
