"""CLI helpers for displaying captured output."""
from __future__ import annotations

import argparse
import sys

from pipewatch.output_capture import capture


def cmd_output_run(args: argparse.Namespace) -> None:
    """Run a command and pretty-print its captured output."""
    if not args.cmd:
        print("error: no command provided", file=sys.stderr)
        sys.exit(1)

    result = capture(
        args.cmd,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
    )

    status = "OK" if result.succeeded() else f"FAILED (rc={result.returncode})"
    print(f"Command : {result.command}")
    print(f"Status  : {status}")
    print(f"Started : {result.started_at.isoformat()}")
    print(f"Finished: {result.finished_at.isoformat()}")
    if result.truncated:
        print("[output truncated]")
    if args.tail:
        print("\n--- tail ---")
        print(result.tail(args.tail))
    else:
        if result.stdout.strip():
            print("\n--- stdout ---")
            print(result.stdout)
        if result.stderr.strip():
            print("\n--- stderr ---")
            print(result.stderr)

    if not result.succeeded():
        sys.exit(result.returncode if result.returncode > 0 else 1)


def build_output_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "output",
        help="Run a command and display captured output",
    )
    p.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command to run (everything after --)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Kill command after SECONDS",
    )
    p.add_argument(
        "--max-bytes",
        type=int,
        default=256 * 1024,
        dest="max_bytes",
        metavar="BYTES",
        help="Truncate each stream at BYTES (default: 262144)",
    )
    p.add_argument(
        "--tail",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N lines of combined output",
    )
    p.set_defaults(func=cmd_output_run)
