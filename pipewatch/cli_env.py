"""CLI sub-commands for inspecting environment snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from pipewatch.env import EnvError, capture


def cmd_env_show(args: argparse.Namespace) -> None:
    """Print captured environment variables as JSON."""
    keys: Optional[List[str]] = args.keys or None
    prefix: Optional[str] = args.prefix or None

    try:
        snap = capture(keys=keys, prefix=prefix)
    except EnvError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not snap:
        print("(no variables captured)")
        return

    print(json.dumps(snap.to_dict(), indent=2, sort_keys=True))


def cmd_env_get(args: argparse.Namespace) -> None:
    """Print the value of a single environment variable, or exit 1 if absent."""
    snap = capture(keys=[args.name])
    value = snap.get(args.name)
    if value is None:
        print(f"error: variable '{args.name}' is not set", file=sys.stderr)
        sys.exit(1)
    print(value)


def build_env_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register 'env' sub-commands onto *subparsers*."""
    env_parser = subparsers.add_parser("env", help="Inspect runtime environment variables")
    env_sub = env_parser.add_subparsers(dest="env_command", required=True)

    # --- show ---
    show_p = env_sub.add_parser("show", help="Print captured env vars as JSON")
    group = show_p.add_mutually_exclusive_group()
    group.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Explicit variable names to capture",
    )
    group.add_argument(
        "--prefix",
        metavar="PREFIX",
        help="Capture all variables starting with PREFIX",
    )
    show_p.set_defaults(func=cmd_env_show)

    # --- get ---
    get_p = env_sub.add_parser("get", help="Print the value of a single variable")
    get_p.add_argument("name", metavar="NAME", help="Variable name")
    get_p.set_defaults(func=cmd_env_get)

    return env_parser
