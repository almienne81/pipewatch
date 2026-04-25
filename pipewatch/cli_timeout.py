"""CLI helpers for inspecting timeout configuration."""

from __future__ import annotations

import argparse
import sys

from pipewatch.timeout import TimeoutPolicy
from pipewatch.duration import parse_duration, format_duration, DurationError


def cmd_timeout_info(args: argparse.Namespace) -> None:
    """Print a human-readable summary of a timeout policy."""
    try:
        seconds = parse_duration(args.duration) if args.duration else None
    except DurationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    policy = TimeoutPolicy(
        seconds=seconds,
        kill_on_timeout=not args.no_kill,
    )

    if not policy.is_enabled():
        print("Timeout: disabled")
        return

    print(f"Timeout : {format_duration(int(policy.seconds))}")
    print(f"On breach: {'kill process' if policy.kill_on_timeout else 'raise only'}")


def build_timeout_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    """Register the *timeout* sub-command group."""
    p = parent.add_parser("timeout", help="Inspect timeout configuration")
    sub = p.add_subparsers(dest="timeout_cmd", required=True)

    info = sub.add_parser("info", help="Show timeout policy details")
    info.add_argument(
        "--duration",
        default=None,
        help="Timeout duration, e.g. 30s, 5m, 1h",
    )
    info.add_argument(
        "--no-kill",
        action="store_true",
        default=False,
        help="Do not kill the process on timeout (raise only)",
    )
    info.set_defaults(func=cmd_timeout_info)

    return p
