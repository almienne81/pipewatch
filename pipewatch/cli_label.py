"""CLI commands for inspecting and filtering pipeline run labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipewatch.label import LabelError, Labels


def _resolve_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def cmd_label_list(args: argparse.Namespace) -> None:
    """Print all labels loaded from a JSON file as key=value lines."""
    path = _resolve_path(args.file)
    if not path.exists():
        print("(no labels file found)", file=sys.stderr)
        sys.exit(1)
    raw = json.loads(path.read_text())
    labels = Labels.from_dict(raw)
    if not labels:
        print("(no labels set)")
        return
    for k, v in labels.items():
        print(f"{k}={v}")


def cmd_label_filter(args: argparse.Namespace) -> None:
    """Exit 0 if labels match the given selector, else exit 1."""
    path = _resolve_path(args.file)
    if not path.exists():
        print("(no labels file found)", file=sys.stderr)
        sys.exit(1)
    raw = json.loads(path.read_text())
    labels = Labels.from_dict(raw)
    selector: dict[str, str] = {}
    for pair in args.selector:
        if "=" not in pair:
            print(f"Invalid selector {pair!r}: expected key=value", file=sys.stderr)
            sys.exit(2)
        k, v = pair.split("=", 1)
        selector[k] = v
    if labels.matches(selector):
        print("match")
        sys.exit(0)
    else:
        print("no match")
        sys.exit(1)


def cmd_label_set(args: argparse.Namespace) -> None:
    """Persist a new key=value label into the labels JSON file."""
    path = _resolve_path(args.file)
    raw: dict[str, str] = json.loads(path.read_text()) if path.exists() else {}
    labels = Labels.from_dict(raw)
    try:
        labels = labels.set(args.key, args.value)
    except LabelError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    path.write_text(json.dumps(labels.to_dict(), indent=2))
    print(f"Set {args.key}={args.value}")


def build_label_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("label", help="Manage pipeline run labels")
    sp = p.add_subparsers(dest="label_cmd", required=True)

    ls = sp.add_parser("list", help="List all labels")
    ls.add_argument("--file", default=".pipewatch_labels.json")
    ls.set_defaults(func=cmd_label_list)

    flt = sp.add_parser("filter", help="Check if labels match a selector")
    flt.add_argument("--file", default=".pipewatch_labels.json")
    flt.add_argument("selector", nargs="+", metavar="KEY=VALUE")
    flt.set_defaults(func=cmd_label_filter)

    st = sp.add_parser("set", help="Set a label value")
    st.add_argument("--file", default=".pipewatch_labels.json")
    st.add_argument("key")
    st.add_argument("value")
    st.set_defaults(func=cmd_label_set)
