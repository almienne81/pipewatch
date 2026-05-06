"""cli_pinboard.py — CLI subcommands for the pinboard feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.pinboard import Pinboard, PinboardError

_DEFAULT_PATH = Path(".pipewatch/pinboard.json")


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_pin_list(args: argparse.Namespace) -> None:
    pb = Pinboard(_resolve_path(args))
    entries = pb.all()
    if not entries:
        print("No pins.")
        return
    for e in entries:
        print(f"{e.key}={e.value}  (pinned {e.pinned_at})")


def cmd_pin_get(args: argparse.Namespace) -> None:
    pb = Pinboard(_resolve_path(args))
    entry = pb.get(args.key)
    if entry is None:
        print(f"Key '{args.key}' not found.")
    else:
        print(entry.value)


def cmd_pin_set(args: argparse.Namespace) -> None:
    pb = Pinboard(_resolve_path(args))
    try:
        entry = pb.pin(args.key, args.value)
        print(f"Pinned {entry.key}={entry.value}")
    except PinboardError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_pin_remove(args: argparse.Namespace) -> None:
    pb = Pinboard(_resolve_path(args))
    removed = pb.remove(args.key)
    if removed:
        print(f"Removed pin '{args.key}'.")
    else:
        print(f"Key '{args.key}' not found.")


def cmd_pin_clear(args: argparse.Namespace) -> None:
    pb = Pinboard(_resolve_path(args))
    pb.clear()
    print("Pinboard cleared.")


def build_pinboard_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("pinboard", help="Manage named pin store")
    p.add_argument("--file", default=None, help="Path to pinboard JSON file")
    cmds = p.add_subparsers(dest="pin_cmd", required=True)

    cmds.add_parser("list", help="List all pins").set_defaults(func=cmd_pin_list)

    g = cmds.add_parser("get", help="Get a pin value")
    g.add_argument("key")
    g.set_defaults(func=cmd_pin_get)

    s = cmds.add_parser("set", help="Set a pin value")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(func=cmd_pin_set)

    r = cmds.add_parser("remove", help="Remove a pin")
    r.add_argument("key")
    r.set_defaults(func=cmd_pin_remove)

    cmds.add_parser("clear", help="Clear all pins").set_defaults(func=cmd_pin_clear)
