"""CLI commands for watermark inspection and management."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.watermark import Watermark, WatermarkError


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(args.file)


def cmd_watermark_show(args: argparse.Namespace) -> None:
    wm = Watermark(_resolve_path(args))
    entries = wm.all()
    if not entries:
        print("No watermarks recorded.")
        return
    for e in sorted(entries, key=lambda x: (x.job, x.key)):
        print(f"{e.job}  {e.key}  {e.value}  {e.recorded_at.isoformat()}")


def cmd_watermark_get(args: argparse.Namespace) -> None:
    wm = Watermark(_resolve_path(args))
    entry = wm.get(args.job, args.key)
    if entry is None:
        print(f"No watermark for {args.job}/{args.key}")
    else:
        print(f"{entry.value}  (recorded {entry.recorded_at.isoformat()})")


def cmd_watermark_update(args: argparse.Namespace) -> None:
    wm = Watermark(_resolve_path(args))
    try:
        entry = wm.update(args.job, args.key, args.value)
    except WatermarkError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    print(f"Watermark set: {entry.job}/{entry.key} = {entry.value}")


def cmd_watermark_clear(args: argparse.Namespace) -> None:
    wm = Watermark(_resolve_path(args))
    if args.all:
        wm.clear_all()
        print("All watermarks cleared.")
    else:
        if not args.job or not args.key:
            print("Error: --job and --key are required unless --all is set.")
            raise SystemExit(1)
        wm.clear(args.job, args.key)
        print(f"Watermark cleared: {args.job}/{args.key}")


def build_watermark_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("watermark", help="Manage pipeline watermarks")
    p.add_argument("--file", default=".pipewatch_watermarks.json")
    cmds = p.add_subparsers(dest="watermark_cmd", required=True)

    cmds.add_parser("show", help="List all watermarks").set_defaults(func=cmd_watermark_show)

    g = cmds.add_parser("get", help="Get watermark for a job/key")
    g.add_argument("job")
    g.add_argument("key")
    g.set_defaults(func=cmd_watermark_get)

    u = cmds.add_parser("update", help="Update watermark if value is higher")
    u.add_argument("job")
    u.add_argument("key")
    u.add_argument("value", type=float)
    u.set_defaults(func=cmd_watermark_update)

    c = cmds.add_parser("clear", help="Clear watermark(s)")
    c.add_argument("--job", default="")
    c.add_argument("--key", default="")
    c.add_argument("--all", action="store_true")
    c.set_defaults(func=cmd_watermark_clear)
