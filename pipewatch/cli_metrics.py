"""CLI sub-commands for displaying pipeline run metrics."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from pipewatch.history import History
from pipewatch.metrics import Metrics
from pipewatch.report import _status_symbol


def _resolve_path(args: argparse.Namespace) -> Optional[str]:
    return getattr(args, "history_file", None)


def cmd_metrics_last(args: argparse.Namespace) -> None:
    """Print metrics for the most recent run."""
    h = History(path=_resolve_path(args))
    entries = h.load()
    if not entries:
        print("No history found.", file=sys.stderr)
        sys.exit(1)
    entry = entries[-1]
    raw = entry.to_dict().get("metrics")
    if not raw:
        print("No metrics recorded for the last run.", file=sys.stderr)
        sys.exit(1)
    m = Metrics.from_dict(raw)
    symbol = _status_symbol(entry.exit_code == 0)
    print(f"{symbol} Command : {entry.command}")
    print(f"  Exit code  : {m.exit_code}")
    print(f"  Elapsed    : {m.elapsed_human}")
    print(f"  Stdout     : {m.stdout_lines} lines")
    print(f"  Stderr     : {m.stderr_lines} lines")
    if m.peak_memory_mb is not None:
        print(f"  Peak mem   : {m.peak_memory_mb:.1f} MB")


def cmd_metrics_summary(args: argparse.Namespace) -> None:
    """Print aggregate metrics across all recorded runs."""
    h = History(path=_resolve_path(args))
    entries = h.load()
    metrics_list = [
        Metrics.from_dict(e.to_dict()["metrics"])
        for e in entries
        if e.to_dict().get("metrics")
    ]
    if not metrics_list:
        print("No metrics data available.")
        return
    durations = [m.elapsed_seconds for m in metrics_list if m.elapsed_seconds is not None]
    if durations:
        avg = sum(durations) / len(durations)
        print(f"Runs with metrics : {len(metrics_list)}")
        print(f"Avg elapsed       : {avg:.1f}s")
        print(f"Min elapsed       : {min(durations):.1f}s")
        print(f"Max elapsed       : {max(durations):.1f}s")
    else:
        print(f"Runs with metrics : {len(metrics_list)}")
        print("No duration data available.")


def build_metrics_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'metrics' sub-command group onto an existing subparser."""
    p = subparsers.add_parser("metrics", help="Show runtime metrics")
    p.add_argument("--history-file", default=None, help="Path to history file")
    sub = p.add_subparsers(dest="metrics_cmd", required=True)

    sub.add_parser("last", help="Metrics for the most recent run").set_defaults(
        func=cmd_metrics_last
    )
    sub.add_parser("summary", help="Aggregate metrics across all runs").set_defaults(
        func=cmd_metrics_summary
    )
