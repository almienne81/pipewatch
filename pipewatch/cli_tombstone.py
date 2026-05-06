"""CLI commands for managing pipeline tombstones."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.tombstone import Tombstone, TombstoneError


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or ".pipewatch/tombstones.json")


def cmd_tombstone_list(args: argparse.Namespace) -> None:
    ts = Tombstone(_resolve_path(args))
    entries = ts.all()
    if not entries:
        print("No retired jobs.")
        return
    for e in entries:
        by = f" by {e.retired_by}" if e.retired_by else ""
        note = f" — {e.note}" if e.note else ""
        print(f"[{e.retired_at.strftime('%Y-%m-%d %H:%M')}] {e.job}{by}: {e.reason}{note}")


def cmd_tombstone_check(args: argparse.Namespace) -> None:
    ts = Tombstone(_resolve_path(args))
    entry = ts.get(args.job)
    if entry is None:
        print(f"{args.job}: active")
    else:
        print(f"{args.job}: RETIRED — {entry.reason}")


def cmd_tombstone_retire(args: argparse.Namespace) -> None:
    ts = Tombstone(_resolve_path(args))
    try:
        entry = ts.retire(
            job=args.job,
            reason=args.reason,
            retired_by=getattr(args, "by", "") or "",
            note=getattr(args, "note", "") or "",
        )
        print(f"Retired '{entry.job}' at {entry.retired_at.isoformat()}.")
    except TombstoneError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_tombstone_remove(args: argparse.Namespace) -> None:
    ts = Tombstone(_resolve_path(args))
    if ts.remove(args.job):
        print(f"Tombstone for '{args.job}' removed.")
    else:
        print(f"No tombstone found for '{args.job}'.")


def build_tombstone_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("tombstone", help="manage retired pipeline job markers")
    p.add_argument("--file", metavar="PATH", help="tombstone store path")
    sp = p.add_subparsers(dest="tombstone_cmd", required=True)

    sp.add_parser("list", help="list all retired jobs").set_defaults(func=cmd_tombstone_list)

    chk = sp.add_parser("check", help="check if a job is retired")
    chk.add_argument("job")
    chk.set_defaults(func=cmd_tombstone_check)

    ret = sp.add_parser("retire", help="mark a job as permanently retired")
    ret.add_argument("job")
    ret.add_argument("reason")
    ret.add_argument("--by", metavar="USER", default="")
    ret.add_argument("--note", default="")
    ret.set_defaults(func=cmd_tombstone_retire)

    rm = sp.add_parser("remove", help="remove a tombstone entry")
    rm.add_argument("job")
    rm.set_defaults(func=cmd_tombstone_remove)

    return p
