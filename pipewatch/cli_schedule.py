"""CLI sub-commands for schedule checking in pipewatch."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import Optional

from pipewatch.scheduler import parse_schedule


def cmd_schedule_check(args: argparse.Namespace) -> None:
    """Check whether a cron expression is currently due (or at a given time)."""
    try:
        schedule = parse_schedule(args.expr)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    at: Optional[datetime] = None
    if args.at:
        try:
            at = datetime.fromisoformat(args.at)
        except ValueError:
            print(
                f"Error: --at value {args.at!r} is not a valid ISO datetime",
                file=sys.stderr,
            )
            sys.exit(1)

    due = schedule.is_due(at)
    ref = at.isoformat() if at else datetime.now().strftime("%Y-%m-%d %H:%M")
    status = "DUE" if due else "NOT DUE"
    print(f"Schedule '{schedule.raw}' is {status} at {ref}")
    sys.exit(0 if due else 1)


def cmd_schedule_next(args: argparse.Namespace) -> None:
    """Print a human-readable description of a cron expression."""
    try:
        schedule = parse_schedule(args.expr)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    parts = [
        f"minute={schedule.minute}",
        f"hour={schedule.hour}",
        f"dom={schedule.day_of_month}",
        f"month={schedule.month}",
        f"dow={schedule.day_of_week}",
    ]
    print(f"Parsed schedule: {' '.join(parts)}")
    print(f"Raw expression : {schedule.raw}")


def build_schedule_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach 'schedule' sub-commands to the provided subparsers."""
    sched = subparsers.add_parser("schedule", help="Cron schedule utilities")
    sub = sched.add_subparsers(dest="schedule_cmd", required=True)

    # check
    p_check = sub.add_parser("check", help="Check if a schedule is due right now")
    p_check.add_argument("expr", help="Cron expression, e.g. '*/5 * * * *' or @hourly")
    p_check.add_argument(
        "--at",
        metavar="DATETIME",
        default=None,
        help="ISO datetime to check against instead of now (e.g. 2024-06-01T08:30)",
    )
    p_check.set_defaults(func=cmd_schedule_check)

    # describe
    p_next = sub.add_parser("describe", help="Describe a cron expression")
    p_next.add_argument("expr", help="Cron expression")
    p_next.set_defaults(func=cmd_schedule_next)
