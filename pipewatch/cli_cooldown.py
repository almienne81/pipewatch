"""CLI sub-commands for inspecting and managing cooldown state."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.cooldown import Cooldown

_DEFAULT_STATE = Path(".pipewatch") / "cooldown.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "state_file", None) or _DEFAULT_STATE)


def cmd_cooldown_list(args: argparse.Namespace) -> None:
    """List all active cooldown entries."""
    cd = Cooldown(path=_resolve_path(args), default_seconds=args.default_seconds)
    entries = cd.all_entries()
    if not entries:
        print("No cooldown entries.")
        return
    print(f"{'KEY':<30} {'LAST ALERTED':>20} {'COUNT':>6}")
    print("-" * 60)
    import time
    for e in sorted(entries, key=lambda x: x.last_alerted, reverse=True):
        age = time.time() - e.last_alerted
        alerted_str = f"{age:.0f}s ago"
        print(f"{e.key:<30} {alerted_str:>20} {e.alert_count:>6}")


def cmd_cooldown_check(args: argparse.Namespace) -> None:
    """Check whether a key is currently suppressed."""
    cd = Cooldown(path=_resolve_path(args), default_seconds=args.default_seconds)
    suppressed = cd.is_suppressed(args.key, args.seconds)
    status = "SUPPRESSED" if suppressed else "ALLOWED"
    print(f"{args.key}: {status}")


def cmd_cooldown_reset(args: argparse.Namespace) -> None:
    """Clear cooldown state for a specific key."""
    cd = Cooldown(path=_resolve_path(args), default_seconds=args.default_seconds)
    cd.reset(args.key)
    print(f"Cooldown reset for key: {args.key}")


def build_cooldown_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("cooldown", help="Manage alert cooldown state")
    p.add_argument("--state-file", default=str(_DEFAULT_STATE), help="Path to cooldown state file")
    p.add_argument("--default-seconds", type=float, default=300.0, help="Default cooldown window in seconds")

    sub = p.add_subparsers(dest="cooldown_cmd", required=True)

    sub.add_parser("list", help="List all cooldown entries").set_defaults(func=cmd_cooldown_list)

    check_p = sub.add_parser("check", help="Check if a key is suppressed")
    check_p.add_argument("key", help="Pipeline key to check")
    check_p.add_argument("--seconds", type=float, default=None, help="Override cooldown window")
    check_p.set_defaults(func=cmd_cooldown_check)

    reset_p = sub.add_parser("reset", help="Reset cooldown for a key")
    reset_p.add_argument("key", help="Pipeline key to reset")
    reset_p.set_defaults(func=cmd_cooldown_reset)
