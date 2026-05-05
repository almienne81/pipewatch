"""CLI commands for the trace log."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.tracelog import TraceLog

_DEFAULT_PATH = Path(".pipewatch/tracelog.json")


def _resolve_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "file", None) or _DEFAULT_PATH)


def cmd_tracelog_list(args: argparse.Namespace) -> None:
    log = TraceLog(_resolve_path(args))
    entries = log.all()
    if not entries:
        print("No trace entries found.")
        return
    job_filter = getattr(args, "job", None)
    span_filter = getattr(args, "span", None)
    if job_filter:
        entries = [e for e in entries if e.job == job_filter]
    if span_filter:
        entries = [e for e in entries if e.span == span_filter]
    for e in entries:
        dur = e.duration_seconds()
        dur_str = f"{dur:.3f}s" if dur is not None else "?"
        print(f"[{e.started_at.isoformat()}] {e.job}/{e.span} status={e.status} dur={dur_str}")


def cmd_tracelog_clear(args: argparse.Namespace) -> None:
    log = TraceLog(_resolve_path(args))
    log.clear()
    print("Trace log cleared.")


def cmd_tracelog_stats(args: argparse.Namespace) -> None:
    log = TraceLog(_resolve_path(args))
    entries = log.all()
    total = len(entries)
    ok = sum(1 for e in entries if e.status == "ok")
    failed = total - ok
    durations = [d for e in entries if (d := e.duration_seconds()) is not None]
    avg = sum(durations) / len(durations) if durations else 0.0
    print(f"Total spans : {total}")
    print(f"OK          : {ok}")
    print(f"Failed      : {failed}")
    print(f"Avg duration: {avg:.3f}s")


def build_tracelog_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("tracelog", help="Manage the pipeline trace log")
    sp = p.add_subparsers(dest="tracelog_cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", help="Path to trace log file")

    ls = sp.add_parser("list", parents=[common], help="List trace entries")
    ls.add_argument("--job", help="Filter by job name")
    ls.add_argument("--span", help="Filter by span name")
    ls.set_defaults(func=cmd_tracelog_list)

    cl = sp.add_parser("clear", parents=[common], help="Clear trace log")
    cl.set_defaults(func=cmd_tracelog_clear)

    st = sp.add_parser("stats", parents=[common], help="Show trace statistics")
    st.set_defaults(func=cmd_tracelog_stats)
