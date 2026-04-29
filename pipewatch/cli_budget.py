"""CLI sub-commands for inspecting budget policies."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.budget import BudgetError, BudgetPolicy, check_budget
from pipewatch.duration import format_duration, parse_duration, DurationError


def cmd_budget_info(args: argparse.Namespace) -> None:
    """Print the resolved budget policy."""
    warn: Optional[float] = None
    fail: Optional[float] = None

    try:
        if args.warn:
            warn = parse_duration(args.warn)
        if args.fail:
            fail = parse_duration(args.fail)
        policy = BudgetPolicy(warn_seconds=warn, fail_seconds=fail)
    except (BudgetError, DurationError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    d = policy.to_dict()
    print(f"warn_seconds : {d['warn_seconds']}")
    print(f"fail_seconds : {d['fail_seconds']}")


def cmd_budget_check(args: argparse.Namespace) -> None:
    """Simulate a budget check for a given elapsed duration."""
    try:
        elapsed = parse_duration(args.elapsed)
        warn = parse_duration(args.warn) if args.warn else None
        fail = parse_duration(args.fail) if args.fail else None
        policy = BudgetPolicy(warn_seconds=warn, fail_seconds=fail)
    except (BudgetError, DurationError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    result = check_budget(policy, elapsed)
    status = "FAIL" if result.failed else ("WARN" if result.warned else "OK")
    msg = result.message or f"Elapsed {format_duration(int(elapsed))} is within budget."
    print(f"[{status}] {msg}")
    if result.failed:
        raise SystemExit(2)


def build_budget_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("budget", help="Inspect or simulate budget policies")
    sub = p.add_subparsers(dest="budget_cmd", required=True)

    info = sub.add_parser("info", help="Show the resolved budget policy")
    info.add_argument("--warn", default=None, help="Soft budget (e.g. 5m)")
    info.add_argument("--fail", default=None, help="Hard budget (e.g. 10m)")
    info.set_defaults(func=cmd_budget_info)

    check = sub.add_parser("check", help="Check elapsed time against a budget")
    check.add_argument("elapsed", help="Elapsed duration (e.g. 7m30s)")
    check.add_argument("--warn", default=None, help="Soft budget")
    check.add_argument("--fail", default=None, help="Hard budget")
    check.set_defaults(func=cmd_budget_check)
