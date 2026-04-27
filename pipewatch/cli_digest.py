"""CLI sub-commands for the digest feature."""
from __future__ import annotations

import argparse
import sys

from pipewatch.digest import build_digest, format_digest
from pipewatch.history import History


def _resolve_path(args: argparse.Namespace) -> str:
    return getattr(args, "history_file", None) or ".pipewatch_history.json"


def cmd_digest_show(args: argparse.Namespace) -> None:
    path = _resolve_path(args)
    history = History(path)
    pipeline = args.pipeline or path
    window = args.window

    digest = build_digest(history, pipeline=pipeline, window_hours=window)

    if args.json:
        import json
        print(json.dumps(digest.to_dict(), indent=2))
    else:
        print(format_digest(digest))


def build_digest_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "digest",
        help="Show a periodic summary digest of pipeline runs",
    )
    sub = parser.add_subparsers(dest="digest_cmd")

    show = sub.add_parser("show", help="Print digest for a pipeline")
    show.add_argument(
        "--pipeline",
        default=None,
        help="Pipeline label (defaults to history file path)",
    )
    show.add_argument(
        "--window",
        type=int,
        default=24,
        metavar="HOURS",
        help="Look-back window in hours (default: 24)",
    )
    show.add_argument(
        "--history-file",
        dest="history_file",
        default=None,
        metavar="PATH",
        help="Path to history JSON file",
    )
    show.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    show.set_defaults(func=cmd_digest_show)

    parser.set_defaults(
        func=lambda a: (parser.print_help(), sys.exit(0))
    )
