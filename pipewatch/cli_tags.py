"""CLI sub-commands for inspecting tags on history entries."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipewatch.history import History
from pipewatch.tags import tags_from_dict

_DEFAULT_HISTORY = Path.home() / ".pipewatch" / "history.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.history_file) if getattr(args, "history_file", None) else _DEFAULT_HISTORY


def cmd_tags_list(args: argparse.Namespace) -> None:
    """Print all unique tag keys seen across history."""
    path = _resolve_path(args)
    history = History(path)
    entries = history.all()
    if not entries:
        print("No history entries found.")
        return
    all_keys: set[str] = set()
    for entry in entries:
        raw = entry.extra.get("tags", {})
        if isinstance(raw, dict):
            all_keys.update(raw.keys())
    if not all_keys:
        print("No tags found in history.")
        return
    for key in sorted(all_keys):
        print(key)


def cmd_tags_filter(args: argparse.Namespace) -> None:
    """Print history entries that match ALL supplied key=value tags."""
    path = _resolve_path(args)
    history = History(path)
    entries = history.all()

    filter_tags: dict[str, str] = {}
    for item in args.tag:
        if '=' not in item:
            print(f"Error: tag filter {item!r} must be 'key=value'", file=sys.stderr)
            sys.exit(1)
        k, _, v = item.partition('=')
        filter_tags[k.strip()] = v.strip()

    matched = []
    for entry in entries:
        raw = entry.extra.get("tags", {})
        entry_tags = tags_from_dict(raw) if isinstance(raw, dict) else None
        if entry_tags and all(entry_tags.get(k) == v for k, v in filter_tags.items()):
            matched.append(entry)

    if not matched:
        print("No matching entries.")
        return
    for e in matched:
        status = "OK" if e.exit_code == 0 else "FAIL"
        print(f"[{status}] {e.command}  exit={e.exit_code}  tags={e.extra.get('tags', {})}")


def build_tags_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    tags_parser = subparsers.add_parser("tags", help="Inspect tags on history entries")
    tags_parser.add_argument("--history-file", metavar="PATH", help="Path to history file")
    tag_sub = tags_parser.add_subparsers(dest="tags_cmd", required=True)

    tag_sub.add_parser("list", help="List all unique tag keys in history").set_defaults(
        func=cmd_tags_list
    )

    filter_p = tag_sub.add_parser("filter", help="Filter history by tag key=value pairs")
    filter_p.add_argument(
        "tag", nargs="+", metavar="KEY=VALUE", help="Tag filter (repeatable)"
    )
    filter_p.set_defaults(func=cmd_tags_filter)
