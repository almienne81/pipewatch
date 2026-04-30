"""CLI sub-commands for inspecting and managing debounce state."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.debounce import Debounce

_DEFAULT_STATE = Path(".pipewatch") / "debounce_state.json"
_DEFAULT_QUIET = 60.0


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "state_file", None) or _DEFAULT_STATE)


def cmd_debounce_status(args: argparse.Namespace) -> None:
    db = Debounce(quiet_seconds=_DEFAULT_QUIET, state_file=_resolve_path(args))
    key = args.key
    entry = db.state_for(key)
    if entry is None:
        print(f"[debounce] no state for key '{key}'")
    else:
        import time
        age = time.time() - entry.last_trigger
        print(f"[debounce] key='{key}'  triggers={entry.count}  age={age:.1f}s")


def cmd_debounce_reset(args: argparse.Namespace) -> None:
    db = Debounce(quiet_seconds=_DEFAULT_QUIET, state_file=_resolve_path(args))
    db.reset(args.key)
    print(f"[debounce] reset key '{args.key}'")


def cmd_debounce_trigger(args: argparse.Namespace) -> None:
    db = Debounce(quiet_seconds=args.quiet, state_file=_resolve_path(args))
    allowed = db.trigger(args.key)
    status = "SEND" if allowed else "SUPPRESSED"
    print(f"[debounce] key='{args.key}'  result={status}")


def build_debounce_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("debounce", help="manage debounce state")
    p.add_argument("--state-file", default=str(_DEFAULT_STATE), metavar="PATH")
    sub = p.add_subparsers(dest="debounce_cmd", required=True)

    # status
    ps = sub.add_parser("status", help="show debounce state for a key")
    ps.add_argument("key")
    ps.set_defaults(func=cmd_debounce_status)

    # reset
    pr = sub.add_parser("reset", help="clear debounce state for a key")
    pr.add_argument("key")
    pr.set_defaults(func=cmd_debounce_reset)

    # trigger
    pt = sub.add_parser("trigger", help="simulate a trigger and print send/suppress")
    pt.add_argument("key")
    pt.add_argument("--quiet", type=float, default=_DEFAULT_QUIET, metavar="SECONDS")
    pt.set_defaults(func=cmd_debounce_trigger)

    return p
