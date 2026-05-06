"""CLI commands for inspecting and managing concurrency state."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipewatch.concurrency import ConcurrencyLimiter, ConcurrencyPolicy


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.state_file)


def cmd_concurrency_status(args: argparse.Namespace) -> None:
    limiter = ConcurrencyLimiter(
        _resolve_path(args),
        ConcurrencyPolicy(max_concurrent=args.max_concurrent),
    )
    slots = limiter.active_slots()
    if not slots:
        print("No active slots.")
        return
    print(f"{len(slots)} active slot(s):")
    for s in slots:
        print(f"  pid={s.pid}  job={s.job}  started_at={s.started_at:.0f}")


def cmd_concurrency_clear(args: argparse.Namespace) -> None:
    limiter = ConcurrencyLimiter(
        _resolve_path(args),
        ConcurrencyPolicy(max_concurrent=args.max_concurrent),
    )
    limiter.clear()
    print("Concurrency state cleared.")


def cmd_concurrency_check(args: argparse.Namespace) -> None:
    limiter = ConcurrencyLimiter(
        _resolve_path(args),
        ConcurrencyPolicy(max_concurrent=args.max_concurrent),
    )
    slots = limiter.active_slots()
    remaining = args.max_concurrent - len(slots)
    if remaining > 0:
        print(f"OK — {remaining} slot(s) available (limit={args.max_concurrent}).")
    else:
        print(
            f"LIMIT REACHED — {len(slots)} active slot(s) (limit={args.max_concurrent})."
        )
        sys.exit(1)


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-file",
        default=".pipewatch_concurrency.json",
        help="Path to concurrency state file.",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=1,
        help="Maximum number of concurrent slots (default: 1).",
    )


def build_concurrency_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("concurrency", help="Manage pipeline concurrency limits.")
    cmds = p.add_subparsers(dest="concurrency_cmd", required=True)

    status = cmds.add_parser("status", help="Show active concurrency slots.")
    _add_common(status)
    status.set_defaults(func=cmd_concurrency_status)

    check = cmds.add_parser("check", help="Exit 1 if limit is reached.")
    _add_common(check)
    check.set_defaults(func=cmd_concurrency_check)

    clear = cmds.add_parser("clear", help="Clear all concurrency state.")
    _add_common(clear)
    clear.set_defaults(func=cmd_concurrency_clear)
