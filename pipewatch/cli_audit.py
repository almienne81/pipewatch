"""CLI sub-commands for the audit log."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.audit import Audit

_DEFAULT_PATH = Path(".pipewatch") / "audit.jsonl"


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "audit_file", None) or _DEFAULT_PATH)


def cmd_audit_list(args: argparse.Namespace) -> None:
    audit = Audit(_resolve_path(args))
    events = audit.for_job(args.job) if getattr(args, "job", None) else audit.all()
    if not events:
        print("No audit events found.")
        return
    for e in events:
        code = f" exit={e.exit_code}" if e.exit_code is not None else ""
        detail = f" — {e.details}" if e.details else ""
        print(f"[{e.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {e.job} {e.event}{code}{detail}")


def cmd_audit_clear(args: argparse.Namespace) -> None:
    audit = Audit(_resolve_path(args))
    audit.clear()
    print("Audit log cleared.")


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Manage the pipeline audit log")
    p.add_argument("--audit-file", metavar="PATH", help="Path to audit JSONL file")
    sub = p.add_subparsers(dest="audit_cmd", required=True)

    ls = sub.add_parser("list", help="List audit events")
    ls.add_argument("--job", metavar="NAME", help="Filter by job name")
    ls.set_defaults(func=cmd_audit_list)

    cl = sub.add_parser("clear", help="Clear the audit log")
    cl.set_defaults(func=cmd_audit_clear)
