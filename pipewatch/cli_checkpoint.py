"""CLI sub-commands for inspecting pipeline checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.checkpoint import Checkpoint

_DEFAULT_PATH = Path(".pipewatch") / "checkpoints.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file) if getattr(args, "file", None) else _DEFAULT_PATH


def cmd_checkpoint_show(args: argparse.Namespace) -> None:
    cp = Checkpoint(_resolve_path(args))
    entries = cp.all()
    if not entries:
        print("No checkpoints recorded.")
        return
    for e in entries:
        symbol = {"ok": "✓", "failed": "✗", "skipped": "–"}.get(e.status, "?")
        msg = f"  {e.message}" if e.message else ""
        print(f"[{symbol}] {e.stage}{msg}")


def cmd_checkpoint_last(args: argparse.Namespace) -> None:
    cp = Checkpoint(_resolve_path(args))
    entry = cp.last(args.stage)
    if entry is None:
        print(f"No checkpoint found for stage: {args.stage}")
        return
    symbol = {"ok": "✓", "failed": "✗", "skipped": "–"}.get(entry.status, "?")
    print(f"[{symbol}] {entry.stage}: {entry.status}" + (f" — {entry.message}" if entry.message else ""))


def cmd_checkpoint_clear(args: argparse.Namespace) -> None:
    cp = Checkpoint(_resolve_path(args))
    cp.clear()
    print("Checkpoints cleared.")


def build_checkpoint_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("checkpoint", help="Inspect pipeline checkpoints")
    p.add_argument("--file", metavar="PATH", help="Checkpoint file path")
    sub = p.add_subparsers(dest="checkpoint_cmd", required=True)

    sub.add_parser("show", help="List all recorded checkpoints").set_defaults(
        func=cmd_checkpoint_show
    )

    last_p = sub.add_parser("last", help="Show last checkpoint for a stage")
    last_p.add_argument("stage", help="Stage name")
    last_p.set_defaults(func=cmd_checkpoint_last)

    sub.add_parser("clear", help="Delete all checkpoints").set_defaults(
        func=cmd_checkpoint_clear
    )
