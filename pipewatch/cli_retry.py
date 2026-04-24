"""CLI sub-commands for retry configuration inspection."""
from __future__ import annotations

import argparse
import sys

from pipewatch.retry import parse_retry_policy


def cmd_retry_info(args: argparse.Namespace) -> None:
    """Print a summary of the resolved retry policy."""
    try:
        policy = parse_retry_policy(
            max_attempts=args.max_attempts,
            delay=args.delay,
            backoff=args.backoff,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Max attempts : {policy.max_attempts}")
    print(f"Initial delay: {policy.delay_seconds}s")
    print(f"Backoff factor: {policy.backoff_factor}x")
    if policy.retry_on_codes:
        codes = ", ".join(str(c) for c in policy.retry_on_codes)
        print(f"Retry on exit codes: {codes}")
    else:
        print("Retry on exit codes: any non-zero")

    print()
    print("Attempt schedule (delay before each retry):")
    for attempt in range(1, policy.max_attempts):
        wait = policy.wait_seconds(attempt - 1)
        print(f"  Before attempt {attempt + 1}: {wait:.1f}s")


def build_retry_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *retry* sub-command group."""
    retry_parser = subparsers.add_parser(
        "retry", help="Inspect retry policy settings"
    )
    retry_sub = retry_parser.add_subparsers(dest="retry_cmd", required=True)

    info_parser = retry_sub.add_parser(
        "info", help="Show resolved retry policy"
    )
    info_parser.add_argument(
        "--max-attempts",
        dest="max_attempts",
        type=int,
        default=1,
        help="Maximum number of attempts (default: 1)",
    )
    info_parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait between retries (default: 5.0)",
    )
    info_parser.add_argument(
        "--backoff",
        type=float,
        default=1.0,
        help="Backoff multiplier applied to delay (default: 1.0)",
    )
    info_parser.set_defaults(func=cmd_retry_info)
