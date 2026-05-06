"""cli_banlist.py — CLI subcommands for the banlist module."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.banlist import Banlist, BanlistError

_DEFAULT_PATH = Path(".pipewatch") / "banlist.json"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_ban_list(args: argparse.Namespace) -> None:
    bl = Banlist(_resolve_path(args))
    entries = bl.all()
    if not entries:
        print("No banned jobs.")
        return
    for e in entries:
        print(f"{e.job:30s}  {e.banned_at.strftime('%Y-%m-%d %H:%M')}  {e.reason}  (by {e.banned_by})")


def cmd_ban_add(args: argparse.Namespace) -> None:
    bl = Banlist(_resolve_path(args))
    try:
        entry = bl.ban(args.job, args.reason, banned_by=args.by)
        print(f"Banned '{entry.job}' at {entry.banned_at.isoformat()}.")
    except BanlistError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_ban_remove(args: argparse.Namespace) -> None:
    bl = Banlist(_resolve_path(args))
    removed = bl.unban(args.job)
    if removed:
        print(f"'{args.job}' removed from banlist.")
    else:
        print(f"'{args.job}' was not on the banlist.")


def cmd_ban_check(args: argparse.Namespace) -> None:
    bl = Banlist(_resolve_path(args))
    entry = bl.get(args.job)
    if entry:
        print(f"BANNED  reason={entry.reason}  at={entry.banned_at.isoformat()}")
        raise SystemExit(1)
    print(f"'{args.job}' is not banned.")


def build_banlist_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("banlist", help="Manage banned job identifiers")
    p.add_argument("--file", metavar="PATH", help="Path to banlist JSON file")
    sp = p.add_subparsers(dest="banlist_cmd", required=True)

    sp.add_parser("list", help="List all banned jobs").set_defaults(func=cmd_ban_list)

    p_add = sp.add_parser("add", help="Ban a job")
    p_add.add_argument("job", help="Job identifier to ban")
    p_add.add_argument("reason", help="Reason for the ban")
    p_add.add_argument("--by", default="system", metavar="ACTOR", help="Who issued the ban")
    p_add.set_defaults(func=cmd_ban_add)

    p_rm = sp.add_parser("remove", help="Remove a job from the banlist")
    p_rm.add_argument("job", help="Job identifier to unban")
    p_rm.set_defaults(func=cmd_ban_remove)

    p_chk = sp.add_parser("check", help="Check whether a job is banned (exits 1 if banned)")
    p_chk.add_argument("job", help="Job identifier to check")
    p_chk.set_defaults(func=cmd_ban_check)
